import unittest

from app.processing.normalize import normalize, similarity


class NormalizeTests(unittest.TestCase):
    def test_dates(self) -> None:
        self.assertEqual(normalize("application_date", "05-10-2026"), "2026-10-05")
        self.assertEqual(normalize("application_date", "5 October 2026"), "2026-10-05")
        self.assertEqual(normalize("application_date", "2026-10-05"), "2026-10-05")
        self.assertIsNone(normalize("application_date", "31-02-2026"))

    def test_money_indian_grouping(self) -> None:
        self.assertEqual(normalize("total_amount", "Rs. 1,33,500.00"), "133500.00")
        self.assertEqual(normalize("total_amount", "₹ 6,500/-"), "6500.00")

    def test_phone_and_ids(self) -> None:
        self.assertEqual(normalize("contact_phone", "+91 98450 12345"), "9845012345")
        self.assertEqual(normalize("institution_id", " 1-4410023451 "), "1-4410023451")
        self.assertEqual(normalize("enrolment_number", "nti-2025-cse-0417"), "NTI-2025-CSE-0417")

    def test_names(self) -> None:
        self.assertEqual(normalize("institution_name", "NORTHGATE INSTITUTE OF TECHNOLOGY"), "Northgate Institute of Technology")

    def test_similarity(self) -> None:
        self.assertEqual(similarity("org", "Northstar Technical Institute", "The Northstar Technical Institute"), 100.0)
        self.assertGreaterEqual(similarity("org", "Northstar Technical Institute", "Northstar Tech Institute Pvt Ltd"), 95)
        self.assertLess(similarity("org", "Northstar Technical Institute", "Northgate Institute of Technology"), 90)
        self.assertEqual(similarity("name", "Rao Ananya", "Ananya Rao"), 100.0)
        self.assertLess(similarity("name", "Rahul Verma", "Ananya Rao"), 50)
