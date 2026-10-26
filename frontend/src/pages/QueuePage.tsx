import { useCallback, useMemo, useRef, useState } from "react";
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

/* ── 3D tilt stat card ─────────────────────────────────────────────────── */
function Stat3DCard({
  label,
  value,
  sub,
  icon,
  iconStyle,
  valueStyle,
  accentColor = "var(--action)",
}: {
  label: string;
  value: number;
  sub: string;
  icon: React.ReactNode;
  iconStyle?: React.CSSProperties;
  valueStyle?: React.CSSProperties;
  accentColor?: string;
}) {
  const cardRef = useRef<HTMLDivElement>(null);
  const glareRef = useRef<HTMLDivElement>(null);

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    const card = cardRef.current;
    if (!card) return;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const cx = rect.width / 2;
    const cy = rect.height / 2;
    const rotateX = ((y - cy) / cy) * -8;
    const rotateY = ((x - cx) / cx) * 8;
    card.style.transform = `perspective(600px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-4px)`;
    card.style.boxShadow = `0 16px 40px -6px rgba(15,23,42,0.12), 0 8px 16px -4px rgba(15,23,42,0.06), inset 0 1px 0 rgba(255,255,255,0.8)`;
    if (glareRef.current) {
      const mx = (x / rect.width) * 100;
      const my = (y / rect.height) * 100;
      glareRef.current.style.background = `radial-gradient(circle at ${mx}% ${my}%, rgba(255,255,255,0.22) 0%, transparent 60%)`;
      glareRef.current.style.opacity = "1";
    }
  }, []);

  const handleMouseLeave = useCallback(() => {
    const card = cardRef.current;
    if (!card) return;
    card.style.transform = "";
    card.style.boxShadow = "";
    if (glareRef.current) glareRef.current.style.opacity = "0";
  }, []);

  return (
    <div
      ref={cardRef}
      className="stat-card"
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{ transition: "transform 0.08s ease, box-shadow 0.08s ease" }}
    >
      {/* Top accent bar */}
      <div className="stat-accent-bar" style={{ background: accentColor }} />
      {/* Glare overlay */}
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
    return { total: data.total, needsReview, highFlags, decided };
  }, [data]);

  return (
    <Layout>
      {/* ── Page header with gradient title ── */}
      <div className="page-head-3d">
        <div>
          <h1>{isApplicant ? "My Applications" : "Review Queue"}</h1>
          <p className="muted">
            {isApplicant
              ? "Track your submitted institutional applications and respond to reviewer clarifications."
              : "Priority-ordered queue based on rule findings and required triage urgency."}
          </p>
        </div>
        <button
          className="btn-press"
          onClick={() => navigate("/cases/new")}
        >
          <IconPlus width="14" height="14" />
          <span>New application</span>
        </button>
      </div>

      {/* ── 3D tilt stat cards ── */}
      {!isApplicant && data && (
        <div className="stats-grid">
          <Stat3DCard
            label="Total Applications"
            value={stats.total}
            sub="Across all approval categories"
            icon={<IconFileText width="16" height="16" />}
            iconStyle={{ background: "var(--surface-3)", color: "var(--ink-2)" }}
            accentColor="var(--ink-3)"
          />
          <Stat3DCard
            label="Needs Review"
            value={stats.needsReview}
            sub="Awaiting officer determination"
            icon={<IconAlert width="16" height="16" />}
            iconStyle={{ background: "var(--action-soft)", color: "var(--action)" }}
            valueStyle={{ color: "var(--action)" }}
            accentColor="var(--action)"
          />
          <Stat3DCard
            label="High-Severity Flags"
            value={stats.highFlags}
            sub="Rules requiring resolution or waiver"
            icon={<IconShield width="16" height="16" />}
            iconStyle={{ background: "var(--high-bg)", color: "var(--high)" }}
            valueStyle={{ color: stats.highFlags > 0 ? "var(--high)" : "var(--ink)" }}
            accentColor={stats.highFlags > 0 ? "var(--high)" : "var(--ink-3)"}
          />
          <Stat3DCard
            label="Decided / Closed"
            value={stats.decided}
            sub="Approved or recorded outcomes"
            icon={<IconCheck width="16" height="16" />}
            iconStyle={{ background: "var(--ok-bg)", color: "var(--ok)" }}
            valueStyle={{ color: "var(--ok)" }}
            accentColor="var(--ok)"
          />
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
            <button className="btn-press" onClick={() => navigate("/cases/new")}>
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
                  <th scope="col">Applicant &amp; Institution</th>
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
