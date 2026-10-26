import { useState, useEffect, useRef, useCallback } from "react";
import { LanyardBadge } from "../components/ui/lanyard-badge";
import { CircularReadings3D } from "../components/ui/CircularReadings3D";
import { DossierHologram3D } from "../components/ui/DossierHologram3D";
import { navigate } from "../lib/router";

/* ─── Hash utilities ─────────────────────────────────────────────────────── */

async function sha256(msg: string): Promise<string> {
  const data = new TextEncoder().encode(msg);
  const buf = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, "0")).join("").slice(0, 20);
}

interface HashNode { id: string; label: string; hash: string; prevHash: string; tampered: boolean; }

/* ─── Data ───────────────────────────────────────────────────────────────── */

const RULES_MATRIX = [
  { id: "EOA-CMP-001", cat: "Completeness", sev: "high", pass: true },
  { id: "EOA-CMP-002", cat: "Completeness", sev: "high", pass: true },
  { id: "EOA-CMP-003", cat: "Completeness", sev: "high", pass: false },
  { id: "EOA-CMP-004", cat: "Completeness", sev: "med",  pass: true },
  { id: "EOA-CMP-005", cat: "Completeness", sev: "high", pass: true },
  { id: "EOA-CMP-006", cat: "Completeness", sev: "high", pass: true },
  { id: "EOA-FMT-001", cat: "Format",       sev: "med",  pass: true },
  { id: "EOA-FMT-002", cat: "Format",       sev: "med",  pass: true },
  { id: "EOA-DAT-001", cat: "Dates",        sev: "low",  pass: true },
  { id: "EOA-DAT-002", cat: "Dates",        sev: "low",  pass: false },
  { id: "EOA-LND-001", cat: "Land",         sev: "high", pass: true },
  { id: "EOA-LND-002", cat: "Land",         sev: "med",  pass: true },
  { id: "EOA-FCR-001", cat: "Faculty",      sev: "med",  pass: true },
  { id: "EOA-FCR-002", cat: "Faculty",      sev: "med",  pass: false },
  { id: "EOA-FCR-003", cat: "Faculty",      sev: "low",  pass: true },
  { id: "EOA-CON-001", cat: "Content",      sev: "high", pass: true },
  { id: "EOA-CON-002", cat: "Content",      sev: "high", pass: true },
  { id: "EOA-ARI-001", cat: "Arithmetic",   sev: "med",  pass: true },
  { id: "EOA-SIG-001", cat: "Signature",    sev: "high", pass: true },
  { id: "EOA-SIG-002", cat: "Signature",    sev: "high", pass: true },
  { id: "EOA-SIG-003", cat: "Signature",    sev: "high", pass: true },
  { id: "EOA-VID-001", cat: "Verification", sev: "high", pass: true },
  { id: "EOA-VID-002", cat: "Verification", sev: "med",  pass: true },
  { id: "EOA-OCR-001", cat: "OCR",          sev: "low",  pass: true },
  { id: "EOA-SEM-001", cat: "Semantics",    sev: "med",  pass: true },
];

const DEMO_ACCOUNTS = [
  { email: "reviewer@demo.local",  role: "Reviewer",  name: "Adarsh K. Rao",    color: "#FF5E1E" },
  { email: "applicant@demo.local", role: "Applicant", name: "Vidya Institute",   color: "#2563EB" },
  { email: "admin@demo.local",     role: "Admin",     name: "Dr. M. Sundaram",  color: "#7C3AED" },
];

const DEMO_PW = typeof atob !== "undefined" ? atob("ZGVtbzEyMzQ=") : "demo1234";

const TICKER_ITEMS = [
  "AICTE APH 2024–27 Chapter II · 25 Automated Statutory Rules",
  "SIH 2026 · Team QTPies · Problem Statement 26261",
  "Zero hallucination extraction via coordinate grounding",
  "SHA-256 Merkle chain tamper detection · Sub-2.8s pipeline",
  "153 backend unit tests · 12/12 Audit Pillars Passed",
  "Real-time NLP + OCR · DTCP / Fire NOC / Cadre Ratio checks",
];

