import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from swiss_os.semantic_graph_cli import cos_graph_main, graphify_main


class SemanticGraphCliTests(unittest.TestCase):
    def test_graphify_scan_writes_manifest_and_graph(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "a.py").write_text("def alpha():\n    return 1\n", encoding="utf-8")
            graph = root / "out" / "graph.jsonl"
            manifest = root / "out" / "manifest.json"
            with contextlib.redirect_stdout(io.StringIO()):
                code = graphify_main([
                    "scan", "--repo", str(root), "--graph-out", str(graph), "--manifest-out", str(manifest),
                ])
            self.assertEqual(code, 0)
            payload = json.loads(manifest.read_text())
            self.assertEqual(payload["authority"], "DERIVED_NON_AUTHORITATIVE_REPOSITORY_INDEX")
            self.assertEqual(payload["cos20"]["reserved_dimensions_nonzero"], 0)
            self.assertTrue(graph.exists())

    def test_cos_explain_is_twenty_dimensional(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cos_graph_main(["explain", "agent session workflow retry graph retrieval"])
        self.assertEqual(code, 0)
        payload = json.loads(out.getvalue())
        self.assertEqual(len(payload["vector"]), 20)


if __name__ == "__main__":
    unittest.main()
