import { useCallback, useMemo, useRef, useState } from "react";
import { api } from "../api/client";
import type { CaseStatus } from "../api/types";
import { Spinner, StatusBadge } from "../components/Badges";
import { IconAlert, IconCheck, IconFileText, IconPlus, IconSearch, IconShield } from "../components/Icons";
import { Layout, PageState } from "../components/Layout";
import { CircularReadings3D, type TelemetryReading } from "../components/ui/CircularReadings3D";
import { ago, STATUS_LABEL } from "../lib/format";
import { errorText, useAsync } from "../lib/hooks";
import { navigate } from "../lib/router";
import { useSession } from "../lib/session";

const REVIEWER_FILTERS: { id: string; label: string }[] = [
  { id: "needs_review,clarification_requested,processing_failed,received,processing", label: "Active" },
  { id: "needs_review", label: STATUS_LABEL.needs_review },
  { id: "clarification_requested", label: STATUS_LABEL.clarification_requested },
  { id: "approved,rejected", label: "Decided" },
  { id: "", label: "All" },
];

/* ── Apple-style 3D tilt stat card ────────────────────────────────────────── */
function StatCard({
  label, value, sub, icon, iconStyle, valueStyle, accentColor = "var(--action)",
}: {
  label: string; value: number; sub: string; icon: React.ReactNode;
  iconStyle?: React.CSSProperties; valueStyle?: React.CSSProperties; accentColor?: string;
}) {
  const cardRef = useRef<HTMLDivElement>(null);
  const glareRef = useRef<HTMLDivElement>(null);

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    const card = cardRef.current; if (!card) return;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left, y = e.clientY - rect.top;
    const rotateX = ((y - rect.height / 2) / (rect.height / 2)) * -6;
    const rotateY = ((x - rect.width / 2) / (rect.width / 2)) * 6;
    card.style.transform = `perspective(800px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-3px)`;
    card.style.boxShadow = `0 20px 48px -8px rgba(14,16,19,0.1), 0 8px 16px -4px rgba(14,16,19,0.06)`;
    if (glareRef.current) {
      glareRef.current.style.background = `radial-gradient(circle at ${(x / rect.width) * 100}% ${(y / rect.height) * 100}%, rgba(255,255,255,0.18) 0%, transparent 60%)`;
      glareRef.current.style.opacity = "1";
    }
  }, []);

  const handleMouseLeave = useCallback(() => {
    const card = cardRef.current; if (!card) return;
    card.style.transform = "";
    card.style.boxShadow = "";
    if (glareRef.current) glareRef.current.style.opacity = "0";
  }, []);

  return (
    <div ref={cardRef} className="stat-card" onMouseMove={handleMouseMove} onMouseLeave={handleMouseLeave}
      style={{ transition: "transform 0.1s ease, box-shadow 0.1s ease" }}>
      <div className="stat-accent-bar" style={{ background: accentColor }} />
      <div ref={glareRef} className="stat-glare" />
      <div className="stat-top">
        <span>{label}</span>
        <span className="stat-icon" style={iconStyle}>{icon}</span>
      </div>
      <div className="stat-num" style={valueStyle}>{value}</div>
      <span className="stat-sub">{sub}</span>
    </div>
  );
}

