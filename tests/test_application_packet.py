import json
import sqlite3
import unittest

from swiss_os.application_adversarial import (
    AuditState,
    DIMENSION_WEIGHTS,
    QUESTION_BANK,
    RISK_COMPONENTS,
    STAKEHOLDERS,
)
from swiss_os.application_adversarial_v31 import HARD_GATE_EXPECTED, evaluate_application
from swiss_os.application_packet import PacketCompileRequest, compile_packet, persist_compiled_packet
from swiss_os.application_readiness import TargetBoundReadinessReceipt, asset_set_sha256
from swiss_os.candidate_assets import AssetManifest
from swiss_os.candidate_truth import CandidateField

CANDIDATE_SHA = "1" * 64
VACANCY_SHA = "2" * 64
OTHER_CANDIDATE_SHA = "3" * 64
OTHER_VACANCY_SHA = "4" * 64


def field(key: str) -> CandidateField:
    return CandidateField(key=key, truth_state="VERIFIED", approved=True, external_allowed=True)


def asset(asset_id: str, asset_type: str, state: str = "APPROVED", *, version: str = "v2", sha: str = "a") -> AssetManifest:
    return AssetManifest(
        asset_id=asset_id,
        asset_type=asset_type,
        version=version,
        state=state,
        private_storage_ref=f"private://{asset_id}",
        claim_ids=("CLAIM-1",),
        content_sha256=sha * 64,
    )


ENTRY_FIELDS = (
    field("contact.email"), field("contact.phone"),
    field("language.wording"), field("availability.start"),
)
HYBRID_FIELDS = ENTRY_FIELDS + (field("social.linkedin"),)


def entry_assets(*, version: str = "v2", sha: str = "a") -> tuple[AssetManifest, ...]:
    return (asset("ASSET-CV-ENTRY-V2", "CV_ENTRY", version=version, sha=sha),)


def ready_aag(*, evidence: int = 98) -> dict[str, object]:
    receipt = evaluate_application(
        dimension_scores={key: 95 for key in DIMENSION_WEIGHTS},
        hard_gate_states=dict(HARD_GATE_EXPECTED),
        risk_scores={key: 10 for key in RISK_COMPONENTS},
        evidence_confidence_score=evidence,
        human_resonance_score=92,
        desperation_score=5,
        questionnaire_answers={q.question_id: AuditState.PASS.value for q in QUESTION_BANK},
        stakeholder_votes={key: True for key in STAKEHOLDERS},
    )
    assert receipt["application_ready_no_send"] is True
    return receipt


def readiness(
    *,
    organization_id: str = "ORG-HOTEL-0001",
    opportunity_id: str = "OPP-1",
    lane: str = "ENTRY",
    channel_id: str = "CHANNEL-EMAIL-1",
    target_role: str = "Housekeeping Mitarbeiter/in",
    vacancy_source_url: str = "https://example.test/jobs/housekeeping",
    candidate_truth_sha256: str = CANDIDATE_SHA,
    vacancy_evidence_sha256: str = VACANCY_SHA,
    evaluated_assets: tuple[AssetManifest, ...] | None = None,
    aag_receipt: dict[str, object] | None = None,
) -> TargetBoundReadinessReceipt:
    evaluated_assets = evaluated_assets or entry_assets()
    return TargetBoundReadinessReceipt.build(
        organization_id=organization_id,
        opportunity_id=opportunity_id,
        lane=lane,
        channel_id=channel_id,
        target_role=target_role,
        vacancy_source_url=vacancy_source_url,
        candidate_truth_sha256=candidate_truth_sha256,
        vacancy_evidence_sha256=vacancy_evidence_sha256,
        evaluated_asset_set_sha256=asset_set_sha256(evaluated_assets),
        aag_receipt=aag_receipt or ready_aag(),
    )


def entry_request(
    *,
    organization_id: str = "ORG-HOTEL-0001",
    opportunity_id: str | None = "OPP-1",
    lane: str = "ENTRY",
    channel_id: str = "CHANNEL-EMAIL-1",
    assets: tuple[AssetManifest, ...] | None = None,
    candidate_truth_sha256: str = CANDIDATE_SHA,
    vacancy_evidence_sha256: str = VACANCY_SHA,
    readiness_receipt: TargetBoundReadinessReceipt | None = None,
) -> PacketCompileRequest:
    assets = assets or entry_assets()
    readiness_receipt = readiness_receipt or readiness(
        organization_id=organization_id,
        opportunity_id=opportunity_id or "OPP-1",
        lane=lane,
        channel_id=channel_id,
        candidate_truth_sha256=candidate_truth_sha256,
        vacancy_evidence_sha256=vacancy_evidence_sha256,
        evaluated_assets=assets,
    )
    return PacketCompileRequest(
        organization_id=organization_id,
        opportunity_id=opportunity_id,
        lane=lane,
        candidate_fields=ENTRY_FIELDS,
        assets=assets,
        channel_id=channel_id,
        readiness=readiness_receipt,
        candidate_truth_sha256=candidate_truth_sha256,
        vacancy_evidence_sha256=vacancy_evidence_sha256,
    )


