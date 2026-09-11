from __future__ import annotations

from dataclasses import dataclass
import json
import time
from typing import Any, Mapping, Protocol, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
import uuid

from .cos_graph import cos20_features, cos20_for_chunk
from .repo_semantics import RepoChunk


SEMANTIC_VECTOR_NAME = "semantic"
COS20_VECTOR_NAME = "cos20"
POINT_NAMESPACE = uuid.UUID("6f7f97f3-27a8-4af1-8fc3-d26644407241")


class SemanticIndexError(RuntimeError):
    pass


class JsonTransport(Protocol):
    def request(self, method: str, url: str, payload: Mapping[str, Any] | None = None, *, timeout: float = 60.0) -> Any: ...


class UrllibJsonTransport:
    def __init__(self, *, retries: int = 2, retry_base_seconds: float = 0.2):
        self.retries = max(0, retries)
        self.retry_base_seconds = max(0.0, retry_base_seconds)

    def request(self, method: str, url: str, payload: Mapping[str, Any] | None = None, *, timeout: float = 60.0) -> Any:
        body = None if payload is None else json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers = {"Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        req = Request(url, data=body, headers=headers, method=method.upper())
        last_error: BaseException | None = None
        for attempt in range(self.retries + 1):
            try:
                with urlopen(req, timeout=timeout) as response:
                    raw = response.read()
                    if not raw:
                        return {}
                    content_type = response.headers.get("Content-Type", "")
                    if "json" not in content_type.lower() and raw[:1] not in {b"{", b"["}:
                        return raw.decode("utf-8", errors="replace")
                    return json.loads(raw)
            except HTTPError as exc:
                last_error = exc
                if exc.code < 500 and exc.code != 429:
                    detail = exc.read().decode("utf-8", errors="replace")
                    raise SemanticIndexError(f"HTTP {exc.code} from {url}: {detail[:500]}") from exc
            except (URLError, TimeoutError, OSError) as exc:
                last_error = exc
            if attempt < self.retries:
                time.sleep(self.retry_base_seconds * (2 ** attempt))
        raise SemanticIndexError(f"request failed after retries: {method} {url}: {last_error}") from last_error


@dataclass(frozen=True)
class EmbedBatchResult:
    embeddings: tuple[tuple[float, ...], ...]
    wall_seconds: float
    server_total_duration_ns: int | None
    server_load_duration_ns: int | None
    prompt_eval_count: int | None

    @property
    def dimension(self) -> int:
        return len(self.embeddings[0]) if self.embeddings else 0


class OllamaEmbeddingClient:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434",
        model: str = "qwen3-embedding:0.6b",
        *,
        timeout: float = 120.0,
        transport: JsonTransport | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.transport = transport or UrllibJsonTransport()

    def health(self) -> dict[str, Any]:
        response = self.transport.request("GET", f"{self.base_url}/api/tags", timeout=self.timeout)
        if not isinstance(response, dict):
            raise SemanticIndexError("Ollama /api/tags returned non-object JSON")
        return response

    def embed(self, inputs: Sequence[str]) -> EmbedBatchResult:
        if not inputs:
            return EmbedBatchResult((), 0.0, None, None, 0)
        started = time.perf_counter()
        response = self.transport.request(
            "POST",
            f"{self.base_url}/api/embed",
            {"model": self.model, "input": list(inputs), "truncate": False},
            timeout=self.timeout,
        )
        wall = time.perf_counter() - started
        if not isinstance(response, dict):
            raise SemanticIndexError("Ollama /api/embed returned non-object JSON")
        raw_embeddings = response.get("embeddings")
        if not isinstance(raw_embeddings, list) or len(raw_embeddings) != len(inputs):
            raise SemanticIndexError("Ollama embedding count does not match input count")
        embeddings: list[tuple[float, ...]] = []
        dim: int | None = None
        for raw_vector in raw_embeddings:
            if not isinstance(raw_vector, list) or not raw_vector:
                raise SemanticIndexError("Ollama returned an empty or invalid embedding")
            vector = tuple(float(value) for value in raw_vector)
            if dim is None:
                dim = len(vector)
            elif len(vector) != dim:
                raise SemanticIndexError("Ollama returned inconsistent embedding dimensions")
            embeddings.append(vector)
        return EmbedBatchResult(
            tuple(embeddings),
            wall,
            _optional_int(response.get("total_duration")),
            _optional_int(response.get("load_duration")),
            _optional_int(response.get("prompt_eval_count")),
        )

    def embed_one(self, text: str) -> tuple[float, ...]:
        result = self.embed([text])
        return result.embeddings[0]


def _optional_int(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def qdrant_point_id(chunk_id: str) -> str:
    return str(uuid.uuid5(POINT_NAMESPACE, chunk_id))


@dataclass(frozen=True)
class SearchHit:
    point_id: str
    score: float
    payload: Mapping[str, Any]
    semantic_score: float | None = None
    cos20_score: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "point_id": self.point_id,
            "score": self.score,
            "semantic_score": self.semantic_score,
            "cos20_score": self.cos20_score,
            "payload": dict(self.payload),
        }


class QdrantRepoIndex:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:6333",
        collection: str = "swiss_os_repo_semantic",
        *,
        timeout: float = 60.0,
        transport: JsonTransport | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.collection = collection
        self.timeout = timeout
        self.transport = transport or UrllibJsonTransport()

    @property
    def collection_url(self) -> str:
        return f"{self.base_url}/collections/{quote(self.collection, safe='')}"

    def health(self) -> dict[str, Any]:
        response = self.transport.request("GET", f"{self.base_url}/collections", timeout=self.timeout)
        if not isinstance(response, dict):
            raise SemanticIndexError("Qdrant /collections returned non-object JSON")
        return response

    def get_collection(self) -> dict[str, Any] | None:
        try:
            response = self.transport.request("GET", self.collection_url, timeout=self.timeout)
        except SemanticIndexError as exc:
            message = str(exc)
            if "HTTP 404" in message:
                return None
            raise
        if not isinstance(response, dict):
            raise SemanticIndexError("Qdrant collection response is invalid")
        return response

    def delete_collection(self) -> None:
        self.transport.request("DELETE", self.collection_url, timeout=self.timeout)

    def ensure_collection(self, semantic_dim: int, *, recreate: bool = False) -> str:
        if semantic_dim <= 0:
            raise ValueError("semantic_dim must be positive")
        current = self.get_collection()
        if current is not None and recreate:
            self.delete_collection()
            current = None
        if current is None:
            payload = {
                "vectors": {
                    SEMANTIC_VECTOR_NAME: {"size": semantic_dim, "distance": "Cosine"},
                    COS20_VECTOR_NAME: {"size": 20, "distance": "Cosine"},
                },
                "on_disk_payload": True,
            }
            self.transport.request("PUT", self.collection_url, payload, timeout=self.timeout)
            return "CREATED"
        dims = _collection_vector_dims(current)
        expected = {SEMANTIC_VECTOR_NAME: semantic_dim, COS20_VECTOR_NAME: 20}
        if dims != expected:
            raise SemanticIndexError(
                f"collection vector schema mismatch: expected {expected}, observed {dims}; "
                "use --recreate-collection only when deleting this derived index is safe"
            )
        return "REUSED"

    def delete_repo_points(self, repo: str) -> None:
        payload = {"filter": {"must": [{"key": "repo", "match": {"value": repo}}]}}
        self.transport.request("POST", f"{self.collection_url}/points/delete?wait=true", payload, timeout=self.timeout)

    def upsert(self, points: Sequence[Mapping[str, Any]]) -> None:
        if not points:
            return
        self.transport.request(
            "PUT",
            f"{self.collection_url}/points?wait=true",
            {"points": list(points)},
            timeout=self.timeout,
        )

    def count(self, *, repo: str | None = None) -> int:
        payload: dict[str, Any] = {"exact": True}
        if repo:
            payload["filter"] = {"must": [{"key": "repo", "match": {"value": repo}}]}
        response = self.transport.request("POST", f"{self.collection_url}/points/count", payload, timeout=self.timeout)
        try:
            return int(response["result"]["count"])
        except (KeyError, TypeError, ValueError) as exc:
            raise SemanticIndexError("invalid Qdrant count response") from exc

    def query(self, vector: Sequence[float], *, using: str, limit: int = 10, repo: str | None = None) -> list[SearchHit]:
        if using not in {SEMANTIC_VECTOR_NAME, COS20_VECTOR_NAME}:
            raise ValueError(f"unknown vector space: {using}")
        if limit < 1:
            raise ValueError("limit must be >= 1")
        payload: dict[str, Any] = {
            "query": [float(v) for v in vector],
            "using": using,
            "limit": limit,
            "with_payload": True,
            "with_vector": False,
        }
        if repo:
            payload["filter"] = {"must": [{"key": "repo", "match": {"value": repo}}]}
        response = self.transport.request("POST", f"{self.collection_url}/points/query", payload, timeout=self.timeout)
        try:
            raw_points = response["result"]["points"]
        except (KeyError, TypeError) as exc:
            raise SemanticIndexError("invalid Qdrant query response") from exc
        if not isinstance(raw_points, list):
            raise SemanticIndexError("invalid Qdrant query points")
        hits: list[SearchHit] = []
        for point in raw_points:
            if not isinstance(point, dict):
                continue
            point_id = str(point.get("id", ""))
            score = float(point.get("score", 0.0))
            point_payload = point.get("payload") if isinstance(point.get("payload"), dict) else {}
            hits.append(SearchHit(
                point_id,
                score,
                point_payload,
                semantic_score=score if using == SEMANTIC_VECTOR_NAME else None,
                cos20_score=score if using == COS20_VECTOR_NAME else None,
            ))
        return hits

    def scroll(self, *, limit: int = 100, repo: str | None = None, with_vectors: bool = False) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {"limit": limit, "with_payload": True, "with_vector": with_vectors}
        if repo:
            payload["filter"] = {"must": [{"key": "repo", "match": {"value": repo}}]}
        response = self.transport.request("POST", f"{self.collection_url}/points/scroll", payload, timeout=self.timeout)
        try:
            points = response["result"]["points"]
        except (KeyError, TypeError) as exc:
            raise SemanticIndexError("invalid Qdrant scroll response") from exc
        return [point for point in points if isinstance(point, dict)]


def _collection_vector_dims(response: Mapping[str, Any]) -> dict[str, int]:
    try:
        vectors = response["result"]["config"]["params"]["vectors"]
    except (KeyError, TypeError) as exc:
        raise SemanticIndexError("Qdrant collection schema missing vector config") from exc
    if not isinstance(vectors, dict):
        raise SemanticIndexError("Qdrant collection is not configured with named vectors")
    out: dict[str, int] = {}
    for name, config in vectors.items():
        if not isinstance(config, dict) or "size" not in config:
            continue
        out[str(name)] = int(config["size"])
    return out


@dataclass(frozen=True)
class IndexRunStats:
    chunks: int
    batches: int
    semantic_dimension: int
    embedding_seconds: float
    upsert_seconds: float
    wall_seconds: float
    prompt_eval_count: int

    @property
    def chunks_per_second(self) -> float:
        return self.chunks / self.wall_seconds if self.wall_seconds > 0 else 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "chunks": self.chunks,
            "batches": self.batches,
            "semantic_dimension": self.semantic_dimension,
            "embedding_seconds": self.embedding_seconds,
            "upsert_seconds": self.upsert_seconds,
            "wall_seconds": self.wall_seconds,
            "chunks_per_second": self.chunks_per_second,
            "prompt_eval_count": self.prompt_eval_count,
        }


