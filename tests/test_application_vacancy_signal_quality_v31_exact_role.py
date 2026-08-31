import unittest

from swiss_os.vacancy_signal_quality import semantic_quality


class VacancyExactRoleV31Tests(unittest.TestCase):
    def quality(self, title, evidence_type="CURRENT_PAGE_HEADING", source_url="https://hotel.example/jobs"):
        route = {"requested_url": "https://hotel.example/jobs", "final_url": "https://hotel.example/jobs"}
        return semantic_quality({"title": title, "source_url": source_url, "evidence_type": evidence_type}, route)

    def test_department_names_are_not_exact_vacancies(self):
        for title in ("Housekeeping", "Küche", "Service", "Front Office", "Marketing"):
            with self.subTest(title=title):
                result = self.quality(title)
                self.assertFalse(result["valid"])
                self.assertIn("GENERIC_DEPARTMENT_NOT_EXACT_ROLE", result["reasons"])

    def test_spontaneous_and_program_buckets_are_not_exact_vacancies(self):
        for title in ("Initiativbewerbung", "Lernende/ Praktikanten", "Interns & Trainees", "Graduate Trainee Programs"):
            with self.subTest(title=title):
                result = self.quality(title, evidence_type="CURRENT_STRUCTURED_JOBPOSTING")
                self.assertFalse(result["valid"])
                self.assertIn("GENERIC_VACANCY_BUCKET_NOT_EXACT_ROLE", result["reasons"])

    def test_descriptive_paragraph_is_not_role_title(self):
        title = "Housekeeping " + ("guest experience and hotel description " * 10)
        result = self.quality(title, evidence_type="CURRENT_PAGE_ROLE_LINK", source_url="https://hotel.example/jobs/housekeeping")
        self.assertFalse(result["valid"])
        self.assertIn("NON_STRUCTURED_TEXT_TOO_LONG_FOR_ROLE_TITLE", result["reasons"])

    def test_exact_housekeeping_job_remains_valid(self):
        result = self.quality("Housekeeping Mitarbeiter/in 60% (a)", evidence_type="CURRENT_STRUCTURED_JOBPOSTING", source_url="https://hotel.example/jobs/housekeeping-mitarbeiter")
        self.assertTrue(result["valid"])


if __name__ == "__main__":
    unittest.main()
