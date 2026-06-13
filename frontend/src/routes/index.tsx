import { createFileRoute, Link } from "@tanstack/react-router";
import {
  Activity,
  Ambulance,
  ArrowRight,
  Brain,
  CheckCircle2,
  FileImage,
  Hospital,
  LayoutDashboard,
  ShieldAlert,
  Stethoscope,
} from "lucide-react";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "PRATHAM — AI-Assisted Emergency Coordination & Clinical Intelligence" },
      {
        name: "description",
        content:
          "PRATHAM helps emergency teams prepare faster, prioritize better, and understand clinical situations under pressure.",
      },
    ],
  }),
  component: Landing,
});

function Landing() {
  return (
    <div className="min-h-dvh bg-background text-foreground">
      <Header />
      <main>
        <Hero />
        <WhatItDoes />
        <Workflow />
        <Explainability />
        <Coordination />
        <Features />
      </main>
      <Footer />
    </div>
  );
}

function Header() {
  return (
    <header className="sticky top-0 z-30 border-b bg-background/85 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between gap-4 px-5">
        <Link to="/" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Activity className="h-4 w-4" />
          </div>
          <div className="leading-tight">
            <p className="font-display text-sm font-semibold tracking-tight">PRATHAM</p>
            <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
              Clinical Intelligence
            </p>
          </div>
        </Link>
        <nav className="hidden items-center gap-6 text-sm text-muted-foreground md:flex">
          <a href="#what" className="hover:text-foreground">What it does</a>
          <a href="#workflow" className="hover:text-foreground">Workflow</a>
          <a href="#explainability" className="hover:text-foreground">Explainability</a>
          <a href="#features" className="hover:text-foreground">Features</a>
        </nav>
        <div className="flex items-center gap-2">
          <Button asChild variant="ghost" size="sm">
            <Link to="/nurse/dashboard">Nurse view</Link>
          </Button>
          <Button asChild size="sm">
            <Link to="/doctor/dashboard">
              Doctor view <ArrowRight className="ml-1 h-3.5 w-3.5" />
            </Link>
          </Button>
        </div>
      </div>
    </header>
  );
}

function Hero() {
  return (
    <section className="relative overflow-hidden border-b">
      <div className="absolute inset-0 -z-10">
        <div className="absolute -top-32 left-1/2 h-[420px] w-[820px] -translate-x-1/2 rounded-full bg-primary/10 blur-3xl" />
      </div>
      <div className="mx-auto grid max-w-7xl items-center gap-10 px-5 py-16 md:grid-cols-2 md:py-24">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border bg-card px-3 py-1 text-[11px] font-medium text-muted-foreground">
            <span className="h-1.5 w-1.5 rounded-full bg-[var(--color-severity-low)]" />
            Prototype · Frontend only · Not for clinical use
          </div>
          <h1 className="mt-5 font-display text-4xl font-semibold tracking-tight md:text-5xl lg:text-6xl">
            AI-Assisted Emergency Coordination
            <span className="block text-primary">& Clinical Intelligence</span>
          </h1>
          <p className="mt-5 max-w-xl text-base leading-relaxed text-muted-foreground md:text-lg">
            Helping emergency teams prepare faster, prioritize better, and understand clinical
            situations under pressure — with explainability and uncertainty built in.
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            <Button asChild size="lg">
              <Link to="/nurse/dashboard">
                Open nurse view <ArrowRight className="ml-1.5 h-4 w-4" />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <Link to="/doctor/dashboard">Open doctor view</Link>
            </Button>
          </div>
          <dl className="mt-10 grid grid-cols-3 gap-6 border-t pt-6 text-sm">
            <div>
              <dt className="text-xs text-muted-foreground">Pages</dt>
              <dd className="mt-1 font-display text-xl font-semibold">10</dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Workflow stages</dt>
              <dd className="mt-1 font-display text-xl font-semibold">4</dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Explainability</dt>
              <dd className="mt-1 font-display text-xl font-semibold">First-class</dd>
            </div>
          </dl>
        </div>

        <DashboardPreview />
      </div>
    </section>
  );
}

