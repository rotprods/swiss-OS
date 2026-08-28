from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from urllib.parse import parse_qs, urlsplit
import unittest
from unittest.mock import patch

from swiss_os.discover_swiss import (
    DiscoverSwissConfig,
    MissingSubscriptionKey,
    PaginationCycleError,
    build_lodgingbusinesses_url,
    fetch_hotelleriesuisse_snapshot,
    normalize_lodging_record,
    resolve_subscription_key,
)


def lodging(
    identifier: str,
    hs_id: str,
    name: str,
    city: str,
    *,
    hs_origin: bool = True,
) -> dict[str, object]:
    origin_source = {"identifier": "hs", "acronym": "hs"} if hs_origin else {"identifier": "tom"}
    datasource = "hs-d365" if hs_origin else "tom"
    return {
        "identifier": identifier,
        "name": name,
        "address": {"addressLocality": city},
        "additionalProperty": [
            {"propertyId": "hsId", "value": hs_id},
        ],
        "link": [
            {"type": "WebHomepage", "url": f"https://{identifier}.example/"},
        ],
        "dataGovernance": {
            "origin": [
                {
                    "datasource": datasource,
                    "sourceId": hs_id,
                    "license": "CC BY-SA",
                    "source": origin_source,
                }
            ]
        },
        "removed": False,
    }


