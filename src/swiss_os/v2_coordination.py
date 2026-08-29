from __future__ import annotations
import hashlib, json
from typing import Iterable, Mapping, Sequence

EVENT_SCHEMA = "COS-V2-EVENT-1.0"
CLAIM_SCHEMA = "COS-V2-CLAIM-1.0"
CONTEXT_SCHEMA = "COS-V2-CONTEXT-PACK-1.0"
PROJECT_STATE_SCHEMA = "COS-V2-PROJECT-STATE-1.0"
ACTIVE_CLAIM_STATES = frozenset({"ACTIVE"})
KNOWN_EVENT_TYPES = frozenset({
    "HELLO","WORK_STARTED","WORK_PROGRESS","WORK_BLOCKED","WORK_COMPLETED",
    "CLAIM_ACQUIRED","CLAIM_RELEASED","CLAIM_SUPERSEDED",
    "CHECKPOINT_REACHED","DECISION_RECORDED","EVIDENCE_RECORDED",
    "CONTEXT_PACK_EMITTED","HEARTBEAT"
})
class CoordinationError(ValueError): pass
def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()
def _text(payload: Mapping[str, object], key: str) -> str:
    v=payload.get(key); return v.strip() if isinstance(v,str) else ""
def _require_text(payload,key,errors):
    v=_text(payload,key)
    if not v: errors.append(f"MISSING_{key.upper()}")
    return v
def _is_sha256(v:str)->bool:
    return len(v)==64 and all(c in "0123456789abcdef" for c in v)
def validate_event(event):
    errors=[]
    if event.get("schema_version")!=EVENT_SCHEMA: errors.append("INVALID_EVENT_SCHEMA")
    for key in ("event_id","event_type","occurred_at","project_id","agent_id","session_id","workstream_id","objective_id","correlation_id","repo","main_sha_observed","base_sha","authority_ceiling","summary","next_action","idempotency_key"):
        _require_text(event,key,errors)
    et=_text(event,"event_type")
    if et and et not in KNOWN_EVENT_TYPES: errors.append("UNKNOWN_EVENT_TYPE")
    for key in ("main_sha_observed","base_sha"):
        v=_text(event,key)
        if v and not _is_sha256(v): errors.append(f"INVALID_{key.upper()}")
    for key in ("canonical_hotel_mutation_allowed","h_id_allocation_allowed","outbound_allowed"):
        if not isinstance(event.get(key),bool): errors.append(f"INVALID_{key.upper()}_BOOLEAN")
    return tuple(dict.fromkeys(errors))
def validate_claim(claim):
    errors=[]
    if claim.get("schema_version")!=CLAIM_SCHEMA: errors.append("INVALID_CLAIM_SCHEMA")
    for key in ("claim_id","project_id","agent_id","session_id","workstream_id","objective_id","correlation_id","state","claimed_at","base_sha","branch","authority_ceiling","idempotency_key"):
        _require_text(claim,key,errors)
    v=_text(claim,"base_sha")
    if v and not _is_sha256(v): errors.append("INVALID_BASE_SHA")
    tok=claim.get("fencing_token")
    if isinstance(tok,bool) or not isinstance(tok,int) or tok<1: errors.append("INVALID_FENCING_TOKEN")
    for key in ("resource_scopes","semantic_scopes","excluded_scopes"):
        val=claim.get(key)
        if not isinstance(val,list) or not all(isinstance(i,str) and i.strip() for i in val): errors.append(f"INVALID_{key.upper()}")
    return tuple(dict.fromkeys(errors))
def scopes_overlap(left:Sequence[str],right:Sequence[str])->bool:
    return bool({x.strip() for x in left if isinstance(x,str) and x.strip()} & {x.strip() for x in right if isinstance(x,str) and x.strip()})
def detect_claim_collisions(claims):
    active=[c for c in claims if c.get("state") in ACTIVE_CLAIM_STATES]; out=[]
    for i,left in enumerate(active):
        for right in active[i+1:]:
            if _text(left,"project_id")!=_text(right,"project_id"): continue
            rs=scopes_overlap(left.get("resource_scopes",[]) if isinstance(left.get("resource_scopes"),list) else [], right.get("resource_scopes",[]) if isinstance(right.get("resource_scopes"),list) else [])
            ss=scopes_overlap(left.get("semantic_scopes",[]) if isinstance(left.get("semantic_scopes"),list) else [], right.get("semantic_scopes",[]) if isinstance(right.get("semantic_scopes"),list) else [])
            if rs or ss: out.append({"left_claim_id":_text(left,"claim_id"),"right_claim_id":_text(right,"claim_id"),"resource_overlap":rs,"semantic_overlap":ss})
    return out
