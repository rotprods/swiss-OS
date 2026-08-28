from __future__ import annotations

from typing import Any, Mapping

from .snapshot_freeze import normalize_url


def _preferred_detail_url(record: Mapping[str, Any]) -> str:
    links = record.get("links", [])
    if not isinstance(links, list):
        return ""
    normalized: list[tuple[str, str]] = []
    for item in links:
        if not isinstance(item, Mapping):
            continue
        url = normalize_url(str(item.get("url", "") or ""))
        if not url:
            continue
        link_type = str(item.get("type", "") or "").casefold()
        normalized.append((link_type, url))
    if not normalized:
        return ""
    # Prefer a canonical/public web link where type metadata exists; otherwise
    # keep deterministic lexical ordering instead of arbitrary source order.
    normalized.sort(key=lambda pair: (0 if pair[0] in {"website", "web", "homepage", "official"} else 1, pair[0], pair[1]))
    return normalized[0][1]


def export_candidate_ingest_records(
    candidate_manifest: Mapping[str, Any],
    api_manifest: Mapping[str, Any],
) -> list[dict[str, str]]:
    """Convert a reconciled FROZEN_CANDIDATE into crm-ingest input records.

    This is intentionally pre-authority. It does not allocate H-IDs or create
    terminal CRM source mappings.
    """

    if not bool(candidate_manifest.get("crm_freeze_eligible", False)):
        raise ValueError("candidate snapshot is not crm_freeze_eligible")
    if str(candidate_manifest.get("snapshot_state", "")) != "FROZEN_CANDIDATE":
        raise ValueError("candidate snapshot must be FROZEN_CANDIDATE")
    candidate_api_id = str(candidate_manifest.get("api_snapshot_id", "") or "").strip()
    api_id = str(api_manifest.get("snapshot_id", "") or "").strip()
    if not candidate_api_id or candidate_api_id != api_id:
        raise ValueError("candidate api_snapshot_id must match API manifest snapshot_id")
    if not bool(api_manifest.get("capture_valid", False)):
        raise ValueError("API manifest capture_valid must be true")

    endpoint = str(api_manifest.get("endpoint", "") or "").strip()
    if not endpoint:
        raise ValueError("API manifest endpoint is required")
    records = api_manifest.get("records", [])
    if not isinstance(records, list):
        raise ValueError("API manifest records must be an array")

    output: list[dict[str, str]] = []
    seen_keys: set[str] = set()
    for item in records:
        if not isinstance(item, Mapping):
            raise ValueError("API manifest records must all be objects")
        provider_key = str(item.get("source_record_key", "") or "").strip()
        name = str(item.get("name", "") or "").strip()
        city = str(item.get("city", "") or "").strip()
        if not provider_key:
            raise ValueError("API source record is missing source_record_key")
        if provider_key in seen_keys:
            raise ValueError(f"duplicate API source_record_key: {provider_key}")
        if not name:
            raise ValueError(f"API source record {provider_key} is missing name")
        seen_keys.add(provider_key)
        output.append(
            {
                "source_url": endpoint,
                "raw_name": name,
                "raw_city": city,
                "detail_url": _preferred_detail_url(item),
                "provider_record_key": provider_key,
            }
        )

    output.sort(key=lambda item: item["provider_record_key"])
    expected = int(api_manifest.get("records_count", len(records)))
    if expected != len(output):
        raise ValueError(f"API records_count={expected} does not equal exported records={len(output)}")
    return output
