import React, { useCallback, useRef, useState } from "react";

export function DossierHologram3D({ step }: { step: 1 | 2 }) {
  const [flipped, setFlipped] = useState(false);
  const cardRef = useRef<HTMLDivElement>(null);
  const glareRef = useRef<HTMLDivElement>(null);

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    const card = cardRef.current;
    if (!card) return;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const cx = rect.width / 2;
    const cy = rect.height / 2;
    const rotateX = ((y - cy) / cy) * -12;
    const rotateY = ((x - cx) / cx) * 14;

    card.style.transform = `perspective(900px) rotateX(${rotateX}deg) rotateY(${rotateY + (flipped ? 180 : 0)}deg) translateY(-6px)`;

    if (glareRef.current) {
      const mx = (x / rect.width) * 100;
      const my = (y / rect.height) * 100;
      glareRef.current.style.background = `radial-gradient(circle at ${mx}% ${my}%, rgba(255,255,255,0.3) 0%, transparent 65%)`;
      glareRef.current.style.opacity = "1";
    }
  }, [flipped]);

  const handleMouseLeave = useCallback(() => {
    const card = cardRef.current;
    if (!card) return;
    card.style.transform = `perspective(900px) rotateX(0deg) rotateY(${flipped ? 180 : 0}deg) translateY(0px)`;
    if (glareRef.current) glareRef.current.style.opacity = "0";
  }, [flipped]);

  const toggleFlip = () => {
    setFlipped(!flipped);
  };

  return (
    <div className="dossier-3d-wrap">
      <div
        ref={cardRef}
        className={`dossier-card-3d ${flipped ? "is-flipped" : ""}`}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        onClick={toggleFlip}
        title="Click to flip dossier card"
      >
        {/* Dynamic glare overlay */}
        <div ref={glareRef} className="dossier-glare" />

        {/* ── FRONT FACE ── */}
        <div className="dossier-face dossier-front">
          <div className="dossier-top-badge">
            <span className="hologram-dot" />
            <span>AICTE APH 2024–27 CHAPTER II</span>
            <span className="flip-hint">⟳ Click to flip</span>
          </div>

          <div className="dossier-seal-wrap">
            <div className="dossier-gold-seal">
              <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 6v6l4 2" />
                <circle cx="12" cy="12" r="4" strokeDasharray="2 2" />
              </svg>
            </div>
            <div className="dossier-seal-text">
              <strong>STATUTORY COMPLIANCE DOSSIER</strong>
              <span>Extension of Approval (EoA) Audit</span>
            </div>
          </div>

          <div className="dossier-stages">
            <div className={`stage-row ${step === 1 ? "active" : "done"}`}>
              <span className="stage-num">01</span>
              <div>
                <div className="stage-title">Regulatory Metadata & Mandate</div>
                <div className="stage-sub">Institutional Ref, Approval Program, Legal Jurisdiction</div>
              </div>
            </div>
            <div className={`stage-row ${step === 2 ? "active" : ""}`}>
              <span className="stage-num">02</span>
              <div>
                <div className="stage-title">Statutory Documents Ingestion</div>
                <div className="stage-sub">DTCP Plan, Fire NOC, FDR Corpus, Anti-Ragging Affidavit</div>
              </div>
            </div>
            <div className="stage-row">
              <span className="stage-num">03</span>
              <div>
                <div className="stage-title">Autonomous Rule Verification</div>
                <div className="stage-sub">AI Vision OCR, Land Norms, Signature & Date cross-checks</div>
              </div>
            </div>
          </div>

          <div className="dossier-footer">
            <span>Security Hologram Protected</span>
            <span className="dossier-code">SPEC-APH-SIH26261</span>
          </div>
        </div>

        {/* ── BACK FACE ── */}
        <div className="dossier-face dossier-back">
          <div className="dossier-top-badge">
            <span>APH 2024–27 AUDIT CHECKLIST</span>
            <span className="flip-hint">⟳ Click to return</span>
          </div>

          <div className="checklist-items">
            <div className="check-item">
              <span className="check-bullet">✓</span>
              <div>
                <strong>Land Area (Chapter II.1)</strong>
                <p>7.5 Acres minimum in rural / 2.5 in urban limits.</p>
              </div>
            </div>
            <div className="check-item">
              <span className="check-bullet">✓</span>
              <div>
                <strong>Faculty Cadre Ratio (Chapter II.4)</strong>
                <p>1:20 mandatory ratio for technical engineering colleges.</p>
              </div>
            </div>
            <div className="check-item">
              <span className="check-bullet">✓</span>
              <div>
                <strong>Fire Safety & DTCP Building Plan</strong>
                <p>Valid NOC from Competent State Authority + Occupancy certificate.</p>
              </div>
            </div>
            <div className="check-item">
              <span className="check-bullet">✓</span>
              <div>
                <strong>Joint Corpus FDR</strong>
                <p>Pledged in the joint name of Society/Trust and AICTE.</p>
              </div>
            </div>
          </div>

          <div className="dossier-footer">
            <span>Chapter II Verification Rules Active</span>
            <span className="dossier-code">PASS/FLAG TRIAGE</span>
          </div>
        </div>
      </div>
    </div>
  );
}
