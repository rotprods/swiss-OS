from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping

from .snapshot_freeze import normalize_text, normalize_url


EXACT = "EXACT"
EXPLAINED = "EXPLAINED"
UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class DirectoryRecord:
    record_id: str
    name: str
    city: str = ""
    hs_id: str = ""
    detail_url: str = ""
    evidence_ref: str = ""

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any], index: int) -> "DirectoryRecord":
        record_id = str(value.get("record_id", "") or "").strip()
        hs_id = str(value.get("hs_id", "") or "").strip()
        detail_url = normalize_url(str(value.get("detail_url", "") or ""))
        name = str(value.get("name", "") or "").strip()
        city = str(value.get("city", "") or "").strip()
        evidence_ref = str(value.get("evidence_ref", "") or "").strip()
        if not record_id:
            seed = f"{hs_id}|{detail_url}|{normalize_text(name)}|{normalize_text(city)}|{index}"
            record_id = "MD-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:20]
        if not name:
            raise ValueError(f"member-directory record {record_id} is missing name")
        if not evidence_ref:
            raise ValueError(f"member-directory record {record_id} is missing evidence_ref")
        return cls(record_id, name, city, hs_id, detail_url, evidence_ref)


@dataclass(frozen=True)
class ScopeExplanation:
    side: str
    record_key: str
    reason_code: str
    evidence_ref: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ScopeExplanation":
        side = str(value.get("side", "") or "").strip().upper()
        record_key = str(value.get("record_key", "") or "").strip()
        reason_code = str(value.get("reason_code", "") or "").strip()
        evidence_ref = str(value.get("evidence_ref", "") or "").strip()
        if side not in {"API", "DIRECTORY"}:
            raise ValueError("scope explanation side must be API or DIRECTORY")
        if not record_key or not reason_code or not evidence_ref:
            raise ValueError("scope explanation requires record_key, reason_code and evidence_ref")
        return cls(side, record_key, reason_code, evidence_ref)


@dataclass(frozen=True)
class ScopeMatch:
    api_source_record_key: str
    directory_record_id: str
    match_basis: str

    def as_dict(self) -> dict[str, str]:
        return {
            "api_source_record_key": self.api_source_record_key,
            "directory_record_id": self.directory_record_id,
            "match_basis": self.match_basis,
        }


@dataclass(frozen=True)
class ScopeReconciliationResult:
    state: str
    api_count: int
    directory_count: int
    matched_count: int
    api_only: tuple[str, ...]
    directory_only: tuple[str, ...]
    conflicts: tuple[str, ...]
    explained_api_only: tuple[str, ...]
    explained_directory_only: tuple[str, ...]
    matches: tuple[ScopeMatch, ...]

    @property
    def reconciled(self) -> bool:
        return self.state in {EXACT, EXPLAINED}

    def as_dict(self) -> dict[str, object]:
        return {
            "state": self.state,
            "reconciled": self.reconciled,
            "api_count": self.api_count,
            "directory_count": self.directory_count,
            "matched_count": self.matched_count,
            "api_only": list(self.api_only),
            "directory_only": list(self.directory_only),
            "conflicts": list(self.conflicts),
            "explained_api_only": list(self.explained_api_only),
            "explained_directory_only": list(self.explained_directory_only),
            "matches": [item.as_dict() for item in self.matches],
        }


def _api_record_key(record: Mapping[str, Any]) -> str:
    key = str(record.get("source_record_key", "") or "").strip()
    if not key:
        raise ValueError("API record is missing source_record_key")
    return key


def _api_hs_id(record: Mapping[str, Any]) -> str:
    return str(record.get("hs_id", "") or "").strip()


def _api_detail_urls(record: Mapping[str, Any]) -> set[str]:
    result: set[str] = set()
    for item in record.get("links", []) if isinstance(record.get("links"), list) else []:
        if not isinstance(item, Mapping):
            continue
        url = normalize_url(str(item.get("url", "") or ""))
        if url:
            result.add(url)
    return result


def _api_name_city(record: Mapping[str, Any]) -> tuple[str, str]:
    return normalize_text(str(record.get("name", "") or "")), normalize_text(str(record.get("city", "") or ""))


def _directory_name_city(record: DirectoryRecord) -> tuple[str, str]:
    return normalize_text(record.name), normalize_text(record.city)


