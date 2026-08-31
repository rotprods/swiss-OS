from __future__ import annotations

import re
from typing import Any, Mapping

from .application_adversarial_v31 import SCHEMA_VERSION as AAG_SCHEMA_VERSION
from .application_learning_v31 import build_vacancy_first_seed
from .application_wave_v31 import compile_top_resolved_vacancy_seeds_v31

SCHEMA_VERSION = "APPLICATION-WAVE-3.2"

# V3.1 already removes broad navigation, departments and non-joblike links. This
# final shortlist-only guard catches labels observed in the real 436-hotel replay
# that still have occupational vocabulary but are not an exact vacancy title.
EXACT_ROLE_SHORTLIST_EXCLUSION_RE = re.compile(
    r"^(?:services?|service links|social media|praktika|"
    r"lehre und praktikum(?: im .*)?|du bist student(?:\*in)? .*|"
    r"wir bieten.*|was wir bieten.*)$",
    re.I,
)


def compile_top_resolved_vacancy_seeds(
    market_aggregate: Mapping[str, Any],
    vacancy_detail: Mapping[str, Any],
    *,
    limit: int = 25,
) -> dict[str, Any]:
    """Compile V3.1 quality output into an AAG-3.1-bound public shortlist.

    The V3.1 compiler is intentionally asked for a much larger ranked pool so that
    shortlist-only exact-role exclusions can be removed and backfilled instead of
    shrinking a nominal top-25 without replacement.
    """
    scan_limit = max(500, limit * 20)
    result = dict(
        compile_top_resolved_vacancy_seeds_v31(
            market_aggregate,
            vacancy_detail,
            limit=scan_limit,
        )
    )
    selected: list[dict[str, Any]] = []
    shortlist_rejected: list[dict[str, str]] = []
    for source_seed in result.get("selected") or []:
        seed = dict(source_seed)
        role = re.sub(r"\s+", " ", str(seed.get("target_role") or "").strip())
        if not role:
            continue
        if EXACT_ROLE_SHORTLIST_EXCLUSION_RE.match(role):
            shortlist_rejected.append(
                {
                    "record_id": str(seed.get("record_id") or ""),
                    "target_role": role,
                    "reason": "SHORTLIST_LABEL_NOT_EXACT_ROLE",
                }
            )
            continue
        careers = list(seed.get("careers_routes") or [])
        strategy = build_vacancy_first_seed(
            {"name": seed.get("hotel_name"), "city": seed.get("city")},
            [{"title": role, "source_url": seed.get("vacancy_source_url")}],
            careers[0] if careers else None,
        )
        seed["strategy"] = strategy
        seed["application_adversarial_gate_required"] = AAG_SCHEMA_VERSION
        seed["private_packet_compiler_required"] = "APPLICATION-PRIVATE-PACKET-3.1"
        seed["application_ready_no_send"] = False
        seed["final_send_ready"] = False
        seed["outbound"] = "CLOSED"
        seed["send_allowed"] = 0
        selected.append(seed)
        if len(selected) >= limit:
            break

    result.update(
        {
            "schema_version": SCHEMA_VERSION,
            "requested_limit": limit,
            "v31_ranked_pool_scanned": min(scan_limit, int(result.get("primary_vacancy_candidate_count") or 0)),
            "shortlist_exact_role_rejected_count": len(shortlist_rejected),
            "shortlist_exact_role_rejections": shortlist_rejected,
            "selected_count": len(selected),
            "selected": selected,
            "application_adversarial_gate_required": AAG_SCHEMA_VERSION,
            "private_packet_compiler_required": "APPLICATION-PRIVATE-PACKET-3.1",
            "selection_policy": (
                "V31_SIGNAL_QUALITY_AND_OWNER_QUARANTINE_THEN_EXACT_ROLE_BACKFILL_THEN_AAG31_NO_SEND"
            ),
            "application_ready_no_send": 0,
            "final_send_ready": False,
            "outbound": "CLOSED",
            "send_allowed": 0,
        }
    )
    return result
