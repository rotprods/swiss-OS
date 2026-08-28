from __future__ import annotations

from datetime import datetime, timedelta, timezone
import copy
import unittest

from swiss_os.exact_current_verify import (
    ExactCurrentVerifyError,
    FetchResponse,
    VerifyConfig,
    classify_verification,
    validate_verification_packet,
    verify_batch,
)


DETAIL = "https://www.hotelleriesuisse.ch/de/verband-und-geschaeftsstelle/mitglieder/mitgliederverzeichnis/hotel-hotel-alpha"


class Clock:
    def __init__(self) -> None:
        self.value = datetime(2026, 8, 28, 14, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        value = self.value
        self.value += timedelta(seconds=1)
        return value


def batch() -> dict[str, object]:
    return {
        "batch_id": "SNAPSHOT:WORK:0001",
        "items_count": 2,
        "items": [
            {
                "source_record_key": "directory:1",
                "name": "Hotel Alpha",
                "city": "Bern",
                "detail_url": DETAIL,
                "work_state": "VERIFY_NEW_ENTITY",
            },
            {
                "source_record_key": "directory:2",
                "name": "Hotel Beta",
                "city": "Basel",
                "detail_url": DETAIL.replace("alpha", "beta"),
                "work_state": "RECONCILE_REQUIRED",
            },
        ],
    }


class ExactCurrentVerifyTests(unittest.TestCase):
    def test_classification(self) -> None:
        self.assertEqual(
            classify_verification(name_match=True, city_match=True, http_ok=True),
            "CURRENT_DETAIL_VERIFIED",
        )
        self.assertEqual(
            classify_verification(name_match=True, city_match=False, http_ok=True),
            "CURRENT_DETAIL_NAME_ONLY",
        )
        self.assertEqual(
            classify_verification(name_match=False, city_match=True, http_ok=True),
            "CURRENT_DETAIL_CITY_ONLY",
        )
        self.assertEqual(
            classify_verification(name_match=False, city_match=False, http_ok=True),
            "CURRENT_DETAIL_MISMATCH",
        )
        self.assertEqual(
            classify_verification(name_match=True, city_match=True, http_ok=False),
            "FETCH_FAILED",
        )

    def test_verified_batch_routes_followups(self) -> None:
        pages = {
            DETAIL: b"<html><title>Hotel Alpha Bern</title><body>Hotel Alpha Bern</body></html>",
            DETAIL.replace("alpha", "beta"): b"<html><title>Hotel Beta Basel</title><body>Hotel Beta Basel</body></html>",
        }

        def fetcher(url: str) -> FetchResponse:
            return FetchResponse(pages[url], 200, url, {"ETag": "fixture"})

        packet = verify_batch(
            batch(),
            config=VerifyConfig(delay_seconds=0),
            fetcher=fetcher,
            robots_checker=lambda config, url: (True, "https://www.hotelleriesuisse.ch/robots.txt"),
            now=Clock(),
            sleeper=lambda _: None,
        )
        self.assertTrue(packet["all_verified"])
        self.assertEqual(packet["counts_by_state"], {"CURRENT_DETAIL_VERIFIED": 2})
        self.assertEqual(
            packet["results"][0]["followup"], "DEDUPE_GROUP_ALIAS_REVIEW"
        )
        self.assertEqual(
            packet["results"][1]["followup"], "RESOLVE_CANONICAL_CONFLICT"
        )
        self.assertEqual(validate_verification_packet(packet), ())
        self.assertFalse(packet["authority_advanced"])
        self.assertEqual(packet["h_id_allocations"], 0)
        self.assertEqual(packet["outbound"], "CLOSED")
        self.assertEqual(packet["send_allowed"], 0)

    def test_mismatch_is_typed_and_requeued(self) -> None:
        one = batch()
        one["items"] = [one["items"][0]]
        one["items_count"] = 1
        packet = verify_batch(
            one,
            config=VerifyConfig(delay_seconds=0),
            fetcher=lambda url: FetchResponse(
                b"<html><title>Different Property</title><body>Zurich</body></html>",
                200,
                url,
                {},
            ),
            robots_checker=lambda config, url: (True, "robots"),
            now=Clock(),
            sleeper=lambda _: None,
        )
        self.assertFalse(packet["all_verified"])
        self.assertEqual(
            packet["results"][0]["verification_state"],
            "CURRENT_DETAIL_MISMATCH",
        )
        self.assertEqual(
            packet["results"][0]["followup"], "REQUEUE_EXACT_CURRENT"
        )

    def test_robots_block_prevents_fetch(self) -> None:
        called = False

        def fetcher(url: str) -> FetchResponse:
            nonlocal called
            called = True
            raise AssertionError("fetch should not execute")

        one = batch()
        one["items"] = [one["items"][0]]
        one["items_count"] = 1
        packet = verify_batch(
            one,
            config=VerifyConfig(delay_seconds=0),
            fetcher=fetcher,
            robots_checker=lambda config, url: (False, "robots"),
            now=Clock(),
            sleeper=lambda _: None,
        )
        self.assertFalse(called)
        self.assertEqual(packet["results"][0]["verification_state"], "ROBOTS_BLOCKED")

    def test_directory_page_url_is_rejected(self) -> None:
        one = batch()
        one["items"] = [copy.deepcopy(one["items"][0])]
        one["items_count"] = 1
        one["items"][0]["detail_url"] = (
            "https://www.hotelleriesuisse.ch/de/verband-und-geschaeftsstelle/"
            "mitglieder/mitgliederverzeichnis/hotel-page-2"
        )
        packet = verify_batch(
            one,
            config=VerifyConfig(delay_seconds=0),
            fetcher=lambda url: FetchResponse(b"", 200, url, {}),
            robots_checker=lambda config, url: (True, "robots"),
            now=Clock(),
            sleeper=lambda _: None,
        )
        self.assertEqual(packet["results"][0]["verification_state"], "FETCH_FAILED")
        self.assertIn("directory page", packet["results"][0]["error"])

    def test_invalid_host_is_rejected(self) -> None:
        one = batch()
        one["items"] = [copy.deepcopy(one["items"][0])]
        one["items_count"] = 1
        one["items"][0]["detail_url"] = "https://example.test/member/hotel-alpha"
        packet = verify_batch(
            one,
            config=VerifyConfig(delay_seconds=0),
            fetcher=lambda url: FetchResponse(b"", 200, url, {}),
            robots_checker=lambda config, url: (True, "robots"),
            now=Clock(),
            sleeper=lambda _: None,
        )
        self.assertEqual(packet["results"][0]["verification_state"], "FETCH_FAILED")
        self.assertIn("not allowed", packet["results"][0]["error"])

    def test_validator_detects_tampering(self) -> None:
        packet = verify_batch(
            batch(),
            config=VerifyConfig(delay_seconds=0),
            fetcher=lambda url: FetchResponse(
                b"<html><body>Hotel Alpha Bern Hotel Beta Basel</body></html>",
                200,
                url,
                {},
            ),
            robots_checker=lambda config, url: (True, "robots"),
            now=Clock(),
            sleeper=lambda _: None,
        )
        packet["results"][0]["expected_name"] = "Tampered"
        self.assertIn("PACKET_SHA_MISMATCH", validate_verification_packet(packet))

    def test_batch_count_mismatch_fails_before_network(self) -> None:
        invalid = batch()
        invalid["items_count"] = 99
        with self.assertRaisesRegex(ExactCurrentVerifyError, "items_count"):
            verify_batch(invalid, config=VerifyConfig(delay_seconds=0))


if __name__ == "__main__":
    unittest.main()
