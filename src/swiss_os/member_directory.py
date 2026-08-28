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
from urllib.parse import urlsplit, urlunsplit


class MemberDirectoryError(ValueError):
    """Raised when member-directory evidence violates the manifest contract."""


CURRENT_SCOPES = frozenset(
    {
        "CURRENT_DIRECTORY_RECORD",
        "CURRENT_EXACT_ENTITY_DETAIL",
        "CURRENT_SNAPSHOT_CONFIRMED",
    }
)
ALLOWED_SCOPES = CURRENT_SCOPES | frozenset(
    {
        "HISTORICAL_CACHE_DISCOVERY_ONLY",
        "RECONCILE_REQUIRED",
        "UNKNOWN_SCOPE",
    }
)


def _text(value: object) -> str:
    return str(value or "").strip()


def _required(value: object, field: str) -> str:
    text = _text(value)
    if not text:
        raise MemberDirectoryError(f"{field} must be non-empty")
    return text


def _iso8601(value: str, field: str) -> str:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise MemberDirectoryError(f"{field} must be ISO-8601") from exc
    return value


def _normalize_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    asciiish = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", asciiish.lower())).strip()


def _normalize_url(value: str) -> str:
    raw = value.strip()
    if not raw:
        return ""
    parts = urlsplit(raw)
    scheme = parts.scheme.lower()
    host = (parts.hostname or "").lower()
    port = parts.port
    if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        host = f"{host}:{port}"
    path = re.sub(r"/+", "/", parts.path or "/")
    if path != "/":
        path = path.rstrip("/")
    return urlunsplit((scheme, host, path, parts.query, ""))


def _sha256(payload: object) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class DirectoryRecord:
    record_id: str
    name: str
    city: str
    evidence_ref: str
    hs_id: str
    detail_url: str
    source_provider: str
    locale: str
    source_surface: str
    source_epoch: str
    partition_key: str
    observed_at: str
    evidence_scope: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "DirectoryRecord":
        record = cls(
            record_id=_required(payload.get("record_id"), "record_id"),
            name=_required(payload.get("name"), "name"),
            city=_required(payload.get("city"), "city"),
            evidence_ref=_required(payload.get("evidence_ref"), "evidence_ref"),
            hs_id=_text(payload.get("hs_id")),
            detail_url=_normalize_url(_text(payload.get("detail_url"))),
            source_provider=_required(payload.get("source_provider"), "source_provider"),
            locale=_required(payload.get("locale"), "locale").lower(),
            source_surface=_required(payload.get("source_surface"), "source_surface"),
            source_epoch=_required(payload.get("source_epoch"), "source_epoch"),
            partition_key=_required(payload.get("partition_key"), "partition_key"),
            observed_at=_iso8601(
                _required(payload.get("observed_at"), "observed_at"), "observed_at"
            ),
            evidence_scope=_required(payload.get("evidence_scope"), "evidence_scope"),
        )
        record.validate()
        return record

    def validate(self) -> None:
        if self.evidence_scope not in ALLOWED_SCOPES:
            raise MemberDirectoryError(
                f"record {self.record_id} has invalid evidence_scope: {self.evidence_scope}"
            )
        if self.detail_url and not self.detail_url.startswith(("https://", "http://")):
            raise MemberDirectoryError(
                f"record {self.record_id} detail_url must be absolute HTTP(S)"
            )
        if not (self.hs_id or self.detail_url or self.record_id):
            raise MemberDirectoryError(
                f"record {self.record_id} lacks stable source identity"
            )

    @property
    def normalized_name_city(self) -> str:
        return f"{_normalize_text(self.name)}|{_normalize_text(self.city)}"

    def ssr_record(self) -> dict[str, str]:
        result = {
            "record_id": self.record_id,
            "name": self.name,
            "city": self.city,
            "evidence_ref": self.evidence_ref,
            "hs_id": self.hs_id,
            "detail_url": self.detail_url,
        }
        return result

    def as_dict(self) -> dict[str, str]:
        return {
            **self.ssr_record(),
            "source_provider": self.source_provider,
            "locale": self.locale,
            "source_surface": self.source_surface,
            "source_epoch": self.source_epoch,
            "partition_key": self.partition_key,
            "observed_at": self.observed_at,
            "evidence_scope": self.evidence_scope,
            "normalized_name_city": self.normalized_name_city,
        }


@dataclass(frozen=True)
class DirectoryManifestConfig:
    snapshot_id: str
    observed_at: str
    source_provider: str
    locale: str
    source_url: str
    source_epoch: str
    expected_partitions: int
    declared_raw_records: int
    coverage_complete_requested: bool

    def validate(self) -> None:
        _required(self.snapshot_id, "snapshot_id")
        _iso8601(_required(self.observed_at, "observed_at"), "observed_at")
        _required(self.source_provider, "source_provider")
        _required(self.locale, "locale")
        _required(self.source_url, "source_url")
        _required(self.source_epoch, "source_epoch")
        if self.expected_partitions <= 0:
            raise MemberDirectoryError("expected_partitions must be positive")
        if self.declared_raw_records <= 0:
            raise MemberDirectoryError("declared_raw_records must be positive")


