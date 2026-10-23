import type { CaseStatus, Severity, TrustLabel } from "../api/types";
import { STATUS_LABEL } from "../lib/format";

export function StatusBadge({ status }: { status: CaseStatus }) {
  return <span className={`status status-${status}`}>{STATUS_LABEL[status]}</span>;
}

const TRUST: Record<TrustLabel, { text: string; hint: string }> = {
  ISSUER_VERIFIED: { text: "Issuer verified", hint: "The issuing body confirmed this document. A recorded issuer response exists." },
  ANOMALY_DETECTED: { text: "Review required", hint: "An automated check raised a signal that a person should look at." },
  NOT_VERIFIED: { text: "Not verified with issuer", hint: "No issuer check is connected, so the document has not been confirmed by its issuer." },
};

export function TrustBadge({ label, simulated = false }: { label: TrustLabel; simulated?: boolean }) {
  const t = TRUST[label];
  return (
    <span className={`trust trust-${label.toLowerCase()}`} title={t.hint}>
      <span className="trust-dot" aria-hidden />
      {t.text}
      {simulated && label === "ISSUER_VERIFIED" ? " (simulated)" : ""}
    </span>
  );
}

export function SeverityTag({ severity }: { severity: Severity }) {
  return <span className={`sev sev-${severity}`}>{severity.charAt(0).toUpperCase() + severity.slice(1)}</span>;
}

export function Confidence({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const tone = pct >= 90 ? "hi" : pct >= 75 ? "mid" : "lo";
  return (
    <span className={`conf conf-${tone}`} title={`Extraction confidence ${pct}%`}>
      <span className="conf-track"><span className="conf-fill" style={{ width: `${pct}%` }} /></span>
      <span className="conf-num">{pct}%</span>
    </span>
  );
}

export function Spinner({ label = "Loading" }: { label?: string }) {
  return <span className="spinner" role="progressbar" aria-label={label} />;
}
