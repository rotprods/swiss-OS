from __future__ import annotations

import io
from contextlib import redirect_stdout
import unittest

from swiss_os.unified_cli import UnifiedCLIError, dispatch


class UnifiedCLITests(unittest.TestCase):
    def test_help_is_available_without_side_effects(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            code = dispatch([])
        self.assertEqual(code, 0)
        self.assertIn("meta-run", output.getvalue())
        self.assertIn("member-directory", output.getvalue())
        self.assertIn("directory-export", output.getvalue())

    def test_legacy_command_is_forwarded_unchanged(self) -> None:
        seen: list[list[str] | None] = []

        def legacy(argv: list[str] | None) -> int:
            seen.append(argv)
            return 7

        code = dispatch(["db", "check", "state.sqlite"], legacy_main=legacy)
        self.assertEqual(code, 7)
        self.assertEqual(seen, [["db", "check", "state.sqlite"]])

    def test_meta_command_strips_router_prefix(self) -> None:
        seen: list[list[str] | None] = []

        def meta(argv: list[str] | None) -> int:
            seen.append(argv)
            return 0

        code = dispatch(["meta-run", "validate-next", "NEXT.json"], meta_main=meta)
        self.assertEqual(code, 0)
        self.assertEqual(seen, [["validate-next", "NEXT.json"]])

    def test_member_capture_routes_to_member_router(self) -> None:
        seen: list[list[str]] = []

        def member(argv: list[str]) -> int:
            seen.append(argv)
            return 0

        code = dispatch(
            ["member-directory", "capture", "--root-url", "https://example.test"],
            member_main=member,
        )
        self.assertEqual(code, 0)
        self.assertEqual(
            seen,
            [["capture", "--root-url", "https://example.test"]],
        )

    def test_staging_and_export_routes(self) -> None:
        staging_seen: list[list[str] | None] = []
        export_seen: list[list[str] | None] = []

        code = dispatch(
            ["staging-evidence", "extract-workbook", "crm.xlsx"],
            staging_main=lambda argv: staging_seen.append(argv) or 0,
        )
        self.assertEqual(code, 0)
        self.assertEqual(staging_seen, [["extract-workbook", "crm.xlsx"]])

        code = dispatch(
            ["directory-export", "manifest.json"],
            export_main=lambda argv: export_seen.append(argv) or 0,
        )
        self.assertEqual(code, 0)
        self.assertEqual(export_seen, [["manifest.json"]])

    def test_unknown_command_fails_closed(self) -> None:
        with self.assertRaisesRegex(UnifiedCLIError, "unknown"):
            dispatch(["outbound-open"])


if __name__ == "__main__":
    unittest.main()
