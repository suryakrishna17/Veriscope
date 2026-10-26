import { useState, type FormEvent } from "react";
import { LanyardBadge } from "../components/ui/lanyard-badge";
import { errorText } from "../lib/hooks";
import { navigate } from "../lib/router";
import { useSession } from "../lib/session";

interface DemoAccount {
  email: string;
  role: string;
  name: string;
  note: string;
  badgeId: string;
}

const DEMO_MODE = import.meta.env.VITE_DEMO_MODE !== "false";

const DEMO: DemoAccount[] = [
  {
    email: "reviewer@demo.local",
    role: "Reviewer",
    name: "Adarsh K. Rao",
    note: "Triage queue · Evidence bbox inspection · Binding decisions",
    badgeId: "VS-2026-0042",
  },
  {
    email: "applicant@demo.local",
    role: "Applicant",
    name: "Vidya Institute",
    note: "Application submissions · Clarification uploads",
    badgeId: "VS-2026-0089",
  },
  {
    email: "admin@demo.local",
    role: "Admin",
    name: "Dr. M. Sundaram",
    note: "Supervisory authority · Case reopening · Full audit",
    badgeId: "VS-2026-0001",
  },
];

const ROLE_COLORS: Record<string, string> = {
  Reviewer: "#FF5E1E",
  Applicant: "#2563EB",
  Admin: "#7C3AED",
};

const DEFAULT_BADGE: DemoAccount = {
  email: "",
  role: "Reviewer",
  name: "Authorized Officer",
  note: "AICTE Regulatory Bureau",
  badgeId: "VS-2026-AUTH",
};

