from __future__ import annotations

import copy
import unittest

from swiss_os.page_count_consensus import (
    PageCountConsensusError,
    normalize_page_count_consensus,
)


def _capture(pages: int = 100) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "MEMBER_DIRECTORY_CAPTURE_V1",
        "capture_id": "CAPTURE-CONSENSUS",
        "locale": "de",
        "expected_pages": pages,
        "reported_records": 0,
        "capture_violations": ["REPORTED_RECORDS_UNRESOLVED"],
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound_opened": False,
        "send_allowed": 0,
        "pages": [],
    }
    for position in range(1, pages + 1):
        payload["pages"].append(  # type: ignore[index]
            {
                "page_position": position,
                "observed_expected_pages": pages,
                "records": [{"detail_url": f"https://example.test/hotel-{position}"}],
            }
        )
    return payload


class PageCountConsensusTests(unittest.TestCase):
    def test_unanimous_countless_capture_passes_through(self) -> None:
        out = normalize_page_count_consensus(_capture())
        proof = out["page_count_consensus"]
        self.assertEqual(proof["consensus_pages"], 100)
        self.assertEqual(proof["outlier_positions"], [])
        self.assertEqual(out["capture_violations"], ["REPORTED_RECORDS_UNRESOLVED"])

    def test_one_stale_minus_one_outlier_at_one_percent_is_normalized(self) -> None:
        payload = _capture()
        payload["pages"][50]["observed_expected_pages"] = 99  # type: ignore[index]
        payload["capture_violations"].append("PAGE_COUNT_DRIFT:99,100")  # type: ignore[union-attr]
        out = normalize_page_count_consensus(payload)
        page = out["pages"][50]
        self.assertEqual(page["observed_expected_pages_original"], 99)
        self.assertEqual(page["observed_expected_pages"], 100)
        self.assertTrue(page["page_count_consensus_normalized"])
        self.assertEqual(out["page_count_consensus"]["outlier_positions"], [51])
        self.assertFalse(out["authority_advanced"])
        self.assertEqual(out["h_id_allocations"], 0)
        self.assertFalse(out["outbound_opened"])
        self.assertEqual(out["send_allowed"], 0)

    def test_more_than_one_percent_outliers_fail_closed(self) -> None:
        payload = _capture()
        payload["pages"][10]["observed_expected_pages"] = 99  # type: ignore[index]
        payload["pages"][20]["observed_expected_pages"] = 99  # type: ignore[index]
        payload["capture_violations"].append("PAGE_COUNT_DRIFT:99,100")  # type: ignore[union-attr]
        with self.assertRaisesRegex(PageCountConsensusError, "below 99 percent"):
            normalize_page_count_consensus(payload)

    def test_larger_drift_fails_closed(self) -> None:
        payload = _capture()
        payload["pages"][50]["observed_expected_pages"] = 98  # type: ignore[index]
        payload["capture_violations"].append("PAGE_COUNT_DRIFT:98,100")  # type: ignore[union-attr]
        with self.assertRaisesRegex(PageCountConsensusError, "expected_pages-1"):
            normalize_page_count_consensus(payload)

    def test_higher_page_observation_fails_closed(self) -> None:
        payload = _capture()
        payload["pages"][50]["observed_expected_pages"] = 101  # type: ignore[index]
        payload["capture_violations"].append("PAGE_COUNT_DRIFT:100,101")  # type: ignore[union-attr]
        with self.assertRaisesRegex(PageCountConsensusError, "expected_pages-1"):
            normalize_page_count_consensus(payload)

    def test_terminal_page_outlier_fails_closed(self) -> None:
        payload = _capture()
        payload["pages"][-1]["observed_expected_pages"] = 99  # type: ignore[index]
        payload["capture_violations"].append("PAGE_COUNT_DRIFT:99,100")  # type: ignore[union-attr]
        with self.assertRaisesRegex(PageCountConsensusError, "terminal page"):
            normalize_page_count_consensus(payload)

    def test_unreported_drift_fails_closed(self) -> None:
        payload = _capture()
        payload["pages"][50]["observed_expected_pages"] = 99  # type: ignore[index]
        with self.assertRaisesRegex(PageCountConsensusError, "absent from capture_violations"):
            normalize_page_count_consensus(payload)

    def test_false_declared_drift_fails_closed(self) -> None:
        payload = _capture()
        payload["capture_violations"].append("PAGE_COUNT_DRIFT:99,100")  # type: ignore[union-attr]
        with self.assertRaisesRegex(PageCountConsensusError, "declares drift"):
            normalize_page_count_consensus(payload)

    def test_other_capture_violation_fails_closed(self) -> None:
        payload = _capture()
        payload["capture_violations"].append("DUPLICATE_DETAIL_URL")  # type: ignore[union-attr]
        with self.assertRaisesRegex(PageCountConsensusError, "unsupported violations"):
            normalize_page_count_consensus(payload)

    def test_type_coercion_fails_closed(self) -> None:
        payload = _capture()
        payload["pages"][0]["page_position"] = "1"  # type: ignore[index]
        with self.assertRaisesRegex(PageCountConsensusError, "positive integer"):
            normalize_page_count_consensus(payload)

    def test_pre_authorization_fails_closed(self) -> None:
        payload = _capture()
        payload["authority_advanced"] = True
        with self.assertRaisesRegex(PageCountConsensusError, "authority_advanced"):
            normalize_page_count_consensus(payload)


if __name__ == "__main__":
    unittest.main()
