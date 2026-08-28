from __future__ import annotations

import unittest

from swiss_os.source_scope import (
    EXACT,
    EXPLAINED,
    UNRESOLVED,
    ScopeExplanation,
    build_candidate_snapshot,
    reconcile_source_scope,
)


def api_manifest(records):
    return {
        "snapshot_id": "DS-HS-TEST",
        "capture_valid": True,
        "records": records,
    }


def directory_manifest(records, *, complete=True):
    return {
        "snapshot_id": "MD-TEST",
        "observed_at": "2026-08-28T12:00:00Z",
        "coverage_complete": complete,
        "records": records,
    }


class SourceScopeTests(unittest.TestCase):
    def test_exact_hsid_reconciliation_passes(self):
        api = api_manifest([
            {"source_record_key": "hs:100", "hs_id": "100", "name": "Hotel Alpha", "city": "Bern", "links": []},
            {"source_record_key": "hs:200", "hs_id": "200", "name": "Hotel Beta", "city": "Zürich", "links": []},
        ])
        directory = directory_manifest([
            {"record_id": "md-a", "hs_id": "100", "name": "Alpha", "city": "Bern", "evidence_ref": "ev:a"},
            {"record_id": "md-b", "hs_id": "200", "name": "Beta", "city": "Zürich", "evidence_ref": "ev:b"},
        ])
        result = reconcile_source_scope(api, directory)
        self.assertEqual(EXACT, result.state)
        self.assertTrue(result.reconciled)
        self.assertEqual(2, result.matched_count)
        candidate = build_candidate_snapshot(api, directory, result)
        self.assertTrue(candidate["crm_freeze_eligible"])
        self.assertEqual("FROZEN_CANDIDATE", candidate["snapshot_state"])
        self.assertFalse(candidate["authority_advanced"])
        self.assertEqual(0, candidate["h_id_allocations"])

    def test_name_city_fallback_is_supported_when_unique(self):
        api = api_manifest([
            {"source_record_key": "discover:a", "hs_id": "", "name": " Hôtel du Lac ", "city": "Genève", "links": []},
        ])
        directory = directory_manifest([
            {"record_id": "md-a", "name": "hôtel du lac", "city": "Genève", "evidence_ref": "ev:a"},
        ])
        result = reconcile_source_scope(api, directory)
        self.assertEqual(EXACT, result.state)
        self.assertEqual("EXACT_NAME_CITY", result.matches[0].match_basis)

    def test_count_equality_does_not_hide_scope_delta(self):
        api = api_manifest([
            {"source_record_key": "hs:100", "hs_id": "100", "name": "Alpha", "city": "Bern", "links": []},
        ])
        directory = directory_manifest([
            {"record_id": "md-z", "hs_id": "999", "name": "Zulu", "city": "Bern", "evidence_ref": "ev:z"},
        ])
        result = reconcile_source_scope(api, directory)
        self.assertEqual(UNRESOLVED, result.state)
        self.assertEqual(1, result.api_count)
        self.assertEqual(1, result.directory_count)
        self.assertEqual(0, result.matched_count)
        candidate = build_candidate_snapshot(api, directory, result)
        self.assertFalse(candidate["crm_freeze_eligible"])
        self.assertEqual("STAGED", candidate["snapshot_state"])

    def test_explicit_evidence_backed_delta_can_be_explained(self):
        api = api_manifest([
            {"source_record_key": "hs:100", "hs_id": "100", "name": "Alpha", "city": "Bern", "links": []},
            {"source_record_key": "hs:retired", "hs_id": "retired", "name": "Old Hotel", "city": "Bern", "links": []},
        ])
        directory = directory_manifest([
            {"record_id": "md-a", "hs_id": "100", "name": "Alpha", "city": "Bern", "evidence_ref": "ev:a"},
        ])
        explanation = ScopeExplanation("API", "hs:retired", "REMOVED_FROM_PUBLIC_MEMBER_DIRECTORY", "ev:retired")
        result = reconcile_source_scope(api, directory, (explanation,))
        self.assertEqual(EXPLAINED, result.state)
        self.assertTrue(result.reconciled)
        candidate = build_candidate_snapshot(api, directory, result, (explanation,))
        self.assertTrue(candidate["crm_freeze_eligible"])
        self.assertEqual(["hs:retired"], candidate["reconciliation"]["explained_api_only"])

    def test_unexplained_delta_fails_closed(self):
        api = api_manifest([
            {"source_record_key": "hs:100", "hs_id": "100", "name": "Alpha", "city": "Bern", "links": []},
            {"source_record_key": "hs:200", "hs_id": "200", "name": "Beta", "city": "Bern", "links": []},
        ])
        directory = directory_manifest([
            {"record_id": "md-a", "hs_id": "100", "name": "Alpha", "city": "Bern", "evidence_ref": "ev:a"},
        ])
        result = reconcile_source_scope(api, directory)
        self.assertEqual(UNRESOLVED, result.state)
        self.assertEqual(("hs:200",), result.api_only)

    def test_partial_directory_evidence_is_rejected(self):
        with self.assertRaises(ValueError):
            reconcile_source_scope(api_manifest([]), directory_manifest([], complete=False))

    def test_ambiguous_name_city_fails_closed(self):
        api = api_manifest([
            {"source_record_key": "discover:a", "hs_id": "", "name": "Hotel Same", "city": "Bern", "links": []},
            {"source_record_key": "discover:b", "hs_id": "", "name": "Hotel Same", "city": "Bern", "links": []},
        ])
        directory = directory_manifest([
            {"record_id": "md-a", "name": "Hotel Same", "city": "Bern", "evidence_ref": "ev:a"},
        ])
        result = reconcile_source_scope(api, directory)
        self.assertEqual(UNRESOLVED, result.state)
        self.assertTrue(any(item.startswith("AMBIGUOUS_NAME_CITY:") for item in result.conflicts))

    def test_duplicate_explanation_is_rejected(self):
        api = api_manifest([{"source_record_key": "hs:1", "hs_id": "1", "name": "A", "city": "B", "links": []}])
        directory = directory_manifest([])
        e = ScopeExplanation("API", "hs:1", "REASON", "ev:1")
        with self.assertRaises(ValueError):
            reconcile_source_scope(api, directory, (e, e))


if __name__ == "__main__":
    unittest.main()
