from __future__ import annotations

import copy
import hashlib
import json
import unittest

from swiss_os.reverse_authority_gap_review import (
    ReverseAuthorityGapReviewError,
    build_reverse_authority_gap_review,
    validate_reverse_authority_gap_review,
)


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def source(key: str, name: str, city: str) -> dict[str, object]:
    return {
        "record_id": key,
        "name": name,
        "city": city,
        "detail_url": f"https://source.test/{key}",
    }


def canonical(hotel_id: str, name: str, city: str) -> dict[str, object]:
    return {
        "hotel_id": hotel_id,
        "name": name,
        "city": city,
        "is_active": True,
        "official_website": f"https://hotel.test/{hotel_id}",
        "membership_state": "CURRENT_DETAIL_VERIFIED",
        "state": "CANONICAL_CURRENT_RECONCILED",
    }


class ReverseAuthorityGapReviewTests(unittest.TestCase):
    def build(self, sources, canonicals, coverage):
        return build_reverse_authority_gap_review(
            snapshot_id="SNAPSHOT",
            authority_epoch="E4",
            source_universe={"records": sources},
            canonical_catalog=canonicals,
            terminal_coverage=coverage,
            source_records_sha256=digest(sources),
            canonical_catalog_sha256=digest(canonicals),
            terminal_coverage_sha256=digest(coverage),
        )

    def test_only_uncovered_active_canonicals_enter_queue(self) -> None:
        sources = [
            source("S1", "Hotel Alpha", "Bern"),
            source("S2", "Hotel Beta", "Bern"),
        ]
        canonicals = [
            canonical("H-0001", "Hotel Alpha", "Bern"),
            canonical("H-0002", "Hotel Gamma", "Bern"),
        ]
        result = self.build(
            sources,
            canonicals,
            [{"source_record_key": "S1", "canonical_hotel_id": "H-0001"}],
        )
        self.assertEqual(result["summary"]["unique_covered_canonical_records"], 1)
        self.assertEqual(result["summary"]["reverse_authority_source_gaps"], 1)
        self.assertEqual(result["review_queue"][0]["canonical_hotel_id"], "H-0002")
        self.assertFalse(result["review_queue"][0]["terminal_decision_allowed_from_queue"])
        self.assertFalse(result["review_queue"][0]["authority_mutation_allowed_from_queue"])
        self.assertEqual(result["h_id_allocations"], 0)
        self.assertEqual(result["canonical_id_reservations"], 0)
        self.assertFalse(result["authority_advanced"])
        self.assertEqual(result["outbound"], "CLOSED")
        self.assertEqual(result["send_allowed"], 0)
        self.assertEqual(validate_reverse_authority_gap_review(result), ())

    def test_suggestions_are_same_city_and_ranked(self) -> None:
        sources = [
            source("S1", "Grand Hotel Alpha", "Bern"),
            source("S2", "Alpha Lodge", "Bern"),
            source("S3", "Grand Hotel Alpha", "Basel"),
        ]
        canonicals = [canonical("H-0001", "Grand Hotel Alfa", "Bern")]
        result = self.build(sources, canonicals, [])
        suggestions = result["review_queue"][0]["suggestions"]
        self.assertEqual([item["source_record_key"] for item in suggestions], ["S1", "S2"])
        self.assertTrue(all(item["source_city"] == "Bern" for item in suggestions))
        self.assertGreaterEqual(
            suggestions[0]["combined_similarity"],
            suggestions[1]["combined_similarity"],
        )

    def test_no_same_city_source_is_explicit(self) -> None:
        result = self.build(
            [source("S1", "Hotel Alpha", "Basel")],
            [canonical("H-0001", "Hotel Alpha", "Bern")],
            [],
        )
        item = result["review_queue"][0]
        self.assertEqual(item["same_city_source_candidates"], 0)
        self.assertEqual(item["suggestions"], [])
        self.assertEqual(
            item["queue_reason"],
            "NO_TERMINAL_SOURCE_MAPPING_NO_SAME_CITY_SOURCE_CANDIDATE",
        )

    def test_inactive_canonical_is_not_a_gap(self) -> None:
        inactive = canonical("H-0002", "Hotel Beta", "Bern")
        inactive["is_active"] = False
        result = self.build(
            [source("S1", "Hotel Alpha", "Bern")],
            [canonical("H-0001", "Hotel Alpha", "Bern"), inactive],
            [{"source_record_key": "S1", "canonical_hotel_id": "H-0001"}],
        )
        self.assertEqual(result["summary"]["reverse_authority_source_gaps"], 0)

    def test_multiple_sources_may_cover_one_canonical(self) -> None:
        sources = [
            source("S1", "Hotel Alpha", "Bern"),
            source("S2", "Hotel Alpha Annex", "Bern"),
        ]
        result = self.build(
            sources,
            [canonical("H-0001", "Hotel Alpha", "Bern")],
            [
                {"source_record_key": "S1", "canonical_hotel_id": "H-0001"},
                {"source_record_key": "S2", "canonical_hotel_id": "H-0001"},
            ],
        )
        self.assertEqual(result["summary"]["terminal_coverage_source_records"], 2)
        self.assertEqual(result["summary"]["unique_covered_canonical_records"], 1)
        self.assertEqual(result["summary"]["reverse_authority_source_gaps"], 0)

    def test_duplicate_coverage_source_key_fails_closed(self) -> None:
        sources = [source("S1", "Hotel Alpha", "Bern")]
        coverage = [
            {"source_record_key": "S1", "canonical_hotel_id": "H-0001"},
            {"source_record_key": "S1", "canonical_hotel_id": "H-0001"},
        ]
        with self.assertRaises(ReverseAuthorityGapReviewError):
            self.build(
                sources,
                [canonical("H-0001", "Hotel Alpha", "Bern")],
                coverage,
            )

    def test_unknown_coverage_source_fails_closed(self) -> None:
        with self.assertRaises(ReverseAuthorityGapReviewError):
            self.build(
                [source("S1", "Hotel Alpha", "Bern")],
                [canonical("H-0001", "Hotel Alpha", "Bern")],
                [{"source_record_key": "S9", "canonical_hotel_id": "H-0001"}],
            )

    def test_inactive_or_unknown_coverage_target_fails_closed(self) -> None:
        with self.assertRaises(ReverseAuthorityGapReviewError):
            self.build(
                [source("S1", "Hotel Alpha", "Bern")],
                [canonical("H-0001", "Hotel Alpha", "Bern")],
                [{"source_record_key": "S1", "canonical_hotel_id": "H-9999"}],
            )

    def test_input_hash_mismatch_fails_closed(self) -> None:
        sources = [source("S1", "Hotel Alpha", "Bern")]
        canonicals = [canonical("H-0001", "Hotel Alpha", "Bern")]
        with self.assertRaises(ReverseAuthorityGapReviewError):
            build_reverse_authority_gap_review(
                snapshot_id="SNAPSHOT",
                authority_epoch="E4",
                source_universe={"records": sources},
                canonical_catalog=canonicals,
                terminal_coverage=[],
                source_records_sha256="a" * 64,
                canonical_catalog_sha256=digest(canonicals),
                terminal_coverage_sha256=digest([]),
            )

    def test_queue_is_deterministic_under_input_reordering(self) -> None:
        sources = [
            source("S2", "Hotel Beta", "Bern"),
            source("S1", "Hotel Alpha", "Bern"),
        ]
        canonicals = [
            canonical("H-0002", "Hotel Gamma", "Bern"),
            canonical("H-0001", "Hotel Delta", "Bern"),
        ]
        first = self.build(sources, canonicals, [])
        second_sources = list(reversed(sources))
        second_canonicals = list(reversed(canonicals))
        second = build_reverse_authority_gap_review(
            snapshot_id="SNAPSHOT",
            authority_epoch="E4",
            source_universe={"records": second_sources},
            canonical_catalog=second_canonicals,
            terminal_coverage=[],
            source_records_sha256=digest(second_sources),
            canonical_catalog_sha256=digest(second_canonicals),
            terminal_coverage_sha256=digest([]),
        )
        self.assertEqual(first["review_queue"], second["review_queue"])
        self.assertEqual(first["queue_sha256"], second["queue_sha256"])

    def test_validator_rejects_encoded_terminal_decision(self) -> None:
        result = self.build(
            [source("S1", "Hotel Alpha", "Bern")],
            [canonical("H-0001", "Hotel Beta", "Bern")],
            [],
        )
        tampered = copy.deepcopy(result)
        tampered["review_queue"][0]["classification"] = "STALE_AUTHORITY"
        tampered["queue_sha256"] = digest(tampered["review_queue"])
        self.assertIn(
            "QUEUE_MUST_NOT_ENCODE_TERMINAL_DECISION",
            validate_reverse_authority_gap_review(tampered),
        )


if __name__ == "__main__":
    unittest.main()
