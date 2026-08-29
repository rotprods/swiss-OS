import subprocess
import unittest
from unittest.mock import patch

from swiss_os.provider_identity_packet_selection import (
    ProviderIdentityPacketSelectionError,
    select_from_git_diff,
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

    @patch("swiss_os.provider_identity_packet_selection.subprocess.run")
    def test_git_diff_selects_packet_from_merge_push(self, run):
        run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout="docs/state/PROVIDER_IDENTITY_WORK_0002_33206402141.json\ntests/test_provider_identity_work_0002_state.py\n",
            stderr="",
        )
        before = "1" * 40
        after = "2" * 40
        self.assertEqual(
            select_from_git_diff(before, after),
            "docs/state/PROVIDER_IDENTITY_WORK_0002_33206402141.json",
        )
        run.assert_called_once_with(
            ["git", "diff", "--name-only", "--diff-filter=AM", before, after, "--", "docs/state"],
            cwd=".", check=True, capture_output=True, text=True, timeout=30,
        )

    @patch("swiss_os.provider_identity_packet_selection.subprocess.run")
    def test_git_diff_zero_or_multiple_packets_fail_closed(self, run):
        for stdout in (
            "STATE.md\n",
            "docs/state/PROVIDER_IDENTITY_WORK_0002_33206402141.json\ndocs/state/PROVIDER_IDENTITY_WORK_0003_33206402141.json\n",
        ):
            run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout=stdout, stderr="")
            with self.subTest(stdout=stdout):
                with self.assertRaises(ProviderIdentityPacketSelectionError):
                    select_from_git_diff("1" * 40, "2" * 40)

    def test_git_diff_rejects_untrusted_sha_arguments_before_subprocess(self):
        for before, after in (("main", "2" * 40), ("1" * 40, "2" * 39 + ";")):
            with self.subTest(before=before, after=after):
                with self.assertRaisesRegex(ProviderIdentityPacketSelectionError, "40-hex"):
                    select_from_git_diff(before, after)


if __name__ == "__main__":
    unittest.main()