def reduce_coordination(events,claims):
    events=list(events); claims=list(claims); errors=[]; ids=set(); idem={}; sessions={}
    for e in events:
        errors.extend(f"{_text(e,'event_id') or '<unknown>'}:{x}" for x in validate_event(e))
        eid=_text(e,"event_id")
        if eid:
            if eid in ids: errors.append(f"DUPLICATE_EVENT_ID:{eid}")
            ids.add(eid)
        ik=_text(e,"idempotency_key")
        if ik:
            prior=idem.get(ik)
            if prior and prior!=eid: errors.append(f"DUPLICATE_IDEMPOTENCY_KEY:{ik}")
            idem[ik]=eid
        sid=_text(e,"session_id")
        if sid:
            s=sessions.setdefault(sid,{"session_id":sid,"agent_id":_text(e,"agent_id"),"workstream_id":_text(e,"workstream_id"),"objective_id":_text(e,"objective_id"),"state":"ACTIVE","event_ids":[]})
            s["event_ids"].append(eid)
            if _text(e,"event_type")=="WORK_COMPLETED": s["state"]="COMPLETED"
            elif _text(e,"event_type")=="WORK_BLOCKED": s["state"]="BLOCKED"
    for c in claims:
        errors.extend(f"{_text(c,'claim_id') or '<unknown>'}:{x}" for x in validate_claim(c))
    watermark=None
    if events:
        ordered=sorted((_text(e,"occurred_at"),_text(e,"event_id")) for e in events); watermark={"occurred_at":ordered[-1][0],"event_id":ordered[-1][1]}
    p={"schema_version":"COS-V2-COORDINATION-PROJECTION-1.0","events_count":len(events),"claims_count":len(claims),"sessions":sorted(sessions.values(),key=lambda x:x["session_id"]),"active_claim_ids":sorted(_text(c,"claim_id") for c in claims if c.get("state") in ACTIVE_CLAIM_STATES),"claim_collisions":detect_claim_collisions(claims),"event_watermark":watermark,"violations":sorted(set(errors))}
    p["projection_revision"]=sha256_json({k:v for k,v in p.items() if k!="projection_revision"})
    return p
def build_context_pack(*,project_id,main_sha,authority_revision,projection,state_refs,blockers,next_safe_actions):
    if not _is_sha256(main_sha): raise CoordinationError("main_sha must be lowercase sha256")
    if not project_id.strip(): raise CoordinationError("project_id required")
    p={"schema_version":CONTEXT_SCHEMA,"project_id":project_id,"main_sha":main_sha,"authority_revision":authority_revision,"projection_revision":projection.get("projection_revision"),"event_watermark":projection.get("event_watermark"),"state_refs":list(state_refs),"active_claim_ids":list(projection.get("active_claim_ids",[])),"blockers":list(blockers),"next_safe_actions":list(next_safe_actions)}
    p["context_pack_revision"]=sha256_json(p); return p
def validate_context_pack(pack,*,current_main_sha,current_projection_revision):
    errors=[]
    if pack.get("schema_version")!=CONTEXT_SCHEMA: errors.append("INVALID_CONTEXT_SCHEMA")
    if pack.get("main_sha")!=current_main_sha: errors.append("STALE_MAIN_SHA")
    if pack.get("projection_revision")!=current_projection_revision: errors.append("STALE_PROJECTION_REVISION")
    if pack.get("context_pack_revision")!=sha256_json({k:v for k,v in pack.items() if k!="context_pack_revision"}): errors.append("CONTEXT_PACK_HASH_MISMATCH")
    return tuple(errors)
def validate_project_state(payload):
    errors=[]
    if payload.get("schema_version")!=PROJECT_STATE_SCHEMA: errors.append("INVALID_PROJECT_STATE_SCHEMA")
    for key in ("project_id","repo","main_sha_observed","authority_epoch","authority_revision","state","current_objective_id"): _require_text(payload,key,errors)
    v=_text(payload,"main_sha_observed")
    if v and not _is_sha256(v): errors.append("INVALID_MAIN_SHA")
    for key in ("authority_advanced","h_id_allocation_allowed","outbound_allowed"):
        if not isinstance(payload.get(key),bool): errors.append(f"INVALID_{key.upper()}_BOOLEAN")
    if payload.get("outbound_allowed") is True: errors.append("V2_ARCHITECTURE_STATE_MUST_NOT_OPEN_OUTBOUND")
    return tuple(dict.fromkeys(errors))
def death_drill(snapshot):
    req={"north_star_ref","current_objective_id","main_sha_observed","event_watermark","projection_revision","active_claim_ids","open_prs","verified_work","unverified_work","blockers","risks","next_safe_actions","authority_revision"}
    return tuple(sorted(k for k in req if k not in snapshot or snapshot.get(k) in (None,"")))
