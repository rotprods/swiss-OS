import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class NextIdentityReviewWorksetTests(unittest.TestCase):
    def test_remaining36_partition_and_safety(self):
        work = json.loads((ROOT / 'docs/operations/CRM_IDENTITY_REVIEW_WORKSET_500599_REMAINING36_2026-08-30.json').read_text(encoding='utf-8'))
        queue = json.loads((ROOT / work['source_queue_path']).read_text(encoding='utf-8'))
        reviewed = json.loads((ROOT / work['reviewed_wave1_path']).read_text(encoding='utf-8'))
        reviewed_keys = {d['source_record_key'] for d in reviewed['decisions']}
        queue_keys = {i['source_record_key'] for i in queue['items']}
        expected = queue_keys - reviewed_keys - {work['terminal_exception_source_key']}
        batches = work['batches']
        actual = [key for batch in batches for key in batch['source_record_keys']]
        self.assertEqual(len(queue_keys), 47)
        self.assertEqual(len(reviewed_keys), 10)
        self.assertEqual(len(expected), 36)
        self.assertEqual(len(actual), 36)
        self.assertEqual(len(actual), len(set(actual)))
        self.assertEqual(set(actual), expected)
        self.assertEqual([len(b['source_record_keys']) for b in batches], [10, 10, 10, 6])
        self.assertEqual(actual, sorted(actual))
        self.assertFalse(work['safety']['authority_advanced'])
        self.assertEqual(work['safety']['canonical_id_reservations'], 0)
        self.assertEqual(work['safety']['h_id_allocations'], 0)
        self.assertEqual(work['safety']['outbound'], 'CLOSED')
        self.assertEqual(work['safety']['send_allowed'], 0)

if __name__ == '__main__':
    unittest.main()
