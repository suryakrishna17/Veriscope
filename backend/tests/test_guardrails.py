"""Trust-language, AI guardrail and prompt-injection tests."""
import json
import re
import unittest
from pathlib import Path

from app.ai.adapter import MockLLM, guard, template_summary
from tests.helpers import AppTestCase

ROOT = Path(__file__).resolve().parents[2]
VERDICT_WORDS = re.compile(r"\b(forged|forgery|fake|fraud|fraudulent|genuine)\b", re.I)
FINDINGS = [{"rule_id": "CON-001", "severity": "medium", "status": "open", "category": "consistency", "summary": "Institution name differs", "detail": "x"}]


class TrustLanguageTests(unittest.TestCase):
    def test_user_facing_text_has_no_verdict_words(self) -> None:
        targets = list((ROOT / "frontend" / "src").rglob("*.ts*")) + [
            ROOT / "backend/app/rules/rulesets/student_support_lite.v1.yaml",
            ROOT / "backend/app/services/reports.py",
            ROOT / "backend/app/services/cases.py",
            ROOT / "backend/app/rules/operators.py",
        ]
        offenders = [f"{p.name}: {m.group(0)}" for p in targets if p.exists() for m in VERDICT_WORDS.finditer(p.read_text())]
        self.assertEqual(offenders, [])


class AiGuardTests(unittest.TestCase):
    def test_valid_output_accepted(self) -> None:
        out = guard(json.dumps({"summary": "One mismatch [CON-001].", "missing_evidence": [], "cited_rule_ids": ["CON-001"]}), FINDINGS, "t")
        self.assertIsNotNone(out)

    def test_rejects_non_json_hallucinated_citations_and_verdicts(self) -> None:
        self.assertIsNone(guard("sure! here you go", FINDINGS, "t"))
        self.assertIsNone(guard(json.dumps({"summary": "See [XYZ-999]."}), FINDINGS, "t"))
        self.assertIsNone(guard(json.dumps({"summary": "This letter is fake."}), FINDINGS, "t"))
        self.assertIsNone(guard(json.dumps({"summary": "You should approve this case."}), FINDINGS, "t"))

    def test_template_always_available(self) -> None:
        s = template_summary("C-1", FINDINGS)
        self.assertEqual(s.kind, "template")
        self.assertIn("not issuer-verified", s.text)
        self.assertEqual(MockLLM().summarize("C-1", FINDINGS).kind, "llm")


class PromptInjectionTests(AppTestCase):
    def test_injected_text_has_no_effect(self) -> None:
        cid = self.upload_fixture_case("SIH-DEMO-015")
        self.process(cid)
        d = self.detail(cid)
        self.assertEqual(d["status"], "needs_review")  # never auto-approved
        self.assertEqual(sorted({f["rule_id"] for f in d["findings"]}), ["DAT-002", "SIG-003"])
        self.assertNotIn("IGNORE", d["summary"]["text"].upper())
        self.assertEqual(d["decisions"], [])
