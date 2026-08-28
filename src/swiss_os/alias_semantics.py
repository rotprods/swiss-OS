from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata
from typing import Iterable, Mapping

_HOTEL_ID_RE = re.compile(r"^H-\d{4}$")
_SUPERSEDED_ID_IN_NOTES_RE = re.compile(r"\b(H-\d{4})\b(?=[^\n]{0,80}\bsupersed(?:e|ed|ing|es)?\b)", re.IGNORECASE)
_ALLOWED_STABLE_BASES = {"EXACT_DETAIL_URL", "EXACT_SOURCE_RECORD_KEY", "EXACT_HSID"}


@dataclass(frozen=True)
class AliasSemanticViolation:
    code: str
    alias_hotel_id: str
    canonical_hotel_id: str
    detail: str

    def as_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "alias_hotel_id": self.alias_hotel_id,
            "canonical_hotel_id": self.canonical_hotel_id,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class AliasSemanticResult:
    state: str
    checked_aliases: int
    violations: tuple[AliasSemanticViolation, ...]

    @property
    def valid(self) -> bool:
        return self.state == "EXACT" and not self.violations

    def as_dict(self) -> dict[str, object]:
        return {
            "alias_semantics_state": self.state,
            "alias_semantics_valid": self.valid,
            "checked_aliases": self.checked_aliases,
            "violations": [item.as_dict() for item in self.violations],
            "authority_advanced": False,
            "h_id_allocations": 0,
            "outbound_opened": False,
            "send_allowed": 0,
        }


def normalize_identity_component(value: object) -> str:
    if not isinstance(value, str):
        return ""
    decomposed = unicodedata.normalize("NFKD", value)
    without_marks = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    folded = without_marks.casefold()
    return " ".join(re.findall(r"[a-z0-9]+", folded))


def identity_key(name: object, city: object) -> tuple[str, str]:
    return normalize_identity_component(name), normalize_identity_component(city)


def _require_mapping_rows(rows: Iterable[Mapping[str, object]], label: str) -> tuple[Mapping[str, object], ...]:
    materialized = tuple(rows)
    if not all(isinstance(row, Mapping) for row in materialized):
        raise ValueError(f"{label} must contain only mapping rows")
    return materialized


