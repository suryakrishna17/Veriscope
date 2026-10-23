import { useState } from "react";
import { api } from "../api/client";
import type { CaseDetail } from "../api/types";
import { humanize } from "../lib/format";
import { errorText } from "../lib/hooks";
import { useSession } from "../lib/session";
import { useToast } from "../lib/toast";
import { Modal } from "./Modal";

type Outcome = "approve" | "request_clarification" | "reject";
const LABEL: Record<Outcome, string> = { approve: "Approve", request_clarification: "Request clarification", reject: "Reject" };
const DONE: Record<Outcome, string> = { approve: "Case approved.", request_clarification: "Clarification requested from the applicant.", reject: "Case rejected." };

export function DecisionBar({ c, onDecided }: { c: CaseDetail; onDecided: () => void }) {
  const { meta } = useSession();
  const toast = useToast();
  const [outcome, setOutcome] = useState<Outcome | null>(null);
  const [reason, setReason] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const openHigh = c.findings.filter((f) => f.status === "open" && f.severity === "high");
  const openAll = c.findings.filter((f) => f.status === "open");
  const can = (a: Outcome) => c.allowed_actions.includes(a);
  if (!can("approve") && !can("reject")) return null;

  const start = (o: Outcome) => { setOutcome(o); setReason(""); setNote(""); setErr(null); };
  const submit = async () => {
    if (!outcome) return;
    setBusy(true); setErr(null);
    try {
      await api.decide(c.id, outcome, reason, note);
      toast(DONE[outcome]);
      setOutcome(null);
      onDecided();
    } catch (e) { setErr(errorText(e)); } finally { setBusy(false); }
  };
  const needsNote = outcome === "reject" || outcome === "request_clarification";

  return (
    <div className="decision-bar" role="region" aria-label="Decision">
      <div className="decision-status">
        {openAll.length === 0 ? "All findings are resolved or waived." : `${openAll.length} open finding(s)${openHigh.length ? `, ${openHigh.length} high severity` : ""}.`}
        {openHigh.length > 0 && <span className="muted"> Approval needs every high-severity finding resolved or waived.</span>}
      </div>
      <div className="decision-actions">
        <button className="btn btn-ghost" onClick={() => start("request_clarification")}>Request clarification</button>
        <button className="btn btn-danger-ghost" onClick={() => start("reject")}>Reject</button>
        <button className="btn btn-primary" onClick={() => start("approve")} disabled={openHigh.length > 0} title={openHigh.length ? "Resolve or waive high-severity findings first" : undefined}>Approve</button>
      </div>
      {outcome && (
        <Modal open title={LABEL[outcome]} onClose={() => setOutcome(null)} footer={
          <>
            <button className="btn btn-ghost" onClick={() => setOutcome(null)}>Cancel</button>
            <button className={outcome === "reject" ? "btn btn-danger" : "btn btn-primary"} disabled={busy || !reason || (needsNote && note.trim().length < 5)} onClick={() => void submit()}>
              {busy ? "Saving…" : LABEL[outcome]}
            </button>
          </>
        }>
          {openAll.length > 0 && (
            <div className="callout">
              <strong>{openAll.length} finding(s) are still open.</strong>
              <ul>{openAll.slice(0, 5).map((f) => <li key={f.id}>{f.rule_id}: {f.summary}</li>)}</ul>
            </div>
          )}
          <label className="stack">
            <span>Reason</span>
            <select value={reason} onChange={(e) => setReason(e.target.value)} required>
              <option value="">Choose a reason</option>
              {(meta?.reason_codes[outcome] ?? []).map((r) => <option key={r} value={r}>{humanize(r)}</option>)}
            </select>
          </label>
          <label className="stack">
            <span>{outcome === "request_clarification" ? "Message to the applicant" : "Note"}{needsNote ? "" : " (optional)"}</span>
            <textarea rows={3} value={note} onChange={(e) => setNote(e.target.value)} placeholder={outcome === "request_clarification" ? "e.g. Upload a signed copy of the application form." : "Recorded in the audit trail and report."} />
          </label>
          <p className="muted small">You are recording a human decision. It is saved with your name and the current findings.</p>
          {err && <p className="inline-error">{err}</p>}
        </Modal>
      )}
    </div>
  );
}
