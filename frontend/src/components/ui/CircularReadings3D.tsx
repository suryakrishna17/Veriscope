import React, { useCallback, useEffect, useRef, useState } from "react";

export interface TelemetryReading {
  id: string;
  code: string;
  label: string;
  val: string;
  metric: string;
  status: "verified" | "flagged" | "auditing";
  source: string;
}

const DEFAULT_READINGS: TelemetryReading[] = [
  {
    id: "R1",
    code: "LAND-7.5A",
    label: "Campus Land Area",
    val: "8.40 Acres",
    metric: "Min Req: 7.50 Acres",
    status: "verified",
    source: "DTCP Master Registry",
  },
  {
    id: "R2",
    code: "FCR-1:20",
    label: "Faculty Cadre Ratio",
    val: "1 : 18.2",
    metric: "Norm: 1:20 UG Tech",
    status: "verified",
    source: "Pay Band Verification",
  },
  {
    id: "R3",
    code: "NOC-FIRE-26",
    label: "Fire Safety Clearance",
    val: "Valid 2026",
    metric: "State Fire Service Dept",
    status: "verified",
    source: "DFS Portal API",
  },
  {
    id: "R4",
    code: "BLD-DTCP-AP",
    label: "Approved Building Plan",
    val: "FAR 1.84",
    metric: "Max Allowable: 2.00",
    status: "verified",
    source: "Municipal Comm.",
  },
  {
    id: "R5",
    code: "AFF-RAG-2026",
    label: "Anti-Ragging Affidavit",
    val: "100% Stamped",
    metric: "E-Stamp Certificate",
    status: "verified",
    source: "SHCIL e-Notary",
  },
  {
    id: "R6",
    code: "BIO-ATT-90",
    label: "Biometric Attendance",
    val: "91.4% Monthly",
    metric: "Min Mandate: 75%",
    status: "auditing",
    source: "Central AICTE Gateway",
  },
  {
    id: "R7",
    code: "CORP-RES-50L",
    label: "Corpus Fund Deposit",
    val: "₹65.0 Lakhs",
    metric: "Joint FDR with AICTE",
    status: "verified",
    source: "SBI Public Sector Bank",
  },
];

/* Helper: Three reversals algorithm */
function reverseSlice<T>(arr: T[], start: number, end: number) {
  while (start < end) {
    const tmp = arr[start];
    arr[start] = arr[end];
    arr[end] = tmp;
    start++;
    end--;
  }
}

export function rotateArrayRight<T>(arr: T[], kInput: bigint | number): {
  result: T[];
  effK: number;
  n: number;
} {
  const n = arr.length;
  if (n <= 1) return { result: [...arr], effK: 0, n };
  const kBig = typeof kInput === "bigint" ? kInput : BigInt(kInput);
  const nBig = BigInt(n);
  const effK = Number(((kBig % nBig) + nBig) % nBig);
  if (effK === 0) return { result: [...arr], effK: 0, n };

  const copy = [...arr];
  // 1. Reverse all
  reverseSlice(copy, 0, n - 1);
  // 2. Reverse first effK
  reverseSlice(copy, 0, effK - 1);
  // 3. Reverse remaining n - effK
  reverseSlice(copy, effK, n - 1);

  return { result: copy, effK, n };
}

