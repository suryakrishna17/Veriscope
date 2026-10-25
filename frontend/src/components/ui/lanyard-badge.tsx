import * as React from "react"

/* -------------------------------------------------------------------------- */
/*  Types                                                                      */
/* -------------------------------------------------------------------------- */

interface Point {
  x: number
  y: number
  px: number
  py: number
  pinned?: boolean
}

interface LanyardBadgeProps {
  name?: string
  role?: string
  org?: string
  badgeId?: string
  accentColor?: string
  width?: number
  autoSwing?: boolean
}

/* -------------------------------------------------------------------------- */
/*  Verlet rope helpers                                                        */
/* -------------------------------------------------------------------------- */

const GRAVITY = 0.4
const DAMPING = 0.985
const CONSTRAINT_ITERS = 14
const SEG = 24

function makeRope(x: number, anchorY: number, bottomY: number): Point[] {
  return Array.from({ length: SEG + 1 }, (_, i) => {
    const t = i / SEG
    return {
      x,
      y: anchorY + t * (bottomY - anchorY),
      px: x,
      py: anchorY + t * (bottomY - anchorY),
    }
  }).map((p, i) => (i === 0 ? { ...p, pinned: true } : p))
}

function stepRope(
  pts: Point[],
  pinX: number,
  pinY: number,
  restLen: number,
  bottomX?: number,
  bottomY?: number
) {
  pts.forEach((p, idx) => {
    if (idx === 0) {
      p.x = pinX
      p.y = pinY
      return
    }
    const vx = (p.x - p.px) * DAMPING
    const vy = (p.y - p.py) * DAMPING
    p.px = p.x
    p.py = p.y
    p.x += vx
    p.y += vy + GRAVITY
  })

  for (let iter = 0; iter < CONSTRAINT_ITERS; iter++) {
    for (let i = 0; i < pts.length - 1; i++) {
      const a = pts[i]
      const b = pts[i + 1]
      const dx = b.x - a.x
      const dy = b.y - a.y
      const dist = Math.sqrt(dx * dx + dy * dy) || 0.001
      const diff = (dist - restLen) / dist / 2
      if (i > 0) {
        a.x += dx * diff
        a.y += dy * diff
      }
      if (i + 1 < pts.length - 1) {
        b.x -= dx * diff
        b.y -= dy * diff
      }
    }
    if (bottomX !== undefined && bottomY !== undefined) {
      const last = pts[pts.length - 1]
      last.x += (bottomX - last.x) * 0.35
      last.y += (bottomY - last.y) * 0.35
    }
  }
}

/* -------------------------------------------------------------------------- */
/*  Component                                                                  */
/* -------------------------------------------------------------------------- */