def hybrid_assets(*, portfolio_version: str = "v2", portfolio_sha: str = "c") -> tuple[AssetManifest, ...]:
    return (
        asset("ASSET-CV-HYBRID-V2", "CV_HYBRID", version="v2", sha="b"),
        asset("ASSET-PORTFOLIO", "PORTFOLIO", version=portfolio_version, sha=portfolio_sha),
        asset("ASSET-CASE", "CASE_STUDY", version="v2", sha="d"),
    )


def hybrid_request(*, portfolio_version: str = "v2", portfolio_sha: str = "c") -> PacketCompileRequest:
    assets = hybrid_assets(portfolio_version=portfolio_version, portfolio_sha=portfolio_sha)
    return PacketCompileRequest(
        organization_id="ORG-HOTEL-0001",
        opportunity_id="OPP-HYBRID-1",
        lane="HYBRID",
        candidate_fields=HYBRID_FIELDS,
        assets=assets,
        channel_id="CHANNEL-EMAIL-1",
        readiness=readiness(
            opportunity_id="OPP-HYBRID-1",
            lane="HYBRID",
            target_role="Content & Digital Marketing Specialist",
            vacancy_source_url="https://example.test/jobs/content-digital",
            evaluated_assets=assets,
        ),
        candidate_truth_sha256=CANDIDATE_SHA,
        vacancy_evidence_sha256=VACANCY_SHA,
    )


