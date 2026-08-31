from __future__ import annotations

from typing import Any, Mapping

from .application_adversarial_v31 import SCHEMA_VERSION as AAG_SCHEMA_VERSION
from .application_learning_v31 import build_vacancy_first_seed
from .application_wave_v31 import compile_top_resolved_vacancy_seeds_v31

SCHEMA_VERSION = "APPLICATION-WAVE-3.2"


def compile_top_resolved_vacancy_seeds(
    market_aggregate: Mapping[str, Any],
    vacancy_detail: Mapping[str, Any],
    *,
    limit: int = 25,
) -> dict[str, Any]:
    """Compile V3.1 signal-quality output into an AAG-3.1-bound public shortlist."""
    result = dict(
        compile_top_resolved_vacancy_seeds_v31(
            market_aggregate,
            vacancy_detail,
            limit=limit,
        )
    )
    selected: list[dict[str, Any]] = []
    for source_seed in result.get("selected") or []:
        seed = dict(source_seed)
        role = str(seed.get("target_role") or "").strip()
        if not role:
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

    result.update(
        {
            "schema_version": SCHEMA_VERSION,
            "selected_count": len(selected),
            "selected": selected,
            "application_adversarial_gate_required": AAG_SCHEMA_VERSION,
            "private_packet_compiler_required": "APPLICATION-PRIVATE-PACKET-3.1",
            "selection_policy": (
                "V31_SIGNAL_QUALITY_AND_OWNER_QUARANTINE_THEN_AAG31_BOUND_NO_SEND_SHORTLIST"
            ),
            "application_ready_no_send": 0,
            "final_send_ready": False,
            "outbound": "CLOSED",
            "send_allowed": 0,
        }
    )
    return result
