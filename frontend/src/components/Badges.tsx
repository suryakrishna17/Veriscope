import type { ReactNode } from "react";
import type { CaseStatus, Severity, TrustLabel } from "../api/types";
import { STATUS_LABEL } from "../lib/format";
import { IconAlert, IconCheck, IconShield } from "./Icons";

export function StatusBadge({ status }: { status: CaseStatus }) {
  const icons: Partial<Record<CaseStatus, ReactNode>> = {
    approved: <IconCheck width="13" height="13" />,
    needs_review: <IconAlert width="13" height="13" />,
    clarification_requested: <IconAlert width="13" height="13" />,
    rejected: <IconShield width="13" height="13" />,
  };

  return (
    <span className={`status status-${status}`}>
      {icons[status] && <span className="status-icon" aria-hidden>{icons[status]}</span>}
      {STATUS_LABEL[status]}
    </span>
  );
}

const TRUST: Record<TrustLabel, { text: string; hint: string }> = {
  VERIFIED: { text: "Verified", hint: "Confirmed against official issuer registry or signed digital credentials." },
  MISMATCH_DETECTED: { text: "Mismatch detected", hint: "Entity mismatch detected between submitted document and official records." },
  EXPIRED: { text: "Expired", hint: "Document validity or statutory clearance date has elapsed." },
  VERIFICATION_PENDING: { text: "Verification pending", hint: "Submitted for issuer lookup; awaiting authoritative confirmation." },
  SOURCE_UNAVAILABLE: { text: "Source unavailable", hint: "Official issuer gateway or portal temporarily unreachable; will retry." },
  MANUAL_REVIEW_REQUIRED: { text: "Manual review required", hint: "Automated verification was inconclusive; scrutiny officer must confirm." },
  ISSUER_VERIFIED: { text: "Issuer verified", hint: "The issuing body confirmed this document. A recorded issuer response exists." },
  ANOMALY_DETECTED: { text: "Review required", hint: "An automated check raised a signal that a person should look at." },
  NOT_VERIFIED: { text: "Not verified with issuer", hint: "No issuer check is connected, so the document has not been confirmed by its issuer." },
};

export function TrustBadge({ label, simulated = false }: { label: TrustLabel; simulated?: boolean }) {
  const t = TRUST[label];
  return (
    <span className={`trust trust-${label.toLowerCase()}`} title={t.hint}>
      <span className="trust-dot" aria-hidden />
      <span>
        {t.text}
        {simulated && label === "ISSUER_VERIFIED" ? " (simulated)" : ""}
      </span>
    </span>
  );
}

export function SeverityTag({ severity }: { severity: Severity }) {
  return (
    <span className={`sev sev-${severity}`}>
      <span className="sev-dot" aria-hidden />
      {severity.charAt(0).toUpperCase() + severity.slice(1)}
    </span>
  );
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
