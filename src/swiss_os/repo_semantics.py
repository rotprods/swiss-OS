from __future__ import annotations

import ast
from dataclasses import dataclass, asdict
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Iterable, Iterator, Sequence


DEFAULT_EXCLUDED_DIRS = frozenset({
    ".git", ".hg", ".svn", ".venv", "venv", "node_modules", "dist", "build",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".next", ".swiss-os",
    "operational", "snapshots", "backups", "candidate_private", "contacts_private",
    "raw_contacts", "raw_evidence", "private_exports", "cv", "portfolio_private", "media_private",
})

DEFAULT_BINARY_SUFFIXES = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".gz", ".tgz",
    ".tar", ".7z", ".rar", ".sqlite", ".sqlite3", ".db", ".woff", ".woff2", ".ttf",
    ".otf", ".mp3", ".mp4", ".mov", ".avi", ".mkv", ".bin", ".pyc", ".p12", ".pem",
})

_LANGUAGE_BY_SUFFIX = {
    ".py": "python", ".md": "markdown", ".mdx": "markdown", ".json": "json",
    ".jsonl": "jsonl", ".toml": "toml", ".yaml": "yaml", ".yml": "yaml",
    ".sh": "shell", ".bash": "shell", ".zsh": "shell", ".js": "javascript",
    ".jsx": "javascript", ".ts": "typescript", ".tsx": "typescript", ".rs": "rust",
    ".go": "go", ".sql": "sql", ".html": "html", ".css": "css", ".scss": "scss",
    ".txt": "text", ".csv": "csv", ".xml": "xml", ".ini": "ini", ".cfg": "config",
}

_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


@dataclass(frozen=True)
class RepoChunk:
    chunk_id: str
    path: str
    language: str
    kind: str
    symbol: str | None
    start_line: int
    end_line: int
    chunk_index: int
    text: str
    content_sha256: str
    file_sha256: str

    def embedding_text(self) -> str:
        metadata = [
            f"repository_path: {self.path}",
            f"language: {self.language}",
            f"chunk_kind: {self.kind}",
        ]
        if self.symbol:
            metadata.append(f"symbol: {self.symbol}")
        return "\n".join(metadata) + "\n\n" + self.text

    def payload(self, *, repo: str, git_sha: str, cos20: Sequence[float] | None = None) -> dict[str, object]:
        out: dict[str, object] = {
            "schema_version": "SWISS-REPO-CHUNK-1.0",
            "repo": repo,
            "git_sha": git_sha,
            **asdict(self),
        }
        if cos20 is not None:
            out["cos20"] = [float(v) for v in cos20]
        return out


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    node_type: str
    path: str
    label: str
    chunk_id: str | None = None


@dataclass(frozen=True)
class GraphEdge:
    source: str
    relation: str
    target: str
    authority: str = "DERIVED_REPOSITORY_STRUCTURE"
    confidence: float = 1.0


@dataclass(frozen=True)
class ChunkingStats:
    files_seen: int
    files_indexed: int
    files_skipped: int
    bytes_indexed: int
    chunks: int


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _stable_chunk_id(path: str, start_line: int, end_line: int, kind: str, symbol: str | None, content_sha: str) -> str:
    raw = f"{path}\0{start_line}\0{end_line}\0{kind}\0{symbol or ''}\0{content_sha}".encode("utf-8")
    return "CHUNK-" + hashlib.sha256(raw).hexdigest()[:24]


def language_for_path(path: Path) -> str:
    if path.name in {"Dockerfile", "Makefile"}:
        return path.name.lower()
    return _LANGUAGE_BY_SUFFIX.get(path.suffix.lower(), "text")


def _is_probably_text(data: bytes) -> bool:
    if b"\x00" in data[:8192]:
        return False
    try:
        data.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def _git_tracked_files(root: Path) -> list[Path] | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            check=True,
            capture_output=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    names = [name for name in proc.stdout.decode("utf-8", errors="strict").split("\x00") if name]
    return [root / name for name in names]


def iter_repository_files(
    root: str | Path,
    *,
    max_file_bytes: int = 4_000_000,
    excluded_dirs: frozenset[str] = DEFAULT_EXCLUDED_DIRS,
) -> Iterator[Path]:
    base = Path(root).resolve()
    candidates = _git_tracked_files(base)
    if candidates is None:
        candidates = [p for p in base.rglob("*") if p.is_file()]
    for path in sorted(candidates, key=lambda p: p.as_posix()):
        try:
            rel = path.resolve().relative_to(base)
        except (OSError, ValueError):
            continue
        if any(part in excluded_dirs for part in rel.parts[:-1]):
            continue
        if path.suffix.lower() in DEFAULT_BINARY_SUFFIXES:
            continue
        try:
            if path.stat().st_size > max_file_bytes:
                continue
        except OSError:
            continue
        yield path


