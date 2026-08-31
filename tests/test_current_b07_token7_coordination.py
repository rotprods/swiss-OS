from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


class CurrentB07Token7CoordinationTest(unittest.TestCase):
    def test_token6_is_superseded_and_token7_is_only_active_claim(self):
        old = load("docs/state/v2/claims/CLAIM-CRM-SRR-SPECIAL-006.json")
        new = load("docs/state/v2/claims/CLAIM-CRM-CURRENT-B07-007.json")
        active = load("docs/state/v2/active-claims.json")
        self.assertEqual(old["state"], "SUPERSEDED")
        self.assertEqual(old["superseded_by"], new["claim_id"])
        self.assertEqual(new["fencing_token"], 7)
        self.assertEqual(active["fencing_high_watermark"], 7)
        self.assertEqual([row["claim_id"] for row in active["claims"]], [new["claim_id"]])
        self.assertEqual(active["collisions"], [])

    def test_projection_context_and_csp_are_coherent_without_recursive_digest_cycle(self):
        project = load("docs/state/v2/project-state.json")
        context = load("docs/state/v2/context-pack.json")
        graph = load("docs/state/v2/graph-snapshot.json")
        csp = load("docs/continuity/CONTEXT_SURVIVAL.json")
        self.assertEqual(project["projection_revision"], graph["projection_revision"])
        self.assertEqual(graph["context_pack_revision"], context["context_pack_revision"])
        self.assertEqual(csp["projection_revision"], project["projection_revision"])
        self.assertEqual(csp["context_pack_revision"], context["context_pack_revision"])
        self.assertNotIn("context_pack_revision", project)
        self.assertEqual(project["active_claim_ids"], ["CLAIM-CRM-CURRENT-B07-007"])
        self.assertEqual(context["active_claim_ids"], ["CLAIM-CRM-CURRENT-B07-007"])
        self.assertEqual(csp["active_claim_ids"], ["CLAIM-CRM-CURRENT-B07-007"])
        self.assertEqual(csp["production_route"], "COMPUTE_CURRENT_UNRESOLVED_LT350000_ZERO_CANONICAL_CITY_B08_FROM_PINNED_LINEAGE")
        self.assertEqual(csp["latest_domain_next"], "docs/state/NEXT_CURRENT_UNRESOLVED_LT350_B07.json")

    def test_safety_ceiling_is_preauthority_only_everywhere(self):
        nxt = load("docs/state/NEXT.json")
        b07 = load("docs/state/CRM_CURRENT_UNRESOLVED_LT350_B07_2026-09-01.json")
        graph = load("docs/state/v2/graph-snapshot.json")
        csp = load("docs/continuity/CONTEXT_SURVIVAL.json")
        self.assertFalse(nxt["safety"]["authority_advanced"])
        self.assertFalse(nxt["safety"]["authority_advance_allowed"])
        self.assertFalse(nxt["safety"]["canonical_id_allocation_allowed"])
        self.assertEqual(nxt["safety"]["h_id_allocations"], 0)
        self.assertEqual(nxt["safety"]["canonical_id_reservations"], 0)
        self.assertEqual(nxt["safety"]["outbound"], "CLOSED")
        self.assertEqual(nxt["safety"]["send_allowed"], 0)
        self.assertFalse(b07["qa"]["authority_advanced"])
        self.assertEqual(graph["h_id_allocations"], 0)
        self.assertEqual(graph["outbound"], "CLOSED")
        self.assertEqual(csp["safety"]["send_allowed"], 0)


if __name__ == "__main__":
    unittest.main()
