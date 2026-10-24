import { useState, type FormEvent } from "react";
import { IconCheck, IconFileText, IconShield } from "../components/Icons";
import { errorText } from "../lib/hooks";
import { navigate } from "../lib/router";
import { useSession } from "../lib/session";

interface DemoAccount {
  email: string;
  role: string;
  name: string;
  note: string;
}

const DEMO: DemoAccount[] = [
  {
    email: "reviewer@demo.local",
    role: "Reviewer",
    name: "Adarsh Rao",
    note: "Works the triage queue, inspects evidence bboxes, and records decisions",
  },
  {
    email: "applicant@demo.local",
    role: "Applicant",
    name: "Vidya Institute of Technology",
    note: "Submits institutional applications and provides clarification uploads",
  },
  {
    email: "admin@demo.local",
    role: "Admin",
    name: "Dr. Meenakshi Sundaram",
    note: "Supervisory authority with case reopening and full audit trail access",
  },
];

export function LoginPage() {
  const { signIn } = useSession();
  const [email, setEmail] = useState("reviewer@demo.local");
  const [password, setPassword] = useState("demo1234");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const submit = async (e?: FormEvent, overrideEmail?: string) => {
    e?.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      await signIn(overrideEmail ?? email, overrideEmail ? "demo1234" : password);
      navigate("/cases");
    } catch (x) {
      setErr(errorText(x));
      setBusy(false);
    }
  };

  return (
    <div className="login">
      <div className="login-intro">
        <div className="login-hackathon-pill">
          <IconShield width="14" height="14" />
          <span>SIH26261 · AICTE Trust Architecture</span>
        </div>

        <div className="login-brand" style={{ marginTop: "1rem" }}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <rect x="3" y="2.5" width="14" height="19" rx="2" stroke="currentColor" strokeWidth="2.2" />
            <path d="M6.5 7.5h7M6.5 11.5h7M6.5 15.5h4" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
            <circle cx="17.5" cy="17" r="4" fill="#111a28" stroke="#2dd4bf" strokeWidth="2.2" />
            <path d="M20.5 20 23 22.5" stroke="#2dd4bf" strokeWidth="2.2" strokeLinecap="round" />
          </svg>
          <span>VeriScope</span>
        </div>

        <h1 className="login-slogan">Every finding grounded in source evidence.</h1>

        <p className="login-intro-desc">
          VeriScope evaluates institutional applications against versioned policy rulebooks,
          projecting every finding directly onto document pages so reviewers decide with speed and precision.
        </p>

        <div className="login-features">
          <div className="login-feature-item">
            <span className="login-feature-icon"><IconCheck width="14" height="14" /></span>
            <div className="login-feature-text">
              <strong>Bounding-Box Provenance</strong>
              <span>Extracted dates, land areas, and names map to their visual source coordinates.</span>
            </div>
          </div>

          <div className="login-feature-item">
            <span className="login-feature-icon"><IconFileText width="14" height="14" /></span>
            <div className="login-feature-text">
              <strong>Deterministic Rule Engine</strong>
              <span>Transparent, auditable policy rules covering AICTE approval standards.</span>
            </div>
          </div>

          <div className="login-feature-item">
            <span className="login-feature-icon"><IconShield width="14" height="14" /></span>
            <div className="login-feature-text">
              <strong>Human-in-the-Loop Governance</strong>
              <span>Algorithms assist and flag; only authorized personnel record binding decisions.</span>
            </div>
          </div>
        </div>

        <p className="muted small" style={{ color: "#64748b" }}>
          Demonstration environment · Synthetic documents and simulated verification data.
        </p>
      </div>

      <div className="login-card-wrap">
        <div className="login-card">
          <h2>Sign in to VeriScope</h2>
          <p className="login-card-sub">Access the institutional verification desk</p>

          <form onSubmit={(e) => void submit(e)}>
            <label className="stack">
              <span>Email</span>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="username"
                required
              />
            </label>

            <label className="stack">
              <span>Password</span>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
            </label>

            {err && <p className="inline-error" role="alert">{err}</p>}

            <button type="submit" className="btn btn-primary btn-block" disabled={busy} style={{ marginTop: "0.5rem" }}>
              {busy ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <div className="demo-section">
            <div className="demo-header">
              <span>One-Click Demo Access</span>
              <span className="muted small">pwd: demo1234</span>
            </div>

            <div className="demo-users">
              {DEMO.map((d) => (
                <button
                  type="button"
                  key={d.email}
                  className="demo-user"
                  onClick={() => void submit(undefined, d.email)}
                  disabled={busy}
                  title={`Sign in as ${d.name} (${d.role})`}
                >
                  <div className="demo-user-info">
                    <strong>{d.name}</strong>
                    <span>{d.note}</span>
                  </div>
                  <span className={`demo-role-badge who-role-${d.role.toLowerCase()}`}>{d.role}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
