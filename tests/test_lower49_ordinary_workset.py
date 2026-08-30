import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSET = ROOT / "docs/operations/CRM_IDENTITY_WORKSET_LOWER49_ORDINARY_47_2026-08-30.json"


def _sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def test_lower49_workset_is_exact_deterministic_and_fail_closed():
    workset = json.loads(WORKSET.read_text(encoding="utf-8"))
    core = dict(workset)
    claimed = core.pop("workset_sha256")
    assert _sha(core) == claimed == "8817941127ede8f9329d81b4831b1fd6643e9ab4c19438c3fa612b78e1169050"
    assert workset["parent_git_sha"] == "317d5892b5c80f0066a16339ed2a1f10dcdae1ef"
    assert workset["authority_revision"] == "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6"
    assert workset["active_claim"]["claim_id"] == "CLAIM-CRM-SRR-SPECIAL-006"
    assert workset["active_claim"]["fencing_token"] == 6
    assert workset["historical_evidence_plane"]["fencing_token"] == 5
    assert workset["historical_evidence_plane"]["use"] == "EVIDENCE_ONLY_NO_CURRENT_WRITE_AUTHORITY"

    all_keys = []
    for batch in workset["batches"]:
        packet = json.loads((ROOT / batch["input_packet"]).read_text(encoding="utf-8"))
        assert packet["packet_sha256"] == batch["input_packet_semantic_sha256"]
        reviews = packet["reviews"]
        assert len(reviews) == batch["records"]
        keys = [item["source_record_key"] for item in reviews]
        assert _sha(keys) == batch["reviewed_source_record_keys_sha256"]
        assert all(item["review_outcome"] == "CURRENT_PUBLIC_DISTINCTNESS_SUPPORTED" for item in reviews)
        assert all(item["terminal_source_mapping"] == "NONE" for item in reviews)
        assert all(item["authority_effect"] == "NONE" for item in reviews)
        assert all(item["new_identity_status"] == "UNALLOCATED_PREAUTH_CANDIDATE" for item in reviews)
        all_keys.extend(keys)

    assert [batch["records"] for batch in workset["batches"]] == [10, 10, 10, 10, 7]
    assert len(all_keys) == len(set(all_keys)) == 47
    assert set(workset["selection_contract"]["special_source_record_keys"]).isdisjoint(all_keys)
    assert workset["selection_contract"]["ordinary_records"] == 47
    assert "DISTINCTNESS_REVIEW_IS_NOT_TYPED_SRR" in workset["selection_contract"]["execution_semantics"]
    safety = workset["safety"]
    assert safety == {
        "authority_advanced": False,
        "canonical_id_reservations": 0,
        "h_0691": "UNALLOCATED",
        "h_id_allocations": 0,
        "irreversible_external_actions": 0,
        "outbound": "CLOSED",
        "send_allowed": 0,
        "terminal_mapping_delta": 0,
    }
