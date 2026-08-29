from __future__ import annotations

import copy
import hashlib
import json
import unittest

from swiss_os.canonical_match_review import (
    CanonicalMatchReviewError,
    build_canonical_match_review_queue,
    validate_canonical_match_review_queue,
)


def digest(value) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def candidate(key: str, name: str, city: str) -> dict[str, object]:
    return {
        "source_record_key": key,
        "name": name,
        "city": city,
        "detail_url": f"https://example.test/{key}",
        "decision": "CANDIDATE_NEW_ENTITY_PREAUTH",
        "matched_hotel_id": "",
    }


def canonical(hotel_id: str, name: str, city: str) -> dict[str, object]:
    return {
        "hotel_id": hotel_id,
        "name": name,
        "city": city,
        "is_active": True,
    }


class CanonicalMatchReviewTests(unittest.TestCase):
    def build(self, candidates, canonicals):
        return build_canonical_match_review_queue(
            snapshot_id="SNAPSHOT",
            candidate_records=candidates,
            canonical_catalog=canonicals,
            candidate_records_sha256=digest(candidates),
            canonical_catalog_sha256=digest(canonicals),
        )

    def test_exact_name_city_is_review_only(self) -> None:
        queue = self.build(
            [candidate("K1", "Hôtel Alpha", "Zürich")],
            [canonical("H-0001", "Hotel Alpha", "Zurich")],
        )
        self.assertEqual(queue["summary"]["review_pairs"], 1)
        item = queue["review_queue"][0]
        self.assertIn("EXACT_NORMALIZED_NAME_CITY", item["signals"])
        self.assertFalse(item["auto_merge_allowed"])
        self.assertFalse(item["terminal_mapping_allowed_from_queue"])
        self.assertNotIn("action", item)
        self.assertNotIn("resolution_action", item)
        self.assertFalse(queue["authority_advanced"])
        self.assertEqual(queue["h_id_allocations"], 0)
        self.assertEqual(queue["canonical_id_reservations"], 0)
        self.assertEqual(queue["outbound"], "CLOSED")
        self.assertEqual(queue["send_allowed"], 0)
        self.assertEqual(validate_canonical_match_review_queue(queue), ())

    def test_token_signature_equal_surfaces_alias_candidate(self) -> None:
        queue = self.build(
            [candidate("K1", "Hotel Neu-Schönstatt", "Quarten")],
            [canonical("H-0114", "Hostel Neu-Schönstatt", "Quarten")],
        )
        item = queue["review_queue"][0]
        self.assertIn("TOKEN_SIGNATURE_EQUAL", item["signals"])
        self.assertEqual(item["suggested_canonical_hotel_id"], "H-0114")

    def test_high_name_similarity_surfaces_typographic_variant(self) -> None:
        queue = self.build(
            [candidate("K1", "wellnesshostel3000 laax", "Laax")],
            [canonical("H-0542", "wellnessHostel 3000 Laax", "Laax")],
        )
        item = queue["review_queue"][0]
        self.assertIn("VERY_HIGH_NAME_SIMILARITY", item["signals"])
        self.assertGreaterEqual(item["name_similarity"], 0.92)

    def test_cross_city_pair_is_never_surfaced(self) -> None:
        queue = self.build(
            [candidate("K1", "Hotel Alpha", "Bern")],
            [canonical("H-0001", "Hotel Alpha", "Basel")],
        )
        self.assertEqual(queue["summary"]["same_city_pairs_evaluated"], 0)
        self.assertEqual(queue["summary"]["review_pairs"], 0)

    def test_low_similarity_same_city_is_not_surfaced(self) -> None:
        queue = self.build(
            [candidate("K1", "Mountain Fox Lodge", "Bern")],
            [canonical("H-0001", "Riverside Crown Palace", "Bern")],
        )
        self.assertEqual(queue["summary"]["review_pairs"], 0)

    def test_multiple_targets_are_counted_but_not_resolved(self) -> None:
        queue = self.build(
            [candidate("K1", "Hotel Alpha", "Bern")],
            [
                canonical("H-0001", "Hotel Alpha", "Bern"),
                canonical("H-0002", "Alpha Hotel", "Bern"),
            ],
        )
        self.assertEqual(queue["summary"]["review_pairs"], 2)
        self.assertEqual(
            queue["summary"]["source_records_with_multiple_targets"], 1
        )
        self.assertTrue(
            all(
                item["required_action"]
                == "EVIDENCE_BACKED_EXPLICIT_REVIEW"
                for item in queue["review_queue"]
            )
        )

    def test_queue_is_deterministic_under_input_reordering(self) -> None:
        candidates = [
            candidate("K2", "Hotel Beta", "Bern"),
            candidate("K1", "Hotel Alpha", "Bern"),
        ]
        canonicals = [
            canonical("H-0002", "Hotel Beta", "Bern"),
            canonical("H-0001", "Hotel Alpha", "Bern"),
        ]
        first = self.build(candidates, canonicals)
        second_candidates = list(reversed(candidates))
        second_canonicals = list(reversed(canonicals))
        second = self.build(second_candidates, second_canonicals)
        self.assertEqual(first["queue_sha256"], second["queue_sha256"])
        self.assertEqual(first["review_queue"], second["review_queue"])

    def test_duplicate_source_key_fails_closed(self) -> None:
        with self.assertRaises(CanonicalMatchReviewError):
            self.build(
                [
                    candidate("K1", "Hotel A", "Bern"),
                    candidate("K1", "Hotel B", "Bern"),
                ],
                [canonical("H-0001", "Hotel A", "Bern")],
            )

    def test_preauth_candidate_with_existing_match_fails_closed(self) -> None:
        bad = candidate("K1", "Hotel A", "Bern")
        bad["matched_hotel_id"] = "H-0001"
        with self.assertRaises(CanonicalMatchReviewError):
            self.build(
                [bad], [canonical("H-0001", "Hotel A", "Bern")]
            )

    def test_candidate_hash_mismatch_fails_closed(self) -> None:
        candidates = [candidate("K1", "Hotel A", "Bern")]
        canonicals = [canonical("H-0001", "Hotel A", "Bern")]
        with self.assertRaises(CanonicalMatchReviewError):
            build_canonical_match_review_queue(
                snapshot_id="SNAPSHOT",
                candidate_records=candidates,
                canonical_catalog=canonicals,
                candidate_records_sha256="a" * 64,
                canonical_catalog_sha256=digest(canonicals),
            )

    def test_canonical_hash_mismatch_fails_closed(self) -> None:
        candidates = [candidate("K1", "Hotel A", "Bern")]
        canonicals = [canonical("H-0001", "Hotel A", "Bern")]
        with self.assertRaises(CanonicalMatchReviewError):
            build_canonical_match_review_queue(
                snapshot_id="SNAPSHOT",
                candidate_records=candidates,
                canonical_catalog=canonicals,
                candidate_records_sha256=digest(candidates),
                canonical_catalog_sha256="b" * 64,
            )

    def test_active_state_must_be_explicit(self) -> None:
        candidates = [candidate("K1", "Hotel A", "Bern")]
        canonicals = [{"hotel_id": "H-0001", "name": "Hotel A", "city": "Bern"}]
        with self.assertRaises(CanonicalMatchReviewError):
            self.build(candidates, canonicals)

    def test_validator_rejects_encoded_resolution_action(self) -> None:
        queue = self.build(
            [candidate("K1", "Hotel Alpha", "Bern")],
            [canonical("H-0001", "Hotel Alpha", "Bern")],
        )
        tampered = copy.deepcopy(queue)
        tampered["review_queue"][0]["action"] = "MATCH_EXISTING"
        tampered["queue_sha256"] = digest(tampered["review_queue"])
        self.assertIn(
            "QUEUE_MUST_NOT_ENCODE_RESOLUTION_ACTION",
            validate_canonical_match_review_queue(tampered),
        )


if __name__ == "__main__":
    unittest.main()