@dataclass(frozen=True)
class DirectoryManifestResult:
    manifest: dict[str, object]
    violations: tuple[str, ...]

    @property
    def coverage_complete(self) -> bool:
        return bool(self.manifest["coverage_complete"])


def _duplicate_values(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    dupes: set[str] = set()
    for value in values:
        if not value:
            continue
        if value in seen:
            dupes.add(value)
        seen.add(value)
    return tuple(sorted(dupes))


def build_member_directory_manifest(
    records: Sequence[DirectoryRecord], config: DirectoryManifestConfig
) -> DirectoryManifestResult:
    config.validate()
    violations: list[str] = []

    if not records:
        violations.append("NO_RECORDS")

    duplicate_record_ids = _duplicate_values(record.record_id for record in records)
    duplicate_hs_ids = _duplicate_values(record.hs_id for record in records)
    duplicate_detail_urls = _duplicate_values(record.detail_url for record in records)
    duplicate_name_city = _duplicate_values(
        record.normalized_name_city for record in records
    )

    if duplicate_record_ids:
        violations.append("DUPLICATE_RECORD_ID")
    if duplicate_hs_ids:
        violations.append("DUPLICATE_HS_ID")
    if duplicate_detail_urls:
        violations.append("DUPLICATE_DETAIL_URL")
    if duplicate_name_city:
        violations.append("DUPLICATE_NORMALIZED_NAME_CITY")

    provider_mismatches = tuple(
        record.record_id
        for record in records
        if record.source_provider != config.source_provider
    )
    locale_mismatches = tuple(
        record.record_id for record in records if record.locale != config.locale.lower()
    )
    epoch_mismatches = tuple(
        record.record_id for record in records if record.source_epoch != config.source_epoch
    )
    post_observation_records = tuple(
        record.record_id for record in records if record.observed_at > config.observed_at
    )
    non_current_records = tuple(
        record.record_id for record in records if record.evidence_scope not in CURRENT_SCOPES
    )

    if provider_mismatches:
        violations.append("MIXED_SOURCE_PROVIDER")
    if locale_mismatches:
        violations.append("MIXED_LOCALE")
    if epoch_mismatches:
        violations.append("MIXED_SOURCE_EPOCH")
    if post_observation_records:
        violations.append("RECORD_OBSERVED_AFTER_MANIFEST")
    if non_current_records:
        violations.append("NON_CURRENT_EVIDENCE_SCOPE")

    partitions = tuple(sorted({record.partition_key for record in records}))
    if len(partitions) != config.expected_partitions:
        violations.append("PARTITION_COVERAGE_MISMATCH")
    if len(records) != config.declared_raw_records:
        violations.append("DECLARED_RECORD_COUNT_MISMATCH")

    unique_violations = tuple(dict.fromkeys(violations))
    coverage_complete = bool(
        config.coverage_complete_requested and not unique_violations
    )

    ordered_records = sorted(records, key=lambda record: record.record_id)
    public_records = [record.ssr_record() for record in ordered_records]
    extended_records = [record.as_dict() for record in ordered_records]

    diagnostics = {
        "duplicate_record_ids": list(duplicate_record_ids),
        "duplicate_hs_ids": list(duplicate_hs_ids),
        "duplicate_detail_urls": list(duplicate_detail_urls),
        "duplicate_normalized_name_city": list(duplicate_name_city),
        "provider_mismatches": list(provider_mismatches),
        "locale_mismatches": list(locale_mismatches),
        "epoch_mismatches": list(epoch_mismatches),
        "post_observation_records": list(post_observation_records),
        "non_current_records": list(non_current_records),
        "observed_partitions": list(partitions),
        "observed_partition_count": len(partitions),
        "expected_partition_count": config.expected_partitions,
        "materialized_record_count": len(records),
        "declared_raw_records": config.declared_raw_records,
    }

    manifest: dict[str, object] = {
        "schema_version": "MEMBER-DIRECTORY-1.0",
        "snapshot_id": config.snapshot_id,
        "observed_at": config.observed_at,
        "source_provider": config.source_provider,
        "locale": config.locale.lower(),
        "source_url": _normalize_url(config.source_url),
        "source_epoch": config.source_epoch,
        "coverage_complete_requested": config.coverage_complete_requested,
        "coverage_complete": coverage_complete,
        "records_count": len(records),
        "records_sha256": _sha256(extended_records),
        "records": public_records,
        "record_extensions": extended_records,
        "violations": list(unique_violations),
        "diagnostics": diagnostics,
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound_opened": False,
        "send_allowed": 0,
    }
    manifest["manifest_sha256"] = _sha256(
        {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    )
    return DirectoryManifestResult(manifest, unique_violations)


def validate_member_directory_manifest(payload: Mapping[str, object]) -> tuple[str, ...]:
    violations: list[str] = []
    if payload.get("schema_version") != "MEMBER-DIRECTORY-1.0":
        violations.append("INVALID_SCHEMA_VERSION")
    if bool(payload.get("authority_advanced")):
        violations.append("AUTHORITY_ADVANCED_FORBIDDEN")
    if int(payload.get("h_id_allocations", 0)) != 0:
        violations.append("H_ID_ALLOCATIONS_FORBIDDEN")
    if bool(payload.get("outbound_opened")):
        violations.append("OUTBOUND_OPENED_FORBIDDEN")
    if int(payload.get("send_allowed", 0)) != 0:
        violations.append("SEND_ALLOWED_FORBIDDEN")

    records = payload.get("record_extensions")
    if not isinstance(records, list):
        violations.append("RECORD_EXTENSIONS_NOT_ARRAY")
        records = []
    if int(payload.get("records_count", -1)) != len(records):
        violations.append("RECORD_COUNT_MISMATCH")
    if payload.get("records_sha256") != _sha256(records):
        violations.append("RECORDS_SHA256_MISMATCH")

    expected_manifest_sha = _sha256(
        {key: value for key, value in payload.items() if key != "manifest_sha256"}
    )
    if payload.get("manifest_sha256") != expected_manifest_sha:
        violations.append("MANIFEST_SHA256_MISMATCH")

    declared_violations = payload.get("violations", [])
    if bool(payload.get("coverage_complete")) and declared_violations:
        violations.append("COMPLETE_WITH_DECLARED_VIOLATIONS")
    if bool(payload.get("coverage_complete")) and not bool(
        payload.get("coverage_complete_requested")
    ):
        violations.append("COMPLETE_NOT_REQUESTED")

    return tuple(dict.fromkeys(violations))


def _read_json(path: str | Path) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str | Path, payload: object) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    tmp.replace(target)


def cmd_build(args: argparse.Namespace) -> int:
    payload = _read_json(args.records)
    if isinstance(payload, Mapping):
        raw_records = payload.get("records", [])
    else:
        raw_records = payload
    if not isinstance(raw_records, list):
        raise MemberDirectoryError("records input must be an array or {records: [...]} object")
    records = tuple(
        DirectoryRecord.from_mapping(item)
        for item in raw_records
        if isinstance(item, Mapping)
    )
    if len(records) != len(raw_records):
        raise MemberDirectoryError("records input must contain only objects")

    config = DirectoryManifestConfig(
        snapshot_id=args.snapshot_id,
        observed_at=args.observed_at,
        source_provider=args.source_provider,
        locale=args.locale,
        source_url=args.source_url,
        source_epoch=args.source_epoch,
        expected_partitions=args.expected_partitions,
        declared_raw_records=args.declared_raw_records,
        coverage_complete_requested=args.coverage_complete,
    )
    result = build_member_directory_manifest(records, config)
    _write_json(args.out, result.manifest)
    print(
        json.dumps(
            {
                "snapshot_id": config.snapshot_id,
                "coverage_complete": result.coverage_complete,
                "violations": list(result.violations),
                "records_count": len(records),
                "records_sha256": result.manifest["records_sha256"],
                "manifest_sha256": result.manifest["manifest_sha256"],
                "authority_advanced": False,
                "h_id_allocations": 0,
                "outbound_opened": False,
                "send_allowed": 0,
                "out": args.out,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if (not args.coverage_complete or result.coverage_complete) else 2


def cmd_validate(path: str) -> int:
    payload = _read_json(path)
    if not isinstance(payload, Mapping):
        raise MemberDirectoryError("manifest must be a JSON object")
    violations = validate_member_directory_manifest(payload)
    print(
        json.dumps(
            {
                "valid": not violations,
                "coverage_complete": bool(payload.get("coverage_complete")),
                "violations": list(violations),
                "records_count": payload.get("records_count"),
                "manifest_sha256": payload.get("manifest_sha256"),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if not violations else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m swiss_os.member_directory")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build")
    build.add_argument("records")
    build.add_argument("--snapshot-id", required=True)
    build.add_argument("--observed-at", required=True)
    build.add_argument("--source-provider", default="HOTELLERIESUISSE_MEMBER_DIRECTORY")
    build.add_argument("--locale", required=True)
    build.add_argument("--source-url", required=True)
    build.add_argument("--source-epoch", required=True)
    build.add_argument("--expected-partitions", type=int, required=True)
    build.add_argument("--declared-raw-records", type=int, required=True)
    build.add_argument("--coverage-complete", action="store_true")
    build.add_argument("--out", required=True)

    validate = sub.add_parser("validate")
    validate.add_argument("path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "build":
            return cmd_build(args)
        if args.command == "validate":
            return cmd_validate(args.path)
    except (MemberDirectoryError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
