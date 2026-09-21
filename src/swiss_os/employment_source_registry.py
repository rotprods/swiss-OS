from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit


SURFACE_TYPES = frozenset({
    "OFFICIAL_PUBLIC_INVENTORY",
    "EMPLOYER_FIRST_PARTY",
    "STAFFING_AGENCY",
    "NATIONAL_JOB_BOARD",
    "SECTOR_JOB_BOARD",
    "SECONDARY_AGGREGATOR",
    "GUIDANCE_SURFACE",
    "PUBLICATION_API",
})
AUTOMATION_POLICIES = frozenset({
    "AUTHORIZED",
    "PROHIBITED",
    "UNKNOWN_REQUIRES_REVIEW",
})
CAPTURE_MODES = frozenset({
    "MANUAL_WEB",
    "SEARCH_ENGINE_DISCOVERY",
    "OFFICIAL_READ_API",
    "FIXTURE_ONLY",
    "BLOCKED",
})
AUTOMATED_CAPTURE_MODES = frozenset({"OFFICIAL_READ_API"})
CANONICALITY = frozenset({
    "PRIMARY_EMPLOYER",
    "PRIMARY_PUBLIC_RECORD",
    "DISCOVERY",
    "SECONDARY_DISCOVERY",
    "POLICY_GUIDANCE",
    "PUBLICATION_ONLY",
})
API_ROLES = frozenset({"NONE", "READ_INVENTORY", "PUBLICATION_ONLY"})


def _require_https(value: str, label: str) -> None:
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"{label} must be an absolute https URL")


@dataclass(frozen=True)
class SourceFamily:
    source_family_id: str
    name: str
    provider: str

    def validate(self) -> None:
        if not self.source_family_id.startswith("FAM-"):
            raise ValueError("source_family_id must use FAM-*")
        if not self.name.strip() or not self.provider.strip():
            raise ValueError("source family name/provider are required")


@dataclass(frozen=True)
class SourceSurface:
    source_id: str
    source_family_id: str
    name: str
    canonical_url: str
    surface_type: str
    scope: str
    languages: tuple[str, ...]
    niche_ids: tuple[str, ...]
    inventory_role: bool
    automation_policy: str
    capture_modes: tuple[str, ...]
    canonicality: str
    observed_at: str
    evidence_refs: tuple[str, ...]
    api_role: str = "NONE"

    def validate(self) -> None:
        if not self.source_id.startswith("SRC-"):
            raise ValueError("source_id must use SRC-*")
        if not self.source_family_id.startswith("FAM-"):
            raise ValueError("source_family_id must use FAM-*")
        if not self.name.strip() or not self.scope.strip():
            raise ValueError("surface name/scope are required")
        _require_https(self.canonical_url, "canonical_url")
        if self.surface_type not in SURFACE_TYPES:
            raise ValueError(f"unknown surface_type: {self.surface_type}")
        if self.automation_policy not in AUTOMATION_POLICIES:
            raise ValueError(f"unknown automation_policy: {self.automation_policy}")
        if self.canonicality not in CANONICALITY:
            raise ValueError(f"unknown canonicality: {self.canonicality}")
        if self.api_role not in API_ROLES:
            raise ValueError(f"unknown api_role: {self.api_role}")
        if not self.capture_modes:
            raise ValueError("at least one capture mode is required")
        unknown_modes = set(self.capture_modes) - CAPTURE_MODES
        if unknown_modes:
            raise ValueError(f"unknown capture modes: {sorted(unknown_modes)}")
        if self.surface_type in {"GUIDANCE_SURFACE", "PUBLICATION_API"} and self.inventory_role:
            raise ValueError(f"{self.surface_type} cannot be vacancy inventory")
        if self.surface_type == "PUBLICATION_API" and self.api_role != "PUBLICATION_ONLY":
            raise ValueError("PUBLICATION_API must declare api_role PUBLICATION_ONLY")
        if self.api_role == "READ_INVENTORY" and "OFFICIAL_READ_API" not in self.capture_modes:
            raise ValueError("READ_INVENTORY API role requires OFFICIAL_READ_API capture mode")
        if self.automation_policy != "AUTHORIZED" and set(self.capture_modes) & AUTOMATED_CAPTURE_MODES:
            raise ValueError("automated capture requires explicit AUTHORIZED policy")
        if self.automation_policy == "PROHIBITED" and "BLOCKED" not in self.capture_modes:
            allowed = {"MANUAL_WEB", "SEARCH_ENGINE_DISCOVERY"}
            if not set(self.capture_modes).issubset(allowed):
                raise ValueError("prohibited automation may only use manual/search discovery or BLOCKED")
        if not self.observed_at.endswith("Z"):
            raise ValueError("observed_at must be an explicit UTC timestamp")
        if not self.evidence_refs:
            raise ValueError("at least one evidence ref is required")
        for ref in self.evidence_refs:
            _require_https(ref, "evidence_ref")
        if len(set(self.languages)) != len(self.languages):
            raise ValueError("duplicate language")
        if len(set(self.niche_ids)) != len(self.niche_ids):
            raise ValueError("duplicate niche_id")


