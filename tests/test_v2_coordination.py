import copy, unittest
from swiss_os.v2_coordination import *
GIT_SHA="a"*40
SCOPE_REV="b"*64
def event(event_id="EVT-1",idempotency="idem-1",event_type="WORK_STARTED",causation=None,occurred_at="2026-08-29T21:42:00Z"):
    payload={"schema_version":"COS-V2-EVENT-1.0","event_id":event_id,"event_type":event_type,"occurred_at":occurred_at,"project_id":"P","agent_id":"A","session_id":"S","workstream_id":"W","objective_id":"O","correlation_id":"C","repo":"owner/repo","main_sha_observed":GIT_SHA,"base_sha":GIT_SHA,"authority_ceiling":"PREAUTHORITY","summary":"x","next_action":"y","idempotency_key":idempotency,"canonical_hotel_mutation_allowed":False,"h_id_allocation_allowed":False,"outbound_allowed":False}
    if causation is not None: payload["causation"]=causation
    return payload
def claim(claim_id="CL-1",scopes=None,semantics=None,token=1,state="ACTIVE"):
    return {"schema_version":"COS-V2-CLAIM-1.0","claim_id":claim_id,"project_id":"P","agent_id":"A","session_id":"S","workstream_id":"W","objective_id":"O","correlation_id":"C","state":state,"claimed_at":"2026-08-29T21:42:00Z","base_sha":GIT_SHA,"branch":"branch","resource_scopes":scopes or ["architecture"],"semantic_scopes":semantics or ["ARCHITECTURE"],"excluded_scopes":["OUTBOUND"],"fencing_token":token,"authority_ceiling":"PREAUTHORITY","idempotency_key":claim_id}
