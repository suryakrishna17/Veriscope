import { useRef, useState, type DragEvent } from "react";
import { api } from "../api/client";
import type { DocType, DocumentInfo } from "../api/types";
import { DOC_LABEL, bytes } from "../lib/format";
import { errorText } from "../lib/hooks";
import { useSession } from "../lib/session";

const TYPES: DocType[] = ["APPLICATION_FORM", "INSTITUTION_AUTHORIZATION_LETTER", "ENROLMENT_OR_IDENTITY_PROOF"];
const HINT: Record<DocType, string> = {
  APPLICATION_FORM: "The signed application form.",
  INSTITUTION_AUTHORIZATION_LETTER: "Letter from the institution authorising the application.",
  ENROLMENT_OR_IDENTITY_PROOF: "Enrolment certificate or student ID. A clear scan is fine.",
};
const ACCEPT = ".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg";

type SlotState = { phase: "idle" | "uploading" | "done" | "error"; message?: string; name?: string };

export function Uploader({ caseId, existing, onUploaded }: { caseId: string; existing: DocumentInfo[]; onUploaded: () => void }) {
  return (
    <div className="slots">
      {TYPES.map((t) => <Slot key={t} caseId={caseId} type={t} existing={existing.filter((d) => d.doc_type === t)} onUploaded={onUploaded} />)}
    </div>
  );
}

function Slot({ caseId, type, existing, onUploaded }: { caseId: string; type: DocType; existing: DocumentInfo[]; onUploaded: () => void }) {
  const { meta } = useSession();
  const input = useRef<HTMLInputElement>(null);
  const [state, setState] = useState<SlotState>({ phase: "idle" });
  const [over, setOver] = useState(false);
  const maxMb = meta?.max_upload_mb ?? 10;

  const send = async (file: File) => {
    if (!/\.(pdf|png|jpe?g)$/i.test(file.name)) { setState({ phase: "error", message: "Choose a PDF, PNG or JPG file." }); return; }
    if (file.size > maxMb * 1024 * 1024) { setState({ phase: "error", message: `${file.name} is ${bytes(file.size)}. The limit is ${maxMb} MB.` }); return; }
    setState({ phase: "uploading", name: file.name });
    try {
      const r = await api.upload(caseId, type, file);
      setState({ phase: "done", name: file.name, message: r.duplicate ? "Uploaded. This exact file was submitted before; a reviewer will be asked to check it." : "Uploaded." });
      onUploaded();
    } catch (e) {
      setState({ phase: "error", name: file.name, message: errorText(e) });
    }
  };
  const drop = (e: DragEvent) => { e.preventDefault(); setOver(false); const f = e.dataTransfer.files[0]; if (f) void send(f); };

  return (
    <div className={`slot ${over ? "is-over" : ""} slot-${state.phase}`} onDragOver={(e) => { e.preventDefault(); setOver(true); }} onDragLeave={() => setOver(false)} onDrop={drop}>
      <div className="slot-text">
        <h3>{DOC_LABEL[type]}</h3>
        <p className="muted small">{HINT[type]}</p>
        {existing.map((d) => <p key={d.id} className="slot-file">✓ {d.original_name} · {bytes(d.size_bytes)}</p>)}
        {state.phase === "uploading" && <p className="small">Uploading {state.name}…</p>}
        {state.phase === "done" && <p className="small ok-text">{state.message}</p>}
        {state.phase === "error" && <p className="inline-error" role="alert">{state.message}</p>}
      </div>
      <input ref={input} type="file" accept={ACCEPT} hidden onChange={(e) => { const f = e.target.files?.[0]; if (f) void send(f); e.target.value = ""; }} aria-label={`Upload ${DOC_LABEL[type]}`} />
      <button className="btn btn-small" onClick={() => input.current?.click()} disabled={state.phase === "uploading"}>
        {existing.length ? "Replace or add" : "Choose file"}
      </button>
    </div>
  );
}
