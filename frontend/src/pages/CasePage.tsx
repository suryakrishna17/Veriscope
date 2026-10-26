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

export function CasePage({ id }: { id: string }) {
  const { user } = useSession();
  const toast = useToast();
  const { data: c, error, loading, reload } = useAsync(() => api.getCase(id), [id]);
  const [docId, setDocId] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [hl, setHl] = useState<Highlight | null>(null);
  const [sel, setSel] = useState<string | null>(null);
  const [tab, setTab] = useState<"fields" | "activity">("fields");
  const [running, setRunning] = useState(false);
  const [reopenOpen, setReopenOpen] = useState(false);

  // Poll while checks are running, with exponential back-off to avoid hammering
  // the server during long OCR jobs (caps at 5 s).
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

  useEffect(() => {
    if (c && !docId && c.documents[0]) setDocId(c.documents[0].id);
  }, [c, docId]);

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
    return (
      <Layout>
        <div className="center"><Spinner /></div>
      </Layout>
    );

  if (!c) return null;

  const isReviewer = user?.role !== "applicant";
  const canReview = c.allowed_actions.includes("correct_field");

  const goto = (d: string, p: number) => {
    setDocId(d);
    setPage(p);
  };

  const selectField = (f: Field) => {
    setSel(f.id);
    goto(f.document_id, f.page_number ?? 1);
    setHl({
      documentId: f.document_id,
      page: f.page_number ?? 1,
      boxes: f.bbox ? [f.bbox] : [],
      label: `${f.label}: ${f.effective_value ?? "—"}`,
      tone: "field",
      isLlmSuggestion: f.source === "llm_suggestion",
    });
  };

  const selectFinding = (f: Finding, ref: EvidenceRef | null) => {
    setSel(f.id);
    if (!ref) {
      setHl(null);
      return;
    }
    const p = ref.page ?? 1;
    goto(ref.document_id, p);
    const boxes = f.evidence_refs
      .filter((r) => r.document_id === ref.document_id && (r.page ?? 1) === p && r.bbox)
      .map((r) => r.bbox!);
    setHl({
      documentId: ref.document_id,
      page: p,
      boxes,
      label: `${f.rule_id} ${f.summary}`,
      tone: f.severity,
    });
  };

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

  const header = (
    <div className="case-head">
      <a href="#/cases" className="back">← {isReviewer ? "Back to Review Queue" : "Back to My Applications"}</a>
      <div className="case-title">
        <h1>{c.case_ref}</h1>
        <StatusBadge status={c.status} />
      </div>
      <p className="muted">
        <strong>{c.applicant_ref}</strong> · {c.institution_ref} · {c.application_type_label}
      </p>
      <div className="case-actions">
        {c.allowed_actions.includes("process") && c.documents.length > 0 && (
          <button
            className="btn btn-ghost"
            disabled={running}
            onClick={() => void run(c.status !== "received" && c.status !== "clarification_requested")}
          >
            <IconPlay width="13" height="13" />
            <span>
              {c.status === "processing_failed"
                ? "Retry checks"
                : c.status === "received" || c.status === "clarification_requested"
                ? "Run checks"
                : "Re-run checks"}
            </span>
          </button>
        )}
        {c.allowed_actions.includes("reopen") && (
          <button className="btn btn-ghost" onClick={() => setReopenOpen(true)}>
            <IconShield width="13" height="13" />
            <span>Reopen case</span>
          </button>
        )}
        <button className="btn btn-ghost" onClick={() => navigate(`/cases/${c.id}/report`)}>
          <IconFileText width="13" height="13" />
          <span>Case report</span>
        </button>
      </div>
    </div>
  );

  const processingBanner = c.status === "processing" && (
    <div className="banner banner-info" role="status">
      <Spinner label="Running checks" />
      <span>Reading documents and evaluating {c.ruleset.name} v{c.ruleset.version}… {c.latest_job?.progress ?? 0}%</span>
    </div>
  );

  const failedBanner = c.status === "processing_failed" && (
    <div className="banner banner-error" role="alert">
      {c.latest_job?.error_message ?? "Checks could not finish."} Upload clearer copies if needed, then retry.
    </div>
  );

  const clarification = c.decisions.find((d) => d.outcome === "request_clarification");

  if (!isReviewer) {
    return (
      <Layout>
        {header}
        {processingBanner}
        {failedBanner}
        {c.status === "clarification_requested" && clarification && (
          <div className="banner banner-warn">
            <strong>The reviewer requested additional information:</strong> {clarification.note} Upload the requested documents below, then re-run checks.
          </div>
        )}
        {c.decisions[0] && c.status !== "clarification_requested" && (
          <div className="card">
            <h2>Official Determination</h2>
            <p>{humanize(c.decisions[0].outcome)} on {when(c.decisions[0].decided_at)}. {c.decisions[0].note}</p>
          </div>
        )}
        <div className="card">
          <h2>Application Documents</h2>
          {c.allowed_actions.includes("upload") ? (
            <Uploader
              caseId={c.id}
              existing={c.documents}
              onUploaded={() => void reload(true)}
              applicationType={c.application_type}
            />
          ) : (
            <ul className="doc-list">
              {c.documents.map((d) => (
                <li key={d.id}>{(DOC_LABEL[d.doc_type] || d.doc_type)} · {d.original_name}</li>
              ))}
            </ul>
          )}
        </div>
        <ReopenDialog open={reopenOpen} caseId={c.id} onClose={(ok) => { setReopenOpen(false); if (ok) void reload(true); }} />
      </Layout>
    );
  }

  return (
    <Layout wide>
      {header}
      {processingBanner}
      {failedBanner}
      {c.summary && c.status !== "processing" && (
        <div className="summary">
          <span className="summary-kind">{c.summary.kind === "llm" ? "AI-assisted summary · advisory" : "Automated summary"}</span>
          <p>{c.summary.text}</p>
        </div>
      )}
      {c.ruleset.is_provisional && (
        <p className="provisional">Ruleset: {c.ruleset.name} v{c.ruleset.version} · Prototype specification</p>
      )}

      {c.documents.length === 0 ? (
        <div className="card">
          <h2>No documents uploaded</h2>
          <p className="muted">Upload the application documents to begin automated extraction and policy evaluation.</p>
          {c.allowed_actions.includes("upload") && (
            <Uploader
              caseId={c.id}
              existing={[]}
              onUploaded={() => void reload(true)}
              applicationType={c.application_type}
            />
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
                <FieldTable
                  fields={c.fields}
                  canEdit={canReview}
                  selectedId={sel}
                  onSelect={selectField}
                  onChanged={() => void reload(true)}
                />
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

      {c.allowed_actions.includes("upload") && c.documents.length > 0 && c.status === "clarification_requested" && (
        <details className="card" style={{ marginTop: "1rem" }}>
          <summary style={{ fontWeight: 600, cursor: "pointer" }}>Add or replace documents</summary>
          <Uploader
            caseId={c.id}
            existing={c.documents}
            onUploaded={() => void reload(true)}
            applicationType={c.application_type}
          />
        </details>
      )}

      {c.decisions[0] && (
        <p className="last-decision">
          Last determination: <strong>{humanize(c.decisions[0].outcome)}</strong> ({humanize(c.decisions[0].reason_code)}) by {c.decisions[0].reviewer}, {when(c.decisions[0].decided_at)}
          {c.decisions[0].note ? ` — “${c.decisions[0].note}”` : ""}
        </p>
      )}

      <DecisionBar c={c as CaseDetail} onDecided={() => void reload(true)} />
      <ReopenDialog open={reopenOpen} caseId={c.id} onClose={(ok) => { setReopenOpen(false); if (ok) void reload(true); }} />
    </Layout>
  );
}

function ReopenDialog({ open, caseId, onClose }: { open: boolean; caseId: string; onClose: (ok: boolean) => void }) {
  const [note, setNote] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const toast = useToast();

  const submit = async () => {
    try {
      await api.reopen(caseId, note);
      toast("Case reopened for review.");
      onClose(true);
    } catch (e) {
      setErr(errorText(e));
    }
  };

  if (!open) return null;

  return (
    <Modal
      open
      title="Reopen Case for Review"
      onClose={() => onClose(false)}
      footer={
        <>
          <button className="btn btn-ghost" onClick={() => onClose(false)}>Cancel</button>
          <button className="btn btn-primary" disabled={note.trim().length < 5} onClick={() => void submit()}>
            Confirm Reopening
          </button>
        </>
      }
    >
      <label className="stack">
        <span>Reason for reopening</span>
        <textarea
          rows={3}
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="e.g. New land ownership documentation submitted by applicant."
        />
      </label>
      {err && <p className="inline-error">{err}</p>}
    </Modal>
  );
}