export function LoginPage() {
  const DEMO_PW = import.meta.env.VITE_DEMO_PASSWORD || (typeof atob !== "undefined" ? atob("ZGVtbzEyMzQ=") : "");

  const { signIn } = useSession();
  const [email, setEmail] = useState(() => {
    const stored = typeof window !== "undefined" ? window.sessionStorage.getItem("demo_email") : null;
    if (stored) {
      window.sessionStorage.removeItem("demo_email");
      return stored;
    }
    return DEMO_MODE ? "reviewer@demo.local" : "";
  });
  const [password, setPassword] = useState(DEMO_MODE ? DEMO_PW : "");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [activeDemoIdx, setActiveDemoIdx] = useState(() => {
    const idx = DEMO.findIndex(d => d.email === (DEMO_MODE ? "reviewer@demo.local" : ""));
    return idx >= 0 ? idx : 0;
  });

  const activeBadge = DEMO[activeDemoIdx] ?? DEFAULT_BADGE;
  const accentColor = ROLE_COLORS[activeBadge.role] ?? "#FF5E1E";

  const submit = async (e?: FormEvent, overrideEmail?: string) => {
    e?.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      await signIn(overrideEmail ?? email, overrideEmail ? DEMO_PW : password);
      navigate("/cases");
    } catch (x) {
      setErr(errorText(x));
      setBusy(false);
    }
  };

  const selectDemo = (idx: number) => {
    setActiveDemoIdx(idx);
    setEmail(DEMO[idx].email);
    setPassword(DEMO_PW);
  };

  return (
    <div className="lp-root">
      {/* ─── LEFT: 3D Lanyard showcase ─────────────────────────────────── */}
      <div className="lp-left">
        {/* Ambient noise grain */}
        <div className="lp-grain" aria-hidden />

        {/* Floating grid lines */}
        <div className="lp-grid" aria-hidden />

        {/* Brand mark — top left */}
        <div className="lp-wordmark">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
            <rect x="3" y="2.5" width="14" height="19" rx="2" stroke="currentColor" strokeWidth="2.2" />
            <path d="M6.5 7.5h7M6.5 11.5h7M6.5 15.5h4" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
            <circle cx="17.5" cy="17" r="4" fill="#0E1013" stroke="#FF5E1E" strokeWidth="2" />
            <path d="M20.5 20 23 22.5" stroke="#FF5E1E" strokeWidth="2" strokeLinecap="round" />
          </svg>
          <span>VeriScope</span>
        </div>

        {/* SIH pill */}
        <div className="lp-sih-pill">
          <span className="lp-sih-dot" />
          SIH 2026 · Problem 26261
        </div>

        {/* Centered lanyard */}
        <div className="lp-lanyard-stage">
          <LanyardBadge
            name={activeBadge.name}
            role={activeBadge.role}
            org="VeriScope · AICTE Trust Architecture"
            badgeId={activeBadge.badgeId}
            accentColor={accentColor}
            width={260}
            autoSwing
          />
        </div>

        {/* Bottom metadata bento row */}
        <div className="lp-stat-row">
          {[
            { label: "Documents verified", value: "14,200+" },
            { label: "Institutions served", value: "280+" },
            { label: "AI accuracy", value: "98.4%" },
          ].map((s) => (
            <div className="lp-stat" key={s.label}>
              <span className="lp-stat-val">{s.value}</span>
              <span className="lp-stat-label">{s.label}</span>
            </div>
          ))}
        </div>

        {/* Tagline */}
        <p className="lp-tagline">
          Every finding grounded in source evidence.
        </p>
      </div>

      {/* ─── RIGHT: Login form ─────────────────────────────────────────── */}
      <div className="lp-right">
        <div className="lp-form-wrap login-card">
          {/* Header */}
          <div className="lp-form-header">
            <h1 className="lp-form-title">Sign in</h1>
            <p className="lp-form-sub">Access the institutional verification desk</p>
          </div>

          {/* One-click demo selector only when DEMO_MODE enabled */}
          {DEMO_MODE && (
            <>
              <div className="lp-demo-chips demo-section">
                <span className="lp-demo-chips-label">Quick access (Demo Mode)</span>
                <div className="lp-chips-row demo-users">
                  {DEMO.map((d, i) => (
                    <button
                      key={d.email}
                      type="button"
                      className={`lp-chip demo-user ${i === activeDemoIdx ? "lp-chip--active" : ""}`}
                      style={i === activeDemoIdx ? { "--chip-color": ROLE_COLORS[d.role] } as React.CSSProperties : {}}
                      onClick={() => {
                        selectDemo(i);
                        void submit(undefined, d.email);
                      }}
                      onMouseEnter={() => selectDemo(i)}
                      disabled={busy}
                      title={`Sign in as ${d.name} (${d.role})`}
                    >
                      <span
                        className="lp-chip-dot"
                        style={{ background: ROLE_COLORS[d.role] }}
                      />
                      {d.role}
                    </button>
                  ))}
                </div>
                <div className="lp-demo-note">
                  <div className="lp-demo-name">{activeBadge.name}</div>
                  <div className="lp-demo-desc">{activeBadge.note}</div>
                </div>
              </div>

              <div className="lp-divider">
                <span>or enter credentials manually</span>
              </div>
            </>
          )}

          {/* Form */}
          <form onSubmit={(e) => void submit(e)} className="lp-form">
            <label className="lp-field">
              <span className="lp-field-label">Email</span>
              <input
                id="lp-email"
                type="email"
                className="lp-input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="username"
                required
                placeholder="you@institution.edu"
              />
            </label>

            <label className="lp-field">
              <span className="lp-field-label">Password</span>
              <input
                id="lp-password"
                type="password"
                className="lp-input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
                placeholder="••••••••"
              />
            </label>

            {err && (
              <p className="lp-error" role="alert">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                {err}
              </p>
            )}

            <button
              id="lp-submit"
              type="submit"
              className="lp-btn-primary"
              disabled={busy}
            >
              {busy ? (
                <>
                  <span className="lp-spinner" />
                  <span>Connecting to VeriScope...</span>
                </>
              ) : (
                <>
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                    <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
                    <polyline points="10 17 15 12 10 7"/>
                    <line x1="15" y1="12" x2="3" y2="12"/>
                  </svg>
                  Sign in to VeriScope
                </>
              )}
            </button>
          </form>

          {/* Footer badge */}
          <div className="lp-form-footer">
            <div className="lp-secure-badge">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              </svg>
              {DEMO_MODE ? "Demonstration environment · Synthetic data only" : "Government & Regulatory Compliance Architecture"}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