def _unique_index(pairs: list[tuple[str, str]]) -> tuple[dict[str, str], set[str]]:
    values: dict[str, set[str]] = {}
    for key, record_id in pairs:
        if key:
            values.setdefault(key, set()).add(record_id)
    unique = {key: next(iter(ids)) for key, ids in values.items() if len(ids) == 1}
    ambiguous = {key for key, ids in values.items() if len(ids) > 1}
    return unique, ambiguous


def reconcile_source_scope(
    api_manifest: Mapping[str, Any],
    directory_manifest: Mapping[str, Any],
    explanations: tuple[ScopeExplanation, ...] = (),
) -> ScopeReconciliationResult:
    """Reconcile discover.swiss capture against member-directory evidence.

    Matching precedence is deterministic and conservative:
    1) exact hsId, 2) exact detail URL, 3) exact normalized name+city.
    Ambiguous evidence fails closed. Count equality never implies scope equality.
    """

    if not bool(api_manifest.get("capture_valid", False)):
        raise ValueError("API manifest capture_valid must be true before scope reconciliation")
    if not bool(directory_manifest.get("coverage_complete", False)):
        raise ValueError("member-directory manifest must declare coverage_complete=true")
    directory_snapshot_id = str(directory_manifest.get("snapshot_id", "") or "").strip()
    if not directory_snapshot_id:
        raise ValueError("member-directory manifest requires snapshot_id")
    if not str(directory_manifest.get("observed_at", "") or "").strip():
        raise ValueError("member-directory manifest requires observed_at")

    api_records_raw = api_manifest.get("records", [])
    directory_records_raw = directory_manifest.get("records", [])
    if not isinstance(api_records_raw, list) or not isinstance(directory_records_raw, list):
        raise ValueError("both manifests must contain records arrays")

    api_records = [item for item in api_records_raw if isinstance(item, Mapping)]
    if len(api_records) != len(api_records_raw):
        raise ValueError("API manifest records must all be objects")
    directory_records = [DirectoryRecord.from_mapping(item, idx) for idx, item in enumerate(directory_records_raw) if isinstance(item, Mapping)]
    if len(directory_records) != len(directory_records_raw):
        raise ValueError("member-directory records must all be objects")

    api_keys = [_api_record_key(item) for item in api_records]
    if len(set(api_keys)) != len(api_keys):
        raise ValueError("API source_record_key values must be unique")
    dir_ids = [item.record_id for item in directory_records]
    if len(set(dir_ids)) != len(dir_ids):
        raise ValueError("member-directory record_id values must be unique")

    api_by_key = {key: record for key, record in zip(api_keys, api_records)}

    dir_hs, ambiguous_dir_hs = _unique_index([(r.hs_id, r.record_id) for r in directory_records])
    dir_url, ambiguous_dir_url = _unique_index([(r.detail_url, r.record_id) for r in directory_records])
    dir_nc, ambiguous_dir_nc = _unique_index([("|".join(_directory_name_city(r)), r.record_id) for r in directory_records])

    api_hs, ambiguous_api_hs = _unique_index([(_api_hs_id(r), key) for key, r in api_by_key.items()])
    api_urls_pairs: list[tuple[str, str]] = []
    for key, record in api_by_key.items():
        api_urls_pairs.extend((url, key) for url in _api_detail_urls(record))
    api_url, ambiguous_api_url = _unique_index(api_urls_pairs)
    api_nc, ambiguous_api_nc = _unique_index([("|".join(_api_name_city(r)), key) for key, r in api_by_key.items()])

    unmatched_api = set(api_keys)
    unmatched_dir = set(dir_ids)
    matches: list[ScopeMatch] = []
    conflicts: set[str] = set()

    # Ambiguity within either source is itself a reconciliation conflict, even
    # before cross-source matching. This prevents duplicate identities from
    # degrading into silent unmatched records.
    conflicts.update(f"AMBIGUOUS_HSID:{key}" for key in sorted(ambiguous_api_hs | ambiguous_dir_hs))
    conflicts.update(f"AMBIGUOUS_DETAIL_URL:{key}" for key in sorted(ambiguous_api_url | ambiguous_dir_url))
    conflicts.update(f"AMBIGUOUS_NAME_CITY:{key}" for key in sorted(ambiguous_api_nc | ambiguous_dir_nc))

    def bind(api_key: str, dir_id: str, basis: str) -> None:
        if api_key not in unmatched_api or dir_id not in unmatched_dir:
            conflicts.add(f"MULTI_MATCH:{basis}:{api_key}:{dir_id}")
            return
        unmatched_api.remove(api_key)
        unmatched_dir.remove(dir_id)
        matches.append(ScopeMatch(api_key, dir_id, basis))

    for hs_id, api_key in sorted(api_hs.items()):
        if hs_id in ambiguous_api_hs or hs_id in ambiguous_dir_hs:
            continue
        dir_id = dir_hs.get(hs_id)
        if dir_id:
            bind(api_key, dir_id, "EXACT_HSID")

    for url, api_key in sorted(api_url.items()):
        if api_key not in unmatched_api:
            continue
        if url in ambiguous_api_url or url in ambiguous_dir_url:
            continue
        dir_id = dir_url.get(url)
        if dir_id and dir_id in unmatched_dir:
            bind(api_key, dir_id, "EXACT_DETAIL_URL")

    for nc, api_key in sorted(api_nc.items()):
        if api_key not in unmatched_api:
            continue
        if nc in ambiguous_api_nc or nc in ambiguous_dir_nc:
            continue
        dir_id = dir_nc.get(nc)
        if dir_id and dir_id in unmatched_dir:
            bind(api_key, dir_id, "EXACT_NAME_CITY")

    explanation_map: dict[tuple[str, str], ScopeExplanation] = {}
    for explanation in explanations:
        key = (explanation.side, explanation.record_key)
        if key in explanation_map:
            raise ValueError(f"duplicate scope explanation for {explanation.side}:{explanation.record_key}")
        explanation_map[key] = explanation

    explained_api = sorted(key for key in unmatched_api if ("API", key) in explanation_map)
    explained_dir = sorted(key for key in unmatched_dir if ("DIRECTORY", key) in explanation_map)
    unresolved_api = sorted(unmatched_api.difference(explained_api))
    unresolved_dir = sorted(unmatched_dir.difference(explained_dir))

    if conflicts or unresolved_api or unresolved_dir:
        state = UNRESOLVED
    elif explained_api or explained_dir:
        state = EXPLAINED
    else:
        state = EXACT

    return ScopeReconciliationResult(
        state=state,
        api_count=len(api_records),
        directory_count=len(directory_records),
        matched_count=len(matches),
        api_only=tuple(unresolved_api),
        directory_only=tuple(unresolved_dir),
        conflicts=tuple(sorted(conflicts)),
        explained_api_only=tuple(explained_api),
        explained_directory_only=tuple(explained_dir),
        matches=tuple(sorted(matches, key=lambda item: item.api_source_record_key)),
    )


