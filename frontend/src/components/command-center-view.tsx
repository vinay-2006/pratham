/**
 * CommandCenterView — Emergency Department Command Center Dashboard
 * Provides real-time active ER case tracking, smart triage queue, and operational metrics.
 */

import { useEffect, useState } from "react";
import axios from "axios";
import { Activity, AlertTriangle, Users, Cpu, ShieldAlert, RefreshCw, AlertCircle } from "lucide-react";

import { API_BASE } from "@/lib/api-config";

interface PriorityBoardItem {
  intake_id: string;
  patient_name: string;
  chief_complaint: string;
  severity: string;
  color_code: string;
  priority: number;
  triage_rationale: string;
  arrival_time: string;
}

interface CommandCenterData {
  active_er_cases: number;
  critical_cases: number;
  high_cases: number;
  moderate_cases: number;
  low_cases: number;
  average_pipeline_latency_seconds: number;
  priority_board: PriorityBoardItem[];
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: "text-rose-600 dark:text-rose-400 font-bold",
  high: "text-orange-600 dark:text-orange-400 font-bold",
  moderate: "text-amber-600 dark:text-amber-400 font-semibold",
  low: "text-emerald-600 dark:text-emerald-400 font-semibold",
};

export function CommandCenterView() {
  const [data, setData] = useState<CommandCenterData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTelemetry = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(`${API_BASE}/command-center/telemetry`);
      setData(res.data);
    } catch (err) {
      console.error("[PRATHAM] Command Center telemetry fetch failed:", err);
      setError(
        axios.isAxiosError(err)
          ? err.response?.data?.detail ?? err.message
          : "Failed to load telemetry data."
      );
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTelemetry();
  }, []);

  if (loading) {
    return <div className="p-8 text-center text-slate-500 font-medium">Loading ED Command Center…</div>;
  }

  if (error) {
    return (
      <div className="p-8 max-w-xl mx-auto">
        <div className="rounded-xl border border-rose-300 dark:border-rose-800 bg-rose-50 dark:bg-rose-950/30 p-6 text-center space-y-3">
          <AlertCircle className="h-8 w-8 text-rose-500 mx-auto" />
          <h2 className="text-sm font-bold text-rose-800 dark:text-rose-300">Command Center Unavailable</h2>
          <p className="text-xs text-rose-600 dark:text-rose-400">{error}</p>
          <button
            onClick={fetchTelemetry}
            className="mt-2 inline-flex items-center gap-2 rounded-lg bg-rose-100 dark:bg-rose-900/40 hover:bg-rose-200 dark:hover:bg-rose-800/40 px-4 py-2 text-xs font-semibold text-rose-700 dark:text-rose-300 transition-colors"
          >
            <RefreshCw className="h-3.5 w-3.5" /> Retry
          </button>
        </div>
      </div>
    );
  }

  const summary = data ?? {
    active_er_cases: 0,
    critical_cases: 0,
    high_cases: 0,
    moderate_cases: 0,
    low_cases: 0,
    average_pipeline_latency_seconds: 0,
    priority_board: [],
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Top Banner */}
      <div className="flex items-center justify-between border-b pb-4 border-slate-200 dark:border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-gray-50 flex items-center gap-2">
            <Activity className="h-6 w-6 text-rose-600" /> Emergency Department Command Center
          </h1>
          <p className="text-xs text-slate-500 font-medium">Real-Time ER Operational Monitoring & Smart Triage Prioritization</p>
        </div>
        <button
          onClick={fetchTelemetry}
          className="flex items-center gap-2 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 px-3 py-1.5 text-xs font-semibold text-slate-700 dark:text-slate-200 transition-colors"
        >
          <RefreshCw className="h-3.5 w-3.5" /> Refresh Telemetry
        </button>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-card p-4 shadow-sm">
          <p className="text-xs font-semibold text-slate-500 flex items-center gap-1.5">
            <Users className="h-3.5 w-3.5 text-blue-500" /> Active ER Cases
          </p>
          <p className="text-2xl font-bold text-slate-900 dark:text-gray-50 mt-1">{summary.active_er_cases}</p>
        </div>

        <div className="rounded-xl border border-rose-200 dark:border-rose-900/40 bg-rose-50/50 dark:bg-rose-950/20 p-4 shadow-sm">
          <p className="text-xs font-semibold text-rose-700 dark:text-rose-400 flex items-center gap-1.5">
            <ShieldAlert className="h-3.5 w-3.5 text-rose-600" /> Critical
          </p>
          <p className="text-2xl font-bold text-rose-900 dark:text-rose-200 mt-1">{summary.critical_cases}</p>
        </div>

        <div className="rounded-xl border border-orange-200 dark:border-orange-900/40 bg-orange-50/50 dark:bg-orange-950/20 p-4 shadow-sm">
          <p className="text-xs font-semibold text-orange-700 dark:text-orange-400 flex items-center gap-1.5">
            <AlertTriangle className="h-3.5 w-3.5 text-orange-600" /> High
          </p>
          <p className="text-2xl font-bold text-orange-900 dark:text-orange-200 mt-1">{summary.high_cases}</p>
        </div>

        <div className="rounded-xl border border-amber-200 dark:border-amber-900/40 bg-amber-50/50 dark:bg-amber-950/20 p-4 shadow-sm">
          <p className="text-xs font-semibold text-amber-700 dark:text-amber-400 flex items-center gap-1.5">
            <AlertTriangle className="h-3.5 w-3.5 text-amber-600" /> Moderate
          </p>
          <p className="text-2xl font-bold text-amber-900 dark:text-amber-200 mt-1">{summary.moderate_cases}</p>
        </div>

        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-card p-4 shadow-sm">
          <p className="text-xs font-semibold text-slate-500 flex items-center gap-1.5">
            <Cpu className="h-3.5 w-3.5 text-emerald-500" /> Low Acuity
          </p>
          <p className="text-2xl font-bold text-slate-900 dark:text-gray-50 mt-1">{summary.low_cases}</p>
        </div>
      </div>

      {/* Smart Triage Queue Table */}
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-card p-5 shadow-sm">
        <h2 className="text-sm font-bold text-slate-900 dark:text-gray-50 mb-4 flex items-center gap-2">
          <Users className="h-4 w-4 text-primary" /> Smart Prioritized ER Triage Queue
        </h2>

        {summary.priority_board.length === 0 ? (
          <div className="py-8 text-center text-sm text-slate-400">
            No active ER cases.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-50 dark:bg-slate-800/60 uppercase font-semibold text-slate-600 dark:text-slate-400">
                <tr>
                  <th className="px-4 py-3">Patient Name</th>
                  <th className="px-4 py-3">Chief Complaint</th>
                  <th className="px-4 py-3">Severity</th>
                  <th className="px-4 py-3">Priority</th>
                  <th className="px-4 py-3">Triage Rationale</th>
                  <th className="px-4 py-3">Arrival</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                {summary.priority_board.map((row) => (
                  <tr key={row.intake_id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                    <td className="px-4 py-3 font-bold text-slate-900 dark:text-slate-100">{row.patient_name}</td>
                    <td className="px-4 py-3 text-slate-700 dark:text-slate-300">{row.chief_complaint}</td>
                    <td className={`px-4 py-3 uppercase text-[10px] tracking-wider ${SEVERITY_COLORS[row.severity] || "text-slate-500"}`}>
                      {row.severity}
                    </td>
                    <td className="px-4 py-3 font-mono font-bold text-slate-900 dark:text-slate-100">P{row.priority}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-400 max-w-xs truncate">{row.triage_rationale}</td>
                    <td className="px-4 py-3 font-mono text-slate-500">{row.arrival_time}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
