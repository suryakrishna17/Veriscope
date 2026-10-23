import type { ReactNode } from "react";
import { useSession } from "../lib/session";

export function Layout({ children, wide = false }: { children: ReactNode; wide?: boolean }) {
  const { user, signOut } = useSession();
  return (
    <div className="shell">
      <a className="skip" href="#main">Skip to content</a>
      <header className="topbar">
        <a href="#/cases" className="brand" aria-label="VeriScope home">
          <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden>
            <rect x="3" y="2.5" width="14" height="19" rx="1.5" fill="none" stroke="currentColor" strokeWidth="1.6" />
            <path d="M6.5 8h7M6.5 11.5h7M6.5 15h4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
            <circle cx="17" cy="16.5" r="3.6" fill="var(--paper)" stroke="var(--action)" strokeWidth="1.8" />
            <path d="M19.6 19.1 22 21.5" stroke="var(--action)" strokeWidth="1.8" strokeLinecap="round" />
          </svg>
          VeriScope
        </a>
        <nav className="topnav" aria-label="Main">
          <a href="#/cases">{user?.role === "applicant" ? "My applications" : "Review queue"}</a>
          <a href="#/cases/new">New application</a>
        </nav>
        {user && (
          <div className="who">
            <span className="who-name">{user.name}</span>
            <span className="who-role">{user.role}</span>
            <button className="link-btn" onClick={signOut}>Sign out</button>
          </div>
        )}
      </header>
      <main id="main" className={wide ? "main main-wide" : "main"}>{children}</main>
      <footer className="caveat">
        Automated checks assist human review. Documents are not issuer-authenticated unless marked “Issuer verified”. A person makes every final decision.
      </footer>
    </div>
  );
}

export function PageState({ title, children, action }: { title: string; children?: ReactNode; action?: ReactNode }) {
  return (
    <div className="state">
      <h2>{title}</h2>
      {children && <p>{children}</p>}
      {action}
    </div>
  );
}