class SemanticGraphEngine:
    def __init__(self, embedder: OllamaEmbeddingClient, qdrant: QdrantRepoIndex):
        self.embedder = embedder
        self.qdrant = qdrant

    def index(
        self,
        chunks: Sequence[RepoChunk],
        *,
        repo: str,
        git_sha: str,
        batch_size: int = 24,
        recreate_collection: bool = False,
        replace_repo: bool = True,
    ) -> IndexRunStats:
        if not chunks:
            raise ValueError("refusing to build an empty semantic index")
        if batch_size < 1:
            raise ValueError("batch_size must be >= 1")
        started = time.perf_counter()

        # Probe once to auto-discover model dimensionality instead of hard-coding it.
        probe = self.embedder.embed([chunks[0].embedding_text()])
        semantic_dim = probe.dimension
        self.qdrant.ensure_collection(semantic_dim, recreate=recreate_collection)
        if replace_repo:
            self.qdrant.delete_repo_points(repo)

        embedding_seconds = probe.wall_seconds
        upsert_seconds = 0.0
        prompt_eval_count = probe.prompt_eval_count or 0
        batches = 0

        def flush(batch_chunks: Sequence[RepoChunk], embeddings: Sequence[Sequence[float]]) -> None:
            nonlocal upsert_seconds, batches
            if len(batch_chunks) != len(embeddings):
                raise SemanticIndexError("chunk/embedding batch cardinality mismatch")
            points = [
                build_qdrant_point(chunk, embedding, repo=repo, git_sha=git_sha, model=self.embedder.model)
                for chunk, embedding in zip(batch_chunks, embeddings)
            ]
            t0 = time.perf_counter()
            self.qdrant.upsert(points)
            upsert_seconds += time.perf_counter() - t0
            batches += 1

        first_batch_chunks = list(chunks[:batch_size])
        first_embeddings: list[Sequence[float]] = [probe.embeddings[0]]
        if len(first_batch_chunks) > 1:
            result = self.embedder.embed([chunk.embedding_text() for chunk in first_batch_chunks[1:]])
            if result.dimension != semantic_dim:
                raise SemanticIndexError("embedding dimension changed during index run")
            embedding_seconds += result.wall_seconds
            prompt_eval_count += result.prompt_eval_count or 0
            first_embeddings.extend(result.embeddings)
        flush(first_batch_chunks, first_embeddings)

        for offset in range(batch_size, len(chunks), batch_size):
            batch_chunks = list(chunks[offset:offset + batch_size])
            result = self.embedder.embed([chunk.embedding_text() for chunk in batch_chunks])
            if result.dimension != semantic_dim:
                raise SemanticIndexError("embedding dimension changed during index run")
            embedding_seconds += result.wall_seconds
            prompt_eval_count += result.prompt_eval_count or 0
            flush(batch_chunks, result.embeddings)

        observed = self.qdrant.count(repo=repo)
        if observed != len(chunks):
            raise SemanticIndexError(f"post-index count mismatch for {repo}: expected {len(chunks)}, observed {observed}")
        wall = time.perf_counter() - started
        return IndexRunStats(len(chunks), batches, semantic_dim, embedding_seconds, upsert_seconds, wall, prompt_eval_count)

    def search(self, query: str, *, repo: str | None = None, limit: int = 10, space: str = "hybrid") -> list[SearchHit]:
        if space == COS20_VECTOR_NAME:
            features = cos20_features(query)
            return self.qdrant.query(features.vector, using=COS20_VECTOR_NAME, limit=limit, repo=repo)
        if space == SEMANTIC_VECTOR_NAME:
            vector = self.embedder.embed_one(query)
            return self.qdrant.query(vector, using=SEMANTIC_VECTOR_NAME, limit=limit, repo=repo)
        if space != "hybrid":
            raise ValueError("space must be semantic, cos20 or hybrid")
        fetch_limit = max(limit * 3, 20)
        semantic_vector = self.embedder.embed_one(query)
        cos_vector = cos20_features(query).vector
        semantic_hits = self.qdrant.query(semantic_vector, using=SEMANTIC_VECTOR_NAME, limit=fetch_limit, repo=repo)
        cos_hits = self.qdrant.query(cos_vector, using=COS20_VECTOR_NAME, limit=fetch_limit, repo=repo)
        return reciprocal_rank_fusion(semantic_hits, cos_hits, limit=limit)