/* ── Applicant view: clean minimal card list ──────────────────────────────── */
function ApplicantQueue() {
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const { data, error, loading, reload } = useAsync(
    () => api.listCases({ q, page, page_size: 10, sort: "priority" }),
    [q, page]
  );

  return (
    <Layout>
      {/* Header */}
      <div className="role-page-header">
        <div className="role-page-header-left">
          <h1 className="role-page-title">My Applications</h1>
          <p className="role-page-subtitle">Track your submitted applications and respond to reviewer clarifications.</p>
        </div>
        <button className="btn-primary-pill" onClick={() => navigate("/cases/new")}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
            <path d="M12 5v14M5 12h14" />
          </svg>
          New Application
        </button>
      </div>

      {/* Search */}
      <div className="apple-search-bar">
        <IconSearch width="15" height="15" />
        <input
          type="search"
          placeholder="Search by case reference or institution…"
          value={q}
          onChange={(e) => { setQ(e.target.value); setPage(1); }}
          aria-label="Search applications"
        />
      </div>

      {/* Content */}
      {error ? (
        <PageState title="Could not load applications" action={<button className="btn" onClick={() => void reload()}>Try again</button>}>
          {errorText(error)}
        </PageState>
      ) : loading && !data ? (
        <div className="center"><Spinner /></div>
      ) : data && data.items.length === 0 ? (
        <div className="applicant-empty">
          <div className="applicant-empty-icon">
            <IconFileText width="28" height="28" />
          </div>
          <h3>No applications yet</h3>
          <p>Submit your first institutional application to get started.</p>
          <button className="btn-primary-pill" onClick={() => navigate("/cases/new")}>
            Start an application
          </button>
        </div>
      ) : data && (
        <>
          <div className="applicant-cards">
            {data.items.map((c) => (
              <button
                key={c.id}
                className="applicant-card"
                onClick={() => navigate(`/cases/${c.id}`)}
              >
                <div className="applicant-card-left">
                  <div className="applicant-card-ref">{c.case_ref}</div>
                  <div className="applicant-card-inst">{c.institution_ref}</div>
                  <div className="applicant-card-meta">{c.document_count} document{c.document_count !== 1 ? "s" : ""} · Updated {ago(c.updated_at)}</div>
                </div>
                <div className="applicant-card-right">
                  <StatusBadge status={c.status as CaseStatus} />
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                    <path d="M9 18l6-6-6-6" />
                  </svg>
                </div>
              </button>
            ))}
          </div>
          <div className="pagination">
            <span className="muted small">Showing {data.items.length} of {data.total} application(s)</span>
            <button className="btn btn-small btn-ghost" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button>
            <button className="btn btn-small btn-ghost" disabled={page * data.page_size >= data.total} onClick={() => setPage(page + 1)}>Next</button>
          </div>
        </>
      )}
    </Layout>
  );
}

