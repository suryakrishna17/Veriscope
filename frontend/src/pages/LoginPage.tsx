import { useState, type FormEvent } from "react";
import { navigate } from "../lib/router";
import { errorText } from "../lib/hooks";
import { useSession } from "../lib/session";

const DEMO = [
  { email: "reviewer@demo.local", label: "Reviewer", note: "Works the review queue and records decisions" },
  { email: "applicant@demo.local", label: "Applicant", note: "Submits applications and answers clarifications" },
  { email: "admin@demo.local", label: "Admin", note: "Reviewer rights plus reopening closed cases" },
];

export function LoginPage() {
  const { signIn } = useSession();
  const [email, setEmail] = useState("reviewer@demo.local");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const submit = async (e?: FormEvent, override?: string) => {
    e?.preventDefault();
    setBusy(true); setErr(null);
    try {
      await signIn(override ?? email, override ? "demo1234" : password);
      navigate("/cases");
    } catch (x) { setErr(errorText(x)); setBusy(false); }
  };

  return (
    <div className="login">
      <div className="login-intro">
        <p className="login-brand">VeriScope</p>
        <h1>Every flag points to the page it came from.</h1>
        <p>VeriScope reads application documents, runs a versioned rulebook, and shows each finding beside its evidence so a reviewer can decide quickly and on the record.</p>
        <p className="muted small">SIH26261 prototype · synthetic data only</p>
      </div>
      <form className="login-card" onSubmit={(e) => void submit(e)}>
        <h2>Sign in</h2>
        <label className="stack"><span>Email</span><input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="username" required /></label>
        <label className="stack"><span>Password</span><input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required /></label>
        {err && <p className="inline-error" role="alert">{err}</p>}
        <button className="btn btn-primary btn-block" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button>
        <div className="demo-users">
          <p className="small muted">Demo accounts (password demo1234)</p>
          {DEMO.map((d) => (
            <button type="button" key={d.email} className="demo-user" onClick={() => void submit(undefined, d.email)} disabled={busy}>
              <strong>{d.label}</strong><span>{d.note}</span>
            </button>
          ))}
        </div>
      </form>
    </div>
  );
}
