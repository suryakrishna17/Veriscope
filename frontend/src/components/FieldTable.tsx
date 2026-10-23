import { useState } from "react";
import { api } from "../api/client";
import type { DocType, Field } from "../api/types";
import { DOC_LABEL } from "../lib/format";
import { errorText } from "../lib/hooks";
import { useToast } from "../lib/toast";
import { Confidence } from "./Badges";

interface Props {
  fields: Field[];
  canEdit: boolean;
  selectedId: string | null;
  onSelect: (f: Field) => void;
  onChanged: () => void;
}

const SOURCE: Record<Field["source"], string> = { pdf_text: "PDF text", ocr: "OCR", visual: "Visual check", llm_suggestion: "AI suggestion" };
const ORDER: DocType[] = ["APPLICATION_FORM", "INSTITUTION_AUTHORIZATION_LETTER", "ENROLMENT_OR_IDENTITY_PROOF"];

export function FieldTable({ fields, canEdit, selectedId, onSelect, onChanged }: Props) {
  const [editing, setEditing] = useState<string | null>(null);
  if (!fields.length) return <p className="muted pad">No values extracted yet. Run the checks to read the documents.</p>;
  return (
    <div className="fields">
      {ORDER.filter((t) => fields.some((f) => f.doc_type === t)).map((t) => (
        <section key={t} className="field-group" aria-label={DOC_LABEL[t]}>
          <h3 className="group-title">{DOC_LABEL[t]}</h3>
          <ul className="field-list">
            {fields.filter((f) => f.doc_type === t).map((f) => (
              <li key={f.id} className={`field ${selectedId === f.id ? "is-selected" : ""} ${f.corrected_value ? "is-corrected" : ""}`}>
                {editing === f.id ? (
                  <CorrectionForm field={f} onDone={(saved) => { setEditing(null); if (saved) onChanged(); }} />
                ) : (
                  <button className="field-row" onClick={() => onSelect(f)} aria-pressed={selectedId === f.id}>
                    <span className="field-label">{f.label}</span>
                    <span className="field-value">{f.effective_value ?? <em className="muted">unreadable</em>}</span>
                    <span className="field-meta">
                      <Confidence value={f.corrected_value ? 1 : f.confidence} />
                      <span className="src">{f.corrected_value ? "Corrected" : SOURCE[f.source]}{f.page_number ? ` · p.${f.page_number}` : ""}</span>
                    </span>
                    {f.corrected_value && (
                      <span className="field-orig">Extracted “{f.raw_value}” · {f.corrected_by}: {f.correction_reason}</span>
                    )}
                  </button>
                )}
                {canEdit && editing !== f.id && f.source !== "visual" && (
                  <button className="link-btn field-edit" onClick={() => setEditing(f.id)} aria-label={`Correct ${f.label}`}>Correct</button>
                )}
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}

function CorrectionForm({ field, onDone }: { field: Field; onDone: (saved: boolean) => void }) {
  const toast = useToast();
  const [value, setValue] = useState(field.corrected_value ?? field.raw_value ?? "");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const save = async () => {
    setBusy(true); setErr(null);
    try {
      await api.correctField(field.id, value, reason);
      toast(`${field.label} corrected. Checks re-ran.`);
      onDone(true);
    } catch (e) { setErr(errorText(e)); setBusy(false); }
  };
  return (
    <form className="correct" onSubmit={(e) => { e.preventDefault(); void save(); }}>
      <label>
        <span>{field.label}</span>
        <input value={value} onChange={(e) => setValue(e.target.value)} autoFocus required />
      </label>
      <label>
        <span>Why are you correcting it?</span>
        <input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="e.g. OCR misread a digit" required minLength={3} />
      </label>
      <p className="muted small">The extracted value “{field.raw_value}” stays on record.</p>
      {err && <p className="inline-error">{err}</p>}
      <div className="row-end">
        <button type="button" className="btn btn-ghost" onClick={() => onDone(false)}>Cancel</button>
        <button className="btn btn-primary" disabled={busy}>{busy ? "Saving…" : "Save correction"}</button>
      </div>
    </form>
  );
}
