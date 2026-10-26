import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { CaseDetail, EvidenceRef, Field, Finding } from "../api/types";
import { AuditTimeline } from "../components/AuditTimeline";
import { Spinner, StatusBadge } from "../components/Badges";
import { DecisionBar } from "../components/DecisionBar";
import { EvidenceViewer, type Highlight } from "../components/EvidenceViewer";
import { FieldTable } from "../components/FieldTable";
import { FindingsPanel } from "../components/FindingsPanel";
import { IconFileText, IconPlay, IconShield } from "../components/Icons";
import { Layout, PageState } from "../components/Layout";
import { Modal } from "../components/Modal";
import { Uploader } from "../components/Uploader";
import { DOC_LABEL, humanize, when } from "../lib/format";
import { errorText, useAsync } from "../lib/hooks";
import { navigate } from "../lib/router";
import { useSession } from "../lib/session";
import { useToast } from "../lib/toast";

/* ── Reopen dialog ────────────────────────────────────────────────────────── */
function ReopenDialog({ open, caseId, onClose }: { open: boolean; caseId: string; onClose: (ok: boolean) => void }) {
  const [note, setNote] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const toast = useToast();

  const submit = async () => {
    try {
      await api.reopen(caseId, note);
      toast("Case reopened for review.");
      onClose(true);
    } catch (e) { setErr(errorText(e)); }
  };

  if (!open) return null;
  return (
    <Modal open title="Reopen Case for Review" onClose={() => onClose(false)}
      footer={<>
        <button className="btn btn-ghost" onClick={() => onClose(false)}>Cancel</button>
        <button className="btn btn-primary" disabled={note.trim().length < 5} onClick={() => void submit()}>Confirm Reopening</button>
      </>}
    >
      <label className="stack">
        <span>Reason for reopening</span>
        <textarea rows={3} value={note} onChange={(e) => setNote(e.target.value)}
          placeholder="e.g. New land ownership documentation submitted by applicant." />
      </label>
      {err && <p className="inline-error">{err}</p>}
    </Modal>
  );
}

