from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any, Mapping

from .v2_kernel import stable_digest

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_REQUIRED_CHECKPOINTS = (
    "CP7",
    "CP8",
    "CP9",
    "CP10",
    "CP11",
    "CP12",
    "CP13",
)
_REQUIRED_WORKFLOWS = (
    "repo-guard",
    "graph-v2-guard",
    "graph-v2-runtime-drills",
    "graph-v2-empirical-qualification",
    "graph-v2-migration-shadow",
)
_REQUIRED_PERSISTENCE_SURFACES = ("GITHUB", "LIBRARY", "DRIVE")
_EXPECTED_CHECKPOINT_STATES = {
    "CP7": "VERIFIED_FOR_DECLARED_SCOPE",
    "CP8": "VERIFIED_FOR_DECLARED_SCOPE",
    "CP9": "VERIFIED_FOR_DECLARED_SCOPE",
    "CP10": "VERIFIED_FOR_DECLARED_SCOPE",
    "CP11": "VERIFIED_FOR_DECLARED_SCOPE",
    "CP12": "VERIFIED_FOR_DECLARED_SCOPE",
    "CP13": "SHADOW_PARITY_VERIFIED",
}
_FEATURE_MODE = "ENFORCED_FOR_NEW_MATERIAL_WAVES"
_COMPATIBILITY_MODE = "LEGACY_DOMAIN_AUTHORITY_PRESERVED"
_ADOPTION_SCOPE = "COORDINATION_CAUSAL_HISTORY_CONTEXTPACK_ASSURANCE"


class AdoptionGateError(ValueError):
    pass


def _required_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AdoptionGateError(f"{label} must be a non-empty string")
    return value.strip()


def _required_bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise AdoptionGateError(f"{label} must be a JSON boolean")
    return value


def _required_nonnegative_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise AdoptionGateError(f"{label} must be a non-negative integer")
    return value


def _required_sha256(value: object, label: str) -> str:
    text = _required_string(value, label)
    if not _SHA256_RE.fullmatch(text):
        raise AdoptionGateError(f"{label} must be a lowercase SHA-256")
    return text


def _required_git_sha(value: object, label: str) -> str:
    text = _required_string(value, label)
    if not _GIT_SHA_RE.fullmatch(text):
        raise AdoptionGateError(f"{label} must be a lowercase Git SHA")
    return text


