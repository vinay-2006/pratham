import { SectionFX } from "@/components/showcase/section-fx";
import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useState } from "react";

/* SECTION 8 — INTERACTIVE DEMO */
export function Demo() {
  const steps = [
    { k: "Ambulance intake", d: "Patient · 62M · chest pain radiating to left arm · 22 min out", meta: "PRE-ARRIVAL" },
    { k: "Nurse vitals", d: "HR 118 · BP 96/62 · SpO2 93% · Temp 37.1 · Pain 8/10", meta: "TRIAGE" },
    { k: "Clinical NLP", d: "Extracted: chest pain · diaphoresis · dyspnea · history HTN, DM", meta: "L2" },
    { k: "Labs & imaging", d: "Troponin I 0.42 ↑ · D-Dimer 380 · CXR: no acute infiltrate", meta: "L3" },
    { k: "Risk engine", d: "HEART 7 · NEWS2 5 · qSOFA 1 · Wells PE 1.5", meta: "L4" },
    { k: "Evidence ranked", d: "Top: ACS (0.82) · Aortic dissection (0.11) · PE (0.04)", meta: "L5" },
    { k: "Grounded report", d: "Draft synthesized from 14 verified metrics · 0 unsourced claims", meta: "L6" },
    { k: "Doctor review", d: "Investigation approved · patient to cath lab · report signed", meta: "L7" },
  ];
  const [i, setI] = useState(0);
  const [playing, setPlaying] = useState(true);
  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => setI((x) => (x + 1) % steps.length), 2600);
    return () => clearInterval(id);
  }, [playing, steps.length]);
  const s = steps[i];

  return (
    <section id="demo" className="relative isolate overflow-hidden py-40">
      <SectionFX variant="mesh" />
      <div className="mx-auto max-w-6xl px-8">
        <p className="text-eyebrow">08 · INTERACTIVE DEMO</p>
        <h2 className="text-display mt-6 text-[clamp(2.5rem,6vw,6rem)]">
          A patient arrives.
          <br /><span className="text-muted-foreground italic">Watch the system think.</span>
        </h2>

        <div className="mt-16 grid gap-6 md:grid-cols-[280px_1fr]">
          <ol className="glass rounded-2xl p-4">
            {steps.map((st, idx) => (
              <li key={st.k}>
                <button
                  onClick={() => { setI(idx); setPlaying(false); }}
                  className={`flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left transition ${idx === i ? "bg-glass text-foreground" : "text-muted-foreground hover:text-foreground"}`}
                >
                  <span className={`h-1.5 w-1.5 rounded-full ${idx === i ? "bg-electric shadow-[0_0_10px_var(--electric)]" : "bg-muted-foreground/50"}`} />
                  <span className="font-mono text-[10px] tracking-widest">{st.meta}</span>
                  <span className="text-sm">{st.k}</span>
                </button>
              </li>
            ))}
            <li className="mt-2 border-t border-glass-border px-3 pt-3">
              <button onClick={() => setPlaying((p) => !p)} className="font-mono text-[10px] tracking-widest text-electric">
                {playing ? "⏸ PAUSE" : "▶ AUTOPLAY"}
              </button>
            </li>
          </ol>

          <div className="glass relative overflow-hidden rounded-3xl p-10 md:p-14 min-h-[420px]">
            <AnimatePresence mode="wait">
              <motion.div
                key={s.k}
                initial={{ opacity: 0, y: 20, filter: "blur(8px)" }}
                animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
                exit={{ opacity: 0, y: -20, filter: "blur(8px)" }}
                transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
              >
                <div className="font-mono text-[10px] tracking-widest text-electric">STEP {String(i + 1).padStart(2, "0")} / {steps.length} · {s.meta}</div>
                <h3 className="text-display mt-6 text-4xl md:text-6xl">{s.k}</h3>
                <p className="mt-6 max-w-xl text-lg text-muted-foreground">{s.d}</p>
              </motion.div>
            </AnimatePresence>

            <div className="absolute inset-x-10 bottom-8 flex items-center gap-2">
              {steps.map((_, idx) => (
                <span key={idx} className={`h-0.5 flex-1 rounded-full ${idx <= i ? "bg-electric" : "bg-glass-border"}`} />
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* SECTION 9 — SYSTEM ATLAS */
export function Atlas() {
  const modules = [
    { k: "Architecture Explorer", d: "Every layer, every dependency, every call — traversable." },
    { k: "API Explorer", d: "Live surface with schemas, examples, and evidence contracts." },
    { k: "Decision Graph", d: "Why the system arrived at this ranking, visualized." },
    { k: "Data Flow", d: "From ambulance stream to signed report, edge-by-edge." },
    { k: "Pipeline Visualization", d: "Per-request layer timings and cache hits." },
    { k: "Interactive System Map", d: "Zoom from patient to layer to line of code." },
  ];
  return (
    <section className="relative isolate overflow-hidden py-40">
      <SectionFX variant="flow" />
      <div className="mx-auto max-w-6xl px-8">
        <p className="text-eyebrow">09 · SYSTEM ATLAS</p>
        <h2 className="text-display mt-6 text-[clamp(2.5rem,6vw,6rem)]">
          Observability, treated as a <em className="italic text-cyan-soft">product</em>.
        </h2>
        <p className="mt-6 max-w-2xl text-muted-foreground">
          Clinicians need to trust the system. Engineers need to reason about it. The System Atlas is how both meet.
        </p>

        <div className="mt-16 grid gap-4 md:grid-cols-3">
          {modules.map((m, i) => (
            <motion.div
              key={m.k}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.06, duration: 0.6 }}
              className="glass group relative overflow-hidden rounded-2xl p-6"
            >
              <div className="font-mono text-[10px] tracking-widest text-muted-foreground">MODULE {String(i + 1).padStart(2, "0")}</div>
              <div className="text-display mt-6 text-2xl">{m.k}</div>
              <p className="mt-3 text-sm text-muted-foreground">{m.d}</p>
              <div className="mt-6 flex gap-1">
                {Array.from({ length: 24 }).map((_, k) => (
                  <span key={k} className="h-6 w-1 rounded-full bg-glass-border" style={{ opacity: 0.2 + ((k + i) % 5) * 0.15 }} />
                ))}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* SECTION 10 — TIMELINE */
export function Timeline() {
  const versions = [
    { v: "v1", t: "Intake prototype", d: "Structured triage capture and a first pass at NEWS2." },
    { v: "v2", t: "Deterministic scoring", d: "All clinical scores moved out of the LLM into pure Python." },
    { v: "v3", t: "Evidence & grounding", d: "Retrieval-constrained generation, evidence dependency graph." },
    { v: "v4", t: "Imaging & NLP", d: "EfficientNetB0 CXR pipeline, entity extraction, longitudinal deltas." },
    { v: "v5", t: "System Atlas & Copilot", d: "Observability portal, ED Command Center, conversational Q&A." },
  ];
  return (
    <section className="relative isolate overflow-hidden py-40">
      <SectionFX variant="grid" />
      <div className="mx-auto max-w-6xl px-8">
        <p className="text-eyebrow">10 · TIMELINE</p>
        <h2 className="text-display mt-6 text-[clamp(2.5rem,6vw,6rem)]">Four phases. One trajectory.</h2>

        <div className="mt-20 grid gap-4 md:grid-cols-5">
          {versions.map((v, i) => (
            <motion.div
              key={v.v}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1, duration: 0.6 }}
              className="glass rounded-2xl p-5"
            >
              <div className="font-mono text-xs tracking-widest text-electric">{v.v.toUpperCase()}</div>
              <div className="text-display mt-6 text-xl">{v.t}</div>
              <p className="mt-2 text-xs text-muted-foreground">{v.d}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* SECTION 11 — LESSONS */
export function Lessons() {
  const lessons = [
    ["Architecture", "Boundaries first, features second. Layers are contracts."],
    ["Reliability", "Determinism where the stakes are highest. LLMs at the edges."],
    ["Clinical Safety", "Refusals are a feature. Dose is not our surface."],
    ["AI Integration", "Grounding is a construction, not a prompt."],
    ["Explainability", "Every claim is a link. Every link is testable."],
    ["Healthcare Workflow", "Design for interruption. The ED never pauses for us."],
    ["System Design", "Cache what is expensive, hash what is deterministic."],
    ["Performance Engineering", "Latency is trust; sub-second is a clinical requirement."],
  ];
  return (
    <section className="relative isolate overflow-hidden py-40">
      <SectionFX variant="rings" />
      <div className="mx-auto max-w-6xl px-8">
        <p className="text-eyebrow">11 · LESSONS</p>
        <h2 className="text-display mt-6 text-[clamp(2.5rem,6vw,6rem)]">What the system taught the engineer.</h2>

        <div className="mt-16 grid gap-6 md:grid-cols-2">
          {lessons.map(([k, v], i) => (
            <motion.div
              key={k}
              initial={{ opacity: 0, x: i % 2 ? 30 : -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.7, delay: (i % 2) * 0.1 }}
              className="border-b border-glass-border pb-6"
            >
              <div className="font-mono text-[10px] tracking-widest text-electric">{String(i + 1).padStart(2, "0")}</div>
              <div className="text-display mt-3 text-3xl">{k}</div>
              <p className="mt-3 max-w-xl text-muted-foreground">{v}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* SECTION 12 — FINALE with Launch CTA */
export function Finale({ onLaunch }: { onLaunch: () => void }) {
  return (
    <section className="relative isolate flex min-h-screen items-center overflow-hidden py-40">
      <SectionFX variant="rings" />
      <div className="pointer-events-none absolute inset-0 hero-grad opacity-60" />
      <div className="pointer-events-none absolute inset-0 grid-lines opacity-30" />
      <div className="relative mx-auto max-w-6xl px-8 text-center">
        <motion.h2
          initial={{ opacity: 0, filter: "blur(20px)", y: 40 }}
          whileInView={{ opacity: 1, filter: "blur(0px)", y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 1.4, ease: [0.22, 1, 0.36, 1] }}
          className="text-display text-[clamp(4rem,16vw,18rem)] leading-[0.85] tracking-tighter"
        >
          PRATHAM
        </motion.h2>
        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.4, duration: 1 }}
          className="mt-6 text-lg text-muted-foreground md:text-2xl"
        >
          Emergency Clinical Intelligence Platform
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.8, duration: 1 }}
          className="text-display mx-auto mt-20 max-w-3xl space-y-3 text-2xl md:text-4xl"
        >
          <div>Built to <em className="italic text-electric">augment</em> clinicians.</div>
          <div>Designed for <em className="italic text-cyan-soft">transparency</em>.</div>
          <div>Engineered for <em className="italic text-emerald-soft">trust</em>.</div>
        </motion.div>

        {/* Launch CTA */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 1.2, duration: 1 }}
          className="mt-20"
        >
          <button
            onClick={onLaunch}
            className="group relative inline-flex flex-col items-center gap-2 rounded-full shimmer-border px-12 py-5 transition-all duration-500 hover:scale-[1.03] hover:shadow-[0_0_80px_-12px_var(--electric)]"
          >
            <span className="flex items-center gap-3 text-lg font-medium tracking-wide text-foreground">
              <span className="text-xl">🚀</span>
              Launch PRATHAM
              <span className="inline-block transition-transform duration-300 group-hover:translate-x-2">→</span>
            </span>
            <span className="font-mono text-[10px] tracking-[0.3em] text-muted-foreground">
              AI-ASSISTED EMERGENCY WORKSPACE
            </span>
          </button>

          {/* Keyboard hint */}
          <motion.p
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 2, duration: 1 }}
            className="mt-6 font-mono text-[10px] tracking-widest text-muted-foreground/50"
          >
            or press <kbd className="rounded border border-glass-border px-1.5 py-0.5 font-mono text-[10px]">Enter</kbd> to launch
          </motion.p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 1.4, duration: 1 }}
          className="mt-24 font-mono text-xs tracking-[0.4em] text-muted-foreground"
        >
          CASE STUDY · BY VINAY KUMAR REDDY
        </motion.div>
      </div>
    </section>
  );
}
