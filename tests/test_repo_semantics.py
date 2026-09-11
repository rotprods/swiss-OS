import tempfile
import unittest
from pathlib import Path

from swiss_os.repo_semantics import chunk_repository, chunk_text, graphify_chunks


class RepoSemanticsTests(unittest.TestCase):
    def test_python_chunking_is_symbol_aware_and_deterministic(self):
        source = """import os\n\n\ndef alpha(x):\n    return x + 1\n\n\nclass Beta:\n    def run(self):\n        return alpha(1)\n"""
        a = chunk_text("src/demo.py", source, max_chars=512, overlap_lines=1)
        b = chunk_text("src/demo.py", source, max_chars=512, overlap_lines=1)
        self.assertEqual([c.chunk_id for c in a], [c.chunk_id for c in b])
        self.assertIn("alpha", {c.symbol for c in a})
        self.assertIn("Beta", {c.symbol for c in a})
        self.assertTrue(all(c.start_line <= c.end_line for c in a))

    def test_markdown_chunks_follow_headings(self):
        source = "# One\ntext\n\n## Two\nmore\n"
        chunks = chunk_text("docs/a.md", source, max_chars=512)
        self.assertEqual([c.symbol for c in chunks], ["One", "Two"])
        self.assertEqual([c.kind for c in chunks], ["markdown-h1", "markdown-h2"])

    def test_repository_scan_skips_binary_and_private_generated_dirs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "src").mkdir()
            (root / "src" / "a.py").write_text("def x():\n    return 1\n", encoding="utf-8")
            (root / ".swiss-os").mkdir()
            (root / ".swiss-os" / "generated.txt").write_text("ignore", encoding="utf-8")
            (root / "pic.png").write_bytes(b"\x89PNG\x00")
            chunks, stats = chunk_repository(root)
            self.assertEqual({c.path for c in chunks}, {"src/a.py"})
            self.assertEqual(stats.files_indexed, 1)

    def test_graphify_emits_file_chunk_and_symbol_edges(self):
        chunks = chunk_text("src/demo.py", "def alpha():\n    return 1\n", max_chars=512)
        nodes, edges = graphify_chunks(chunks)
        relations = {e.relation for e in edges}
        self.assertIn("CONTAINS", relations)
        self.assertIn("DEFINES", relations)
        self.assertIn("IMPLEMENTED_BY", relations)
        self.assertEqual(len({n.node_id for n in nodes}), len(nodes))


if __name__ == "__main__":
    unittest.main()
