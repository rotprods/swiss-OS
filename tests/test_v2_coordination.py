import copy, unittest
from swiss_os.v2_coordination import *
GIT_SHA="a"*40
def event(event_id="EVT-1",idempotency="idem-1",event_type="WORK_STARTED"):
    return {"schema_version":"COS-V2-EVENT-1.0","event_id":event_id,"event_type":event_type,"occurred_at":"2026-08-29T21:42:00Z","project_id":"P","agent_id":"A","session_id":"S","workstream_id":"W","objective_id":"O","correlation_id":"C","repo":"owner/repo","main_sha_observed":GIT_SHA,"base_sha":GIT_SHA,"authority_ceiling":"PREAUTHORITY","summary":"x","next_action":"y","idempotency_key":idempotency,"canonical_hotel_mutation_allowed":False,"h_id_allocation_allowed":False,"outbound_allowed":False}
def claim(claim_id="CL-1",scopes=None,semantics=None,token=1):
    return {"schema_version":"COS-V2-CLAIM-1.0","claim_id":claim_id,"project_id":"P","agent_id":"A","session_id":"S","workstream_id":"W","objective_id":"O","correlation_id":"C","state":"ACTIVE","claimed_at":"2026-08-29T21:42:00Z","base_sha":GIT_SHA,"branch":"branch","resource_scopes":scopes or ["architecture"],"semantic_scopes":semantics or ["ARCHITECTURE"],"excluded_scopes":["OUTBOUND"],"fencing_token":token,"authority_ceiling":"PREAUTHORITY","idempotency_key":claim_id}
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
    def test_context(self):
        p=reduce_coordination([event()],[claim()])
        pack=build_context_pack(project_id="P",main_sha=GIT_SHA,authority_revision="A",projection=p,state_refs=[],blockers=[],next_safe_actions=[])
        self.assertEqual(validate_context_pack(pack,current_main_sha=GIT_SHA,current_projection_revision=p["projection_revision"]),())
        self.assertIn("STALE_MAIN_SHA",validate_context_pack(pack,current_main_sha="b"*40,current_projection_revision=p["projection_revision"]))
        tam=copy.deepcopy(pack); tam["blockers"].append("x")
        self.assertIn("CONTEXT_PACK_HASH_MISMATCH",validate_context_pack(tam,current_main_sha=GIT_SHA,current_projection_revision=p["projection_revision"]))
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
