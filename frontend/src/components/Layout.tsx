import type { ReactNode } from "react";
import { useSession } from "../lib/session";
import { IconUser } from "./Icons";

export function Layout({ children, wide = false }: { children: ReactNode; wide?: boolean }) {
  const { user, signOut } = useSession();
  const isApplicant = user?.role === "applicant";

  return (
    <div className="shell">
      <a className="skip" href="#main">Skip to content</a>
      <header className="topbar">
        <div className="topbar-left">
          <a href="#/cases" className="brand" aria-label="VeriScope home">
            <span className="brand-logo" aria-hidden>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
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
          <a href="#/cases" className="nav-item">
            {isApplicant ? "My Applications" : "Review Queue"}
          </a>
          <a href="#/cases/new" className="nav-item">
            New application
          </a>
        </nav>

        {user && (
          <div className="who">
            <div className="who-user">
              <span className="who-avatar" aria-hidden><IconUser width="14" height="14" /></span>
              <span className="who-name">{user.name}</span>
              <span className={`who-role-pill who-role-${user.role}`}>{user.role}</span>
            </div>
            <button className="btn btn-small btn-ghost who-signout" onClick={signOut}>Sign out</button>
          </div>
        )}
      </header>

      <main id="main" className={wide ? "main main-wide" : "main"}>{children}</main>

      <footer className="caveat">
        <div className="caveat-inner">
          <span className="caveat-dot" aria-hidden />
          <span>
            Automated checks assist human review. Documents are not issuer-authenticated unless marked “Issuer verified”. A person makes every final decision.
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
