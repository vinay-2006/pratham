import { SectionFX } from "@/components/showcase/section-fx";
import { motion, useScroll, useTransform } from "framer-motion";
import { useRef, useState } from "react";

/* SECTION 5 — ENGINEERING CHALLENGES */
export function Engineering() {
  const challenges = [
    {
      t: "Evidence deletion cascades",
      p: "Deleting one lab could quietly invalidate a downstream risk score, but the report still cited it.",
      r: "A clinical report must never reference evidence that no longer exists — silent invalidation is a safety hazard.",
      s: "Introduced an evidence dependency graph. Deletions trigger a scoped pipeline regeneration and mark the report stale.",
      o: "Zero orphaned citations across the 20-scenario regression suite.",
    },
    {
      t: "Pipeline regeneration",
      p: "Full re-runs on every edit were too slow for triage cadence.",
      r: "Doctors edit as new data arrives — sub-second responsiveness is not optional.",
      s: "Content-addressed layer outputs, memoized by input hash. Only affected layers recompute.",
      o: "Median regeneration 240ms · P95 under 900ms.",
    },
    {
      t: "Deterministic calculations",
      p: "LLMs drifted on the same input across runs — unacceptable for a scoring engine.",
      r: "A score that changes between refreshes is not a score.",
      s: "Moved every clinical calculation (NEWS2, qSOFA, CURB-65, HEART, Wells) out of the LLM into pure Python with property-based tests.",
      o: "100% regression accuracy across 20 high-fidelity scenarios.",
    },
    {
      t: "Clinical safety envelope",
      p: "The model kept helpfully suggesting doses.",
      r: "PRATHAM is decision support, not a prescriber. Dosing is out of scope by policy.",
      s: "Hard content firewall: drug names and dosages blocked at the synthesis boundary, verified by adversarial red-team prompts.",
      o: "0 dose recommendations across 10k synthetic prompts.",
    },
    {
      t: "Grounded AI",
      p: "Free-form generation invented lab values and cited studies that did not exist.",
      r: "Every number in a clinical narrative must be traceable to a source metric.",
      s: "Retrieval-constrained generation: the LLM can only reference tokens present in the verified evidence bundle.",
      o: "Every clinical statement carries an evidence pointer.",
    },
    {
      t: "Report regeneration & versioning",
      p: "Doctors needed to see what changed between two reports on the same patient.",
      r: "Trust requires an audit trail — not just a final PDF.",
      s: "Every report is a versioned artifact with a semantic diff of scores, evidence, and narrative.",
      o: "Full longitudinal history per patient, replayable.",
    },
    {
      t: "Explainability by construction",
      p: "'Trust me, it's an AI' is not a clinical answer.",
      r: "A clinician has to defend every decision to a patient, a colleague, and a court.",
      s: "Every score exposes its inputs. Every narrative line links to the metric. Every metric links to the raw record.",
      o: "A doctor can trace any word in the report back to the source in three clicks.",
    },
  ];

  return (
    <section id="engineering" className="relative isolate overflow-hidden py-40">
      <SectionFX variant="grid" />
      <div className="mx-auto max-w-6xl px-8">
        <p className="text-eyebrow">05 · ENGINEERING</p>
        <h2 className="text-display mt-6 text-[clamp(2.5rem,6vw,6rem)]">
          Seven decisions
          <br /><span className="italic text-cyan-soft">that shaped the system.</span>
        </h2>
        <p className="mt-6 max-w-2xl text-muted-foreground">
          Each of these is a story: what broke, why it mattered clinically, how we fixed it, and what it earned us.
        </p>

        <div className="mt-20 space-y-8">
          {challenges.map((c, i) => (
            <ChallengeCard key={c.t} idx={i} {...c} />
          ))}
        </div>
      </div>
    </section>
  );
}

function ChallengeCard({ idx, t, p, r, s, o }: { idx: number; t: string; p: string; r: string; s: string; o: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start end", "end start"] });
  const y = useTransform(scrollYProgress, [0, 1], [40, -40]);
  return (
    <motion.article
      ref={ref}
      style={{ y }}
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true, margin: "-10%" }}
      transition={{ duration: 0.8 }}
      className="glass grid gap-8 rounded-3xl p-8 md:grid-cols-[auto_1fr_1fr_1fr_1fr] md:items-start md:p-10"
    >
      <div className="font-mono text-xs tracking-widest text-electric">
        {String(idx + 1).padStart(2, "0")}
        <div className="mt-3 text-display text-2xl text-foreground">{t}</div>
      </div>
      {[
        { k: "Problem", v: p },
        { k: "Reason", v: r },
        { k: "Solution", v: s },
        { k: "Result", v: o, hi: true },
      ].map((b) => (
        <div key={b.k}>
          <div className={`font-mono text-[10px] tracking-widest ${b.hi ? "text-emerald-soft" : "text-muted-foreground"}`}>{b.k.toUpperCase()}</div>
          <p className="mt-2 text-sm leading-relaxed text-foreground/85">{b.v}</p>
        </div>
      ))}
    </motion.article>
  );
}