def _required_time(value: object, label: str) -> str:
    text = _required_string(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AdoptionGateError(f"{label} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise AdoptionGateError(f"{label} must include a timezone")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class CheckpointEvidence:
    checkpoint_id: str
    state: str
    commit_sha: str
    artifact_sha256: str
    evidence_ref: str
    scope: str
    ancestor_verified: bool
    lineage_evidence_ref: str
    authority_advanced: bool
    h_id_allocations: int
    outbound_opened: bool
    send_allowed: int

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "CheckpointEvidence":
        if not isinstance(payload, Mapping):
            raise AdoptionGateError("checkpoint evidence must be a mapping")
        item = cls(
            checkpoint_id=_required_string(payload.get("checkpoint_id"), "checkpoint_id"),
            state=_required_string(payload.get("state"), "checkpoint state"),
            commit_sha=_required_git_sha(payload.get("commit_sha"), "checkpoint commit_sha"),
            artifact_sha256=_required_sha256(payload.get("artifact_sha256"), "checkpoint artifact_sha256"),
            evidence_ref=_required_string(payload.get("evidence_ref"), "checkpoint evidence_ref"),
            scope=_required_string(payload.get("scope"), "checkpoint scope"),
            ancestor_verified=_required_bool(payload.get("ancestor_verified"), "checkpoint ancestor_verified"),
            lineage_evidence_ref=_required_string(payload.get("lineage_evidence_ref"), "checkpoint lineage_evidence_ref"),
            authority_advanced=_required_bool(payload.get("authority_advanced"), "checkpoint authority_advanced"),
            h_id_allocations=_required_nonnegative_int(payload.get("h_id_allocations"), "checkpoint h_id_allocations"),
            outbound_opened=_required_bool(payload.get("outbound_opened"), "checkpoint outbound_opened"),
            send_allowed=_required_nonnegative_int(payload.get("send_allowed"), "checkpoint send_allowed"),
        )
        item.validate()
        return item

    def validate(self) -> None:
        if self.checkpoint_id not in _EXPECTED_CHECKPOINT_STATES:
            raise AdoptionGateError(f"unexpected checkpoint evidence: {self.checkpoint_id}")
        if self.state != _EXPECTED_CHECKPOINT_STATES[self.checkpoint_id]:
            raise AdoptionGateError(
                f"{self.checkpoint_id} state {self.state!r} does not satisfy adoption"
            )
        if not self.ancestor_verified:
            raise AdoptionGateError(f"{self.checkpoint_id} commit ancestry is unverified")
        if self.authority_advanced or self.h_id_allocations != 0:
            raise AdoptionGateError(f"{self.checkpoint_id} evidence mutated domain authority")
        if self.outbound_opened or self.send_allowed != 0:
            raise AdoptionGateError(f"{self.checkpoint_id} evidence violated outbound lock")

    def to_dict(self) -> dict[str, object]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "state": self.state,
            "commit_sha": self.commit_sha,
            "artifact_sha256": self.artifact_sha256,
            "evidence_ref": self.evidence_ref,
            "scope": self.scope,
            "ancestor_verified": self.ancestor_verified,
            "lineage_evidence_ref": self.lineage_evidence_ref,
            "authority_advanced": False,
            "h_id_allocations": 0,
            "outbound_opened": False,
            "send_allowed": 0,
        }


@dataclass(frozen=True)
class WorkflowEvidence:
    name: str
    state: str
    commit_sha: str
    run_id: str
    evidence_ref: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "WorkflowEvidence":
        if not isinstance(payload, Mapping):
            raise AdoptionGateError("workflow evidence must be a mapping")
        item = cls(
            name=_required_string(payload.get("name"), "workflow name"),
            state=_required_string(payload.get("state"), "workflow state"),
            commit_sha=_required_git_sha(payload.get("commit_sha"), "workflow commit_sha"),
            run_id=_required_string(payload.get("run_id"), "workflow run_id"),
            evidence_ref=_required_string(payload.get("evidence_ref"), "workflow evidence_ref"),
        )
        if item.state != "SUCCESS":
            raise AdoptionGateError(f"workflow {item.name} did not succeed")
        return item

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "state": self.state,
            "commit_sha": self.commit_sha,
            "run_id": self.run_id,
            "evidence_ref": self.evidence_ref,
        }


@dataclass(frozen=True)
class PersistenceReceipt:
    surface: str
    state: str
    artifact_set_sha256: str
    evidence_ref: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "PersistenceReceipt":
        if not isinstance(payload, Mapping):
            raise AdoptionGateError("persistence receipt must be a mapping")
        item = cls(
            surface=_required_string(payload.get("surface"), "persistence surface"),
            state=_required_string(payload.get("state"), "persistence state"),
            artifact_set_sha256=_required_sha256(payload.get("artifact_set_sha256"), "persistence artifact_set_sha256"),
            evidence_ref=_required_string(payload.get("evidence_ref"), "persistence evidence_ref"),
        )
        if item.surface not in _REQUIRED_PERSISTENCE_SURFACES:
            raise AdoptionGateError(f"unexpected persistence surface: {item.surface}")
        if item.state != "VERIFIED":
            raise AdoptionGateError(f"persistence surface {item.surface} is not verified")
        return item

    def to_dict(self) -> dict[str, str]:
        return {
            "surface": self.surface,
            "state": self.state,
            "artifact_set_sha256": self.artifact_set_sha256,
            "evidence_ref": self.evidence_ref,
        }