def _hotel_id(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _catalog_id(row: Mapping[str, object]) -> str:
    return _hotel_id(row.get("hotel_id") or row.get("id"))


def _catalog_name(row: Mapping[str, object]) -> object:
    return row.get("canonical_name", row.get("name", ""))


def _catalog_city(row: Mapping[str, object]) -> object:
    return row.get("city", "")


def _alias_id(row: Mapping[str, object]) -> str:
    return _hotel_id(row.get("alias_hotel_id") or row.get("alias_id") or row.get("superseded_hotel_id"))


def _alias_target(row: Mapping[str, object]) -> str:
    return _hotel_id(row.get("canonical_hotel_id") or row.get("canonical_id") or row.get("superseded_by"))


def _resolution_candidate_identity(row: Mapping[str, object]) -> tuple[str, str]:
    return identity_key(
        row.get("candidate_name", row.get("name", row.get("raw_name", ""))),
        row.get("candidate_city", row.get("city", row.get("raw_city", ""))),
    )


def _resolution_target(row: Mapping[str, object]) -> str:
    return _hotel_id(
        row.get("canonical_hotel_id")
        or row.get("canonical_id")
        or row.get("matched_hotel_id")
        or row.get("target_hotel_id")
    )


def _claimed_alias_ids(row: Mapping[str, object]) -> tuple[str, ...]:
    explicit = _hotel_id(
        row.get("claimed_alias_hotel_id")
        or row.get("alias_hotel_id")
        or row.get("superseded_hotel_id")
    )
    if explicit:
        return (explicit,)
    notes = row.get("notes", "")
    if not isinstance(notes, str):
        return ()
    # Do not bind every H-ID mentioned in prose. Only the H-ID syntactically
    # associated with a supersession assertion is eligible as the alias side.
    return tuple(dict.fromkeys(_SUPERSEDED_ID_IN_NOTES_RE.findall(notes)))


def _stable_equivalence_proven(row: Mapping[str, object]) -> bool:
    # A bare boolean is deliberately insufficient. Stronger-than-name+city
    # equivalence must name a supported stable identity basis and durable ref.
    if row.get("stable_identity_verified") is not True:
        return False
    basis = row.get("stable_identity_basis")
    ref = row.get("stable_identity_ref")
    return isinstance(basis, str) and basis in _ALLOWED_STABLE_BASES and isinstance(ref, str) and bool(ref.strip())


def validate_alias_semantics(
    catalog_rows: Iterable[Mapping[str, object]],
    alias_rows: Iterable[Mapping[str, object]],
    resolution_rows: Iterable[Mapping[str, object]],
) -> AliasSemanticResult:
    """Validate alias edges against physical identity and entity-resolution evidence.

    This is intentionally fail-closed. Structural PK/FK validity is insufficient:
    a superseded H-ID must resolve to the same real-world entity as the persisted
    canonical target, and the entity-resolution evidence must bind that exact H-ID.

    The function is read-only. It never allocates IDs, mutates authority or opens
    outbound.
    """

    catalog = _require_mapping_rows(catalog_rows, "catalog_rows")
    aliases = _require_mapping_rows(alias_rows, "alias_rows")
    resolutions = _require_mapping_rows(resolution_rows, "resolution_rows")

    catalog_by_id: dict[str, Mapping[str, object]] = {}
    violations: list[AliasSemanticViolation] = []

    for row in catalog:
        hotel_id = _catalog_id(row)
        if not _HOTEL_ID_RE.fullmatch(hotel_id):
            raise ValueError(f"invalid catalog hotel_id: {hotel_id!r}")
        if hotel_id in catalog_by_id:
            raise ValueError(f"duplicate catalog hotel_id: {hotel_id}")
        catalog_by_id[hotel_id] = row

    resolutions_by_alias: dict[str, list[Mapping[str, object]]] = {}
    for row in resolutions:
        for claimed_id in _claimed_alias_ids(row):
            if _HOTEL_ID_RE.fullmatch(claimed_id):
                resolutions_by_alias.setdefault(claimed_id, []).append(row)

    seen_alias_ids: set[str] = set()
    for alias in aliases:
        alias_id = _alias_id(alias)
        target_id = _alias_target(alias)

        if not _HOTEL_ID_RE.fullmatch(alias_id) or not _HOTEL_ID_RE.fullmatch(target_id):
            violations.append(
                AliasSemanticViolation("INVALID_ALIAS_EDGE", alias_id, target_id, "alias/target H-ID format invalid")
            )
            continue
        if alias_id in seen_alias_ids:
            violations.append(
                AliasSemanticViolation("DUPLICATE_ALIAS_EDGE", alias_id, target_id, "alias H-ID appears more than once")
            )
            continue
        seen_alias_ids.add(alias_id)

        alias_hotel = catalog_by_id.get(alias_id)
        target_hotel = catalog_by_id.get(target_id)
        if alias_hotel is None:
            violations.append(
                AliasSemanticViolation("ALIAS_HOTEL_MISSING", alias_id, target_id, "alias H-ID absent from physical catalog")
            )
            continue
        if target_hotel is None:
            violations.append(
                AliasSemanticViolation("CANONICAL_TARGET_MISSING", alias_id, target_id, "canonical target absent from physical catalog")
            )
            continue
        if alias_id == target_id:
            violations.append(
                AliasSemanticViolation("SELF_ALIAS", alias_id, target_id, "alias cannot target itself")
            )
            continue

        evidence_rows = resolutions_by_alias.get(alias_id, [])
        if not evidence_rows:
            violations.append(
                AliasSemanticViolation("ALIAS_EVIDENCE_MISSING", alias_id, target_id, "no entity-resolution row binds this alias H-ID")
            )
            continue
        if len(evidence_rows) != 1:
            violations.append(
                AliasSemanticViolation(
                    "ALIAS_EVIDENCE_AMBIGUOUS",
                    alias_id,
                    target_id,
                    f"expected exactly one entity-resolution row, found {len(evidence_rows)}",
                )
            )
            continue

        resolution = evidence_rows[0]
        explicit_target = _resolution_target(resolution)
        if explicit_target and explicit_target != target_id:
            violations.append(
                AliasSemanticViolation(
                    "RESOLUTION_TARGET_MISMATCH",
                    alias_id,
                    target_id,
                    f"entity-resolution target {explicit_target} differs from persisted target",
                )
            )
            continue

        candidate_key = _resolution_candidate_identity(resolution)
        alias_key = identity_key(_catalog_name(alias_hotel), _catalog_city(alias_hotel))
        target_key = identity_key(_catalog_name(target_hotel), _catalog_city(target_hotel))

        if not all(candidate_key) or not all(alias_key) or not all(target_key):
            violations.append(
                AliasSemanticViolation("IDENTITY_FIELDS_MISSING", alias_id, target_id, "name/city identity is incomplete")
            )
            continue

        candidate_matches_alias = candidate_key == alias_key
        candidate_matches_target = candidate_key == target_key
        alias_matches_target = alias_key == target_key
        stable_requested = resolution.get("stable_identity_verified") is True
        stable_proof = _stable_equivalence_proven(resolution)

        if stable_requested and not stable_proof:
            violations.append(
                AliasSemanticViolation(
                    "STABLE_IDENTITY_PROOF_INVALID",
                    alias_id,
                    target_id,
                    "stable identity override lacks an allowed basis and non-empty durable reference",
                )
            )
            continue

        if candidate_matches_target and not candidate_matches_alias:
            violations.append(
                AliasSemanticViolation(
                    "ALIAS_IDENTITY_MISMATCH",
                    alias_id,
                    target_id,
                    "entity-resolution candidate matches canonical target but not the physical alias H-ID identity",
                )
            )
            continue

        if not candidate_matches_alias and not stable_proof:
            violations.append(
                AliasSemanticViolation(
                    "ALIAS_EVIDENCE_IDENTITY_MISMATCH",
                    alias_id,
                    target_id,
                    "entity-resolution candidate does not identify the physical alias H-ID",
                )
            )
            continue

        if not alias_matches_target and not stable_proof:
            violations.append(
                AliasSemanticViolation(
                    "REAL_WORLD_EQUIVALENCE_UNPROVEN",
                    alias_id,
                    target_id,
                    "alias and canonical target differ by name+city and no stable-identity proof is present",
                )
            )
            continue

    state = "EXACT" if not violations else "RECONCILE_REQUIRED"
    return AliasSemanticResult(state=state, checked_aliases=len(aliases), violations=tuple(violations))
