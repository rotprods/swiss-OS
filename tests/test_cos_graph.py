import math
import unittest

from swiss_os.cos_graph import COS_DIMENSIONS, cos20_features, cosine_similarity


class CosGraphTests(unittest.TestCase):
    def test_exactly_twenty_dimensions_and_reserved_tail_zero(self):
        result = cos20_features("agent session claim fencing token workflow retry qdrant graph retrieval")
        self.assertEqual(len(result.vector), 20)
        self.assertEqual(len(COS_DIMENSIONS), 20)
        self.assertEqual(result.vector[17:], (0.0, 0.0, 0.0))
        self.assertAlmostEqual(math.sqrt(sum(x*x for x in result.vector)), 1.0, places=9)

    def test_agent_workflow_query_activates_expected_layers(self):
        result = cos20_features("agent session claim fencing token workflow idempotency retry")
        active = set(result.active_dimensions)
        self.assertIn("L13:Agent", active)
        self.assertIn("L15:Workflow", active)

    def test_graph_retrieval_activates_graphrag_and_similarity(self):
        result = cos20_features("cosine vector embedding nearest neighbor GraphRAG qdrant retrieval")
        self.assertGreater(result.raw_scores[10], 0)
        self.assertGreater(result.raw_scores[11], 0)

    def test_generic_text_never_becomes_zero_vector(self):
        result = cos20_features("xyzzy plugh")
        self.assertGreater(sum(abs(v) for v in result.vector), 0)

    def test_cosine(self):
        self.assertAlmostEqual(cosine_similarity([1, 0], [1, 0]), 1.0)
        self.assertAlmostEqual(cosine_similarity([1, 0], [0, 1]), 0.0)


if __name__ == "__main__":
    unittest.main()
