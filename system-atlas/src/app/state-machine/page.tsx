"use client";

import { Activity } from "lucide-react";
import { useState } from "react";

const STATES = [
  { name: "Intake Pending", status: "Succeeded" },
  { name: "NLP Running", status: "Succeeded" },
  { name: "Risk Calculated", status: "Succeeded" },
  { name: "Awaiting Approval", status: "Waiting" },
  { name: "Evidence Pending", status: "Waiting" },
  { name: "Lab Running", status: "Running" },
  { name: "Imaging Running", status: "Failed" },
  { name: "Aggregation Running", status: "Pending" },
  { name: "Report Ready", status: "Pending" },
  { name: "Completed", status: "Pending" },
];

export default function StateMachine() {
  const [hoverState, setHoverState] = useState<string | null>(null);

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-12">
        <h1 className="text-3xl font-bold text-white mb-2 tracking-tight flex items-center gap-3">
          <Activity className="text-indigo-400" />
          State Machine
        </h1>
        <p className="text-zinc-400">Enterprise state transitions for the core pipeline.</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {STATES.map((state, idx) => {
          const statusColors = {
            Succeeded: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
            Running: "bg-blue-500/10 text-blue-400 border-blue-500/30 animate-pulse",
            Failed: "bg-red-500/10 text-red-400 border-red-500/30",
            Waiting: "bg-amber-500/10 text-amber-400 border-amber-500/30",
            Pending: "bg-white/5 text-zinc-500 border-white/10"
          }[state.status] || "bg-white/5 text-zinc-500";

          return (
            <div 
              key={idx}
              onMouseEnter={() => setHoverState(state.name)}
              onMouseLeave={() => setHoverState(null)}
              className={`glass rounded-xl p-4 flex flex-col items-center justify-center text-center relative overflow-hidden transition-all duration-300 ${
                hoverState === state.name ? "scale-105 border-indigo-500/50 shadow-[0_0_15px_rgba(99,102,241,0.3)]" : ""
              }`}
            >
              <h3 className="text-sm font-semibold text-white mb-2">{state.name}</h3>
              <span className={`px-2 py-1 rounded text-[10px] uppercase font-bold tracking-wider border ${statusColors}`}>
                {state.status}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  );
}
