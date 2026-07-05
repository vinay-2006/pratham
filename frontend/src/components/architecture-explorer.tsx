/**
 * ArchitectureExplorer — Interactive Platform Subsystem Inspector
 * Provides clinical engineering data sheets (inputs, outputs, runtimes, dependencies) per subsystem.
 */

import { useState } from "react";
import { Layers, Database, ShieldAlert, Cpu, Bot, CheckCircle } from "lucide-react";

interface Subsystem {
  id: string;
  name: string;
  purpose: string;
  inputs: string[];
  outputs: string[];
  runtime: string;
  dependencies: string[];
}

const SUBSYSTEMS: Subsystem[] = [
  {
    id: "nlp",
    name: "Clinical NLP Parser",
    purpose: "Analyze unstructured triage descriptions and extract medical signs, history, and distress metrics.",
    inputs: ["Free-text intake logs", "Chief complaints"],
    outputs: ["Cardiac distress flags", "Neurological risk indicators", "Extracted medical symptoms"],
    runtime: "1.40s",
    dependencies: ["Groq API", "Llama-3-70B model", "Pydantic JSON schema parser"]
  },
  {
    id: "labs",
    name: "Demographic Lab Engine",
    purpose: "Evaluate blood panels relative to patient age, sex, and pregnancy baseline context indicators.",
    inputs: ["Numerical analytes (Troponin, Creatinine, WBC, D-Dimer)", "Demographics"],
    outputs: ["Abnormal flagged markers", "Critical value indicators"],
    runtime: "800ms",
    dependencies: ["Reference Range YAML Matrix", "Demographic Adjuster Service"]
  },
  {
    id: "imaging",
    name: "CXR Medical Imaging Engine",
    purpose: "Run neural network pneumonia inference on Chest X-Rays and generate visual Grad-CAM overlays.",
    inputs: ["Chest Radiograph images (.jpg, .png)"],
    outputs: ["Pneumonia probability scores", "Radiology reports", "Grad-CAM spatial maps"],
    runtime: "1.20s",
    dependencies: ["PyTorch Core", "EfficientNetB0 weights", "Supabase Storage API"]
  },
  {
    id: "scoring",
    name: "Deterministic Scoring Engine",
    purpose: "Calculate mathematical severity classifications (NEWS2, qSOFA, HEART, Wells PE, CURB-65).",
    inputs: ["Vital parameters", "Analytes", "Symptom markers"],
    outputs: ["Score index values", "Risk classification categories"],
    runtime: "< 25ms",
    dependencies: ["Python mathematical operators", "NEWS2 Scoring Matrix"]
  },
  {
    id: "aggregation",
    name: "YAML Pattern Synthesizer",
    purpose: "Perform cross-modal clinical evidence synthesis against emergency disease diagnostic rules.",
    inputs: ["Scoring vectors", "Imaging probabilities", "Vitals data"],
    outputs: ["Support/Conflict matrices", "Missing diagnostics checklists", "Disease ranking vectors"],
    runtime: "500ms",
    dependencies: ["13 Disease YAML rules", "Clinical Pattern Service"]
  },
  {
    id: "report",
    name: "Grounded Summary Engine",
    purpose: "Synthesize findings into clean clinical reports and download auditor-ready PDF files.",
    inputs: ["Disease rankings", "Patient metadata", "Evidence logs"],
    outputs: ["Structured PDF documents", "Auditor summary notes"],
    runtime: "600ms",
    dependencies: ["ReportLab PDF toolkit", "Grounded prompt schema"]
  },
  {
    id: "copilot",
    name: "Evidence-Aware Copilot",
    purpose: "Provide dual-mode Q&A (clinical findings and platform telemetry) with citation tracking.",
    inputs: ["Physician queries", "Patient IDs", "Orchestrator context registry"],
    outputs: ["Answer citations", "Interactive evidence replay nodes", "Safety validations"],
    runtime: "900ms",
    dependencies: ["Copilot registry", "Llama-3-8B context builder"]
  }
];

export function ArchitectureExplorer() {
  const [selectedSubsystem, setSelectedSubsystem] = useState<Subsystem>(SUBSYSTEMS[0]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 max-w-7xl mx-auto bg-background text-foreground p-6">
      {/* Subsystem Node Selector */}
      <div className="lg:col-span-5 space-y-4">
        <div>
          <h3 className="text-base font-bold flex items-center gap-2">
            <Layers className="h-5 w-5 text-primary" /> Interactive Architecture Explorer
          </h3>
          <p className="text-[11px] text-slate-500 mt-0.5">Click any block to inspect its data inputs, runtime, and technical dependencies.</p>
        </div>

        <div className="space-y-2">
          {SUBSYSTEMS.map((sub) => (
            <button
              key={sub.id}
              onClick={() => setSelectedSubsystem(sub)}
              className={`w-full p-4 rounded-xl border text-left transition-all flex items-center justify-between ${
                selectedSubsystem.id === sub.id
                  ? "border-primary bg-primary/5 text-primary shadow-sm"
                  : "border-slate-200 dark:border-slate-800 bg-card hover:border-slate-300 dark:hover:border-slate-700"
              }`}
            >
              <div>
                <h4 className="font-bold text-xs">{sub.name}</h4>
                <p className="text-[10px] text-slate-400 mt-1 line-clamp-1">{sub.purpose}</p>
              </div>
              <span className="text-[9px] font-mono font-bold bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded ml-2">
                {sub.runtime}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Technical Data Sheet Spec Panel */}
      <div className="lg:col-span-7 bg-card border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm flex flex-col justify-between">
        <div className="space-y-6">
          <div className="border-b pb-4 border-slate-100 dark:border-slate-800">
            <span className="text-[9px] font-mono font-bold text-primary bg-primary/10 px-2 py-0.5 rounded uppercase">
              Specification Sheet
            </span>
            <h2 className="text-lg font-bold text-slate-900 dark:text-slate-50 mt-1">
              {selectedSubsystem.name}
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-2 leading-relaxed font-medium">
              {selectedSubsystem.purpose}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <h5 className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Inputs</h5>
              <ul className="space-y-1.5">
                {selectedSubsystem.inputs.map((inp, i) => (
                  <li key={i} className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                    <CheckCircle className="h-3 w-3 text-slate-400 flex-shrink-0" /> {inp}
                  </li>
                ))}
              </ul>
            </div>

            <div className="space-y-2">
              <h5 className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Outputs</h5>
              <ul className="space-y-1.5">
                {selectedSubsystem.outputs.map((out, i) => (
                  <li key={i} className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                    <CheckCircle className="h-3 w-3 text-primary flex-shrink-0" /> {out}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="space-y-2 border-t pt-4 border-slate-100 dark:border-slate-800">
            <h5 className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">System Dependencies</h5>
            <div className="flex flex-wrap gap-1.5">
              {selectedSubsystem.dependencies.map((dep, i) => (
                <span
                  key={i}
                  className="text-[10px] font-bold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-2.5 py-1 rounded-lg border border-slate-200/50 dark:border-slate-800/50"
                >
                  {dep}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="border-t pt-4 border-slate-100 dark:border-slate-800 flex justify-between text-[11px] text-slate-400 font-mono mt-6">
          <span>Latency: {selectedSubsystem.runtime}</span>
          <span>Status: CALIBRATED</span>
        </div>
      </div>
    </div>
  );
}
