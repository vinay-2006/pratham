/**
 * PortfolioLandingPage — Modern SaaS Portfolio Presentation Homepage
 */

import { Activity, ShieldCheck, Cpu, Database, Brain, ArrowRight, CheckCircle2, Server, Award, Zap } from "lucide-react";
import { Link } from "@tanstack/react-router";

export function PortfolioLandingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Hero Section */}
      <section className="relative px-6 py-20 md:py-32 max-w-7xl mx-auto text-center space-y-6">
        <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-1.5 text-xs font-semibold text-primary">
          <Award className="h-4 w-4" /> PRATHAM v2.0 — Enterprise Emergency Medical AI Platform
        </div>

        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-slate-900 dark:text-slate-50 max-w-4xl mx-auto leading-tight">
          Intelligent Triage & Clinical Decision Support for Emergency Care
        </h1>

        <p className="text-base md:text-lg text-slate-600 dark:text-slate-300 max-w-2xl mx-auto leading-relaxed">
          PRATHAM combines 13 standardized emergency condition engines, demographic lab analysis, clinical scoring systems (NEWS2, qSOFA, HEART), and grounded AI reasoning to reduce diagnostic uncertainty in high-acuity settings.
        </p>

        <div className="flex flex-wrap justify-center gap-4 pt-4">
          <Link
            to="/nurse/intake"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-primary text-primary-foreground font-bold text-sm hover:opacity-90 transition-opacity shadow-lg shadow-primary/20"
          >
            Launch Emergency Workstation <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            to="/admin"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-card hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-200 font-bold text-sm transition-colors"
          >
            View Telemetry Dashboard
          </Link>
        </div>
      </section>

      {/* Core Platform Capabilities Grid */}
      <section className="px-6 py-16 bg-slate-50/50 dark:bg-slate-900/30 border-y border-slate-200 dark:border-slate-800">
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="text-center space-y-2">
            <h2 className="text-2xl md:text-3xl font-bold text-slate-900 dark:text-slate-50">Enterprise Architectural Pillars</h2>
            <p className="text-xs text-slate-500 max-w-xl mx-auto">Built from the ground up for zero missing data hallucinations and total clinical auditability</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-6 rounded-2xl border border-slate-200 dark:border-slate-800 bg-card space-y-3">
              <div className="h-10 w-10 rounded-xl bg-rose-100 dark:bg-rose-950/60 text-rose-600 dark:text-rose-400 flex items-center justify-center">
                <Brain className="h-5 w-5" />
              </div>
              <h3 className="font-bold text-slate-900 dark:text-slate-100 text-base">13 Emergency Condition Engine</h3>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                Evaluates standardized YAML rules for ACS, Heart Failure, Sepsis, Pneumonia, PE, Stroke, DKA, AKI, and 5 more acute emergencies.
              </p>
            </div>

            <div className="p-6 rounded-2xl border border-slate-200 dark:border-slate-800 bg-card space-y-3">
              <div className="h-10 w-10 rounded-xl bg-blue-100 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 flex items-center justify-center">
                <Cpu className="h-5 w-5" />
              </div>
              <h3 className="font-bold text-slate-900 dark:text-slate-100 text-base">Clinical Scoring Calculators</h3>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                Deterministic calculation of NEWS2, qSOFA, CURB-65, HEART, and Wells PE scores without LLM arithmetic drift.
              </p>
            </div>

            <div className="p-6 rounded-2xl border border-slate-200 dark:border-slate-800 bg-card space-y-3">
              <div className="h-10 w-10 rounded-xl bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <h3 className="font-bold text-slate-900 dark:text-slate-100 text-base">Longitudinal Analyte Deltas</h3>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                Tracks cross-visit physiological trends (e.g. SpO₂ 88% → 96% Improved) to catch subtle patient decompensation early.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Subsystem Health Metrics Section */}
      <section className="px-6 py-16 max-w-7xl mx-auto space-y-8">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center border-b pb-4 border-slate-200 dark:border-slate-800">
          <div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-50">Proven Clinical System Telemetry</h2>
            <p className="text-xs text-slate-500 font-medium">Validated against 20 high-fidelity emergency scenario test suites</p>
          </div>
          <div className="mt-4 md:mt-0 flex items-center gap-2 text-xs font-bold text-emerald-600 dark:text-emerald-400">
            <CheckCircle2 className="h-4 w-4" /> 100% Regression Test Pass Rate
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-card">
            <span className="text-3xl font-extrabold text-primary block">13</span>
            <span className="text-xs font-semibold text-slate-500 mt-1 block">Emergency Conditions</span>
          </div>
          <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-card">
            <span className="text-3xl font-extrabold text-primary block">5</span>
            <span className="text-xs font-semibold text-slate-500 mt-1 block">Validated Clinical Scores</span>
          </div>
          <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-card">
            <span className="text-3xl font-extrabold text-primary block">20/20</span>
            <span className="text-xs font-semibold text-slate-500 mt-1 block">Passed Test Scenarios</span>
          </div>
          <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-card">
            <span className="text-3xl font-extrabold text-primary block">&lt;4.5s</span>
            <span className="text-xs font-semibold text-slate-500 mt-1 block">End-to-End Pipeline Latency</span>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 py-8 border-t border-slate-200 dark:border-slate-800 text-center text-xs text-slate-500">
        PRATHAM Medical AI Platform — Created for Clinical Portfolio & Emergency Assistive Technology Research.
      </footer>
    </div>
  );
}
