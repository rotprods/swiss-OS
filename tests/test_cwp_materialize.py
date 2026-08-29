from __future__ import annotations

import unittest

from swiss_os.cwp_materialize import CwpMaterializeError, build_idle_report, build_work_packet


def row(offset: int, key: str, *, matched_hotel_id: str = "") -> dict[str, object]:
    return {
        "original_candidate_offset": offset,
        "source_record_key": key,
        "name": f"hotel {offset}",
        "city": "city",
        "detail_url": f"https://www.hotelleriesuisse.ch/de/verband/mitgliedschaft/mitgliederverzeichnis/hotel-test-{offset}",
        "decision": "CANDIDATE_NEW_ENTITY_PREAUTH",
        "work_state": "VERIFY_NEW_ENTITY",
        "priority": 80,
        "reason": "NO_EXACT_CURRENT_CANONICAL_MATCH",
        "matched_hotel_id": matched_hotel_id,
    }


class CwpMaterializeTests(unittest.TestCase):
    def test_build_packet_preserves_exact_candidate_slice_and_safety(self):
        records = [row(i, f"MD-{i:04d}") for i in range(8)]
        packet = build_work_packet(
            records,
            snapshot_id="SNAP",
            start_offset=3,
            items_count=3,
            subbatch_number=36,
        )
        self.assertEqual(packet["batch_id"], "SNAP:WORK:0001:SUB:0036")
        self.assertEqual(packet["items_count"], 3)
        self.assertEqual([item["source_record_key"] for item in packet["items"]], ["MD-0003", "MD-0004", "MD-0005"])
        self.assertTrue(all("original_candidate_offset" not in item for item in packet["items"]))
        self.assertFalse(packet["authority_advanced"])
        self.assertEqual(packet["h_id_allocations"], 0)
        self.assertEqual(packet["outbound"], "CLOSED")
        self.assertEqual(packet["send_allowed"], 0)
        self.assertEqual(len(packet["items_sha256"]), 64)

    def test_idle_report_is_safe_when_no_request_is_active(self):
        report = build_idle_report({"source_universe": {"snapshot_id": "SNAP"}})
        self.assertEqual(report["state"], "NO_ACTIVE_CWP_REQUEST")
        self.assertFalse(report["materialized"])
        self.assertEqual(report["snapshot_id"], "SNAP")
        self.assertFalse(report["authority_advanced"])
        self.assertEqual(report["h_id_allocations"], 0)
        self.assertEqual(report["outbound"], "CLOSED")
        self.assertEqual(report["send_allowed"], 0)

    def test_lineage_gap_fails_closed(self):
        records = [row(i, f"MD-{i:04d}") for i in range(5)]
        records[3]["original_candidate_offset"] = 9
        with self.assertRaisesRegex(CwpMaterializeError, "candidate lineage drift"):
            build_work_packet(records, snapshot_id="SNAP", start_offset=2, items_count=2, subbatch_number=36)

    def test_existing_canonical_id_fails_closed(self):
        records = [row(0, "MD-0000", matched_hotel_id="H-9999")]
        with self.assertRaisesRegex(CwpMaterializeError, "must not carry a canonical hotel ID"):
            build_work_packet(records, snapshot_id="SNAP", start_offset=0, items_count=1, subbatch_number=36)

    def test_out_of_bounds_fails_closed(self):
        records = [row(i, f"MD-{i:04d}") for i in range(2)]
        with self.assertRaisesRegex(CwpMaterializeError, "exceeds candidate export"):
            build_work_packet(records, snapshot_id="SNAP", start_offset=1, items_count=2, subbatch_number=36)


if __name__ == "__main__":
    unittest.main()
