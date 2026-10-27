"use client";

import { Bot, Network, Cpu, FileWarning, HelpCircle } from "lucide-react";

const AI_MODELS = [
  {
    name: "Imaging AI",
    purpose: "Detects pneumonia and cardiomegaly in Chest X-Rays.",
    model: "EfficientNetB0 (PyTorch)",
    dataset: "NIH Chest X-ray Dataset (Subset)",
    input: "DICOM / JPEG image",
    output: "Disease probability (0-100%) and Grad-CAM heatmap overlay",
    confidence: "Medium-High (85% AUC)",
    limitations: "Poor performance on rotated images. Artifacts can cause false positives.",
    failure: "Fallback to manual doctor interpretation. Confidence suppression in Aggregation."
  },
  {
    name: "Clinical NLP",
    purpose: "Extracts structured medical entities (symptoms, severity) from raw nurse notes.",
    model: "Groq LLM + Llama 3 70B (JSON Schema Mode)",
    dataset: "Zero-shot with Clinical Context Prompting",
    input: "Raw text string",
    output: "Structured JSON (e.g. { chest_pain: true, trauma: false })",
    confidence: "High (92% recall on standard terms)",
    limitations: "Struggles with heavy spelling errors or highly ambiguous acronyms.",
    failure: "Returns empty extraction set; Risk Engine proceeds with baseline vitals only."
  },
  {
    name: "Lab Intelligence (XGBoost)",
    purpose: "Predicts decompensation risk based on multi-analyte panels.",
    model: "XGBoost Classifier + SHAP",
    dataset: "MIMIC-IV (Lab Events)",
    input: "Structured lab results (Troponin, Creatinine, WBC, etc.)",
    output: "Risk Probability + SHAP feature importance",
    confidence: "High",
    limitations: "Requires at least 3 core analytes to generate a confident prediction.",
    failure: "Returns 'Insufficient Data' flag."
  }
];

export default function AIModelCards() {
  return (
    <div className="p-8 max-w-7xl mx-auto min-h-screen">
      <div className="mb-12">
        <h1 className="text-3xl font-bold text-white mb-2 tracking-tight flex items-center gap-3">
          <Bot className="text-indigo-400" />
          AI Model Cards
        </h1>
        <p className="text-zinc-400">Transparency and technical details for all intelligent subsystems in PRATHAM.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {AI_MODELS.map((model, idx) => (
          <div key={idx} className="glass rounded-2xl p-6 border border-white/10 hover:border-indigo-500/30 transition-colors flex flex-col h-full relative overflow-hidden group">
            
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <Network className="w-24 h-24 text-indigo-500" />
            </div>

            <div className="flex items-center gap-3 mb-6 relative z-10">
              <div className="w-10 h-10 rounded-xl bg-indigo-500/20 flex items-center justify-center text-indigo-400">
                <Cpu className="w-5 h-5" />
              </div>
              <h2 className="text-xl font-bold text-white tracking-wide">{model.name}</h2>
            </div>

            <div className="space-y-4 flex-1 relative z-10">
              <div>
                <span className="text-[10px] uppercase font-bold tracking-widest text-zinc-500 block mb-1">Purpose</span>
                <p className="text-sm text-zinc-300 leading-relaxed">{model.purpose}</p>
              </div>

              <div className="grid grid-cols-2 gap-4 bg-white/5 p-3 rounded-xl border border-white/5">
                <div>
                  <span className="text-[10px] uppercase font-bold tracking-widest text-zinc-500 block mb-1">Input</span>
                  <p className="text-xs text-white font-mono bg-black/50 p-1.5 rounded">{model.input}</p>
                </div>
                <div>
                  <span className="text-[10px] uppercase font-bold tracking-widest text-zinc-500 block mb-1">Output</span>
                  <p className="text-xs text-indigo-300 font-mono bg-black/50 p-1.5 rounded">{model.output}</p>
                </div>
              </div>

              <div>
                <span className="text-[10px] uppercase font-bold tracking-widest text-zinc-500 block mb-1">Architecture</span>
                <p className="text-sm text-zinc-300 font-medium">{model.model}</p>
                <p className="text-xs text-zinc-500 mt-0.5">Trained on {model.dataset}</p>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-white/10 space-y-3 relative z-10">
              <div className="flex items-start gap-2 text-sm text-amber-400">
                <HelpCircle className="w-4 h-4 mt-0.5 shrink-0" />
                <span>{model.limitations}</span>
              </div>
              <div className="flex items-start gap-2 text-sm text-red-400">
                <FileWarning className="w-4 h-4 mt-0.5 shrink-0" />
                <span>{model.failure}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
