import { useState, type ReactNode } from "react";
import { useSession } from "../lib/session";
import { useRoute } from "../lib/router";
import { IconUser } from "./Icons";
import { Modal } from "./Modal";
import { LanyardBadge } from "./ui/lanyard-badge";

const ROLE_COLORS: Record<string, string> = {
  reviewer: "#FF5E1E",
  applicant: "#2563EB",
  admin: "#7C3AED",
};

export function Layout({ children, wide = false }: { children: ReactNode; wide?: boolean }) {
  const { user, signOut } = useSession();
  const route = useRoute();
  const [showBadge, setShowBadge] = useState(false);
  const isApplicant = user?.role === "applicant";

  const accentColor = user ? ROLE_COLORS[user.role] ?? "#FF5E1E" : "#FF5E1E";

  return (
    <div className="shell">
      <a className="skip" href="#main">Skip to content</a>
      <header className="topbar" style={{ position: "relative" }}>
        <div className="topbar-left">
          <a href="#/cases" className="brand" aria-label="VeriScope home">
            <span className="brand-logo" aria-hidden>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <rect x="3" y="2.5" width="14" height="19" rx="2" stroke="currentColor" strokeWidth="2" />
                <path d="M6.5 7.5h7M6.5 11.5h7M6.5 15.5h4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                <circle cx="17.5" cy="17" r="4" fill="var(--surface)" stroke="var(--action)" strokeWidth="2" />
                <path d="M20.5 20 23 22.5" stroke="var(--action)" strokeWidth="2" strokeLinecap="round" />
              </svg>
            </span>
            <span className="brand-title">VeriScope</span>
          </a>
          <span className="brand-badge">SIH26261 · AICTE</span>
        </div>

        <nav className="topnav" aria-label="Main">
          <a
            href="#/cases"
            className={`nav-item${route.name === "queue" ? " active" : ""}`}
          >
            {isApplicant ? "My Applications" : "Review Queue"}
          </a>
          <a
            href="#/cases/new"
            className={`nav-item${route.name === "new" ? " active" : ""}`}
          >
            New application
          </a>
        </nav>

        {user && (
          <div className="who">
            <button
              type="button"
              className="btn btn-small btn-badge-toggle"
              onClick={() => setShowBadge(true)}
              title="Inspect interactive 3D Lanyard ID Badge"
            >
              <span>🪪 3D Badge</span>
            </button>
            <div className="who-user">
              <span className="who-avatar" aria-hidden><IconUser width="14" height="14" /></span>
              <span className="who-name">{user.name}</span>
              <span className={`who-role-pill who-role-${user.role}`}>{user.role}</span>
            </div>
            <button className="btn btn-small btn-ghost who-signout" onClick={signOut}>Sign out</button>
          </div>
        )}
      </header>

      {/* ── Interactive 3D ID Badge Inspection Modal ── */}
      {user && (
        <Modal
          open={showBadge}
          title={`3D Inspector Credential · ${user.name}`}
          onClose={() => setShowBadge(false)}
        >
          <div className="modal-badge-stage">
            <p className="muted small" style={{ textAlign: "center", marginBottom: "0.5rem" }}>
              Interactive 3D Verlet rope badge. Hover to dip &amp; tilt, click/drag to swing, double-click to flip.
            </p>
            <div style={{ display: "flex", justifyContent: "center", width: "100%", overflow: "hidden" }}>
              <LanyardBadge
                name={user.name}
                role={user.role === "reviewer" ? "Reviewer" : user.role === "admin" ? "Admin" : "Applicant"}
                org="SIH26261 · AICTE"
                badgeId={`VS-2026-${user.id.slice(0, 4)}`}
                accentColor={accentColor}
                width={360}
                autoSwing={true}
              />
            </div>
          </div>
        </Modal>
      )}

      <main id="main" className={wide ? "main main-wide" : "main"}>{children}</main>

      <footer className="caveat">
        <div className="caveat-inner">
          <span className="caveat-dot" aria-hidden />
          <span>
            Automated checks assist human review. Documents are not issuer-authenticated unless marked "Issuer verified". A person makes every final decision.
          </span>
          <span className="caveat-sys">System operational · v1.0.0</span>
        </div>
      </footer>
    </div>
  );
}

export function PageState({ title, children, action }: { title: string; children?: ReactNode; action?: ReactNode }) {
  return (
    <div className="state">
      <div className="state-card">
        <h2>{title}</h2>
        {children && <p className="muted">{children}</p>}
        {action && <div className="state-act">{action}</div>}
      </div>
    </div>
  );
}
