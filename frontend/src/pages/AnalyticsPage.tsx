import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { AnalyticsData } from "../api/types";
import { SeverityTag, Spinner } from "../components/Badges";
import { Layout } from "../components/Layout";

export function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    api.analytics()
      .then((res) => {
        if (active) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (active) {
          setError(err.message || "Failed to load analytics");
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <Layout wide>
      <div className="analytics-page" style={{ padding: "1.5rem", maxWidth: "1400px", margin: "0 auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
          <div>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 700, margin: 0 }}>
              Institutional Compliance &amp; Operations Analytics
            </h1>
            <p className="muted" style={{ margin: "0.25rem 0 0 0" }}>
              Authoritative statutory auditing telemetry across technical institutions under AICTE APH Chapter II.
            </p>
          </div>
          <button
            type="button"
            className="btn btn-secondary btn-small"
            onClick={() => {
              setLoading(true);
              api.analytics().then((res) => { setData(res); setLoading(false); });
            }}
          >
            ↻ Refresh Telemetry
          </button>
        </div>

        {loading && (
          <div className="center full" style={{ minHeight: "300px" }}>
            <Spinner />
          </div>
        )}

        {error && (
          <div className="alert alert-error" style={{ marginBottom: "1.5rem" }}>
            <strong>Analytics Error:</strong> {error}
          </div>
        )}

        {data && (
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            {/* ── KPI Row ── */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem" }}>
              <div className="card" style={{ padding: "1.25rem" }}>
                <div className="muted small" style={{ textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 600 }}>
                  Total Dossiers
                </div>
                <div style={{ fontSize: "2rem", fontWeight: 700, marginTop: "0.5rem" }}>
                  {data.overview.total_cases}
                </div>
                <div className="small muted" style={{ marginTop: "0.25rem" }}>
                  {data.overview.active_cases} Active · {data.overview.decided_cases} Finalized
                </div>
              </div>

              <div className="card" style={{ padding: "1.25rem" }}>
                <div className="muted small" style={{ textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 600 }}>
                  Automated Pass Rate
                </div>
                <div style={{ fontSize: "2rem", fontWeight: 700, marginTop: "0.5rem", color: "#10b981" }}>
                  {data.overview.automated_pass_rate_percent}%
                </div>
                <div className="small muted" style={{ marginTop: "0.25rem" }}>
                  {data.outcome_distribution.PASS || 0} PASS / {data.outcome_distribution.FAIL || 0} FAIL
                </div>
              </div>

              <div className="card" style={{ padding: "1.25rem" }}>
                <div className="muted small" style={{ textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 600 }}>
                  Mean Urgency Score
                </div>
                <div style={{ fontSize: "2rem", fontWeight: 700, marginTop: "0.5rem", color: "#f59e0b" }}>
                  {data.overview.mean_urgency_score} <span style={{ fontSize: "1rem", color: "var(--text-muted)" }}>/ 100</span>
                </div>
                <div className="small muted" style={{ marginTop: "0.25rem" }}>
                  Weighted risk triage ranking
                </div>
              </div>

              <div className="card" style={{ padding: "1.25rem" }}>
                <div className="muted small" style={{ textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 600 }}>
                  Review Turnaround
                </div>
                <div style={{ fontSize: "2rem", fontWeight: 700, marginTop: "0.5rem" }}>
                  {data.overview.mean_tat_hours} <span style={{ fontSize: "1rem", color: "var(--text-muted)" }}>hrs</span>
                </div>
                <div className="small muted" style={{ marginTop: "0.25rem" }}>
                  Average creation-to-decision SLA
                </div>
              </div>

              <div className="card" style={{ padding: "1.25rem" }}>
                <div className="muted small" style={{ textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 600 }}>
                  OCR Confidence
                </div>
                <div style={{ fontSize: "2rem", fontWeight: 700, marginTop: "0.5rem" }}>
                  {data.overview.mean_ocr_confidence}%
                </div>
                <div className="small muted" style={{ marginTop: "0.25rem" }}>
                  Multi-tier vector + vision OCR
                </div>
              </div>
            </div>

            {/* ── Status Pipeline Breakdown ── */}
            <div className="card" style={{ padding: "1.5rem" }}>
              <h3 style={{ margin: "0 0 1rem 0", fontSize: "1.1rem", fontWeight: 600 }}>
                Regulatory Lifecycle Pipeline
              </h3>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "1rem" }}>
                {[
                  { key: "received", label: "Received", color: "#6b7280" },
                  { key: "processing", label: "Processing", color: "#3b82f6" },
                  { key: "needs_review", label: "Needs Review", color: "#f59e0b" },
                  { key: "clarification_requested", label: "Clarification Req.", color: "#8b5cf6" },
                  { key: "approved", label: "Approved", color: "#10b981" },
                  { key: "rejected", label: "Rejected", color: "#ef4444" },
                ].map((s) => {
                  const count = data.status_distribution[s.key] || 0;
                  const pct = data.overview.total_cases > 0
                    ? Math.round((count / data.overview.total_cases) * 100)
                    : 0;
                  return (
                    <div
                      key={s.key}
                      style={{
                        padding: "0.75rem",
                        borderRadius: "8px",
                        background: "rgba(255, 255, 255, 0.03)",
                        border: "1px solid var(--border)",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span className="small muted">{s.label}</span>
                        <strong style={{ color: s.color }}>{count}</strong>
                      </div>
                      <div
                        style={{
                          height: "4px",
                          width: "100%",
                          background: "rgba(255, 255, 255, 0.1)",
                          borderRadius: "2px",
                          marginTop: "0.5rem",
                          overflow: "hidden",
                        }}
                      >
                        <div
                          style={{
                            height: "100%",
                            width: `${pct}%`,
                            background: s.color,
                            borderRadius: "2px",
                          }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* ── Top Statutory Deficiencies ── */}
            <div className="card" style={{ padding: "1.5rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: "1.1rem", fontWeight: 600 }}>
                    Top Systemic AICTE Statutory Non-Compliance Deficiencies
                  </h3>
                  <p className="muted small" style={{ margin: "0.25rem 0 0 0" }}>
                    Ranked by occurrence across active institutional dossiers under Approval Process Handbook (APH).
                  </p>
                </div>
              </div>

              {data.top_deficiencies.length === 0 ? (
                <p className="muted" style={{ padding: "1rem 0" }}>
                  No open statutory deficiencies recorded across current applications.
                </p>
              ) : (
                <div style={{ overflowX: "auto" }}>
                  <table className="table" style={{ width: "100%", textAlign: "left", borderCollapse: "collapse" }}>
                    <thead>
                      <tr style={{ borderBottom: "1px solid var(--border)", color: "var(--text-muted)", fontSize: "0.85rem" }}>
                        <th style={{ padding: "0.75rem" }}>Violations</th>
                        <th style={{ padding: "0.75rem" }}>Severity</th>
                        <th style={{ padding: "0.75rem" }}>Rule ID</th>
                        <th style={{ padding: "0.75rem" }}>Official Statutory Citation</th>
                        <th style={{ padding: "0.75rem" }}>Summary &amp; Category</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.top_deficiencies.map((d) => (
                        <tr key={d.rule_id} style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.05)" }}>
                          <td style={{ padding: "0.75rem" }}>
                            <span
                              style={{
                                display: "inline-block",
                                padding: "0.2rem 0.6rem",
                                borderRadius: "999px",
                                background: "rgba(239, 68, 68, 0.15)",
                                color: "#ef4444",
                                fontWeight: 700,
                                fontSize: "0.85rem",
                              }}
                            >
                              {d.count}
                            </span>
                          </td>
                          <td style={{ padding: "0.75rem" }}>
                            <SeverityTag severity={d.severity} />
                          </td>
                          <td style={{ padding: "0.75rem", fontFamily: "monospace", fontSize: "0.85rem", fontWeight: 600 }}>
                            {d.rule_id}
                          </td>
                          <td style={{ padding: "0.75rem", fontSize: "0.85rem", color: "var(--action)" }}>
                            {d.clause_citation ? `📜 ${d.clause_citation}` : "Statutory Baseline"}
                          </td>
                          <td style={{ padding: "0.75rem", fontSize: "0.85rem" }}>
                            <div>{d.summary}</div>
                            <span className="muted small" style={{ textTransform: "capitalize" }}>
                              Category: {d.category}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* ── Document Trust & Three-Tier Verification Distribution ── */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "1rem" }}>
              <div className="card" style={{ padding: "1.25rem" }}>
                <h4 style={{ margin: "0 0 0.5rem 0", fontWeight: 600 }}>Three-Tier Trust State Model</h4>
                <p className="muted small" style={{ margin: "0 0 1rem 0" }}>
                  Strict trust classification preventing false authenticity claims without external PKI registry verification.
                </p>
                <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span className="badge" style={{ background: "rgba(107, 114, 128, 0.2)", color: "#9ca3af" }}>
                      NOT_VERIFIED (Default Intake)
                    </span>
                    <strong>{data.trust_distribution.NOT_VERIFIED || 0}</strong>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span className="badge" style={{ background: "rgba(245, 158, 11, 0.2)", color: "#f59e0b" }}>
                      ANOMALY_DETECTED (Discrepancy)
                    </span>
                    <strong>{data.trust_distribution.ANOMALY_DETECTED || 0}</strong>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span className="badge" style={{ background: "rgba(16, 185, 129, 0.2)", color: "#10b981" }}>
                      ISSUER_VERIFIED (DPI / PKI)
                    </span>
                    <strong>{data.trust_distribution.ISSUER_VERIFIED || 0}</strong>
                  </div>
                </div>
              </div>

              <div className="card" style={{ padding: "1.25rem" }}>
                <h4 style={{ margin: "0 0 0.5rem 0", fontWeight: 600 }}>Application Types Monitored</h4>
                <p className="muted small" style={{ margin: "0 0 1rem 0" }}>
                  Statutory regulatory catalogues currently active in VeriScope.
                </p>
                <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span>🏛️ AICTE Extension of Approval (EoA)</span>
                    <strong>{data.application_type_distribution.AICTE_EOA || 0}</strong>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span>🎓 Student Support (Prototype Lite)</span>
                    <strong>{data.application_type_distribution.STUDENT_SUPPORT_LITE || 0}</strong>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