/* ─── Merkle Chain Bento ─────────────────────────────────────────────────── */

function MerkleHashChain() {
  const [nodes, setNodes] = useState<HashNode[]>([]);
  const [tamperedIdx, setTamperedIdx] = useState<number | null>(null);
  const [rebuilding, setRebuilding] = useState(false);
  const DOCS = ["EoA Application", "Land Certificate", "Fire NOC", "Affiliation Order", "Struct. Certificate"];

  const buildChain = useCallback(async (tamper: number | null = null) => {
    const result: HashNode[] = [];
    for (let i = 0; i < DOCS.length; i++) {
      const prevHash = i === 0 ? "0000000000000000000000000000" : result[i - 1].hash;
      const raw = DOCS[i] + prevHash + (tamper === i ? "-TAMPERED" : "");
      const hash = await sha256(raw);
      result.push({ id: `B${i + 1}`, label: DOCS[i], hash, prevHash, tampered: tamper === i });
    }
    setNodes(result);
  }, []);

  useEffect(() => { void buildChain(); }, [buildChain]);

  const isCorrupted = (node: HashNode, idx: number): boolean => {
    if (idx === 0) return node.tampered;
    const prev = nodes[idx - 1];
    return node.tampered || (prev ? isCorrupted(prev, idx - 1) : false);
  };

  const tamper = async (idx: number) => {
    if (tamperedIdx !== null) return;
    setTamperedIdx(idx);
    await buildChain(idx);
  };

  const reanchor = async () => {
    setRebuilding(true);
    await new Promise(r => setTimeout(r, 800));
    setTamperedIdx(null);
    await buildChain(null);
    setRebuilding(false);
  };

  return (
    <div style={{ padding: "1.25rem", height: "100%", display: "flex", flexDirection: "column", gap: "0.6rem" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.25rem" }}>
        <div>
          <div style={{ fontSize: "0.65rem", fontFamily: "var(--mono)", color: "var(--ink-3)", letterSpacing: "0.1em", textTransform: "uppercase" }}>Cryptographic Audit Trail</div>
          <div style={{ fontSize: "0.95rem", fontWeight: 700, color: "var(--ink)", letterSpacing: "-0.02em" }}>SHA-256 Merkle Chain</div>
        </div>
        {tamperedIdx !== null && (
          <button onClick={reanchor} disabled={rebuilding} style={{ fontSize: "0.72rem", fontWeight: 700, padding: "0.3rem 0.7rem", borderRadius: "6px", border: "1px solid #FF5E1E", background: rebuilding ? "#FFF7ED" : "#FF5E1E", color: rebuilding ? "#FF5E1E" : "#fff", cursor: "pointer", transition: "all 0.2s" }}>
            {rebuilding ? "⟳ Re-anchoring…" : "↺ Re-anchor chain"}
          </button>
        )}
      </div>
      <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "5px", overflow: "hidden" }}>
        {nodes.map((node, i) => {
          const corrupt = isCorrupted(node, i);
          return (
            <div key={node.id} onClick={() => void tamper(i)} style={{ display: "flex", alignItems: "center", gap: "8px", padding: "7px 10px", borderRadius: "8px", border: `1px solid ${corrupt ? "#FECACA" : "#E4E4E7"}`, background: corrupt ? "#FEF2F2" : "#F4F3EF", cursor: tamperedIdx === null ? "pointer" : "default", transition: "all 0.3s ease" }}>
              <div style={{ width: "28px", height: "28px", borderRadius: "6px", background: corrupt ? "#BA1A1A" : "#FF5E1E", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.65rem", fontWeight: 700, color: "#fff", flexShrink: 0 }}>{node.id}</div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: "0.72rem", fontWeight: 600, color: corrupt ? "#BA1A1A" : "var(--ink)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{node.label} {corrupt && "⚠ CHAIN BROKEN"}</div>
                <div style={{ fontFamily: "var(--mono)", fontSize: "0.62rem", color: corrupt ? "#BA1A1A" : "var(--ink-3)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{node.hash}…</div>
              </div>
              {tamperedIdx === null && <div style={{ fontSize: "0.6rem", color: "var(--ink-3)", opacity: 0.6, flexShrink: 0 }}>tamper?</div>}
            </div>
          );
        })}
      </div>
      <div style={{ fontSize: "0.65rem", color: "var(--ink-3)", fontFamily: "var(--mono)", textAlign: "center" }}>Click any block to simulate tamper · Re-anchor to verify</div>
    </div>
  );
}

/* ─── Rule Matrix Bento ─────────────────────────────────────────────────── */

function RuleMatrix() {
  const [filter, setFilter] = useState<string>("all");
  const cats = ["all", ...Array.from(new Set(RULES_MATRIX.map(r => r.cat)))];
  const filtered = filter === "all" ? RULES_MATRIX : RULES_MATRIX.filter(r => r.cat === filter);
  const passCount = RULES_MATRIX.filter(r => r.pass).length;
  const failCount = RULES_MATRIX.length - passCount;
  const sevColor = (sev: string) => sev === "high" ? "#BA1A1A" : sev === "med" ? "#D97706" : "#2563EB";

  return (
    <div style={{ padding: "1.25rem", height: "100%", display: "flex", flexDirection: "column", gap: "0.75rem", overflow: "hidden" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <div style={{ fontSize: "0.65rem", fontFamily: "var(--mono)", color: "var(--ink-3)", letterSpacing: "0.1em", textTransform: "uppercase" }}>AICTE APH 2024–27 Chapter II</div>
          <div style={{ fontSize: "0.95rem", fontWeight: 700, color: "var(--ink)", letterSpacing: "-0.02em" }}>Rule Matrix Inspector</div>
        </div>
        <div style={{ display: "flex", gap: "8px" }}>
          <span style={{ fontSize: "0.72rem", padding: "2px 8px", borderRadius: "999px", background: "#ECFDF5", border: "1px solid #A7F3D0", color: "#059669", fontWeight: 700 }}>{passCount} PASS</span>
          <span style={{ fontSize: "0.72rem", padding: "2px 8px", borderRadius: "999px", background: "#FEF2F2", border: "1px solid #FECACA", color: "#BA1A1A", fontWeight: 700 }}>{failCount} FAIL</span>
        </div>
      </div>
      <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
        {cats.map(c => (
          <button key={c} onClick={() => setFilter(c)} style={{ fontSize: "0.65rem", fontWeight: 600, padding: "3px 8px", borderRadius: "6px", border: `1px solid ${filter === c ? "#FF5E1E" : "#E4E4E7"}`, background: filter === c ? "#FF5E1E" : "#F4F3EF", color: filter === c ? "#fff" : "#52525B", cursor: "pointer", transition: "all 0.15s", textTransform: "uppercase", letterSpacing: "0.05em" }}>{c}</button>
        ))}
      </div>
      <div style={{ flex: 1, overflowY: "auto", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "5px" }}>
        {filtered.map(rule => (
          <div key={rule.id} style={{ display: "flex", alignItems: "center", gap: "6px", padding: "6px 8px", borderRadius: "6px", border: `1px solid ${rule.pass ? "#E4E4E7" : "#FECACA"}`, background: rule.pass ? "#F4F3EF" : "#FEF2F2" }}>
            <div style={{ width: "14px", height: "14px", borderRadius: "50%", background: rule.pass ? "#059669" : "#BA1A1A", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
              <span style={{ fontSize: "8px", color: "#fff", fontWeight: 800 }}>{rule.pass ? "✓" : "✗"}</span>
            </div>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontSize: "0.65rem", fontWeight: 700, color: "var(--ink)", fontFamily: "var(--mono)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{rule.id}</div>
              <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: sevColor(rule.sev), display: "inline-block" }} />
            </div>
          </div>
        ))}
      </div>
      <div style={{ fontSize: "0.65rem", color: "var(--ink-3)", fontFamily: "var(--mono)", textAlign: "center" }}>{filtered.length} of 25 rules · Click categories to filter</div>
    </div>
  );
}

/* ─── Metrics strip ──────────────────────────────────────────────────────── */

function MetricStrip() {
  const metrics = [
    { val: "25/25", label: "Rules Automated", sub: "AICTE APH Ch. II" },
    { val: "0ms", label: "Hallucination Rate", sub: "Grounded extraction" },
    { val: "100%", label: "Coordinate Ground.", sub: "Bounding-box anchored" },
    { val: "<2.8s", label: "Pipeline Latency", sub: "End-to-end median" },
  ];
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", height: "100%" }}>
      {metrics.map((m, i) => (
        <div key={m.label} style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "1.5rem 1rem", borderRight: i < 3 ? "1px solid #E4E4E7" : undefined, gap: "0.3rem" }}>
          <div style={{ fontSize: "clamp(1.4rem, 3vw, 2.2rem)", fontWeight: 900, letterSpacing: "-0.04em", color: "#FF5E1E", fontFamily: "Space Grotesk, sans-serif", lineHeight: 1 }}>{m.val}</div>
          <div style={{ fontSize: "0.78rem", fontWeight: 700, color: "#0E1013", textAlign: "center", lineHeight: 1.2 }}>{m.label}</div>
          <div style={{ fontSize: "0.65rem", color: "#52525B", textAlign: "center", fontFamily: "var(--mono)", letterSpacing: "0.02em" }}>{m.sub}</div>
        </div>
      ))}
    </div>
  );
}

/* ─── Sandbox Launcher ───────────────────────────────────────────────────── */

function SandboxLauncher() {
  const [loading, setLoading] = useState<string | null>(null);

  const launch = async (email: string, role: string) => {
    setLoading(role);
    await new Promise(r => setTimeout(r, 600));
    window.sessionStorage.setItem("demo_email", email);
    window.sessionStorage.setItem("demo_pw", DEMO_PW);
    navigate("/login");
  };

  return (
    <div className="login-card" style={{ padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1rem", height: "100%" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
        <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#059669", boxShadow: "0 0 8px #059669" }} />
        <div style={{ fontSize: "0.65rem", fontFamily: "var(--mono)", color: "var(--ink-3)", letterSpacing: "0.1em", textTransform: "uppercase" }}>Sandbox Active</div>
      </div>
      <div>
        <div style={{ fontSize: "1.05rem", fontWeight: 800, color: "var(--ink)", letterSpacing: "-0.02em" }}>Demo Persona Switcher</div>
        <div style={{ fontSize: "0.78rem", color: "var(--ink-3)", marginTop: "0.2rem" }}>One-click institution access</div>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: "8px", flex: 1 }}>
        {DEMO_ACCOUNTS.map(a => (
          <button key={a.email} className="demo-user" onClick={() => void launch(a.email, a.role)} disabled={loading !== null} style={{ display: "flex", alignItems: "center", gap: "0.75rem", padding: "0.7rem 0.95rem", border: `1px solid ${loading === a.role ? a.color : "#E4E4E7"}`, borderRadius: "10px", background: loading === a.role ? `${a.color}14` : "#F4F3EF", cursor: loading ? "wait" : "pointer", transition: "all 0.2s", textAlign: "left", width: "100%" }}>
            <div style={{ width: "32px", height: "32px", borderRadius: "8px", background: `${a.color}20`, border: `1px solid ${a.color}40`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
              <div style={{ width: "10px", height: "10px", borderRadius: "50%", background: a.color }} />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: "0.84rem", fontWeight: 700, color: "#0E1013" }}>{a.role}</div>
              <div style={{ fontSize: "0.7rem", color: "#52525B" }}>{a.name}</div>
            </div>
            {loading === a.role && <div style={{ width: "14px", height: "14px", borderRadius: "50%", border: `2px solid ${a.color}`, borderTopColor: "transparent", animation: "spin 0.7s linear infinite", flexShrink: 0 }} />}
          </button>
        ))}
      </div>
      <div style={{ borderTop: "1px solid #E4E4E7", paddingTop: "0.8rem" }}>
        <div style={{ fontSize: "0.65rem", color: "var(--ink-3)", textAlign: "center", fontFamily: "var(--mono)" }}>SIH-DEMO-014 · SIH-DEMO-015 · EOA-DEMO-001 pre-seeded</div>
      </div>
    </div>
  );
}

/* ─── Live Ticker ────────────────────────────────────────────────────────── */

function Ticker() {
  const [offset, setOffset] = useState(0);
  const raf = useRef<number>(0);
  const startTs = useRef<number | null>(null);
  const innerRef = useRef<HTMLDivElement>(null);
  const speed = 50;

  useEffect(() => {
    const animate = (ts: number) => {
      if (!startTs.current) startTs.current = ts;
      const elapsed = (ts - startTs.current) / 1000;
      const inner = innerRef.current;
      if (inner) {
        const w = inner.scrollWidth / 2;
        if (w > 0) setOffset((elapsed * speed) % w);
      }
      raf.current = requestAnimationFrame(animate);
    };
    raf.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(raf.current);
  }, []);

  return (
    <div style={{ overflow: "hidden", background: "#0E1013", borderTop: "1px solid #1A1C1E", borderBottom: "1px solid #1A1C1E", padding: "0.5rem 0" }}>
      <div ref={innerRef} style={{ display: "flex", whiteSpace: "nowrap", transform: `translateX(-${offset}px)`, willChange: "transform" }}>
        {[...TICKER_ITEMS, ...TICKER_ITEMS].map((item, i) => (
          <span key={i} style={{ display: "inline-flex", alignItems: "center", gap: "0.75rem", padding: "0 2rem" }}>
            <span style={{ fontSize: "0.72rem", fontWeight: 600, color: "#F9F8F5", fontFamily: "Space Grotesk, sans-serif", letterSpacing: "0.03em" }}>{item}</span>
            <span style={{ width: "4px", height: "4px", borderRadius: "50%", background: "#FF5E1E", display: "inline-block", flexShrink: 0 }} />
          </span>
        ))}
      </div>
    </div>
  );
}

/* ─── Crosshair Decoration ───────────────────────────────────────────────── */

function Crosshair({ style }: { style?: React.CSSProperties }) {
  return (
    <div style={{ position: "absolute", width: "16px", height: "16px", ...style, pointerEvents: "none", zIndex: 1 }}>
      <div style={{ position: "absolute", top: "50%", left: 0, right: 0, height: "1px", background: "#E4E4E7", transform: "translateY(-50%)" }} />
      <div style={{ position: "absolute", left: "50%", top: 0, bottom: 0, width: "1px", background: "#E4E4E7", transform: "translateX(-50%)" }} />
    </div>
  );
}

/* ─── Bento Card ─────────────────────────────────────────────────────────── */

function BentoCard({ children, style, label, accent = false }: {
  children: React.ReactNode;
  style?: React.CSSProperties;
  label?: string;
  accent?: boolean;
}) {
  const cardRef = useRef<HTMLDivElement>(null);

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    const card = cardRef.current;
    if (!card) return;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const cx = rect.width / 2;
    const cy = rect.height / 2;
    const rx = ((y - cy) / cy) * -4;
    const ry = ((x - cx) / cx) * 4;
    card.style.transform = `perspective(1200px) rotateX(${rx}deg) rotateY(${ry}deg) translateY(-2px)`;
    card.style.boxShadow = "0 16px 48px -8px rgba(14,16,19,0.12), 0 4px 16px rgba(255,94,30,0.06)";
  }, []);

  const handleMouseLeave = useCallback(() => {
    const card = cardRef.current;
    if (!card) return;
    card.style.transform = "perspective(1200px) rotateX(0deg) rotateY(0deg) translateY(0px)";
    card.style.boxShadow = "inset 0 1px 0 0 rgba(255,255,255,0.9), 0 1px 3px 0 rgba(14,16,19,0.04)";
  }, []);

  return (
    <div ref={cardRef} onMouseMove={handleMouseMove} onMouseLeave={handleMouseLeave} style={{ background: "#fff", border: "1px solid #E4E4E7", borderRadius: "16px", position: "relative", overflow: "hidden", transition: "box-shadow 0.2s ease, transform 0.15s ease", boxShadow: "inset 0 1px 0 0 rgba(255,255,255,0.9), 0 1px 3px 0 rgba(14,16,19,0.04)", transformStyle: "preserve-3d", ...style }}>
      <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: "1px", background: "rgba(255,255,255,0.9)", pointerEvents: "none", zIndex: 2 }} />
      <Crosshair style={{ top: -8, left: -8 }} />
      <Crosshair style={{ top: -8, right: -8 }} />
      <Crosshair style={{ bottom: -8, left: -8 }} />
      <Crosshair style={{ bottom: -8, right: -8 }} />
      {accent && <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: "3px", background: "linear-gradient(90deg, #FF5E1E, #FF8050)", borderRadius: "16px 16px 0 0", zIndex: 3 }} />}
      {label && (
        <div style={{ position: "absolute", top: accent ? "18px" : "12px", left: "14px", fontSize: "0.6rem", fontWeight: 700, letterSpacing: "0.12em", textTransform: "uppercase", color: "#52525B", fontFamily: "Space Grotesk, sans-serif", zIndex: 4, display: "flex", alignItems: "center", gap: "5px" }}>
          <span style={{ width: "5px", height: "5px", borderRadius: "50%", background: "#FF5E1E" }} />
          {label}
        </div>
      )}
      {children}
    </div>
  );
}

