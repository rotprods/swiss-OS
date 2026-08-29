from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from swiss_os.candidate_export_materialize import materialize_candidate_export


class CandidateExportMaterializeTests(unittest.TestCase):
    def test_materializes_current_candidate_export_without_authority_mutation(self) -> None:
        root = Path(__file__).resolve().parents[1]
        manifest_path = root / "docs/state/CRM_CANDIDATE_EXPORT_33206402141.manifest.json"
        with tempfile.TemporaryDirectory() as tmp:
            report = materialize_candidate_export(root, manifest_path, Path(tmp))
            payload = json.loads((Path(tmp) / "CRM_CANDIDATE_EXPORT.json").read_text(encoding="utf-8"))

        self.assertEqual(report["schema_version"], "CRM-CANDIDATE-EXPORT-MATERIALIZE-1.0")
        self.assertEqual(report["snapshot_id"], "HS-MEMBER-DE-33206402141")
        self.assertEqual(report["records_count"], 1438)
        self.assertEqual(report["records_sha256"], "34d9aa9cfa4fe896bf1db8fba4dedfded9a1dbf2e135b847101904644d16bba0")
        self.assertEqual(report["source_records"], 2061)
        self.assertEqual(report["exact_name_city_matches"], 623)
        self.assertFalse(report["authority_advanced"])
        self.assertEqual(report["h_id_allocations"], 0)
        self.assertEqual(report["outbound"], "CLOSED")
        self.assertEqual(report["send_allowed"], 0)

        self.assertEqual(payload["records_count"], 1438)
        self.assertEqual(len(payload["records"]), 1438)
        self.assertFalse(payload["authority_advanced"])
        self.assertEqual(payload["h_id_allocations"], 0)
        self.assertEqual(payload["outbound"], "CLOSED")
        self.assertEqual(payload["send_allowed"], 0)


if __name__ == "__main__":
    unittest.main()
