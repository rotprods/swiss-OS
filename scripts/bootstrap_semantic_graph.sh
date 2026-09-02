#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MODEL="${SWISS_OS_EMBED_MODEL:-qwen3-embedding:0.6b}"
OLLAMA_URL="${SWISS_OS_OLLAMA_URL:-http://127.0.0.1:11434}"
QDRANT_URL="${SWISS_OS_QDRANT_URL:-http://127.0.0.1:6333}"
COLLECTION="${SWISS_OS_QDRANT_COLLECTION:-swiss_os_repo_semantic}"

mkdir -p .swiss-os/logs .swiss-os/graphify .swiss-os/benchmarks

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required for the local Qdrant service" >&2
  exit 2
fi
if ! command -v ollama >/dev/null 2>&1; then
  echo "ollama is required; install the native Ollama app/CLI first" >&2
  exit 2
fi
if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required for local health checks" >&2
  exit 2
fi

echo "[semantic-graph] starting Qdrant..."
docker compose -f docker-compose.semantic.yml up -d qdrant

if ! curl -fsS "$OLLAMA_URL/api/tags" >/dev/null 2>&1; then
  echo "[semantic-graph] starting Ollama server..."
  nohup ollama serve >.swiss-os/logs/ollama.log 2>&1 &
  for _ in $(seq 1 30); do
    if curl -fsS "$OLLAMA_URL/api/tags" >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
fi
curl -fsS "$OLLAMA_URL/api/tags" >/dev/null
curl -fsS "$QDRANT_URL/collections" >/dev/null

echo "[semantic-graph] pulling embedding model: $MODEL"
ollama pull "$MODEL"

echo "[semantic-graph] graphifying + indexing full repository"
PYTHONPATH=src python -m swiss_os.semantic_graph_cli graphify index \
  --repo . \
  --model "$MODEL" \
  --ollama-url "$OLLAMA_URL" \
  --qdrant-url "$QDRANT_URL" \
  --collection "$COLLECTION"

echo "[semantic-graph] running isolated benchmark"
PYTHONPATH=src python -m swiss_os.semantic_graph_cli graphify benchmark \
  --repo . \
  --model "$MODEL" \
  --ollama-url "$OLLAMA_URL" \
  --qdrant-url "$QDRANT_URL" \
  --collection "$COLLECTION" \
  --enforce-quality

echo "[semantic-graph] final status"
PYTHONPATH=src python -m swiss_os.semantic_graph_cli cos-graph-engine status \
  --model "$MODEL" \
  --ollama-url "$OLLAMA_URL" \
  --qdrant-url "$QDRANT_URL" \
  --collection "$COLLECTION"
