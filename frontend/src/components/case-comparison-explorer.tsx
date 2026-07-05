/**
 * CaseComparisonExplorer — Side-by-Side Multi-Visit Patient Trajectory Delta Viewer
 */

import { useState } from "react";
import { GitCompare, TrendingUp, TrendingDown, Minus, Clock, FileText } from "lucide-react";

interface VisitRecord {
  visit_id: string;
  timestamp: string;
  chief_complaint: string;
  vitals: {
    hr: number;
    bp: string;
    spo2: number;
    rr: number;
    temp: number;
  };
  labs: {
    troponin: string;
    wbc: string;
    crp: string;
    creatinine: string;
  };
  scores: {
    news2: number;
    qsofa: number;
  };
  primary_diagnosis: string;
}

const DEMO_VISITS: VisitRecord[] = [
  {
    visit_id: "VISIT-001 (Initial Presentation - 48h ago)",
    timestamp: "2026-07-03 08:30",
    chief_complaint: "Progressive dyspnea and persistent cough for 3 days",
    vitals: { hr: 98, bp: "125/80", spo2: 91, rr: 24, temp: 38.4 },
    labs: { troponin: "<0.01 ng/mL", wbc: "14.2 x10^3/uL", crp: "48 mg/L", creatinine: "0.9 mg/dL" },
    scores: { news2: 5, qsofa: 1 },
    primary_diagnosis: "Bacterial Pneumonia (Moderate Risk)",
  },
  {
    visit_id: "VISIT-002 (Current Presentation - Today)",
    timestamp: "2026-07-05 14:15",
    chief_complaint: "Acute onset pleuritic chest pain and severe SOB",
    vitals: { hr: 114, bp: "102/65", spo2: 88, rr: 29, temp: 37.8 },
    labs: { troponin: "0.12 ng/mL", wbc: "16.8 x10^3/uL", crp: "85 mg/L", creatinine: "1.4 mg/dL" },
    scores: { news2: 9, qsofa: 2 },
    primary_diagnosis: "Pneumonia complicated by Pulmonary Embolism & AKI",
  },
];

