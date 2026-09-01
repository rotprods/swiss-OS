#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, re, subprocess
from pathlib import Path
import sys
from swiss_os.v2_coordination import ACTIVE_CLAIM_STATES, death_drill, project_claim_lifecycle, reduce_coordination, validate_claim, validate_context_pack, validate_event, validate_project_state

ROOT=Path(__file__).resolve().parents[1]
REQUIRED=("ARCHITECTURE.md","HANDOFF.md","TASKS.md","LEXICON.md","docs/architecture/V2_ARCHITECTURE.md","docs/architecture/V2_GRAPH_MODEL.md","docs/architecture/V2_GAP_RISK_MATRIX.md","docs/architecture/V2_DECISION_LEDGER.md","docs/operations/V2_IMPLEMENTATION_PROGRAM.md","docs/operations/V2_TEST_SECURITY_RECOVERY.md","docs/state/v2/project-state.json","docs/state/v2/goal-state.json","docs/state/v2/tasks.json","docs/state/v2/checkpoint.json","docs/state/v2/active-claims.json","docs/state/v2/context-pack.json","docs/state/v2/graph-snapshot.json","schemas/v2/event.schema.json","schemas/v2/claim.schema.json","schemas/v2/context-pack.schema.json")
TASK_REF_RE=re.compile(r"\bV2-T\d{3}\b")
def load(rel):
    value=json.loads((ROOT/rel).read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise ValueError(f"{rel}: expected JSON object")
    return value
def scope_revision(paths):
    entries=[]
    for rel in paths:
        path=ROOT/rel
        if not path.is_file(): raise ValueError(f"relevant path missing: {rel}")
        oid=subprocess.check_output(["git","hash-object",rel],cwd=ROOT,text=True).strip()
        entries.append(f"{rel}:{oid}")
    return hashlib.sha256("\n".join(entries).encode()).hexdigest()
def is_ancestor(base):
    if not isinstance(base,str) or len(base)!=40: return False
    return subprocess.run(["git","merge-base","--is-ancestor",base,"HEAD"],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False).returncode==0
def task_program_errors(tasks):
    errors=[]; rows=[i for i in tasks.get("tasks",[]) if isinstance(i,dict)]; tids=[str(i.get("task_id","")) for i in rows]
    if len(tids)!=len(set(tids)): errors.append("DUPLICATE_TASK_ID")
    if not tids: errors.append("EMPTY_TASK_PROGRAM"); return errors
    known=set(tids); deps={}
    for row in rows:
        tid=str(row.get("task_id","")); raw=row.get("dependencies",[])
        if not isinstance(raw,list): errors.append(f"INVALID_TASK_DEPENDENCIES:{tid}"); raw=[]
        declared={str(x) for x in raw if isinstance(x,str)}; deps[tid]=declared
        for dep in declared:
            if dep not in known: errors.append(f"UNKNOWN_TASK_DEPENDENCY:{tid}:{dep}")
        referenced=set()
        for value in row.get("inputs",[]) if isinstance(row.get("inputs"),list) else []:
            if isinstance(value,str): referenced.update(TASK_REF_RE.findall(value))
        missing=sorted((referenced & known)-declared)
        for dep in missing: errors.append(f"UNDECLARED_TASK_DEPENDENCY:{tid}:{dep}")
    visiting=set(); visited=set()
    def visit(tid):
        if tid in visited: return
        if tid in visiting: errors.append(f"TASK_DEPENDENCY_CYCLE:{tid}"); return
        visiting.add(tid)
        for dep in deps.get(tid,set()):
            if dep in known: visit(dep)
        visiting.remove(tid); visited.add(tid)
    for tid in tids: visit(tid)
    return errors
def main():
    errors=[]
    for rel in REQUIRED:
        if not (ROOT/rel).exists(): errors.append(f"MISSING_REQUIRED_V2_FILE:{rel}")
    if errors: print("\n".join(errors)); return 1
    state=load("docs/state/v2/project-state.json"); errors.extend(f"project-state:{x}" for x in validate_project_state(state))
    events=[]
    for path in sorted((ROOT/"docs/state/v2/events").glob("*.json")):
        value=json.loads(path.read_text(encoding="utf-8")); events.append(value); errors.extend(f"{path.name}:{x}" for x in validate_event(value))
    claims=[]
    for path in sorted((ROOT/"docs/state/v2/claims").glob("*.json")):
        value=json.loads(path.read_text(encoding="utf-8")); claims.append(value); errors.extend(f"{path.name}:{x}" for x in validate_claim(value))
    effective_claims,lifecycle_errors=project_claim_lifecycle(events,claims); errors.extend(f"claim-lifecycle:{x}" for x in lifecycle_errors)
    projection=reduce_coordination(events,claims); errors.extend(f"projection:{x}" for x in projection["violations"])
    if state.get("projection_revision")!=projection["projection_revision"]: errors.append(f"PROJECT_STATE_PROJECTION_REVISION_MISMATCH:state={state.get('projection_revision')}:computed={projection['projection_revision']}")
    if state.get("event_watermark")!=projection.get("event_watermark"): errors.append(f"PROJECT_STATE_EVENT_WATERMARK_MISMATCH:state={state.get('event_watermark')}:computed={projection.get('event_watermark')}")
    if sorted(state.get("active_claim_ids",[]))!=projection.get("active_claim_ids"): errors.append(f"PROJECT_STATE_ACTIVE_CLAIMS_MISMATCH:state={sorted(state.get('active_claim_ids',[]))}:computed={projection.get('active_claim_ids')}")
    context=load("docs/state/v2/context-pack.json")
    paths=context.get("relevant_paths") if isinstance(context.get("relevant_paths"),list) else []
    try: current_scope=scope_revision(paths)
    except (ValueError,subprocess.SubprocessError) as exc: errors.append(f"context:{exc}"); current_scope=""
    context_errors=validate_context_pack(context,base_is_ancestor=is_ancestor(context.get("base_main_sha")),current_projection_revision=projection["projection_revision"],current_relevant_scope_revision=current_scope,current_authority_revision=str(state.get("authority_revision","")))
    errors.extend(f"context:{x}" for x in context_errors)
    if context.get("relevant_scope_revision")!=current_scope: errors.append(f"CONTEXT_SCOPE_REVISION_MISMATCH:state={context.get('relevant_scope_revision')}:computed={current_scope}")
    if context.get("event_watermark")!=projection.get("event_watermark"): errors.append(f"CONTEXT_EVENT_WATERMARK_MISMATCH:state={context.get('event_watermark')}:computed={projection.get('event_watermark')}")
    if sorted(context.get("active_claim_ids",[]))!=projection.get("active_claim_ids"): errors.append(f"CONTEXT_ACTIVE_CLAIMS_MISMATCH:state={sorted(context.get('active_claim_ids',[]))}:computed={projection.get('active_claim_ids')}")
    active=load("docs/state/v2/active-claims.json")
    projected_ids=sorted(str(i.get("claim_id","")) for i in active.get("claims",[]) if isinstance(i,dict))
    effective_ids=sorted(str(i.get("claim_id","")) for i in effective_claims if i.get("state") in ACTIVE_CLAIM_STATES)
    if projected_ids!=effective_ids: errors.append(f"ACTIVE_CLAIMS_ID_PROJECTION_MISMATCH:state={projected_ids}:computed={effective_ids}")
    if active.get("collisions")!=projection.get("claim_collisions"): errors.append("ACTIVE_CLAIMS_COLLISION_PROJECTION_MISMATCH")
    tokens=[i.get("fencing_token") for i in claims if isinstance(i.get("fencing_token"),int) and not isinstance(i.get("fencing_token"),bool)]
    high=max(tokens,default=0)
    if active.get("fencing_high_watermark")!=high: errors.append(f"FENCING_HIGH_WATERMARK_MISMATCH:state={active.get('fencing_high_watermark')}:computed={high}")
    graph=load("docs/state/v2/graph-snapshot.json")
    for key,expected in (("authority_advanced",False),("h_id_allocations",0),("outbound","CLOSED"),("send_allowed",0)):
        value=graph.get(key)
        if value!=expected or (type(expected) is int and isinstance(value,bool)): errors.append(f"GRAPH_SAFETY_LOCK_MISMATCH:{key}")
    if state.get("authority_advanced") is not False: errors.append("STATE_AUTHORITY_ADVANCED_FORBIDDEN")
    if state.get("h_id_allocation_allowed") is not False: errors.append("STATE_H_ID_ALLOCATION_FORBIDDEN")
    if state.get("outbound_allowed") is not False: errors.append("STATE_OUTBOUND_FORBIDDEN")
    errors.extend(f"death-drill:MISSING_{key}" for key in death_drill(state))
    tasks=load("docs/state/v2/tasks.json"); errors.extend(task_program_errors(tasks))
    cps=load("docs/state/v2/checkpoint.json"); cids=[i.get("id") for i in cps.get("checkpoints",[]) if isinstance(i,dict)]
    if len(cids)!=len(set(cids)): errors.append("DUPLICATE_CHECKPOINT_ID")
    if errors:
        print("v2_contract_guard: FAIL")
        print(f"computed_projection_revision={projection['projection_revision']}")
        print(f"computed_event_watermark={json.dumps(projection.get('event_watermark'),sort_keys=True)}")
        print(f"computed_active_claim_ids={json.dumps(projection.get('active_claim_ids'),sort_keys=True)}")
        print(f"computed_relevant_scope_revision={current_scope}")
        for error in sorted(set(errors)): print(f"- {error}")
        return 1
    print(f"v2_contract_guard: PASS events={len(events)} claims={len(claims)} projection={projection['projection_revision']} context={context['context_pack_revision']} scope={current_scope}")
    return 0
if __name__=="__main__": sys.exit(main())
