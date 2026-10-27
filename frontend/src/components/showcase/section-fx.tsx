/**
 * SectionFX — a self-contained, always-on ambient motion layer for a section.
 *
 * Drop <SectionFX variant="..." /> as the first child of a `relative isolate
 * overflow-hidden` section. It paints behind the section content (its own
 * negative z within the section's isolated stacking context) and animates
 * continuously — independent of scroll — so no section ever feels static.
 *
 * Purely decorative (pointer-events: none) and GPU-friendly
 * (transform / opacity only).
 */

type Variant = "mesh" | "grid" | "rings" | "dna" | "neural" | "flow";

const HUES = {
  electric: "var(--electric)",
  cyan: "var(--cyan-soft)",
  emerald: "var(--emerald-soft)",
} as const;

function Particles({ count = 18, tint = "electric" }: { count?: number; tint?: keyof typeof HUES }) {
  const dots = Array.from({ length: count }).map((_, i) => ({
    left: `${(i * 61 + 11) % 100}%`,
    delay: `${(i * 0.53) % 10}s`,
    dur: `${14 + ((i * 5) % 16)}s`,
    size: 1 + (i % 3) * 0.6,
  }));
  return (
    <div className="absolute inset-0">
      {dots.map((p, i) => (
        <span
          key={i}
          className="absolute rounded-full"
          style={{
            left: p.left,
            bottom: "-6%",
            width: p.size,
            height: p.size,
            background: HUES[tint],
            boxShadow: `0 0 8px ${HUES[tint]}`,
            opacity: 0.6,
            animation: `float-up ${p.dur} linear ${p.delay} infinite`,
          }}
        />
      ))}
    </div>
  );
}

function MeshBlobs({ a = "electric", b = "cyan" }: { a?: keyof typeof HUES; b?: keyof typeof HUES }) {
  return (
    <>
      <div
        className="absolute -left-[10%] top-[5%] h-[55vmax] w-[55vmax] rounded-full blur-3xl mix-blend-screen"
        style={{
          background: `radial-gradient(circle, color-mix(in oklab, ${HUES[a]} 22%, transparent), transparent 60%)`,
          animation: "mesh-float-a 26s ease-in-out infinite",
        }}
      />
      <div
        className="absolute -right-[10%] bottom-[0%] h-[50vmax] w-[50vmax] rounded-full blur-3xl mix-blend-screen"
        style={{
          background: `radial-gradient(circle, color-mix(in oklab, ${HUES[b]} 18%, transparent), transparent 60%)`,
          animation: "mesh-float-b 32s ease-in-out infinite",
        }}
      />
    </>
  );
}

function ExpandingRings({ tint = "electric", x = "80%", y = "30%" }: { tint?: keyof typeof HUES; x?: string; y?: string }) {
  return (
    <div className="absolute h-[40vmin] w-[40vmin]" style={{ left: x, top: y, transform: "translate(-50%,-50%)" }}>
      {[0, 2.2, 4.4].map((d, i) => (
        <div
          key={i}
          className="absolute inset-0 rounded-full border"
          style={{
            borderColor: `color-mix(in oklab, ${HUES[tint]} 30%, transparent)`,
            animation: `ring-expand 6.6s ease-out ${d}s infinite`,
          }}
        />
      ))}
    </div>
  );
}

function ScanBeam({ tint = "cyan" }: { tint?: keyof typeof HUES }) {
  return (
    <div
      className="absolute inset-x-0 top-0 h-24"
      style={{
        background: `linear-gradient(180deg, transparent, color-mix(in oklab, ${HUES[tint]} 22%, transparent), transparent)`,
        animation: "scanline-move 16s linear infinite",
      }}
    />
  );
}

