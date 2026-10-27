import { useEffect, useRef } from "react";

/**
 * A fixed, always-on cinematic backdrop:
 * - Aurora blobs (breathing gradient mesh)
 * - Drifting grid
 * - Radar sweep + concentric rings
 * - Continuous ECG waveform
 * - Floating particle field
 * - Cursor-reactive spotlight
 * All GPU-friendly (transform / opacity only). Purely decorative — pointer-events: none.
 */
export function Ambient() {
  const spotRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = spotRef.current;
    if (!el) return;
    let raf = 0;
    let tx = 0, ty = 0, cx = 0, cy = 0;
    const on = (e: PointerEvent) => { tx = e.clientX; ty = e.clientY; };
    const tick = () => {
      cx += (tx - cx) * 0.08;
      cy += (ty - cy) * 0.08;
      el.style.transform = `translate3d(${cx - 300}px, ${cy - 300}px, 0)`;
      raf = requestAnimationFrame(tick);
    };
    window.addEventListener("pointermove", on, { passive: true });
    raf = requestAnimationFrame(tick);
    return () => { window.removeEventListener("pointermove", on); cancelAnimationFrame(raf); };
  }, []);

  // Deterministic particle positions (SSR-safe)
  const particles = Array.from({ length: 40 }).map((_, i) => ({
    left: `${(i * 53 + 7) % 100}%`,
    delay: `${(i * 0.37) % 12}s`,
    dur: `${16 + ((i * 7) % 18)}s`,
    size: 1 + (i % 3) * 0.5,
    hue: i % 5 === 0 ? "var(--emerald-soft)" : i % 3 === 0 ? "var(--cyan-soft)" : "var(--electric)",
  }));

  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      {/* Base gradient wash */}
      <div className="absolute inset-0" style={{
        background:
          "radial-gradient(ellipse at 50% -10%, oklch(0.28 0.09 250 / 0.55), transparent 55%)," +
          "radial-gradient(ellipse at 50% 110%, oklch(0.18 0.06 250 / 0.45), transparent 55%)," +
          "linear-gradient(180deg, oklch(0.10 0.012 260), oklch(0.08 0.012 260))",
      }} />

      {/* Aurora blobs */}
      <div className="absolute -inset-40 opacity-70 mix-blend-screen" style={{ animation: "hue-shift 24s ease-in-out infinite" }}>
        <div
          className="absolute left-1/4 top-1/4 h-[70vmax] w-[70vmax] rounded-full blur-3xl"
          style={{
            background: "radial-gradient(circle, oklch(0.72 0.19 245 / 0.35), transparent 60%)",
            animation: "aurora-a 22s ease-in-out infinite",
          }}
        />
        <div
          className="absolute right-1/4 top-1/3 h-[60vmax] w-[60vmax] rounded-full blur-3xl"
          style={{
            background: "radial-gradient(circle, oklch(0.85 0.11 210 / 0.28), transparent 60%)",
            animation: "aurora-b 28s ease-in-out infinite",
          }}
        />
        <div
          className="absolute left-1/2 top-2/3 h-[50vmax] w-[50vmax] rounded-full blur-3xl"
          style={{
            background: "radial-gradient(circle, oklch(0.78 0.13 165 / 0.14), transparent 60%)",
            animation: "aurora-c 34s ease-in-out infinite",
          }}
        />
      </div>

      {/* Drifting grid */}
      <div className="absolute inset-0 ambient-grid opacity-[0.35]" />

      {/* Concentric radar rings + sweep, top-right */}
      <div className="absolute -right-40 -top-40 h-[70vmin] w-[70vmin]">
        {[0.35, 0.55, 0.78, 1].map((s, i) => (
          <div
            key={i}
            className="absolute inset-0 rounded-full border border-electric/15"
            style={{ transform: `scale(${s})`, animation: `breathe ${8 + i}s ease-in-out ${i * 0.6}s infinite` }}
          />
        ))}
        <div
          className="absolute inset-0 rounded-full"
          style={{
            background: "conic-gradient(from 0deg, transparent 0deg, oklch(0.72 0.19 245 / 0.25) 24deg, transparent 60deg)",
            mask: "radial-gradient(circle, transparent 40%, black 41%)",
            WebkitMask: "radial-gradient(circle, transparent 40%, black 41%)",
            animation: "radar-sweep 12s linear infinite",
          }}
        />
      </div>

      {/* Big slow heartbeat pulse ring, bottom-left */}
      <div className="absolute -bottom-40 -left-40 h-[80vmin] w-[80vmin]">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="absolute inset-0 rounded-full border border-cyan-soft/20"
            style={{ animation: `pulse-ring-xl ${9}s ease-out ${i * 3}s infinite` }}
          />
        ))}
      </div>

      {/* Continuous ECG at bottom */}
      <svg
        viewBox="0 0 1600 120"
        preserveAspectRatio="none"
        className="absolute inset-x-0 bottom-0 h-24 w-full opacity-40"
      >
        <defs>
          <linearGradient id="ecgGrad" x1="0" x2="1">
            <stop offset="0%" stopColor="transparent" />
            <stop offset="50%" stopColor="var(--electric)" />
            <stop offset="100%" stopColor="transparent" />
          </linearGradient>
        </defs>
        <path
          d="M0,60 L200,60 L220,60 L235,20 L250,100 L265,40 L280,60 L520,60 L540,60 L555,20 L570,100 L585,40 L600,60 L900,60 L920,60 L935,20 L950,100 L965,40 L980,60 L1300,60 L1320,60 L1335,20 L1350,100 L1365,40 L1380,60 L1600,60"
          fill="none"
          stroke="url(#ecgGrad)"
          strokeWidth="1.3"
          strokeDasharray="3200"
          style={{ animation: "ecg 8s linear infinite" }}
        />
      </svg>

      {/* Diagonal scan-line beam */}
      <div
        className="absolute inset-x-0 h-40 opacity-30"
        style={{
          background: "linear-gradient(180deg, transparent, oklch(0.85 0.11 210 / 0.25), transparent)",
          animation: "scan 14s linear infinite",
        }}
      />

      {/* Floating particles */}
      <div className="absolute inset-0">
        {particles.map((p, i) => (
          <span
            key={i}
            className="absolute rounded-full"
            style={{
              left: p.left,
              bottom: "-10vh",
              width: p.size,
              height: p.size,
              background: p.hue,
              boxShadow: `0 0 8px ${p.hue}`,
              animation: `float-up ${p.dur} linear ${p.delay} infinite`,
              opacity: 0.7,
            }}
          />
        ))}
      </div>

      {/* Cursor spotlight */}
      <div
        ref={spotRef}
        className="absolute h-[600px] w-[600px] rounded-full opacity-40 mix-blend-screen blur-3xl transition-opacity"
        style={{
          background: "radial-gradient(circle, oklch(0.72 0.19 245 / 0.35), transparent 60%)",
          willChange: "transform",
        }}
      />

      {/* Vignette */}
      <div
        className="absolute inset-0"
        style={{ background: "radial-gradient(ellipse at center, transparent 40%, oklch(0.05 0.005 260 / 0.7) 100%)" }}
      />
    </div>
  );
}
