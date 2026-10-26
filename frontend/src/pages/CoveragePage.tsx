import { useState } from "react";
import { Layout } from "../components/Layout";
import { SeverityTag } from "../components/Badges";

interface RuleItem {
  id: string;
  category: string;
  severity: "high" | "medium" | "low" | "info";
  citation: string;
  summary: string;
  docTypes: string[];
  status: "VERIFIED_OFFICIAL" | "ILLUSTRATIVE";
  sourcePage: string;
}

const RULES: RuleItem[] = [
  {
    id: "EOA-CMP-001",
    category: "Completeness",
    severity: "high",
    citation: "AICTE APH 2024-27 Chapter II, Clause 2.4 & Clause 2.5, Annexure-2",
    summary: "Mandatory university affiliation order must be submitted for the current academic session",
    docTypes: ["UNIVERSITY_AFFILIATION_ORDER"],
    status: "VERIFIED_OFFICIAL",
    sourcePage: "Chapter II, pp. 24-28",
  },
  {
    id: "EOA-CMP-002",
    category: "Completeness",
    severity: "high",
    citation: "AICTE APH 2024-27 Chapter II, Clause 2.5, Clause 2.6, Annexure-2",
    summary: "Fire Safety Clearance Certificate (NOC) must be submitted by competent state authority",
    docTypes: ["FIRE_SAFETY_CERTIFICATE"],
    status: "VERIFIED_OFFICIAL",
    sourcePage: "Chapter II, pp. 25-29",
  },
  {
    id: "EOA-CMP-003",
    category: "Completeness",
    severity: "high",
    citation: "AICTE APH 2024-27 Chapter II, Clause 2.3 & Clause 2.5, Annexure-2",
    summary: "Structural Stability Certificate must be provided by competent chartered engineer",
    docTypes: ["BUILDING_SAFETY_CERTIFICATE"],
    status: "VERIFIED_OFFICIAL",
    sourcePage: "Chapter II, pp. 23-28",
  },
  {
    id: "EOA-CMP-004",
    category: "Completeness",
    severity: "medium",
    citation: "AICTE APH 2024-27 Chapter II, Clause 2.5, Annexure-2",
    summary: "Municipal completion or occupancy certificate must be provided",
    docTypes: ["OCCUPANCY_CERTIFICATE"],
    status: "VERIFIED_OFFICIAL",
    sourcePage: "Chapter II, pp. 25-28",
  },
  {
    id: "EOA-CMP-005",
    category: "Completeness",
    severity: "high",
    citation: "AICTE APH 2024-27 Chapter II, Clause 2.5, Annexure-2, Appendix 6",
    summary: "Certified land document confirming ownership, continuous possession, or registered lease",
    docTypes: ["LAND_DOCUMENT_AND_USE_CERTIFICATE"],
    status: "VERIFIED_OFFICIAL",
    sourcePage: "Chapter II, p. 27 & Appendix 6",
  },
  {
    id: "EOA-CMP-006",
    category: "Completeness",
    severity: "high",
    citation: "AICTE APH 2024-27 Chapter II, Clause 2.5, Annexure-2, Appendix 6",
    summary: "Complete Extension of Approval Application Form signed by Head of Institution",
    docTypes: ["EOA_APPLICATION_FORM"],
    status: "VERIFIED_OFFICIAL",
    sourcePage: "Chapter II, p. 27 & Appendix 6",
  },
  {
    id: "EOA-FMT-001",
    category: "Format & Identity",
    severity: "medium",
    citation: "AICTE APH 2024-27 Chapter II, Clause 2.3",
    summary: "AICTE Permanent Institute ID must conform to standard hyphenated 10-digit format (1-XXXXXXXXXX)",
    docTypes: ["EOA_APPLICATION_FORM"],
    status: "VERIFIED_OFFICIAL",
    sourcePage: "Chapter II, p. 23",
  },
  {
    id: "EOA-FMT-002",
    category: "Format & Identity",
    severity: "medium",
    citation: "AICTE APH 2024-27 Chapter II, Clause 2.2 & Clause 2.3",
    summary: "Academic session on the application form must match the current regulatory review cycle",
    docTypes: ["EOA_APPLICATION_FORM"],
    status: "VERIFIED_OFFICIAL",
    sourcePage: "Chapter II, pp. 22-23",
  },
  {
    id: "EOA-DAT-001",
    category: "Dates & Chronology",
    severity: "low",
    citation: "AICTE APH 2024-27 Chapter II, Clause 2.2 & Clause 2.3",
    summary: "Application submission date must fall within announced AICTE annual notification calendar",
    docTypes: ["EOA_APPLICATION_FORM"],
    status: "VERIFIED_OFFICIAL",
    sourcePage: "Chapter II, pp. 22-23",
  },
  {
    id: "EOA-DAT-002",
    category: "Dates & Chronology",
    severity: "high",
    citation: "AICTE APH 2024-27 Chapter II, Clause 2.5, Annexure-2, Appendix 6",
    summary: "Fire Safety Certificate validity must extend through or beyond the academic year",
    docTypes: ["FIRE_SAFETY_CERTIFICATE"],
    status: "VERIFIED_OFFICIAL",
    sourcePage: "Chapter II, p. 27 & Appendix 6",
  },
  {
    id: "EOA-DAT-003",
    category: "Dates & Chronology",
    severity: "medium",
    citation: "AICTE APH 2024-27 Chapter II, Clause 2.5, Annexure-2, Appendix 6",
    summary: "Structural engineer fitness certification must be active for the operational cycle",
    docTypes: ["BUILDING_SAFETY_CERTIFICATE"],
    status: "VERIFIED_OFFICIAL",
    sourcePage: "Chapter II, p. 27 & Appendix 6",
  },
  {
    id: "EOA-COM-001",
    category: "Statutory Committees",
    severity: "high",
    citation: "AICTE (Prevention & Prohibition of Ragging) Reg. 2009; APH Ch. II Clause 2.5",
    summary: "Anti-Ragging Committee constituted per regulations with diverse stakeholder representation",
    docTypes: ["EOA_APPLICATION_FORM"],
    status: "VERIFIED_OFFICIAL",
    sourcePage: "Annexure-2 & Appendix 6, p. 73",
  },
  {
    id: "EOA-COM-002",
    category: "Statutory Committees",
    severity: "high",
    citation: "AICTE (Prevention & Prohibition of Ragging) Reg. 2009; APH Ch. II Clause 2.5",
    summary: "Anti-Ragging Squad constituted with round-the-clock hostel and campus inspection capability",
    docTypes: ["EOA_APPLICATION_FORM"],
    status: "VERIFIED_OFFICIAL",
    sourcePage: "Annexure-2 & Appendix 6, p. 74",
  },
  {
    id: "EOA-COM-003",
    category: "Statutory Committees",
    severity: "high",
    citation: "PoSH Act 2013; AICTE Gender Sensitization Regulations 2016; APH Ch. II Clause 2.5",
    summary: "Internal Complaints Committee (ICC) constituted for prevention of sexual harassment",
    docTypes: ["EOA_APPLICATION_FORM"],
    status: "VERIFIED_OFFICIAL",
    sourcePage: "Annexure-2 & Appendix 6, p. 75",
  },
  {
    id: "EOA-COM-004",
    category: "Statutory Committees",
    severity: "high",
    citation: "AICTE (Redressal of Grievance of Students) Reg. 2019; APH Ch. II Clause 2.5",
    summary: "Student Grievance Redressal Committee (SGRC) constituted per AICTE norms",
    docTypes: ["EOA_APPLICATION_FORM"],
    status: "VERIFIED_OFFICIAL",
    sourcePage: "Annexure-2 & Appendix 6, p. 76",
  },
  {
    id: "EOA-COM-005",
    category: "Statutory Committees",
    severity: "medium",
    citation: "SC/ST (Prevention of Atrocities) Act 1989; APH Ch. II Clause 2.5",
    summary: "Committee for SC/ST constituted for safeguarding rights of marginalized scholars",
    docTypes: ["EOA_APPLICATION_FORM"],
    status: "VERIFIED_OFFICIAL",
    sourcePage: "Annexure-2 & Appendix 6, p. 77",
  },
  {
    id: "EOA-COM-006",
    category: "Statutory Committees",
    severity: "medium",
    citation: "AICTE APH 2024-27 Chapter II, Clause 2.5, Annexure-2, Appendix 6",
    summary: "Internal Quality Assurance Cell (IQAC) established per national accreditation benchmarks",
    docTypes: ["EOA_APPLICATION_FORM"],
    status: "VERIFIED_OFFICIAL",
    sourcePage: "Annexure-2 & Appendix 6, p. 78",
  },
  {
    id: "EOA-INF-001",
    category: "Infrastructure & Norms",
    severity: "high",
    citation: "Rights of Persons with Disabilities Act 2016; APH Ch. II Clause 2.5, Appendix 6",
    summary: "Barrier-free environment: accessible ramps, adapted restrooms, and tactile braille lifts",
    docTypes: ["EOA_APPLICATION_FORM"],
    status: "VERIFIED_OFFICIAL",
    sourcePage: "Appendix 6, p. 81",
  },
  {
    id: "EOA-INF-002",
    category: "Infrastructure & Norms",
    severity: "medium",
    citation: "AICTE APH 2024-27 Chapter II, Clause 2.13 and Annexure-2",
    summary: "Institutional mandatory public disclosure link active and accessible on web portal",
    docTypes: ["EOA_APPLICATION_FORM"],
    status: "VERIFIED_OFFICIAL",
    sourcePage: "Chapter II, p. 33 & Annexure-2",
  },
  {
    id: "EOA-INF-003",
    category: "Infrastructure & Norms",
    severity: "high",
    citation: "AICTE APH 2024-27 Chapter II, Clause 2.3, Clause 2.5, Affidavit-2",
    summary: "Affidavit-2 submitted declaring statutory compliance and absence of legal encumbrances",
    docTypes: ["EOA_APPLICATION_FORM"],
    status: "VERIFIED_OFFICIAL",
    sourcePage: "Chapter II, p. 24 & Affidavit-2",
  },
  {
    id: "EOA-CON-001",
    category: "Consistency",
    severity: "medium",
    citation: "AICTE APH 2024-27 Chapter II, Clause 2.4, Clause 2.5, Annexure-2",
    summary: "Institution name in Affiliation Order matches Application Form within 85% fuzzy threshold",
    docTypes: ["EOA_APPLICATION_FORM", "UNIVERSITY_AFFILIATION_ORDER"],
    status: "VERIFIED_OFFICIAL",
    sourcePage: "Chapter II, pp. 25-28",
  },
  {
    id: "EOA-CON-002",
    category: "Consistency",
    severity: "medium",
    citation: "AICTE APH 2024-27 Chapter II, Clause 2.5 and Annexure-2",
    summary: "Academic session in University Affiliation Order matches current EoA application session",
    docTypes: ["EOA_APPLICATION_FORM", "UNIVERSITY_AFFILIATION_ORDER"],
    status: "VERIFIED_OFFICIAL",
    sourcePage: "Chapter II, p. 26",
  },
  {
    id: "EOA-SIG-001",
    category: "Document Signals",
    severity: "medium",
    citation: "AICTE APH 2024-27 Chapter II, Clause 2.3 & Chapter VII",
    summary: "Identical document SHA-256 hash submitted across multiple cases triggers cross-check",
    docTypes: ["ALL"],
    status: "VERIFIED_OFFICIAL",
    sourcePage: "Chapter II, p. 23 & Chapter VII",
  },
  {
    id: "EOA-SIG-002",
    category: "Document Signals",
    severity: "low",
    citation: "AICTE APH 2024-27 Chapter II, Clause 2.3 and Annexure-2",
    summary: "PDF metadata post-issuance modifications flagged for visual comparison with original copy",
    docTypes: ["ALL"],
    status: "VERIFIED_OFFICIAL",
    sourcePage: "Chapter II, p. 23 & Annexure-2",
  },
  {
    id: "EOA-SIG-003",
    category: "Document Signals",
    severity: "high",
    citation: "AICTE APH 2024-27 Advisory — Document Integrity Guideline",
    summary: "Hidden, zero-contrast, or invisible vector text detected in document streams",
    docTypes: ["ALL"],
    status: "ILLUSTRATIVE",
    sourcePage: "Advisory Signal / Experimental Heuristic",
  },
];

