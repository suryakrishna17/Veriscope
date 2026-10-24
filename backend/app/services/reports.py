"""Case report: the auditable record of inputs, findings, evidence, decision and limitations."""
from __future__ import annotations

import io
from typing import TYPE_CHECKING, Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ..core.db import utcnow
from .cases import case_detail

if TYPE_CHECKING:
    from ..container import Services

VERIFICATION_CAVEAT = (
    "Automated checks assist human review; they do not establish whether a document was issued by its stated issuer. "
    "No document in this case is issuer-verified unless it is explicitly labelled ISSUER_VERIFIED with a recorded issuer response. "
    "Anomaly signals (such as duplicate files or metadata edits) indicate that review is required, not wrongdoing."
)
TRUST_TEXT = {"ISSUER_VERIFIED": "Issuer verified", "ANOMALY_DETECTED": "Review required", "NOT_VERIFIED": "Not verified with issuer"}


def build_report(svc: Services, user: dict[str, Any], case_id: str) -> dict[str, Any]:
    d = case_detail(svc, case_id, user)
    rs = svc.ruleset
    return {
        "generated_at": utcnow(),
        "case": {k: d[k] for k in ("case_ref", "application_type_label", "applicant_ref", "institution_ref", "status", "triage_priority", "created_at", "updated_at")},
        "ruleset": {"name": rs.name, "version": rs.version, "checksum": rs.checksum, "is_provisional": rs.is_provisional, "note": rs.source_note},
        "documents": [
            {"doc_type": x["doc_type"], "original_name": x["original_name"], "sha256": x["sha256"], "pages": x["page_count"],
             "processing_status": x["processing_status"], "trust_label": x["trust_label"], "issuer_check": x["issuer_check"]}
            for x in d["documents"]
        ],
        "fields": [
            {"doc_type": f["doc_type"], "field": f["label"], "value": f["effective_value"], "extracted": f["raw_value"], "corrected": f["corrected_value"] is not None,
             "confidence": f["confidence"], "page": f["page_number"]}
            for f in d["fields"]
        ],
        "findings": [
            {"rule_id": f["rule_id"], "rule_version": f["rule_version"], "severity": f["severity"], "status": f["status"], "category": f["category"],
             "summary": f["summary"], "detail": f["detail"], "evidence": [{"doc_type": e.get("doc_type"), "page": e.get("page"), "excerpt": e.get("excerpt")} for e in f["evidence_refs"]],
             "resolution_note": f["resolution_note"], "resolved_by": f["resolved_by"]}
            for f in d["findings"]
        ],
        "decisions": d["decisions"],
        "summary": d["summary"],
        "verification_caveat": VERIFICATION_CAVEAT,
        "limitations": [
            "Rules come from a prototype rulebook and are not official AICTE policy.",
            "OCR can misread values; extracted values carry a confidence score and were open to reviewer correction.",
            "Signature, seal and letterhead detection are visual heuristics that report presence only.",
        ],
    }


