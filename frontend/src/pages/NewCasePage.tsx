import { useState, type FormEvent } from "react";
import { api, ApiError } from "../api/client";
import { Layout } from "../components/Layout";
import { Uploader } from "../components/Uploader";
import { errorText, useAsync } from "../lib/hooks";
import { navigate } from "../lib/router";
import { useToast } from "../lib/toast";

export function NewCasePage() {
  const toast = useToast();
  const [step, setStep] = useState<1 | 2>(1);
  const [appType, setAppType] = useState<string>("AICTE_EOA");
  const [form, setForm] = useState({ applicant_ref: "", institution_ref: "" });
  const [errs, setErrs] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [caseId, setCaseId] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const docs = useAsync(() => (caseId ? api.getCase(caseId) : Promise.resolve(null)), [caseId]);

  const isEoa = appType === "AICTE_EOA";

  const create = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true); setErr(null); setErrs({});
    try {
      const c = await api.createCase({ ...form, application_type: appType });
      setCaseId(c.id);
      setStep(2);
    } catch (x) {
      if (x instanceof ApiError && x.details.fields) setErrs(x.details.fields as Record<string, string>);
      setErr(errorText(x));
    } finally { setBusy(false); }
  };

  const run = async () => {
    if (!caseId) return;
    setBusy(true); setErr(null);
    try {
      await api.process(caseId);
      toast("Documents submitted. Regulatory evaluation checks are running.");
      navigate(`/cases/${caseId}`);
    } catch (x) { setErr(errorText(x)); setBusy(false); }
  };

  const uploaded = docs.data?.documents ?? [];
  return (
    <Layout>
      <div className="page-head">
        <div>
          <h1>New Application</h1>
          <p className="muted">
            {isEoa
              ? "AICTE Extension of Approval (Existing Institutions) — APH 2024–27 Chapter II compliance audit."
              : "Student support application (prototype rulebook)."}
          </p>
        </div>
      </div>
      <ol className="steps" aria-label="Progress">
        <li className={step === 1 ? "is-current" : "is-done"}>Application details</li>
        <li className={step === 2 ? "is-current" : ""}>Statutory Documents</li>
      </ol>

      {step === 1 && (
        <form className="card form" onSubmit={(e) => void create(e)}>
          <label className="stack">
            <span>Regulatory Approval Program</span>
            <select
              value={appType}
              onChange={(e) => setAppType(e.target.value)}
              style={{ fontWeight: 500 }}
            >
              <option value="AICTE_EOA">
                AICTE Extension of Approval (Existing Institutions) — Official APH 2024–27
              </option>
              <option value="STUDENT_SUPPORT_LITE">
                Student Support Application (Prototype Rulebook)
              </option>
            </select>
          </label>

          <label className="stack">
            <span>{isEoa ? "Institutional Registrar / Authorized Signatory" : "Applicant Name or Reference"}</span>
            <input
              value={form.applicant_ref}
              onChange={(e) => setForm({ ...form, applicant_ref: e.target.value })}
              required
              minLength={2}
              maxLength={120}
              placeholder={isEoa ? "e.g., Dr. R. K. Sharma (Registrar)" : "e.g., Jane Doe"}
              aria-invalid={!!errs.applicant_ref}
            />
            {errs.applicant_ref && <small className="inline-error">{errs.applicant_ref}</small>}
          </label>

          <label className="stack">
            <span>{isEoa ? "Institution Name & AICTE Permanent ID" : "Institution"}</span>
            <input
              value={form.institution_ref}
              onChange={(e) => setForm({ ...form, institution_ref: e.target.value })}
              required
              minLength={2}
              maxLength={160}
              placeholder={isEoa ? "e.g., Vidya Institute of Technology (1-10923481)" : "e.g., City College"}
              aria-invalid={!!errs.institution_ref}
            />
            {errs.institution_ref && <small className="inline-error">{errs.institution_ref}</small>}
          </label>

          <p className="muted small">
            {isEoa
              ? "All submitted documents are evaluated against AICTE APH Chapter II statutory criteria with pixel-level coordinate grounding."
              : "Use synthetic or test data only in this prototype."}
          </p>
          {err && <p className="inline-error" role="alert">{err}</p>}
          <div className="row-end">
            <button className="btn btn-primary" disabled={busy}>
              {busy ? "Creating dossier…" : "Continue to documents"}
            </button>
          </div>
        </form>
      )}

      {step === 2 && caseId && (
        <div className="card">
          <p>
            {isEoa
              ? "Upload the statutory documents for AICTE Extension of Approval (PDF, PNG or JPG, up to 10 MB each). Text is parsed natively with high-accuracy OCR fallback."
              : "Upload the three documents. PDF, PNG or JPG, up to 10 MB each. Scans are read with OCR."}
          </p>
          <Uploader
            caseId={caseId}
            existing={uploaded}
            onUploaded={() => void docs.reload(true)}
            applicationType={appType}
          />
          {err && <p className="inline-error" role="alert">{err}</p>}
          <div className="row-end">
            <button className="btn btn-ghost" onClick={() => navigate(`/cases/${caseId}`)}>
              Save and finish later
            </button>
            <button
              className="btn btn-primary"
              disabled={busy || uploaded.length === 0}
              onClick={() => void run()}
            >
              {busy ? "Submitting…" : `Submit ${uploaded.length} document(s) and run regulatory checks`}
            </button>
          </div>
        </div>
      )}
    </Layout>
  );
}