def build_qdrant_point(
    chunk: RepoChunk,
    semantic_vector: Sequence[float],
    *,
    repo: str,
    git_sha: str,
    model: str,
) -> dict[str, Any]:
    cos = cos20_for_chunk(chunk)
    payload = chunk.payload(repo=repo, git_sha=git_sha, cos20=cos.vector)
    payload.update({
        "embedding_model": model,
        "semantic_dimension": len(semantic_vector),
        "cos20_active_dimensions": list(cos.active_dimensions),
        "index_authority": "DERIVED_NON_AUTHORITATIVE_RETRIEVAL_INDEX",
    })
    return {
        "id": qdrant_point_id(chunk.chunk_id),
        "vector": {
            SEMANTIC_VECTOR_NAME: [float(value) for value in semantic_vector],
            COS20_VECTOR_NAME: list(cos.vector),
        },
        "payload": payload,
    }


def reciprocal_rank_fusion(
    semantic_hits: Sequence[SearchHit],
    cos_hits: Sequence[SearchHit],
    *,
    limit: int,
    semantic_weight: float = 0.82,
    cos20_weight: float = 0.18,
    rank_constant: float = 60.0,
) -> list[SearchHit]:
    if limit < 1:
        return []
    merged: dict[str, dict[str, Any]] = {}
    for rank, hit in enumerate(semantic_hits, 1):
        slot = merged.setdefault(hit.point_id, {"payload": hit.payload, "score": 0.0, "semantic": None, "cos20": None})
        slot["score"] += semantic_weight / (rank_constant + rank)
        slot["semantic"] = hit.score
    for rank, hit in enumerate(cos_hits, 1):
        slot = merged.setdefault(hit.point_id, {"payload": hit.payload, "score": 0.0, "semantic": None, "cos20": None})
        slot["score"] += cos20_weight / (rank_constant + rank)
        slot["cos20"] = hit.score
    ordered = sorted(merged.items(), key=lambda item: (-float(item[1]["score"]), item[0]))[:limit]
    return [
        SearchHit(
            point_id=point_id,
            score=float(data["score"]),
            payload=data["payload"],
            semantic_score=data["semantic"],
            cos20_score=data["cos20"],
        )
        for point_id, data in ordered
    ]
