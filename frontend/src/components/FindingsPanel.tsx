import { useMemo, useState } from "react";
import { api } from "../api/client";
import type { EvaluationSummary, EvidenceRef, Finding, Severity } from "../api/types";
import { DOC_LABEL, humanize, when } from "../lib/format";
import { errorText } from "../lib/hooks";
import { useToast } from "../lib/toast";
import { SeverityTag } from "./Badges";
import { IconCheck, IconEye } from "./Icons";
import { Modal } from "./Modal";

const APH_CITATIONS: Record<string, string> = {
  "CMP-001": "AICTE APH 2024-27 Clause 1.4.3 & Annexure-1 §1.1(ii), p. 4, 77",
  "CMP-002": "AICTE APH 2024-27 Clause 1.8(d) & Annexure-1 §1.1, p. 7, 77",
  "CMP-003": "AICTE APH 2024-27 Clause 1.4.3 & Clause 7.4(a), p. 4, 71",
  "CMP-004": "AICTE APH 2024-27 Clause 1.4.4 & Affidavit-2, p. 4, 186",
  "CMP-005": "AICTE APH 2024-27 Clause 6.14(n) & Annexure-8, p. 55, 101",
  "FMT-001": "AICTE APH 2024-27 Clause 1.4.1(d) & Clause 2.3.1, p. 2, 12",
  "FMT-002": "AICTE APH 2024-27 Clause 1.4.1 & Annexure-18 §18.1, p. 2, 180",
  "DAT-001": "AICTE APH 2024-27 Clause 1.2(b) & Clause 2.2, p. 1, 12",
  "DAT-002": "AICTE APH 2024-27 Chapter II, Clause 2.1 & 2.3, p. 11, 12",
  "ARI-001": "AICTE APH 2024-27 Chapter VI, Clause 6.34 & 6.42(c), p. 58, 59",
  "CON-001": "AICTE APH 2024-27 Clause 1.5.4 & Format-2 / Format-3, p. 5, 202, 205",
  "CON-002": "AICTE APH 2024-27 Annexure-8 & Annexure-18 §18.16, p. 101, 184",
  "CON-003": "AICTE APH 2024-27 Clause 1.4.1 & Clause 2.3.1, p. 2, 12",
  "SIG-001": "AICTE APH 2024-27 Chapter VII, Clause 7.4(a) & 1.5.5, p. 71, 5",
  "SIG-002": "AICTE APH 2024-27 Clause 1.4.3 & Clause 7.4(a), p. 4, 71",
  "SIG-003": "AICTE APH 2024-27 Clause 1.8(d) & Clause 2.28, p. 7, 32",
  "SIG-004": "AICTE APH 2024-27 Format-1, Format-2 & Certificate-1/2/3, p. 201, 202, 210",
};

interface Props {
  findings: Finding[];
  canAct: boolean;
  selectedId: string | null;
  onSelect: (f: Finding, ref: EvidenceRef | null) => void;
  onChanged: () => void;
  evaluationSummary?: EvaluationSummary | null;
  ruleset?: { name: string; version: string; is_provisional: boolean };
  applicationType?: string;
}

function EvaluationSummaryBanner({
  summary,
  ruleset,
  applicationType,
}: {
  summary?: EvaluationSummary | null;
  ruleset?: { name: string; version: string; is_provisional: boolean };
  applicationType?: string;
}) {
  if (!summary) return null;

  const isEoa = applicationType === "AICTE_EOA" || summary.ruleset_name?.includes("eoa");
  const title = isEoa
    ? "AICTE EoA Regulatory Audit Summary (APH 2024-27 Chapter II)"
    : `${ruleset?.name || "Regulatory"} Evaluation Summary`;

  return (
    <div className="eval-summary-card" role="region" aria-label="Evaluation summary">
      <div className="eval-summary-head">
        <span className="eval-summary-title">📜 {title}</span>
        <span className="eval-summary-total">Total Evaluated: {summary.total} Rules</span>
      </div>
      <div className="eval-badges-grid">
        <div className="eval-badge eval-badge-pass" title="Passing statutory checks">
          <span className="eval-badge-val">{summary.pass}</span>
          <span className="eval-badge-lbl">PASS</span>
        </div>
        <div className="eval-badge eval-badge-fail" title="Active statutory deficiencies">
          <span className="eval-badge-val">{summary.fail}</span>
          <span className="eval-badge-lbl">FAIL</span>
        </div>
        <div className="eval-badge eval-badge-review" title="Checks requiring human reviewer scrutiny">
          <span className="eval-badge-val">{summary.review_required}</span>
          <span className="eval-badge-lbl">REVIEW REQUIRED</span>
        </div>
        <div className="eval-badge eval-badge-na" title="Statutory rules not applicable to this dossier">
          <span className="eval-badge-val">{summary.not_applicable}</span>
          <span className="eval-badge-lbl">NOT APPLICABLE</span>
        </div>
      </div>
    </div>
  );
}