export function CaseComparisonExplorer() {
  const [visit1] = useState<VisitRecord>(DEMO_VISITS[0]);
  const [visit2] = useState<VisitRecord>(DEMO_VISITS[1]);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between border-b pb-4 border-slate-200 dark:border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-gray-50 flex items-center gap-2">
            <GitCompare className="h-6 w-6 text-primary" /> Multi-Visit Case Comparison Explorer
          </h1>
          <p className="text-xs text-slate-500 font-medium">Side-by-Side Longitudinal Clinical Trajectory & Analyte Delta Engine</p>
        </div>
      </div>

      {/* Main Side-by-Side Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Visit 1 */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-card p-5 shadow-sm space-y-4">
          <div className="flex justify-between items-center border-b pb-3 border-slate-100 dark:border-slate-800">
            <div>
              <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Baseline Visit</span>
              <h3 className="font-bold text-slate-900 dark:text-slate-100 text-sm">{visit1.visit_id}</h3>
            </div>
            <span className="flex items-center gap-1 text-[11px] font-mono text-slate-500">
              <Clock className="h-3 w-3" /> {visit1.timestamp}
            </span>
          </div>

          <div className="text-xs space-y-2">
            <p><span className="font-semibold text-slate-700 dark:text-slate-300">Chief Complaint:</span> {visit1.chief_complaint}</p>
            <p><span className="font-semibold text-slate-700 dark:text-slate-300">Diagnosis:</span> <span className="font-bold text-blue-600 dark:text-blue-400">{visit1.primary_diagnosis}</span></p>
          </div>

          <div className="border-t pt-3 border-slate-100 dark:border-slate-800">
            <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 mb-2">Vitals & Scores</h4>
            <div className="grid grid-cols-2 gap-2 text-xs font-mono">
              <div className="p-2 bg-slate-50 dark:bg-slate-800/40 rounded border border-slate-200 dark:border-slate-700">HR: {visit1.vitals.hr} bpm</div>
              <div className="p-2 bg-slate-50 dark:bg-slate-800/40 rounded border border-slate-200 dark:border-slate-700">BP: {visit1.vitals.bp}</div>
              <div className="p-2 bg-slate-50 dark:bg-slate-800/40 rounded border border-slate-200 dark:border-slate-700">SpO₂: {visit1.vitals.spo2}%</div>
              <div className="p-2 bg-slate-50 dark:bg-slate-800/40 rounded border border-slate-200 dark:border-slate-700">NEWS2: {visit1.scores.news2}</div>
            </div>
          </div>
        </div>

        {/* Visit 2 */}
        <div className="rounded-xl border border-rose-200 dark:border-rose-900/40 bg-rose-50/20 dark:bg-rose-950/10 p-5 shadow-sm space-y-4">
          <div className="flex justify-between items-center border-b pb-3 border-rose-200 dark:border-rose-900/40">
            <div>
              <span className="text-[10px] uppercase font-bold tracking-wider text-rose-600">Current Presentation</span>
              <h3 className="font-bold text-slate-900 dark:text-slate-100 text-sm">{visit2.visit_id}</h3>
            </div>
            <span className="flex items-center gap-1 text-[11px] font-mono text-slate-500">
              <Clock className="h-3 w-3" /> {visit2.timestamp}
            </span>
          </div>

          <div className="text-xs space-y-2">
            <p><span className="font-semibold text-slate-700 dark:text-slate-300">Chief Complaint:</span> {visit2.chief_complaint}</p>
            <p><span className="font-semibold text-slate-700 dark:text-slate-300">Diagnosis:</span> <span className="font-bold text-rose-600 dark:text-rose-400">{visit2.primary_diagnosis}</span></p>
          </div>

          <div className="border-t pt-3 border-rose-200 dark:border-rose-900/40">
            <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 mb-2">Vitals & Scores</h4>
            <div className="grid grid-cols-2 gap-2 text-xs font-mono">
              <div className="p-2 bg-rose-100/50 dark:bg-rose-950/40 rounded border border-rose-300 dark:border-rose-800 font-bold text-rose-700 dark:text-rose-300">HR: {visit2.vitals.hr} bpm (+16)</div>
              <div className="p-2 bg-rose-100/50 dark:bg-rose-950/40 rounded border border-rose-300 dark:border-rose-800 font-bold text-rose-700 dark:text-rose-300">BP: {visit2.vitals.bp} (Hypotensive)</div>
              <div className="p-2 bg-rose-100/50 dark:bg-rose-950/40 rounded border border-rose-300 dark:border-rose-800 font-bold text-rose-700 dark:text-rose-300">SpO₂: {visit2.vitals.spo2}% (-3%)</div>
              <div className="p-2 bg-rose-100/50 dark:bg-rose-950/40 rounded border border-rose-300 dark:border-rose-800 font-bold text-rose-700 dark:text-rose-300">NEWS2: {visit2.scores.news2} (+4 CRITICAL)</div>
            </div>
          </div>
        </div>
      </div>

      {/* Delta Analysis Section */}
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-card p-5 shadow-sm">
        <h2 className="text-sm font-bold text-slate-900 dark:text-gray-50 mb-3 flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-rose-500" /> Key Clinical Deltas & Decompensation Indicators
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
          <div className="p-3 rounded-lg border border-rose-200 dark:border-rose-900/50 bg-rose-50/50 dark:bg-rose-950/20">
            <span className="font-semibold text-rose-800 dark:text-rose-300 block">Troponin Delta</span>
            <span className="text-sm font-bold font-mono text-rose-900 dark:text-rose-100 mt-1 block">&lt;0.01 → 0.12 ng/mL</span>
            <span className="text-[10px] text-rose-700 dark:text-rose-400 mt-1 block">New elevation indicating myocardial stress or injury.</span>
          </div>

          <div className="p-3 rounded-lg border border-amber-200 dark:border-amber-900/50 bg-amber-50/50 dark:bg-amber-950/20">
            <span className="font-semibold text-amber-800 dark:text-amber-300 block">Creatinine Delta</span>
            <span className="text-sm font-bold font-mono text-amber-900 dark:text-amber-100 mt-1 block">0.9 → 1.4 mg/dL</span>
            <span className="text-[10px] text-amber-700 dark:text-amber-400 mt-1 block">55% increase indicating Stage 1 Acute Kidney Injury.</span>
          </div>

          <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/40">
            <span className="font-semibold text-slate-700 dark:text-slate-300 block">WBC Count Delta</span>
            <span className="text-sm font-bold font-mono text-slate-900 dark:text-slate-100 mt-1 block">14.2 → 16.8 x10^3/uL</span>
            <span className="text-[10px] text-slate-500 dark:text-slate-400 mt-1 block">Worsening leukocytosis consistent with systemic inflammation.</span>
          </div>
        </div>
      </div>
    </div>
  );
}