def render_pdf(report: dict[str, Any]) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm,
                            title=f"Case report {report['case']['case_ref']}", author="VeriScope")
    ss = getSampleStyleSheet()
    ink = colors.HexColor("#1B2A3A")
    h1 = ParagraphStyle("h1", parent=ss["Heading1"], fontName="Helvetica-Bold", fontSize=17, textColor=ink, spaceAfter=4)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=11.5, textColor=ink, spaceBefore=10, spaceAfter=4)
    body = ParagraphStyle("b", parent=ss["BodyText"], fontName="Helvetica", fontSize=8.8, leading=11.5, textColor=ink)
    small = ParagraphStyle("s", parent=body, fontSize=7.8, leading=10, textColor=colors.HexColor("#4A5A6A"))
    P = lambda t, s=body: Paragraph(escape(str(t if t is not None else "—")), s)  # noqa: E731

    def table(rows: list[list[Any]], widths: list[float]) -> Table:
        t = Table(rows, colWidths=widths, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E3E9EF")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C5CFD8")),
            ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        return t

    c = report["case"]
    story: list[Any] = [
        Paragraph(escape(f"Case report {c['case_ref']}"), h1),
        P(f"{c['application_type_label']} · Applicant: {c['applicant_ref']} · Institution: {c['institution_ref']}"),
        P(f"Status: {c['status'].replace('_', ' ')} · Generated {report['generated_at']} · Ruleset {report['ruleset']['name']} v{report['ruleset']['version']}"
          + (" (provisional)" if report["ruleset"]["is_provisional"] else ""), small),
        Spacer(1, 4),
        Paragraph(escape(report["verification_caveat"]), ParagraphStyle("cv", parent=body, backColor=colors.HexColor("#FFF6E5"), borderPadding=6, borderColor=colors.HexColor("#E8C27A"), borderWidth=0.6)),
        Spacer(1, 6),
    ]
    if report.get("summary"):
        story += [Paragraph("Summary", h2), P(report["summary"].get("text"))]

    story.append(Paragraph("Documents", h2))
    rows = [[P("Type", small), P("File", small), P("SHA-256", small), P("Issuer check", small)]]
    for d in report["documents"]:
        rows.append([P(d["doc_type"].replace("_", " ").title(), small), P(d["original_name"], small), P(d["sha256"][:24] + "…", small), P(TRUST_TEXT.get(d["trust_label"], d["trust_label"]), small)])
    story.append(table(rows, [40 * mm, 45 * mm, 50 * mm, 39 * mm]))

    story.append(Paragraph("Findings", h2))
    if not report["findings"]:
        story.append(P("No findings were raised."))
    else:
        rows = [[P("Rule", small), P("Severity / status", small), P("Finding and evidence", small), P("Resolution", small)]]
        for f in report["findings"]:
            ev = "; ".join(f"{(e.get('doc_type') or '').replace('_', ' ').lower()} p.{e.get('page') or '–'}: {e.get('excerpt') or ''}"[:140] for e in f["evidence"]) or "No source evidence"
            rows.append([P(f"{f['rule_id']} v{f['rule_version']}", small), P(f"{f['severity']} / {f['status']}", small),
                         Paragraph(f"<b>{escape(f['summary'])}</b><br/>{escape(f['detail'])}<br/><font color='#5B6B7B'>Evidence: {escape(ev)}</font>", small),
                         P(f"{f['resolution_note'] or ''} {('— ' + f['resolved_by']) if f['resolved_by'] else ''}".strip() or "—", small)])
        story.append(table(rows, [22 * mm, 24 * mm, 88 * mm, 40 * mm]))

    if report["fields"]:
        story.append(Paragraph("Extracted values", h2))
        rows = [[P("Document", small), P("Field", small), P("Value", small), P("Conf.", small), P("Page", small)]]
        for f in report["fields"]:
            rows.append([P(f["doc_type"].replace("_", " ").title(), small), P(f["field"] + (" (corrected)" if f["corrected"] else ""), small),
                         P(f["value"], small), P(f"{f['confidence']:.2f}", small), P(f["page"], small)])
        story.append(table(rows, [44 * mm, 44 * mm, 58 * mm, 14 * mm, 14 * mm]))

    story.append(Paragraph("Human decision", h2))
    if report["decisions"]:
        for dcs in report["decisions"]:
            story.append(P(f"{dcs['decided_at']}: {dcs['outcome'].replace('_', ' ')} ({dcs['reason_code']}) by {dcs['reviewer']}. {dcs['note'] or ''}"))
    else:
        story.append(P("No decision recorded yet."))

    story.append(Paragraph("Limitations", h2))
    for lim in report["limitations"]:
        story.append(P("• " + lim, small))
    story.append(P(f"Ruleset checksum {report['ruleset']['checksum'][:16]}… · {report['ruleset']['note']}", small))
    doc.build(story)
    return buf.getvalue()
