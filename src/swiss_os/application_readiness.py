from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping
from urllib.parse import urlsplit

from .application_adversarial_v31 import (
    HARD_GATE_EXPECTED as AAG31_HARD_GATES,
    SCHEMA_VERSION as AAG31_SCHEMA_VERSION,
)

SCHEMA_VERSION = "TARGET-BOUND-APPLICATION-READINESS-1.0"
READY_DECISIONS = frozenset({"APPLICATION_READY_NO_SEND", "ELITE_MATCH"})


def _canonical_sha256(value: Mapping[str, Any]) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _require_text(value: str | None, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field} required")
    return text


def _https_url(value: str) -> str:
    text = _require_text(value, "vacancy_source_url")
    parsed = urlsplit(text)
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        raise ValueError("vacancy_source_url must be absolute HTTPS")
    return text


def _validate_aag31(aag_receipt: Mapping[str, Any]) -> None:
    if aag_receipt.get("schema_version") != AAG31_SCHEMA_VERSION:
        raise ValueError("AAG-3.1 receipt required")
    if str(aag_receipt.get("decision") or "") not in READY_DECISIONS:
        raise ValueError("AAG-3.1 decision is not packet-ready")
    if aag_receipt.get("application_ready_no_send") is not True:
        raise ValueError("AAG-3.1 readiness flag mismatch")
    if aag_receipt.get("final_send_ready") is not False:
        raise ValueError("AAG-3.1 cannot preauthorize final send")
    if aag_receipt.get("outbound") != "CLOSED" or aag_receipt.get("send_allowed") != 0:
        raise ValueError("AAG-3.1 outbound safety mismatch")
    if aag_receipt.get("blockers"):
        raise ValueError("AAG-3.1 blockers present")

    hard = aag_receipt.get("hard_gates")
    if not isinstance(hard, Mapping):
        raise ValueError("AAG-3.1 hard-gate receipt missing")
    if hard.get("pass") is not True:
        raise ValueError("AAG-3.1 hard gates not terminal PASS")
    if hard.get("failures") or hard.get("unknown"):
        raise ValueError("AAG-3.1 hard gates contain failure/unknown")
    observed = hard.get("observed")
    if not isinstance(observed, Mapping):
        raise ValueError("AAG-3.1 observed hard gates missing")
    if set(observed) != set(AAG31_HARD_GATES):
        raise ValueError("AAG-3.1 hard-gate keyset mismatch")
    for gate, expected in AAG31_HARD_GATES.items():
        if observed.get(gate) is not expected:
            raise ValueError(f"AAG-3.1 hard gate not satisfied: {gate}")