function DashboardPreview() {
  return (
    <div className="relative">
      <div className="rounded-2xl border bg-card shadow-2xl shadow-primary/5">
        <div className="flex items-center gap-2 border-b px-4 py-3">
          <div className="flex gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-[var(--color-severity-critical)]/60" />
            <span className="h-2.5 w-2.5 rounded-full bg-[var(--color-severity-moderate)]/70" />
            <span className="h-2.5 w-2.5 rounded-full bg-[var(--color-severity-low)]/70" />
          </div>
          <div className="ml-2 text-xs text-muted-foreground">pratham.health / dashboard</div>
          <div className="ml-auto flex items-center gap-2">
            <span className="rounded-full bg-[var(--color-severity-high-soft)] px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-[color-mix(in_oklab,var(--color-severity-high)_70%,black)] dark:text-[var(--color-severity-high)]">
              Evidence · MODERATE
            </span>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3 p-4">
          {[
            { l: "Cardiac", v: 78, c: "var(--color-severity-high)" },
            { l: "Respiratory", v: 62, c: "var(--color-severity-moderate)" },
            { l: "Trauma", v: 8, c: "var(--color-severity-low)" },
            { l: "Neurological", v: 22, c: "var(--color-severity-low)" },
          ].map((r) => (
            <div key={r.l} className="rounded-lg border bg-background p-3">
              <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                {r.l}
              </p>
              <p className="mt-1 font-display text-2xl font-semibold tabular-nums">{r.v}</p>
              <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-muted">
                <div className="h-full rounded-full" style={{ width: `${r.v}%`, background: r.c }} />
              </div>
            </div>
          ))}
        </div>
        <div className="border-t p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
            Assistive differential
          </p>
          <div className="mt-2 space-y-2">
            {[
              ["Acute Coronary Syndrome", 71, "Moderate"],
              ["Pulmonary Embolism", 14, "Low"],
              ["Severe Arrhythmia", 7, "Low"],
            ].map(([n, p, c]) => (
              <div key={n as string} className="flex items-center gap-3">
                <span className="flex-1 truncate text-xs">{n}</span>
                <div className="h-1.5 w-24 overflow-hidden rounded-full bg-muted">
                  <div className="h-full rounded-full bg-primary" style={{ width: `${p}%` }} />
                </div>
                <span className="w-9 text-right text-xs font-medium tabular-nums">{p}%</span>
                <span className="rounded border px-1.5 py-0.5 text-[9px] uppercase tracking-wider text-muted-foreground">
                  AI {c}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function WhatItDoes() {
  const items = [
    {
      icon: Ambulance,
      title: "Coordinates ambulance → hospital",
      copy: "Captures intake while in transit so the receiving team is ready the moment doors open.",
    },
    {
      icon: LayoutDashboard,
      title: "Operational risk at a glance",
      copy: "Translates vitals, symptoms, and context into prepared, prioritized actions — not predictions.",
    },
    {
      icon: Brain,
      title: "Explains, then defers",
      copy: "Surfaces contributing evidence and uncertainty, and suppresses output when evidence is too thin.",
    },
  ];
  return (
    <section id="what" className="border-b">
      <div className="mx-auto max-w-7xl px-5 py-20">
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary">
          What PRATHAM does
        </p>
        <h2 className="mt-2 max-w-2xl font-display text-3xl font-semibold tracking-tight md:text-4xl">
          Decision support for the first ten minutes.
        </h2>
        <div className="mt-10 grid gap-5 md:grid-cols-3">
          {items.map((it) => (
            <div key={it.title} className="rounded-xl border bg-card p-6">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <it.icon className="h-5 w-5" />
              </div>
              <h3 className="mt-4 font-display text-lg font-semibold">{it.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{it.copy}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Workflow() {
  const steps = [
    { t: "Ambulance Intake", d: "Vitals + symptoms captured en route" },
    { t: "Risk Estimation", d: "Operational risk surfaces priorities" },
    { t: "Hospital Prep", d: "ICU, oxygen, CT, trauma team alerted" },
    { t: "Doctor Review", d: "Evidence + AI summary on arrival" },
  ];
  return (
    <section id="workflow" className="border-b bg-muted/30">
      <div className="mx-auto max-w-7xl px-5 py-20">
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary">
          Workflow
        </p>
        <h2 className="mt-2 max-w-2xl font-display text-3xl font-semibold tracking-tight md:text-4xl">
          Ambulance to hospital, in one continuous thread.
        </h2>

        <div className="mt-12 relative">
          <div className="absolute left-0 right-0 top-5 hidden h-px bg-border md:block" />
          <ol className="grid gap-6 md:grid-cols-4">
            {steps.map((s, i) => (
              <li key={s.t} className="relative">
                <div className="relative z-10 flex h-10 w-10 items-center justify-center rounded-full border bg-background font-display text-sm font-semibold text-primary">
                  {i + 1}
                </div>
                <p className="mt-3 font-medium">{s.t}</p>
                <p className="mt-1 text-sm text-muted-foreground">{s.d}</p>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </section>
  );
}

function Explainability() {
  return (
    <section id="explainability" className="border-b">
      <div className="mx-auto grid max-w-7xl items-center gap-12 px-5 py-20 md:grid-cols-2">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary">
            Explainable AI
          </p>
          <h2 className="mt-2 font-display text-3xl font-semibold tracking-tight md:text-4xl">
            Observable reasoning, not magic output.
          </h2>
          <p className="mt-4 text-base leading-relaxed text-muted-foreground">
            Every estimate is paired with the evidence that produced it — labs, vitals, imaging
            findings, free-text — each with provenance. When evidence is insufficient, PRATHAM
            says so clearly instead of generating false confidence.
          </p>
          <ul className="mt-6 space-y-3 text-sm">
            {[
              "Contributing evidence per condition",
              "AI confidence separate from probability",
              "Confidence suppression when evidence is thin",
              "Missing-evidence callouts on every relevant view",
            ].map((t) => (
              <li key={t} className="flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-[var(--color-severity-low)]" />
                <span>{t}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-2xl border bg-card p-5 shadow-xl shadow-primary/5">
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Acute Coronary Syndrome · 71%
          </p>
          <div className="mt-3 space-y-2">
            {[
              ["Symptom pattern (chest pain + radiation)", "Source · intake free-text"],
              ["Heart rate 118 bpm", "Source · ambulance monitor"],
              ["Age + sex risk profile", "Source · patient demographics"],
            ].map(([f, s]) => (
              <div key={f} className="rounded-md border bg-background p-3">
                <p className="text-sm font-medium">{f}</p>
                <p className="mt-0.5 font-mono text-[11px] text-muted-foreground">{s}</p>
              </div>
            ))}
          </div>
          <div className="mt-4 rounded-md border border-[var(--color-severity-moderate)]/30 bg-[var(--color-severity-moderate-soft)] p-3 text-xs leading-relaxed text-[color-mix(in_oklab,var(--color-severity-moderate)_55%,black)] dark:text-[var(--color-severity-moderate)]">
            Troponin and ECG not yet available — estimate may shift substantially.
          </div>
        </div>
      </div>
    </section>
  );
}

function Coordination() {
  const items = [
    { i: Hospital, t: "ICU bed standby", d: "Pre-allocated based on incoming severity" },
    { i: Activity, t: "Oxygen prep", d: "Set up before the patient arrives" },
    { i: Stethoscope, t: "Trauma team prep", d: "On-call alerted with case summary" },
    { i: FileImage, t: "CT readiness", d: "Suite reserved, technician notified" },
  ];
  return (
    <section className="border-b bg-muted/30">
      <div className="mx-auto max-w-7xl px-5 py-20">
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary">
          Hospital preparation coordination
        </p>
        <h2 className="mt-2 max-w-2xl font-display text-3xl font-semibold tracking-tight md:text-4xl">
          Prep moves while the ambulance is still moving.
        </h2>
        <div className="mt-10 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {items.map((it) => (
            <div key={it.t} className="rounded-xl border bg-card p-5">
              <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary/10 text-primary">
                <it.i className="h-4 w-4" />
              </div>
              <p className="mt-4 font-medium">{it.t}</p>
              <p className="mt-1 text-sm text-muted-foreground">{it.d}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Features() {
  const items = [
    { i: LayoutDashboard, t: "Operational Risk Dashboard", d: "Command-center view of priorities" },
    { i: FileImage, t: "Imaging Analysis", d: "Grad-CAM overlay + confidence" },
    { i: Brain, t: "Explainability Panel", d: "Evidence cards with provenance" },
    { i: ShieldAlert, t: "Confidence Suppression", d: "Suppress output when evidence is thin" },
    { i: Ambulance, t: "Emergency Intake", d: "Multi-section in-transit capture" },
    { i: Stethoscope, t: "Doctor Review", d: "Workstation for on-arrival review" },
  ];
  return (
    <section id="features" className="border-b">
      <div className="mx-auto max-w-7xl px-5 py-20">
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary">
          Features
        </p>
        <h2 className="mt-2 max-w-2xl font-display text-3xl font-semibold tracking-tight md:text-4xl">
          Built around the emergency workflow.
        </h2>
        <div className="mt-10 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {items.map((it) => (
            <div key={it.t} className="group rounded-xl border bg-card p-6 transition-colors hover:border-primary/40">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted text-foreground">
                <it.i className="h-5 w-5" />
              </div>
              <p className="mt-4 font-display text-lg font-semibold">{it.t}</p>
              <p className="mt-1.5 text-sm text-muted-foreground">{it.d}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="bg-background">
      <div className="mx-auto flex max-w-7xl flex-col gap-4 px-5 py-10 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Activity className="h-3.5 w-3.5" />
          </div>
          <span className="font-display text-sm font-semibold">PRATHAM</span>
          <span className="text-xs text-muted-foreground">· Clinical Intelligence Prototype</span>
        </div>
        <p className="max-w-md text-xs leading-relaxed text-muted-foreground">
          Research / educational prototype built by an AIML student. Not a medical device. Not
          intended for diagnosis, treatment, or any clinical use.
        </p>
      </div>
    </footer>
  );
}
