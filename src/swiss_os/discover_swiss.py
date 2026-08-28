from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class DiscoverSwissError(RuntimeError):
    """Base error for discover.swiss snapshot acquisition."""


class MissingSubscriptionKey(DiscoverSwissError):
    """Raised when no Infocenter subscription key is available."""


class PaginationCycleError(DiscoverSwissError):
    """Raised when discover.swiss returns a repeated continuation token."""


JsonGetter = Callable[[str, Mapping[str, str], float], Mapping[str, Any]]


@dataclass(frozen=True)
class DiscoverSwissConfig:
    base_url: str = "https://api.discover.swiss/info/v2"
    project: str = "dsod-hs"
    language: str = "de"
    top: int = -1
    timeout_seconds: float = 30.0
    category_version: str = "sui"
    subscription_key_env: str = "DISCOVER_SWISS_SUBSCRIPTION_KEY"

    def validate(self) -> None:
        if not self.base_url.strip():
            raise ValueError("base_url is required")
        if not self.project.strip():
            raise ValueError("project is required")
        if not self.language.strip():
            raise ValueError("language is required")
        if self.top == 0 or self.top < -1:
            raise ValueError("top must be -1 or a positive integer")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if not self.subscription_key_env.strip():
            raise ValueError("subscription_key_env is required")


def resolve_subscription_key(
    config: DiscoverSwissConfig,
    environ: Mapping[str, str] | None = None,
) -> str:
    config.validate()
    env = os.environ if environ is None else environ
    key = str(env.get(config.subscription_key_env, "")).strip()
    if not key:
        raise MissingSubscriptionKey(
            f"missing discover.swiss subscription key in environment variable "
            f"{config.subscription_key_env}"
        )
    return key


def build_lodgingbusinesses_url(
    config: DiscoverSwissConfig,
    *,
    continuation_token: str | None = None,
    include_count: bool = False,
    updated_since: str | None = None,
    deleted: bool = False,
) -> str:
    """Build one paged lodgingbusinesses request.

    The continuation token is passed as the `continuationToken` query parameter.
    `urllib.parse.urlencode` performs the required URL encoding.
    """

    config.validate()
    params: list[tuple[str, str]] = [
        ("project", config.project),
        ("top", str(config.top)),
    ]
    if include_count:
        params.append(("includeCount", "true"))
    if continuation_token:
        params.append(("continuationToken", continuation_token))
    if updated_since:
        params.append(("updatedSince", updated_since))
    if deleted:
        params.append(("deleted", "true"))
    return f"{config.base_url.rstrip('/')}/lodgingbusinesses?{urlencode(params)}"


