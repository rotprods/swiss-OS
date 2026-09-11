import unittest

from swiss_os.repo_semantics import chunk_text
from swiss_os.semantic_index import (
    COS20_VECTOR_NAME,
    SEMANTIC_VECTOR_NAME,
    OllamaEmbeddingClient,
    QdrantRepoIndex,
    SearchHit,
    SemanticGraphEngine,
    SemanticIndexError,
    build_qdrant_point,
    qdrant_point_id,
    reciprocal_rank_fusion,
)


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, payload=None, *, timeout=60.0):
        self.calls.append((method, url, payload, timeout))
        if not self.responses:
            raise AssertionError("no fake response left")
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


class SemanticIndexTests(unittest.TestCase):
    def test_ollama_embed_uses_current_api_and_batches(self):
        transport = FakeTransport([{
            "embeddings": [[1, 2, 3], [4, 5, 6]],
            "total_duration": 10,
            "load_duration": 2,
            "prompt_eval_count": 8,
        }])
        client = OllamaEmbeddingClient(model="qwen3-embedding:0.6b", transport=transport)
        result = client.embed(["a", "b"])
        self.assertEqual(result.dimension, 3)
        method, url, payload, _ = transport.calls[0]
        self.assertEqual(method, "POST")
        self.assertTrue(url.endswith("/api/embed"))
        self.assertEqual(payload["input"], ["a", "b"])
        self.assertFalse(payload["truncate"])

    def test_qdrant_create_uses_named_vectors(self):
        transport = FakeTransport([
            SemanticIndexError("HTTP 404 from collection"),
            {"result": True},
        ])
        index = QdrantRepoIndex(collection="x", transport=transport)
        state = index.ensure_collection(768)
        self.assertEqual(state, "CREATED")
        payload = transport.calls[1][2]
        self.assertEqual(payload["vectors"][SEMANTIC_VECTOR_NAME]["size"], 768)
        self.assertEqual(payload["vectors"][COS20_VECTOR_NAME]["size"], 20)
        self.assertEqual(payload["vectors"][COS20_VECTOR_NAME]["distance"], "Cosine")

    def test_qdrant_rejects_dimension_drift(self):
        transport = FakeTransport([{
            "result": {"config": {"params": {"vectors": {
                "semantic": {"size": 1024}, "cos20": {"size": 20}
            }}}}
        }])
        index = QdrantRepoIndex(collection="x", transport=transport)
        with self.assertRaises(SemanticIndexError):
            index.ensure_collection(768)

    def test_point_id_and_payload_are_deterministic(self):
        chunk = chunk_text("a.py", "def x():\n    return 1\n", max_chars=512)[0]
        point_a = build_qdrant_point(chunk, [0.1, 0.2], repo="rotprods/swiss-OS", git_sha="a"*40, model="m")
        point_b = build_qdrant_point(chunk, [0.1, 0.2], repo="rotprods/swiss-OS", git_sha="a"*40, model="m")
        self.assertEqual(point_a, point_b)
        self.assertEqual(point_a["id"], qdrant_point_id(chunk.chunk_id))
        self.assertEqual(len(point_a["vector"]["cos20"]), 20)
        self.assertEqual(point_a["payload"]["index_authority"], "DERIVED_NON_AUTHORITATIVE_RETRIEVAL_INDEX")

    def test_rrf_prefers_semantic_but_preserves_cos_signal(self):
        a = SearchHit("a", 0.9, {"path": "a"}, semantic_score=0.9)
        b = SearchHit("b", 0.8, {"path": "b"}, semantic_score=0.8)
        b_cos = SearchHit("b", 0.95, {"path": "b"}, cos20_score=0.95)
        c_cos = SearchHit("c", 0.9, {"path": "c"}, cos20_score=0.9)
        hits = reciprocal_rank_fusion([a, b], [b_cos, c_cos], limit=3)
        self.assertEqual(hits[0].point_id, "b")
        self.assertIsNotNone(hits[0].semantic_score)
        self.assertIsNotNone(hits[0].cos20_score)

    def test_engine_index_batches_once_and_verifies_count(self):
        chunks = chunk_text("a.md", "# A\none\n\n# B\ntwo\n\n# C\nthree\n", max_chars=512)

        class FakeEmbedder:
            model = "fake-model"
            def __init__(self):
                self.calls = []
            def embed(self, inputs):
                from swiss_os.semantic_index import EmbedBatchResult
                self.calls.append(list(inputs))
                vectors = tuple((float(i + 1), 0.5, 0.25) for i, _ in enumerate(inputs))
                return EmbedBatchResult(vectors, 0.001, None, None, len(inputs))
            def embed_one(self, text):
                return (1.0, 0.5, 0.25)

        class FakeQdrant:
            def __init__(self):
                self.points = []
                self.dim = None
            def ensure_collection(self, dim, recreate=False):
                self.dim = dim
                return "CREATED"
            def delete_repo_points(self, repo):
                self.points.clear()
            def upsert(self, points):
                self.points.extend(points)
            def count(self, repo=None):
                return len(self.points)

        embedder = FakeEmbedder()
        qdrant = FakeQdrant()
        engine = SemanticGraphEngine(embedder, qdrant)
        stats = engine.index(chunks, repo="r", git_sha="a" * 40, batch_size=2)
        self.assertEqual(stats.chunks, len(chunks))
        self.assertEqual(qdrant.dim, 3)
        self.assertEqual(len(qdrant.points), len(chunks))
        self.assertEqual(len(embedder.calls), 3)  # probe, remainder of first batch, second batch


if __name__ == "__main__":
    unittest.main()
