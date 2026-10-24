import { useMemo, useState } from "react";
import { api } from "../api/client";
import type { CaseStatus } from "../api/types";
import { Spinner, StatusBadge } from "../components/Badges";
import { IconAlert, IconCheck, IconFileText, IconPlus, IconSearch, IconShield } from "../components/Icons";
import { Layout, PageState } from "../components/Layout";
import { ago, STATUS_LABEL } from "../lib/format";
import { errorText, useAsync } from "../lib/hooks";
import { navigate } from "../lib/router";
import { useSession } from "../lib/session";

const FILTERS: { id: string; label: string }[] = [
  { id: "needs_review,clarification_requested,processing_failed,received,processing", label: "Active" },
  { id: "needs_review", label: STATUS_LABEL.needs_review },
  { id: "clarification_requested", label: STATUS_LABEL.clarification_requested },
  { id: "approved,rejected", label: "Decided" },
  { id: "", label: "All" },
];

export function QueuePage() {
  const { user } = useSession();
  const isApplicant = user?.role === "applicant";
  const [status, setStatus] = useState(isApplicant ? "" : FILTERS[0].id);
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const { data, error, loading, reload } = useAsync(
    () => api.listCases({ status, q, page, page_size: 15, sort: "priority" }),
    [status, q, page]
  );

  // Compute stat metrics for the current view
  const stats = useMemo(() => {
    if (!data) return { total: 0, needsReview: 0, highFlags: 0, decided: 0 };
    let needsReview = 0;
    let highFlags = 0;
    let decided = 0;
    for (const c of data.items) {
      if (c.status === "needs_review") needsReview++;
      if (c.status === "approved" || c.status === "rejected") decided++;
      highFlags += c.open_findings.high || 0;
    }
    return {
      total: data.total,
      needsReview,
      highFlags,
      decided,
    };
  }, [data]);

  return (
    <Layout>
      <div className="page-head">
        <div>
          <h1>{isApplicant ? "My Applications" : "Review Queue"}</h1>
          <p className="muted">
            {isApplicant
              ? "Track your submitted institutional applications and respond to reviewer clarifications."
              : "Priority-ordered queue based on rule findings and required triage urgency."}
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => navigate("/cases/new")}>
          <IconPlus width="14" height="14" />
          <span>New Application</span>
        </button>
      </div>

      {!isApplicant && data && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-top">
              <span>Total Applications</span>
              <span className="stat-icon" style={{ background: "var(--surface-3)", color: "var(--ink-2)" }}>
                <IconFileText width="16" height="16" />
              </span>
            </div>
            <div className="stat-num">{stats.total}</div>
            <span className="stat-sub">Across all approval categories</span>
          </div>

          <div className="stat-card">
            <div className="stat-top">
              <span>Needs Review</span>
              <span className="stat-icon" style={{ background: "var(--action-soft)", color: "var(--action)" }}>
                <IconAlert width="16" height="16" />
              </span>
            </div>
            <div className="stat-num" style={{ color: "var(--action)" }}>{stats.needsReview}</div>
            <span className="stat-sub">Awaiting officer determination</span>
          </div>

          <div className="stat-card">
            <div className="stat-top">
              <span>High-Severity Flags</span>
              <span className="stat-icon" style={{ background: "var(--high-bg)", color: "var(--high)" }}>
                <IconShield width="16" height="16" />
              </span>
            </div>
            <div className="stat-num" style={{ color: stats.highFlags > 0 ? "var(--high)" : "var(--ink)" }}>
              {stats.highFlags}
            </div>
            <span className="stat-sub">Rules requiring resolution or waiver</span>
          </div>

          <div className="stat-card">
            <div className="stat-top">
              <span>Decided / Closed</span>
              <span className="stat-icon" style={{ background: "var(--ok-bg)", color: "var(--ok)" }}>
                <IconCheck width="16" height="16" />
              </span>
            </div>
            <div className="stat-num" style={{ color: "var(--ok)" }}>{stats.decided}</div>
            <span className="stat-sub">Approved or recorded outcomes</span>
          </div>
        </div>
      )}

      <div className="filters">
        {!isApplicant && (
          <div className="segmented" role="tablist" aria-label="Filter by status">
            {FILTERS.map((f) => (
              <button
                key={f.label}
                role="tab"
                aria-selected={status === f.id}
                onClick={() => {
                  setStatus(f.id);
                  setPage(1);
                }}
              >
                {f.label}
              </button>
            ))}
          </div>
        )}

        <div className="search-box">
          <span className="search-icon"><IconSearch width="15" height="15" /></span>
          <input
            type="search"
            placeholder="Search case ref, applicant or institute…"
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setPage(1);
            }}
            aria-label="Search cases"
          />
        </div>
      </div>

      {error ? (
        <PageState
          title="The queue could not be loaded"
          action={<button className="btn" onClick={() => void reload()}>Try again</button>}
        >
          {errorText(error)}
        </PageState>
      ) : loading && !data ? (
        <div className="center"><Spinner /></div>
      ) : data && data.items.length === 0 ? (
        <PageState
          title={q ? "No cases match this search" : "No applications found"}
          action={
            <button className="btn btn-primary" onClick={() => navigate("/cases/new")}>
              <IconPlus width="14" height="14" />
              <span>Start an application</span>
            </button>
          }
        >
          {q ? "Try searching with a different case reference, applicant name, or institution ID." : "New institutional applications will appear here once submitted."}
        </PageState>
      ) : data && (
        <>
          <div className="table-wrap">
            <table className="queue">
              <thead>
                <tr>
                  <th scope="col">Case Reference</th>
                  <th scope="col">Applicant & Institution</th>
                  <th scope="col">Status</th>
                  {!isApplicant && <th scope="col">Open Findings</th>}
                  {!isApplicant && <th scope="col">Triage Priority</th>}
                  <th scope="col">Last Activity</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((c) => (
                  <tr key={c.id} onClick={() => navigate(`/cases/${c.id}`)} className="clickable">
                    <td>
                      <a href={`#/cases/${c.id}`} className="case-ref" onClick={(e) => e.stopPropagation()}>
                        {c.case_ref}
                      </a>
                      <span className="sub">{c.document_count} document(s) uploaded</span>
                    </td>
                    <td>
                      <strong style={{ fontWeight: 600 }}>{c.applicant_ref}</strong>
                      <span className="sub">{c.institution_ref}</span>
                    </td>
                    <td>
                      <StatusBadge status={c.status as CaseStatus} />
                    </td>
                    {!isApplicant && (
                      <td>
                        <span className="counts">
                          {(["high", "medium", "low"] as const).map(
                            (s) =>
                              c.open_findings[s] > 0 && (
                                <span key={s} className={`count count-${s}`} title={`${c.open_findings[s]} ${s} severity`}>
                                  {c.open_findings[s]} {s}
                                </span>
                              )
                          )}
                          {c.open_findings.high + c.open_findings.medium + c.open_findings.low === 0 && (
                            <span className="muted small">All clear</span>
                          )}
                        </span>
                      </td>
                    )}
                    {!isApplicant && (
                      <td>
                        <span
                          className="triage"
                          title={c.triage_components.map((t) => `${t.label}: +${t.points}`).join("\n") || "No open findings"}
                        >
                          <span className="triage-bar">
                            <span style={{ width: `${Math.min(100, c.triage_priority)}%` }} />
                          </span>
                          <span>{c.triage_priority}</span>
                        </span>
                        {c.triage_components[0] && <span className="sub">{c.triage_components[0].label}</span>}
                      </td>
                    )}
                    <td className="muted" style={{ fontSize: "0.84rem" }}>{ago(c.updated_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="pagination">
            <span className="muted small">Showing {data.items.length} of {data.total} case(s)</span>
            <button className="btn btn-small btn-ghost" disabled={page <= 1} onClick={() => setPage(page - 1)}>
              Previous
            </button>
            <button className="btn btn-small btn-ghost" disabled={page * data.page_size >= data.total} onClick={() => setPage(page + 1)}>
              Next
            </button>
          </div>
        </>
      )}
    </Layout>
  );
}
