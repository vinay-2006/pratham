import { SectionFX } from "@/components/showcase/section-fx";
import { motion, useScroll, useTransform } from "framer-motion";
import { useRef } from "react";

/* SECTION 2 — THE PROBLEM: chaos of information */
export function Problem() {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start end", "end start"] });
  const chaosOpacity = useTransform(scrollYProgress, [0.15, 0.45, 0.65, 0.85], [0, 1, 1, 0]);
  const calmOpacity = useTransform(scrollYProgress, [0.65, 0.85], [0, 1]);
  const chaosScale = useTransform(scrollYProgress, [0.15, 0.65], [0.9, 1.05]);

  const streams = [
    { label: "PATIENT 44Y M · CHEST PAIN", tag: "VITALS" },
    { label: "HR 128 · BP 92/60 · SpO2 91%", tag: "STREAM" },
    { label: "CXR pending — radiology queue #7", tag: "IMAGING" },
    { label: "TROPONIN I 0.48 ng/mL ↑", tag: "LAB" },
    { label: "NURSE NOTE: diaphoretic, dyspnea", tag: "NLP" },
    { label: "BED 3 · CODE STEMI CALLED", tag: "ALERT" },
    { label: "Patient B · fever 39.4 · rigors", tag: "TRIAGE" },
    { label: "D-DIMER 1.9 · Wells 4.5", tag: "LAB" },
    { label: "GCS 13 · confused", tag: "NEURO" },
    { label: "New arrival · MVA · trauma", tag: "INTAKE" },
  ];

  return (
    <section id="problem" ref={ref} className="relative min-h-[220vh] py-40">
      <div className="sticky top-0 flex h-screen items-center justify-center overflow-hidden">
        {/* Chaotic streams */}
        <motion.div style={{ opacity: chaosOpacity, scale: chaosScale }} className="absolute inset-0 grid-lines">
          <div className="absolute inset-0 flex flex-wrap content-center items-center justify-center gap-3 p-16">
            {streams.map((s, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: false, margin: "-100px" }}
                transition={{ delay: i * 0.08, duration: 0.6 }}
                style={{
                  animation: `drift ${4 + (i % 5)}s ease-in-out ${i * 0.2}s infinite`,
                }}
                className="glass flex items-center gap-3 rounded-xl px-4 py-3 text-sm"
              >
                <span className="font-mono text-[10px] tracking-widest text-electric">{s.tag}</span>
                <span className="text-muted-foreground">{s.label}</span>
              </motion.div>
            ))}
          </div>
          <div className="absolute inset-x-0 bottom-16 text-center font-mono text-[10px] tracking-[0.4em] text-destructive/80">
            SIGNAL-TO-NOISE COLLAPSING · ATTENTION EXCEEDED
          </div>
        </motion.div>

        {/* Calm reveal */}
        <motion.div style={{ opacity: calmOpacity }} className="relative z-10 mx-auto max-w-5xl px-8 text-center">
          <p className="text-eyebrow">02 · THE PROBLEM</p>
          <h2 className="text-display mt-8 text-[clamp(2.5rem,7vw,7rem)]">
            Healthcare professionals
            <br />
            shouldn't <em className="text-electric not-italic">fight</em> information.
          </h2>
          <p className="mx-auto mt-8 max-w-2xl text-lg text-muted-foreground">
            An ED clinician makes hundreds of consequential decisions per shift while juggling vitals, imaging, labs, notes and alarms — the fight is not medicine, it's cognitive load.
          </p>
        </motion.div>
      </div>
    </section>
  );
}

