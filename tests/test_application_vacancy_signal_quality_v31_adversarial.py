import unittest

from swiss_os.vacancy_signal_quality import semantic_quality


class VacancySignalQualityV31AdversarialTests(unittest.TestCase):
    def test_job_page_marketing_heading_is_not_a_role(self):
        route = {
            "requested_url": "https://group.example/stellenangebote/jobs-berge",
            "final_url": "https://group.example/stellenangebote/jobs-berge",
        }
        signal = {
            "title": "Internationale Bergdestination:",
            "source_url": "https://group.example/stellenangebote/jobs-berge?category=1952",
            "evidence_type": "CURRENT_PAGE_ROLE_LINK",
        }
        result = semantic_quality(signal, route)
        self.assertFalse(result["valid"])
        self.assertIn("NON_STRUCTURED_TEXT_NOT_ROLE_LIKE", result["reasons"])

    def test_real_nonstructured_role_on_job_page_stays_eligible_semantically(self):
        route = {
            "requested_url": "https://group.example/stellenangebote/jobs-berge",
            "final_url": "https://group.example/stellenangebote/jobs-berge",
        }
        signal = {
            "title": "Mitarbeiter:in Front Office Mountain Hotels",
            "source_url": "https://group.example/stellenangebote/Mitarbeiter-in-Front-Office-Mountain-Hotels_j_2808482",
            "evidence_type": "CURRENT_PAGE_ROLE_LINK",
        }
        result = semantic_quality(signal, route)
        self.assertTrue(result["valid"])
        self.assertTrue(result["role_like_title"])


if __name__ == "__main__":
    unittest.main()
