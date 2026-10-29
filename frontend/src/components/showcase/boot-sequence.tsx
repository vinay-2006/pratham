import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate } from "@tanstack/react-router";

const MODULES = [
  { name: "FastAPI Backend", icon: "⚡" },
  { name: "Supabase PostgreSQL", icon: "🗄️" },
  { name: "Clinical NLP Engine", icon: "🧠" },
  { name: "Risk Scoring Engine", icon: "📊" },
  { name: "Investigation Engine", icon: "🔬" },
  { name: "Lab Intelligence AI", icon: "🧪" },
  { name: "Imaging AI (EfficientNetB0)", icon: "📷" },
  { name: "Aggregation Pipeline", icon: "⚙️" },
  { name: "Report Service", icon: "📋" },
  { name: "Clinical Copilot", icon: "✨" },
];

export function BootSequence({
  isVisible,
  onComplete,
}: {
  isVisible: boolean;
  onComplete: () => void;
}) {
  const navigate = useNavigate();
  const [loadedCount, setLoadedCount] = useState(0);
  const [phase, setPhase] = useState<"boot" | "launching" | "done">("boot");

  useEffect(() => {
    if (!isVisible) {
      setLoadedCount(0);
      setPhase("boot");
      return;
    }

    let idx = 0;
    const interval = setInterval(() => {
      idx++;
      setLoadedCount(idx);
      if (idx >= MODULES.length) {
        clearInterval(interval);
        setTimeout(() => setPhase("launching"), 400);
        setTimeout(() => {
          setPhase("done");
          navigate({ to: "/nurse/dashboard" });
          onComplete();
        }, 1800);
      }
    }, 160);

    return () => clearInterval(interval);
  }, [isVisible, navigate, onComplete]);

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0, scale: 1.05, filter: "blur(20px)" }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          className="fixed inset-0 z-[100] flex items-center justify-center"
          style={{
            background:
              "radial-gradient(ellipse at center, oklch(0.14 0.03 250), oklch(0.06 0.015 260))",
          }}
        >
          {/* Ambient scan line */}
          <div
            className="pointer-events-none absolute inset-x-0 h-32 opacity-20"
            style={{
              background:
                "linear-gradient(180deg, transparent, oklch(0.72 0.19 245 / 0.3), transparent)",
              animation: "boot-scanline 3s linear infinite",
            }}
          />

          {/* Grid background */}
          <div className="pointer-events-none absolute inset-0 grid-lines opacity-20" />

          <div className="relative w-full max-w-lg px-8">
            {/* Header */}
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
              className="text-center"
            >
              <div className="font-mono text-[10px] tracking-[0.4em] text-muted-foreground">
                INITIALIZING
              </div>
              <h1
                className="mt-4 text-5xl font-normal tracking-tighter md:text-7xl"
                style={{ fontFamily: "var(--font-display)" }}
              >
                PRATHAM
              </h1>
              <p className="mt-2 font-mono text-xs tracking-widest text-muted-foreground">
                Emergency Clinical Intelligence Platform
              </p>
            </motion.div>

            {/* Divider */}
            <motion.div
              initial={{ scaleX: 0 }}
              animate={{ scaleX: 1 }}
              transition={{ delay: 0.4, duration: 0.8 }}
              className="mx-auto mt-8 h-px w-full origin-center bg-gradient-to-r from-transparent via-electric/50 to-transparent"
            />

            {/* Module list */}
            <div className="mt-8 space-y-1.5">
              {MODULES.map((mod, i) => {
                const loaded = i < loadedCount;
                return (
                  <motion.div
                    key={mod.name}
                    initial={{ opacity: 0, x: -12 }}
                    animate={{
                      opacity: loaded ? 1 : 0.3,
                      x: 0,
                    }}
                    transition={{
                      delay: 0.5 + i * 0.04,
                      duration: 0.4,
                    }}
                    className="flex items-center gap-3 font-mono text-xs"
                  >
                    <motion.span
                      animate={{
                        color: loaded
                          ? "var(--emerald-soft)"
                          : "var(--muted-foreground)",
                      }}
                      className="w-4 text-center"
                    >
                      {loaded ? "✓" : "○"}
                    </motion.span>
                    <span
                      className="tracking-widest transition-colors duration-300"
                      style={{
                        color: loaded
                          ? "var(--foreground)"
                          : "var(--muted-foreground)",
                      }}
                    >
                      {mod.name}
                    </span>
                    {loaded && (
                      <motion.span
                        initial={{ opacity: 0, scale: 0 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="ml-auto text-[10px] tracking-widest text-emerald-soft"
                      >
                        READY
                      </motion.span>
                    )}
                  </motion.div>
                );
              })}
            </div>

            {/* Progress bar */}
            <div className="mt-8 h-px w-full overflow-hidden rounded-full bg-glass-border">
              <motion.div
                className="h-full bg-gradient-to-r from-electric via-cyan-soft to-emerald-soft"
                initial={{ width: "0%" }}
                animate={{
                  width: `${(loadedCount / MODULES.length) * 100}%`,
                }}
                transition={{ duration: 0.15, ease: "easeOut" }}
              />
            </div>

            {/* Status text */}
            <motion.div
              className="mt-6 text-center font-mono text-[10px] tracking-[0.3em]"
              animate={{
                color:
                  phase === "launching"
                    ? "var(--electric)"
                    : "var(--muted-foreground)",
              }}
            >
              {phase === "boot" && (
                <span>
                  Loading modules...{" "}
                  <span className="tabular-nums">
                    {loadedCount}/{MODULES.length}
                  </span>
                </span>
              )}
              {phase === "launching" && (
                <motion.span
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  style={{ animation: "boot-pulse 1.2s ease-in-out infinite" }}
                >
                  LAUNCHING WORKSPACE...
                </motion.span>
              )}
            </motion.div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