@dataclass(frozen=True)
class AdoptionCandidate:
    current_main_sha: str
    authority_epoch: str
    authority_manifest_sha256: str
    state_pointer_sha256: str
    next_pointer_sha256: str
    observed_at: str
    feature_mode: str
    compatibility_mode: str
    adoption_scope: str
    domain_authority_preserved: bool
    rollback_verified: bool
    cp_evidence: tuple[CheckpointEvidence, ...]
    workflow_evidence: tuple[WorkflowEvidence, ...]
    persistence_receipts: tuple[PersistenceReceipt, ...]
    active_conflicting_write_claims: tuple[Mapping[str, object], ...]
    open_conflicting_prs: tuple[Mapping[str, object], ...]
    crm_universe_complete: bool
    outbound: str
    send_allowed: int
    authority_advance_allowed: bool
    canonical_id_allocation_allowed: bool
    outbound_allowed: bool

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "AdoptionCandidate":
        if not isinstance(payload, Mapping):
            raise AdoptionGateError("adoption candidate must be a mapping")
        cp_raw = payload.get("cp_evidence")
        workflow_raw = payload.get("workflow_evidence")
        persistence_raw = payload.get("persistence_receipts")
        claims = payload.get("active_conflicting_write_claims", [])
        prs = payload.get("open_conflicting_prs", [])
        for label, value in (
            ("cp_evidence", cp_raw),
            ("workflow_evidence", workflow_raw),
            ("persistence_receipts", persistence_raw),
            ("active_conflicting_write_claims", claims),
            ("open_conflicting_prs", prs),
        ):
            if not isinstance(value, list) or not all(isinstance(item, Mapping) for item in value):
                raise AdoptionGateError(f"{label} must contain only mapping objects")
        candidate = cls(
            current_main_sha=_required_git_sha(payload.get("current_main_sha"), "current_main_sha"),
            authority_epoch=_required_string(payload.get("authority_epoch"), "authority_epoch"),
            authority_manifest_sha256=_required_sha256(payload.get("authority_manifest_sha256"), "authority_manifest_sha256"),
            state_pointer_sha256=_required_sha256(payload.get("state_pointer_sha256"), "state_pointer_sha256"),
            next_pointer_sha256=_required_sha256(payload.get("next_pointer_sha256"), "next_pointer_sha256"),
            observed_at=_required_time(payload.get("observed_at"), "observed_at"),
            feature_mode=_required_string(payload.get("feature_mode"), "feature_mode"),
            compatibility_mode=_required_string(payload.get("compatibility_mode"), "compatibility_mode"),
            adoption_scope=_required_string(payload.get("adoption_scope"), "adoption_scope"),
            domain_authority_preserved=_required_bool(payload.get("domain_authority_preserved"), "domain_authority_preserved"),
            rollback_verified=_required_bool(payload.get("rollback_verified"), "rollback_verified"),
            cp_evidence=tuple(CheckpointEvidence.from_mapping(item) for item in cp_raw),
            workflow_evidence=tuple(WorkflowEvidence.from_mapping(item) for item in workflow_raw),
            persistence_receipts=tuple(PersistenceReceipt.from_mapping(item) for item in persistence_raw),
            active_conflicting_write_claims=tuple(dict(item) for item in claims),
            open_conflicting_prs=tuple(dict(item) for item in prs),
            crm_universe_complete=_required_bool(payload.get("crm_universe_complete"), "crm_universe_complete"),
            outbound=_required_string(payload.get("outbound"), "outbound"),
            send_allowed=_required_nonnegative_int(payload.get("send_allowed"), "send_allowed"),
            authority_advance_allowed=_required_bool(payload.get("authority_advance_allowed"), "authority_advance_allowed"),
            canonical_id_allocation_allowed=_required_bool(payload.get("canonical_id_allocation_allowed"), "canonical_id_allocation_allowed"),
            outbound_allowed=_required_bool(payload.get("outbound_allowed"), "outbound_allowed"),
        )
        candidate.validate()
        return candidate

    def validate(self) -> None:
        if self.feature_mode != _FEATURE_MODE:
            raise AdoptionGateError("unsupported feature_mode")
        if self.compatibility_mode != _COMPATIBILITY_MODE:
            raise AdoptionGateError("domain authority compatibility mode is not preserved")
        if self.adoption_scope != _ADOPTION_SCOPE:
            raise AdoptionGateError("adoption scope is not the coordination-only V2 scope")
        if not self.domain_authority_preserved:
            raise AdoptionGateError("domain authority preservation is mandatory")
        if not self.rollback_verified:
            raise AdoptionGateError("rollback is not verified")
        if self.active_conflicting_write_claims:
            raise AdoptionGateError("active conflicting write claims block adoption")
        if self.open_conflicting_prs:
            raise AdoptionGateError("open conflicting PRs block adoption")
        if self.authority_advance_allowed:
            raise AdoptionGateError("candidate preauthorizes domain authority advancement")
        if self.canonical_id_allocation_allowed:
            raise AdoptionGateError("candidate preauthorizes H-ID allocation")
        if self.outbound_allowed or self.outbound != "CLOSED" or self.send_allowed != 0:
            raise AdoptionGateError("candidate violates outbound hard lock")

        checkpoint_ids = [item.checkpoint_id for item in self.cp_evidence]
        if len(checkpoint_ids) != len(set(checkpoint_ids)):
            raise AdoptionGateError("duplicate checkpoint evidence")
        if set(checkpoint_ids) != set(_REQUIRED_CHECKPOINTS):
            missing = sorted(set(_REQUIRED_CHECKPOINTS) - set(checkpoint_ids))
            extra = sorted(set(checkpoint_ids) - set(_REQUIRED_CHECKPOINTS))
            raise AdoptionGateError(
                f"checkpoint evidence set mismatch: missing={missing}, extra={extra}"
            )

        workflow_names = [item.name for item in self.workflow_evidence]
        if len(workflow_names) != len(set(workflow_names)):
            raise AdoptionGateError("duplicate workflow evidence")
        if set(workflow_names) != set(_REQUIRED_WORKFLOWS):
            missing = sorted(set(_REQUIRED_WORKFLOWS) - set(workflow_names))
            extra = sorted(set(workflow_names) - set(_REQUIRED_WORKFLOWS))
            raise AdoptionGateError(
                f"workflow evidence set mismatch: missing={missing}, extra={extra}"
            )
        for item in self.workflow_evidence:
            if item.commit_sha != self.current_main_sha:
                raise AdoptionGateError(
                    f"workflow {item.name} was not executed on current main"
                )

        surfaces = [item.surface for item in self.persistence_receipts]
        if len(surfaces) != len(set(surfaces)):
            raise AdoptionGateError("duplicate persistence receipt")
        if set(surfaces) != set(_REQUIRED_PERSISTENCE_SURFACES):
            missing = sorted(set(_REQUIRED_PERSISTENCE_SURFACES) - set(surfaces))
            extra = sorted(set(surfaces) - set(_REQUIRED_PERSISTENCE_SURFACES))
            raise AdoptionGateError(
                f"persistence surface mismatch: missing={missing}, extra={extra}"
            )

    def to_public_dict(self) -> dict[str, object]:
        return {
            "current_main_sha": self.current_main_sha,
            "authority_epoch": self.authority_epoch,
            "authority_manifest_sha256": self.authority_manifest_sha256,
            "state_pointer_sha256": self.state_pointer_sha256,
            "next_pointer_sha256": self.next_pointer_sha256,
            "observed_at": self.observed_at,
            "feature_mode": self.feature_mode,
            "compatibility_mode": self.compatibility_mode,
            "adoption_scope": self.adoption_scope,
            "domain_authority_preserved": self.domain_authority_preserved,
            "rollback_verified": self.rollback_verified,
            "checkpoint_evidence": [item.to_dict() for item in sorted(self.cp_evidence, key=lambda item: int(item.checkpoint_id[2:]))],
            "workflow_evidence": [item.to_dict() for item in sorted(self.workflow_evidence, key=lambda item: item.name)],
            "persistence_receipts": [item.to_dict() for item in sorted(self.persistence_receipts, key=lambda item: item.surface)],
            "active_conflicting_write_claim_count": 0,
            "open_conflicting_pr_count": 0,
            "crm_universe_complete": self.crm_universe_complete,
            "outbound": self.outbound,
            "send_allowed": self.send_allowed,
            "authority_advance_allowed": False,
            "canonical_id_allocation_allowed": False,
            "outbound_allowed": False,
        }


