from __future__ import annotations

import copy
import unittest
from unittest.mock import patch

from swiss_os.provider_identity_enrichment import (
    ProviderIdentityEnrichmentError,
    _ProviderOnlyRedirectHandler,
    enrich_batch,
    extract_identity_candidates,
    validate_packet,
)


HTML = b'''<html><head><script type="application/ld+json">{"@type":"Hotel","name":"Hotel Example","url":"https://hotel.example/","address":{"streetAddress":"Main 1","postalCode":"8000","addressLocality":"Zurich","addressCountry":"CH"}}</script></head><body><a href="https://hotel.example/en">Website</a><a href="https://www.instagram.com/example">IG</a><a href="/internal">Internal</a></body></html>'''


class ProviderIdentityEnrichmentTests(unittest.TestCase):
    def _batch(self):
        return {
            "snapshot_id": "HS-TEST",
            "batch_id": "HS-TEST:PIE:0001",
            "authority_advanced": False,
            "h_id_allocations": 0,
            "outbound": "CLOSED",
            "send_allowed": 0,
            "items": [{
                "source_record_key": "MD-1",
                "name": "Hotel Example",
                "city": "Zurich",
                "detail_url": "https://www.hotelleriesuisse.ch/de/hotel-example",
            }],
        }

    def test_extracts_candidates_without_asserting_identity(self):
        result = extract_identity_candidates(HTML, "https://www.hotelleriesuisse.ch/de/hotel-example")
        self.assertEqual(result["external_link_candidates"][0]["host"], "hotel.example")
        self.assertEqual(result["external_link_candidates"][0]["evidence_role"], "EXTERNAL_LINK_CANDIDATE_ONLY")
        self.assertEqual(result["structured_identity_candidates"][0]["address"]["postalCode"], "8000")
        self.assertNotIn("official_domain", result)

    @patch("swiss_os.provider_identity_enrichment._fetch")
    def test_packet_is_review_only_and_targetless(self, fetch):
        fetch.return_value = (200, "https://www.hotelleriesuisse.ch/de/hotel-example", HTML)
        packet = enrich_batch(self._batch(), delay=0)
        self.assertEqual(validate_packet(packet), ())
        self.assertFalse(packet["identity_decision_allowed"])
        self.assertFalse(packet["terminal_mapping_allowed"])
        self.assertFalse(packet["canonical_id_reservation_allowed"])
        self.assertEqual(packet["h_id_allocations"], 0)
        self.assertEqual(packet["outbound"], "CLOSED")
        self.assertEqual(packet["send_allowed"], 0)
        self.assertNotIn("canonical_hotel_id", packet["results"][0])

    def test_input_target_hid_is_forbidden(self):
        batch = self._batch()
        batch["items"][0]["matched_hotel_id"] = "H-0001"
        with self.assertRaisesRegex(ProviderIdentityEnrichmentError, "target H-ID"):
            enrich_batch(batch, delay=0)

    def test_non_provider_or_http_url_fails_closed(self):
        for url in ("https://example.com/hotel", "http://www.hotelleriesuisse.ch/hotel"):
            batch = self._batch()
            batch["items"][0]["detail_url"] = url
            with self.assertRaisesRegex(ProviderIdentityEnrichmentError, "unsupported provider"):
                enrich_batch(batch, delay=0)

    def test_redirect_cannot_escape_provider_origin(self):
        handler = _ProviderOnlyRedirectHandler()
        with self.assertRaisesRegex(ProviderIdentityEnrichmentError, "escaped trust boundary"):
            handler.redirect_request(None, None, 302, "Found", {}, "https://127.0.0.1/internal")

    @patch("swiss_os.provider_identity_enrichment._fetch")
    def test_hash_or_target_tampering_is_detected(self, fetch):
        fetch.return_value = (200, "https://www.hotelleriesuisse.ch/de/hotel-example", HTML)
        packet = enrich_batch(self._batch(), delay=0)
        tampered = copy.deepcopy(packet)
        tampered["results"][0]["canonical_hotel_id"] = "H-9999"
        violations = validate_packet(tampered)
        self.assertIn("RESULT_TARGET_HID_FORBIDDEN", violations)
        self.assertIn("RESULTS_SHA_MISMATCH", violations)
        self.assertIn("PACKET_SHA_MISMATCH", violations)


if __name__ == "__main__":
    unittest.main()
