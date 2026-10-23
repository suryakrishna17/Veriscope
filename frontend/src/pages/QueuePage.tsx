import { useState } from "react";
import { api } from "../api/client";
import type { CaseStatus } from "../api/types";
import { StatusBadge, Spinner } from "../components/Badges";
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
  const { data, error, loading, reload } = useAsync(() => api.listCases({ status, q, page, page_size: 15, sort: "priority" }), [status, q, page]);

  return (
    <Layout>
      <div className="page-head">
        <div>
          <h1>{isApplicant ? "My applications" : "Review queue"}</h1>
          <p className="muted">{isApplicant ? "Track your applications and answer requests from reviewers." : "Highest triage priority first. Priority only orders the queue; it never decides a case."}</p>
        </div>
        <button className="btn btn-primary" onClick={() => navigate("/cases/new")}>New application</button>
      </div>

      <div className="filters">
        {!isApplicant && (
          <div className="segmented" role="tablist" aria-label="Filter by status">
            {FILTERS.map((f) => (
              <button key={f.label} role="tab" aria-selected={status === f.id} onClick={() => { setStatus(f.id); setPage(1); }}>{f.label}</button>
            ))}
          </div>
        )}
        <input className="search" type="search" placeholder="Search case, applicant or institution" value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} aria-label="Search cases" />
      </div>

      {error ? (
        <PageState title="The queue could not be loaded" action={<button className="btn" onClick={() => void reload()}>Try again</button>}>{errorText(error)}</PageState>
      ) : loading && !data ? (
        <div className="center"><Spinner /></div>
      ) : data && data.items.length === 0 ? (
        <PageState title={q ? "No cases match this search" : "Nothing here yet"} action={<button className="btn btn-primary" onClick={() => navigate("/cases/new")}>Start an application</button>}>
          {q ? "Try another name, case reference or institution." : "New applications appear here once they are created."}
        </PageState>
      ) : data && (
        <>
          <div className="table-wrap">
            <table className="queue">
              <thead>
                <tr>
                  <th scope="col">Case</th>
                  <th scope="col">Applicant</th>
                  <th scope="col">Status</th>
                  {!isApplicant && <th scope="col">Open findings</th>}
                  {!isApplicant && <th scope="col">Triage priority</th>}
                  <th scope="col">Updated</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((c) => (
                  <tr key={c.id} onClick={() => navigate(`/cases/${c.id}`)} className="clickable">
                    <td><a href={`#/cases/${c.id}`} className="case-ref" onClick={(e) => e.stopPropagation()}>{c.case_ref}</a><span className="sub">{c.document_count} document(s)</span></td>
                    <td>{c.applicant_ref}<span className="sub">{c.institution_ref}</span></td>
                    <td><StatusBadge status={c.status as CaseStatus} /></td>
                    {!isApplicant && (
                      <td>
                        <span className="counts">
                          {(["high", "medium", "low"] as const).map((s) => c.open_findings[s] > 0 && <span key={s} className={`count count-${s}`} title={`${c.open_findings[s]} ${s}`}>{c.open_findings[s]} {s}</span>)}
                          {c.open_findings.high + c.open_findings.medium + c.open_findings.low === 0 && <span className="muted">None</span>}
                        </span>
                      </td>
                    )}
                    {!isApplicant && (
                      <td>
                        <span className="triage" title={c.triage_components.map((t) => `${t.label}: +${t.points}`).join("\n") || "No open findings"}>
                          <span className="triage-bar"><span style={{ width: `${c.triage_priority}%` }} /></span>
                          {c.triage_priority}
                        </span>
                        {c.triage_components[0] && <span className="sub">{c.triage_components[0].label}</span>}
                      </td>
                    )}
                    <td>{ago(c.updated_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="pagination">
            <span className="muted">{data.total} case(s)</span>
            <button className="btn btn-small btn-ghost" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button>
            <button className="btn btn-small btn-ghost" disabled={page * data.page_size >= data.total} onClick={() => setPage(page + 1)}>Next</button>
          </div>
        </>
      )}
    </Layout>
  );
}
