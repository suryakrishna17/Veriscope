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

export function AuditTimeline({ events }: { events: AuditEvent[] }) {
  if (!events.length) return <p className="muted pad">No activity yet.</p>;
  return (
    <ol className="timeline">
      {events.map((e) => (
        <li key={e.id}>
          <span className="t-when">{when(e.created_at)}</span>
          <span className="t-what">{describe(e)}</span>
          <span className="t-who">{e.actor}{(e.payload as { note?: string }).note ? ` — “${(e.payload as { note?: string }).note}”` : ""}</span>
        </li>
      ))}
    </ol>
  );
}
