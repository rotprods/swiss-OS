from __future__ import annotations

import unittest

from swiss_os.alias_semantics import identity_key, validate_alias_semantics


class AliasSemanticTests(unittest.TestCase):
    def test_normalization_handles_accents_case_and_punctuation(self) -> None:
        self.assertEqual(identity_key("Hôtel Märthof", "Basel-Stadt"), ("hotel marthof", "basel stadt"))

    def test_valid_exact_alias_is_accepted(self) -> None:
        result = validate_alias_semantics(
            [
                {"hotel_id": "H-0001", "canonical_name": "Hotel Example", "city": "Bern"},
                {"hotel_id": "H-0002", "canonical_name": "Hôtel Example", "city": "Bern"},
            ],
            [{"alias_hotel_id": "H-0001", "canonical_hotel_id": "H-0002"}],
            [
                {
                    "resolution_id": "ER-1",
                    "candidate_name": "Hotel Example",
                    "candidate_city": "Bern",
                    "claimed_alias_hotel_id": "H-0001",
                    "canonical_hotel_id": "H-0002",
                }
            ],
        )
        self.assertTrue(result.valid)
        self.assertEqual(result.state, "EXACT")
        self.assertEqual(result.as_dict()["authority_advanced"], False)
        self.assertEqual(result.as_dict()["h_id_allocations"], 0)
        self.assertEqual(result.as_dict()["outbound_opened"], False)
        self.assertEqual(result.as_dict()["send_allowed"], 0)

    def test_stable_identity_proof_allows_spelling_or_city_variant(self) -> None:
        result = validate_alias_semantics(
            [
                {"hotel_id": "H-0001", "canonical_name": "Example Lodge", "city": "Zürich"},
                {"hotel_id": "H-0002", "canonical_name": "The Example Lodge", "city": "Zurich"},
            ],
            [{"alias_hotel_id": "H-0001", "canonical_hotel_id": "H-0002"}],
            [
                {
                    "candidate_name": "Example Lodge",
                    "candidate_city": "Zürich",
                    "claimed_alias_hotel_id": "H-0001",
                    "canonical_hotel_id": "H-0002",
                    "stable_identity_verified": True,
                }
            ],
        )
        self.assertTrue(result.valid)

    def test_issue_89_four_mismatches_fail_closed(self) -> None:
        cases = [
            ("H-0610", "Hôtel Alpe Fleurie", "Villars-sur-Ollon", "H-0656", "Hotel Murtenhof & Krone", "Murten"),
            ("H-0624", "Hôtel Le Mont Paisible", "Crans-Montana", "H-0639", "Hotel Alpbach", "Meiringen"),
            ("H-0629", "Stiftung Lilienberg Unternehmerforum", "Ermatingen", "H-0638", "Jugendherberge Seelisberg", "Seelisberg"),
            ("H-0630", "Strandhotel Iseltwald", "Iseltwald", "H-0640", "Hotel Central Luzern", "Luzern"),
        ]
        catalog = []
        aliases = []
        resolutions = []
        for index, (alias_id, alias_name, alias_city, target_id, target_name, target_city) in enumerate(cases, start=1):
            catalog.extend(
                [
                    {"hotel_id": alias_id, "canonical_name": alias_name, "city": alias_city},
                    {"hotel_id": target_id, "canonical_name": target_name, "city": target_city},
                ]
            )
            aliases.append({"alias_hotel_id": alias_id, "canonical_hotel_id": target_id})
            resolutions.append(
                {
                    "resolution_id": f"ER-CP0650-00{index}",
                    "candidate_name": target_name,
                    "candidate_city": target_city,
                    "canonical_hotel_id": target_id,
                    "notes": f"{alias_id} superseded; richer {target_id} remains canonical",
                }
            )

        result = validate_alias_semantics(catalog, aliases, resolutions)
        self.assertFalse(result.valid)
        self.assertEqual(result.state, "RECONCILE_REQUIRED")
        self.assertEqual(len(result.violations), 4)
        self.assertEqual({v.code for v in result.violations}, {"ALIAS_IDENTITY_MISMATCH"})
        self.assertEqual(result.as_dict()["authority_advanced"], False)
        self.assertEqual(result.as_dict()["h_id_allocations"], 0)
        self.assertEqual(result.as_dict()["outbound_opened"], False)

    def test_missing_evidence_fails_closed(self) -> None:
        result = validate_alias_semantics(
            [
                {"hotel_id": "H-0001", "canonical_name": "Hotel Example", "city": "Bern"},
                {"hotel_id": "H-0002", "canonical_name": "Hotel Example", "city": "Bern"},
            ],
            [{"alias_hotel_id": "H-0001", "canonical_hotel_id": "H-0002"}],
            [],
        )
        self.assertEqual(result.violations[0].code, "ALIAS_EVIDENCE_MISSING")

    def test_ambiguous_resolution_rows_fail_closed(self) -> None:
        resolution = {
            "candidate_name": "Hotel Example",
            "candidate_city": "Bern",
            "claimed_alias_hotel_id": "H-0001",
            "canonical_hotel_id": "H-0002",
        }
        result = validate_alias_semantics(
            [
                {"hotel_id": "H-0001", "canonical_name": "Hotel Example", "city": "Bern"},
                {"hotel_id": "H-0002", "canonical_name": "Hotel Example", "city": "Bern"},
            ],
            [{"alias_hotel_id": "H-0001", "canonical_hotel_id": "H-0002"}],
            [resolution, dict(resolution)],
        )
        self.assertEqual(result.violations[0].code, "ALIAS_EVIDENCE_AMBIGUOUS")

    def test_candidate_that_identifies_alias_but_not_target_requires_equivalence_proof(self) -> None:
        result = validate_alias_semantics(
            [
                {"hotel_id": "H-0001", "canonical_name": "Hotel A", "city": "Bern"},
                {"hotel_id": "H-0002", "canonical_name": "Hotel B", "city": "Bern"},
            ],
            [{"alias_hotel_id": "H-0001", "canonical_hotel_id": "H-0002"}],
            [
                {
                    "candidate_name": "Hotel A",
                    "candidate_city": "Bern",
                    "claimed_alias_hotel_id": "H-0001",
                    "canonical_hotel_id": "H-0002",
                }
            ],
        )
        self.assertEqual(result.violations[0].code, "REAL_WORLD_EQUIVALENCE_UNPROVEN")

    def test_invalid_and_duplicate_catalog_ids_raise(self) -> None:
        with self.assertRaises(ValueError):
            validate_alias_semantics([{"hotel_id": "bad", "canonical_name": "x", "city": "y"}], [], [])
        with self.assertRaises(ValueError):
            validate_alias_semantics(
                [
                    {"hotel_id": "H-0001", "canonical_name": "x", "city": "y"},
                    {"hotel_id": "H-0001", "canonical_name": "x2", "city": "y2"},
                ],
                [],
                [],
            )


if __name__ == "__main__":
    unittest.main()
