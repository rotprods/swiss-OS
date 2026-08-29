#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

from swiss_os.v2_coordination import death_drill, reduce_coordination, validate_claim, validate_context_pack, validate_event, validate_project_state

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "ARCHITECTURE.md","HANDOFF.md","TASKS.md","LEXICON.md",
    "docs/architecture/V2_ARCHITECTURE.md","docs/architecture/V2_GRAPH_MODEL.md",
    "docs/architecture/V2_GAP_RISK_MATRIX.md","docs/architecture/V2_DECISION_LEDGER.md",
    "docs/operations/V2_IMPLEMENTATION_PROGRAM.md","docs/operations/V2_TEST_SECURITY_RECOVERY.md",
    "docs/state/v2/project-state.json","docs/state/v2/goal-state.json","docs/state/v2/tasks.json",
    "docs/state/v2/checkpoint.json","docs/state/v2/active-claims.json","docs/state/v2/context-pack.json",
    "docs/state/v2/graph-snapshot.json","schemas/v2/event.schema.json","schemas/v2/claim.schema.json",
    "schemas/v2/context-pack.schema.json",
)

def load(rel: str) -> dict:
    value=json.loads((ROOT/rel).read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise ValueError(f"{rel}: expected JSON object")
    return value

def main() -> int:
    errors=[]
    for rel in REQUIRED:
        if not (ROOT/rel).exists(): errors.append(f"MISSING_REQUIRED_V2_FILE:{rel}")
    if errors:
        print("\n".join(errors)); return 1
    state=load("docs/state/v2/project-state.json")
    errors.extend(f"project-state:{x}" for x in validate_project_state(state))
    events=[]
    for path in sorted((ROOT/"docs/state/v2/events").glob("*.json")):
        value=json.loads(path.read_text(encoding="utf-8")); events.append(value)
        errors.extend(f"{path.name}:{x}" for x in validate_event(value))
    claims=[]
    for path in sorted((ROOT/"docs/state/v2/claims").glob("*.json")):
        value=json.loads(path.read_text(encoding="utf-8")); claims.append(value)
        errors.extend(f"{path.name}:{x}" for x in validate_claim(value))
    projection=reduce_coordination(events,claims)
    errors.extend(f"projection:{x}" for x in projection["violations"])
    if state.get("projection_revision")!=projection["projection_revision"]: errors.append("PROJECT_STATE_PROJECTION_REVISION_MISMATCH")
    context=load("docs/state/v2/context-pack.json")
    errors.extend(f"context:{x}" for x in validate_context_pack(context,current_main_sha=str(state.get("main_sha_observed","")),current_projection_revision=projection["projection_revision"]))
    if context.get("authority_revision")!=state.get("authority_revision"): errors.append("CONTEXT_AUTHORITY_REVISION_MISMATCH")
    if context.get("event_watermark")!=projection.get("event_watermark"): errors.append("CONTEXT_EVENT_WATERMARK_MISMATCH")
    active=load("docs/state/v2/active-claims.json")
    projected_ids=sorted(str(i.get("claim_id","")) for i in active.get("claims",[]) if isinstance(i,dict))
    durable_ids=sorted(str(i.get("claim_id","")) for i in claims)
    if projected_ids!=durable_ids: errors.append("ACTIVE_CLAIMS_ID_PROJECTION_MISMATCH")
    if active.get("collisions")!=projection.get("claim_collisions"): errors.append("ACTIVE_CLAIMS_COLLISION_PROJECTION_MISMATCH")
    graph=load("docs/state/v2/graph-snapshot.json")
    for key,expected in (("authority_advanced",False),("h_id_allocations",0),("outbound","CLOSED"),("send_allowed",0)):
        value=graph.get(key)
        if value!=expected or (expected==0 and isinstance(value,bool)): errors.append(f"GRAPH_SAFETY_LOCK_MISMATCH:{key}")
    if state.get("authority_advanced") is not False: errors.append("STATE_AUTHORITY_ADVANCED_FORBIDDEN")
    if state.get("h_id_allocation_allowed") is not False: errors.append("STATE_H_ID_ALLOCATION_FORBIDDEN")
    if state.get("outbound_allowed") is not False: errors.append("STATE_OUTBOUND_FORBIDDEN")
    errors.extend(f"death-drill:MISSING_{key}" for key in death_drill(state))
    tasks=load("docs/state/v2/tasks.json"); tids=[i.get("task_id") for i in tasks.get("tasks",[]) if isinstance(i,dict)]
    if len(tids)!=len(set(tids)): errors.append("DUPLICATE_TASK_ID")
    if not tids: errors.append("EMPTY_TASK_PROGRAM")
    cps=load("docs/state/v2/checkpoint.json"); cids=[i.get("id") for i in cps.get("checkpoints",[]) if isinstance(i,dict)]
    if len(cids)!=len(set(cids)): errors.append("DUPLICATE_CHECKPOINT_ID")
    if errors:
        print("v2_contract_guard: FAIL")
        for error in sorted(set(errors)): print(f"- {error}")
        return 1
    print(f"v2_contract_guard: PASS events={len(events)} claims={len(claims)} projection={projection['projection_revision']} context={context['context_pack_revision']}")
    return 0

if __name__=="__main__": sys.exit(main())