def create_persistence_tables(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("""CREATE TABLE applications_v2(
        application_id TEXT PRIMARY KEY, opportunity_id TEXT, organization_id TEXT NOT NULL,
        lane TEXT NOT NULL, state TEXT NOT NULL, selected_asset_manifest_id TEXT,
        selected_channel_id TEXT, idempotency_key TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL
    )""")
    conn.execute("""CREATE TABLE application_packet_receipts_v1(
        packet_id TEXT PRIMARY KEY, application_id TEXT NOT NULL,
        readiness_binding_sha256 TEXT NOT NULL, aag_receipt_sha256 TEXT NOT NULL,
        candidate_truth_sha256 TEXT NOT NULL, vacancy_evidence_sha256 TEXT NOT NULL,
        evaluated_asset_set_sha256 TEXT NOT NULL, target_role TEXT NOT NULL,
        vacancy_source_url TEXT NOT NULL, selected_asset_manifest_id TEXT NOT NULL,
        selected_asset_version TEXT NOT NULL, selected_asset_sha256 TEXT NOT NULL,
        selected_channel_id TEXT NOT NULL, supplemental_assets_json TEXT NOT NULL,
        state TEXT NOT NULL, created_at TEXT NOT NULL,
        FOREIGN KEY(application_id) REFERENCES applications_v2(application_id) ON DELETE CASCADE
    )""")


class ApplicationPacketTests(unittest.TestCase):
    def test_entry_compiles_only_with_target_and_input_bound_ready_aag(self):
        packet = compile_packet(entry_request())
        self.assertTrue(packet.gate.ready)
        self.assertEqual(packet.selected_asset_manifest_id, "ASSET-CV-ENTRY-V2")
        self.assertEqual(packet.candidate_truth_sha256, CANDIDATE_SHA)
        self.assertEqual(packet.vacancy_evidence_sha256, VACANCY_SHA)
        self.assertEqual(packet.evaluated_asset_set_sha256, asset_set_sha256(entry_assets()))
        self.assertEqual(packet.public_safe_receipt()["state"], "PACKET_COMPILED_NO_SEND")
        self.assertEqual(packet.public_safe_receipt()["send_allowed"], 0)

    def test_packet_requires_exact_opportunity(self):
        with self.assertRaisesRegex(ValueError, "exact opportunity_id"):
            compile_packet(entry_request(opportunity_id=None))

    def test_readiness_from_other_target_dimensions_is_rejected(self):
        fixtures = [
            (readiness(organization_id="ORG-HOTEL-OTHER"), "organization_id"),
            (readiness(opportunity_id="OPP-OTHER"), "opportunity_id"),
            (readiness(lane="HYBRID"), "lane"),
            (readiness(channel_id="CHANNEL-PORTAL-1"), "channel_id"),
        ]
        for wrong, field_name in fixtures:
            with self.assertRaisesRegex(ValueError, f"readiness target/input mismatch: {field_name}"):
                compile_packet(entry_request(readiness_receipt=wrong))

    def test_stale_candidate_truth_digest_is_rejected(self):
        old = readiness(candidate_truth_sha256=CANDIDATE_SHA)
        with self.assertRaisesRegex(ValueError, "candidate_truth_sha256"):
            compile_packet(entry_request(
                candidate_truth_sha256=OTHER_CANDIDATE_SHA,
                readiness_receipt=old,
            ))

    def test_stale_vacancy_evidence_digest_is_rejected(self):
        old = readiness(vacancy_evidence_sha256=VACANCY_SHA)
        with self.assertRaisesRegex(ValueError, "vacancy_evidence_sha256"):
            compile_packet(entry_request(
                vacancy_evidence_sha256=OTHER_VACANCY_SHA,
                readiness_receipt=old,
            ))

    def test_stale_asset_set_digest_is_rejected(self):
        old_assets = entry_assets(version="v2", sha="a")
        new_assets = entry_assets(version="v3", sha="b")
        old = readiness(evaluated_assets=old_assets)
        with self.assertRaisesRegex(ValueError, "evaluated asset set mismatch"):
            compile_packet(entry_request(assets=new_assets, readiness_receipt=old))

    def test_tampered_readiness_binding_is_rejected(self):
        original = readiness()
        tampered = TargetBoundReadinessReceipt(**{**original.__dict__, "binding_sha256": "0" * 64})
        with self.assertRaisesRegex(ValueError, "binding hash mismatch"):
            compile_packet(entry_request(readiness_receipt=tampered))

    def test_non_ready_or_hard_gate_incomplete_aag_cannot_build_target_receipt(self):
        bad = ready_aag()
        bad["decision"] = "LIMBO"
        bad["application_ready_no_send"] = False
        with self.assertRaisesRegex(ValueError, "decision is not packet-ready"):
            readiness(aag_receipt=bad)
        for state in (None, False):
            hard = dict(HARD_GATE_EXPECTED)
            hard["employer_scope_verified"] = state
            blocked = evaluate_application(
                dimension_scores={key: 100 for key in DIMENSION_WEIGHTS},
                hard_gate_states=hard,
                risk_scores={key: 0 for key in RISK_COMPONENTS},
                evidence_confidence_score=100,
                human_resonance_score=100,
                desperation_score=0,
                questionnaire_answers={q.question_id: AuditState.PASS.value for q in QUESTION_BANK},
                stakeholder_votes={key: True for key in STAKEHOLDERS},
            )
            with self.assertRaises(ValueError):
                readiness(aag_receipt=blocked)

    def test_portal_is_still_vacancy_specific_and_uses_entry_cv(self):
        assets = entry_assets()
        packet = compile_packet(PacketCompileRequest(
            organization_id="ORG-HOTEL-0001", opportunity_id="OPP-PORTAL-1", lane="PORTAL",
            candidate_fields=ENTRY_FIELDS, assets=assets, channel_id="CHANNEL-PORTAL-1",
            readiness=readiness(
                opportunity_id="OPP-PORTAL-1", lane="PORTAL", channel_id="CHANNEL-PORTAL-1",
                evaluated_assets=assets,
            ),
            candidate_truth_sha256=CANDIDATE_SHA, vacancy_evidence_sha256=VACANCY_SHA,
        ))
        self.assertEqual(packet.selected_asset_manifest_id, "ASSET-CV-ENTRY-V2")

    def test_hybrid_fails_without_portfolio_and_case_study(self):
        assets = (asset("ASSET-CV-HYBRID-V2", "CV_HYBRID", sha="b"),)
        with self.assertRaisesRegex(ValueError, "lane gate blocked"):
            compile_packet(PacketCompileRequest(
                organization_id="ORG-HOTEL-0001", opportunity_id="OPP-HYBRID-1", lane="HYBRID",
                candidate_fields=HYBRID_FIELDS, assets=assets, channel_id="CHANNEL-EMAIL-1",
                readiness=readiness(opportunity_id="OPP-HYBRID-1", lane="HYBRID", evaluated_assets=assets),
                candidate_truth_sha256=CANDIDATE_SHA, vacancy_evidence_sha256=VACANCY_SHA,
            ))

    def test_hybrid_compiles_with_exact_supplements(self):
        packet = compile_packet(hybrid_request())
        self.assertEqual(packet.supplemental_asset_ids, ("ASSET-PORTFOLIO", "ASSET-CASE"))
        supplements = json.loads(packet.supplemental_assets_json)
        self.assertEqual([item["asset_type"] for item in supplements], ["PORTFOLIO", "CASE_STUDY"])
        self.assertTrue(all(item["content_sha256"] for item in supplements))

    def test_deprecated_and_ambiguous_primary_assets_fail_closed(self):
        deprecated = (asset("ASSET-OLD", "CV_ENTRY", state="DEPRECATED"),)
        with self.assertRaises(ValueError):
            compile_packet(entry_request(assets=deprecated))
        ambiguous = (asset("ASSET-A", "CV_ENTRY"), asset("ASSET-B", "CV_ENTRY"))
        with self.assertRaisesRegex(ValueError, "ambiguous approved primary assets"):
            compile_packet(entry_request(assets=ambiguous))

    def test_identity_is_deterministic(self):
        req = entry_request()
        a, b = compile_packet(req), compile_packet(req)
        self.assertEqual((a.idempotency_key, a.application_id, a.packet_id),
                         (b.idempotency_key, b.application_id, b.packet_id))

    def test_asset_revision_requires_revalidation_but_not_new_application_identity(self):
        assets_a = entry_assets(version="v2", sha="a")
        assets_b = entry_assets(version="v3", sha="b")
        a = compile_packet(entry_request(assets=assets_a))
        b = compile_packet(entry_request(assets=assets_b))
        self.assertEqual(a.application_id, b.application_id)
        self.assertNotEqual(a.readiness_binding_sha256, b.readiness_binding_sha256)
        self.assertNotEqual(a.packet_id, b.packet_id)

    def test_aag_refresh_changes_packet_not_application_identity(self):
        assets = entry_assets()
        a = compile_packet(entry_request(
            assets=assets,
            readiness_receipt=readiness(evaluated_assets=assets, aag_receipt=ready_aag(evidence=98)),
        ))
        b = compile_packet(entry_request(
            assets=assets,
            readiness_receipt=readiness(evaluated_assets=assets, aag_receipt=ready_aag(evidence=99)),
        ))
        self.assertEqual(a.application_id, b.application_id)
        self.assertNotEqual(a.readiness_binding_sha256, b.readiness_binding_sha256)
        self.assertNotEqual(a.packet_id, b.packet_id)

    def test_supplemental_revision_requires_revalidation_but_not_new_application_identity(self):
        a = compile_packet(hybrid_request(portfolio_version="v2", portfolio_sha="c"))
        b = compile_packet(hybrid_request(portfolio_version="v3", portfolio_sha="e"))
        self.assertEqual(a.application_id, b.application_id)
        self.assertNotEqual(a.readiness_binding_sha256, b.readiness_binding_sha256)
        self.assertNotEqual(a.packet_id, b.packet_id)
        self.assertNotEqual(a.supplemental_assets_json, b.supplemental_assets_json)

    def test_target_change_changes_application_identity(self):
        a = compile_packet(entry_request())
        b = compile_packet(entry_request(opportunity_id="OPP-2"))
        self.assertNotEqual(a.idempotency_key, b.idempotency_key)

    def test_persist_keeps_stable_application_and_versioned_packet_receipts(self):
        conn = sqlite3.connect(":memory:")
        create_persistence_tables(conn)
        assets = entry_assets()
        first = compile_packet(entry_request(
            assets=assets,
            readiness_receipt=readiness(evaluated_assets=assets, aag_receipt=ready_aag(evidence=98)),
        ))
        second = compile_packet(entry_request(
            assets=assets,
            readiness_receipt=readiness(evaluated_assets=assets, aag_receipt=ready_aag(evidence=99)),
        ))
        self.assertEqual(persist_compiled_packet(conn, first, created_at="2026-09-01T00:00:00Z"), (True, True))
        self.assertEqual(persist_compiled_packet(conn, first, created_at="2026-09-01T00:00:00Z"), (False, False))
        self.assertEqual(persist_compiled_packet(conn, second, created_at="2026-09-01T01:00:00Z"), (False, True))
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM applications_v2").fetchone()[0], 1)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM application_packet_receipts_v1").fetchone()[0], 2)

    def test_persist_allows_supplemental_asset_version_history_without_duplicate_application(self):
        conn = sqlite3.connect(":memory:")
        create_persistence_tables(conn)
        first = compile_packet(hybrid_request(portfolio_version="v2", portfolio_sha="c"))
        second = compile_packet(hybrid_request(portfolio_version="v3", portfolio_sha="e"))
        self.assertEqual(persist_compiled_packet(conn, first, created_at="2026-09-01T02:00:00Z"), (True, True))
        self.assertEqual(persist_compiled_packet(conn, second, created_at="2026-09-01T03:00:00Z"), (False, True))
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM applications_v2").fetchone()[0], 1)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM application_packet_receipts_v1").fetchone()[0], 2)
        supplemental = [json.loads(row[0]) for row in conn.execute(
            "SELECT supplemental_assets_json FROM application_packet_receipts_v1 ORDER BY created_at"
        ).fetchall()]
        self.assertEqual(supplemental[0][0]["version"], "v2")
        self.assertEqual(supplemental[1][0]["version"], "v3")


if __name__ == "__main__":
    unittest.main()
