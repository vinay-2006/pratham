/**
 * InteractiveArchitectureExplorer — Clickable 7-Layer Clinical AI Pipeline Flow Diagram
 */

import { useState } from "react";
import { Cpu, ArrowRight, Layers, Database, ShieldCheck, FileText, CheckCircle2 } from "lucide-react";

interface PipelineLayer {
  layer_number: number;
  name: string;
  short_desc: string;
  details: string;
  technologies: string[];
}

const PIPELINE_LAYERS: PipelineLayer[] = [
  {
    layer_number: 1,
    name: "Patient Data Ingestion & Clinical Context",
    short_desc: "Demographic normalization, baseline context, and initial intake parsing",
    details: "Adjusts reference ranges based on patient age, sex, pregnancy status, and chronic disease baselines (e.g. CKD baseline creatinine vs acute elevation).",
    technologies: ["FastAPI Intake API", "Pydantic Validation", "Clinical Context Engine"],
  },
  {
    layer_number: 2,
    name: "Demographic Reference Range Engine",
    short_desc: "Context-aware normal range evaluation across lab analytes",
    details: "Transforms raw numerical lab values (e.g. Troponin T = 0.84) into qualitative clinical findings (HIGH / ABNORMAL) with demographic thresholds.",
    technologies: ["Demographic Reference Range Engine", "Analyte Range Mapping"],
  },
  {
    layer_number: 3,
    name: "Generic Laboratory & Imaging Intelligence",
    short_desc: "Analyte-agnostic laboratory evaluator and EfficientNetB0 imaging classifier",
    details: "Evaluates chest radiographs for acute infiltrates/consolidation with high-fidelity confidence scores and processes multi-panel blood work.",
    technologies: ["EfficientNetB0 PyTorch Model", "Lab Analysis Engine", "D-Dimer / Troponin Parsers"],
  },
  {
    layer_number: 4,
    name: "Clinical Pattern & Syndrome Engine",
    short_desc: "Disease-agnostic physiological syndrome synthesis",
    details: "Synthesizes low-level vital & lab anomalies into high-level syndromes: Respiratory Distress, Hemodynamic Instability, Systemic Inflammation, Myocardial Injury, Renal Impairment.",
    technologies: ["Clinical Pattern Engine", "Syndrome Matchers"],
  },
  {
    layer_number: 5,
    name: "Clinical Scoring Engine",
    short_desc: "Standardized emergency clinical risk calculators",
    details: "Calculates validated clinical scores: NEWS2 (National Early Warning Score), qSOFA, CURB-65, HEART Score, and Wells PE criteria with zero missing data hallucination.",
    technologies: ["NEWS2 Calculator", "qSOFA Engine", "Wells PE Criteria", "HEART Score"],
  },
  {
    layer_number: 6,
    name: "Evidence Ranking & Assisted Reasoning Hierarchy",
    short_desc: "Multi-factor support, conflict, and missing evidence scoring across 13 conditions",
    details: "Evaluates 13 emergency condition YAML rules, penalizing unsupported diagnoses while boosting conditions backed by concordant objective findings.",
    technologies: ["Evidence Ranking Engine", "13 YAML Disease Schemas", "Clinical Reasoning Hierarchy"],
  },
  {
    layer_number: 7,
    name: "Grounded Clinical Summary & Audit Log Generator",
    short_desc: "Strict LLM synthesis with explicit clinical audit metadata logging",
    details: "Generates structured clinical summaries with 4-tier recommendation hierarchy (Stat, Urgent, Standard, Safety) and records complete system audit metadata.",
    technologies: ["Groq LLM API", "Clinical Audit Log Service", "Structured Report Engine"],
  },
];

export function InteractiveArchitectureExplorer() {
  const [selectedLayer, setSelectedLayer] = useState<PipelineLayer>(PIPELINE_LAYERS[0]);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between border-b pb-4 border-slate-200 dark:border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-gray-50 flex items-center gap-2">
            <Layers className="h-6 w-6 text-primary" /> Interactive Pipeline Architecture Explorer
          </h1>
          <p className="text-xs text-slate-500 font-medium">Click on any pipeline layer to inspect its clinical responsibilities and internal engine logic</p>
        </div>
      </div>

      {/* Pipeline Visual Flow */}
      <div className="space-y-2">
        <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">7-Layer Clinical Processing Flow</p>
        <div className="grid grid-cols-1 md:grid-cols-7 gap-2">
          {PIPELINE_LAYERS.map((layer) => (
            <button
              key={layer.layer_number}
              onClick={() => setSelectedLayer(layer)}
              className={`p-3 rounded-lg border text-left transition-all ${
                selectedLayer.layer_number === layer.layer_number
                  ? "border-primary bg-primary/10 shadow-md ring-2 ring-primary/40"
                  : "border-slate-200 dark:border-slate-800 bg-card hover:bg-slate-50 dark:hover:bg-slate-800/60"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono font-bold text-xs text-primary">L{layer.layer_number}</span>
                {selectedLayer.layer_number === layer.layer_number && <CheckCircle2 className="h-3.5 w-3.5 text-primary" />}
              </div>
              <p className="font-bold text-slate-900 dark:text-slate-100 text-[11px] mt-1 line-clamp-2 leading-tight">
                {layer.name}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Layer Detail Inspector */}
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-card p-6 shadow-sm space-y-4">
        <div className="flex justify-between items-center border-b pb-3 border-slate-200 dark:border-slate-800">
          <div>
            <span className="text-[10px] font-mono font-bold text-primary px-2 py-0.5 rounded bg-primary/10">
              LAYER {selectedLayer.layer_number} SPECIFICATION
            </span>
            <h2 className="text-xl font-bold text-slate-900 dark:text-slate-50 mt-1">{selectedLayer.name}</h2>
          </div>
        </div>

        <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
          {selectedLayer.short_desc}
        </p>

        <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/40 text-xs text-slate-800 dark:text-slate-200 leading-relaxed">
          <span className="font-bold text-slate-900 dark:text-slate-100 block mb-1">Engine Operational Details:</span>
          {selectedLayer.details}
        </div>

        <div>
          <span className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-2">Underlying Subsystems & Technologies:</span>
          <div className="flex flex-wrap gap-2">
            {selectedLayer.technologies.map((tech, i) => (
              <span key={i} className="px-3 py-1 rounded-md bg-slate-200 dark:bg-slate-800 font-mono text-[11px] font-semibold text-slate-800 dark:text-slate-200">
                {tech}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