/* ─── Hero ───────────────────────────────────────────────────────────────── */

function HeroSection() {
  const [tick, setTick] = useState(0);
  const phrases = ["Grounded.", "Auditable.", "Trustworthy."];
  useEffect(() => { const id = setInterval(() => setTick(t => (t + 1) % phrases.length), 2200); return () => clearInterval(id); }, []);

  return (
    <section style={{ background: "#0E1013", position: "relative", overflow: "hidden", padding: "5rem 3rem 4rem", borderBottom: "1px solid #1A1C1E" }}>
      <div style={{ position: "absolute", inset: 0, backgroundImage: "linear-gradient(rgba(255,94,30,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,94,30,0.04) 1px, transparent 1px)", backgroundSize: "48px 48px", pointerEvents: "none" }} />
      <div style={{ position: "absolute", top: "-20%", left: "40%", width: "600px", height: "600px", borderRadius: "50%", background: "radial-gradient(circle at center, rgba(255,94,30,0.12) 0%, transparent 65%)", pointerEvents: "none" }} />
      <div style={{ position: "relative", zIndex: 2, maxWidth: "1200px", margin: "0 auto" }}>
        <div style={{ display: "inline-flex", alignItems: "center", gap: "8px", padding: "0.3rem 0.85rem", borderRadius: "999px", border: "1px solid rgba(255,94,30,0.3)", background: "rgba(255,94,30,0.08)", marginBottom: "1.75rem" }}>
          <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#059669", boxShadow: "0 0 8px #059669", animation: "blink-green 2s ease-in-out infinite" }} />
          <span style={{ fontSize: "0.7rem", fontWeight: 700, color: "#FF5E1E", letterSpacing: "0.08em", fontFamily: "Space Grotesk, sans-serif", textTransform: "uppercase" }}>System Operational · AICTE APH 2024–27 · SIH 2026261</span>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: "2rem", alignItems: "start" }}>
          <div>
            <h1 style={{ fontSize: "clamp(2.5rem, 5vw, 4.5rem)", fontWeight: 900, letterSpacing: "-0.04em", lineHeight: 1.08, color: "#F9F8F5", margin: "0 0 0.5rem", fontFamily: "Space Grotesk, sans-serif" }}>
              Institutional Verification
              <span style={{ display: "block", color: "#FF5E1E", transition: "opacity 0.3s" }}>{phrases[tick]}</span>
            </h1>
            <p style={{ fontSize: "1.05rem", color: "#5A6070", maxWidth: "600px", lineHeight: 1.6, margin: "1rem 0 2rem", fontFamily: "Hanken Grotesk, sans-serif" }}>
              High-assurance document verification for AICTE Extension of Approval. 25 automated statutory rules, cryptographic audit trails, and zero-hallucination coordinate grounding.
            </p>
            <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
              <button className="btn-press" onClick={() => navigate("/cases")} style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", padding: "0.75rem 1.5rem", borderRadius: "10px", fontSize: "0.9rem", fontWeight: 700, cursor: "pointer", fontFamily: "Space Grotesk, sans-serif" }}>
                Open Review Queue →
              </button>
              <button onClick={() => navigate("/login")} style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", padding: "0.75rem 1.5rem", borderRadius: "10px", border: "1px solid rgba(255,255,255,0.15)", background: "rgba(255,255,255,0.06)", color: "#F9F8F5", fontSize: "0.9rem", fontWeight: 600, cursor: "pointer", fontFamily: "Space Grotesk, sans-serif", transition: "all 0.2s" }}>
                🪪 Sign In
              </button>
            </div>
          </div>
          <div style={{ flexShrink: 0, textAlign: "right" }}>
            <div style={{ fontFamily: "var(--mono)", fontSize: "0.62rem", color: "#3A3E48", letterSpacing: "0.08em", textTransform: "uppercase" }}>
              <div>SIH 2026 · TEAM QTPIES</div>
              <div style={{ marginTop: "0.25rem" }}>PROBLEM STMT 26261</div>
              <div style={{ marginTop: "0.5rem", color: "#FF5E1E", fontWeight: 700 }}>v1.0.0 PRODUCTION</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   MAIN LANDING PAGE
   ═══════════════════════════════════════════════════════════════════════════ */