export function SectionFX({
  variant = "mesh",
  className = "",
}: {
  variant?: Variant;
  className?: string;
}) {
  return (
    <div
      aria-hidden
      className={`pointer-events-none absolute inset-0 -z-10 overflow-hidden ${className}`}
    >
      {variant === "mesh" && (
        <>
          <MeshBlobs a="electric" b="cyan" />
          <Particles count={16} tint="electric" />
          <ScanBeam tint="cyan" />
        </>
      )}

      {variant === "grid" && (
        <>
          <div className="absolute inset-0 ambient-grid opacity-[0.28]" />
          <MeshBlobs a="cyan" b="emerald" />
          <ExpandingRings tint="cyan" x="88%" y="18%" />
          <Particles count={14} tint="cyan" />
        </>
      )}

      {variant === "rings" && (
        <>
          <MeshBlobs a="electric" b="emerald" />
          <ExpandingRings tint="electric" x="18%" y="30%" />
          <ExpandingRings tint="cyan" x="82%" y="70%" />
          <Particles count={14} tint="emerald" />
        </>
      )}

      {variant === "dna" && (
        <>
          <MeshBlobs a="cyan" b="electric" />
          <svg
            viewBox="0 0 1200 300"
            preserveAspectRatio="none"
            className="absolute inset-0 h-full w-full opacity-[0.22]"
          >
            <path
              d="M0,150 C150,40 300,260 450,150 C600,40 750,260 900,150 C1050,40 1200,260 1350,150"
              fill="none"
              stroke={HUES.electric}
              strokeWidth="1.4"
              strokeDasharray="10 12"
              style={{ animation: "dna-wave 6s linear infinite" }}
            />
            <path
              d="M0,150 C150,260 300,40 450,150 C600,260 750,40 900,150 C1050,260 1200,40 1350,150"
              fill="none"
              stroke={HUES.cyan}
              strokeWidth="1.4"
              strokeDasharray="10 12"
              style={{ animation: "dna-wave 7.5s linear infinite reverse" }}
            />
          </svg>
          <Particles count={14} tint="cyan" />
        </>
      )}

      {variant === "neural" && (
        <>
          <MeshBlobs a="electric" b="cyan" />
          <svg viewBox="0 0 1000 500" className="absolute inset-0 h-full w-full opacity-30">
            {[
              [120, 120, 420, 90],
              [120, 260, 420, 250],
              [120, 400, 420, 410],
              [420, 90, 720, 200],
              [420, 250, 720, 200],
              [420, 410, 720, 320],
              [720, 200, 900, 260],
              [720, 320, 900, 260],
            ].map(([x1, y1, x2, y2], i) => (
              <line
                key={i}
                x1={x1} y1={y1} x2={x2} y2={y2}
                stroke={HUES.electric}
                strokeWidth="1"
                strokeDasharray="6 10"
                style={{ animation: `dna-wave ${4 + (i % 4)}s linear ${i * 0.3}s infinite` }}
              />
            ))}
            {[[120, 120], [120, 260], [120, 400], [420, 90], [420, 250], [420, 410], [720, 200], [720, 320], [900, 260]].map(
              ([cx, cy], i) => (
                <circle
                  key={`n${i}`}
                  cx={cx} cy={cy} r="4"
                  fill={i % 2 ? HUES.cyan : HUES.electric}
                  style={{ animation: `tilt-glow ${3 + (i % 3)}s ease-in-out ${i * 0.2}s infinite` }}
                />
              ),
            )}
          </svg>
          <Particles count={12} tint="cyan" />
        </>
      )}

      {variant === "flow" && (
        <>
          <MeshBlobs a="emerald" b="electric" />
          <div className="absolute inset-0">
            {[0, 1, 2, 3].map((i) => (
              <span
                key={i}
                className="absolute h-px w-40"
                style={{
                  top: `${18 + i * 20}%`,
                  left: 0,
                  background: `linear-gradient(90deg, transparent, ${i % 2 ? HUES.cyan : HUES.electric}, transparent)`,
                  animation: `flow-x ${6 + i * 1.5}s linear ${i * 1.2}s infinite`,
                }}
              />
            ))}
          </div>
          <ExpandingRings tint="emerald" x="50%" y="50%" />
          <Particles count={14} tint="emerald" />
        </>
      )}
    </div>
  );
}