@dataclass(frozen=True)
class DiscoveryProgram:
    program_id: str
    name: str
    purpose: str
    seed_surface_ids: tuple[str, ...]

    def validate(self) -> None:
        if not self.program_id.startswith("DP-"):
            raise ValueError("program_id must use DP-*")
        if self.purpose != "DISCOVERY_ONLY":
            raise ValueError("DiscoveryProgram is never an inventory surface")
        if not self.name.strip():
            raise ValueError("discovery program name required")


@dataclass(frozen=True)
class GuidanceSurface:
    guidance_id: str
    source_id: str
    topics: tuple[str, ...]

    def validate(self) -> None:
        if not self.guidance_id.startswith("GS-"):
            raise ValueError("guidance_id must use GS-*")
        if not self.source_id.startswith("SRC-") or not self.topics:
            raise ValueError("guidance source/topics are required")


@dataclass(frozen=True)
class Registry:
    families: tuple[SourceFamily, ...]
    surfaces: tuple[SourceSurface, ...]
    discovery_programs: tuple[DiscoveryProgram, ...]
    guidance_surfaces: tuple[GuidanceSurface, ...]


def _tuple_strings(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field} must be a list of strings")
    return tuple(value)


def validate_registry(payload: Mapping[str, Any]) -> Registry:
    if payload.get("schema_version") != "EMPLOYMENT-SOURCE-REGISTRY-1.0":
        raise ValueError("unexpected source registry schema")
    if payload.get("claim_national_completeness") is not False:
        raise ValueError("registry must never claim national completeness")
    if payload.get("outbound") != "CLOSED" or payload.get("send_allowed") != 0:
        raise ValueError("source registry cannot authorize outbound")

    families = tuple(
        SourceFamily(
            source_family_id=item["source_family_id"],
            name=item["name"],
            provider=item["provider"],
        )
        for item in payload.get("source_families", [])
    )
    surfaces = tuple(
        SourceSurface(
            source_id=item["source_id"],
            source_family_id=item["source_family_id"],
            name=item["name"],
            canonical_url=item["canonical_url"],
            surface_type=item["surface_type"],
            scope=item["scope"],
            languages=_tuple_strings(item.get("languages", []), "languages"),
            niche_ids=_tuple_strings(item.get("niche_ids", []), "niche_ids"),
            inventory_role=item["inventory_role"],
            automation_policy=item["automation_policy"],
            capture_modes=_tuple_strings(item.get("capture_modes", []), "capture_modes"),
            canonicality=item["canonicality"],
            observed_at=item["observed_at"],
            evidence_refs=_tuple_strings(item.get("evidence_refs", []), "evidence_refs"),
            api_role=item.get("api_role", "NONE"),
        )
        for item in payload.get("source_surfaces", [])
    )
    programs = tuple(
        DiscoveryProgram(
            program_id=item["program_id"],
            name=item["name"],
            purpose=item["purpose"],
            seed_surface_ids=_tuple_strings(item.get("seed_surface_ids", []), "seed_surface_ids"),
        )
        for item in payload.get("discovery_programs", [])
    )
    guidance = tuple(
        GuidanceSurface(
            guidance_id=item["guidance_id"],
            source_id=item["source_id"],
            topics=_tuple_strings(item.get("topics", []), "topics"),
        )
        for item in payload.get("guidance_surfaces", [])
    )

    for item in (*families, *surfaces, *programs, *guidance):
        item.validate()

    family_ids = [item.source_family_id for item in families]
    source_ids = [item.source_id for item in surfaces]
    program_ids = [item.program_id for item in programs]
    guidance_ids = [item.guidance_id for item in guidance]
    for label, values in (
        ("source_family_id", family_ids),
        ("source_id", source_ids),
        ("program_id", program_ids),
        ("guidance_id", guidance_ids),
    ):
        if len(values) != len(set(values)):
            raise ValueError(f"duplicate {label}")

    known_families = set(family_ids)
    known_sources = set(source_ids)
    surface_by_id = {item.source_id: item for item in surfaces}
    for surface in surfaces:
        if surface.source_family_id not in known_families:
            raise ValueError(f"unknown source family: {surface.source_family_id}")
    for program in programs:
        unknown = set(program.seed_surface_ids) - known_sources
        if unknown:
            raise ValueError(f"discovery program references unknown surfaces: {sorted(unknown)}")
    for item in guidance:
        if item.source_id not in known_sources:
            raise ValueError(f"guidance references unknown surface: {item.source_id}")
        if surface_by_id[item.source_id].surface_type != "GUIDANCE_SURFACE":
            raise ValueError("GuidanceSurface must point to a GUIDANCE_SURFACE source")

    return Registry(families=families, surfaces=surfaces, discovery_programs=programs, guidance_surfaces=guidance)


def load_registry(path: Path) -> Registry:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("registry root must be an object")
    return validate_registry(payload)
