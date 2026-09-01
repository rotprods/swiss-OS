from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import sqlite3
from typing import Iterable

from .candidate_assets import AssetManifest
from .candidate_truth import CandidateField, LaneGateResult, evaluate_lane

LANE_PRIMARY_ASSET_TYPE = {
    "ENTRY": "CV_ENTRY",
    "PORTAL": "CV_ENTRY",
    "HYBRID": "CV_HYBRID",
    "CREATIVE": "CV_CREATIVE",
}

ASSET_FIELD_BY_TYPE = {
    "CV_ENTRY": "asset.cv",
    "CV_HYBRID": "asset.cv",
    "CV_CREATIVE": "asset.cv",
    "PORTFOLIO": "asset.portfolio",
    "CASE_STUDY": "asset.case_studies",
}


@dataclass(frozen=True)
class PacketCompileRequest:
    organization_id: str
    lane: str
    candidate_fields: tuple[CandidateField, ...]
    assets: tuple[AssetManifest, ...]
    channel_id: str
    opportunity_id: str | None = None

    def validate(self) -> None:
        if self.lane not in LANE_PRIMARY_ASSET_TYPE:
            raise ValueError(f"unknown lane: {self.lane}")
        if not self.organization_id.strip():
            raise ValueError("organization_id required")
        if not self.channel_id.strip():
            raise ValueError("channel_id required")
        for field in self.candidate_fields:
            field.validate()
        for asset in self.assets:
            asset.validate()


@dataclass(frozen=True)
class CompiledApplicationPacket:
    packet_id: str
    application_id: str
    organization_id: str
    opportunity_id: str | None
    lane: str
    selected_asset_manifest_id: str
    selected_channel_id: str
    supplemental_asset_ids: tuple[str, ...]
    idempotency_key: str
    gate: LaneGateResult

    def public_safe_receipt(self) -> dict[str, object]:
        return {
            "packet_id": self.packet_id,
            "application_id": self.application_id,
            "organization_id": self.organization_id,
            "opportunity_present": self.opportunity_id is not None,
            "lane": self.lane,
            "selected_asset_manifest_id": self.selected_asset_manifest_id,
            "selected_channel_id": self.selected_channel_id,
            "supplemental_asset_count": len(self.supplemental_asset_ids),
            "idempotency_key": self.idempotency_key,
            "gate_ready": self.gate.ready,
        }


def _hash(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _synthesized_asset_fields(assets: Iterable[AssetManifest]) -> tuple[CandidateField, ...]:
    by_field: dict[str, bool] = {}
    for asset in assets:
        field_key = ASSET_FIELD_BY_TYPE.get(asset.asset_type)
        if field_key is None:
            continue
        by_field[field_key] = by_field.get(field_key, False) or asset.approved
    return tuple(
        CandidateField(
            key=key,
            truth_state="VERIFIED" if approved else "UNKNOWN",
            approved=approved,
            external_allowed=approved,
            private_reference=True,
        )
        for key, approved in sorted(by_field.items())
    )


def _select_primary_asset(lane: str, assets: Iterable[AssetManifest]) -> AssetManifest:
    required_type = LANE_PRIMARY_ASSET_TYPE[lane]
    candidates = [a for a in assets if a.asset_type == required_type and a.approved]
    if not candidates:
        raise ValueError(f"no approved {required_type} asset for lane {lane}")
    if len(candidates) != 1:
        ids = ",".join(sorted(a.asset_id for a in candidates))
        raise ValueError(f"ambiguous approved primary assets for lane {lane}: {ids}")
    return candidates[0]


def _supplemental_assets(lane: str, assets: Iterable[AssetManifest]) -> tuple[AssetManifest, ...]:
    required = ("PORTFOLIO", "CASE_STUDY") if lane in {"HYBRID", "CREATIVE"} else ()
    selected: list[AssetManifest] = []
    for asset_type in required:
        matches = [a for a in assets if a.asset_type == asset_type and a.approved]
        if len(matches) != 1:
            raise ValueError(f"expected exactly one approved {asset_type} for lane {lane}")
        selected.append(matches[0])
    return tuple(selected)


def _application_identity(request: PacketCompileRequest) -> str:
    # Stable across asset revisions: replacing a CV must never authorize a duplicate application.
    return _hash({
        "organization_id": request.organization_id,
        "opportunity_id": request.opportunity_id or "",
        "lane": request.lane,
        "channel_id": request.channel_id,
    })


def _asset_identity(asset: AssetManifest) -> dict[str, object]:
    return {
        "asset_id": asset.asset_id,
        "asset_type": asset.asset_type,
        "version": asset.version,
        "content_sha256": asset.content_sha256 or "",
    }


def compile_packet(request: PacketCompileRequest) -> CompiledApplicationPacket:
    request.validate()
    gate = evaluate_lane(request.lane, tuple(request.candidate_fields) + _synthesized_asset_fields(request.assets))
    if not gate.ready:
        raise ValueError(f"lane gate blocked: missing={','.join(gate.missing)} blocked={','.join(gate.blocked)}")

    primary = _select_primary_asset(request.lane, request.assets)
    supplements = _supplemental_assets(request.lane, request.assets)
    application_hash = _application_identity(request)
    packet_hash = _hash({
        "application_key": application_hash,
        "primary": _asset_identity(primary),
        "supplements": [_asset_identity(a) for a in supplements],
    })

    return CompiledApplicationPacket(
        packet_id=f"PKT-{packet_hash[:20]}",
        application_id=f"APP-{application_hash[:20]}",
        organization_id=request.organization_id,
        opportunity_id=request.opportunity_id,
        lane=request.lane,
        selected_asset_manifest_id=primary.asset_id,
        selected_channel_id=request.channel_id,
        supplemental_asset_ids=tuple(a.asset_id for a in supplements),
        idempotency_key=application_hash,
        gate=gate,
    )


def persist_application(
    conn: sqlite3.Connection,
    packet: CompiledApplicationPacket,
    *,
    created_at: str,
    state: str = "PACKET_COMPILED",
) -> bool:
    """Persist application metadata only; this function never sends or renders content."""
    existing = conn.execute(
        "SELECT application_id FROM applications_v2 WHERE idempotency_key=?",
        (packet.idempotency_key,),
    ).fetchone()
    if existing:
        if existing[0] != packet.application_id:
            raise ValueError("idempotency collision with different application_id")
        return False

    conn.execute(
        """INSERT INTO applications_v2(
             application_id, opportunity_id, organization_id, lane, state,
             selected_asset_manifest_id, selected_channel_id, idempotency_key, created_at
           ) VALUES(?,?,?,?,?,?,?,?,?)""",
        (
            packet.application_id,
            packet.opportunity_id,
            packet.organization_id,
            packet.lane,
            state,
            packet.selected_asset_manifest_id,
            packet.selected_channel_id,
            packet.idempotency_key,
            created_at,
        ),
    )
    return True
