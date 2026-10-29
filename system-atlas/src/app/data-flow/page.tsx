"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Route, HeartPulse, Stethoscope, Droplets, Image as ImageIcon } from "lucide-react";

const DATA_TRACES = [
  { id: "spo2", name: "SpO₂ (Blood Oxygen)", icon: HeartPulse, steps: ["Nurse Form", "FastAPI /intake", "Supabase vitals", "Risk Engine", "Aggregation", "Clinical PDF"] },
  { id: "troponin", name: "Troponin", icon: Droplets, steps: ["HL7 Lab Upload", "Lab Parser Service", "XGBoost Lab AI", "Aggregation", "Copilot Context"] },
  { id: "cxr", name: "Chest X-Ray", icon: ImageIcon, steps: ["DICOM Upload", "EfficientNetB0", "Grad-CAM Gen", "Supabase Storage", "Aggregation", "Doctor Review UI"] },
  { id: "symptoms", name: "Symptoms Text", icon: Stethoscope, steps: ["Nurse Intake", "Clinical NLP (Groq)", "Extracted Entities DB", "Rule Agreement Matrix", "Report Generator"] },
];

export default function DataFlowExplorer() {
  const [activeTrace, setActiveTrace] = useState(DATA_TRACES[0]);

  return (
    <div className="p-8 max-w-7xl mx-auto min-h-screen">
      <div className="mb-12">
        <h1 className="text-3xl font-bold text-white mb-2 tracking-tight flex items-center gap-3">
          <Route className="text-indigo-400" />
          Data Flow Explorer
        </h1>
        <p className="text-zinc-400">Trace the exact transformation of clinical variables through the PRATHAM pipeline.</p>
      </div>

      <div className="flex gap-4 mb-16">
        {DATA_TRACES.map(trace => {
          const Icon = trace.icon;
          const isActive = activeTrace.id === trace.id;
          return (
            <button
              key={trace.id}
              onClick={() => setActiveTrace(trace)}
              className={`flex items-center gap-2 px-4 py-3 rounded-xl font-medium transition-all duration-300 ${
                isActive ? "bg-indigo-500 text-white shadow-[0_0_20px_rgba(99,102,241,0.4)]" : "glass text-zinc-400 hover:text-white"
              }`}
            >
              <Icon className="w-4 h-4" />
              {trace.name}
            </button>
          )
        })}
      </div>

      <div className="relative mt-24">
        <div className="absolute top-1/2 left-0 w-full h-1 bg-white/10 -translate-y-1/2 rounded-full overflow-hidden">
          <motion.div 
            className="h-full bg-gradient-to-r from-indigo-500 to-purple-500"
            initial={{ width: "0%" }}
            animate={{ width: "100%" }}
            transition={{ duration: 2, ease: "easeInOut" }}
            key={activeTrace.id}
          />
        </div>

        <div className="relative flex justify-between w-full">
          <AnimatePresence mode="popLayout">
            {activeTrace.steps.map((step, idx) => (
              <motion.div
                key={`${activeTrace.id}-${step}`}
                initial={{ opacity: 0, y: 20, scale: 0.8 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.4, delay: idx * 0.3 }}
                className="flex flex-col items-center group relative z-10"
              >
                <div className="w-12 h-12 rounded-full bg-black border-2 border-indigo-500 shadow-[0_0_15px_rgba(99,102,241,0.5)] flex items-center justify-center text-white mb-4 z-10">
                  {idx + 1}
                </div>
                <div className="absolute top-16 w-32 text-center">
                  <span className="text-sm font-semibold text-white tracking-wide">{step}</span>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
