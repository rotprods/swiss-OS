import sqlite3
import tempfile
import unittest

from swiss_os.db import connect, initialize, sqlite_logical_differences


class RestoreEquivalenceTests(unittest.TestCase):
    def _seed_source(self, path: str) -> None:
        conn = connect(path)
        initialize(conn)
        conn.execute(
            "INSERT INTO canonical_hotels(hotel_id, canonical_name, city, state, source_ref) VALUES (?,?,?,?,?)",
            ("H-0001", "Hotel Alpha", "Bern", "ACTIVE", "fixture"),
        )
        conn.commit()
        conn.close()

    def test_backup_is_logically_equivalent(self):
        with tempfile.NamedTemporaryFile(suffix=".sqlite") as source_file, tempfile.NamedTemporaryFile(suffix=".sqlite") as restored_file:
            self._seed_source(source_file.name)
            source = sqlite3.connect(source_file.name)
            restored = sqlite3.connect(restored_file.name)
            source.backup(restored)
            restored.close()
            source.close()

            self.assertEqual(
                sqlite_logical_differences(source_file.name, restored_file.name),
                [],
            )

    def test_content_drift_is_detected_bidirectionally(self):
        with tempfile.NamedTemporaryFile(suffix=".sqlite") as source_file, tempfile.NamedTemporaryFile(suffix=".sqlite") as restored_file:
            self._seed_source(source_file.name)
            source = sqlite3.connect(source_file.name)
            restored = sqlite3.connect(restored_file.name)
            source.backup(restored)
            source.close()

            restored.execute(
                "UPDATE canonical_hotels SET canonical_name='Hotel Mutated' WHERE hotel_id='H-0001'"
            )
            restored.commit()
            restored.close()

            errors = sqlite_logical_differences(source_file.name, restored_file.name)
            self.assertTrue(any("canonical_hotels content differs" in error for error in errors))

    def test_schema_drift_is_detected(self):
        with tempfile.NamedTemporaryFile(suffix=".sqlite") as source_file, tempfile.NamedTemporaryFile(suffix=".sqlite") as restored_file:
            self._seed_source(source_file.name)
            source = sqlite3.connect(source_file.name)
            restored = sqlite3.connect(restored_file.name)
            source.backup(restored)
            source.close()

            restored.execute("CREATE TABLE unexpected_table(id TEXT PRIMARY KEY)")
            restored.commit()
            restored.close()

            errors = sqlite_logical_differences(source_file.name, restored_file.name)
            self.assertIn("schema objects differ", errors)
            self.assertIn("table sets differ", errors)


if __name__ == "__main__":
    unittest.main()
