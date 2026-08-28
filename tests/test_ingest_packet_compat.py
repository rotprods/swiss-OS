from __future__ import annotations

import unittest

from swiss_os.ingest_packet import MATCHED_EXISTING, TERMINAL_MATCH


class IngestPacketCompatibilityTests(unittest.TestCase):
    def test_serialized_terminal_state_alias_is_stable(self) -> None:
        self.assertEqual(TERMINAL_MATCH, "MATCHED_EXISTING")
        self.assertEqual(MATCHED_EXISTING, TERMINAL_MATCH)


if __name__ == "__main__":
    unittest.main()
