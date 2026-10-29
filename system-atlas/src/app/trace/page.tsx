"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ActivitySquare, CheckCircle, Database, Server, FileText, BrainCircuit } from "lucide-react";

const STAGES = [
  { id: 1, title: "Patient Arrives", desc: "Nurse starts intake form", icon: ActivitySquare },
  { id: 2, title: "Vitals Entered", desc: "HR: 110, SpO2: 92%, BP: 140/90", icon: ActivitySquare },
  { id: 3, title: "Clinical NLP", desc: "Extracting 'chest pain' & 'sweating'", icon: BrainCircuit },
  { id: 4, title: "Risk Engine", desc: "Calculating NEWS2 and TIMI scores", icon: Server },
  { id: 5, title: "Database Write", desc: "Saving to public.intake & public.risk_scores", icon: Database },
  { id: 6, title: "AI Investigations", desc: "Running ECG and Troponin models", icon: BrainCircuit },
  { id: 7, title: "Aggregation", desc: "Synthesizing AI confidence scores", icon: Server },
  { id: 8, title: "Clinical Report", desc: "LLM grounding and PDF generation", icon: FileText },
];

export default function TracePatient() {
  const [currentStage, setCurrentStage] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (isPlaying && currentStage < STAGES.length) {
      timer = setTimeout(() => {
        setCurrentStage(prev => prev + 1);
      }, 1500); // 1.5 seconds per stage for cinematic effect
    } else if (currentStage >= STAGES.length) {
      setIsPlaying(false);
    }
    return () => clearTimeout(timer);
  }, [isPlaying, currentStage]);

  return (
    <div className="p-8 max-w-5xl mx-auto min-h-screen flex flex-col items-center">
      <div className="mb-12 text-center w-full">
        <h1 className="text-3xl font-bold text-white mb-2 tracking-tight flex items-center justify-center gap-3">
          <ActivitySquare className="text-indigo-400" />
          Trace One Patient
        </h1>
        <p className="text-zinc-400">Cinematic simulation of a single patient flowing through the PRATHAM architecture.</p>
        
        <button 
          onClick={() => { setCurrentStage(0); setIsPlaying(true); }}
          className="mt-8 px-8 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-bold tracking-wide shadow-[0_0_20px_rgba(99,102,241,0.5)] transition-all"
        >
          {currentStage > 0 && currentStage < STAGES.length ? "Restart Simulation" : "Start Simulation"}
        </button>
      </div>

      <div className="relative w-full max-w-2xl mt-8">
        {/* Connection Line */}
        <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-white/10" />
        <motion.div 
          className="absolute left-8 top-0 w-0.5 bg-indigo-500 shadow-[0_0_10px_rgba(99,102,241,1)]"
          initial={{ height: "0%" }}
          animate={{ height: `${(currentStage / STAGES.length) * 100}%` }}
          transition={{ duration: 0.5 }}
        />

        <div className="space-y-12">
          {STAGES.map((stage, idx) => {
            const isActive = currentStage === idx;
            const isPast = currentStage > idx;
            const Icon = stage.icon;

            return (
              <div key={stage.id} className="relative flex items-center gap-8 pl-16">
                {/* Node Point */}
                <div className={`absolute left-5 w-6 h-6 rounded-full border-2 transform -translate-x-1/2 transition-all duration-500 flex items-center justify-center ${
                  isPast ? "bg-indigo-500 border-indigo-400 shadow-[0_0_15px_rgba(99,102,241,0.8)] scale-110" :
                  isActive ? "bg-black border-indigo-400 shadow-[0_0_25px_rgba(99,102,241,1)] scale-125 animate-pulse" :
                  "bg-black border-zinc-700"
                }`}>
                  {isPast && <CheckCircle className="w-3 h-3 text-white" />}
                </div>

                {/* Content Card */}
                <motion.div 
                  initial={{ opacity: 0.3, x: -20 }}
                  animate={{ 
                    opacity: isPast || isActive ? 1 : 0.3, 
                    x: isPast || isActive ? 0 : -20,
                    scale: isActive ? 1.02 : 1
                  }}
                  className={`w-full p-6 rounded-2xl border transition-all duration-500 ${
                    isActive ? "bg-indigo-500/10 border-indigo-500/50 shadow-[0_0_30px_rgba(99,102,241,0.2)]" :
                    isPast ? "glass border-white/10" :
                    "bg-black/20 border-white/5"
                  }`}
                >
                  <div className="flex items-center gap-4">
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                      isActive ? "bg-indigo-500 text-white" : "bg-white/5 text-zinc-500"
                    }`}>
                      <Icon className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className={`text-lg font-bold tracking-tight ${isActive ? "text-indigo-400" : isPast ? "text-white" : "text-zinc-600"}`}>
                        {stage.title}
                      </h3>
                      <p className={`text-sm mt-1 ${isActive ? "text-zinc-300" : isPast ? "text-zinc-400" : "text-zinc-700"}`}>
                        {stage.desc}
                      </p>
                    </div>
                  </div>
                </motion.div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