function isSelfDisclosure(f: Finding): boolean {
  return (
    f.rule_id.startsWith("EOA-COM-") ||
    f.rule_id === "ARI-001" ||
    f.rule_id === "CMP-004" ||
    f.summary.toLowerCase().includes("committee") ||
    f.summary.toLowerCase().includes("self-disclosure") ||
    f.detail.toLowerCase().includes("self-disclosure")
  );
}

export function FindingsPanel({
  findings,
  canAct,
  selectedId,
  onSelect,
  onChanged,
  evaluationSummary,
  ruleset,
  applicationType,
}: Props) {
  const [acting, setActing] = useState<{ f: Finding; to: Finding["status"] } | null>(null);
  const [filterSev, setFilterSev] = useState<string>("all");

  const open = useMemo(() => findings.filter((f) => f.status === "open"), [findings]);
  const closed = useMemo(() => findings.filter((f) => f.status !== "open"), [findings]);

  const filteredOpen = useMemo(() => {
    if (filterSev === "all") return open;
    return open.filter((f) => f.severity === filterSev);
  }, [open, filterSev]);

  if (!findings.length) {
    return (
      <div className="pad">
        <EvaluationSummaryBanner
          summary={evaluationSummary}
          ruleset={ruleset}
          applicationType={applicationType}
        />
        <p className="clear-msg">No findings recorded. Every automated rule check passed.</p>
        <p className="muted small">This does not mean documents have been confirmed by their issuers.</p>
      </div>
    );
  }

  return (
    <div className="findings">
      <EvaluationSummaryBanner
        summary={evaluationSummary}
        ruleset={ruleset}
        applicationType={applicationType}
      />
      {open.length > 0 && (
        <div style={{ padding: "0.5rem 1rem", display: "flex", gap: "0.35rem", borderBottom: "1px solid var(--line-2)" }}>
          {(["all", "high", "medium", "low"] as const).map((s) => {
            const count = s === "all" ? open.length : open.filter((f) => f.severity === s).length;
            if (s !== "all" && count === 0) return null;
            return (
              <button
                key={s}
                className="btn btn-small"
                style={{
                  fontSize: "0.74rem",
                  padding: "0.15rem 0.5rem",
                  background: filterSev === s ? "var(--ink)" : "var(--surface)",
                  color: filterSev === s ? "var(--paper)" : "var(--ink-2)",
                  borderColor: filterSev === s ? "var(--ink)" : "var(--line)",
                }}
                onClick={() => setFilterSev(s)}
              >
                {s.toUpperCase()} ({count})
              </button>
            );
          })}
        </div>
      )}

      <ul className="finding-list">
        {filteredOpen.map((f) => (
          <FindingCard
            key={f.id}
            f={f}
            selected={selectedId === f.id}
            canAct={canAct}
            onSelect={onSelect}
            onAct={(to) => setActing({ f, to })}
          />
        ))}
        {filteredOpen.length === 0 && open.length > 0 && (
          <li style={{ padding: "1.5rem 1rem", textAlign: "center", color: "var(--ink-3)", fontSize: "0.85rem" }}>
            No open findings matching filter.
          </li>
        )}
      </ul>

      {closed.length > 0 && (
        <details className="closed">
          <summary>{closed.length} resolved or waived finding(s)</summary>
          <ul className="finding-list">
            {closed.map((f) => (
              <FindingCard
                key={f.id}
                f={f}
                selected={selectedId === f.id}
                canAct={canAct}
                onSelect={onSelect}
                onAct={(to) => setActing({ f, to })}
              />
            ))}
          </ul>
        </details>
      )}

      {acting && (
        <ResolveDialog
          finding={acting.f}
          to={acting.to}
          onClose={(saved) => {
            setActing(null);
            if (saved) onChanged();
          }}
        />
      )}
    </div>
  );
}