/* SECTION 6 — AI */
export function AI() {
  const flow = [
    "Clinical Notes", "NLP", "Entity Extraction", "Lab Intelligence", "Imaging AI",
    "Clinical Scoring", "Evidence Ranking", "Grounded LLM", "Explainable Report",
  ];
  return (
    <section className="relative isolate overflow-hidden py-40">
      <SectionFX variant="neural" />
      <div className="pointer-events-none absolute inset-0 hero-grad opacity-40" />
      <div className="mx-auto max-w-6xl px-8">
        <p className="text-eyebrow">06 · ARTIFICIAL INTELLIGENCE</p>
        <h2 className="text-display mt-6 text-[clamp(2.5rem,6vw,6rem)]">
          Not "we use AI."
          <br /><span className="text-muted-foreground italic">This is how it moves.</span>
        </h2>

        <div className="mt-20 flex flex-wrap items-center justify-center gap-3">
          {flow.map((f, i) => (
            <div key={f} className="contents">
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true, margin: "-10%" }}
                transition={{ delay: i * 0.1, duration: 0.6 }}
                className="glass rounded-full px-5 py-3 text-sm shadow-[0_0_30px_-15px_var(--electric)]"
              >
                {f}
              </motion.div>
              {i < flow.length - 1 && (
                <motion.span
                  initial={{ scaleX: 0 }}
                  whileInView={{ scaleX: 1 }}
                  viewport={{ once: true, margin: "-10%" }}
                  transition={{ delay: i * 0.1 + 0.05, duration: 0.4 }}
                  className="h-px w-8 origin-left bg-gradient-to-r from-electric to-cyan-soft"
                />
              )}
            </div>
          ))}
        </div>

        <div className="mt-24 grid gap-6 md:grid-cols-3">
          {[
            { k: "Entity extraction", v: "Symptoms · temporality · negation · severity — from free-text notes into structured fields." },
            { k: "Lab intelligence", v: "Reference ranges dynamically shift with age, sex, and pregnancy state." },
            { k: "Imaging AI", v: "EfficientNetB0 chest X-ray pneumonia detection with Grad-CAM overlays." },
            { k: "Clinical scoring", v: "NEWS2 · qSOFA · CURB-65 · HEART · Wells PE. All deterministic." },
            { k: "Evidence ranking", v: "13 emergency disease rules with weighted evidence and confidence." },
            { k: "Grounded synthesis", v: "The LLM can only cite metrics it was actually given." },
          ].map((c) => (
            <div key={c.k} className="glass rounded-2xl p-6">
              <div className="text-display text-xl">{c.k}</div>
              <p className="mt-2 text-sm text-muted-foreground">{c.v}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* SECTION 7 — PRODUCTION SYSTEM */
export function Production() {
  const nodes = [
    { k: "Frontend", d: "TanStack Start · React 19" },
    { k: "Backend", d: "FastAPI · Python 3.12" },
    { k: "Database", d: "Postgres · pgvector" },
    { k: "Clinical Engines", d: "Pure-Python deterministic" },
    { k: "AI Gateway", d: "Grounded LLM · guardrails" },
    { k: "Storage", d: "Object store · versioned" },
    { k: "Reports", d: "Signed · auditable PDFs" },
    { k: "Deployment", d: "Edge worker · autoscale" },
  ];
  return (
    <section className="relative isolate overflow-hidden py-40">
      <SectionFX variant="rings" />
      <div className="mx-auto max-w-6xl px-8">
        <p className="text-eyebrow">07 · PRODUCTION SYSTEM</p>
        <h2 className="text-display mt-6 text-[clamp(2.5rem,6vw,6rem)]">
          A living <span className="italic text-cyan-soft">ecosystem</span>, not a logo wall.
        </h2>

        <div className="relative mt-20 grid gap-4 md:grid-cols-4">
          {nodes.map((n, i) => (
            <motion.div
              key={n.k}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.06, duration: 0.6 }}
              className="glass relative overflow-hidden rounded-2xl p-6"
            >
              <div className="flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-soft shadow-[0_0_10px_var(--emerald-soft)]" />
                <span className="font-mono text-[10px] tracking-widest text-muted-foreground">NODE {String(i + 1).padStart(2, "0")}</span>
              </div>
              <div className="text-display mt-6 text-xl">{n.k}</div>
              <div className="mt-1 text-xs text-muted-foreground">{n.d}</div>
              <div
                className="pointer-events-none absolute inset-x-0 -bottom-6 h-6 bg-[linear-gradient(90deg,transparent,var(--electric),transparent)] opacity-40 blur-md"
                style={{ animation: `shimmer ${3 + (i % 3)}s linear infinite`, backgroundSize: "200% 100%" }}
              />
            </motion.div>
          ))}
        </div>

        <div className="mt-10 font-mono text-[10px] tracking-[0.3em] text-muted-foreground">
          ● API REQUESTS · ● DB SYNC · ● PIPELINE HEARTBEAT · ● REPORT SIGNING
        </div>
      </div>
    </section>
  );
}
