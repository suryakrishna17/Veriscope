"""Analytics and macro-compliance metrics service for VeriScope."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..core.db import loads

if TYPE_CHECKING:
    from ..container import Services


def get_analytics_summary(svc: Services) -> dict[str, Any]:
    """Calculate institutional compliance analytics, SLA throughput, and statutory deficiency rankings."""
    # 1. Total and Status Distribution
    status_rows = svc.db.all("SELECT status, COUNT(*) AS count FROM cases GROUP BY status")
    status_counts = {r["status"]: r["count"] for r in status_rows}
    total_cases = sum(status_counts.values())

    active_cases = sum(status_counts.get(s, 0) for s in ("received", "processing", "needs_review", "clarification_requested"))
    decided_cases = sum(status_counts.get(s, 0) for s in ("approved", "rejected"))
    approved_cases = status_counts.get("approved", 0)
    approval_rate = round((approved_cases / decided_cases * 100), 1) if decided_cases > 0 else 0.0

    # 2. Application Types Distribution
    type_rows = svc.db.all("SELECT application_type, COUNT(*) AS count FROM cases GROUP BY application_type")
    type_counts = {r["application_type"]: r["count"] for r in type_rows}

    # 3. Urgency / Triage Averages
    avg_triage = svc.db.scalar("SELECT AVG(triage_priority) FROM cases") or 0.0

    # 4. Top Statutory Non-Compliance Deficiencies (Current Findings)
    deficiency_rows = svc.db.all(
        """SELECT rule_id, summary, category, severity, clause_citation, COUNT(*) AS violation_count
           FROM findings
           WHERE is_current = 1 AND status = 'open'
           GROUP BY rule_id, summary, category, severity, clause_citation
           ORDER BY violation_count DESC, severity ASC
           LIMIT 10"""
    )
    top_deficiencies = [
        {
            "rule_id": r["rule_id"],
            "summary": r["summary"],
            "category": r["category"],
            "severity": r["severity"],
            "clause_citation": r["clause_citation"],
            "count": r["violation_count"],
        }
        for r in deficiency_rows
    ]

    # 5. Global Evaluation Outcome Aggregations
    summary_rows = svc.db.all("SELECT summary_json FROM cases WHERE summary_json IS NOT NULL")
    outcome_totals = {"PASS": 0, "FAIL": 0, "REVIEW_REQUIRED": 0, "NOT_APPLICABLE": 0}
    for row in summary_rows:
        try:
            data = loads(row["summary_json"], {})
            eval_sum = data.get("evaluation_summary")
            if eval_sum:
                outcome_totals["PASS"] += eval_sum.get("pass", 0)
                outcome_totals["FAIL"] += eval_sum.get("fail", 0)
                outcome_totals["REVIEW_REQUIRED"] += eval_sum.get("review_required", 0)
                outcome_totals["NOT_APPLICABLE"] += eval_sum.get("not_applicable", 0)
        except Exception:
            continue

    total_evals = sum(outcome_totals.values())
    pass_rate = round((outcome_totals["PASS"] / total_evals * 100), 1) if total_evals > 0 else 0.0

    # 6. Document Trust & Verification Metrics
    trust_rows = svc.db.all("SELECT trust_label, COUNT(*) AS count FROM documents GROUP BY trust_label")
    trust_counts = {r["trust_label"]: r["count"] for r in trust_rows}

    # Mean OCR Confidence across all extracted pages
    mean_ocr_conf = svc.db.scalar("SELECT AVG(mean_confidence) FROM pages WHERE mean_confidence IS NOT NULL") or 0.0

    # 7. SLA & Turnaround Times (average hours from creation to first decision)
    # SQLite julianday subtraction yields days; multiply by 24 for hours
    avg_tat_hours = svc.db.scalar(
        """SELECT AVG((julianday(d.decided_at) - julianday(c.created_at)) * 24.0)
           FROM decisions d
           JOIN cases c ON c.id = d.case_id"""
    ) or 0.0

    return {
        "overview": {
            "total_cases": total_cases,
            "active_cases": active_cases,
            "decided_cases": decided_cases,
            "approval_rate_percent": approval_rate,
            "automated_pass_rate_percent": pass_rate,
            "mean_urgency_score": round(avg_triage, 1),
            "mean_ocr_confidence": round(mean_ocr_conf, 1),
            "mean_tat_hours": round(avg_tat_hours, 1),
        },
        "status_distribution": status_counts,
        "application_type_distribution": type_counts,
        "outcome_distribution": outcome_totals,
        "trust_distribution": trust_counts,
        "top_deficiencies": top_deficiencies,
    }
