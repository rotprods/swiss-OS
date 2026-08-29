#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, subprocess
from pathlib import Path
from swiss_os.v2_coordination import ACTIVE_CLAIM_STATES, death_drill, reduce_coordination, validate_context_pack

ROOT=Path(__file__).resolve().parents[1]
CANONICAL_ZERO_CONTEXT=("GOAL.md","STATE.md","ARCHITECTURE.md","HANDOFF.md","TASKS.md","LEXICON.md","docs/state/v2/project-state.json","docs/state/v2/context-pack.json","docs/state/v2/active-claims.json","docs/state/v2/checkpoint.json")

def load(path:Path):
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise ValueError(f"{path}: expected object")
    return value

def ledger_projection(root:Path=ROOT):
    events=[load(p) for p in sorted((root/"docs/state/v2/events").glob("*.json"))]
    claims=[load(p) for p in sorted((root/"docs/state/v2/claims").glob("*.json"))]
    return reduce_coordination(events,claims), events, claims

def scope_revision(paths,root:Path=ROOT):
    entries=[]
    for rel in paths:
        path=root/rel
        if not path.is_file(): raise ValueError(f"relevant path missing: {rel}")
        oid=subprocess.check_output(["git","hash-object",rel],cwd=root,text=True).strip()
        entries.append(f"{rel}:{oid}")
    return hashlib.sha256("\n".join(entries).encode()).hexdigest()

def is_ancestor(base,root:Path=ROOT):
    return isinstance(base,str) and len(base)==40 and subprocess.run(["git","merge-base","--is-ancestor",base,"HEAD"],cwd=root,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False).returncode==0

def run_drill(root:Path=ROOT):
    errors=[]
    # Recovery drill: rebuild coordination projection from durable Event+Claim ledger only.
    rebuilt, events, claims=ledger_projection(root)
    state=load(root/"docs/state/v2/project-state.json")
    if rebuilt.get("violations"): errors.extend(f"ledger:{x}" for x in rebuilt["violations"])
    if rebuilt.get("projection_revision")!=state.get("projection_revision"): errors.append("RECOVERY_REBUILD_REVISION_MISMATCH")
    active=load(root/"docs/state/v2/active-claims.json")
    expected_active=sorted(str(c.get("claim_id","")) for c in claims if c.get("state") in ACTIVE_CLAIM_STATES)
    projected_active=sorted(str(c.get("claim_id","")) for c in active.get("claims",[]) if isinstance(c,dict))
    if expected_active!=projected_active: errors.append("RECOVERY_ACTIVE_CLAIM_MISMATCH")

    # Zero-context death drill: reconstruct resumable operator state from canonical durable surfaces only.
    for rel in CANONICAL_ZERO_CONTEXT:
        if not (root/rel).is_file(): errors.append(f"ZERO_CONTEXT_MISSING:{rel}")
    missing=death_drill(state)
    errors.extend(f"ZERO_CONTEXT_STATE_MISSING:{key}" for key in missing)
    handoff=(root/"HANDOFF.md").read_text(encoding="utf-8")
    for rel in ("GOAL.md","STATE.md","ARCHITECTURE.md","docs/state/v2/project-state.json","docs/state/v2/context-pack.json","docs/state/v2/active-claims.json","TASKS.md"):
        if rel not in handoff: errors.append(f"HANDOFF_POINTER_MISSING:{rel}")
    context=load(root/"docs/state/v2/context-pack.json")
    paths=context.get("relevant_paths") if isinstance(context.get("relevant_paths"),list) else []
    scope=scope_revision(paths,root)
    errors.extend(f"context:{x}" for x in validate_context_pack(context,base_is_ancestor=is_ancestor(context.get("base_main_sha"),root),current_projection_revision=rebuilt.get("projection_revision"),current_relevant_scope_revision=scope,current_authority_revision=str(state.get("authority_revision",""))))
    if context.get("event_watermark")!=rebuilt.get("event_watermark"): errors.append("ZERO_CONTEXT_EVENT_WATERMARK_MISMATCH")

    graph=load(root/"docs/state/v2/graph-snapshot.json")
    safety={"authority_advanced":False,"h_id_allocations":0,"outbound":"CLOSED","send_allowed":0}
    for key,expected in safety.items():
        value=graph.get(key)
        if value!=expected or (type(expected) is int and isinstance(value,bool)): errors.append(f"SAFETY_LOCK_MISMATCH:{key}")

    receipt={
        "schema_version":"COS-V2-EMPIRICAL-QUALIFICATION-RECEIPT-1.0",
        "project_id":"SWITZERLAND_JOB_OS",
        "objective_id":"OBJ-V2-RECOVERY-DEATH-DRILL",
        "recovery_drill":"PASS" if not any(e.startswith(("RECOVERY_","ledger:")) for e in errors) else "FAIL",
        "zero_context_death_drill":"PASS" if not any(e.startswith(("ZERO_CONTEXT_","HANDOFF_","context:")) for e in errors) else "FAIL",
        "rebuilt_projection_revision":rebuilt.get("projection_revision"),
        "event_watermark":rebuilt.get("event_watermark"),
        "events_replayed":len(events),
        "claims_replayed":len(claims),
        "active_claim_ids":rebuilt.get("active_claim_ids"),
        "relevant_scope_revision":scope,
        "authority_revision":state.get("authority_revision"),
        "authority_advanced":False,
        "h_id_allocations":0,
        "outbound":"CLOSED",
        "send_allowed":0,
        "errors":sorted(set(errors)),
    }
    receipt["overall"]="PASS" if not errors else "FAIL"
    return receipt

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--receipt")
    args=parser.parse_args(); receipt=run_drill(ROOT)
    rendered=json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)
    print(rendered)
    if args.receipt: Path(args.receipt).write_text(rendered+"\n",encoding="utf-8")
    return 0 if receipt["overall"]=="PASS" else 1

if __name__=="__main__": raise SystemExit(main())