@dataclass(frozen=True)
class TargetBoundReadinessReceipt:
    schema_version: str
    organization_id: str
    opportunity_id: str
    lane: str
    channel_id: str
    target_role: str
    vacancy_source_url: str
    aag_schema_version: str
    aag_decision: str
    aag_receipt_sha256: str
    hard_gate_count: int
    binding_sha256: str
    application_ready_no_send: bool
    final_send_ready: bool
    outbound: str
    send_allowed: int

    @classmethod
    def build(
        cls,
        *,
        organization_id: str,
        opportunity_id: str,
        lane: str,
        channel_id: str,
        target_role: str,
        vacancy_source_url: str,
        aag_receipt: Mapping[str, Any],
    ) -> "TargetBoundReadinessReceipt":
        _validate_aag31(aag_receipt)
        organization_id = _require_text(organization_id, "organization_id")
        opportunity_id = _require_text(opportunity_id, "opportunity_id")
        lane = _require_text(lane, "lane")
        channel_id = _require_text(channel_id, "channel_id")
        target_role = _require_text(target_role, "target_role")
        vacancy_source_url = _https_url(vacancy_source_url)
        aag_sha = _canonical_sha256(aag_receipt)
        target = {
            "organization_id": organization_id,
            "opportunity_id": opportunity_id,
            "lane": lane,
            "channel_id": channel_id,
            "target_role": target_role,
            "vacancy_source_url": vacancy_source_url,
            "aag_schema_version": AAG31_SCHEMA_VERSION,
            "aag_receipt_sha256": aag_sha,
        }
        binding_sha = _canonical_sha256(target)
        return cls(
            schema_version=SCHEMA_VERSION,
            organization_id=organization_id,
            opportunity_id=opportunity_id,
            lane=lane,
            channel_id=channel_id,
            target_role=target_role,
            vacancy_source_url=vacancy_source_url,
            aag_schema_version=AAG31_SCHEMA_VERSION,
            aag_decision=str(aag_receipt["decision"]),
            aag_receipt_sha256=aag_sha,
            hard_gate_count=len(AAG31_HARD_GATES),
            binding_sha256=binding_sha,
            application_ready_no_send=True,
            final_send_ready=False,
            outbound="CLOSED",
            send_allowed=0,
        )

    def validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("target-bound readiness schema mismatch")
        _require_text(self.organization_id, "organization_id")
        _require_text(self.opportunity_id, "opportunity_id")
        _require_text(self.lane, "lane")
        _require_text(self.channel_id, "channel_id")
        _require_text(self.target_role, "target_role")
        _https_url(self.vacancy_source_url)
        if self.aag_schema_version != AAG31_SCHEMA_VERSION:
            raise ValueError("target-bound readiness requires AAG-3.1")
        if self.aag_decision not in READY_DECISIONS:
            raise ValueError("target-bound readiness decision not ready")
        if self.hard_gate_count != len(AAG31_HARD_GATES):
            raise ValueError("target-bound readiness hard-gate count mismatch")
        for field, value in (
            ("aag_receipt_sha256", self.aag_receipt_sha256),
            ("binding_sha256", self.binding_sha256),
        ):
            if len(value) != 64 or any(c not in "0123456789abcdef" for c in value.lower()):
                raise ValueError(f"{field} must be SHA-256 hex")
        if self.application_ready_no_send is not True:
            raise ValueError("target-bound readiness flag must be true")
        if self.final_send_ready is not False or self.outbound != "CLOSED" or self.send_allowed != 0:
            raise ValueError("target-bound readiness cannot authorize outbound")

        expected_binding = _canonical_sha256({
            "organization_id": self.organization_id,
            "opportunity_id": self.opportunity_id,
            "lane": self.lane,
            "channel_id": self.channel_id,
            "target_role": self.target_role,
            "vacancy_source_url": self.vacancy_source_url,
            "aag_schema_version": self.aag_schema_version,
            "aag_receipt_sha256": self.aag_receipt_sha256,
        })
        if expected_binding != self.binding_sha256:
            raise ValueError("target-bound readiness binding hash mismatch")

    def validate_for_target(
        self,
        *,
        organization_id: str,
        opportunity_id: str | None,
        lane: str,
        channel_id: str,
    ) -> None:
        self.validate()
        if not opportunity_id:
            raise ValueError("W5.1 packet compilation requires an exact opportunity_id")
        expected = {
            "organization_id": organization_id,
            "opportunity_id": opportunity_id,
            "lane": lane,
            "channel_id": channel_id,
        }
        observed = {
            "organization_id": self.organization_id,
            "opportunity_id": self.opportunity_id,
            "lane": self.lane,
            "channel_id": self.channel_id,
        }
        mismatches = [key for key in expected if expected[key] != observed[key]]
        if mismatches:
            raise ValueError(f"readiness target mismatch: {mismatches[0]}")

    def public_safe_receipt(self) -> dict[str, object]:
        self.validate()
        return {
            "schema_version": self.schema_version,
            "organization_id": self.organization_id,
            "opportunity_id": self.opportunity_id,
            "lane": self.lane,
            "channel_id": self.channel_id,
            "target_role": self.target_role,
            "vacancy_source_url": self.vacancy_source_url,
            "aag_schema_version": self.aag_schema_version,
            "aag_decision": self.aag_decision,
            "aag_receipt_sha256": self.aag_receipt_sha256,
            "hard_gate_count": self.hard_gate_count,
            "binding_sha256": self.binding_sha256,
            "application_ready_no_send": True,
            "final_send_ready": False,
            "outbound": "CLOSED",
            "send_allowed": 0,
        }
