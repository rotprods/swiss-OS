from __future__ import annotations

import copy
import unittest

from swiss_os.ingest_packet import (
    IngestPacketError,
    MATCHED_EXISTING,
    RECONCILE,
    REVIEW_UNKNOWN,
    VERIFY_NEW,
    build_work_packet,
    classify_work_state,
    validate_work_packet,
)


class WorkStateTests(unittest.TestCase):
    def test_matching_and_fallback_classification(self) -> None:
        self.assertEqual(classify_work_state("EXACT_MATCH", "H-0001"), MATCHED_EXISTING)
        self.assertEqual(classify_work_state("AMBIGUOUS_MATCH", "H-0001"), RECONCILE)
        self.assertEqual(classify_work_state("NEW_CANDIDATE", ""), VERIFY_NEW)
        self.assertEqual(classify_work_state("UNRECOGNIZED", ""), REVIEW_UNKNOWN)


class IngestPacketTests(unittest.TestCase):
    def payload(self) -> dict[str, object]:
        return {
            "decisions": [
                {
                    "provider_record_key": "source:3",
                    "raw_name": "Hotel Existing",
                    "raw_city": "Bern",
                    "detail_url": "https://example.test/existing",
                    "decision": "EXACT_MATCH",
                    "matched_hotel_id": "H-0001",
                },
                {
                    "provider_record_key": "source:2",
                    "raw_name": "Hotel New",
                    "raw_city": "Basel",
                    "detail_url": "https://example.test/new",
                    "decision": "NEW_CANDIDATE",
                },
                {
                    "provider_record_key": "source:1",
                    "raw_name": "Hotel Ambiguous",
                    "raw_city": "Genève",
                    "detail_url": "https://example.test/ambiguous",
                    "decision": "AMBIGUOUS_MATCH",
                    "matched_hotel_id": "H-0002",
                },
                {
                    "provider_record_key": "source:4",
                    "raw_name": "Hotel Unknown",
                    "raw_city": "Lugano",
                    "decision": "OTHER",
                },
            ]
        }

    def test_builds_deterministic_prioritized_batches(self) -> None:
        packet = build_work_packet(
            self.payload(), snapshot_id="SNAPSHOT-1", batch_size=2
        )
        self.assertEqual(packet["input_decisions"], 4)
        self.assertEqual(packet["active_work_items"], 3)
        self.assertEqual(packet["terminal_matches"], 1)
        self.assertEqual(packet["counts_by_state"][RECONCILE], 1)
        self.assertEqual(packet["counts_by_state"][VERIFY_NEW], 1)
        self.assertEqual(packet["counts_by_state"][REVIEW_UNKNOWN], 1)
        self.assertEqual(packet["batches_count"], 2)
        first = packet["batches"][0]["items"]
        self.assertEqual(first[0]["source_record_key"], "source:1")
        self.assertEqual(first[0]["work_state"], RECONCILE)
        self.assertEqual(first[1]["source_record_key"], "source:2")
        self.assertEqual(first[1]["work_state"], VERIFY_NEW)
        self.assertEqual(validate_work_packet(packet), ())
        self.assertFalse(packet["authority_advanced"])
        self.assertEqual(packet["h_id_allocations"], 0)
        self.assertEqual(packet["outbound"], "CLOSED")
        self.assertEqual(packet["send_allowed"], 0)

    def test_fingerprint_is_deterministic(self) -> None:
        first = build_work_packet(self.payload(), snapshot_id="SNAPSHOT-1")
        second = build_work_packet(self.payload(), snapshot_id="SNAPSHOT-1")
        self.assertEqual(first["packet_sha256"], second["packet_sha256"])
        self.assertEqual(first, second)

    def test_nested_result_decisions_are_supported(self) -> None:
        packet = build_work_packet(
            {"result": self.payload()}, snapshot_id="SNAPSHOT-1"
        )
        self.assertEqual(packet["input_decisions"], 4)

    def test_duplicate_source_keys_fail_closed(self) -> None:
        payload = self.payload()
        payload["decisions"].append(copy.deepcopy(payload["decisions"][0]))
        with self.assertRaisesRegex(IngestPacketError, "duplicate source_record_key"):
            build_work_packet(payload, snapshot_id="SNAPSHOT-1")

    def test_invalid_batch_size_is_rejected(self) -> None:
        with self.assertRaisesRegex(IngestPacketError, "batch_size"):
            build_work_packet(self.payload(), snapshot_id="SNAPSHOT-1", batch_size=0)

    def test_validator_detects_tampering(self) -> None:
        packet = build_work_packet(self.payload(), snapshot_id="SNAPSHOT-1")
        packet["batches"][0]["items"][0]["name"] = "Tampered"
        violations = validate_work_packet(packet)
        self.assertIn("BATCH_ITEMS_SHA_MISMATCH", violations)
        self.assertIn("PACKET_SHA_MISMATCH", violations)

    def test_terminal_match_cannot_enter_active_batch(self) -> None:
        packet = build_work_packet(self.payload(), snapshot_id="SNAPSHOT-1")
        packet["batches"][0]["items"][0]["work_state"] = MATCHED_EXISTING
        violations = validate_work_packet(packet)
        self.assertIn("TERMINAL_MATCH_IN_ACTIVE_BATCH", violations)


if __name__ == "__main__":
    unittest.main()
