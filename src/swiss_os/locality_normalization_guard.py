from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from typing import Mapping, Sequence

CANTON_CODES = frozenset({
    "ag","ai","ar","be","bl","bs","fr","ge","gl","gr","ju","lu","ne","nw","ow",
    "sg","sh","so","sz","tg","ti","ur","vd","vs","zg","zh",
})
AIRPORT_QUALIFIERS = frozenset({"airport", "aeroport"})


class LocalityGuardError(ValueError):
    pass


def _text(value: object) -> str:
    return str(value or "").strip()


def normalize_identity_text(value: object) -> str:
    return re.sub(r"\s+", " ", _text(value)).casefold()


def _ascii(value: object) -> str:
    return unicodedata.normalize("NFKD", _text(value)).encode("ascii", "ignore").decode().casefold()


def locality_keys(value: object) -> tuple[str, ...]:
    """Return conservative locality-equivalence keys for review-space expansion only.

    These keys may expose literal zero-city false negatives but never prove property identity.
    Presentation-only qualifiers handled here include accents/punctuation, parentheticals,
    canton suffixes, numeric district suffixes and a final airport/aeroport token.
    """
    raw = _ascii(value)

    def clean(text: str) -> str:
        tokens = re.sub(r"[^a-z0-9]+", " ", text).split()
        tokens = [t for t in tokens if t not in CANTON_CODES and not t.isdigit()]
        return " ".join(tokens)

    keys: set[str] = set()
    full = clean(raw)
    if full:
        keys.add(full)
    no_parenthetical = clean(re.sub(r"\([^)]*\)", " ", raw))
    if no_parenthetical:
        keys.add(no_parenthetical)
    for key in tuple(keys):
        tokens = key.split()
        if len(tokens) > 1 and tokens[-1] in AIRPORT_QUALIFIERS:
            keys.add(" ".join(tokens[:-1]))
    return tuple(sorted(k for k in keys if k))


def _canonical_name(item: Mapping[str, object]) -> str:
    return _text(item.get("canonical_name") or item.get("name"))


def _source_key(item: Mapping[str, object]) -> str:
    return _text(item.get("record_id") or item.get("source_record_key"))


def _validate_identity_sets(
    source_records: Sequence[Mapping[str, object]],
    canonical_records: Sequence[Mapping[str, object]],
) -> None:
    source_seen: set[str] = set()
    for item in source_records:
        key = _source_key(item)
        if not key:
            raise LocalityGuardError("SOURCE_RECORD_KEY_REQUIRED")
        if key in source_seen:
            raise LocalityGuardError(f"DUPLICATE_SOURCE_RECORD_KEY:{key}")
        source_seen.add(key)

    canonical_seen: set[str] = set()
    for item in canonical_records:
        hotel_id = _text(item.get("hotel_id"))
        if not hotel_id:
            raise LocalityGuardError("CANONICAL_HOTEL_ID_REQUIRED")
        if hotel_id in canonical_seen:
            raise LocalityGuardError(f"DUPLICATE_CANONICAL_HOTEL_ID:{hotel_id}")
        canonical_seen.add(hotel_id)


def rebuild_zero_city_lane(
    source_records: Sequence[Mapping[str, object]],
    canonical_records: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Rebuild the conservative zero-exact-city lane without granting authority.

    Exact normalized name+city rows are outside the candidate universe. Rows with no exact
    canonical city form the raw zero-city pool. Exact global-name/cross-locality conflicts are
    excluded because they require a separate identity-conflict review lane.
    """
    _validate_identity_sets(source_records, canonical_records)
    by_name_city: dict[tuple[str, str], list[Mapping[str, object]]] = defaultdict(list)
    by_city: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    by_name: dict[str, list[Mapping[str, object]]] = defaultdict(list)

    for item in canonical_records:
        name = normalize_identity_text(_canonical_name(item))
        city = normalize_identity_text(item.get("city"))
        if name and city:
            by_name_city[(name, city)].append(item)
        if city:
            by_city[city].append(item)
        if name:
            by_name[name].append(item)

    candidate = []
    for item in source_records:
        name = normalize_identity_text(item.get("name"))
        city = normalize_identity_text(item.get("city"))
        if not by_name_city.get((name, city)):
            candidate.append(item)

    raw_zero_city = [
        item for item in candidate
        if not by_city.get(normalize_identity_text(item.get("city")))
    ]
    exact_name_conflicts = [
        item for item in raw_zero_city
        if by_name.get(normalize_identity_text(item.get("name")))
    ]
    excluded = {_source_key(item) for item in exact_name_conflicts}
    lane = sorted(
        (item for item in raw_zero_city if _source_key(item) not in excluded),
        key=_source_key,
    )
    return {
        "candidate_records": len(candidate),
        "raw_zero_city_records": len(raw_zero_city),
        "exact_global_name_conflicts": len(exact_name_conflicts),
        "lane_records": len(lane),
        "lane": lane,
        "excluded_exact_name_conflicts": sorted(excluded),
        "authority_action": "NONE",
        "auto_bind_allowed": False,
    }


def locality_variant_review(
    source_records: Sequence[Mapping[str, object]],
    canonical_records: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    """Find literal zero-city rows whose locality normalizes onto canonical localities.

    Every result remains review-only. A locality match narrows comparator space but cannot
    establish same-property identity or create a canonical/terminal mapping. Multiple locality
    candidates are surfaced as explicit ambiguity rather than collapsed by ordering.
    """
    _validate_identity_sets(source_records, canonical_records)
    canonical_by_literal_city: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    canonical_by_locality_key: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for item in canonical_records:
        city = normalize_identity_text(item.get("city"))
        if city:
            canonical_by_literal_city[city].append(item)
        for key in locality_keys(item.get("city")):
            canonical_by_locality_key[key].append(item)

    findings: list[dict[str, object]] = []
    for source in sorted(source_records, key=_source_key):
        source_city = normalize_identity_text(source.get("city"))
        if canonical_by_literal_city.get(source_city):
            continue
        hits: dict[str, Mapping[str, object]] = {}
        matched_keys: set[str] = set()
        for key in locality_keys(source.get("city")):
            for item in canonical_by_locality_key.get(key, ()):
                hotel_id = _text(item.get("hotel_id"))
                if hotel_id:
                    hits[hotel_id] = item
                    matched_keys.add(key)
        if not hits:
            continue
        candidates = [
            {
                "hotel_id": hotel_id,
                "canonical_name": _canonical_name(item),
                "canonical_city": _text(item.get("city")),
            }
            for hotel_id, item in sorted(hits.items())
        ]
        findings.append({
            "source_record_key": _source_key(source),
            "source_name": _text(source.get("name")),
            "source_city": _text(source.get("city")),
            "normalized_locality_keys": sorted(matched_keys),
            "canonical_candidates": candidates,
            "candidate_count": len(candidates),
            "ambiguity": "MULTIPLE_CANONICAL_LOCALITY_CANDIDATES" if len(candidates) > 1 else "SINGLE_LOCALITY_COMPARATOR",
            "disposition": "LOCALITY_VARIANT_REVIEW_REQUIRED",
            "auto_bind_allowed": False,
            "authority_action": "NONE",
        })
    return findings
