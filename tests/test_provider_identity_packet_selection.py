import unittest

from swiss_os.provider_identity_packet_selection import (
    ProviderIdentityPacketSelectionError,
    select_push_packet,
    validate_packet_path,
)


class ProviderIdentityPacketSelectionTests(unittest.TestCase):
    def test_selects_exactly_one_changed_provider_packet(self):
        event = {"commits": [{"added": ["docs/state/PROVIDER_IDENTITY_WORK_0002_33206402141.json"], "modified": ["STATE.md"]}]}
        self.assertEqual(select_push_packet(event), "docs/state/PROVIDER_IDENTITY_WORK_0002_33206402141.json")

    def test_multiple_packets_fail_closed(self):
        event = {"commits": [{"added": [
            "docs/state/PROVIDER_IDENTITY_WORK_0002_33206402141.json",
            "docs/state/PROVIDER_IDENTITY_WORK_0003_33206402141.json",
        ]}]}
        with self.assertRaisesRegex(ProviderIdentityPacketSelectionError, "exactly one"):
            select_push_packet(event)

    def test_no_packet_fails_closed(self):
        with self.assertRaisesRegex(ProviderIdentityPacketSelectionError, "found 0"):
            select_push_packet({"commits": [{"modified": ["STATE.md"]}]})

    def test_removed_or_unrelated_files_do_not_select(self):
        event = {"commits": [{"removed": ["docs/state/PROVIDER_IDENTITY_WORK_0001_33206402141.json"], "added": ["docs/state/other.json"]}]}
        with self.assertRaises(ProviderIdentityPacketSelectionError):
            select_push_packet(event)

    def test_path_traversal_and_wrong_prefix_rejected(self):
        for path in ("../docs/state/PROVIDER_IDENTITY_WORK_0002.json", "/docs/state/PROVIDER_IDENTITY_WORK_0002.json", "docs/state/NEXT.json"):
            with self.subTest(path=path):
                with self.assertRaises(ProviderIdentityPacketSelectionError):
                    validate_packet_path(path)


if __name__ == "__main__":
    unittest.main()