@dataclass(frozen=True)
class AdoptionEvaluation:
    state: str
    candidate_digest: str
    v2_coordination_authority_allowed: bool
    v2_coordination_authority_activated: bool
    activation_requirements: tuple[str, ...]
    rollback_requirements: tuple[str, ...]
    public_candidate: Mapping[str, object]
    domain_authority_mutated: bool = False
    h_id_allocations: int = 0
    outbound_opened: bool = False
    send_allowed: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": "GRAPH_V2_CP14_ADOPTION_EVALUATION_1",
            "state": self.state,
            "candidate_digest": self.candidate_digest,
            "v2_coordination_authority_allowed": self.v2_coordination_authority_allowed,
            "v2_coordination_authority_activated": self.v2_coordination_authority_activated,
            "activation_requirements": list(self.activation_requirements),
            "rollback_requirements": list(self.rollback_requirements),
            "candidate": dict(self.public_candidate),
            "domain_authority_mutated": self.domain_authority_mutated,
            "h_id_allocations": self.h_id_allocations,
            "outbound_opened": self.outbound_opened,
            "send_allowed": self.send_allowed,
        }


def evaluate_adoption(candidate: AdoptionCandidate) -> AdoptionEvaluation:
    public = candidate.to_public_dict()
    return AdoptionEvaluation(
        state="ADOPTION_ELIGIBLE",
        candidate_digest=stable_digest(public),
        v2_coordination_authority_allowed=True,
        v2_coordination_authority_activated=False,
        activation_requirements=(
            "branch activation changes from the evaluated current_main_sha or descendant",
            "update AGENTS and WOP bridge for new material waves",
            "update mutable STATE/NEXT with exact activation SHA after merge",
            "append adoption event and compile post-activation ContextPack",
            "run all V2 workflows on activation SHA",
            "persist exact adoption receipt to GitHub, Library and Drive",
            "execute one bounded compatibility-mode production wave",
        ),
        rollback_requirements=(
            "stop issuing new V2 leases",
            "release or expire active V2 claims",
            "retain append-only adoption and rollback events",
            "restore prior coordination feature flag",
            "retain all legacy domain authority stores unchanged",
            "rebuild ContextPack and NEXT",
        ),
        public_candidate=public,
    )


