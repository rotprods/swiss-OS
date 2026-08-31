import unittest
from unittest.mock import patch

from swiss_os.market_enrichment import FetchResult
from swiss_os.vacancy_detail import aggregate_shards
from swiss_os.vacancy_detail_fault_isolation import (
    PUBLIC_URL_SAFETY_ERRORS,
    ROUTE_REJECTION_STATE,
    compile_shard_fault_isolated,
    resolve_route_isolated,
)


class FakeClient:
    def __init__(self, pages=None):
        self.pages = pages or {}

    def fetch(self, url, respect_robots=True):
        body = self.pages.get(url)
        if body is None:
            return FetchResult(url, None, "FETCH_FAILED", None, None, None, "MissingFixture")
        return FetchResult(url, url, "FETCHED", 200, "abc123", body, None)


def market_record(record_id, routes):
    return {
        "record_id": record_id,
        "name": record_id,
        "city": "Davos",
        "e07_vacancy": {"opening_routes": routes},
        "safety": {
            "authority_advanced": False,
            "canonical_id_allocations": 0,
            "canonical_id_reservations": 0,
            "outbound": "CLOSED",
            "send_allowed": 0,
            "irreversible_external_actions": 0,
        },
    }


def market_aggregate(records):
    return {
        "source_records": 2061,
        "source_snapshot_id": "S",
        "records": records,
        "safety": {
            "authority_advanced": False,
            "outbound": "CLOSED",
            "send_allowed": 0,
            "irreversible_external_actions": 0,
        },
    }


class VacancyDetailFaultIsolationTests(unittest.TestCase):
    def test_all_known_public_url_safety_value_errors_become_typed_rejections(self):
        self.assertEqual(
            PUBLIC_URL_SAFETY_ERRORS,
            {
                "only public HTTPS URLs are allowed",
                "URL credentials/non-standard ports are forbidden",
                "hostname must resolve only to public addresses",
            },
        )
        for message in PUBLIC_URL_SAFETY_ERRORS:
            with self.subTest(message=message), patch(
                "swiss_os.vacancy_detail_fault_isolation.resolve_route",
                side_effect=ValueError(message),
            ):
                result = resolve_route_isolated(FakeClient(), "https://example.com/jobs", "2026-08-31T20:10:00Z")
            self.assertEqual(result["resolution_state"], ROUTE_REJECTION_STATE)
            self.assertEqual(result["fetch_state"], "URL_REJECTED")
            self.assertEqual(result["role_signals"], [])
            self.assertFalse(result["no_openings_explicit"])
            self.assertEqual(result["authority_effect"], "NONE")
            self.assertEqual(result["outbound"], "CLOSED")
            self.assertEqual(result["send_allowed"], 0)

    def test_unrecognized_value_error_is_not_mislabeled_as_security(self):
        with patch(
            "swiss_os.vacancy_detail_fault_isolation.resolve_route",
            side_effect=ValueError("unexpected parser invariant"),
        ):
            with self.assertRaisesRegex(ValueError, "unexpected parser invariant"):
                resolve_route_isolated(FakeClient(), "https://example.com/jobs", "2026-08-31T20:10:00Z")

    def test_non_safety_runtime_failure_is_not_silently_swallowed(self):
        with patch(
            "swiss_os.vacancy_detail_fault_isolation.resolve_route",
            side_effect=RuntimeError("programmer bug"),
        ):
            with self.assertRaises(RuntimeError):
                resolve_route_isolated(FakeClient(), "https://example.com/jobs", "2026-08-31T20:10:00Z")

    def test_rejected_route_does_not_destroy_other_route_or_record(self):
        bad = "https://bad.example/jobs"
        good = "https://good.example/jobs/housekeeping"
        data = market_aggregate([market_record("a", [bad, good])])
        client = FakeClient({good: "<html><body><h1>Housekeeping Attendant</h1></body></html>"})

        def fake_resolve(client_arg, url, observed_at):
            if url == bad:
                raise ValueError("hostname must resolve only to public addresses")
            return {
                "requested_url": url,
                "final_url": url,
                "fetch_state": "FETCHED",
                "http_status": 200,
                "body_sha256": "abc",
                "observed_at": observed_at,
                "role_signals": [{"title": "Housekeeping Attendant", "source_url": url}],
                "language_signal_snippets": [],
                "experience_signal_snippets": [],
                "start_signal_snippets": [],
                "housing_signal": False,
                "contact_emails": [],
                "no_openings_explicit": False,
                "resolution_state": "CURRENT_ROLE_SIGNALS_FOUND",
                "authority_effect": "NONE",
                "outbound": "CLOSED",
                "send_allowed": 0,
            }

        with patch("swiss_os.vacancy_detail_fault_isolation.resolve_route", side_effect=fake_resolve):
            shard = compile_shard_fault_isolated(
                data,
                shard_index=0,
                shard_count=1,
                observed_at="2026-08-31T20:10:00Z",
                client=client,
            )

        self.assertEqual(len(shard["records"]), 1)
        self.assertEqual(shard["route_rejections"], 1)
        self.assertEqual(shard["records"][0]["route_rejections"], 1)
        self.assertEqual(shard["records"][0]["role_signal_count"], 1)
        self.assertEqual(shard["records"][0]["current_role_signal_titles"], ["Housekeeping Attendant"])
        self.assertEqual(shard["outbound"], "CLOSED")
        self.assertEqual(shard["send_allowed"], 0)

    def test_fault_isolated_shard_remains_aggregate_compatible(self):
        data = market_aggregate([
            market_record("a", ["https://a.example/jobs"]),
            market_record("b", ["https://b.example/jobs"]),
        ])

        def fake_resolve(client_arg, url, observed_at):
            if "a.example" in url:
                raise ValueError("hostname must resolve only to public addresses")
            return {
                "requested_url": url,
                "final_url": url,
                "fetch_state": "FETCHED",
                "http_status": 200,
                "body_sha256": "abc",
                "observed_at": observed_at,
                "role_signals": [{"title": "Kitchen Helper", "source_url": url}],
                "language_signal_snippets": [],
                "experience_signal_snippets": [],
                "start_signal_snippets": [],
                "housing_signal": False,
                "contact_emails": [],
                "no_openings_explicit": False,
                "resolution_state": "CURRENT_ROLE_SIGNALS_FOUND",
                "authority_effect": "NONE",
                "outbound": "CLOSED",
                "send_allowed": 0,
            }

        with patch("swiss_os.vacancy_detail_fault_isolation.resolve_route", side_effect=fake_resolve):
            s0 = compile_shard_fault_isolated(data, shard_index=0, shard_count=2, observed_at="T", client=FakeClient())
            s1 = compile_shard_fault_isolated(data, shard_index=1, shard_count=2, observed_at="T", client=FakeClient())
        combined = aggregate_shards(data, [s0, s1])
        self.assertEqual(combined["workset_total"], 2)
        self.assertEqual(combined["route_resolution_states"][ROUTE_REJECTION_STATE], 1)
        self.assertEqual(combined["role_signal_hotels"], 1)
        self.assertFalse(combined["authority_advanced"])
        self.assertEqual(combined["send_allowed"], 0)


if __name__ == "__main__":
    unittest.main()
