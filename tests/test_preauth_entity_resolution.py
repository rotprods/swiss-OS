from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from swiss_os.preauth_entity_resolution import (
    EntityResolutionError,
    build_workset,
    validate_workset,
)


def _packet(items: list[dict[str, str]], *, batch_id: str = "S:WORK:0001:SUB:0001") -> dict[str, object]:
    return {
        "schema_version": "CMI-WORK-PACKET-1.0",
        "snapshot_id": "S",
        "batch_id": batch_id,
        "items": items,
        "items_count": len(items),
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound": "CLOSED",
        "send_allowed": 0,
    }


def _next(total: int) -> dict[str, object]:
    return {
        "ecv_frontier": {
            "candidate_records_total": total,
            "current_detail_verified": total,
            "remaining_unverified": 0,
            "pending_requeue": 0,
            "lineage_holes": [],
        }
    }


class PreauthEntityResolutionTests(unittest.TestCase):
    def _paths(self) -> tuple[Path, Path]:
        root = Path(tempfile.mkdtemp())
        state = root / "state"
        state.mkdir()
        return root, state

    def test_exact_name_city_creates_review_group_without_mapping_effect(self) -> None:
        root, state = self._paths()
        items = [
            {"source_record_key": "a", "name": "Hotel A", "city": "Zürich", "detail_url": "https://example.test/a"},
            {"source_record_key": "b", "name": "hotel a", "city": "zürich", "detail_url": "https://example.test/b"},
            {"source_record_key": "c", "name": "Hotel C", "city": "Bern", "detail_url": "https://example.test/c"},
        ]
        (state / "CMI_WORK_BATCH_0001_TEST.json").write_text(json.dumps(_packet(items)), encoding="utf-8")
        next_path = root / "NEXT.json"
        next_path.write_text(json.dumps(_next(3)), encoding="utf-8")

        workset = build_workset(state, next_path=next_path, snapshot_id="S", expected_records=3)

        self.assertEqual(workset["source_records"], 3)
        self.assertEqual(workset["duplicate_group_count"], 1)
        self.assertEqual(workset["duplicate_records"], 2)
        self.assertEqual(workset["unique_records"], 1)
        self.assertEqual(workset["entity_group_candidates"], 2)
        self.assertEqual(workset["terminal_mapping_effect"], "NONE")
        self.assertFalse(workset["canonical_id_allocation_allowed"])
        self.assertFalse(workset["authority_advanced"])
        self.assertEqual(workset["h_id_allocations"], 0)
        self.assertEqual(workset["outbound"], "CLOSED")
        self.assertEqual(workset["send_allowed"], 0)
        self.assertEqual(validate_workset(workset), ())

    def test_exact_detail_url_links_records(self) -> None:
        root, state = self._paths()
        items = [
            {"source_record_key": "a", "name": "One", "city": "Bern", "detail_url": "https://example.test/shared/"},
            {"source_record_key": "b", "name": "Two", "city": "Basel", "detail_url": "https://EXAMPLE.test/shared"},
        ]
        (state / "CMI_WORK_BATCH_0001_TEST.json").write_text(json.dumps(_packet(items)), encoding="utf-8")
        next_path = root / "NEXT.json"
        next_path.write_text(json.dumps(_next(2)), encoding="utf-8")

        workset = build_workset(state, next_path=next_path, snapshot_id="S", expected_records=2)
        self.assertEqual(workset["duplicate_group_count"], 1)
        self.assertEqual(workset["duplicate_groups"][0]["signals"], ["EXACT_DETAIL_URL"])

    def test_identical_duplicate_key_is_deduped_across_packets(self) -> None:
        root, state = self._paths()
        item = {"source_record_key": "a", "name": "Hotel A", "city": "Bern", "detail_url": "https://example.test/a"}
        (state / "CMI_WORK_BATCH_0001_A.json").write_text(json.dumps(_packet([item], batch_id="S:A")), encoding="utf-8")
        (state / "CMI_WORK_BATCH_0001_B.json").write_text(json.dumps(_packet([item], batch_id="S:B")), encoding="utf-8")
        next_path = root / "NEXT.json"
        next_path.write_text(json.dumps(_next(1)), encoding="utf-8")

        workset = build_workset(state, next_path=next_path, snapshot_id="S", expected_records=1)
        self.assertEqual(workset["source_records"], 1)
        self.assertEqual(workset["unique_records"], 1)

    def test_conflicting_duplicate_key_fails_closed(self) -> None:
        root, state = self._paths()
        a = {"source_record_key": "a", "name": "Hotel A", "city": "Bern", "detail_url": "https://example.test/a"}
        b = {"source_record_key": "a", "name": "Hotel B", "city": "Bern", "detail_url": "https://example.test/b"}
        (state / "CMI_WORK_BATCH_0001_A.json").write_text(json.dumps(_packet([a], batch_id="S:A")), encoding="utf-8")
        (state / "CMI_WORK_BATCH_0001_B.json").write_text(json.dumps(_packet([b], batch_id="S:B")), encoding="utf-8")
        next_path = root / "NEXT.json"
        next_path.write_text(json.dumps(_next(1)), encoding="utf-8")

        with self.assertRaisesRegex(EntityResolutionError, "conflicting duplicate source_record_key"):
            build_workset(state, next_path=next_path, snapshot_id="S", expected_records=1)

    def test_incomplete_exact_current_frontier_fails_closed(self) -> None:
        root, state = self._paths()
        item = {"source_record_key": "a", "name": "Hotel A", "city": "Bern", "detail_url": "https://example.test/a"}
        (state / "CMI_WORK_BATCH_0001_TEST.json").write_text(json.dumps(_packet([item])), encoding="utf-8")
        next_payload = _next(1)
        next_payload["ecv_frontier"]["current_detail_verified"] = 0
        next_payload["ecv_frontier"]["remaining_unverified"] = 1
        next_path = root / "NEXT.json"
        next_path.write_text(json.dumps(next_payload), encoding="utf-8")

        with self.assertRaisesRegex(EntityResolutionError, "frontier is not complete"):
            build_workset(state, next_path=next_path, snapshot_id="S", expected_records=1)

    def test_validator_detects_authority_tamper(self) -> None:
        root, state = self._paths()
        item = {"source_record_key": "a", "name": "Hotel A", "city": "Bern", "detail_url": "https://example.test/a"}
        (state / "CMI_WORK_BATCH_0001_TEST.json").write_text(json.dumps(_packet([item])), encoding="utf-8")
        next_path = root / "NEXT.json"
        next_path.write_text(json.dumps(_next(1)), encoding="utf-8")
        workset = build_workset(state, next_path=next_path, snapshot_id="S", expected_records=1)
        workset["authority_advanced"] = True
        violations = validate_workset(workset)
        self.assertIn("AUTHORITY_ADVANCED_FORBIDDEN", violations)
        self.assertIn("WORKSET_SHA_MISMATCH", violations)


if __name__ == "__main__":
    unittest.main()