export function LandingPage() {
  return (
    <div style={{ fontFamily: "var(--font)", background: "#F9F8F5", minHeight: "100vh" }}>
      {/* Sticky top nav */}
      <header style={{ position: "sticky", top: 0, zIndex: 100, background: "rgba(249,248,245,0.92)", backdropFilter: "blur(16px)", WebkitBackdropFilter: "blur(16px)", borderBottom: "1px solid #E4E4E7", padding: "0.7rem 2rem", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <div style={{ width: "32px", height: "32px", borderRadius: "8px", background: "linear-gradient(135deg, rgba(255,94,30,0.12), rgba(255,94,30,0.04))", border: "1px solid rgba(255,94,30,0.28)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <rect x="3" y="2.5" width="14" height="19" rx="2" stroke="#FF5E1E" strokeWidth="2" />
              <path d="M6.5 7.5h7M6.5 11.5h7M6.5 15.5h4" stroke="#FF5E1E" strokeWidth="2" strokeLinecap="round" />
              <circle cx="17.5" cy="17" r="4" fill="#F9F8F5" stroke="#FF5E1E" strokeWidth="2" />
              <path d="M20.5 20 23 22.5" stroke="#FF5E1E" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </div>
          <span style={{ fontWeight: 800, fontSize: "1.05rem", letterSpacing: "-0.02em", color: "#0E1013", fontFamily: "Space Grotesk, sans-serif" }}>VeriScope</span>
          <span style={{ fontSize: "0.65rem", fontWeight: 700, padding: "0.15rem 0.5rem", borderRadius: "999px", background: "#F4F3EF", border: "1px solid #E4E4E7", color: "#52525B", letterSpacing: "0.05em", textTransform: "uppercase" }}>SIH26261 · AICTE</span>
        </div>
        <nav style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
          {[["#/cases", "Review Queue"], ["#/coverage", "APH Coverage"], ["#/analytics", "Analytics"]].map(([href, label]) => (
            <a key={href} href={href} style={{ fontSize: "0.85rem", fontWeight: 600, color: "#52525B", textDecoration: "none", padding: "0.3rem 0.7rem", borderRadius: "8px", transition: "all 0.15s" }}>{label}</a>
          ))}
          <button onClick={() => navigate("/login")} style={{ fontSize: "0.85rem", fontWeight: 700, padding: "0.38rem 1rem", borderRadius: "8px", border: "1px solid #FF5E1E", background: "#FF5E1E", color: "#fff", cursor: "pointer", fontFamily: "Space Grotesk, sans-serif", transition: "all 0.15s" }}>Sign In</button>
        </nav>
      </header>

      <HeroSection />
      <Ticker />

      {/* Bento Grid */}
      <section style={{ maxWidth: "1400px", margin: "0 auto", padding: "3rem 2rem 4rem" }}>
        <div style={{ marginBottom: "2rem", display: "flex", alignItems: "flex-end", justifyContent: "space-between" }}>
          <div>
            <div style={{ fontSize: "0.65rem", fontFamily: "var(--mono)", color: "#52525B", letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: "0.3rem" }}>· VERISCOPE PLATFORM</div>
            <h2 style={{ fontSize: "clamp(1.4rem, 3vw, 2.2rem)", fontWeight: 800, letterSpacing: "-0.03em", color: "#0E1013", margin: 0, fontFamily: "Space Grotesk, sans-serif" }}>Interactive Platform Overview</h2>
          </div>
          <div style={{ fontFamily: "var(--mono)", fontSize: "0.65rem", color: "#52525B", textAlign: "right" }}>
            <div>25 RULES AUTOMATED</div>
            <div style={{ color: "#FF5E1E", fontWeight: 700, marginTop: "2px" }}>AICTE CH. II 2024–27</div>
          </div>
        </div>

        {/* Row 1 */}
        <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr 1fr", gap: "16px", marginBottom: "16px" }}>
          <BentoCard label="Array Rotation Telemetry" accent style={{ minHeight: "520px" }}>
            <div style={{ paddingTop: "42px", height: "100%" }}><CircularReadings3D /></div>
          </BentoCard>
          <BentoCard label="3D Identity Badge" style={{ minHeight: "520px", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", background: "#0E1013", border: "1px solid #2B2E35" }}>
            <div style={{ paddingTop: "32px", display: "flex", flexDirection: "column", alignItems: "center", width: "100%" }}>
              <LanyardBadge name="Adarsh K. Rao" role="Senior Reviewer" org="SIH26261 · AICTE" badgeId="VS-2026-0042" accentColor="#FF5E1E" width={210} autoSwing={true} />
            </div>
          </BentoCard>
          <BentoCard label="Cryptographic Trail" style={{ minHeight: "520px" }}>
            <div style={{ paddingTop: "36px", height: "100%" }}><MerkleHashChain /></div>
          </BentoCard>
        </div>

        {/* Row 2 */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1.6fr 1fr", gap: "16px", marginBottom: "16px" }}>
          <BentoCard label="Chapter II Rulebook" style={{ minHeight: "380px" }}>
            <div style={{ paddingTop: "36px", height: "100%", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <DossierHologram3D step={1} />
            </div>
          </BentoCard>
          <BentoCard label="Rule Matrix Inspector" accent style={{ minHeight: "380px" }}>
            <div style={{ paddingTop: "42px", height: "100%" }}><RuleMatrix /></div>
          </BentoCard>
          <BentoCard label="Demo Sandbox" style={{ minHeight: "380px" }}>
            <div style={{ paddingTop: "36px", height: "100%" }}><SandboxLauncher /></div>
          </BentoCard>
        </div>

        {/* Row 3 — metrics strip */}
        <BentoCard accent style={{ minHeight: "120px" }}>
          <div style={{ paddingTop: "4px" }}><MetricStrip /></div>
        </BentoCard>
      </section>

      {/* Footer */}
      <footer style={{ borderTop: "1px solid #E4E4E7", background: "#0E1013", padding: "2rem 3rem", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "1rem" }}>
        <div>
          <div style={{ fontSize: "0.85rem", fontWeight: 800, color: "#F9F8F5", letterSpacing: "-0.02em", fontFamily: "Space Grotesk, sans-serif" }}>VeriScope</div>
          <div style={{ fontSize: "0.68rem", color: "#3A3E48", marginTop: "0.2rem", fontFamily: "var(--mono)" }}>Automated checks assist human review. Humans make every final decision.</div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#059669", boxShadow: "0 0 8px #059669" }} />
            <span style={{ fontSize: "0.68rem", color: "#5A6070", fontFamily: "var(--mono)" }}>System operational</span>
          </div>
          <span style={{ fontSize: "0.68rem", color: "#3A3E48", fontFamily: "var(--mono)" }}>AICTE APH 2024–27 · Chapter II · 25 Rules</span>
          <span style={{ fontSize: "0.68rem", color: "#3A3E48", fontFamily: "var(--mono)" }}>© 2026 SIH Team QTPies</span>
        </div>
      </footer>

      <style>{`
        @keyframes blink-green { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