def _split_line_range(lines: Sequence[str], start: int, end: int, *, max_chars: int, overlap_lines: int) -> list[tuple[int, int]]:
    if start > end:
        return []
    ranges: list[tuple[int, int]] = []
    cursor = start
    while cursor <= end:
        chars = 0
        stop = cursor - 1
        while stop < end:
            candidate = lines[stop] if stop < len(lines) else ""
            if stop >= cursor and chars + len(candidate) > max_chars:
                break
            chars += len(candidate)
            stop += 1
        if stop < cursor:
            stop = cursor
        ranges.append((cursor, min(stop, end)))
        if stop >= end:
            break
        cursor = max(cursor + 1, stop - overlap_lines + 1)
    return ranges


def _python_ranges(text: str, *, max_chars: int, overlap_lines: int) -> list[tuple[int, int, str, str | None]]:
    lines = text.splitlines(keepends=True)
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return [(s, e, "python-block", None) for s, e in _split_line_range(lines, 1, len(lines), max_chars=max_chars, overlap_lines=overlap_lines)]

    out: list[tuple[int, int, str, str | None]] = []
    top_nodes = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and getattr(n, "end_lineno", None)]
    first_symbol_line = min((n.lineno for n in top_nodes), default=len(lines) + 1)
    if first_symbol_line > 1:
        for s, e in _split_line_range(lines, 1, first_symbol_line - 1, max_chars=max_chars, overlap_lines=overlap_lines):
            if any(line.strip() for line in lines[s - 1:e]):
                out.append((s, e, "python-module", None))

    for node in top_nodes:
        kind = "python-class" if isinstance(node, ast.ClassDef) else "python-function"
        symbol = node.name
        start_line = min([getattr(d, "lineno", node.lineno) for d in getattr(node, "decorator_list", [])] + [node.lineno])
        end_line = int(node.end_lineno)
        for s, e in _split_line_range(lines, start_line, end_line, max_chars=max_chars, overlap_lines=overlap_lines):
            out.append((s, e, kind, symbol))

    covered = [False] * (len(lines) + 1)
    for s, e, _, _ in out:
        for i in range(max(1, s), min(len(lines), e) + 1):
            covered[i] = True
    residual_start: int | None = None
    for i in range(1, len(lines) + 2):
        active = i <= len(lines) and not covered[i] and bool(lines[i - 1].strip())
        if active and residual_start is None:
            residual_start = i
        if residual_start is not None and (not active or i == len(lines) + 1):
            residual_end = i - 1
            for s, e in _split_line_range(lines, residual_start, residual_end, max_chars=max_chars, overlap_lines=overlap_lines):
                out.append((s, e, "python-block", None))
            residual_start = None
    return sorted(set(out), key=lambda item: (item[0], item[1], item[2], item[3] or ""))


def _markdown_ranges(text: str, *, max_chars: int, overlap_lines: int) -> list[tuple[int, int, str, str | None]]:
    lines = text.splitlines(keepends=True)
    headings: list[tuple[int, int, str]] = []
    for i, line in enumerate(lines, 1):
        match = _HEADING.match(line.rstrip("\n"))
        if match:
            headings.append((i, len(match.group(1)), match.group(2).strip()))
    if not headings:
        return [(s, e, "markdown-block", None) for s, e in _split_line_range(lines, 1, len(lines), max_chars=max_chars, overlap_lines=overlap_lines)]

    out: list[tuple[int, int, str, str | None]] = []
    if headings[0][0] > 1:
        for s, e in _split_line_range(lines, 1, headings[0][0] - 1, max_chars=max_chars, overlap_lines=overlap_lines):
            out.append((s, e, "markdown-preamble", None))
    for idx, (line_no, level, title) in enumerate(headings):
        end = (headings[idx + 1][0] - 1) if idx + 1 < len(headings) else len(lines)
        for s, e in _split_line_range(lines, line_no, end, max_chars=max_chars, overlap_lines=overlap_lines):
            out.append((s, e, f"markdown-h{level}", title))
    return out


def _generic_ranges(text: str, *, max_chars: int, overlap_lines: int) -> list[tuple[int, int, str, str | None]]:
    lines = text.splitlines(keepends=True)
    if not lines:
        return []
    return [(s, e, "text-block", None) for s, e in _split_line_range(lines, 1, len(lines), max_chars=max_chars, overlap_lines=overlap_lines)]


