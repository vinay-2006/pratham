import { motion, useScroll, useTransform } from "framer-motion";
import { useRef } from "react";
import { Link } from "@tanstack/react-router";

const SYSTEM_STATUS = [
  { name: "Imaging AI", status: "online" },
  { name: "Lab Engine", status: "online" },
  { name: "Clinical NLP", status: "online" },
  { name: "Risk Scoring", status: "online" },
  { name: "Copilot", status: "online" },
];

export function Nav() {
  return (
    <motion.nav
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.8, delay: 0.2 }}
      className="fixed inset-x-0 top-0 z-50 flex items-center justify-between px-8 py-6"
    >
      <div className="flex items-center gap-2">
        <div className="relative h-2 w-2 rounded-full bg-electric shadow-[0_0_12px_var(--electric)]">
          <span className="absolute inset-0 rounded-full bg-electric" style={{ animation: "pulse-ring 2s ease-out infinite" }} />
        </div>
        <span className="font-mono text-xs tracking-[0.3em]">PRATHAM</span>
      </div>
      <div className="hidden items-center gap-8 font-mono text-xs tracking-widest text-muted-foreground md:flex">
        <a href="#problem" className="transition-colors hover:text-foreground">01 · CHAOS</a>
        <a href="#system" className="transition-colors hover:text-foreground">02 · SYSTEM</a>
        <a href="#engineering" className="transition-colors hover:text-foreground">03 · ENGINEERING</a>
        <a href="#demo" className="transition-colors hover:text-foreground">04 · DEMO</a>
      </div>
      <div className="font-mono text-[10px] tracking-[0.3em] text-muted-foreground">v6.0.0 · CASE STUDY</div>
    </motion.nav>
  );
}

