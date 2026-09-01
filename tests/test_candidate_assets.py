import unittest

from swiss_os.candidate_assets import AssetManifest, canonical_manifest_hash, sha256_text


class CandidateAssetManifestTests(unittest.TestCase):
    def test_public_receipt_does_not_expose_private_storage_reference(self):
        asset = AssetManifest(
            asset_id="ASSET-CV-ENTRY-002",
            asset_type="CV_ENTRY",
            version="2.0.0",
            state="APPROVED",
            private_storage_ref="Drive:PRIVATE-CV-REF",
            claim_ids=("CF02", "CF03", "CF09", "CF10"),
            content_sha256=sha256_text("fixture"),
        )
        receipt = asset.public_safe_receipt()
        self.assertTrue(asset.approved)
        self.assertNotIn("private_storage_ref", receipt)
        self.assertEqual(receipt["claim_count"], 4)

    def test_invalid_hash_fails(self):
        asset = AssetManifest(
            "ASSET-X", "CV_ENTRY", "2.0.0", "DRAFT", "Drive:PRIVATE", (), "not-a-hash"
        )
        with self.assertRaises(ValueError):
            asset.validate()

    def test_approved_asset_without_hash_fails(self):
        asset = AssetManifest(
            "ASSET-X", "CV_ENTRY", "2.0.0", "APPROVED", "Drive:PRIVATE", (), None
        )
        with self.assertRaisesRegex(ValueError, "approved asset requires content_sha256"):
            asset.validate()

    def test_manifest_hash_is_deterministic(self):
        asset = AssetManifest(
            "ASSET-X", "CV_MASTER", "2.0.0", "QA_PENDING", "Drive:PRIVATE", ("CF01",)
        )
        self.assertEqual(canonical_manifest_hash(asset), canonical_manifest_hash(asset))


if __name__ == "__main__":
    unittest.main()