def chunk_text(path: str, text: str, *, max_chars: int = 6000, overlap_lines: int = 8) -> list[RepoChunk]:
    if max_chars < 256:
        raise ValueError("max_chars must be >= 256")
    if overlap_lines < 0:
        raise ValueError("overlap_lines must be >= 0")
    p = Path(path)
    language = language_for_path(p)
    raw = text.encode("utf-8")
    file_sha = _sha256(raw)
    lines = text.splitlines(keepends=True)
    if language == "python":
        ranges = _python_ranges(text, max_chars=max_chars, overlap_lines=overlap_lines)
    elif language == "markdown":
        ranges = _markdown_ranges(text, max_chars=max_chars, overlap_lines=overlap_lines)
    else:
        ranges = _generic_ranges(text, max_chars=max_chars, overlap_lines=overlap_lines)

    chunks: list[RepoChunk] = []
    for idx, (start, end, kind, symbol) in enumerate(ranges):
        body = "".join(lines[start - 1:end]).strip()
        if not body:
            continue
        content_sha = _sha256(body.encode("utf-8"))
        chunks.append(RepoChunk(
            chunk_id=_stable_chunk_id(path, start, end, kind, symbol, content_sha),
            path=path,
            language=language,
            kind=kind,
            symbol=symbol,
            start_line=start,
            end_line=end,
            chunk_index=idx,
            text=body,
            content_sha256=content_sha,
            file_sha256=file_sha,
        ))
    return chunks


def chunk_repository(
    root: str | Path,
    *,
    max_chars: int = 6000,
    overlap_lines: int = 8,
    max_file_bytes: int = 4_000_000,
) -> tuple[list[RepoChunk], ChunkingStats]:
    base = Path(root).resolve()
    chunks: list[RepoChunk] = []
    files_seen = files_indexed = files_skipped = bytes_indexed = 0
    for path in iter_repository_files(base, max_file_bytes=max_file_bytes):
        files_seen += 1
        try:
            data = path.read_bytes()
        except OSError:
            files_skipped += 1
            continue
        if not _is_probably_text(data):
            files_skipped += 1
            continue
        text = data.decode("utf-8")
        rel = path.resolve().relative_to(base).as_posix()
        produced = chunk_text(rel, text, max_chars=max_chars, overlap_lines=overlap_lines)
        if not produced:
            files_skipped += 1
            continue
        files_indexed += 1
        bytes_indexed += len(data)
        chunks.extend(produced)
    return chunks, ChunkingStats(files_seen, files_indexed, files_skipped, bytes_indexed, len(chunks))


def graphify_chunks(chunks: Sequence[RepoChunk]) -> tuple[list[GraphNode], list[GraphEdge]]:
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    by_path: dict[str, list[RepoChunk]] = {}
    for chunk in chunks:
        by_path.setdefault(chunk.path, []).append(chunk)
    for path, file_chunks in sorted(by_path.items()):
        file_node_id = "FILE-" + hashlib.sha256(path.encode("utf-8")).hexdigest()[:24]
        nodes.append(GraphNode(file_node_id, "File", path, path))
        ordered = sorted(file_chunks, key=lambda c: (c.start_line, c.end_line, c.chunk_id))
        previous: RepoChunk | None = None
        for chunk in ordered:
            nodes.append(GraphNode(chunk.chunk_id, "Chunk", path, chunk.symbol or f"{path}:{chunk.start_line}-{chunk.end_line}", chunk.chunk_id))
            edges.append(GraphEdge(file_node_id, "CONTAINS", chunk.chunk_id))
            if chunk.symbol:
                symbol_id = "SYMBOL-" + hashlib.sha256(f"{path}\0{chunk.symbol}".encode("utf-8")).hexdigest()[:24]
                nodes.append(GraphNode(symbol_id, "Symbol", path, chunk.symbol, chunk.chunk_id))
                edges.append(GraphEdge(file_node_id, "DEFINES", symbol_id))
                edges.append(GraphEdge(symbol_id, "IMPLEMENTED_BY", chunk.chunk_id))
            if previous is not None:
                edges.append(GraphEdge(previous.chunk_id, "PRECEDES", chunk.chunk_id))
            previous = chunk
    unique_nodes = {node.node_id: node for node in nodes}
    unique_edges = {(e.source, e.relation, e.target): e for e in edges}
    return list(unique_nodes.values()), list(unique_edges.values())


def write_graph_jsonl(path: str | Path, nodes: Sequence[GraphNode], edges: Sequence[GraphEdge]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for node in nodes:
            fh.write(json.dumps({"record_type": "node", **asdict(node)}, ensure_ascii=False, sort_keys=True) + "\n")
        for edge in edges:
            fh.write(json.dumps({"record_type": "edge", **asdict(edge)}, ensure_ascii=False, sort_keys=True) + "\n")
    tmp.replace(target)
