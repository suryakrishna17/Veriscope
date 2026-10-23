import { useState } from "react";
import { api, download } from "../api/client";
import { Spinner } from "../components/Badges";
import { Layout, PageState } from "../components/Layout";
import { humanize, when } from "../lib/format";
import { errorText, useAsync } from "../lib/hooks";
import { useToast } from "../lib/toast";

interface Report {
  generated_at: string;
  case: { case_ref: string; application_type_label: string; applicant_ref: string; institution_ref: string; status: string };
  ruleset: { name: string; version: string; checksum: string; is_provisional: boolean; note: string };
  documents: { doc_type: string; original_name: string; sha256: string; pages: number; trust_label: string }[];
  findings: { rule_id: string; rule_version: string; severity: string; status: string; summary: string; detail: string; evidence: { doc_type?: string; page?: number; excerpt?: string }[]; resolution_note: string | null; resolved_by: string | null }[];
  decisions: { outcome: string; reason_code: string; note: string; reviewer: string; decided_at: string }[];
  summary: { text: string; kind: string } | null;
  verification_caveat: string;
  limitations: string[];
}

const TRUST: Record<string, string> = { ISSUER_VERIFIED: "Issuer verified", ANOMALY_DETECTED: "Review required", NOT_VERIFIED: "Not verified with issuer" };

export function ReportPage({ id }: { id: string }) {
  const toast = useToast();
  const { data, error, loading } = useAsync(() => api.report(id) as unknown as Promise<Report>, [id]);
  const [busy, setBusy] = useState(false);
  if (error) return <Layout><PageState title="The report could not be built">{errorText(error)}</PageState></Layout>;
  if (loading || !data) return <Layout><div className="center"><Spinner /></div></Layout>;
  const r = data;
  const pdf = async () => {
    setBusy(true);
    try { download(await api.reportPdf(id), `${r.case.case_ref}-report.pdf`); }
    catch (e) { toast(errorText(e), "error"); }
    finally { setBusy(false); }
  };
  const json = () => download(new Blob([JSON.stringify(r, null, 2)], { type: "application/json" }), `${r.case.case_ref}-report.json`);

  return (
    <Layout>
      <div className="page-head">
        <div>
          <a href={`#/cases/${id}`} className="back">← Back to case</a>
          <h1>Case report {r.case.case_ref}</h1>
          <p className="muted">{r.case.application_type_label} · {r.case.applicant_ref} · {r.case.institution_ref} · {humanize(r.case.status)}</p>
        </div>
        <div className="row-end">
          <button className="btn btn-ghost" onClick={json}>Download JSON</button>
          <button className="btn btn-primary" onClick={() => void pdf()} disabled={busy}>{busy ? "Preparing…" : "Download PDF"}</button>
        </div>
      </div>
      <article className="report">
        <p className="callout">{r.verification_caveat}</p>
        {r.summary && <section><h2>Summary</h2><p>{r.summary.text}</p></section>}
        <section>
          <h2>Documents</h2>
          <div className="table-wrap"><table className="plain">
            <thead><tr><th>Type</th><th>File</th><th>SHA-256</th><th>Issuer check</th></tr></thead>
            <tbody>{r.documents.map((d) => <tr key={d.sha256 + d.doc_type}><td>{humanize(d.doc_type)}</td><td>{d.original_name}</td><td className="hash">{d.sha256.slice(0, 20)}…</td><td>{TRUST[d.trust_label]}</td></tr>)}</tbody>
          </table></div>
        </section>
        <section>
          <h2>Findings</h2>
          {r.findings.length === 0 ? <p>No findings were raised.</p> : (
            <ul className="report-findings">
              {r.findings.map((f) => (
                <li key={f.rule_id + f.summary + f.detail}>
                  <p><strong>{f.rule_id}</strong> v{f.rule_version} · {f.severity} · {f.status}</p>
                  <p>{f.summary}. {f.detail}</p>
                  <p className="muted small">Evidence: {f.evidence.map((e) => `${humanize(e.doc_type ?? "document")} p.${e.page ?? "–"}`).join("; ") || "No source evidence"}</p>
                  {f.resolution_note && <p className="small">Resolution: “{f.resolution_note}” — {f.resolved_by}</p>}
                </li>
              ))}
            </ul>
          )}
        </section>
        <section>
          <h2>Human decision</h2>
          {r.decisions.length ? r.decisions.map((d) => <p key={d.decided_at}>{humanize(d.outcome)} ({humanize(d.reason_code)}) by {d.reviewer} on {when(d.decided_at)}. {d.note}</p>) : <p>No decision recorded yet.</p>}
        </section>
        <section>
          <h2>Limitations</h2>
          <ul>{r.limitations.map((l) => <li key={l}>{l}</li>)}</ul>
          <p className="muted small">Ruleset {r.ruleset.name} v{r.ruleset.version}{r.ruleset.is_provisional ? " (provisional)" : ""} · checksum {r.ruleset.checksum.slice(0, 16)}… · generated {when(r.generated_at)}</p>
        </section>
      </article>
    </Layout>
  );
}
