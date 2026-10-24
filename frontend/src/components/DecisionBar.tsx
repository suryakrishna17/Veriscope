import { useState } from "react";
import { api } from "../api/client";
import type { CaseDetail } from "../api/types";
import { humanize } from "../lib/format";
import { errorText } from "../lib/hooks";
import { useSession } from "../lib/session";
import { useToast } from "../lib/toast";
import { IconAlert, IconCheck, IconShield } from "./Icons";
import { Modal } from "./Modal";

type Outcome = "approve" | "request_clarification" | "reject";
const LABEL: Record<Outcome, string> = {
  approve: "Approve application",
  request_clarification: "Request clarification",
  reject: "Reject application",
};
const DONE: Record<Outcome, string> = {
  approve: "Case approved.",
  request_clarification: "Clarification request sent to the applicant.",
  reject: "Case outcome recorded as rejected.",
};

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

  const start = (o: Outcome) => {
    setOutcome(o);
    if (o === "request_clarification") {
      setReason("DATA_MISMATCH");
      const openFindings = c.findings.filter((f) => f.status === "open");
      const list = openFindings
        .map((f, i) => `${i + 1}. [${f.rule_id}] ${f.summary}: ${f.next_action || f.detail}`)
        .join("\n");
      setNote(
        `Dear Applicant / Institution Registrar,\n\nDuring the automated AICTE regulatory compliance evaluation of application ${c.case_ref}, the following item(s) require official clarification:\n\n${list}\n\nPlease upload the rectified registered documents through the institution portal within 7 working days.`
      );
    } else {
      setReason("");
      setNote("");
    }
    setErr(null);
  };

  const submit = async () => {
    if (!outcome) return;
    setBusy(true);
    setErr(null);
    try {
      await api.decide(c.id, outcome, reason, note);
      toast(DONE[outcome]);
      setOutcome(null);
      onDecided();
    } catch (e) {
      setErr(errorText(e));
    } finally {
      setBusy(false);
    }
  };

  const needsNote = outcome === "reject" || outcome === "request_clarification";

  return (
    <div className="decision-bar" role="region" aria-label="Review determination bar">
      <div className="decision-status">
        {openAll.length === 0 ? (
          <span style={{ color: "var(--ok)", display: "inline-flex", alignItems: "center", gap: "0.4rem" }}>
            <IconCheck width="16" height="16" />
            All findings are resolved or waived.
          </span>
        ) : (
          <span>
            <strong>{openAll.length}</strong> open finding(s)
            {openHigh.length > 0 && (
              <span style={{ color: "var(--high)" }}> ({openHigh.length} high severity)</span>
            )}
            .
            {openHigh.length > 0 && (
              <span className="muted"> All high-severity findings must be resolved or waived before approval.</span>
            )}
          </span>
        )}
      </div>

      <div className="decision-actions">
        <button className="btn btn-ghost" onClick={() => start("request_clarification")}>
          <IconAlert width="14" height="14" />
          <span>Request clarification</span>
        </button>

        <button className="btn btn-danger-ghost" onClick={() => start("reject")}>
          <IconShield width="14" height="14" />
          <span>Reject</span>
        </button>

        <button
          className="btn btn-primary"
          onClick={() => start("approve")}
          disabled={openHigh.length > 0}
          title={openHigh.length ? "Resolve or waive high-severity findings first" : "Record approval decision"}
        >
          <IconCheck width="14" height="14" />
          <span>Approve</span>
        </button>
      </div>

      {outcome && (
        <Modal
          open
          title={LABEL[outcome]}
          onClose={() => setOutcome(null)}
          footer={
            <>
              <button className="btn btn-ghost" onClick={() => setOutcome(null)}>Cancel</button>
              <button
                className={outcome === "reject" ? "btn btn-danger" : "btn btn-primary"}
                disabled={busy || !reason || (needsNote && note.trim().length < 5)}
                onClick={() => void submit()}
              >
                {busy ? "Saving determination…" : LABEL[outcome]}
              </button>
            </>
          }
        >
          {openAll.length > 0 && (
            <div className="callout">
              <strong>{openAll.length} finding(s) remain open:</strong>
              <ul>
                {openAll.slice(0, 5).map((f) => (
                  <li key={f.id}>{f.rule_id}: {f.summary}</li>
                ))}
              </ul>
            </div>
          )}

          <label className="stack">
            <span>Official Reason Code</span>
            <select value={reason} onChange={(e) => setReason(e.target.value)} required>
              <option value="">Select official reason</option>
              {(meta?.reason_codes[outcome] ?? []).map((r) => (
                <option key={r} value={r}>{humanize(r)}</option>
              ))}
            </select>
          </label>

          <label className="stack">
            <span>
              {outcome === "request_clarification" ? "Instructions to Applicant" : "Reviewer Determination Note"}
              {needsNote ? "" : " (optional)"}
            </span>
            <textarea
              rows={3}
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder={
                outcome === "request_clarification"
                  ? "e.g. Please provide an updated registered Land Sale Deed showing parcel survey numbers."
                  : "Recorded permanently in the immutable audit log and inspection dossier."
              }
            />
          </label>

          <p className="muted small">
            You are recording an official reviewer determination. Your authenticated identity and timestamp will be logged.
          </p>

          {err && <p className="inline-error">{err}</p>}
        </Modal>
      )}
    </div>
  );
}
