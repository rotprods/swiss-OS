from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .market_enrichment import HttpResearchClient
from .vacancy_detail import SCHEMA_VERSION, opening_route_workset, resolve_route, sha256_value


ROUTE_REJECTION_STATE = "ROUTE_URL_REJECTED_SECURITY_BOUNDARY"


def rejected_route_result(route_url: str, observed_at: str, exc: ValueError) -> dict[str, Any]:
    """Materialize a route-level safety rejection without weakening the safety check.

    The route remains unresolved and contributes no role/no-opening inference. Only the
    blast radius changes: one rejected URL cannot destroy evidence collected for the
    other records assigned to the same deterministic shard.
    """
    return {
        "requested_url": route_url,
        "final_url": None,
        "fetch_state": "URL_REJECTED",
        "http_status": None,
        "body_sha256": None,
        "observed_at": observed_at,
        "role_signals": [],
        "language_signal_snippets": [],
        "experience_signal_snippets": [],
        "start_signal_snippets": [],
        "housing_signal": False,
        "contact_emails": [],
        "no_openings_explicit": False,
        "resolution_state": ROUTE_REJECTION_STATE,
        "rejection_class": "PUBLIC_URL_SAFETY_VALIDATION_REJECTED",
        "rejection_reason": str(exc)[:240],
        "authority_effect": "NONE",
        "outbound": "CLOSED",
        "send_allowed": 0,
    }


def resolve_route_isolated(client: HttpResearchClient, route_url: str, observed_at: str) -> dict[str, Any]:
    try:
        return resolve_route(client, route_url, observed_at)
    except ValueError as exc:
        return rejected_route_result(route_url, observed_at, exc)


def compile_shard_fault_isolated(
    aggregate: Mapping[str, Any],
    *,
    shard_index: int,
    shard_count: int,
    observed_at: str,
    client: HttpResearchClient | None = None,
) -> dict[str, Any]:
    workset = opening_route_workset(aggregate)
    if not (0 <= shard_index < shard_count):
        raise ValueError("invalid shard index")
    assigned = [item for index, item in enumerate(workset) if index % shard_count == shard_index]
    client = client or HttpResearchClient()
    records: list[dict[str, Any]] = []
    rejected_routes = 0
    for item in assigned:
        route_results = [resolve_route_isolated(client, route, observed_at) for route in item["opening_routes"]]
        rejected_routes += sum(1 for result in route_results if result.get("resolution_state") == ROUTE_REJECTION_STATE)
        signals = [signal for result in route_results for signal in result.get("role_signals") or []]
        records.append(
            {
                **item,
                "routes": route_results,
                "role_signal_count": len(signals),
                "current_role_signal_titles": sorted(
                    {str(signal.get("title")) for signal in signals if signal.get("title")}
                )[:50],
                "no_openings_explicit": bool(route_results)
                and all(bool(result.get("no_openings_explicit")) for result in route_results),
                "route_rejections": sum(
                    1 for result in route_results if result.get("resolution_state") == ROUTE_REJECTION_STATE
                ),
                "authority_effect": "NONE",
                "outbound": "CLOSED",
                "send_allowed": 0,
            }
        )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "execution_adapter": "VACANCY-DETAIL-FAULT-ISOLATION-1.0",
        "project": "SWITZERLAND_JOB_OS",
        "source_market_aggregate_sha256": sha256_value(aggregate),
        "source_snapshot_id": aggregate.get("source_snapshot_id"),
        "workset_total": len(workset),
        "workset_sha256": sha256_value(workset),
        "shard_index": shard_index,
        "shard_count": shard_count,
        "observed_at": observed_at,
        "records": records,
        "record_ids_sha256": sha256_value([record["record_id"] for record in records]),
        "route_rejections": rejected_routes,
        "authority_advanced": False,
        "canonical_id_allocations": 0,
        "canonical_id_reservations": 0,
        "outbound": "CLOSED",
        "send_allowed": 0,
        "irreversible_external_actions": 0,
    }
    return payload


def _load(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError(f"expected JSON object: {path}")
    return value


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aggregate", type=Path, required=True)
    parser.add_argument("--shard-index", type=int, required=True)
    parser.add_argument("--shard-count", type=int, required=True)
    parser.add_argument("--observed-at", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    market = _load(args.aggregate)
    payload = compile_shard_fault_isolated(
        market,
        shard_index=args.shard_index,
        shard_count=args.shard_count,
        observed_at=args.observed_at,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "records": len(payload["records"]),
                "route_rejections": payload["route_rejections"],
                "outbound": payload["outbound"],
                "send_allowed": payload["send_allowed"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
