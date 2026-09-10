import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class LocalityContractDocTests(unittest.TestCase):
    def test_contract_preserves_review_only_semantics(self):
        text=(ROOT/'docs/operations/LOCALITY_NORMALIZATION_CONTRACT_V1.md').read_text(encoding='utf-8')
        for phrase in (
            'MUST NOT prove same-property identity',
            'MUST NOT create a source mapping',
            'MUST NOT reserve or allocate an H-ID',
            'MUST NOT mutate canonical authority',
            'MUST NOT open outbound',
            'MULTIPLE_CANONICAL_LOCALITY_CANDIDATES',
        ):
            self.assertIn(phrase,text)


if __name__=='__main__':
    unittest.main()
