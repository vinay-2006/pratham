/**
 * PatientTimelineView — Longitudinal Patient History & Comparative Delta UI
 */

import { useEffect, useState } from "react";
import axios from "axios";
import { Clock, TrendingUp, CheckCircle2, AlertCircle, Calendar, ArrowRight, Activity, FileText } from "lucide-react";
import { cn } from "@/lib/utils";

const API_BASE = "http://localhost:8000/api";

interface Delta {
  parameter: string;
  previous_value: string;
  current_value: string;
  status: "IMPROVED" | "DETERIORATED" | "STABLE";
  display_str: string;
}

interface EventItem {
  timestamp: string;
  title: string;
  category: string;
  status: string;
}

interface TimelineProps {
  patientId?: string;
  intakeId?: string;
}

export function PatientTimelineView({ patientId, intakeId }: TimelineProps) {
  const [deltas, setDeltas] = useState<Delta[]>([]);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [trajectory, setTrajectory] = useState<string>("CLINICALLY IMPROVING");

  useEffect(() => {
    // Default comparative demonstration trajectory
    setDeltas([
      { parameter: "SpO₂ Saturation", previous_value: "88%", current_value: "96%", status: "IMPROVED", display_str: "SpO₂: 88% → 96% (Improved)" },
      { parameter: "Respiratory Rate", previous_value: "28/min", current_value: "15/min", status: "IMPROVED", display_str: "Respiratory Rate: 28 → 15/min (Improved)" },
      { parameter: "Heart Rate", previous_value: "118 bpm", current_value: "74 bpm", status: "IMPROVED", display_str: "Heart Rate: 118 → 74 bpm (Improved)" },
      { parameter: "Body Temperature", previous_value: "39.2°C", current_value: "36.7°C", status: "IMPROVED", display_str: "Temperature: 39.2°C → 36.7°C (Improved)" },
    ]);

    setEvents([
      { timestamp: "09:15 AM", title: "Patient Arrived & Emergency Intake Registered", category: "intake", status: "completed" },
      { timestamp: "09:17 AM", title: "Clinical NLP Symptom Extraction Completed", category: "nlp", status: "completed" },
      { timestamp: "09:18 AM", title: "Deterministic Risk Scoring Engine Executed", category: "risk", status: "completed" },
      { timestamp: "09:21 AM", title: "Doctor Approved CBC & Basic Metabolic Panel", category: "approval", status: "completed" },
      { timestamp: "09:30 AM", title: "Laboratory Diagnostic File Uploaded", category: "evidence", status: "completed" },
      { timestamp: "09:32 AM", title: "Demographic Reference Range Evaluation Completed", category: "lab", status: "completed" },
      { timestamp: "09:36 AM", title: "Unified PRATHAM v2.0 Report Generated", category: "report", status: "completed" },
    ]);
  }, [patientId, intakeId]);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Title */}
      <div className="flex items-center justify-between border-b pb-4 border-slate-200 dark:border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-gray-50 flex items-center gap-2">
            <Calendar className="h-6 w-6 text-primary" /> Longitudinal Patient History & Trajectory
          </h1>
          <p className="text-xs text-slate-500 font-medium">Multi-Visit Trajectory, Comparative Deltas & Workflow Event Timeline</p>
        </div>
        <div className="flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-50 dark:bg-emerald-950/40 px-3.5 py-1 text-xs font-bold text-emerald-700 dark:text-emerald-300">
          <TrendingUp className="h-4 w-4" /> Trajectory: {trajectory}
        </div>
      </div>

      {/* Comparative Delta Reporting */}
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-card p-5 shadow-sm">
        <h2 className="text-sm font-bold text-slate-900 dark:text-gray-50 mb-3 flex items-center gap-2">
          <Activity className="h-4 w-4 text-primary" /> Comparative Visit Delta Analysis (Visit 1 vs Current Visit)
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          {deltas.map((d, idx) => (
            <div key={idx} className="rounded-lg border-2 border-emerald-500/30 bg-emerald-500/5 p-3.5">
              <span className="text-xs font-bold text-slate-700 dark:text-gray-300 block">{d.parameter}</span>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xs font-semibold text-slate-500 line-through">{d.previous_value}</span>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400" />
                <span className="text-sm font-bold text-emerald-700 dark:text-emerald-400 tabular-nums">{d.current_value}</span>
              </div>
              <span className="mt-2 inline-block rounded bg-emerald-100 dark:bg-emerald-950/60 px-2 py-0.5 text-[10px] font-bold text-emerald-800 dark:text-emerald-300 uppercase tracking-wider">
                ✓ {d.status}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Clinical Event Log Timeline */}
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-card p-5 shadow-sm">
        <h2 className="text-sm font-bold text-slate-900 dark:text-gray-50 mb-4 flex items-center gap-2">
          <Clock className="h-4 w-4 text-primary" /> Clinical Workflow Event Log
        </h2>
        <div className="relative border-l-2 border-primary/30 pl-6 space-y-4">
          {events.map((ev, i) => (
            <div key={i} className="relative group">
              <div className="absolute -left-[31px] top-1 h-3.5 w-3.5 rounded-full border-2 border-primary bg-background" />
              <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/40 p-3 flex items-center justify-between">
                <div>
                  <p className="text-xs font-bold text-slate-900 dark:text-gray-100">{ev.title}</p>
                  <p className="text-[10px] font-semibold text-slate-500 mt-0.5">Event Stage: {ev.category.toUpperCase()}</p>
                </div>
                <span className="text-[10px] font-mono font-bold text-primary bg-primary/10 px-2 py-1 rounded">
                  {ev.timestamp}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
