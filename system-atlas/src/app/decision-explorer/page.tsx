"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { GitCommitHorizontal, ChevronDown, ChevronUp, Plus, Minus } from "lucide-react";

const DECISIONS = [
  {
    syndrome: "Acute Coronary Syndrome (ACS)",
    probability: "72%",
    status: "High Risk",
    factors: [
      { name: "Chest pain (Clinical NLP)", weight: "+14", type: "positive" },
      { name: "Troponin > 0.04 (Lab AI)", weight: "+18", type: "positive" },
      { name: "HR > 100 (Vitals)", weight: "+9", type: "positive" },
      { name: "Age > 65 (Demographics)", weight: "+11", type: "positive" },
      { name: "ECG ST-Elevation (Imaging AI)", weight: "-8", type: "negative", reason: "Model reported normal sinus rhythm" },
    ]
  },
  {
    syndrome: "Pulmonary Embolism (PE)",
    probability: "45%",
    status: "Moderate Risk",
    factors: [
      { name: "D-Dimer > 500 (Lab AI)", weight: "+22", type: "positive" },
      { name: "Breathlessness (Clinical NLP)", weight: "+12", type: "positive" },
      { name: "Wells Score Low (Clinical Scoring)", weight: "-15", type: "negative" },
    ]
  }
];

export default function DecisionExplorer() {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(0);

  return (
    <div className="p-8 max-w-4xl mx-auto min-h-screen">
      <div className="mb-12">
        <h1 className="text-3xl font-bold text-white mb-2 tracking-tight flex items-center gap-3">
          <GitCommitHorizontal className="text-indigo-400" />
          Decision Explorer
        </h1>
        <p className="text-zinc-400">Deep dive into the Aggregation Engine's reasoning, weights, and confidence matrices.</p>
      </div>

      <div className="space-y-6">
        {DECISIONS.map((decision, idx) => (
          <div key={idx} className="glass rounded-2xl overflow-hidden border border-white/10 transition-all hover:border-indigo-500/30">
            <button 
              onClick={() => setExpandedIndex(expandedIndex === idx ? null : idx)}
              className="w-full flex items-center justify-between p-6 bg-black/40 hover:bg-white/5 transition-colors"
            >
              <div className="flex items-center gap-6">
                <div className={`w-16 h-16 rounded-full flex items-center justify-center border-4 ${
                  decision.status === "High Risk" ? "border-red-500/20 text-red-400" : "border-amber-500/20 text-amber-400"
                }`}>
                  <span className="font-bold text-xl">{decision.probability}</span>
                </div>
                <div className="text-left">
                  <h2 className="text-xl font-bold text-white tracking-wide">{decision.syndrome}</h2>
                  <p className="text-sm text-zinc-400 mt-1">Aggregation Engine Conclusion</p>
                </div>
              </div>
              {expandedIndex === idx ? <ChevronUp className="text-zinc-400" /> : <ChevronDown className="text-zinc-400" />}
            </button>

            <AnimatePresence>
              {expandedIndex === idx && (
                <motion.div 
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="border-t border-white/5 bg-black/60"
                >
                  <div className="p-6 space-y-3">
                    <h3 className="text-xs uppercase tracking-wider text-zinc-500 font-bold mb-4">Evidence Weights</h3>
                    {decision.factors.map((factor, fIdx) => (
                      <div key={fIdx} className="flex items-center justify-between p-3 rounded-xl bg-white/5">
                        <div className="flex items-center gap-3">
                          <div className={`w-6 h-6 rounded-md flex items-center justify-center ${
                            factor.type === "positive" ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"
                          }`}>
                            {factor.type === "positive" ? <Plus className="w-4 h-4" /> : <Minus className="w-4 h-4" />}
                          </div>
                          <div>
                            <span className="text-white text-sm font-medium">{factor.name}</span>
                            {factor.reason && <p className="text-xs text-zinc-500 mt-0.5">{factor.reason}</p>}
                          </div>
                        </div>
                        <span className={`font-bold font-mono ${
                          factor.type === "positive" ? "text-emerald-400" : "text-red-400"
                        }`}>{factor.weight}</span>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        ))}
      </div>
    </div>
  );
}
