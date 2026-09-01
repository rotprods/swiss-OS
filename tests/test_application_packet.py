import sqlite3
import unittest

from swiss_os.application_packet import PacketCompileRequest, compile_packet, persist_application
from swiss_os.candidate_assets import AssetManifest
from swiss_os.candidate_truth import CandidateField


def field(key: str) -> CandidateField:
    return CandidateField(key=key, truth_state="VERIFIED", approved=True, external_allowed=True)


def asset(asset_id: str, asset_type: str, state: str = "APPROVED") -> AssetManifest:
    return AssetManifest(
        asset_id=asset_id,
        asset_type=asset_type,
        version="v2",
        state=state,
        private_storage_ref=f"private://{asset_id}",
        claim_ids=("CLAIM-1",),
        content_sha256="a" * 64,
    )


ENTRY_FIELDS = (
    field("contact.email"),
    field("contact.phone"),
    field("language.wording"),
    field("availability.start"),
)

HYBRID_FIELDS = ENTRY_FIELDS + (field("social.linkedin"),)


class ApplicationPacketTests(unittest.TestCase):
    def test_entry_compiles_with_approved_entry_cv_only(self):
        req = PacketCompileRequest(
            organization_id="ORG-HOTEL-0001",
            opportunity_id="OPP-1",
            lane="ENTRY",
            candidate_fields=ENTRY_FIELDS,
            assets=(asset("ASSET-CV-ENTRY-V2", "CV_ENTRY"),),
            channel_id="CHANNEL-EMAIL-1",
        )
        packet = compile_packet(req)
        self.assertTrue(packet.gate.ready)
        self.assertEqual(packet.selected_asset_manifest_id, "ASSET-CV-ENTRY-V2")
        self.assertEqual(packet.supplemental_asset_ids, ())

    def test_portal_uses_entry_cv(self):
        packet = compile_packet(PacketCompileRequest(
            organization_id="ORG-HOTEL-0001",
            lane="PORTAL",
            candidate_fields=ENTRY_FIELDS,
            assets=(asset("ASSET-CV-ENTRY-V2", "CV_ENTRY"),),
            channel_id="CHANNEL-PORTAL-1",
        ))
        self.assertEqual(packet.selected_asset_manifest_id, "ASSET-CV-ENTRY-V2")

    def test_hybrid_fails_without_portfolio_and_case_study(self):
        req = PacketCompileRequest(
            organization_id="ORG-HOTEL-0001",
            lane="HYBRID",
            candidate_fields=HYBRID_FIELDS,
            assets=(asset("ASSET-CV-HYBRID-V2", "CV_HYBRID"),),
            channel_id="CHANNEL-EMAIL-1",
        )
        with self.assertRaisesRegex(ValueError, "lane gate blocked"):
            compile_packet(req)

    def test_hybrid_compiles_with_exact_supplements(self):
        req = PacketCompileRequest(
            organization_id="ORG-HOTEL-0001",
            lane="HYBRID",
            candidate_fields=HYBRID_FIELDS,
            assets=(
                asset("ASSET-CV-HYBRID-V2", "CV_HYBRID"),
                asset("ASSET-PORTFOLIO-V2", "PORTFOLIO"),
                asset("ASSET-CASE-V2", "CASE_STUDY"),
            ),
            channel_id="CHANNEL-EMAIL-1",
        )
        packet = compile_packet(req)
        self.assertEqual(packet.supplemental_asset_ids, ("ASSET-PORTFOLIO-V2", "ASSET-CASE-V2"))

    def test_deprecated_asset_cannot_satisfy_gate(self):
        req = PacketCompileRequest(
            organization_id="ORG-HOTEL-0001",
            lane="ENTRY",
            candidate_fields=ENTRY_FIELDS,
            assets=(asset("ASSET-OLD", "CV_ENTRY", state="DEPRECATED"),),
            channel_id="CHANNEL-EMAIL-1",
        )
        with self.assertRaises(ValueError):
            compile_packet(req)

    def test_ambiguous_approved_primary_assets_fail_closed(self):
        req = PacketCompileRequest(
            organization_id="ORG-HOTEL-0001",
            lane="ENTRY",
            candidate_fields=ENTRY_FIELDS,
            assets=(asset("ASSET-A", "CV_ENTRY"), asset("ASSET-B", "CV_ENTRY")),
            channel_id="CHANNEL-EMAIL-1",
        )
        with self.assertRaisesRegex(ValueError, "ambiguous approved primary assets"):
            compile_packet(req)

    def test_identity_is_deterministic(self):
        req = PacketCompileRequest(
            organization_id="ORG-HOTEL-0001",
            opportunity_id="OPP-1",
            lane="ENTRY",
            candidate_fields=ENTRY_FIELDS,
            assets=(asset("ASSET-CV-ENTRY-V2", "CV_ENTRY"),),
            channel_id="CHANNEL-EMAIL-1",
        )
        a = compile_packet(req)
        b = compile_packet(req)
        self.assertEqual(a.idempotency_key, b.idempotency_key)
        self.assertEqual(a.application_id, b.application_id)

    def test_persist_is_idempotent_and_metadata_only(self):
        conn = sqlite3.connect(":memory:")
        conn.execute("""CREATE TABLE applications_v2(
            application_id TEXT PRIMARY KEY,
            opportunity_id TEXT,
            organization_id TEXT NOT NULL,
            lane TEXT NOT NULL,
            state TEXT NOT NULL,
            selected_asset_manifest_id TEXT,
            selected_channel_id TEXT,
            idempotency_key TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        )""")
        packet = compile_packet(PacketCompileRequest(
            organization_id="ORG-HOTEL-0001",
            lane="ENTRY",
            candidate_fields=ENTRY_FIELDS,
            assets=(asset("ASSET-CV-ENTRY-V2", "CV_ENTRY"),),
            channel_id="CHANNEL-EMAIL-1",
        ))
        self.assertTrue(persist_application(conn, packet, created_at="2026-09-01T00:00:00Z"))
        self.assertFalse(persist_application(conn, packet, created_at="2026-09-01T00:00:00Z"))
        row = conn.execute("SELECT state, selected_asset_manifest_id FROM applications_v2").fetchone()
        self.assertEqual(row, ("PACKET_COMPILED", "ASSET-CV-ENTRY-V2"))


if __name__ == "__main__":
    unittest.main()