class T(unittest.TestCase):
    def test_event(self):
        self.assertEqual(validate_event(event()),())
        x=event(); x["outbound_allowed"]="false"; self.assertIn("INVALID_OUTBOUND_ALLOWED_BOOLEAN",validate_event(x))
        x=event(); x["base_sha"]="b"*64; self.assertIn("INVALID_BASE_SHA",validate_event(x))
    def test_claim(self):
        self.assertEqual(validate_claim(claim()),())
        self.assertIn("INVALID_FENCING_TOKEN",validate_claim(claim(token=0)))
        self.assertIn("INVALID_FENCING_TOKEN",validate_claim(claim(token=True)))
    def test_collision(self):
        self.assertEqual(len(detect_claim_collisions([claim("A"),claim("B")])),1)
        self.assertEqual(detect_claim_collisions([claim("A",["x"],["X"]),claim("B",["y"],["Y"])]),[])
    def test_duplicate_idem(self):
        p=reduce_coordination([event("E1","same"),event("E2","same")],[])
        self.assertTrue(any(v.startswith("DUPLICATE_IDEMPOTENCY_KEY:") for v in p["violations"]))
    def test_duplicate_event(self):
        p=reduce_coordination([event("E1","i1"),event("E1","i2")],[])
        self.assertIn("DUPLICATE_EVENT_ID:E1",p["violations"])
    def test_claim_release_is_event_derived(self):
        c=claim(state="RELEASED")
        acquired=event("E-A","i-a","CLAIM_ACQUIRED",["claim:CL-1"],"2026-08-29T21:42:00Z")
        released=event("E-R","i-r","CLAIM_RELEASED",["claim:CL-1"],"2026-08-29T21:43:00Z")
        projected,errs=project_claim_lifecycle([released,acquired],[c])
        self.assertEqual(errs,())
        self.assertEqual(projected[0]["state"],"RELEASED")
        self.assertEqual(reduce_coordination([released,acquired],[c])["active_claim_ids"],[])
    def test_claim_supersession_is_event_derived(self):
        c=claim(state="SUPERSEDED")
        acquired=event("E-A","i-a","CLAIM_ACQUIRED",["claim:CL-1"],"2026-08-29T21:42:00Z")
        superseded=event("E-S","i-s","CLAIM_SUPERSEDED",["claim:CL-1"],"2026-08-29T21:43:00Z")
        projected,errs=project_claim_lifecycle([superseded,acquired],[c])
        self.assertEqual(errs,())
        self.assertEqual(projected[0]["state"],"SUPERSEDED")
    def test_legacy_terminal_event_without_explicit_ref_is_uniquely_inferred(self):
        c=claim(state="RELEASED")
        released=event("E-R","i-r","CLAIM_RELEASED",None,"2026-08-29T21:43:00Z")
        projected,errs=project_claim_lifecycle([released],[c])
        self.assertEqual(errs,())
        self.assertEqual(projected[0]["state"],"RELEASED")
        self.assertNotIn("INVALID_CLAIM_LIFECYCLE_REFERENCE_COUNT",validate_event(released))
    def test_legacy_missing_ref_fails_when_claim_identity_is_ambiguous(self):
        first=claim("CL-1",state="RELEASED")
        second=claim("CL-2",token=2,state="RELEASED")
        released=event("E-R","i-r","CLAIM_RELEASED",None,"2026-08-29T21:43:00Z")
        _,errs=project_claim_lifecycle([released],[first,second])
        self.assertIn("CLAIM_LIFECYCLE_REFERENCE_COUNT:E-R:0",errs)
    def test_new_lifecycle_event_requires_exact_claim_reference(self):
        c=claim()
        bad=event("E-R","i-r","CLAIM_RELEASED",[],"2026-09-01T00:00:00Z")
        self.assertIn("INVALID_CLAIM_LIFECYCLE_REFERENCE_COUNT",validate_event(bad))
        _,errs=project_claim_lifecycle([bad],[c])
        self.assertIn("CLAIM_LIFECYCLE_REFERENCE_COUNT:E-R:0",errs)
    def test_stale_mutable_claim_state_is_detected(self):
        c=claim(state="ACTIVE")
        acquired=event("E-A","i-a","CLAIM_ACQUIRED",["claim:CL-1"],"2026-08-29T21:42:00Z")
        released=event("E-R","i-r","CLAIM_RELEASED",["claim:CL-1"],"2026-08-29T21:43:00Z")
        _,errs=project_claim_lifecycle([acquired,released],[c])
        self.assertIn("CLAIM_DECLARED_STATE_DRIFT:CL-1:ACTIVE->RELEASED",errs)
    def test_context_descendant_head_without_scope_drift_is_valid(self):
        p=reduce_coordination([event()],[claim()])
        pack=build_context_pack(project_id="P",base_main_sha=GIT_SHA,authority_revision="A",projection=p,state_refs=[],relevant_paths=["ARCHITECTURE.md"],relevant_scope_revision=SCOPE_REV,blockers=[],next_safe_actions=[])
        self.assertEqual(validate_context_pack(pack,base_is_ancestor=True,current_projection_revision=p["projection_revision"],current_relevant_scope_revision=SCOPE_REV,current_authority_revision="A"),())
    def test_context_rejects_nonancestor_or_relevant_drift(self):
        p=reduce_coordination([event()],[claim()])
        pack=build_context_pack(project_id="P",base_main_sha=GIT_SHA,authority_revision="A",projection=p,state_refs=[],relevant_paths=["ARCHITECTURE.md"],relevant_scope_revision=SCOPE_REV,blockers=[],next_safe_actions=[])
        self.assertIn("BASE_NOT_ANCESTOR",validate_context_pack(pack,base_is_ancestor=False,current_projection_revision=p["projection_revision"],current_relevant_scope_revision=SCOPE_REV,current_authority_revision="A"))
        self.assertIn("RELEVANT_SCOPE_DRIFT",validate_context_pack(pack,base_is_ancestor=True,current_projection_revision=p["projection_revision"],current_relevant_scope_revision="c"*64,current_authority_revision="A"))
    def test_context_tamper_and_authority_drift(self):
        p=reduce_coordination([event()],[claim()])
        pack=build_context_pack(project_id="P",base_main_sha=GIT_SHA,authority_revision="A",projection=p,state_refs=[],relevant_paths=["ARCHITECTURE.md"],relevant_scope_revision=SCOPE_REV,blockers=[],next_safe_actions=[])
        tam=copy.deepcopy(pack); tam["blockers"].append("x")
        errs=validate_context_pack(tam,base_is_ancestor=True,current_projection_revision=p["projection_revision"],current_relevant_scope_revision=SCOPE_REV,current_authority_revision="B")
        self.assertIn("CONTEXT_PACK_HASH_MISMATCH",errs); self.assertIn("STALE_AUTHORITY_REVISION",errs)
    def test_state(self):
        s={"schema_version":"COS-V2-PROJECT-STATE-1.0","project_id":"P","repo":"r","main_sha_observed":GIT_SHA,"authority_epoch":"E","authority_revision":"R","state":"I","current_objective_id":"O","authority_advanced":False,"h_id_allocation_allowed":False,"outbound_allowed":False}
        self.assertEqual(validate_project_state(s),())
        s["outbound_allowed"]=True; self.assertIn("V2_ARCHITECTURE_STATE_MUST_NOT_OPEN_OUTBOUND",validate_project_state(s))
    def test_death(self):
        self.assertIn("north_star_ref",death_drill({}))
        s={"north_star_ref":"G","current_objective_id":"O","main_sha_observed":GIT_SHA,"event_watermark":{"e":1},"projection_revision":"P","active_claim_ids":[],"open_prs":[],"verified_work":[],"unverified_work":[],"blockers":[],"risks":[],"next_safe_actions":["x"],"authority_revision":"A"}
        self.assertEqual(death_drill(s),())
    def test_deterministic(self):
        self.assertEqual(reduce_coordination([event()],[claim()])["projection_revision"],reduce_coordination([event()],[claim()])["projection_revision"])