/* ── Admin view: management overview ──────────────────────────────────────── */
function AdminQueue() {
  const [status, setStatus] = useState("");
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const { data, error, loading, reload } = useAsync(
    () => api.listCases({ status, q, page, page_size: 20, sort: "priority" }),
    [status, q, page]
  );

  const stats = useMemo(() => {
    if (!data) return { total: 0, active: 0, decided: 0, failed: 0 };
    let active = 0, decided = 0, failed = 0;
    for (const c of data.items) {
      if (c.status === "approved" || c.status === "rejected") decided++;
      else if (c.status === "processing_failed") failed++;
      else active++;
    }
    return { total: data.total, active, decided, failed };
  }, [data]);

  return (
    <Layout wide>
      {/* Admin header */}
      <div className="role-page-header admin-header">
        <div className="role-page-header-left">
          <div className="admin-role-chip">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
            </svg>
            Admin Console
          </div>
          <h1 className="role-page-title">Case Management</h1>
          <p className="role-page-subtitle">System-wide oversight of all institutional verification cases.</p>
        </div>
      </div>

      {/* Admin summary row */}
      {data && (
        <div className="admin-summary-row">
          <div className="admin-summary-item">
            <span className="admin-summary-value">{data.total}</span>
            <span className="admin-summary-label">Total Cases</span>
          </div>
          <div className="admin-summary-divider" />
          <div className="admin-summary-item">
            <span className="admin-summary-value admin-active">{stats.active}</span>
            <span className="admin-summary-label">Active</span>
          </div>
          <div className="admin-summary-divider" />
          <div className="admin-summary-item">
            <span className="admin-summary-value admin-decided">{stats.decided}</span>
            <span className="admin-summary-label">Decided</span>
          </div>
          <div className="admin-summary-divider" />
          <div className="admin-summary-item">
            <span className="admin-summary-value admin-failed">{stats.failed}</span>
            <span className="admin-summary-label">Failed</span>
          </div>
        </div>
      )}

      {/* Filters + search */}
      <div className="filters admin-filters">
        <div className="segmented" role="tablist" aria-label="Filter by status">
          {[
            { id: "", label: "All" },
            { id: "needs_review,received,processing,clarification_requested", label: "Active" },
            { id: "approved,rejected", label: "Decided" },
            { id: "processing_failed", label: "Failed" },
          ].map((f) => (
            <button key={f.id} role="tab" aria-selected={status === f.id}
              onClick={() => { setStatus(f.id); setPage(1); }}>
              {f.label}
            </button>
          ))}
        </div>
        <div className="apple-search-bar">
          <IconSearch width="15" height="15" />
          <input
            type="search"
            placeholder="Search case ref, applicant or institution…"
            value={q}
            onChange={(e) => { setQ(e.target.value); setPage(1); }}
            aria-label="Search cases"
          />
        </div>
      </div>

      {/* Table */}
      {error ? (
        <PageState title="Could not load cases" action={<button className="btn" onClick={() => void reload()}>Try again</button>}>
          {errorText(error)}
        </PageState>
      ) : loading && !data ? (
        <div className="center"><Spinner /></div>
      ) : data && (
        <>
          <div className="table-wrap">
            <table className="queue">
              <thead>
                <tr>
                  <th scope="col">Case Reference</th>
                  <th scope="col">Applicant &amp; Institution</th>
                  <th scope="col">Status</th>
                  <th scope="col">Documents</th>
                  <th scope="col">Last Activity</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((c) => (
                  <tr key={c.id} onClick={() => navigate(`/cases/${c.id}`)} className="clickable">
                    <td>
                      <a href={`#/cases/${c.id}`} className="case-ref" onClick={(e) => e.stopPropagation()}>{c.case_ref}</a>
                      <span className="sub">{c.application_type_label}</span>
                    </td>
                    <td>
                      <strong style={{ fontWeight: 600 }}>{c.applicant_ref}</strong>
                      <span className="sub">{c.institution_ref}</span>
                    </td>
                    <td><StatusBadge status={c.status as CaseStatus} /></td>
                    <td className="muted" style={{ fontSize: "0.84rem" }}>{c.document_count} doc{c.document_count !== 1 ? "s" : ""}</td>
                    <td className="muted" style={{ fontSize: "0.84rem" }}>{ago(c.updated_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="pagination">
            <span className="muted small">Showing {data.items.length} of {data.total}</span>
            <button className="btn btn-small btn-ghost" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button>
            <button className="btn btn-small btn-ghost" disabled={page * data.page_size >= data.total} onClick={() => setPage(page + 1)}>Next</button>
          </div>
        </>
      )}
    </Layout>
  );
}

/* ── Reviewer view: full queue with stats and telemetry ───────────────────── */
function ReviewerQueue() {
  const [status, setStatus] = useState(REVIEWER_FILTERS[0].id);
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const { data, error, loading, reload } = useAsync(
    () => api.listCases({ status, q, page, page_size: 15, sort: "priority" }),
    [status, q, page]
  );

  const stats = useMemo(() => {
    if (!data) return { total: 0, needsReview: 0, highFlags: 0, decided: 0 };
    let needsReview = 0, highFlags = 0, decided = 0;
    for (const c of data.items) {
      if (c.status === "needs_review") needsReview++;
      if (c.status === "approved" || c.status === "rejected") decided++;
      highFlags += c.open_findings.high || 0;
    }
    return { total: data.total, needsReview, highFlags, decided };
  }, [data]);

  const telemetryItems: TelemetryReading[] = useMemo(() => {
    if (!data?.items?.length) return [];
    return data.items.map((c) => {
      const isApproved = c.status === "approved";
      const hasHigh = (c.open_findings.high || 0) > 0;
      const s: "verified" | "flagged" | "auditing" = isApproved ? "verified" : hasHigh ? "flagged" : "auditing";
      return {
        id: c.id, code: c.case_ref, label: c.applicant_ref,
        val: isApproved ? "Approved · Verified" : hasHigh ? `${c.open_findings.high} High Discrepancies` : `${c.document_count} Documents Ingested`,
        metric: `Triage: ${c.triage_priority} pts · ${c.institution_ref}`,
        status: s,
        source: c.triage_components?.[0]?.label || (isApproved ? "Approved" : "Awaiting review"),
      };
    });
  }, [data]);

  return (
    <Layout>
      {/* Reviewer header */}
      <div className="role-page-header">
        <div className="role-page-header-left">
          <h1 className="role-page-title">Review Queue</h1>
          <p className="role-page-subtitle">Priority-ordered queue based on rule findings and triage urgency.</p>
        </div>
      </div>

      {/* Stat cards */}
      {data && (
        <div className="stats-grid">
          <StatCard label="Total Applications" value={stats.total} sub="Across all categories"
            icon={<IconFileText width="16" height="16" />} iconStyle={{ background: "var(--surface-3)", color: "var(--ink-2)" }} accentColor="var(--ink-3)" />
          <StatCard label="Needs Review" value={stats.needsReview} sub="Awaiting determination"
            icon={<IconAlert width="16" height="16" />} iconStyle={{ background: "var(--action-soft)", color: "var(--action)" }}
            valueStyle={{ color: "var(--action)" }} accentColor="var(--action)" />
          <StatCard label="High-Severity Flags" value={stats.highFlags} sub="Requiring resolution"
            icon={<IconShield width="16" height="16" />} iconStyle={{ background: "var(--high-bg)", color: "var(--high)" }}
            valueStyle={{ color: stats.highFlags > 0 ? "var(--high)" : "var(--ink)" }}
            accentColor={stats.highFlags > 0 ? "var(--high)" : "var(--ink-3)"} />
          <StatCard label="Decided / Closed" value={stats.decided} sub="Approved or recorded"
            icon={<IconCheck width="16" height="16" />} iconStyle={{ background: "var(--ok-bg)", color: "var(--ok)" }}
            valueStyle={{ color: "var(--ok)" }} accentColor="var(--ok)" />
        </div>
      )}

      {/* Telemetry display */}
      {data && <CircularReadings3D items={telemetryItems} />}

      {/* Filters + search */}
      <div className="filters">
        <div className="segmented" role="tablist" aria-label="Filter by status">
          {REVIEWER_FILTERS.map((f) => (
            <button key={f.label} role="tab" aria-selected={status === f.id}
              onClick={() => { setStatus(f.id); setPage(1); }}>
              {f.label}
            </button>
          ))}
        </div>
        <div className="apple-search-bar">
          <IconSearch width="15" height="15" />
          <input
            type="search"
            placeholder="Search case ref, applicant or institute…"
            value={q}
            onChange={(e) => { setQ(e.target.value); setPage(1); }}
            aria-label="Search cases"
          />
        </div>
      </div>

      {/* Table */}
      {error ? (
        <PageState title="The queue could not be loaded" action={<button className="btn" onClick={() => void reload()}>Try again</button>}>
          {errorText(error)}
        </PageState>
      ) : loading && !data ? (
        <div className="center"><Spinner /></div>
      ) : data && data.items.length === 0 ? (
        <PageState title={q ? "No cases match this search" : "Queue is empty"}>
          {q ? "Try a different case reference, applicant name, or institution ID." : "All cases have been processed."}
        </PageState>
      ) : data && (
        <>
          <div className="table-wrap">
            <table className="queue">
              <thead>
                <tr>
                  <th scope="col">Case Reference</th>
                  <th scope="col">Applicant &amp; Institution</th>
                  <th scope="col">Status</th>
                  <th scope="col">Open Findings</th>
                  <th scope="col">Triage Priority</th>
                  <th scope="col">Last Activity</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((c) => (
                  <tr key={c.id} onClick={() => navigate(`/cases/${c.id}`)} className="clickable">
                    <td>
                      <a href={`#/cases/${c.id}`} className="case-ref" onClick={(e) => e.stopPropagation()}>{c.case_ref}</a>
                      <span className="sub">{c.document_count} document(s) uploaded</span>
                    </td>
                    <td>
                      <strong style={{ fontWeight: 600 }}>{c.applicant_ref}</strong>
                      <span className="sub">{c.institution_ref}</span>
                    </td>
                    <td><StatusBadge status={c.status as CaseStatus} /></td>
                    <td>
                      <span className="counts">
                        {(["high", "medium", "low"] as const).map((s) =>
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
                    <td>
                      <span className="triage" title={c.triage_components.map((t) => `${t.label}: +${t.points}`).join("\n") || "No open findings"}>
                        <span className="triage-bar"><span style={{ width: `${Math.min(100, c.triage_priority)}%` }} /></span>
                        <span>{c.triage_priority}</span>
                      </span>
                      {c.triage_components[0] && <span className="sub">{c.triage_components[0].label}</span>}
                    </td>
                    <td className="muted" style={{ fontSize: "0.84rem" }}>{ago(c.updated_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="pagination">
            <span className="muted small">Showing {data.items.length} of {data.total} case(s)</span>
            <button className="btn btn-small btn-ghost" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button>
            <button className="btn btn-small btn-ghost" disabled={page * data.page_size >= data.total} onClick={() => setPage(page + 1)}>Next</button>
          </div>
        </>
      )}
    </Layout>
  );
}

/* ── Root: dispatch by role ────────────────────────────────────────────────── */
export function QueuePage() {
  const { user } = useSession();
  if (user?.role === "applicant") return <ApplicantQueue />;
  if (user?.role === "admin") return <AdminQueue />;
  return <ReviewerQueue />;
}
