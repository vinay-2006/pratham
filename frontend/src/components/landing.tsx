/**
 * Landing — Premium SaaS Portfolio Homepage Component
 * Houses PRATHAM's marketing layout, interactive dashboards, and developer playground integrations.
 */

import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { 
  ShieldAlert, Sparkles, Code2, Bot, Layers, CheckCircle2, ArrowRight, 
  BookOpen, Github, Terminal, BarChart3, Presentation
} from "lucide-react";

// Import custom showcase components
import { DemoLibrary } from "./demo-library";
import { GuidedTour } from "./guided-tour";
import { RecruiterMode } from "./recruiter-mode";
import { ArchitectureExplorer } from "./architecture-explorer";
import { APIPlayground } from "./api-playground";
import { PlatformDashboard } from "./platform-dashboard";

export default function Landing() {
  const [tourOpen, setTourOpen] = useState(false);
  const [recruiterOpen, setRecruiterOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<"demo" | "explorer" | "api" | "dashboard">("demo");

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-primary selection:text-white">
      {/* Dynamic Guided Tour Overlay */}
      {tourOpen && <GuidedTour onClose={() => setTourOpen(false)} />}

      {/* Recruiter Console Overlay */}
      {recruiterOpen && <RecruiterMode onClose={() => setRecruiterOpen(false)} />}

      {/* ── 1. Top Navbar ── */}
      <header className="sticky top-0 z-40 bg-slate-950/80 backdrop-blur-md border-b border-slate-900 px-6 py-4 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center font-bold text-white shadow-lg shadow-primary/20">
            P
          </div>
          <span className="font-bold text-base tracking-wide bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
            PRATHAM AI
          </span>
        </div>

        <nav className="hidden md:flex items-center gap-6 text-xs font-bold text-slate-400">
          <a href="#problem" className="hover:text-white transition-colors">Problem</a>
          <a href="#features" className="hover:text-white transition-colors">Features</a>
          <a href="#showcase" className="hover:text-white transition-colors">Interactive Demo</a>
          <a href="#architecture" className="hover:text-white transition-colors">Architecture</a>
          <a href="#highlights" className="hover:text-white transition-colors">Engineering</a>
        </nav>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setRecruiterOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 border border-slate-800 text-[11px] font-bold rounded-lg hover:bg-slate-900 transition-colors text-slate-300"
          >
            <Presentation className="h-3.5 w-3.5" /> Recruiter Presentation
          </button>
          <Link
            to="/nurse/dashboard"
            className="flex items-center gap-1 px-4 py-1.5 bg-primary text-white text-[11px] font-bold rounded-lg shadow-lg shadow-primary/10 hover:bg-primary/95 transition-all"
          >
            Launch Workstation <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </header>

      {/* ── 2. Hero Section ── */}
      <section className="relative py-20 px-6 max-w-7xl mx-auto text-center space-y-8 overflow-hidden">
        {/* Subtle decorative glow */}
        <div className="absolute top-20 left-1/2 -translate-x-1/2 w-[500px] h-[300px] bg-primary/10 rounded-full blur-[120px] pointer-events-none" />

        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border border-primary/20 bg-primary/5 text-primary text-[10px] font-bold tracking-wider uppercase relative z-10 animate-bounce">
          <Sparkles className="h-3 w-3" /> Flagship Portfolio Project · v5.0.0 Stable
        </div>

        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight max-w-4xl mx-auto leading-[1.1] relative z-10">
          Transforming Emergency Triage With{" "}
          <span className="bg-gradient-to-r from-primary to-blue-400 bg-clip-text text-transparent">
            Hallucination-Free Clinical AI
          </span>
        </h1>

        <p className="text-sm md:text-base text-slate-400 max-w-2xl mx-auto leading-relaxed relative z-10">
          PRATHAM is an enterprise clinical decision support system utilizing a modular 7-layer design that isolates deterministic scoring algorithms from generative summary engines.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-4 relative z-10 pt-4">
          <button
            onClick={() => setTourOpen(true)}
            className="px-6 py-2.5 bg-primary hover:bg-primary/95 text-white font-bold text-xs rounded-xl shadow-lg shadow-primary/20 transition-all flex items-center gap-1.5"
          >
            <Bot className="h-4 w-4" /> Start Interactive Product Tour
          </button>
          <a
            href="#showcase"
            className="px-6 py-2.5 border border-slate-800 hover:bg-slate-900 text-slate-300 font-bold text-xs rounded-xl transition-all"
          >
            Load Demo Patient Cases
          </a>
        </div>
      </section>

      {/* ── 3. Problem Statement & Solution ── */}
      <section id="problem" className="py-20 px-6 bg-slate-900/30 border-y border-slate-900">
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
          
          <div className="space-y-6">
            <span className="text-[10px] font-bold tracking-wider text-rose-500 uppercase">The Challenge</span>
            <h2 className="text-2xl font-extrabold tracking-tight">The Crisis in Emergency Department Triage</h2>
            <p className="text-xs md:text-sm text-slate-400 leading-relaxed font-medium">
              Triage nurses handle excessive patient inflows under high stress. Traditional clinical calculators (NEWS2, qSOFA) are calculated manually, which is prone to errors, while LLM solutions risk clinical hallucinations when generating diagnostic assessments.
            </p>
            <div className="space-y-3">
              <div className="flex gap-3 text-xs leading-relaxed text-slate-400">
                <ShieldAlert className="h-5 w-5 text-rose-500 flex-shrink-0" />
                <span>** Hallucination Risk**: Pure LLMs hallucinate vital metrics.</span>
              </div>
              <div className="flex gap-3 text-xs leading-relaxed text-slate-400">
                <ShieldAlert className="h-5 w-5 text-rose-500 flex-shrink-0" />
                <span>** Lack of Evidence Tracking**: Decisions lack structured citation audits.</span>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <span className="text-[10px] font-bold tracking-wider text-emerald-500 uppercase">The Solution</span>
            <h2 className="text-2xl font-extrabold tracking-tight">Deterministic-First Medical Diagnostics</h2>
            <p className="text-xs md:text-sm text-slate-400 leading-relaxed font-medium">
              PRATHAM resolves this via modular processing: calculating clinical risk scoring arrays mathematically, synthesizing them against 13 disease specifications, and calling LLM APIs only to format structured patient reports.
            </p>
            <div className="space-y-3">
              <div className="flex gap-3 text-xs leading-relaxed text-slate-400">
                <CheckCircle2 className="h-5 w-5 text-emerald-500 flex-shrink-0" />
                <span>** Halucination-Free**: Isolates clinical logic strictly in python equations.</span>
              </div>
              <div className="flex gap-3 text-xs leading-relaxed text-slate-400">
                <CheckCircle2 className="h-5 w-5 text-emerald-500 flex-shrink-0" />
                <span>** Full Traceability**: Structured evidence rankings match clinical YAML specs.</span>
              </div>
            </div>
          </div>

        </div>
      </section>

      {/* ── 4. Interactive Live Showcase & Sandbox ── */}
      <section id="showcase" className="py-20 px-6 max-w-7xl mx-auto space-y-12">
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-extrabold tracking-tight">Interactive Product Showcase</h2>
          <p className="text-xs text-slate-400 max-w-md mx-auto">Explore live developer playgrounds, system dashboards, and load case libraries directly below.</p>
        </div>

        {/* Tab Selector */}
        <div className="flex justify-center bg-slate-900 border border-slate-800 p-1 rounded-xl max-w-md mx-auto">
          {[
            { id: "demo", label: "Demo Cases", icon: PlayCircleIcon },
            { id: "explorer", label: "Architecture", icon: LayersIcon },
            { id: "api", label: "API Client", icon: TerminalIcon },
            { id: "dashboard", label: "Telemetry", icon: BarChartIcon }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex-1 py-2 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
                activeTab === tab.id ? "bg-primary text-white shadow-md shadow-primary/20" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <tab.icon className="h-4 w-4" /> {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Panel Render */}
        <div className="bg-slate-900/40 border border-slate-900 rounded-3xl overflow-hidden p-2 shadow-2xl">
          {activeTab === "demo" && <DemoLibrary />}
          {activeTab === "explorer" && <ArchitectureExplorer />}
          {activeTab === "api" && <APIPlayground />}
          {activeTab === "dashboard" && <PlatformDashboard />}
        </div>
      </section>

      {/* ── 5. Technical Highlights & Scale ── */}
      <section id="highlights" className="py-20 px-6 bg-slate-900/30 border-t border-slate-900">
        <div className="max-w-6xl mx-auto space-y-12">
          <div className="text-center space-y-2">
            <h2 className="text-2xl font-extrabold tracking-tight">Engineering & Architectural Highlights</h2>
            <p className="text-xs text-slate-400 max-w-md mx-auto">PRATHAM is engineered around core production paradigms.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-xs md:text-sm">
            <div className="p-6 rounded-2xl border border-slate-900 bg-slate-950 space-y-3">
              <h4 className="font-bold text-slate-200 flex items-center gap-2">
                <Code2 className="h-5 w-5 text-primary" /> Memory caching layer
              </h4>
              <p className="text-slate-400 leading-relaxed font-medium">
                To eliminate startup and query lags, PyTorch weights, ML models, and codebase filesystem metrics are loaded once on startup during the FastAPI lifespan hook, reducing diagnostic delays.
              </p>
            </div>
            <div className="p-6 rounded-2xl border border-slate-900 bg-slate-950 space-y-3">
              <h4 className="font-bold text-slate-200 flex items-center gap-2">
                <Terminal className="h-5 w-5 text-primary" /> Parameterized integrity
              </h4>
              <p className="text-slate-400 leading-relaxed font-medium">
                Every data transaction uses Postgres parameterization via the Supabase Client SDK, blocking SQL Injection vectors. Custom FastAPI middleware generates `Request-ID` telemetry trace logs.
              </p>
            </div>
            <div className="p-6 rounded-2xl border border-slate-900 bg-slate-950 space-y-3">
              <h4 className="font-bold text-slate-200 flex items-center gap-2">
                <Layers className="h-5 w-5 text-primary" /> Isolated Demo Resets
              </h4>
              <p className="text-slate-400 leading-relaxed font-medium">
                The database demo reset utilizes safe sequence deletions that preserve database structure, schemas, and configurations. It is isolated behind environment flags to protect production data.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── 6. Footer & Quick Start ── */}
      <footer className="border-t border-slate-900 py-12 px-6 bg-slate-950 text-slate-500 text-xs">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="space-y-2 text-center md:text-left">
            <p className="font-bold text-slate-400 flex items-center gap-1.5 justify-center md:justify-start">
              PRATHAM Medical AI Platform · v5.0.0 Stable
            </p>
            <p className="text-[10px] leading-relaxed">
              Designed as a showcase clinical Decision Support System. Under code-freeze stabilization.
            </p>
          </div>

          <div className="flex flex-wrap gap-4 text-slate-400 font-bold justify-center">
            <Link to="/nurse/dashboard" className="hover:text-white transition-colors">Clinical Queue</Link>
            <a href="https://github.com/vinay-2006/pratham" className="hover:text-white flex items-center gap-1 transition-colors">
              <Github className="h-4 w-4" /> Github Codebase
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}

// Simple Helper Icon wrappers for styling
function PlayCircleIcon(props: any) { return <Bot {...props} />; }
function LayersIcon(props: any) { return <Layers {...props} />; }
function TerminalIcon(props: any) { return <Terminal {...props} />; }
function BarChartIcon(props: any) { return <BarChart3 {...props} />; }
