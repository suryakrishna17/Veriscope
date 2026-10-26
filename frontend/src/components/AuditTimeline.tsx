import { useState } from "react";
import { api } from "../api/client";
import type { AuditEvent } from "../api/types";
import { humanize, when } from "../lib/format";

function describe(e: AuditEvent): string {
  const p = e.payload as Record<string, unknown>;
  switch (e.action) {
    case "case.status_changed": return `Status: ${humanize(String(p.from))} → ${humanize(String(p.to))}`;
    case "document.uploaded": return `Uploaded ${humanize(String(p.doc_type))}`;
    case "document.processed": return `Read document (${p.fields} values${p.ocr_used ? ", OCR" : ""})`;
    case "rules.evaluated": return `Ran ${p.ruleset}: ${p.new_findings} new, ${p.cleared_findings} cleared`;
    case "field.corrected": return `Corrected ${humanize(String(p.field_key))}: “${p.original}” → “${p.new}”`;
    default: return humanize(e.action);
  }
}

export function AuditTimeline({ events, caseId }: { events: AuditEvent[]; caseId?: string }) {
  const [verifying, setVerifying] = useState(false);
  const [verifyResult, setVerifyResult] = useState<{
    valid: boolean;
    event_count: number;
    head_hash?: string;
    broken_at_seq?: number;
  } | null>(null);

  const handleVerify = async () => {
    if (!caseId) return;
    setVerifying(true);
    try {
      const res = await api.auditVerify(caseId);
      setVerifyResult(res);
    } catch (err) {
      console.error("Audit verification error:", err);
    } finally {
      setVerifying(false);
    }
  };

  if (!events.length) return <p className="muted pad">No activity yet.</p>;

  return (
    <div>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0.5rem 0.75rem",
          marginBottom: "0.75rem",
          background: verifyResult && !verifyResult.valid ? "rgba(239, 68, 68, 0.08)" : "rgba(16, 185, 129, 0.08)",
          border: `1px solid ${verifyResult && !verifyResult.valid ? "rgba(239, 68, 68, 0.3)" : "rgba(16, 185, 129, 0.25)"}`,
          borderRadius: "6px",
          fontSize: "0.75rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span style={{ color: verifyResult && !verifyResult.valid ? "#ef4444" : "#10b981", fontWeight: 600 }}>
            {verifyResult && !verifyResult.valid ? "⚠️ Hash Chain Tamper Detected" : "🔒 Cryptographic SHA-256 Audit Trail"}
          </span>
          <span className="mono muted" style={{ fontSize: "0.7rem" }}>
            ({events.length} Events)
          </span>
        </div>

        {caseId && (
          <button
            type="button"
            onClick={() => void handleVerify()}
            disabled={verifying}
            style={{
              background: verifyResult?.valid
                ? "rgba(16, 185, 129, 0.18)"
                : verifyResult && !verifyResult.valid
                ? "rgba(239, 68, 68, 0.2)"
                : "rgba(255, 94, 30, 0.12)",
              border: `1px solid ${
                verifyResult?.valid
                  ? "#10b981"
                  : verifyResult && !verifyResult.valid
                  ? "#ef4444"
                  : "#FF5E1E"
              }`,
              color: verifyResult?.valid
                ? "#10b981"
                : verifyResult && !verifyResult.valid
                ? "#ef4444"
                : "#E04D12",
              borderRadius: "4px",
              padding: "3px 8px",
              fontSize: "0.72rem",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            {verifying
              ? "Verifying..."
              : verifyResult?.valid
              ? `✓ Valid (${verifyResult.event_count}/${events.length} Chained)`
              : verifyResult && !verifyResult.valid
              ? `⚠️ Broken at Seq #${verifyResult.broken_at_seq}`
              : "🛡️ Verify Hash Chain"}
          </button>
        )}
      </div>
      <ol className="timeline">
        {events.map((e) => (
          <li key={e.id}>
            <span className="t-when">{when(e.created_at)}</span>
            <span className="t-what">{describe(e)}</span>
            <span className="t-who">
              {e.actor}
              {(e.payload as { note?: string }).note ? ` — “${(e.payload as { note?: string }).note}”` : ""}
            </span>
          </li>
        ))}
      </ol>
    </div>
  );
}