def build_candidate_snapshot(
    api_manifest: Mapping[str, Any],
    directory_manifest: Mapping[str, Any],
    result: ScopeReconciliationResult,
    explanations: tuple[ScopeExplanation, ...] = (),
) -> dict[str, Any]:
    """Build a public-safe candidate-snapshot manifest without advancing authority."""

    api_snapshot_id = str(api_manifest.get("snapshot_id", "") or "").strip()
    directory_snapshot_id = str(directory_manifest.get("snapshot_id", "") or "").strip()
    if not api_snapshot_id or not directory_snapshot_id:
        raise ValueError("both source manifests require snapshot_id")

    reconciliation_payload = result.as_dict()
    reconciliation_payload["explanations"] = [
        {
            "side": item.side,
            "record_key": item.record_key,
            "reason_code": item.reason_code,
            "evidence_ref": item.evidence_ref,
        }
        for item in sorted(explanations, key=lambda item: (item.side, item.record_key))
    ]
    reconciliation_sha = hashlib.sha256(
        json.dumps(reconciliation_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    eligible = bool(api_manifest.get("capture_valid", False)) and bool(directory_manifest.get("coverage_complete", False)) and result.reconciled
    return {
        "schema_version": "swiss-os-crm-candidate-snapshot-v1",
        "candidate_snapshot_id": f"CRM-CAND-{api_snapshot_id}-{reconciliation_sha[:12]}",
        "api_snapshot_id": api_snapshot_id,
        "member_directory_snapshot_id": directory_snapshot_id,
        "source_scope_reconciliation": result.state,
        "member_directory_scope_reconciled": result.reconciled,
        "snapshot_state": "FROZEN_CANDIDATE" if eligible else "STAGED",
        "crm_freeze_eligible": eligible,
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound_opened": False,
        "reconciliation_sha256": reconciliation_sha,
        "reconciliation": reconciliation_payload,
    }