export function LanyardBadge({
  name = "Adarsh K. Rao",
  role = "Senior Reviewer",
  org = "VeriScope · AICTE Trust Architecture",
  badgeId = "VS-2026-0042",
  accentColor = "#FF5E1E",
  width = 280,
  autoSwing = true,
}: LanyardBadgeProps) {
  const containerRef = React.useRef<HTMLDivElement>(null)
  const canvasRef = React.useRef<HTMLCanvasElement>(null)
  const cardRef = React.useRef<HTMLDivElement>(null)
  const frontGlareRef = React.useRef<HTMLDivElement>(null)
  const backGlareRef = React.useRef<HTMLDivElement>(null)

  const rafRef = React.useRef<number>(0)
  const ropeRef = React.useRef<Point[]>([])
  const swingRef = React.useRef({ angle: autoSwing ? 0.2 : 0, vel: autoSwing ? -0.005 : 0 })
  const hoverRef = React.useRef(false)
  const isDraggingRef = React.useRef(false)
  const dragStartRef = React.useRef({ x: 0, y: 0 })
  const dragCurrentRef = React.useRef({ x: 0, y: 0 })
  const mouseRef = React.useRef({ x: 0, y: 0 })

  const targetRef = React.useRef({ x: 0, y: 0, tx: 0, ty: 0, tz: 0 })
  const currentRef = React.useRef({ x: 0, y: 0, tx: 0, ty: 0, tz: 0 })
  const flippedRef = React.useRef(false)
  const flipAngleRef = React.useRef(0)
  const glareOpacityRef = React.useRef(0)

  const [cursorGrab, setCursorGrab] = React.useState(false)

  const CARD_H = Math.round(width * 1.42)
  const CANVAS_W = Math.round(width * 1.4)
  const CANVAS_H = Math.round(CARD_H * 0.52)
  const PIN_X = CANVAS_W / 2
  const PIN_Y = 0
  const REST_LEN = (CANVAS_H * 0.95) / SEG

  React.useEffect(() => {
    ropeRef.current = makeRope(PIN_X, PIN_Y, CANVAS_H * 0.92)
  }, [PIN_X, CANVAS_H])

  React.useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext("2d")
    if (!ctx) return

    const draw = () => {
      const swing = swingRef.current

      // Calculate target transforms based on state
      if (isDraggingRef.current) {
        // Drag mode
        const dx = dragCurrentRef.current.x
        const dy = dragCurrentRef.current.y
        targetRef.current.tx = Math.max(-90, Math.min(90, dx))
        targetRef.current.ty = Math.max(-40, Math.min(70, dy))
        targetRef.current.y = (targetRef.current.tx / 90) * 32
        targetRef.current.x = (-targetRef.current.ty / 70) * 22
        targetRef.current.tz = 35
      } else if (hoverRef.current) {
        // Interactive 3D hover: cursor causes the card to dip and shift toward that side
        const mx = mouseRef.current.x // -1 (left) to +1 (right)
        const my = mouseRef.current.y // -1 (top) to +1 (bottom)

        // Dip away into the screen on the hovered side:
        // Right side hover (mx > 0) -> rotates right edge away (positive rotateY)
        // Bottom side hover (my > 0) -> rotates bottom edge away (negative rotateX)
        targetRef.current.y = mx * 28
        targetRef.current.x = -my * 22
        targetRef.current.tx = mx * 20
        targetRef.current.ty = my * 15
        targetRef.current.tz = 28
      } else {
        // Idle swing
        swing.angle += swing.vel
        if (Math.abs(swing.angle) > 0.16) swing.vel *= -0.96
        swing.vel += -swing.angle * 0.0035

        targetRef.current.y = Math.sin(swing.angle) * 14
        targetRef.current.x = 0
        targetRef.current.tx = Math.sin(swing.angle) * 12
        targetRef.current.ty = 0
        targetRef.current.tz = 0
      }

      // Smooth interpolation (lerp)
      const lerpSpeed = isDraggingRef.current ? 0.35 : 0.14
      currentRef.current.y += (targetRef.current.y - currentRef.current.y) * lerpSpeed
      currentRef.current.x += (targetRef.current.x - currentRef.current.x) * lerpSpeed
      currentRef.current.tx += (targetRef.current.tx - currentRef.current.tx) * lerpSpeed
      currentRef.current.ty += (targetRef.current.ty - currentRef.current.ty) * lerpSpeed
      currentRef.current.tz += (targetRef.current.tz - currentRef.current.tz) * lerpSpeed

      // Flip transition
      const targetFlip = flippedRef.current ? 180 : 0
      flipAngleRef.current += (targetFlip - flipAngleRef.current) * 0.12

      // Step rope physics with bottom anchored to the card
      const bottomAttachX = PIN_X + currentRef.current.tx * 0.8
      const bottomAttachY = CANVAS_H * 0.92 + currentRef.current.ty * 0.4
      stepRope(ropeRef.current, PIN_X, PIN_Y, REST_LEN, bottomAttachX, bottomAttachY)

      // Draw canvas lanyard
      ctx.clearRect(0, 0, CANVAS_W, CANVAS_H)
      const pts = ropeRef.current
      if (pts.length > 1) {
        // Main strap
        ctx.beginPath()
        ctx.moveTo(pts[0].x, pts[0].y)
        for (let i = 1; i < pts.length; i++) {
          const prev = pts[i - 1]
          const curr = pts[i]
          ctx.quadraticCurveTo(prev.x, prev.y, (prev.x + curr.x) / 2, (prev.y + curr.y) / 2)
        }
        ctx.strokeStyle = accentColor
        ctx.lineWidth = 4
        ctx.lineCap = "round"
        ctx.stroke()

        // White inner lanyard stitch/highlight
        ctx.beginPath()
        ctx.moveTo(pts[0].x, pts[0].y)
        for (let i = 1; i < pts.length; i++) {
          const prev = pts[i - 1]
          const curr = pts[i]
          ctx.quadraticCurveTo(prev.x, prev.y, (prev.x + curr.x) / 2, (prev.y + curr.y) / 2)
        }
        ctx.strokeStyle = "rgba(255, 255, 255, 0.45)"
        ctx.lineWidth = 1.4
        ctx.stroke()

        // Metal split ring
        const last = pts[pts.length - 1]
        ctx.beginPath()
        ctx.arc(last.x, last.y, 8, 0, Math.PI * 2)
        ctx.strokeStyle = "#D1D5DB"
        ctx.lineWidth = 2.8
        ctx.stroke()

        // Lobster clasp
        ctx.fillStyle = "#9CA3AF"
        ctx.fillRect(last.x - 3, last.y + 4, 6, 10)
        ctx.beginPath()
        ctx.arc(last.x, last.y + 14, 4, 0, Math.PI)
        ctx.strokeStyle = "#9CA3AF"
        ctx.lineWidth = 2.4
        ctx.stroke()
      }

      // Update card 3D transform & shadow
      if (cardRef.current) {
        const { tx, ty, tz, x, y } = currentRef.current
        const flipY = flipAngleRef.current
        // When card is flipped, invert local Y-axis hover rotation so the visible side dips naturally
        const effectiveY = flipY > 90 ? flipY - y : flipY + y

        cardRef.current.style.transform = `
          translate3d(${tx}px, ${ty}px, ${tz}px)
          rotateY(${effectiveY}deg)
          rotateX(${x}deg)
        `

        // Dynamic 3D shadow: shifts in opposite direction of tilt
        const shadowX = -y * 1.3
        const shadowY = x * 1.1 + 25 + (tz > 5 ? 12 : 0)
        const shadowBlur = tz > 5 ? 48 : 32
        const shadowOpacity = tz > 5 ? 0.38 : 0.22
        cardRef.current.style.boxShadow = `
          ${shadowX}px ${shadowY}px ${shadowBlur}px -10px rgba(14, 16, 19, ${shadowOpacity}),
          0 4px 14px rgba(14, 16, 19, 0.12)
        `
      }

      // Specular sheen highlight update
      if (frontGlareRef.current && backGlareRef.current) {
        const targetOpacity = hoverRef.current ? 0.8 : 0
        glareOpacityRef.current += (targetOpacity - glareOpacityRef.current) * 0.15

        const gx = ((mouseRef.current.x + 1) / 2) * 100
        const gy = ((mouseRef.current.y + 1) / 2) * 100

        frontGlareRef.current.style.opacity = `${glareOpacityRef.current}`
        frontGlareRef.current.style.background = `radial-gradient(circle at ${gx}% ${gy}%, rgba(255,255,255,0.7) 0%, rgba(255,255,255,0) 65%)`

        backGlareRef.current.style.opacity = `${glareOpacityRef.current * 0.55}`
        backGlareRef.current.style.background = `radial-gradient(circle at ${gx}% ${gy}%, rgba(255,255,255,0.35) 0%, rgba(255,255,255,0) 65%)`
      }

      rafRef.current = requestAnimationFrame(draw)
    }

    rafRef.current = requestAnimationFrame(draw)
    return () => cancelAnimationFrame(rafRef.current)
  }, [PIN_X, CANVAS_W, CANVAS_H, REST_LEN, accentColor])

  // Mouse & drag event handlers
  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (isDraggingRef.current) {
      dragCurrentRef.current = {
        x: e.clientX - dragStartRef.current.x,
        y: e.clientY - dragStartRef.current.y,
      }
      return
    }

    if (!cardRef.current) return
    const rect = cardRef.current.getBoundingClientRect()
    const cardCenterX = rect.left + rect.width / 2
    const cardCenterY = rect.top + rect.height / 2

    // Normalized from -1 to +1 relative to the card's center
    const rawX = (e.clientX - cardCenterX) / (rect.width / 2)
    const rawY = (e.clientY - cardCenterY) / (rect.height / 2)

    mouseRef.current = {
      x: Math.max(-1.4, Math.min(1.4, rawX)),
      y: Math.max(-1.4, Math.min(1.4, rawY)),
    }
    hoverRef.current = true
  }

  const handleMouseEnter = () => {
    hoverRef.current = true
    swingRef.current.vel = 0
  }

  const handleMouseLeave = () => {
    hoverRef.current = false
    isDraggingRef.current = false
    setCursorGrab(false)
    mouseRef.current = { x: 0, y: 0 }
  }

  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    isDraggingRef.current = true
    setCursorGrab(true)
    dragStartRef.current = { x: e.clientX, y: e.clientY }
    dragCurrentRef.current = { x: 0, y: 0 }
  }

  const handleMouseUp = () => {
    if (isDraggingRef.current) {
      const dist = Math.hypot(dragCurrentRef.current.x, dragCurrentRef.current.y)
      if (dist < 8) {
        // Clean tap / click flips the card
        flippedRef.current = !flippedRef.current
      } else {
        // Drag release imparts momentum to the rope swing
        swingRef.current.vel = (dragCurrentRef.current.x / 100) * 0.05
      }
    }
    isDraggingRef.current = false
    setCursorGrab(false)
    dragCurrentRef.current = { x: 0, y: 0 }
  }

  // Window-level mouseup to handle releasing outside the card
  React.useEffect(() => {
    const onWindowMouseUp = () => {
      if (isDraggingRef.current) {
        handleMouseUp()
      }
    }
    window.addEventListener("mouseup", onWindowMouseUp)
    return () => window.removeEventListener("mouseup", onWindowMouseUp)
  }, [])

  const initials = name
    .split(" ")
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase()

  return (
    <div
      ref={containerRef}
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        userSelect: "none",
        cursor: cursorGrab ? "grabbing" : "grab",
        width: CANVAS_W,
        position: "relative",
      }}
      onMouseMove={handleMouseMove}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
    >
      {/* Verlet physics rope canvas */}
      <canvas
        ref={canvasRef}
        width={CANVAS_W}
        height={CANVAS_H}
        style={{
          display: "block",
          width: CANVAS_W,
          height: CANVAS_H,
          pointerEvents: "none",
        }}
      />

      {/* 3D Perspective card stage */}
      <div
        style={{
          perspective: "800px",
          perspectiveOrigin: "50% 50%",
          width,
          height: CARD_H,
          marginTop: -6,
        }}
      >
        <div
          ref={cardRef}
          style={{
            width: "100%",
            height: "100%",
            transformStyle: "preserve-3d",
            transition: "none",
            willChange: "transform, box-shadow",
            position: "relative",
            borderRadius: 16,
          }}
        >
          {/* FRONT FACE */}
          <div
            style={{
              position: "absolute",
              inset: 0,
              backfaceVisibility: "hidden",
              WebkitBackfaceVisibility: "hidden",
              borderRadius: 16,
              overflow: "hidden",
              background: "#FAFAF8",
              border: "1px solid rgba(255,255,255,0.9)",
            }}
          >
            {/* Dynamic specular glare overlay */}
            <div
              ref={frontGlareRef}
              style={{
                position: "absolute",
                inset: 0,
                pointerEvents: "none",
                borderRadius: 16,
                zIndex: 15,
                mixBlendMode: "overlay",
                opacity: 0,
              }}
            />

            {/* Top accent bar */}
            <div style={{ height: 6, background: `linear-gradient(90deg, ${accentColor} 0%, #FF8C5A 100%)` }} />

            {/* Top grommet / lanyard punch hole */}
            <div
              style={{
                position: "absolute",
                top: 12,
                left: "50%",
                transform: "translateX(-50%)",
                width: 18,
                height: 18,
                borderRadius: "50%",
                background: "#E0DDD7",
                border: "3px solid #C8C5BE",
                boxShadow: "inset 0 1px 3px rgba(0,0,0,0.25)",
              }}
            />

            {/* Header banner */}
            <div
              style={{
                marginTop: 12,
                padding: "14px 20px 12px",
                background: `linear-gradient(135deg, ${accentColor}18 0%, transparent 100%)`,
                borderBottom: "1px solid rgba(255,94,30,0.12)",
                textAlign: "center",
              }}
            >
              <div
                style={{
                  fontSize: 9,
                  fontWeight: 700,
                  letterSpacing: "0.18em",
                  color: accentColor,
                  textTransform: "uppercase",
                  fontFamily: "Space Grotesk, system-ui, sans-serif",
                }}
              >
                AICTE TRUST ARCHITECTURE · SIH 2026
              </div>
              <div
                style={{
                  fontSize: 11,
                  fontWeight: 600,
                  color: "#5A5650",
                  marginTop: 2,
                  fontFamily: "Space Grotesk, system-ui, sans-serif",
                }}
              >
                Official Verification Access
              </div>
            </div>

            {/* Avatar & Identifiers */}
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", padding: "18px 20px 0" }}>
              <div
                style={{
                  width: 64,
                  height: 64,
                  borderRadius: "50%",
                  background: `linear-gradient(135deg, ${accentColor} 0%, #FF8C5A 100%)`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 22,
                  fontWeight: 800,
                  color: "#fff",
                  fontFamily: "Space Grotesk, system-ui, sans-serif",
                  boxShadow: `0 4px 16px ${accentColor}44`,
                  border: "3px solid #fff",
                  letterSpacing: "-0.02em",
                }}
              >
                {initials}
              </div>
              <div style={{ marginTop: 12, textAlign: "center" }}>
                <div
                  style={{
                    fontSize: 15,
                    fontWeight: 700,
                    color: "#0E1013",
                    fontFamily: "Space Grotesk, system-ui, sans-serif",
                    letterSpacing: "-0.02em",
                  }}
                >
                  {name}
                </div>
                <div
                  style={{
                    fontSize: 11,
                    fontWeight: 600,
                    color: accentColor,
                    marginTop: 3,
                    letterSpacing: "0.04em",
                    textTransform: "uppercase",
                    fontFamily: "Space Grotesk, system-ui, sans-serif",
                  }}
                >
                  {role}
                </div>
                <div
                  style={{
                    fontSize: 10,
                    color: "#7A7670",
                    marginTop: 4,
                    fontFamily: "Hanken Grotesk, system-ui, sans-serif",
                    maxWidth: 200,
                  }}
                >
                  {org}
                </div>
              </div>
            </div>

            {/* QR verification block */}
            <div
              style={{
                margin: "16px 20px 0",
                padding: "10px 12px",
                background: "rgba(255,94,30,0.05)",
                borderRadius: 8,
                border: "1px solid rgba(255,94,30,0.14)",
                display: "flex",
                alignItems: "center",
                gap: 10,
              }}
            >
              <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
                <rect x="1" y="1" width="14" height="14" rx="2" stroke="#0E1013" strokeWidth="1.5" />
                <rect x="5" y="5" width="6" height="6" fill="#0E1013" rx="1" />
                <rect x="21" y="1" width="14" height="14" rx="2" stroke="#0E1013" strokeWidth="1.5" />
                <rect x="25" y="5" width="6" height="6" fill="#0E1013" rx="1" />
                <rect x="1" y="21" width="14" height="14" rx="2" stroke="#0E1013" strokeWidth="1.5" />
                <rect x="5" y="25" width="6" height="6" fill="#0E1013" rx="1" />
                <rect x="21" y="21" width="3" height="3" fill="#0E1013" />
                <rect x="26" y="21" width="3" height="3" fill="#0E1013" />
                <rect x="31" y="21" width="3" height="3" fill="#0E1013" />
                <rect x="21" y="26" width="3" height="3" fill="#0E1013" />
                <rect x="26" y="26" width="3" height="3" fill="#0E1013" />
                <rect x="31" y="31" width="3" height="3" fill="#0E1013" />
                <rect x="21" y="31" width="3" height="3" fill="#0E1013" />
              </svg>
              <div>
                <div
                  style={{
                    fontSize: 9,
                    color: "#9A9590",
                    letterSpacing: "0.12em",
                    textTransform: "uppercase",
                    fontFamily: "Space Grotesk, system-ui, sans-serif",
                  }}
                >
                  Badge ID
                </div>
                <div
                  style={{
                    fontSize: 12,
                    fontWeight: 700,
                    color: "#0E1013",
                    fontFamily: "JetBrains Mono, monospace",
                    letterSpacing: "0.06em",
                  }}
                >
                  {badgeId}
                </div>
              </div>
            </div>

            {/* Bottom active pill */}
            <div
              style={{
                position: "absolute",
                bottom: 0,
                left: 0,
                right: 0,
                padding: "8px 20px 10px",
                background: "linear-gradient(180deg, transparent, rgba(255,94,30,0.06))",
                borderTop: "1px solid rgba(255,94,30,0.1)",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <div
                style={{
                  fontSize: 9,
                  color: "#9A9590",
                  fontFamily: "Space Grotesk, system-ui, sans-serif",
                  letterSpacing: "0.08em",
                }}
              >
                VeriScope Platform
              </div>
              <div
                style={{
                  fontSize: 9,
                  fontWeight: 600,
                  color: accentColor,
                  background: `${accentColor}15`,
                  padding: "2px 8px",
                  borderRadius: 4,
                  fontFamily: "Space Grotesk, system-ui, sans-serif",
                }}
              >
                ACTIVE
              </div>
            </div>
          </div>

          {/* BACK FACE */}
          <div
            style={{
              position: "absolute",
              inset: 0,
              backfaceVisibility: "hidden",
              WebkitBackfaceVisibility: "hidden",
              transform: "rotateY(180deg)",
              borderRadius: 16,
              overflow: "hidden",
              background: "#0E1013",
              border: "1px solid rgba(255,255,255,0.1)",
            }}
          >
            {/* Dynamic specular glare overlay */}
            <div
              ref={backGlareRef}
              style={{
                position: "absolute",
                inset: 0,
                pointerEvents: "none",
                borderRadius: 16,
                zIndex: 15,
                mixBlendMode: "screen",
                opacity: 0,
              }}
            />

            <div style={{ height: 6, background: "linear-gradient(90deg, #FF5E1E, #FF8C5A)" }} />
            <div style={{ height: 42, background: "linear-gradient(180deg, #1a1a1a 0%, #111 100%)", marginTop: 30 }} />
            <div style={{ padding: "16px 20px" }}>
              <div
                style={{
                  fontSize: 9,
                  color: "#FF5E1E",
                  letterSpacing: "0.14em",
                  textTransform: "uppercase",
                  fontFamily: "Space Grotesk, system-ui, sans-serif",
                  marginBottom: 8,
                }}
              >
                Access Scope
              </div>
              {["Document Upload & Verification", "Evidence Bounding Box Review", "Audit Trail Read-Only Access"].map(
                (t) => (
                  <div key={t} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                    <div style={{ width: 4, height: 4, borderRadius: "50%", background: "#FF5E1E" }} />
                    <div style={{ fontSize: 10, color: "#A0A8B0", fontFamily: "Hanken Grotesk, system-ui, sans-serif" }}>
                      {t}
                    </div>
                  </div>
                )
              )}
              <div
                style={{
                  marginTop: 16,
                  padding: "8px 10px",
                  background: "rgba(255,94,30,0.08)",
                  borderRadius: 6,
                  border: "1px solid rgba(255,94,30,0.2)",
                  fontSize: 9,
                  color: "#6A6E74",
                  fontFamily: "Space Grotesk, system-ui, sans-serif",
                  lineHeight: 1.5,
                }}
              >
                This badge is property of the AICTE Trust Architecture system. Unauthorized use is prohibited.
              </div>
            </div>
            <div
              style={{
                position: "absolute",
                bottom: 12,
                left: 20,
                right: 20,
                fontSize: 9,
                color: "#4A4E54",
                fontFamily: "Space Grotesk, system-ui, sans-serif",
                textAlign: "center",
              }}
            >
              Click to flip · VeriScope Platform · SIH 2026
            </div>
          </div>
        </div>
      </div>

      {/* Interactive Helper Pill */}
      <div
        style={{
          marginTop: 16,
          display: "inline-flex",
          alignItems: "center",
          gap: 6,
          padding: "5px 12px",
          borderRadius: 20,
          background: "rgba(255, 255, 255, 0.04)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          fontSize: 10,
          color: "#9A9590",
          fontFamily: "Space Grotesk, system-ui, sans-serif",
          letterSpacing: "0.03em",
          pointerEvents: "none",
        }}
      >
        <span
          style={{
            width: 6,
            height: 6,
            borderRadius: "50%",
            background: accentColor,
            boxShadow: `0 0 8px ${accentColor}`,
          }}
        />
        <span>Hover to tilt & dip · Drag to pull · Click to flip</span>
      </div>
    </div>
  )
}
