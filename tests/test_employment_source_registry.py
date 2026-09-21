import copy
import json
import unittest
from pathlib import Path

from swiss_os.employment_source_registry import SourceSurface, load_registry, validate_registry

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs" / "state" / "employment" / "SOURCE_REGISTRY_V1_2026-09-21.json"


class EmploymentSourceRegistryTests(unittest.TestCase):
    def payload(self):
        return json.loads(REGISTRY.read_text(encoding="utf-8"))

    def test_registry_validates_and_never_claims_national_completeness(self):
        registry = load_registry(REGISTRY)
        self.assertGreaterEqual(len(registry.surfaces), 10)
        payload = self.payload()
        self.assertIs(payload["claim_national_completeness"], False)
        self.assertEqual(payload["outbound"], "CLOSED")
        self.assertEqual(payload["send_allowed"], 0)

    def test_jobcloud_is_one_family_three_physical_surfaces_and_manual_only(self):
        registry = load_registry(REGISTRY)
        jobcloud = [s for s in registry.surfaces if s.source_family_id == "FAM-JOBCLOUD"]
        self.assertEqual({s.source_id for s in jobcloud}, {"SRC-003", "SRC-004", "SRC-005"})
        self.assertTrue(all(s.automation_policy == "PROHIBITED" for s in jobcloud))
        self.assertTrue(all(set(s.capture_modes) <= {"MANUAL_WEB", "SEARCH_ENGINE_DISCOVERY"} for s in jobcloud))

    def test_guidance_and_jobroom_publication_api_are_not_inventory(self):
        registry = load_registry(REGISTRY)
        by_id = {s.source_id: s for s in registry.surfaces}
        self.assertEqual(by_id["SRC-002"].surface_type, "GUIDANCE_SURFACE")
        self.assertFalse(by_id["SRC-002"].inventory_role)
        self.assertEqual(by_id["SRC-026"].api_role, "PUBLICATION_ONLY")
        self.assertFalse(by_id["SRC-026"].inventory_role)

    def test_unknown_policy_fails_closed_for_automated_read(self):
        surface = SourceSurface(
            source_id="SRC-TEST", source_family_id="FAM-TEST", name="x",
            canonical_url="https://example.test/jobs", surface_type="NATIONAL_JOB_BOARD",
            scope="TEST", languages=(), niche_ids=(), inventory_role=True,
            automation_policy="UNKNOWN_REQUIRES_REVIEW", capture_modes=("OFFICIAL_READ_API",),
            canonicality="DISCOVERY", observed_at="2026-09-21T00:00:00Z",
            evidence_refs=("https://example.test/terms",), api_role="READ_INVENTORY",
        )
        with self.assertRaisesRegex(ValueError, "explicit AUTHORIZED"):
            surface.validate()

    def test_prohibited_policy_cannot_hide_automated_capture(self):
        surface = SourceSurface(
            source_id="SRC-TEST", source_family_id="FAM-TEST", name="x",
            canonical_url="https://example.test/jobs", surface_type="NATIONAL_JOB_BOARD",
            scope="TEST", languages=(), niche_ids=(), inventory_role=True,
            automation_policy="PROHIBITED", capture_modes=("OFFICIAL_READ_API",),
            canonicality="DISCOVERY", observed_at="2026-09-21T00:00:00Z",
            evidence_refs=("https://example.test/terms",), api_role="READ_INVENTORY",
        )
        with self.assertRaises(ValueError):
            surface.validate()

    def test_discovery_program_and_guidance_are_not_promoted_to_inventory(self):
        registry = load_registry(REGISTRY)
        self.assertTrue(all(p.purpose == "DISCOVERY_ONLY" for p in registry.discovery_programs))
        source_by_id = {s.source_id: s for s in registry.surfaces}
        self.assertTrue(all(source_by_id[g.source_id].surface_type == "GUIDANCE_SURFACE"
                            for g in registry.guidance_surfaces))

    def test_completeness_claim_or_send_gate_is_rejected(self):
        payload = self.payload()
        bad = copy.deepcopy(payload)
        bad["claim_national_completeness"] = True
        with self.assertRaisesRegex(ValueError, "national completeness"):
            validate_registry(bad)
        bad = copy.deepcopy(payload)
        bad["send_allowed"] = 1
        with self.assertRaisesRegex(ValueError, "outbound"):
            validate_registry(bad)


if __name__ == "__main__":
    unittest.main()
