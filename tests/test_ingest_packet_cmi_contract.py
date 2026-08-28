from __future__ import annotations

import unittest

from swiss_os.ingest_packet import (
    MATCHED_EXISTING,
    REVIEW_UNKNOWN,
    VERIFY_NEW,
    build_work_packet,
    classify_work_state,
    validate_work_packet,
)


class CMIToCWPContractTests(unittest.TestCase):
    def test_true_missing_is_verify_new_entity(self) -> None:
        self.assertEqual(classify_work_state("TRUE_MISSING", ""), VERIFY_NEW)

    def test_direct_mass_ingest_decision_shape_is_lossless(self) -> None:
        payload = {
            "decisions": [
                {
                    "snapshot_record_id": "SR-new",
                    "snapshot_id": "SNAP-1",
                    "source_record_key": "provider:MD-new",
                    "staging_class": "TRUE_MISSING",
                    "matched_hotel_id": None,
                    "reason_code": "NO_EXACT_IDENTITY_MATCH",
                    "normalized_name": "hotel new",
                    "normalized_city": "bern",
                    "normalized_detail_url": "https://www.hotelleriesuisse.ch/de/verband/mitgliedschaft/mitgliederverzeichnis/hotel-hotel-new",
                },
                {
                    "snapshot_record_id": "SR-existing",
                    "snapshot_id": "SNAP-1",
                    "source_record_key": "provider:MD-existing",
                    "staging_class": "ACTIVE_MATCH",
                    "matched_hotel_id": "H-0001",
                    "reason_code": "EXACT_CANONICAL_NAME_CITY",
                    "normalized_name": "hotel existing",
                    "normalized_city": "basel",
                    "normalized_detail_url": "https://www.hotelleriesuisse.ch/de/verband/mitgliedschaft/mitgliederverzeichnis/hotel-hotel-existing",
                },
            ]
        }
        packet = build_work_packet(payload, snapshot_id="SNAP-1", batch_size=100)
        self.assertEqual(validate_work_packet(packet), ())
        self.assertEqual(packet["input_decisions"], 2)
        self.assertEqual(packet["active_work_items"], 1)
        self.assertEqual(packet["terminal_matches"], 1)
        self.assertEqual(packet["counts_by_state"][VERIFY_NEW], 1)
        self.assertEqual(packet["counts_by_state"][MATCHED_EXISTING], 1)
        self.assertEqual(packet["counts_by_state"][REVIEW_UNKNOWN], 0)
        item = packet["batches"][0]["items"][0]
        self.assertEqual(item["source_record_key"], "provider:MD-new")
        self.assertEqual(item["decision"], "TRUE_MISSING")
        self.assertEqual(item["work_state"], VERIFY_NEW)
        self.assertEqual(item["name"], "hotel new")
        self.assertEqual(item["city"], "bern")
        self.assertIn("hotel-hotel-new", item["detail_url"])
        self.assertEqual(item["reason"], "NO_EXACT_IDENTITY_MATCH")
        self.assertFalse(packet["authority_advanced"])
        self.assertEqual(packet["h_id_allocations"], 0)
        self.assertEqual(packet["outbound"], "CLOSED")
        self.assertEqual(packet["send_allowed"], 0)

    def test_unknown_staging_class_still_fails_closed_to_review(self) -> None:
        self.assertEqual(classify_work_state("SOMETHING_NEWISH_BUT_UNRECOGNIZED", ""), VERIFY_NEW)
        self.assertEqual(classify_work_state("UNCLASSIFIED_STATE", ""), REVIEW_UNKNOWN)


if __name__ == "__main__":
    unittest.main()
