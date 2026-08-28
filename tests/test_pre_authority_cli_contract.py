import unittest
from pathlib import Path


class PreAuthorityCliContractTests(unittest.TestCase):
    def test_pab_operating_contract_is_persisted(self):
        path = Path('docs/operations/WOP_CRM_UNIVERSE_NEXT_WAVE_2026-08-28.md')
        self.assertTrue(path.exists())
        text = path.read_text(encoding='utf-8')
        normalized = text.upper()
        for token in (
            'FROZEN_CANDIDATE_READY',
            'BLOCKED_PRE_AUTHORITY',
            'AUTHORITY_ADVANCED = FALSE',
            'H_ID_ALLOCATIONS = 0',
            'OUTBOUND_OPENED = FALSE',
            'RECONCILE_REQUIRED = 0',
            'UNMAPPED = 0',
        ):
            self.assertIn(token, normalized)


if __name__ == '__main__':
    unittest.main()