/* SECTION 3 — MEET PRATHAM: pipeline */
export function Pipeline() {
  const stages = [
    { k: "Patient", d: "In-transit ambulance intake, pre-arrival context." },
    { k: "Nurse Intake", d: "Structured vitals, chief complaint, comorbidities." },
    { k: "Clinical NLP", d: "Entity extraction from free-text notes." },
    { k: "Risk Engine", d: "Deterministic NEWS2 · qSOFA · CURB-65 · HEART · Wells." },
    { k: "Evidence", d: "Ranked, cited, editable — never a black box." },
    { k: "Doctor Review", d: "Human-in-the-loop, override, approve." },
    { k: "Clinical Report", d: "Grounded LLM synthesis. Signed. Auditable." },
  ];
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start end", "end start"] });
  const lineScale = useTransform(scrollYProgress, [0.1, 0.9], [0, 1]);

  return (
    <section ref={ref} className="relative isolate overflow-hidden py-40">
      <SectionFX variant="dna" />
      <div className="mx-auto max-w-6xl px-8">
        <p className="text-eyebrow">03 · MEET PRATHAM</p>
        <h2 className="text-display mt-6 text-[clamp(2.5rem,6vw,6rem)]">
          A calm, deterministic <em className="italic text-cyan-soft">pipeline</em> for a chaotic hour.
        </h2>

        <div className="relative mt-24">
          {/* vertical spine */}
          <motion.div
            style={{ scaleY: lineScale, transformOrigin: "top" }}
            className="absolute left-8 top-0 h-full w-px bg-gradient-to-b from-electric via-cyan-soft/60 to-transparent md:left-1/2"
          />
          {/* flowing packets down the spine */}
          <div className="pointer-events-none absolute left-8 top-0 h-full w-px overflow-hidden md:left-1/2">
            {[0, 1.8, 3.6].map((d, i) => (
              <span
                key={i}
                className="absolute left-1/2 h-16 w-px -translate-x-1/2 bg-gradient-to-b from-transparent via-electric to-transparent"
                style={{ animation: `float-up 5.4s linear ${d}s infinite`, transform: "translateY(100vh)" }}
              />
            ))}
          </div>
          <div className="space-y-16">
            {stages.map((s, i) => {
              const left = i % 2 === 0;
              return (
                <motion.div
                  key={s.k}
                  initial={{ opacity: 0, y: 40 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: "-15%" }}
                  transition={{ duration: 0.8, delay: i * 0.05 }}
                  className={`relative flex items-center ${left ? "md:justify-start" : "md:justify-end"}`}
                >
                  <span className="absolute left-8 h-4 w-4 -translate-x-1/2 rounded-full bg-background ring-2 ring-electric md:left-1/2">
                    <span className="absolute inset-0 rounded-full bg-electric/50" style={{ animation: "pulse-ring 2.6s ease-out infinite" }} />
                  </span>
                  <div className={`glass ml-16 max-w-md rounded-2xl p-6 transition-transform hover:-translate-y-1 md:ml-0 md:w-1/2 ${left ? "md:mr-auto md:pr-14" : "md:ml-auto md:pl-14"}`}>
                    <div className="flex items-baseline gap-3">
                      <span className="font-mono text-[10px] tracking-widest text-muted-foreground">{String(i + 1).padStart(2, "0")}</span>
                      <h3 className="text-display text-2xl">{s.k}</h3>
                    </div>
                    <p className="mt-3 text-sm text-muted-foreground">{s.d}</p>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}

/* SECTION 4 — SYSTEM ARCHITECTURE: 7 layers */
export function Architecture() {
  const layers = [
    { n: "L1", k: "Ingest", d: "Ambulance stream · nurse intake · HL7 · uploads", tone: "det" },
    { n: "L2", k: "Extract", d: "Clinical NLP entity extraction · negation · temporal", tone: "det" },
    { n: "L3", k: "Normalize", d: "Demographic-aware labs · SI units · reference ranges", tone: "det" },
    { n: "L4", k: "Score", d: "NEWS2 · qSOFA · CURB-65 · HEART · Wells (pure Python)", tone: "det" },
    { n: "L5", k: "Reason", d: "13-disease rule engine · evidence ranking · confidence", tone: "det" },
    { n: "L6", k: "Synthesize", d: "Grounded LLM narrative · only cites verified metrics", tone: "llm" },
    { n: "L7", k: "Report", d: "Explainable output · versioned · doctor-signed", tone: "det" },
  ];
  return (
    <section id="system" className="relative isolate overflow-hidden py-40">
      <SectionFX variant="neural" />
      <div className="mx-auto max-w-6xl px-8">
        <p className="text-eyebrow">04 · SYSTEM ARCHITECTURE</p>
        <h2 className="text-display mt-6 text-[clamp(2.5rem,6vw,6rem)]">
          Seven layers.
          <br />
          <span className="text-muted-foreground">One clinical intelligence.</span>
        </h2>
        <p className="mt-6 max-w-2xl text-muted-foreground">
          Six deterministic layers do the math. One grounded LLM writes the story — and only from numbers the deterministic layers have already verified.
        </p>

        <div className="mt-20 grid gap-4 md:grid-cols-7">
          {layers.map((l, i) => (
            <motion.div
              key={l.n}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-10%" }}
              transition={{ delay: i * 0.08, duration: 0.7 }}
              className={`glass group relative flex flex-col justify-between rounded-2xl p-5 md:min-h-[280px] ${l.tone === "llm" ? "ring-1 ring-cyan-soft/40" : ""}`}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-[10px] tracking-widest text-muted-foreground">{l.n}</span>
                <span className={`relative h-1.5 w-1.5 rounded-full ${l.tone === "llm" ? "bg-cyan-soft shadow-[0_0_10px_var(--cyan-soft)]" : "bg-electric shadow-[0_0_10px_var(--electric)]"}`}>
                  <span
                    className={`absolute -inset-1 rounded-full ${l.tone === "llm" ? "bg-cyan-soft/40" : "bg-electric/40"}`}
                    style={{ animation: `pulse-ring 2.4s ease-out ${i * 0.2}s infinite` }}
                  />
                </span>
              </div>
              <div className="mt-8">
                <h3 className="text-display text-2xl">{l.k}</h3>
                <p className="mt-3 text-xs leading-relaxed text-muted-foreground">{l.d}</p>
              </div>
              <div className="mt-6 font-mono text-[9px] uppercase tracking-widest text-muted-foreground">
                {l.tone === "llm" ? "GROUNDED · LLM" : "DETERMINISTIC"}
              </div>
              {/* animated connector with traveling packet */}
              {i < layers.length - 1 && (
                <span className="pointer-events-none absolute right-0 top-1/2 hidden h-px w-4 -translate-y-1/2 translate-x-full overflow-hidden bg-gradient-to-r from-electric/60 to-transparent md:block">
                  <span
                    className="absolute inset-y-0 left-0 w-2 bg-electric shadow-[0_0_8px_var(--electric)]"
                    style={{ animation: `flow-x 2.2s linear ${i * 0.25}s infinite` }}
                  />
                </span>
              )}
            </motion.div>
          ))}
        </div>

        <div className="mt-16 grid gap-6 md:grid-cols-2">
          <div className="glass rounded-2xl p-6">
            <span className="font-mono text-[10px] tracking-widest text-electric">DETERMINISTIC</span>
            <p className="text-display mt-3 text-2xl">Pure Python, unit-tested, reproducible.</p>
            <p className="mt-2 text-sm text-muted-foreground">Scores, ranges, rules — every number is a function you can read. No stochasticity in the math.</p>
          </div>
          <div className="glass rounded-2xl p-6 ring-1 ring-cyan-soft/30">
            <span className="font-mono text-[10px] tracking-widest text-cyan-soft">GROUNDED LLM</span>
            <p className="text-display mt-3 text-2xl">Narrative — never invention.</p>
            <p className="mt-2 text-sm text-muted-foreground">The LLM is only allowed to reference metrics the deterministic layers computed. Hallucinated numbers are impossible by construction.</p>
          </div>
        </div>
      </div>
    </section>
  );
}