export function CircularReadings3D({ items }: { items?: TelemetryReading[] } = {}) {
  const initial = items && items.length > 0 ? items : DEFAULT_READINGS;
  const [readings, setReadings] = useState<TelemetryReading[]>(initial);

  useEffect(() => {
    if (items && items.length > 0) {
      setReadings(items);
    }
  }, [items]);
  const [ticksCount, setTicksCount] = useState<number>(0);
  const [kInput, setKInput] = useState<string>("2");
  const [autoTick, setAutoTick] = useState<boolean>(false);
  const [viewStep, setViewStep] = useState<number | null>(null);
  const [stepData, setStepData] = useState<{
    original: TelemetryReading[];
    step1: TelemetryReading[];
    step2: TelemetryReading[];
    step3: TelemetryReading[];
    effK: number;
  } | null>(null);

  // 3D Cylinder rotation state
  const [rotY, setRotY] = useState<number>(0);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const dragStartX = useRef<number>(0);
  const dragStartRot = useRef<number>(0);

  const n = readings.length;
  const radius = Math.max(260, Math.round(n * 42)); // 3D radius based on items

  // Tick step forward (rotate right by 1)
  const handleTick = useCallback((stepCount = 1) => {
    setReadings((prev) => {
      const { result } = rotateArrayRight(prev, stepCount);
      return result;
    });
    setTicksCount((c) => c + stepCount);
    // Also smoothly rotate 3D cylinder
    setRotY((r) => r - (360 / n) * stepCount);
  }, [n]);

  // Rotate by custom K with 3-reversals calculation
  const handleRotateByK = useCallback(() => {
    const kNum = parseInt(kInput, 10);
    if (isNaN(kNum)) return;

    const copy = [...readings];
    const nLen = copy.length;
    const effK = ((kNum % nLen) + nLen) % nLen;

    // Precalculate the 3 reversal steps for visualization
    const s1 = [...copy];
    reverseSlice(s1, 0, nLen - 1);

    const s2 = [...s1];
    reverseSlice(s2, 0, effK - 1);

    const s3 = [...s2];
    reverseSlice(s3, effK, nLen - 1);

    setStepData({
      original: copy,
      step1: s1,
      step2: s2,
      step3: s3,
      effK,
    });
    setViewStep(3); // show result

    setReadings(s3);
    setTicksCount((c) => c + kNum);
    setRotY((r) => r - (360 / n) * effK);
  }, [kInput, readings, n]);

  // Reset to initial readings
  const handleReset = useCallback(() => {
    setReadings(items && items.length > 0 ? items : DEFAULT_READINGS);
    setTicksCount(0);
    setRotY(0);
    setViewStep(null);
    setStepData(null);
  }, [items]);

  // Auto-tick interval
  useEffect(() => {
    if (!autoTick) return;
    const interval = setInterval(() => {
      handleTick(1);
    }, 2800);
    return () => clearInterval(interval);
  }, [autoTick, handleTick]);

  // Mouse drag 3D rotation handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    dragStartX.current = e.clientX;
    dragStartRot.current = rotY;
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    const delta = e.clientX - dragStartX.current;
    setRotY(dragStartRot.current + delta * 0.4);
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  return (
    <div className="circular-readings-wrap">
      {/* ── Section Header ── */}
      <div className="circular-readings-head">
        <div className="circular-readings-badge-tag">
          <span className="dot-live" />
          <span>AICTE APH 2024–27 · 3D CIRCULAR READINGS BUFFER</span>
        </div>
        <div className="circular-readings-title-row">
          <div>
            <h3 style={{ color: "#f8fafc" }}>Regulatory Telemetry Display</h3>
            <p style={{ color: "#cbd5e1", margin: "0.25rem 0 0" }}>
              Dynamic 3D telemetry buffer of {n} live institutional applications.
              Array rotated using the <strong style={{ color: "var(--action)" }}>Three-Reversals Algorithm</strong>.
            </p>
          </div>
          <div className="circular-readings-tick-pill">
            <span className="tick-label">TICKS PROCESSED:</span>
            <span className="tick-num">{ticksCount}</span>
          </div>
        </div>
      </div>

      {/* ── 3D Viewport ── */}
      <div
        className="cylinder-viewport"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        style={{ cursor: isDragging ? "grabbing" : "grab" }}
      >
        <div className="cylinder-instruction">
          <span>⇄ Drag horizontally to spin 3D cylinder</span>
        </div>

        <div
          className="cylinder-ring"
          style={{
            transform: `rotateX(-10deg) rotateY(${rotY}deg)`,
            transition: isDragging ? "none" : "transform 0.6s cubic-bezier(0.16, 1, 0.3, 1)",
          }}
        >
          {readings.map((r, i) => {
            const angle = (360 / n) * i;
            const isFront = (Math.abs((rotY + angle) % 360) < 35) || (Math.abs(((rotY + angle) % 360) - 360) < 35);
            return (
              <div
                key={`${r.id}-${i}`}
                className={`cylinder-card ${isFront ? "is-front" : ""}`}
                style={{
                  transform: `rotateY(${angle}deg) translateZ(${radius}px)`,
                }}
              >
                <div className="card-glass-glow" />
                <div className="card-top-row">
                  <span className="card-slot-idx">SLOT [{i}]</span>
                  <span className={`card-status-badge status-${r.status}`}>
                    {r.status.toUpperCase()}
                  </span>
                </div>
                <div className="card-code">{r.code}</div>
                <div className="card-value">{r.val}</div>
                <div className="card-label">{r.label}</div>
                <div className="card-meta">
                  <span>{r.metric}</span>
                  <span className="card-src">{r.source}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* 3D Floor Reflection */}
        <div className="cylinder-floor" />
      </div>

      {/* ── Interactive Controls Toolbar ── */}
      <div className="circular-controls-bar">
        <div className="controls-left">
          <button
            type="button"
            className="btn-press btn-tick"
            onClick={() => handleTick(1)}
            title="Advance by 1 tick (moves last element to front)"
          >
            <span>+1 Tick Clock</span>
          </button>

          <button
            type="button"
            className={`btn-press ${autoTick ? "btn-tick-active" : ""}`}
            onClick={() => setAutoTick(!autoTick)}
          >
            <span>{autoTick ? "⏸ Pause Auto-Tick" : "▶ Auto-Tick (2.8s)"}</span>
          </button>

          <button
            type="button"
            className="btn btn-ghost btn-small"
            onClick={handleReset}
          >
            Reset Buffer
          </button>
        </div>

        {/* K-Rotation Input Form */}
        <div className="controls-right">
          <label className="k-input-group">
            <span className="k-input-label">Rotate by K:</span>
            <input
              type="number"
              min="0"
              value={kInput}
              onChange={(e) => setKInput(e.target.value)}
              className="k-input-box"
              placeholder="K ticks"
            />
          </label>
          <button
            type="button"
            className="btn-press btn-k-action"
            onClick={handleRotateByK}
          >
            <span>Run 3-Reversals</span>
          </button>
        </div>
      </div>

      {/* ── Three-Reversals Visual Stepper ── */}
      {stepData && (
        <div className="reversal-stepper-panel">
          <div className="stepper-title">
            <span>Algorithm Trace: 3-Reversals (K = {kInput}, K mod {n} = {stepData.effK})</span>
            <button
              type="button"
              className="btn btn-ghost btn-small"
              onClick={() => setStepData(null)}
            >
              Close Trace ✕
            </button>
          </div>
          <div className="stepper-tabs">
            <button
              className={`stepper-tab ${viewStep === 0 ? "active" : ""}`}
              onClick={() => {
                setViewStep(0);
                setReadings(stepData.original);
              }}
            >
              0. Original Array
            </button>
            <button
              className={`stepper-tab ${viewStep === 1 ? "active" : ""}`}
              onClick={() => {
                setViewStep(1);
                setReadings(stepData.step1);
              }}
            >
              1. Reverse All [0..{n - 1}]
            </button>
            <button
              className={`stepper-tab ${viewStep === 2 ? "active" : ""}`}
              onClick={() => {
                setViewStep(2);
                setReadings(stepData.step2);
              }}
            >
              2. Reverse First {stepData.effK} [0..{stepData.effK - 1}]
            </button>
            <button
              className={`stepper-tab ${viewStep === 3 ? "active" : ""}`}
              onClick={() => {
                setViewStep(3);
                setReadings(stepData.step3);
              }}
            >
              3. Reverse Last {n - stepData.effK} [Result]
            </button>
          </div>
          <div className="stepper-array-preview">
            {readings.map((r, idx) => (
              <span key={idx} className="preview-chip">
                <span className="chip-idx">{idx}:</span>
                <span className="chip-code">{r.code}</span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