function FindingCard({
  f,
  selected,
  canAct,
  onSelect,
  onAct,
}: {
  f: Finding;
  selected: boolean;
  canAct: boolean;
  onSelect: (f: Finding, ref: EvidenceRef | null) => void;
  onAct: (to: Finding["status"]) => void;
}) {
  const located = f.evidence_refs.filter((r) => r.page);

  return (
    <li className={`finding finding-${f.severity} ${selected ? "is-selected" : ""} ${f.status !== "open" ? "is-closed" : ""}`}>
      <button
        className="finding-main"
        onClick={() => onSelect(f, located[0] ?? f.evidence_refs[0] ?? null)}
        aria-pressed={selected}
      >
        <span className="finding-top">
          <SeverityTag severity={f.severity as Severity} />
          {f.outcome && (
            <span className={`pill outcome-pill outcome-${f.outcome.toLowerCase()}`} title={`Evaluation outcome: ${f.outcome}`}>
              {f.outcome.replace("_", " ")}
            </span>
          )}
          <span className="rule">{f.rule_id} · v{f.rule_version}</span>
          {f.status !== "open" && (
            <span className="pill">{f.status === "resolved" ? "Resolved" : "Waived"}</span>
          )}
        </span>
        <span className="finding-title">{f.summary}</span>
        {(f.clause_citation || APH_CITATIONS[f.rule_id]) && (
          <span className="clause-citation" title="Official statutory provision in AICTE Approval Process Handbook (2024-25 to 2026-27)">
            📜 {f.clause_citation || APH_CITATIONS[f.rule_id]}
          </span>
        )}
        <span className="finding-detail">{f.detail}</span>
        {isSelfDisclosure(f) && (
          <div className="self-disclosure-note" role="note">
            <span className="note-icon">ℹ️</span>
            <span>Self-disclosure checked &apos;yes&apos;. Reviewer must inspect uploaded office order to verify representation.</span>
          </div>
        )}
      </button>

      {f.evidence_refs.length > 0 && (
        <div className="evidence-chips" aria-label="Evidence coordinates">
          {f.evidence_refs.map((r, i) => (
            <button
              key={i}
              className="chip"
              onClick={() => onSelect(f, r)}
              disabled={!r.page && !r.document_id}
              title="Click to view highlighted evidence page"
            >
              <IconEye width="12" height="12" style={{ verticalAlign: "middle", marginRight: "4px" }} />
              {r.doc_type ? (DOC_LABEL[r.doc_type] || humanize(r.doc_type)) : "Document"}
              {r.page ? ` · p.${r.page}` : ""}
              {r.value ? ` · ${r.value}` : ""}
            </button>
          ))}
        </div>
      )}

      {f.status === "open" && f.next_action && (
        <p className="next">Suggested next step: {f.next_action}</p>
      )}

      {f.status !== "open" && f.resolution_note && (
        <p className="resolution">“{f.resolution_note}” — {f.resolved_by}, {when(f.resolved_at)}</p>
      )}

      {canAct && (
        <div className="finding-actions">
          {f.status === "open" ? (
            <>
              <button className="btn btn-small" onClick={() => onAct("resolved")}>
                <IconCheck width="12" height="12" />
                <span>Mark resolved</span>
              </button>
              <button className="btn btn-small btn-ghost" onClick={() => onAct("waived")}>
                Waive
              </button>
            </>
          ) : (
            <button className="btn btn-small btn-ghost" onClick={() => onAct("open")}>
              Reopen finding
            </button>
          )}
        </div>
      )}
    </li>
  );
}

function ResolveDialog({
  finding,
  to,
  onClose,
}: {
  finding: Finding;
  to: Finding["status"];
  onClose: (saved: boolean) => void;
}) {
  const toast = useToast();
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const title = to === "resolved" ? "Mark finding as resolved" : to === "waived" ? "Waive finding" : "Reopen finding";

  const submit = async () => {
    setBusy(true);
    setErr(null);
    try {
      await api.updateFinding(finding.id, to, note);
      toast(`Finding marked ${to}.`);
      onClose(true);
    } catch (e) {
      setErr(errorText(e));
      setBusy(false);
    }
  };

  return (
    <Modal
      open
      title={title}
      onClose={() => onClose(false)}
      footer={
        <>
          <button className="btn btn-ghost" onClick={() => onClose(false)}>Cancel</button>
          <button
            className="btn btn-primary"
            disabled={busy || (to !== "open" && note.trim().length < 5)}
            onClick={() => void submit()}
          >
            {busy ? "Saving…" : "Confirm"}
          </button>
        </>
      }
    >
      <p style={{ fontSize: "0.88rem", marginBottom: "0.75rem" }}>
        <strong>{finding.rule_id}:</strong> {finding.summary}
      </p>
      <label className="stack">
        <span>Reason or justification</span>
        <textarea
          rows={3}
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder={to === "resolved" ? "e.g. Verified with updated land mutation certificate." : "e.g. Discrepancy under allowable institutional threshold."}
        />
      </label>
      {err && <p className="inline-error">{err}</p>}
    </Modal>
  );
}