/* ── Applicant case view ──────────────────────────────────────────────────── */
function ApplicantCaseView({ c, reload, reopenOpen, setReopenOpen }: {
  c: CaseDetail; reload: (s?: boolean) => Promise<void>;
  reopenOpen: boolean; setReopenOpen: (v: boolean) => void;
}) {
  const clarification = c.decisions.find((d) => d.outcome === "request_clarification");
  const isProcessing = c.status === "processing";
  const isFailed = c.status === "processing_failed";

  return (
    <Layout>
      {/* Back + title */}
      <div className="case-head apple-case-head">
        <a href="#/cases" className="apple-back-btn">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M15 18l-6-6 6-6" />
          </svg>
          My Applications
        </a>
        <div className="apple-case-title-row">
          <h1 className="apple-case-title">{c.case_ref}</h1>
          <StatusBadge status={c.status} />
        </div>
        <p className="apple-case-meta">{c.applicant_ref} · {c.institution_ref} · {c.application_type_label}</p>
      </div>

      {/* Status banners */}
      {isProcessing && (
        <div className="apple-banner apple-banner-info" role="status">
          <Spinner label="Processing" />
          <span>Your documents are being analysed — {c.latest_job?.progress ?? 0}% complete.</span>
        </div>
      )}
      {isFailed && (
        <div className="apple-banner apple-banner-error" role="alert">
          {c.latest_job?.error_message ?? "Document checks could not complete."} Upload clearer copies and try again.
        </div>
      )}
      {c.status === "clarification_requested" && clarification && (
        <div className="apple-banner apple-banner-warn banner-warn">
          <strong>Additional information requested:</strong> {clarification.note} Upload the requested documents below, then re-run checks.
        </div>
      )}

      {/* Official determination */}
      {c.decisions[0] && c.status !== "clarification_requested" && (
        <div className="apple-card apple-card-determination">
          <div className="apple-card-label">Official Determination</div>
          <p className="apple-determination-outcome">{humanize(c.decisions[0].outcome)}</p>
          <p className="apple-determination-meta">
            {when(c.decisions[0].decided_at)} · {c.decisions[0].reviewer}
            {c.decisions[0].note ? ` — "${c.decisions[0].note}"` : ""}
          </p>
        </div>
      )}

      {/* Documents */}
      <div className="apple-card">
        <div className="apple-card-header">
          <div className="apple-card-label">Application Documents</div>
          <span className="apple-card-count">{c.documents.length} uploaded</span>
        </div>
        {c.allowed_actions.includes("upload") ? (
          <Uploader caseId={c.id} existing={c.documents} onUploaded={() => void reload(true)} applicationType={c.application_type} />
        ) : (
          <ul className="apple-doc-list">
            {c.documents.map((d) => (
              <li key={d.id} className="apple-doc-item">
                <span className="apple-doc-icon">
                  <IconFileText width="16" height="16" />
                </span>
                <span className="apple-doc-name">{DOC_LABEL[d.doc_type] || d.doc_type}</span>
                <span className="apple-doc-filename">{d.original_name}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Re-run checks (if applicant can trigger) */}
      {c.allowed_actions.includes("process") && c.documents.length > 0 && (
        <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "1rem" }}>
          <button className="btn-primary-pill" onClick={() => void api.process(c.id).then(() => reload(true))}>
            <IconPlay width="13" height="13" />
            Run checks
          </button>
        </div>
      )}

      <ReopenDialog open={reopenOpen} caseId={c.id} onClose={(ok) => { setReopenOpen(false); if (ok) void reload(true); }} />
    </Layout>
  );
}

/* ── Admin case view ──────────────────────────────────────────────────────── */
function AdminCaseView({ c, reload, running, run, reopenOpen, setReopenOpen }: {
  c: CaseDetail; reload: (s?: boolean) => Promise<void>;
  running: boolean; run: (force: boolean) => Promise<void>;
  reopenOpen: boolean; setReopenOpen: (v: boolean) => void;
}) {
  return (
    <Layout>
      <div className="case-head apple-case-head">
        <a href="#/cases" className="apple-back-btn">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M15 18l-6-6 6-6" />
          </svg>
          Case Queue
        </a>
        <div className="apple-case-title-row">
          <div className="admin-role-chip" style={{ marginBottom: "0.25rem" }}>
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
            </svg>
            Admin View
          </div>
          <h1 className="apple-case-title">{c.case_ref}</h1>
          <StatusBadge status={c.status} />
        </div>
        <p className="apple-case-meta">{c.applicant_ref} · {c.institution_ref} · {c.application_type_label}</p>
      </div>

      {/* Admin action bar */}
      <div className="admin-action-bar">
        {c.allowed_actions.includes("process") && c.documents.length > 0 && (
          <button className="btn btn-ghost" disabled={running}
            onClick={() => void run(c.status !== "received" && c.status !== "clarification_requested")}>
            <IconPlay width="13" height="13" />
            <span>{c.status === "processing_failed" ? "Retry checks" : c.status === "received" ? "Run checks" : "Re-run checks"}</span>
          </button>
        )}
        {c.allowed_actions.includes("reopen") && (
          <button className="btn btn-ghost admin-reopen-btn" onClick={() => setReopenOpen(true)}>
            <IconShield width="13" height="13" />
            <span>Reopen Case</span>
          </button>
        )}
        <button className="btn btn-ghost" onClick={() => navigate(`/cases/${c.id}/report`)}>
          <IconFileText width="13" height="13" />
          <span>Case report</span>
        </button>
      </div>

      {/* Status banners */}
      {c.status === "processing" && (
        <div className="apple-banner apple-banner-info" role="status">
          <Spinner label="Processing" />
          <span>Running checks — {c.latest_job?.progress ?? 0}%</span>
        </div>
      )}
      {c.status === "processing_failed" && (
        <div className="apple-banner apple-banner-error" role="alert">
          {c.latest_job?.error_message ?? "Checks could not finish."} Retry or upload clearer copies.
        </div>
      )}

      {/* Case info cards */}
      <div className="admin-case-grid">
        <div className="apple-card">
          <div className="apple-card-label">Documents</div>
          <ul className="apple-doc-list">
            {c.documents.length === 0 ? (
              <li className="muted small">No documents uploaded.</li>
            ) : c.documents.map((d) => (
              <li key={d.id} className="apple-doc-item">
                <span className="apple-doc-icon"><IconFileText width="16" height="16" /></span>
                <span className="apple-doc-name">{DOC_LABEL[d.doc_type] || d.doc_type}</span>
                <span className="apple-doc-filename">{d.original_name}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="apple-card">
          <div className="apple-card-label">Decisions</div>
          {c.decisions.length === 0 ? (
            <p className="muted small">No determinations recorded.</p>
          ) : c.decisions.map((d, i) => (
            <div key={i} className="admin-decision-item">
              <div className="admin-decision-outcome">{humanize(d.outcome)}</div>
              <div className="admin-decision-meta">{when(d.decided_at)} · {d.reviewer}</div>
              {d.note && <div className="admin-decision-note">"{d.note}"</div>}
            </div>
          ))}
        </div>
      </div>

      <ReopenDialog open={reopenOpen} caseId={c.id} onClose={(ok) => { setReopenOpen(false); if (ok) void reload(true); }} />
    </Layout>
  );
}

/* ── Reviewer case view ────────────────────────────────────────────────────── */
function ReviewerCaseView({ c, reload, running, run, reopenOpen, setReopenOpen }: {
  c: CaseDetail; reload: (s?: boolean) => Promise<void>;
  running: boolean; run: (force: boolean) => Promise<void>;
  reopenOpen: boolean; setReopenOpen: (v: boolean) => void;
}) {
  const [docId, setDocId] = useState<string | null>(c.documents[0]?.id ?? null);
  const [page, setPage] = useState(1);
  const [hl, setHl] = useState<Highlight | null>(null);
  const [sel, setSel] = useState<string | null>(null);
  const [tab, setTab] = useState<"fields" | "activity">("fields");
  const canReview = c.allowed_actions.includes("correct_field");

  useEffect(() => {
    if (!docId && c.documents[0]) setDocId(c.documents[0].id);
  }, [c, docId]);

  const goto = (d: string, p: number) => { setDocId(d); setPage(p); };

  const selectField = (f: Field) => {
    setSel(f.id); goto(f.document_id, f.page_number ?? 1);
    setHl({ documentId: f.document_id, page: f.page_number ?? 1, boxes: f.bbox ? [f.bbox] : [],
      label: `${f.label}: ${f.effective_value ?? "—"}`, tone: "field", isLlmSuggestion: f.source === "llm_suggestion" });
  };

  const selectFinding = (f: Finding, ref: EvidenceRef | null) => {
    setSel(f.id);
    if (!ref) { setHl(null); return; }
    const p = ref.page ?? 1; goto(ref.document_id, p);
    const boxes = f.evidence_refs.filter((r) => r.document_id === ref.document_id && (r.page ?? 1) === p && r.bbox).map((r) => r.bbox!);
    setHl({ documentId: ref.document_id, page: p, boxes, label: `${f.rule_id} ${f.summary}`, tone: f.severity });
  };

  return (
    <Layout wide>
      {/* Header */}
      <div className="case-head apple-case-head">
        <a href="#/cases" className="apple-back-btn">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M15 18l-6-6 6-6" />
          </svg>
          Review Queue
        </a>
        <div className="apple-case-title-row">
          <h1 className="apple-case-title">{c.case_ref}</h1>
          <StatusBadge status={c.status} />
        </div>
        <p className="apple-case-meta">{c.applicant_ref} · {c.institution_ref} · {c.application_type_label}</p>
        {/* Reviewer action strip */}
        <div className="reviewer-action-strip">
          {c.allowed_actions.includes("process") && c.documents.length > 0 && (
            <button className="btn btn-ghost" disabled={running}
              onClick={() => void run(c.status !== "received" && c.status !== "clarification_requested")}>
              <IconPlay width="13" height="13" />
              <span>{c.status === "processing_failed" ? "Retry" : c.status === "received" ? "Run checks" : "Re-run checks"}</span>
            </button>
          )}
          {c.allowed_actions.includes("reopen") && (
            <button className="btn btn-ghost" onClick={() => setReopenOpen(true)}>
              <IconShield width="13" height="13" />
              <span>Reopen</span>
            </button>
          )}
          <button className="btn btn-ghost" onClick={() => navigate(`/cases/${c.id}/report`)}>
            <IconFileText width="13" height="13" />
            <span>Case report</span>
          </button>
        </div>
      </div>

      {/* Status banners */}
      {c.status === "processing" && (
        <div className="apple-banner apple-banner-info" role="status">
          <Spinner label="Running checks" />
          <span>Reading documents and evaluating {c.ruleset.name} v{c.ruleset.version}… {c.latest_job?.progress ?? 0}%</span>
        </div>
      )}
      {c.status === "processing_failed" && (
        <div className="apple-banner apple-banner-error" role="alert">
          {c.latest_job?.error_message ?? "Checks could not finish."} Upload clearer copies if needed, then retry.
        </div>
      )}

      {/* AI advisory summary */}
      {c.summary && c.status !== "processing" && (
        <div className="reviewer-summary">
          <div className="reviewer-summary-label">
            {c.summary.kind === "llm" ? (
              <>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                </svg>
                AI-assisted summary · advisory only
              </>
            ) : "Automated summary"}
          </div>
          <p className="reviewer-summary-text">{c.summary.text}</p>
        </div>
      )}
      {c.ruleset.is_provisional && (
        <p className="provisional">Ruleset: {c.ruleset.name} v{c.ruleset.version} · Prototype specification</p>
      )}

      {/* Main review pane */}
      {c.documents.length === 0 ? (
        <div className="apple-card">
          <div className="apple-card-label">No Documents Uploaded</div>
          <p className="muted">Upload application documents to begin automated extraction and policy evaluation.</p>
          {c.allowed_actions.includes("upload") && (
            <Uploader caseId={c.id} existing={[]} onUploaded={() => void reload(true)} applicationType={c.application_type} />
          )}
        </div>
      ) : (
        <div className="review">
          <EvidenceViewer documents={c.documents} activeDocId={docId} page={page} highlight={hl} onNavigate={goto} />

          <section className="pane" aria-label="Extracted values and activity">
            <div className="pane-tabs" role="tablist">
              <button role="tab" aria-selected={tab === "fields"} onClick={() => setTab("fields")}>
                Extracted Values <span className="n">{c.fields.length}</span>
              </button>
              <button role="tab" aria-selected={tab === "activity"} onClick={() => setTab("activity")}>
                Audit Activity <span className="n">{c.audit.length}</span>
              </button>
            </div>
            <div className="pane-body">
              {tab === "fields" ? (
                <FieldTable fields={c.fields} canEdit={canReview} selectedId={sel} onSelect={selectField} onChanged={() => void reload(true)} />
              ) : (
                <AuditTimeline events={c.audit} caseId={c.id} />
              )}
            </div>
          </section>

          <section className="pane" aria-label="Findings">
            <div className="pane-tabs">
              <h2 className="pane-title">
                Findings <span className="n">{c.findings.filter((f) => f.status === "open").length} open</span>
              </h2>
            </div>
            <div className="pane-body">
              <FindingsPanel
                findings={c.findings}
                canAct={canReview}
                selectedId={sel}
                onSelect={selectFinding}
                onChanged={() => void reload(true)}
                evaluationSummary={c.evaluation_summary}
                ruleset={c.ruleset}
                applicationType={c.application_type}
              />
            </div>
          </section>
        </div>
      )}

      {/* Upload clarification */}
      {c.allowed_actions.includes("upload") && c.documents.length > 0 && c.status === "clarification_requested" && (
        <details className="apple-card" style={{ marginTop: "1rem" }}>
          <summary style={{ fontWeight: 600, cursor: "pointer" }}>Add or replace documents</summary>
          <Uploader caseId={c.id} existing={c.documents} onUploaded={() => void reload(true)} applicationType={c.application_type} />
        </details>
      )}

      {/* Last decision */}
      {c.decisions[0] && (
        <p className="last-decision">
          Last determination: <strong>{humanize(c.decisions[0].outcome)}</strong> ({humanize(c.decisions[0].reason_code)}) by {c.decisions[0].reviewer}, {when(c.decisions[0].decided_at)}
          {c.decisions[0].note ? ` — "${c.decisions[0].note}"` : ""}
        </p>
      )}

      <DecisionBar c={c as CaseDetail} onDecided={() => void reload(true)} />
      <ReopenDialog open={reopenOpen} caseId={c.id} onClose={(ok) => { setReopenOpen(false); if (ok) void reload(true); }} />
    </Layout>
  );
}

/* ── Root CasePage ────────────────────────────────────────────────────────── */
export function CasePage({ id }: { id: string }) {
  const { user } = useSession();
  const toast = useToast();
  const { data: c, error, loading, reload } = useAsync(() => api.getCase(id), [id]);
  const [running, setRunning] = useState(false);
  const [reopenOpen, setReopenOpen] = useState(false);

  // Poll while checks are running with exponential back-off
  useEffect(() => {
    if (c?.status !== "processing") return;
    let delay = 1200;
    let timer: ReturnType<typeof setTimeout>;
    const poll = () => {
      timer = setTimeout(() => {
        void reload(true);
        delay = Math.min(Math.round(delay * 1.5), 5000);
        poll();
      }, delay);
    };
    poll();
    return () => clearTimeout(timer);
  }, [c?.status, reload]);

  if (error)
    return (
      <Layout>
        <PageState
          title={error.status === 404 ? "Case not found" : "The case could not be loaded"}
          action={<button className="btn" onClick={() => navigate("/cases")}>Back to queue</button>}
        >
          {errorText(error)}
        </PageState>
      </Layout>
    );

  if (loading && !c)
    return <Layout><div className="center"><Spinner /></div></Layout>;

  if (!c) return null;

  const run = async (force: boolean) => {
    setRunning(true);
    try {
      await api.process(c.id, force);
      toast("Checks started.");
      await reload(true);
    } catch (e) {
      toast(errorText(e), "error");
    } finally {
      setRunning(false);
    }
  };

  const role = user?.role;

  if (role === "applicant") {
    return <ApplicantCaseView c={c} reload={reload} reopenOpen={reopenOpen} setReopenOpen={setReopenOpen} />;
  }

  if (role === "admin") {
    return <AdminCaseView c={c} reload={reload} running={running} run={run} reopenOpen={reopenOpen} setReopenOpen={setReopenOpen} />;
  }

  // reviewer (default)
  return (
    <ReviewerCaseView
      c={c} reload={reload} running={running} run={run}
      reopenOpen={reopenOpen} setReopenOpen={setReopenOpen}
    />
  );
}
