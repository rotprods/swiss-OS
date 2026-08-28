from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata
from typing import Iterable, Mapping, Sequence
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET
import zipfile

from .member_directory import (
    DirectoryManifestConfig,
    DirectoryRecord,
    build_member_directory_manifest,
    validate_member_directory_manifest,
)


class StagingAdapterError(ValueError):
    """Raised when a staging workbook cannot be converted safely."""


_MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_NS = {"m": _MAIN_NS, "r": _REL_NS}
_URL_RE = re.compile(r"https?://[^\s|]+", re.IGNORECASE)


def _required(value: object, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise StagingAdapterError(f"{field} must be non-empty")
    return text


def _iso8601(value: str, field: str) -> str:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise StagingAdapterError(f"{field} must be ISO-8601") from exc
    return value


def _normalize(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text.lower())).strip()


def _column_number(column: str) -> int:
    number = 0
    for char in column:
        number = number * 26 + ord(char) - 64
    return number


def _slug(value: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return result or "unknown"


def _locale_from_url(url: str) -> str:
    path = urlsplit(url).path.lower()
    if "/fr/" in path:
        return "fr"
    if "/de/" in path:
        return "de"
    if "/it/" in path:
        return "it"
    if "/en/" in path:
        return "en"
    return "unknown"


def _stable_id(prefix: str, parts: Iterable[object]) -> str:
    payload = "|".join(str(part or "").strip() for part in parts).encode("utf-8")
    return f"{prefix}:{hashlib.sha256(payload).hexdigest()[:20]}"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_xlsx_sheet(path: str | Path, sheet_name: str) -> list[dict[str, object]]:
    """Read one XLSX sheet using only the standard library.

    Formula evaluation is intentionally out of scope. The adapter consumes the
    values persisted in the workbook and never writes back to the source file.
    """

    source = Path(path)
    if not source.is_file():
        raise StagingAdapterError(f"workbook not found: {source}")

    with zipfile.ZipFile(source) as archive:
        names = set(archive.namelist())
        shared: list[str] = []
        if "xl/sharedStrings.xml" in names:
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall("m:si", _NS):
                shared.append(
                    "".join(
                        node.text or ""
                        for node in item.iter(f"{{{_MAIN_NS}}}t")
                    )
                )

        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relationships = ET.fromstring(
            archive.read("xl/_rels/workbook.xml.rels")
        )
        relationship_map = {
            node.attrib["Id"]: node.attrib["Target"] for node in relationships
        }

        target: str | None = None
        sheets = workbook.find("m:sheets", _NS)
        if sheets is None:
            raise StagingAdapterError("workbook has no sheets collection")
        for sheet in sheets:
            if sheet.attrib.get("name") != sheet_name:
                continue
            relationship_id = sheet.attrib[f"{{{_REL_NS}}}id"]
            raw_target = relationship_map[relationship_id]
            target = (
                f"xl/{raw_target.lstrip('/')}"
                if not raw_target.startswith("/")
                else raw_target.lstrip("/")
            )
            break
        if not target:
            raise StagingAdapterError(f"sheet not found: {sheet_name}")

        root = ET.fromstring(archive.read(target))
        raw_rows: list[list[object]] = []
        for row in root.findall(".//m:sheetData/m:row", _NS):
            values: dict[int, object] = {}
            for cell in row.findall("m:c", _NS):
                reference = cell.attrib.get("r", "")
                match = re.match(r"([A-Z]+)(\d+)", reference)
                if not match:
                    continue
                column = _column_number(match.group(1))
                cell_type = cell.attrib.get("t")
                if cell_type == "inlineStr":
                    inline = cell.find("m:is", _NS)
                    value: object = (
                        ""
                        if inline is None
                        else "".join(
                            node.text or ""
                            for node in inline.iter(f"{{{_MAIN_NS}}}t")
                        )
                    )
                else:
                    value_node = cell.find("m:v", _NS)
                    raw = "" if value_node is None else (value_node.text or "")
                    if cell_type == "s" and raw:
                        try:
                            value = shared[int(raw)]
                        except (ValueError, IndexError):
                            value = raw
                    elif cell_type == "b":
                        value = raw == "1"
                    else:
                        value = raw
                values[column] = value
            if values:
                raw_rows.append(
                    [values.get(index, "") for index in range(1, max(values) + 1)]
                )

    if not raw_rows:
        return []
    headers = [_normalize(value).replace(" ", "_") for value in raw_rows[0]]
    if any(not header for header in headers):
        raise StagingAdapterError(f"sheet {sheet_name} has blank header cells")
    if len(headers) != len(set(headers)):
        raise StagingAdapterError(f"sheet {sheet_name} has duplicate normalized headers")

    result: list[dict[str, object]] = []
    for row_index, row in enumerate(raw_rows[1:], start=2):
        if not any(str(value or "").strip() for value in row):
            continue
        padded = list(row) + [""] * max(0, len(headers) - len(row))
        record = dict(zip(headers, padded[: len(headers)]))
        record["_row_number"] = row_index
        result.append(record)
    return result


@dataclass(frozen=True)
class AdapterReject:
    sheet: str
    row_number: int
    reason_code: str
    name: str
    city: str

    def as_dict(self) -> dict[str, object]:
        return {
            "sheet": self.sheet,
            "row_number": self.row_number,
            "reason_code": self.reason_code,
            "name": self.name,
            "city": self.city,
        }


def cache_records_from_rows(
    rows: Sequence[Mapping[str, object]],
    workbook_name: str,
    observed_at: str,
) -> tuple[tuple[DirectoryRecord, ...], tuple[AdapterReject, ...]]:
    _iso8601(observed_at, "observed_at")
    records: list[DirectoryRecord] = []
    rejects: list[AdapterReject] = []

    for row in rows:
        row_number = int(row.get("_row_number", 0))
        page = str(row.get("source_page", "")).strip()
        name = str(row.get("hotel_name", "")).strip()
        city = str(row.get("city", "")).strip()
        source_url = str(row.get("source_url", "")).strip()
        cache_age = str(row.get("cache_age", "UNKNOWN_CACHE_AGE")).strip()
        observed_count = str(row.get("observed_count", "")).strip()
        evidence_scope = str(
            row.get("evidence_scope", "HISTORICAL_CACHE_DISCOVERY_ONLY")
        ).strip()

        if not (page and name and city and source_url):
            rejects.append(
                AdapterReject(
                    "Directory_Cache_Observations",
                    row_number,
                    "MISSING_REQUIRED_CACHE_FIELD",
                    name,
                    city,
                )
            )
            continue
        locale = _locale_from_url(source_url)
        source_epoch = f"CACHE:{locale}:{cache_age}:{observed_count or 'COUNT_UNKNOWN'}"
        record_id = _stable_id(
            "cache",
            (page, name, city, source_url, cache_age, observed_count),
        )
        records.append(
            DirectoryRecord.from_mapping(
                {
                    "record_id": record_id,
                    "name": name,
                    "city": city,
                    "evidence_ref": (
                        f"{workbook_name}#Directory_Cache_Observations!{row_number}"
                    ),
                    "hs_id": "",
                    "detail_url": "",
                    "source_provider": "HOTELLERIESUISSE_INDEXED_CACHE",
                    "locale": locale,
                    "source_surface": "member-directory-index-cache",
                    "source_epoch": source_epoch,
                    "partition_key": f"page:{page}",
                    "observed_at": observed_at,
                    "evidence_scope": evidence_scope,
                }
            )
        )
    return tuple(records), tuple(rejects)


def v16_records_from_rows(
    rows: Sequence[Mapping[str, object]],
    workbook_name: str,
    observed_at: str,
    source_epoch: str,
) -> tuple[tuple[DirectoryRecord, ...], tuple[AdapterReject, ...]]:
    _iso8601(observed_at, "observed_at")
    _required(source_epoch, "source_epoch")
    records: list[DirectoryRecord] = []
    rejects: list[AdapterReject] = []

    for row in rows:
        row_number = int(row.get("_row_number", 0))
        proposed_id = str(row.get("proposed_id", "")).strip()
        name = str(row.get("name", "")).strip()
        city = str(row.get("city", "")).strip()
        evidence = str(row.get("evidence", ""))
        exact_urls = [
            url.rstrip(",.;)")
            for url in _URL_RE.findall(evidence)
            if "hotelleriesuisse.ch" in url.lower()
        ]
        if not (proposed_id and name and city):
            rejects.append(
                AdapterReject(
                    "V16_Canary",
                    row_number,
                    "MISSING_REQUIRED_V16_FIELD",
                    name,
                    city,
                )
            )
            continue
        if not exact_urls:
            rejects.append(
                AdapterReject(
                    "V16_Canary",
                    row_number,
                    "NO_EXACT_HOTELLERIESUISSE_DETAIL_URL",
                    name,
                    city,
                )
            )
            continue
        detail_url = exact_urls[0]
        locale = _locale_from_url(detail_url)
        records.append(
            DirectoryRecord.from_mapping(
                {
                    "record_id": f"v16:{proposed_id}",
                    "name": name,
                    "city": city,
                    "evidence_ref": f"{workbook_name}#V16_Canary!{row_number}",
                    "hs_id": "",
                    "detail_url": detail_url,
                    "source_provider": "HOTELLERIESUISSE_MEMBER_DIRECTORY",
                    "locale": locale,
                    "source_surface": "member-detail",
                    "source_epoch": source_epoch,
                    "partition_key": f"entity:{proposed_id}",
                    "observed_at": observed_at,
                    "evidence_scope": "CURRENT_EXACT_ENTITY_DETAIL",
                }
            )
        )
    return tuple(records), tuple(rejects)


def _cohort_key(record: DirectoryRecord) -> tuple[str, str, str, str]:
    return (
        record.source_provider,
        record.locale,
        record.source_epoch,
        record.evidence_scope,
    )


def build_cohort_registry(
    records: Sequence[DirectoryRecord],
    rejects: Sequence[AdapterReject],
    output_dir: str | Path,
    observed_at: str,
    expected_partitions: int,
    declared_raw_records: int,
    workbook_sha256: str,
) -> dict[str, object]:
    _iso8601(observed_at, "observed_at")
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)

    cohorts: dict[tuple[str, str, str, str], list[DirectoryRecord]] = {}
    for record in records:
        cohorts.setdefault(_cohort_key(record), []).append(record)

    entries: list[dict[str, object]] = []
    for cohort_key, cohort_records in sorted(cohorts.items()):
        provider, locale, epoch, evidence_scope = cohort_key
        cohort_id = _slug("-".join(cohort_key))[:120]
        config = DirectoryManifestConfig(
            snapshot_id=f"MDM-PARTIAL-{cohort_id}",
            observed_at=observed_at,
            source_provider=provider,
            locale=locale,
            source_url=(
                f"https://www.hotelleriesuisse.ch/{locale}/"
                if provider == "HOTELLERIESUISSE_MEMBER_DIRECTORY"
                else "https://www.hotelleriesuisse.ch/"
            ),
            source_epoch=epoch,
            expected_partitions=expected_partitions,
            declared_raw_records=declared_raw_records,
            coverage_complete_requested=False,
        )
        result = build_member_directory_manifest(tuple(cohort_records), config)
        manifest_path = target / f"{cohort_id}.manifest.json"
        records_path = target / f"{cohort_id}.records.json"
        _write_json(manifest_path, result.manifest)
        _write_json(records_path, [record.as_dict() for record in cohort_records])
        validation = validate_member_directory_manifest(result.manifest)
        if validation:
            raise StagingAdapterError(
                f"generated cohort {cohort_id} failed transfer validation: {validation}"
            )
        entries.append(
            {
                "cohort_id": cohort_id,
                "source_provider": provider,
                "locale": locale,
                "source_epoch": epoch,
                "evidence_scope": evidence_scope,
                "records_count": len(cohort_records),
                "coverage_complete": result.coverage_complete,
                "ssr_eligible": result.coverage_complete,
                "semantic_violations": list(result.violations),
                "manifest_path": manifest_path.name,
                "manifest_sha256": _sha256(manifest_path),
                "records_path": records_path.name,
                "records_file_sha256": _sha256(records_path),
            }
        )

    registry: dict[str, object] = {
        "schema_version": "STAGING-EVIDENCE-REGISTRY-1.0",
        "generated_at": observed_at,
        "workbook_sha256": workbook_sha256,
        "cohorts": entries,
        "cohort_count": len(entries),
        "records_count": len(records),
        "rejects_count": len(rejects),
        "rejects": [reject.as_dict() for reject in rejects],
        "coverage_complete": False,
        "ssr_eligible_cohorts": sum(1 for entry in entries if entry["ssr_eligible"]),
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound": "CLOSED",
        "send_allowed": 0,
        "selection_rule": (
            "SSR requires exactly one independently complete coherent current manifest; "
            "partial cohorts are evidence inputs and must never be unioned into a completion claim."
        ),
    }
    registry_without_hash = json.dumps(
        registry, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    registry["registry_sha256"] = hashlib.sha256(registry_without_hash).hexdigest()
    _write_json(target / "STAGING_EVIDENCE_REGISTRY.json", registry)
    return registry


def extract_workbook(
    workbook: str | Path,
    output_dir: str | Path,
    observed_at: str,
    v16_epoch: str,
    expected_partitions: int,
    declared_raw_records: int,
) -> dict[str, object]:
    workbook_path = Path(workbook)
    cache_rows = read_xlsx_sheet(workbook_path, "Directory_Cache_Observations")
    v16_rows = read_xlsx_sheet(workbook_path, "V16_Canary")
    cache_records, cache_rejects = cache_records_from_rows(
        cache_rows, workbook_path.name, observed_at
    )
    v16_records, v16_rejects = v16_records_from_rows(
        v16_rows, workbook_path.name, observed_at, v16_epoch
    )
    return build_cohort_registry(
        cache_records + v16_records,
        cache_rejects + v16_rejects,
        output_dir,
        observed_at,
        expected_partitions,
        declared_raw_records,
        _sha256(workbook_path),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m swiss_os.staging_adapter")
    sub = parser.add_subparsers(dest="command", required=True)
    extract = sub.add_parser("extract-workbook")
    extract.add_argument("workbook")
    extract.add_argument("--out-dir", required=True)
    extract.add_argument("--observed-at", required=True)
    extract.add_argument("--v16-epoch", required=True)
    extract.add_argument("--expected-partitions", type=int, default=171)
    extract.add_argument("--declared-raw-records", type=int, default=2050)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "extract-workbook":
            registry = extract_workbook(
                args.workbook,
                args.out_dir,
                args.observed_at,
                args.v16_epoch,
                args.expected_partitions,
                args.declared_raw_records,
            )
            print(json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True))
            return 0
    except (StagingAdapterError, ValueError, zipfile.BadZipFile) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
