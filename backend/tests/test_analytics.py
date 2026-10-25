"""Tests for the /api/v1/analytics endpoint and macro metrics calculations."""
from tests.helpers import AppTestCase


class AnalyticsApiTests(AppTestCase):
    def test_analytics_auth_required(self) -> None:
        # Anonymous fails with 401
        r = self.client.get("/api/v1/analytics")
        self.assertEqual(r.status_code, 401)

        # Applicant role fails with 403 (role-restricted)
        r = self.client.get("/api/v1/analytics", headers=self.h("applicant"))
        self.assertEqual(r.status_code, 403)

    def test_analytics_reviewer_and_admin_access(self) -> None:
        # Reviewer can access
        r = self.client.get("/api/v1/analytics", headers=self.h("reviewer"))
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertIn("overview", data)
        self.assertIn("status_distribution", data)
        self.assertIn("application_type_distribution", data)
        self.assertIn("outcome_distribution", data)
        self.assertIn("trust_distribution", data)
        self.assertIn("top_deficiencies", data)

        # Admin can access
        r = self.client.get("/api/v1/analytics", headers=self.h("admin"))
        self.assertEqual(r.status_code, 200)

    def test_analytics_aggregates_cases(self) -> None:
        # Create an AICTE_EOA case
        res = self.client.post(
            "/api/v1/cases",
            json={
                "application_type": "AICTE_EOA",
                "applicant_ref": "Registrar Dr. Raman",
                "institution_ref": "Northstar Technical Institute",
            },
            headers=self.h("reviewer"),
        )
        self.assertEqual(res.status_code, 201)
        case = res.get_json()
        self.assertIsNotNone(case["id"])

        r = self.client.get("/api/v1/analytics", headers=self.h("reviewer"))
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertGreaterEqual(data["overview"]["total_cases"], 1)
        self.assertIn("AICTE_EOA", data["application_type_distribution"])
