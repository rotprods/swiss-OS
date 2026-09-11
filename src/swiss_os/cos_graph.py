from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Sequence

from .repo_semantics import RepoChunk


COS_DIMENSIONS: tuple[tuple[str, str], ...] = (
    ("L0", "Visual"),
    ("L1", "Execution"),
    ("L2", "State"),
    ("L3", "Dependency"),
    ("L4", "Call"),
    ("L5", "Control"),
    ("L6", "DataFlow"),
    ("L7", "Compute"),
    ("L8", "Knowledge"),
    ("L9", "Semantic"),
    ("L10", "Similarity"),
    ("L11", "GraphRAG"),
    ("L12", "Memory"),
    ("L13", "Agent"),
    ("L14", "Tool"),
    ("L15", "Workflow"),
    ("L16", "Network"),
    ("L17", "Reserved"),
    ("L18", "Reserved"),
    ("L19", "Reserved"),
)

# Tokens deliberately follow docs/architecture/V2_GRAPH_MODEL.md. L17-L19 remain zero
# until their domain-specific meaning is explicitly justified in the canonical model.
_DIMENSION_TERMS: tuple[tuple[str, ...], ...] = (
    ("mermaid", "diagram", "visual", "svg", "render", "projection", "topology", "ui", "html", "css"),
    ("goal", "objective", "task", "checkpoint", "definition of done", "acceptance", "execute", "execution", "north star", "scheduler"),
    ("state", "transition", "session", "claim", "release", "active", "blocked", "completed", "superseded", "epoch", "watermark"),
    ("depend", "requires", "required by", "blocks", "blocked by", "precedes", "follows", "import", "dependency", "coupling"),
    ("function", "class", "method", "call", "calls", "called by", "def ", "async def", "import ", "from ", "interface"),
    ("fail closed", "guard", "invariant", "error", "exception", "raise", "if ", "else", "validate", "reject", "security"),
    ("input", "output", "source", "evidence", "read", "write", "transform", "payload", "schema", "manifest", "dataflow", "ingest"),
    ("compute", "performance", "latency", "throughput", "benchmark", "batch", "replay", "complexity", "memory usage", "cpu", "runtime"),
    ("fact", "claim", "assumption", "hypothesis", "insight", "decision", "rule", "pattern", "knowledge", "evidence", "provenance"),
    ("semantic", "lexicon", "term", "definition", "meaning", "ontology", "canonical", "normalize", "naming"),
    ("similarity", "cosine", "nearest", "dedupe", "duplicate", "distance", "embedding", "vector", "ranking"),
    ("graph", "graphrag", "rag", "retrieval", "retrieve", "context", "neighbor", "edge", "node", "hypergraph", "qdrant"),
    ("memory", "context pack", "history", "historical", "recovery", "restore", "handoff", "persist", "persistence", "cache"),
    ("agent", "session", "claim", "lease", "fencing", "handoff", "role", "capability", "tool invocation", "autoresearch"),
    ("tool", "provider", "connector", "capability", "permission", "fallback", "github", "drive", "sheets", "ollama", "qdrant"),
    ("wave", "colette", "workflow", "pipeline", "idempot", "retry", "compensation", "transaction", "runbook", "protocol", "route"),
    ("http", "https", "api", "network", "socket", "endpoint", "url", "request", "response", "external provider", "web"),
    (), (), (),
)



@dataclass(frozen=True)
class COS20Explanation:
    vector: tuple[float, ...]
    raw_scores: tuple[float, ...]
    active_dimensions: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "vector": list(self.vector),
            "raw_scores": list(self.raw_scores),
            "active_dimensions": list(self.active_dimensions),
            "dimensions": [f"{code}:{name}" for code, name in COS_DIMENSIONS],
        }


def _term_count(haystack: str, term: str) -> int:
    if not term:
        return 0
    if " " in term or term.endswith(" "):
        return haystack.count(term)
    return len(re.findall(rf"(?<![a-z0-9_]){re.escape(term)}(?![a-z0-9_])", haystack))


def _base_scores(path: str, language: str, kind: str) -> list[float]:
    scores = [0.0] * 20
    lower_path = path.lower()
    if language == "python" or kind.startswith("python-"):
        scores[4] += 0.22
        scores[5] += 0.06
        scores[6] += 0.06
    elif language == "markdown" or kind.startswith("markdown-"):
        scores[8] += 0.12
        scores[9] += 0.06
    else:
        scores[6] += 0.08
    if "/tests/" in f"/{lower_path}" or lower_path.startswith("tests/"):
        scores[5] += 0.12
        scores[7] += 0.08
    if "/docs/" in f"/{lower_path}" or lower_path.startswith("docs/"):
        scores[8] += 0.08
    if "workflow" in lower_path or ".github/" in lower_path:
        scores[15] += 0.15
    if "graph" in lower_path:
        scores[11] += 0.12
    if "agent" in lower_path:
        scores[13] += 0.12
    if "api" in lower_path or "provider" in lower_path:
        scores[16] += 0.10
    return scores


def cos20_features(text: str, *, path: str = "", language: str = "text", kind: str = "text-block") -> COS20Explanation:
    haystack = f"{path}\n{kind}\n{text}".lower()
    scores = _base_scores(path, language, kind)
    for idx, terms in enumerate(_DIMENSION_TERMS):
        if idx >= 17:
            continue
        hits = sum(_term_count(haystack, term) for term in terms)
        if hits:
            # Saturating score: repeated evidence matters without allowing giant docs to dominate.
            scores[idx] += min(1.0, math.log1p(hits) / math.log(8.0))
    scores = [min(1.0, value) if idx < 17 else 0.0 for idx, value in enumerate(scores)]
    norm = math.sqrt(sum(value * value for value in scores))
    if norm <= 1e-12:
        # Generic textual knowledge is the least-assumptive non-zero fallback. Reserved L17-L19 stay zero.
        scores[8] = 1.0
        norm = 1.0
    vector = tuple(value / norm for value in scores)
    active = tuple(
        f"{COS_DIMENSIONS[idx][0]}:{COS_DIMENSIONS[idx][1]}"
        for idx, value in enumerate(scores)
        if value > 0.0
    )
    return COS20Explanation(tuple(vector), tuple(scores), active)


def cos20_for_chunk(chunk: RepoChunk) -> COS20Explanation:
    return cos20_features(chunk.text, path=chunk.path, language=chunk.language, kind=chunk.kind)


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b):
        raise ValueError("vectors must have the same dimensionality")
    dot = sum(float(x) * float(y) for x, y in zip(a, b))
    na = math.sqrt(sum(float(x) * float(x) for x in a))
    nb = math.sqrt(sum(float(y) * float(y) for y in b))
    if na <= 1e-12 or nb <= 1e-12:
        return 0.0
    return dot / (na * nb)
