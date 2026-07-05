/**
 * PipelineVisualizer — Animated E2E Clinical AI Pipeline Flow
 * Renders the 8 processing steps of the PRATHAM diagnostics loop with step durations.
 */

import { Play, CheckCircle, Hourglass, HelpCircle, Activity } from "lucide-react";

interface Stage {
  name: string;
  duration: string;
  status: "completed" | "running" | "pending";
}

const DEFAULT_STAGES: Stage[] = [
  { name: "Emergency Intake", duration: "120ms", status: "completed" },
  { name: "Clinical NLP Entity Extraction", duration: "1.4s", status: "completed" },
  { name: "NEWS2 / Triage Risk Calculator", duration: "25ms", status: "completed" },
  { name: "Demographic Lab Intelligence", duration: "800ms", status: "completed" },
  { name: "EfficientNetB0 Pneumonia CXR", duration: "1.2s", status: "completed" },
  { name: "Evidence Synthesis & YAML Rules", duration: "500ms", status: "completed" },
  { name: "Clinical Report PDF Generator", duration: "600ms", status: "completed" },
  { name: "Clinical & System Copilot", duration: "900ms", status: "completed" }
];

export function PipelineVisualizer({ stages = DEFAULT_STAGES }: { stages?: Stage[] }) {
  return (
    <div className="p-6 rounded-xl border border-slate-200 dark:border-slate-800 bg-card space-y-6">
      <div className="flex justify-between items-center border-b pb-3 border-slate-100 dark:border-slate-800">
        <div>
          <h3 className="text-sm font-bold flex items-center gap-1.5">
            <Activity className="h-4 w-4 text-primary animate-pulse" /> Live Pipeline Execution Flow
          </h3>
          <p className="text-[10px] text-slate-500">Track runtime and validation status across the 8 layers of PRATHAM.</p>
        </div>
        <span className="text-[10px] font-bold text-slate-400">Total Loop: ~5.5s</span>
      </div>

      <div className="relative pl-6 space-y-4">
        {/* Connected vertical line */}
        <div className="absolute top-2 bottom-2 left-[11px] w-0.5 bg-slate-100 dark:bg-slate-800" />

        {stages.map((stg, idx) => (
          <div key={idx} className="relative flex items-center justify-between gap-4">
            {/* Stage Indicator Node */}
            <div className="absolute -left-6 flex items-center justify-center">
              {stg.status === "completed" ? (
                <div className="h-[24px] w-[24px] rounded-full bg-emerald-500/10 border border-emerald-500 flex items-center justify-center">
                  <CheckCircle className="h-3 w-3 text-emerald-500" />
                </div>
              ) : stg.status === "running" ? (
                <div className="h-[24px] w-[24px] rounded-full bg-amber-500/10 border border-amber-500 flex items-center justify-center animate-spin">
                  <Hourglass className="h-3 w-3 text-amber-500" />
                </div>
              ) : (
                <div className="h-[24px] w-[24px] rounded-full bg-slate-200 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 flex items-center justify-center">
                  <HelpCircle className="h-3 w-3 text-slate-400" />
                </div>
              )}
            </div>

            {/* Content info */}
            <div>
              <h5 className="font-bold text-xs text-slate-800 dark:text-slate-200">{stg.name}</h5>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
                Status: {stg.status}
              </p>
            </div>

            <span className="text-[11px] font-mono font-bold text-slate-500 px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800">
              {stg.duration}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
