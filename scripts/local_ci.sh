#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="${PYTHONPATH:-src}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
RECEIPT_DIR="${RECEIPT_DIR:-.artifacts/local-ci}"
mkdir -p "$RECEIPT_DIR"

run() {
  printf '\n==> %s\n' "$1"
  shift
  "$@"
}

run "Python version" "$PYTHON_BIN" --version
run "Public repository guard" "$PYTHON_BIN" scripts/repo_guard.py
run "Stable contract drift guard" "$PYTHON_BIN" scripts/system_contract_guard.py
run "Agent improvement / GRAPH-REFACTOR-V2 guard" "$PYTHON_BIN" scripts/agent_improvement_guard.py
run "Session Runtime Protocol guard" "$PYTHON_BIN" scripts/session_runtime_guard.py
run "V2 coordination contract guard" "$PYTHON_BIN" scripts/v2_contract_guard.py
run "Context survival / compaction checkpoint guard" "$PYTHON_BIN" scripts/context_survival_guard.py
run "V2 empirical recovery and death drill" "$PYTHON_BIN" scripts/v2_empirical_drill.py --receipt "$RECEIPT_DIR/v2-empirical-receipt.json"
run "CWP candidate lineage guard" "$PYTHON_BIN" -m swiss_os.cwp_lineage_guard
run "Durable handoff frontier guard" "$PYTHON_BIN" scripts/handoff_frontier_guard.py
run "Unit tests" "$PYTHON_BIN" -m unittest discover -s tests -v
run "Manifest semantics canary" "$PYTHON_BIN" -m swiss_os.cli manifest validate tests/fixtures/manifest_superseded.json
run "Python compileall" "$PYTHON_BIN" -m compileall -q src scripts tests

printf '\nLOCAL_CI_PASS\n'