const NON_AUTOMATED_NORMS = [
  {
    clause: "Clause 2.14 & Chapter VII",
    title: "Surprise Inspection Committee (SIC) Physical Visit",
    reason: "Requires in-person physical laboratory verification, equipment stock checking, and library physical volume counts by appointed AICTE expert committee.",
  },
  {
    clause: "Clause 1.4.1 & Appendix 4",
    title: "Original Land Registry Physical Deed Scrutiny",
    reason: "Requires physical inspection of wet-ink stamped original title deeds and encumbrance certificates at the District Sub-Registrar registry.",
  },
  {
    clause: "Clause 2.15",
    title: "Faculty Biometric Attendance & Salary Bank Transfer",
    reason: "Requires integration with national bank payment gateways and physical biometric hardware at institutional premises.",
  },
  {
    clause: "Clause 7.1",
    title: "Dispute & Criminal Litigation Adjudication",
    reason: "Requires legal judgment by the AICTE Appellate Committee regarding sub-judice matters or jurisdictional civil disputes.",
  },
];

export function CoveragePage() {
  const [selectedCat, setSelectedCat] = useState("All");

  const categories = ["All", ...Array.from(new Set(RULES.map((r) => r.category)))];
  const filtered = selectedCat === "All" ? RULES : RULES.filter((r) => r.category === selectedCat);

  const verifiedCount = RULES.filter((r) => r.status === "VERIFIED_OFFICIAL").length;
  const illustrativeCount = RULES.filter((r) => r.status === "ILLUSTRATIVE").length;

  return (
    <Layout wide>
      <div className="coverage-page" style={{ padding: "1.5rem", maxWidth: "1400px", margin: "0 auto" }}>
        <div style={{ marginBottom: "2rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.5rem" }}>
            <span className="badge" style={{ background: "var(--action-bg)", color: "var(--action)", fontWeight: 700 }}>
              SIH26261 REGULATORY ALIGNMENT
            </span>
            <span className="badge" style={{ background: "var(--surface-2)", color: "var(--ink-2)" }}>
              AICTE APH 2024–27 CHAPTER II
            </span>
          </div>
          <h1 style={{ fontSize: "2rem", fontWeight: 800, margin: 0, color: "var(--ink)" }}>
            Approval Process Handbook (APH) Statutory Coverage
          </h1>
          <p className="muted" style={{ margin: "0.5rem 0 0 0", fontSize: "1.05rem" }}>
            Transparent mapping of VeriScope&apos;s deterministic compliance rules against official AICTE Approval Process Handbook (2024–27 Chapter II) regulations.
          </p>
        </div>

        {/* ── Summary KPI Cards ── */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "1rem", marginBottom: "2rem" }}>
          <div className="card" style={{ padding: "1.25rem", borderLeft: "4px solid var(--action)" }}>
            <div className="muted" style={{ fontSize: "0.82rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>Total Catalogued Rules</div>
            <div style={{ fontSize: "2rem", fontWeight: 800, color: "var(--ink)", marginTop: "0.25rem" }}>{RULES.length}</div>
            <div className="sub" style={{ fontSize: "0.85rem", color: "var(--ink-3)" }}>Across 7 regulatory categories</div>
          </div>
          <div className="card" style={{ padding: "1.25rem", borderLeft: "4px solid var(--ok)" }}>
            <div className="muted" style={{ fontSize: "0.82rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>Verified Official APH Rules</div>
            <div style={{ fontSize: "2rem", fontWeight: 800, color: "var(--ok)", marginTop: "0.25rem" }}>{verifiedCount}</div>
            <div className="sub" style={{ fontSize: "0.85rem", color: "var(--ink-3)" }}>Backed by specific APH Chapter II clauses</div>
          </div>
          <div className="card" style={{ padding: "1.25rem", borderLeft: "4px solid var(--medium)" }}>
            <div className="muted" style={{ fontSize: "0.82rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>Illustrative Signals</div>
            <div style={{ fontSize: "2rem", fontWeight: 800, color: "var(--medium)", marginTop: "0.25rem" }}>{illustrativeCount}</div>
            <div className="sub" style={{ fontSize: "0.85rem", color: "var(--ink-3)" }}>Document forensics heuristic (EOA-SIG-003)</div>
          </div>
          <div className="card" style={{ padding: "1.25rem", borderLeft: "4px solid var(--ink-3)" }}>
            <div className="muted" style={{ fontSize: "0.82rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>Human Scrutiny Reserved</div>
            <div style={{ fontSize: "2rem", fontWeight: 800, color: "var(--ink-2)", marginTop: "0.25rem" }}>{NON_AUTOMATED_NORMS.length}</div>
            <div className="sub" style={{ fontSize: "0.85rem", color: "var(--ink-3)" }}>On-site visits &amp; original physical deed checks</div>
          </div>
        </div>

        {/* ── Category Filter ── */}
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginBottom: "1.25rem" }}>
          {categories.map((cat) => (
            <button
              key={cat}
              className={`btn btn-small ${selectedCat === cat ? "btn-primary" : "btn-ghost"}`}
              onClick={() => setSelectedCat(cat)}
            >
              {cat} ({cat === "All" ? RULES.length : RULES.filter((r) => r.category === cat).length})
            </button>
          ))}
        </div>

        {/* ── Rule Catalogue Table ── */}
        <div className="table-wrap" style={{ marginBottom: "3rem" }}>
          <table className="queue">
            <thead>
              <tr>
                <th scope="col" style={{ width: "130px" }}>Rule ID</th>
                <th scope="col" style={{ width: "100px" }}>Severity</th>
                <th scope="col">Statutory Citation &amp; APH Section</th>
                <th scope="col">Requirement &amp; Verification Action</th>
                <th scope="col" style={{ width: "200px" }}>Target Document(s)</th>
                <th scope="col" style={{ width: "160px" }}>Provenance Status</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => (
                <tr key={r.id}>
                  <td>
                    <span className="mono" style={{ fontWeight: 700, color: "var(--action)" }}>{r.id}</span>
                    <div style={{ fontSize: "0.78rem", color: "var(--ink-3)" }}>{r.category}</div>
                  </td>
                  <td>
                    <SeverityTag severity={r.severity} />
                  </td>
                  <td>
                    <div style={{ fontWeight: 600, fontSize: "0.9rem" }}>{r.citation}</div>
                    <div style={{ fontSize: "0.8rem", color: "var(--ink-3)" }}>Source: {r.sourcePage}</div>
                  </td>
                  <td>
                    <div style={{ fontSize: "0.92rem", color: "var(--ink)" }}>{r.summary}</div>
                  </td>
                  <td>
                    {r.docTypes.map((dt) => (
                      <span key={dt} className="badge" style={{ fontSize: "0.74rem", marginRight: "4px", marginBottom: "4px", display: "inline-block" }}>
                        {dt.replace(/_/g, " ")}
                      </span>
                    ))}
                  </td>
                  <td>
                    {r.status === "VERIFIED_OFFICIAL" ? (
                      <span className="badge" style={{ background: "rgba(16,185,129,0.12)", color: "#059669", fontWeight: 600 }}>
                        ✓ APH Verified
                      </span>
                    ) : (
                      <span className="badge" style={{ background: "rgba(245,158,11,0.15)", color: "#D97706", fontWeight: 600 }}>
                        ⚙ Illustrative Signal
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* ── Non-Automated Norms Section ── */}
        <div className="card" style={{ padding: "1.75rem", background: "var(--surface)", border: "1px solid var(--border)" }}>
          <h2 style={{ fontSize: "1.3rem", fontWeight: 700, margin: "0 0 0.5rem 0", color: "var(--ink)" }}>
            Non-Automated Norms Reserved for AICTE Scrutiny Officers (R15 Human Authority)
          </h2>
          <p className="muted" style={{ margin: "0 0 1.25rem 0", fontSize: "0.95rem" }}>
            In strict adherence to SIH26261 Requirement R15, VeriScope acts as decision support and never usurps statutory human discretion. The following institutional norms remain exclusively under manual scrutiny:
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "1rem" }}>
            {NON_AUTOMATED_NORMS.map((n) => (
              <div key={n.title} style={{ padding: "1rem", borderRadius: "8px", background: "var(--surface-2)", border: "1px solid var(--border)" }}>
                <span className="badge" style={{ fontSize: "0.75rem", background: "var(--surface)", color: "var(--ink-2)", marginBottom: "0.5rem", display: "inline-block" }}>
                  {n.clause}
                </span>
                <div style={{ fontWeight: 700, fontSize: "0.95rem", color: "var(--ink)", marginBottom: "0.35rem" }}>
                  {n.title}
                </div>
                <div style={{ fontSize: "0.85rem", color: "var(--ink-2)", lineHeight: 1.4 }}>
                  {n.reason}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Layout>
  );
}
