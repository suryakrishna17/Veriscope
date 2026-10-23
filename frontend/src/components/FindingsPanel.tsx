import { useState } from "react";
import { api } from "../api/client";
import type { EvidenceRef, Finding } from "../api/types";
import { DOC_LABEL, when } from "../lib/format";
import { errorText } from "../lib/hooks";
import { useToast } from "../lib/toast";
import { SeverityTag } from "./Badges";
import { Modal } from "./Modal";

interface Props {
  findings: Finding[];
  canAct: boolean;
  selectedId: string | null;
  onSelect: (f: Finding, ref: EvidenceRef | null) => void;
  onChanged: () => void;
}

export function FindingsPanel({ findings, canAct, selectedId, onSelect, onChanged }: Props) {
  const [acting, setActing] = useState<{ f: Finding; to: Finding["status"] } | null>(null);
  const open = findings.filter((f) => f.status === "open");
  const closed = findings.filter((f) => f.status !== "open");

  if (!findings.length)
    return (
      <div className="pad">
        <p className="clear-msg">No findings. Every automated check passed.</p>
        <p className="muted small">This does not mean the documents were confirmed by their issuers.</p>
      </div>
    );

  return (
    <div className="findings">
      <ul className="finding-list">
        {open.map((f) => (
          <FindingCard key={f.id} f={f} selected={selectedId === f.id} canAct={canAct} onSelect={onSelect} onAct={(to) => setActing({ f, to })} />
        ))}
      </ul>
      {closed.length > 0 && (
        <details className="closed">
          <summary>{closed.length} resolved or waived</summary>
          <ul className="finding-list">
            {closed.map((f) => (
              <FindingCard key={f.id} f={f} selected={selectedId === f.id} canAct={canAct} onSelect={onSelect} onAct={(to) => setActing({ f, to })} />
            ))}
          </ul>
        </details>
      )}
      {acting && <ResolveDialog finding={acting.f} to={acting.to} onClose={(saved) => { setActing(null); if (saved) onChanged(); }} />}
    </div>
  );
}

function FindingCard({ f, selected, canAct, onSelect, onAct }: {
  f: Finding; selected: boolean; canAct: boolean;
  onSelect: (f: Finding, ref: EvidenceRef | null) => void; onAct: (to: Finding["status"]) => void;
}) {
  const located = f.evidence_refs.filter((r) => r.page);
  return (
    <li className={`finding finding-${f.severity} ${selected ? "is-selected" : ""} ${f.status !== "open" ? "is-closed" : ""}`}>
      <button className="finding-main" onClick={() => onSelect(f, located[0] ?? f.evidence_refs[0] ?? null)} aria-pressed={selected}>
        <span className="finding-top">
          <SeverityTag severity={f.severity} />
          <span className="rule">{f.rule_id} · v{f.rule_version}</span>
          {f.status !== "open" && <span className="pill">{f.status === "resolved" ? "Resolved" : "Waived"}</span>}
        </span>
        <span className="finding-title">{f.summary}</span>
        <span className="finding-detail">{f.detail}</span>
      </button>
      {f.evidence_refs.length > 0 && (
        <div className="evidence-chips" aria-label="Evidence">
          {f.evidence_refs.map((r, i) => (
            <button key={i} className="chip" onClick={() => onSelect(f, r)} disabled={!r.page && !r.document_id}>
              {r.doc_type ? DOC_LABEL[r.doc_type] : "Document"}{r.page ? ` · p.${r.page}` : ""}{r.value ? ` · ${r.value}` : ""}
            </button>
          ))}
        </div>
      )}
      {f.status === "open" && f.next_action && <p className="next">Next step: {f.next_action}</p>}
      {f.status !== "open" && f.resolution_note && (
        <p className="resolution">“{f.resolution_note}” — {f.resolved_by}, {when(f.resolved_at)}</p>
      )}
      {canAct && (
        <div className="finding-actions">
          {f.status === "open" ? (
            <>
              <button className="btn btn-small" onClick={() => onAct("resolved")}>Mark resolved</button>
              <button className="btn btn-small btn-ghost" onClick={() => onAct("waived")}>Waive</button>
            </>
          ) : (
            <button className="btn btn-small btn-ghost" onClick={() => onAct("open")}>Reopen finding</button>
          )}
        </div>
      )}
    </li>
  );
}

function ResolveDialog({ finding, to, onClose }: { finding: Finding; to: Finding["status"]; onClose: (saved: boolean) => void }) {
  const toast = useToast();
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const verb = to === "resolved" ? "Mark resolved" : to === "waived" ? "Waive finding" : "Reopen finding";
  const submit = async () => {
    setBusy(true); setErr(null);
    try {
      await api.updateFinding(finding.id, to, note);
      toast(to === "open" ? "Finding reopened." : to === "resolved" ? "Finding marked resolved." : "Finding waived.");
      onClose(true);
    } catch (e) { setErr(errorText(e)); setBusy(false); }
  };
  return (
    <Modal open title={verb} onClose={() => onClose(false)} footer={
      <>
        <button className="btn btn-ghost" onClick={() => onClose(false)}>Cancel</button>
        <button className="btn btn-primary" disabled={busy || (to !== "open" && note.trim().length < 5)} onClick={() => void submit()}>{busy ? "Saving…" : verb}</button>
      </>
    }>
      <p><strong>{finding.rule_id}</strong> {finding.summary}</p>
      {to !== "open" && (
        <label className="stack">
          <span>{to === "resolved" ? "What did you check?" : "Why is it acceptable to waive this?"}</span>
          <textarea rows={3} value={note} onChange={(e) => setNote(e.target.value)} placeholder="This note is saved to the audit trail and the case report." />
        </label>
      )}
      {err && <p className="inline-error">{err}</p>}
    </Modal>
  );
}