class DiscoverSwissTests(unittest.TestCase):
    def test_build_url_uses_project_top_and_continuation_token(self) -> None:
        config = DiscoverSwissConfig(project="dsod-hs", top=-1)
        token = '[{"token":"+RID:abc==#RT:1"}]'
        url = build_lodgingbusinesses_url(
            config,
            continuation_token=token,
            include_count=True,
        )
        params = parse_qs(urlsplit(url).query)
        self.assertEqual(params["project"], ["dsod-hs"])
        self.assertEqual(params["top"], ["-1"])
        self.assertEqual(params["includeCount"], ["true"])
        self.assertEqual(params["continuationToken"], [token])

    def test_normalize_prefers_official_hs_id_as_source_record_key(self) -> None:
        record = normalize_lodging_record(
            lodging("log_abc", "17800", "Hotel Test", "Bern")
        )
        self.assertEqual(record["source_record_key"], "hs:17800")
        self.assertEqual(record["discover_identifier"], "log_abc")
        self.assertEqual(record["hs_id"], "17800")
        self.assertEqual(record["city"], "Bern")
        self.assertTrue(record["has_hotelleriesuisse_origin"])

    def test_fetch_snapshot_paginates_with_next_page_token(self) -> None:
        config = DiscoverSwissConfig(project="dsod-hs", top=-1)
        calls: list[dict[str, list[str]]] = []
        token = '[{"token":"page-2"}]'

        def fake_get(url: str, headers: object, timeout: float) -> dict[str, object]:
            params = parse_qs(urlsplit(url).query)
            calls.append(params)
            self.assertEqual(timeout, 30.0)
            self.assertEqual(headers["Ocp-Apim-Subscription-Key"], "secret-for-test")
            if len(calls) == 1:
                return {
                    "count": 2,
                    "hasNextPage": True,
                    "nextPageToken": token,
                    "data": [lodging("log_a", "100", "Hotel A", "Bern")],
                }
            self.assertEqual(params["continuationToken"], [token])
            return {
                "hasNextPage": False,
                "data": [lodging("log_b", "101", "Hotel B", "Basel")],
            }

        manifest = fetch_hotelleriesuisse_snapshot(
            config,
            "secret-for-test",
            get_json=fake_get,
            fetched_at=datetime(2026, 8, 28, 10, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0]["includeCount"], ["true"])
        self.assertNotIn("includeCount", calls[1])
        self.assertEqual(manifest["reported_count"], 2)
        self.assertEqual(manifest["records_count"], 2)
        self.assertEqual(manifest["api_pages"], 2)
        self.assertTrue(manifest["capture_valid"])
        self.assertFalse(manifest["member_directory_scope_reconciled"])
        self.assertFalse(manifest["crm_freeze_eligible"])

    def test_repeated_continuation_token_fails_closed(self) -> None:
        config = DiscoverSwissConfig()
        token = '[{"token":"same"}]'
        calls = 0

        def fake_get(url: str, headers: object, timeout: float) -> dict[str, object]:
            nonlocal calls
            calls += 1
            return {
                "count": 2 if calls == 1 else None,
                "hasNextPage": True,
                "nextPageToken": token,
                "data": [lodging(f"log_{calls}", str(calls), f"Hotel {calls}", "Bern")],
            }

        with self.assertRaises(PaginationCycleError):
            fetch_hotelleriesuisse_snapshot(config, "key", get_json=fake_get)

    def test_reported_count_mismatch_marks_capture_invalid(self) -> None:
        config = DiscoverSwissConfig()

        def fake_get(url: str, headers: object, timeout: float) -> dict[str, object]:
            return {
                "count": 2,
                "hasNextPage": False,
                "data": [lodging("log_a", "100", "Hotel A", "Bern")],
            }

        manifest = fetch_hotelleriesuisse_snapshot(config, "key", get_json=fake_get)
        self.assertFalse(manifest["capture_valid"])
        self.assertIn("reported_count=2 != records_count=1", manifest["capture_violations"])

    def test_duplicate_hs_id_marks_capture_invalid(self) -> None:
        config = DiscoverSwissConfig()

        def fake_get(url: str, headers: object, timeout: float) -> dict[str, object]:
            return {
                "count": 2,
                "hasNextPage": False,
                "data": [
                    lodging("log_a", "100", "Hotel A", "Bern"),
                    lodging("log_b", "100", "Hotel B", "Basel"),
                ],
            }

        manifest = fetch_hotelleriesuisse_snapshot(config, "key", get_json=fake_get)
        self.assertFalse(manifest["capture_valid"])
        self.assertEqual(manifest["duplicate_hs_ids"], ["100"])
        self.assertIn("duplicate HotellerieSuisse hsId values detected", manifest["capture_violations"])

    def test_missing_hs_origin_or_hs_id_fails_capture_validation(self) -> None:
        config = DiscoverSwissConfig()
        bad = lodging("log_a", "100", "Hotel A", "Bern", hs_origin=False)
        bad["additionalProperty"] = []

        def fake_get(url: str, headers: object, timeout: float) -> dict[str, object]:
            return {"count": 1, "hasNextPage": False, "data": [bad]}

        manifest = fetch_hotelleriesuisse_snapshot(config, "key", get_json=fake_get)
        self.assertFalse(manifest["capture_valid"])
        self.assertEqual(manifest["missing_hs_id"], 1)
        self.assertEqual(manifest["records_without_hotelleriesuisse_origin"], 1)

    def test_subscription_key_never_enters_snapshot_manifest(self) -> None:
        config = DiscoverSwissConfig()
        secret = "VERY-SECRET-SUBSCRIPTION-KEY"

        def fake_get(url: str, headers: object, timeout: float) -> dict[str, object]:
            self.assertEqual(headers["Ocp-Apim-Subscription-Key"], secret)
            return {
                "count": 1,
                "hasNextPage": False,
                "data": [lodging("log_a", "100", "Hotel A", "Bern")],
            }

        manifest = fetch_hotelleriesuisse_snapshot(config, secret, get_json=fake_get)
        self.assertNotIn(secret, json.dumps(manifest, sort_keys=True))

    def test_resolve_subscription_key_requires_environment_variable(self) -> None:
        config = DiscoverSwissConfig(subscription_key_env="DISCOVER_SWISS_TEST_KEY")
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(MissingSubscriptionKey):
                resolve_subscription_key(config)
        with patch.dict(os.environ, {"DISCOVER_SWISS_TEST_KEY": "abc"}, clear=True):
            self.assertEqual(resolve_subscription_key(config), "abc")


if __name__ == "__main__":
    unittest.main()