def _default_get_json(
    url: str,
    headers: Mapping[str, str],
    timeout_seconds: float,
) -> Mapping[str, Any]:
    request = Request(url, headers=dict(headers), method="GET")
    try:
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        raise DiscoverSwissError(
            f"discover.swiss HTTP {exc.code} while requesting lodgingbusinesses"
        ) from exc
    except URLError as exc:
        raise DiscoverSwissError(
            f"discover.swiss transport error while requesting lodgingbusinesses: {exc.reason}"
        ) from exc

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise DiscoverSwissError("discover.swiss returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise DiscoverSwissError("discover.swiss response must be a JSON object")
    return payload


def _iter_dicts(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def extract_hs_id(record: Mapping[str, Any]) -> str:
    for item in _iter_dicts(record.get("additionalProperty")):
        if str(item.get("propertyId", "")).strip() == "hsId":
            value = item.get("value", item.get("valueStr", ""))
            return str(value or "").strip()
    return ""


def extract_city(record: Mapping[str, Any]) -> str:
    for address in _iter_dicts(record.get("address")):
        for key in ("addressLocality", "city", "locality"):
            value = str(address.get(key, "") or "").strip()
            if value:
                return value
    return ""


def extract_links(record: Mapping[str, Any]) -> list[dict[str, str]]:
    values: set[tuple[str, str]] = set()
    for item in _iter_dicts(record.get("link")):
        url = str(item.get("url", "") or "").strip()
        if not url:
            continue
        values.add((str(item.get("type", "") or "").strip(), url))
    return [
        {"type": link_type, "url": url}
        for link_type, url in sorted(values, key=lambda item: (item[0], item[1]))
    ]


def extract_origins(record: Mapping[str, Any]) -> list[dict[str, str]]:
    governance = record.get("dataGovernance")
    if not isinstance(governance, dict):
        return []
    origins: list[dict[str, str]] = []
    for item in _iter_dicts(governance.get("origin")):
        source = item.get("source") if isinstance(item.get("source"), dict) else {}
        origins.append(
            {
                "datasource": str(item.get("datasource", "") or "").strip(),
                "source_id": str(item.get("sourceId", "") or "").strip(),
                "source": str(
                    source.get("identifier", source.get("acronym", "")) or ""
                ).strip(),
                "license": str(item.get("license", "") or "").strip(),
                "last_modified": str(item.get("lastModified", "") or "").strip(),
            }
        )
    origins.sort(
        key=lambda item: (
            item["source"],
            item["datasource"],
            item["source_id"],
            item["license"],
        )
    )
    return origins


def has_hotelleriesuisse_origin(origins: list[dict[str, str]]) -> bool:
    for origin in origins:
        source = origin.get("source", "").casefold()
        datasource = origin.get("datasource", "").casefold()
        if source == "hs" or datasource == "hs" or datasource.startswith("hs-"):
            return True
    return False


def normalize_lodging_record(record: Mapping[str, Any]) -> dict[str, Any]:
    identifier = str(record.get("identifier", "") or "").strip()
    if not identifier:
        raise DiscoverSwissError("lodgingbusiness record is missing identifier")

    hs_id = extract_hs_id(record)
    origins = extract_origins(record)
    source_record_key = f"hs:{hs_id}" if hs_id else f"discover:{identifier}"
    return {
        "source_record_key": source_record_key,
        "discover_identifier": identifier,
        "hs_id": hs_id,
        "name": str(record.get("name", "") or "").strip(),
        "city": extract_city(record),
        "removed": bool(record.get("removed", False)),
        "last_modified": str(record.get("lastModified", "") or "").strip(),
        "links": extract_links(record),
        "origins": origins,
        "has_hotelleriesuisse_origin": has_hotelleriesuisse_origin(origins),
    }


def _duplicate_values(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicate: set[str] = set()
    for value in values:
        if not value:
            continue
        if value in seen:
            duplicate.add(value)
        seen.add(value)
    return sorted(duplicate)


def _canonical_records_sha256(records: list[dict[str, Any]]) -> str:
    payload = json.dumps(
        records,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_snapshot_manifest(
    *,
    config: DiscoverSwissConfig,
    records: list[dict[str, Any]],
    reported_count: int | None,
    api_pages: int,
    fetched_at: datetime | None = None,
) -> dict[str, Any]:
    ordered = sorted(records, key=lambda item: item["source_record_key"])
    data_sha = _canonical_records_sha256(ordered)
    now = fetched_at or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    fetched = now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    snapshot_id = f"DS-HS-{now.astimezone(timezone.utc):%Y%m%dT%H%M%SZ}-{data_sha[:12]}"

    discover_ids = [item["discover_identifier"] for item in ordered]
    hs_ids = [item["hs_id"] for item in ordered if item["hs_id"]]
    source_keys = [item["source_record_key"] for item in ordered]
    duplicate_discover_ids = _duplicate_values(discover_ids)
    duplicate_hs_ids = _duplicate_values(hs_ids)
    duplicate_source_keys = _duplicate_values(source_keys)
    missing_hs_id = sum(1 for item in ordered if not item["hs_id"])
    missing_hs_origin = sum(
        1 for item in ordered if not item["has_hotelleriesuisse_origin"]
    )

    violations: list[str] = []
    if reported_count is None:
        violations.append("first page did not report count despite includeCount=true")
    elif reported_count != len(ordered):
        violations.append(
            f"reported_count={reported_count} != records_count={len(ordered)}"
        )
    if api_pages <= 0:
        violations.append("api_pages must be greater than zero")
    if duplicate_discover_ids:
        violations.append("duplicate discover.swiss identifiers detected")
    if duplicate_hs_ids:
        violations.append("duplicate HotellerieSuisse hsId values detected")
    if duplicate_source_keys:
        violations.append("duplicate source_record_key values detected")
    if missing_hs_id:
        violations.append(f"records missing hsId: {missing_hs_id}")
    if missing_hs_origin:
        violations.append(
            f"records without HotellerieSuisse dataGovernance origin: {missing_hs_origin}"
        )

    # Capturing dsod-hs is not by itself proof that this is exactly the current
    # public member-directory universe. That is a separate reconciliation gate.
    scope_state = "HOTELLERIESUISSE_API_CAPTURED_MEMBER_DIRECTORY_RECONCILIATION_REQUIRED"

    return {
        "schema_version": "discover-swiss-hotelleriesuisse-snapshot-v1",
        "snapshot_id": snapshot_id,
        "source": "discover.swiss Infocenter / AccommoDataHub",
        "endpoint": f"{config.base_url.rstrip('/')}/lodgingbusinesses",
        "project": config.project,
        "language": config.language,
        "category_version": config.category_version,
        "top": config.top,
        "fetched_at": fetched,
        "reported_count": reported_count,
        "records_count": len(ordered),
        "api_pages": api_pages,
        "records_sha256": data_sha,
        "duplicate_discover_identifiers": duplicate_discover_ids,
        "duplicate_hs_ids": duplicate_hs_ids,
        "duplicate_source_record_keys": duplicate_source_keys,
        "missing_hs_id": missing_hs_id,
        "records_without_hotelleriesuisse_origin": missing_hs_origin,
        "capture_valid": not violations,
        "capture_violations": violations,
        "scope_state": scope_state,
        "member_directory_scope_reconciled": False,
        "crm_freeze_eligible": False,
        "records": ordered,
    }


def fetch_hotelleriesuisse_snapshot(
    config: DiscoverSwissConfig,
    subscription_key: str,
    *,
    get_json: JsonGetter = _default_get_json,
    fetched_at: datetime | None = None,
) -> dict[str, Any]:
    """Enumerate HotellerieSuisse-specific lodging businesses from Infocenter.

    The subscription key is used only as a request header and is never included
    in the returned manifest.
    """

    config.validate()
    key = subscription_key.strip()
    if not key:
        raise MissingSubscriptionKey("discover.swiss subscription key is empty")

    headers = {
        "Ocp-Apim-Subscription-Key": key,
        "Accept-Language": config.language,
        "categoryVersion": config.category_version,
        "Accept": "application/json",
    }

    continuation_token: str | None = None
    seen_tokens: set[str] = set()
    records: list[dict[str, Any]] = []
    reported_count: int | None = None
    api_pages = 0

    while True:
        url = build_lodgingbusinesses_url(
            config,
            continuation_token=continuation_token,
            include_count=api_pages == 0,
        )
        payload = get_json(url, headers, config.timeout_seconds)
        if not isinstance(payload, Mapping):
            raise DiscoverSwissError("discover.swiss response must be a mapping")
        data = payload.get("data")
        if not isinstance(data, list):
            raise DiscoverSwissError("discover.swiss response is missing data list")

        api_pages += 1
        if api_pages == 1:
            raw_count = payload.get("count")
            if isinstance(raw_count, bool):
                reported_count = None
            elif isinstance(raw_count, (int, float)):
                reported_count = int(raw_count)

        for item in data:
            if not isinstance(item, Mapping):
                raise DiscoverSwissError("lodgingbusiness data item must be an object")
            records.append(normalize_lodging_record(item))

        has_next = bool(payload.get("hasNextPage", False))
        if not has_next:
            break

        next_token = str(payload.get("nextPageToken", "") or "").strip()
        if not next_token:
            raise DiscoverSwissError("hasNextPage=true but nextPageToken is missing")
        if next_token in seen_tokens:
            raise PaginationCycleError("discover.swiss continuation token cycle detected")
        seen_tokens.add(next_token)
        continuation_token = next_token

    return build_snapshot_manifest(
        config=config,
        records=records,
        reported_count=reported_count,
        api_pages=api_pages,
        fetched_at=fetched_at,
    )


def write_snapshot_manifest(path: str | Path, manifest: Mapping[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(
        json.dumps(dict(manifest), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    tmp.replace(target)