def build_activation_receipt(
    evaluation: AdoptionEvaluation,
    *,
    activation_sha: str,
    activated_at: str,
    agents_sha256: str,
    wop_sha256: str,
    state_sha256: str,
    next_sha256: str,
    adoption_event_hash: str,
    contextpack_digest: str,
    recovery_bundle_sha256: str,
    compatibility_wave_evidence_ref: str,
) -> dict[str, object]:
    if evaluation.state != "ADOPTION_ELIGIBLE":
        raise AdoptionGateError("evaluation is not adoption eligible")
    values = {
        "activation_sha": _required_git_sha(activation_sha, "activation_sha"),
        "activated_at": _required_time(activated_at, "activated_at"),
        "agents_sha256": _required_sha256(agents_sha256, "agents_sha256"),
        "wop_sha256": _required_sha256(wop_sha256, "wop_sha256"),
        "state_sha256": _required_sha256(state_sha256, "state_sha256"),
        "next_sha256": _required_sha256(next_sha256, "next_sha256"),
        "adoption_event_hash": _required_sha256(adoption_event_hash, "adoption_event_hash"),
        "contextpack_digest": _required_sha256(contextpack_digest, "contextpack_digest"),
        "recovery_bundle_sha256": _required_sha256(recovery_bundle_sha256, "recovery_bundle_sha256"),
        "compatibility_wave_evidence_ref": _required_string(compatibility_wave_evidence_ref, "compatibility_wave_evidence_ref"),
    }
    return {
        "schema_version": "GRAPH_V2_CP14_ACTIVATION_RECEIPT_1",
        "state": "ADOPTED_COORDINATION_ONLY",
        "candidate_digest": evaluation.candidate_digest,
        **values,
        "feature_mode": _FEATURE_MODE,
        "compatibility_mode": _COMPATIBILITY_MODE,
        "adoption_scope": _ADOPTION_SCOPE,
        "v2_coordination_authority_activated": True,
        "domain_authority_preserved": True,
        "domain_authority_mutated": False,
        "h_id_allocations": 0,
        "outbound_opened": False,
        "send_allowed": 0,
        "receipt_digest": stable_digest({"candidate_digest": evaluation.candidate_digest, **values}),
    }