export function Hero() {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start start", "end start"] });
  const y = useTransform(scrollYProgress, [0, 1], [0, 200]);
  const scale = useTransform(scrollYProgress, [0, 1], [1, 1.15]);
  const opacity = useTransform(scrollYProgress, [0, 0.8], [1, 0]);
  const blur = useTransform(scrollYProgress, [0, 1], ["blur(0px)", "blur(12px)"]);

  return (
    <section ref={ref} className="relative flex min-h-[110vh] flex-col justify-between overflow-hidden pt-32">
      {/* Ambient background */}
      <motion.div style={{ scale, opacity }} className="pointer-events-none absolute inset-0 hero-grad" />
      <motion.div style={{ opacity }} className="pointer-events-none absolute inset-0 grid-lines opacity-40" />

      {/* Floating orbs */}
      <div className="pointer-events-none absolute inset-0">
        {Array.from({ length: 24 }).map((_, i) => (
          <motion.span
            key={i}
            className="absolute h-1 w-1 rounded-full bg-cyan-soft/60"
            initial={{ opacity: 0 }}
            animate={{ opacity: [0, 1, 0], y: [-20, -80] }}
            transition={{ duration: 6 + (i % 5), repeat: Infinity, delay: i * 0.3 }}
            style={{ left: `${(i * 37) % 100}%`, top: `${40 + ((i * 13) % 50)}%` }}
          />
        ))}
      </div>

      {/* Breathing halo + rotating holographic rings behind headline */}
      <div className="pointer-events-none absolute left-1/2 top-[45%] -translate-x-1/2 -translate-y-1/2">
        <div
          className="h-[70vmin] w-[70vmin] rounded-full opacity-70 blur-2xl"
          style={{
            background: "radial-gradient(circle, oklch(0.72 0.19 245 / 0.35), transparent 60%)",
            animation: "breathe 6s ease-in-out infinite",
          }}
        />
      </div>
      <div className="pointer-events-none absolute left-1/2 top-[45%] -translate-x-1/2 -translate-y-1/2">
        {[0.6, 0.85, 1.1].map((s, i) => (
          <div
            key={i}
            className="absolute left-1/2 top-1/2 h-[50vmin] w-[50vmin] -translate-x-1/2 -translate-y-1/2 rounded-full border border-electric/15"
            style={{ transform: `translate(-50%, -50%) scale(${s})`, animation: `${i % 2 ? "ring-rot" : "spin-slow"} ${40 + i * 15}s linear infinite` }}
          >
            <span className="absolute -top-1 left-1/2 h-2 w-2 -translate-x-1/2 rounded-full bg-cyan-soft shadow-[0_0_12px_var(--cyan-soft)]" />
          </div>
        ))}
      </div>

      <motion.div style={{ y, opacity, filter: blur }} className="relative z-10 mx-auto max-w-7xl px-8">
        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 1 }}
          className="text-eyebrow"
        >
          A CASE STUDY · PREDICTIVE RISK ASSESSMENT & TRIAGE FOR HEALTHCARE AI
        </motion.p>

        <h1 className="text-display mt-8 text-[clamp(3rem,9vw,10rem)] leading-[0.9]">
          {["Emergency", "departments make", "hundreds of critical", "decisions every day."].map((line, i) => (
            <motion.span
              key={i}
              initial={{ opacity: 0, y: 40, filter: "blur(12px)" }}
              animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
              transition={{ delay: 0.6 + i * 0.15, duration: 1.1, ease: [0.22, 1, 0.36, 1] }}
              className="block"
            >
              {line}
            </motion.span>
          ))}
        </h1>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.6, duration: 1 }}
          className="text-display mt-10 max-w-3xl text-2xl italic text-muted-foreground md:text-4xl"
        >
          What if AI could organize the chaos <span className="text-foreground">instead of replacing the doctor?</span>
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 2, duration: 0.8 }}
          className="mt-16 flex flex-wrap items-center gap-6"
        >
          <Link to="/nurse/dashboard" className="group relative inline-flex items-center gap-3 rounded-full bg-electric px-7 py-3.5 text-sm font-medium text-primary-foreground shadow-[var(--shadow-glow)] transition-transform hover:scale-[1.02]">
            Explore PRATHAM
            <span className="inline-block transition-transform group-hover:translate-x-1">→</span>
          </Link>
          <span className="font-mono text-xs tracking-widest text-muted-foreground">LAUNCH TRIAGE WORKSPACE</span>
        </motion.div>
      </motion.div>

      {/* Status bar with system indicators */}
      <div className="relative z-10 mt-16 overflow-hidden border-y border-glass-border/60 bg-ink/40 py-8 backdrop-blur">
        <div className="flex flex-wrap items-center gap-x-8 gap-y-3 px-8 font-mono text-[10px] tracking-[0.3em] text-muted-foreground">
          {/* Live system status */}
          <div className="flex items-center gap-6">
            {SYSTEM_STATUS.map((sys, i) => (
              <motion.span
                key={sys.name}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 2.2 + i * 0.15 }}
                className="flex items-center gap-1.5"
              >
                <span className="relative flex h-1.5 w-1.5">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-soft opacity-75" />
                  <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-soft shadow-[0_0_6px_var(--emerald-soft)]" />
                </span>
                {sys.name}
              </motion.span>
            ))}
          </div>
          <span className="hidden md:inline">7 LAYERS</span>
          <span className="hidden md:inline">13 CONDITIONS</span>
          <span className="hidden lg:inline">100% REGRESSION</span>
          <svg viewBox="0 0 400 40" className="ml-auto hidden h-10 w-64 md:block">
            <path
              d="M0,20 L60,20 L70,20 L80,5 L90,35 L100,10 L110,20 L180,20 L190,20 L200,8 L210,32 L220,20 L400,20"
              fill="none"
              stroke="var(--electric)"
              strokeWidth="1.5"
              strokeDasharray="1000"
              style={{ animation: "ecg 3s linear infinite" }}
            />
          </svg>
        </div>
      </div>
    </section>
  );
}
