from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


SCHEMA_VERSION = "NPP-1.0"


@dataclass(frozen=True)
class NextPointer:
    project: str
    generated_at: str
    cycle_id: str
    parent_git_sha: str
    authority_epoch: str
    authority_parent: str
    execution_mode: str
    selected_route: str
    next_route: str
    goal_id: str
    checkpoint_id: str
    graph_impact: str
    hard_blockers: tuple[str, ...] = field(default_factory=tuple)
    dependencies: tuple[str, ...] = field(default_factory=tuple)
    required_inputs: tuple[str, ...] = field(default_factory=tuple)
    capabilities_required: tuple[str, ...] = field(default_factory=tuple)
    artifacts: tuple[str, ...] = field(default_factory=tuple)
    resume_instructions: tuple[str, ...] = field(default_factory=tuple)
    done_when: tuple[str, ...] = field(default_factory=tuple)
    authority_advance_allowed: bool = False
    canonical_id_allocation_allowed: bool = False
    outbound_allowed: bool = False
    schema_version: str = SCHEMA_VERSION

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        required = {
            "project": self.project,
            "generated_at": self.generated_at,
            "cycle_id": self.cycle_id,
            "parent_git_sha": self.parent_git_sha,
            "authority_epoch": self.authority_epoch,
            "authority_parent": self.authority_parent,
            "execution_mode": self.execution_mode,
            "selected_route": self.selected_route,
            "next_route": self.next_route,
            "goal_id": self.goal_id,
            "checkpoint_id": self.checkpoint_id,
            "graph_impact": self.graph_impact,
        }
        for key, value in required.items():
            if not str(value).strip():
                errors.append(f"missing required NEXT field: {key}")
        if self.schema_version != SCHEMA_VERSION:
            errors.append(f"unsupported schema_version: {self.schema_version}")
        if self.graph_impact not in {"NONE", "META", "OPERATIONAL", "BOTH"}:
            errors.append(f"invalid graph_impact: {self.graph_impact}")

        # NEXT is resumable state, never authority or authorization. Future runs
        # must independently reconstruct/revalidate all three gates.
        if self.authority_advance_allowed:
            errors.append("NEXT pointer cannot pre-authorize authority advancement")
        if self.canonical_id_allocation_allowed:
            errors.append("NEXT pointer cannot pre-authorize canonical ID allocation")
        if self.outbound_allowed:
            errors.append("NEXT pointer cannot pre-authorize outbound")
        return tuple(errors)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "project": self.project,
            "generated_at": self.generated_at,
            "cycle_id": self.cycle_id,
            "parent_git_sha": self.parent_git_sha,
            "authority_epoch": self.authority_epoch,
            "authority_parent": self.authority_parent,
            "execution_mode": self.execution_mode,
            "selected_route": self.selected_route,
            "next_route": self.next_route,
            "goal_id": self.goal_id,
            "checkpoint_id": self.checkpoint_id,
            "hard_blockers": list(self.hard_blockers),
            "dependencies": list(self.dependencies),
            "required_inputs": list(self.required_inputs),
            "capabilities_required": list(self.capabilities_required),
            "artifacts": list(self.artifacts),
            "graph_impact": self.graph_impact,
            "authority_advance_allowed": self.authority_advance_allowed,
            "canonical_id_allocation_allowed": self.canonical_id_allocation_allowed,
            "outbound_allowed": self.outbound_allowed,
            "resume_instructions": list(self.resume_instructions),
            "done_when": list(self.done_when),
        }

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "NextPointer":
        allowed = set(cls.__dataclass_fields__)
        unknown = sorted(set(payload) - allowed)
        if unknown:
            raise ValueError(f"unknown NEXT pointer keys: {', '.join(unknown)}")

        tuple_fields = {
            "hard_blockers",
            "dependencies",
            "required_inputs",
            "capabilities_required",
            "artifacts",
            "resume_instructions",
            "done_when",
        }
        boolean_fields = {
            "authority_advance_allowed",
            "canonical_id_allocation_allowed",
            "outbound_allowed",
        }
        kwargs: dict[str, Any] = {}
        for key, value in payload.items():
            if key in tuple_fields:
                if not isinstance(value, (list, tuple)):
                    raise ValueError(f"NEXT field {key} must be an array")
                kwargs[key] = tuple(str(item) for item in value)
            elif key in boolean_fields:
                if not isinstance(value, bool):
                    raise ValueError(f"NEXT field {key} must be a JSON boolean")
                kwargs[key] = value
            else:
                kwargs[key] = str(value)
        pointer = cls(**kwargs)
        errors = pointer.validate()
        if errors:
            raise ValueError("; ".join(errors))
        return pointer
