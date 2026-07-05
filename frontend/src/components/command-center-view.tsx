/**
 * CommandCenterView — Emergency Department Command Center Dashboard
 * Provides real-time active ER case tracking, smart triage queue, and operational resource recommendations.
 */

import { useEffect, useState } from "react";
import axios from "axios";
import { Activity, AlertTriangle, Users, Cpu, ShieldAlert, CheckCircle2, RefreshCw } from "lucide-react";

const API_BASE = "http://localhost:8000/api";

interface CommandCenterData {
  summary: {
    active_er_cases: number;
    high_acuity_cases: number;
    moderate_acuity_cases: number;
    low_acuity_cases: number;
    average_wait_time_minutes: number;
    triage_alert_count: number;
  };
  smart_triage_queue: Array<{
    patient_id: string;
    intake_id: string;
    chief_complaint: string;
    vitals: Record<string, any>;
    triage_score: number;
    recommended_acuity: string;
    primary_condition: string;
  }>;
  operational_recommendations: Array<{
    patient_id: string;
    recommended_unit: string;
    specialist_consult: string;
    priority_level: string;
    equipment_needed: string[];
    rationale: string;
  }>;
}

export function CommandCenterView() {
  const [data, setData] = useState<CommandCenterData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchTelemetry = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/command-center/telemetry`);
      setData(res.data);
    } catch {
      // Demo fallback data if server unavailable
      setData({
        summary: {
          active_er_cases: 14,
          high_acuity_cases: 3,
          moderate_acuity_cases: 7,
          low_acuity_cases: 4,
          average_wait_time_minutes: 18,
          triage_alert_count: 2,
        },
        smart_triage_queue: [
          {
            patient_id: "P-101",
            intake_id: "INT-801",
            chief_complaint: "Severe crushing chest pain radiating to jaw",
            vitals: { hr: 112, bp: "90/60", spo2: 91 },
            triage_score: 9.2,
            recommended_acuity: "HIGH (Level 1)",
            primary_condition: "Acute Coronary Syndrome",
          },
          {
            patient_id: "P-104",
            intake_id: "INT-804",
            chief_complaint: "High fever, altered mental status, tachypnea",
            vitals: { hr: 124, temp: 39.1, rr: 28, bp: "88/54" },
            triage_score: 8.8,
            recommended_acuity: "HIGH (Level 1)",
            primary_condition: "Sepsis",
          },
        ],
        operational_recommendations: [
          {
            patient_id: "P-101",
            recommended_unit: "Cardiac Cath Lab / Cardiac ICU",
            specialist_consult: "Cardiology Fellow / Attending",
            priority_level: "IMMEDIATE (STAT)",
            equipment_needed: ["12-Lead ECG", "Continuous Cardiac Monitor", "Intravenous Access Lines"],
            rationale: "High suspicion for acute myocardial ischemia requiring urgent invasive evaluation.",
          },
        ],
      });
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

  const summary = data?.summary || {
    active_er_cases: 0,
    high_acuity_cases: 0,
    moderate_acuity_cases: 0,
    low_acuity_cases: 0,
    average_wait_time_minutes: 0,
    triage_alert_count: 0,
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
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-card p-4 shadow-sm">
          <p className="text-xs font-semibold text-slate-500 flex items-center gap-1.5">
            <Users className="h-3.5 w-3.5 text-blue-500" /> Active ER Cases
          </p>
          <p className="text-2xl font-bold text-slate-900 dark:text-gray-50 mt-1">{summary.active_er_cases}</p>
        </div>

        <div className="rounded-xl border border-rose-200 dark:border-rose-900/40 bg-rose-50/50 dark:bg-rose-950/20 p-4 shadow-sm">
          <p className="text-xs font-semibold text-rose-700 dark:text-rose-400 flex items-center gap-1.5">
            <ShieldAlert className="h-3.5 w-3.5 text-rose-600" /> High Acuity (Level 1)
          </p>
          <p className="text-2xl font-bold text-rose-900 dark:text-rose-200 mt-1">{summary.high_acuity_cases}</p>
        </div>

        <div className="rounded-xl border border-amber-200 dark:border-amber-900/40 bg-amber-50/50 dark:bg-amber-950/20 p-4 shadow-sm">
          <p className="text-xs font-semibold text-amber-700 dark:text-amber-400 flex items-center gap-1.5">
            <AlertTriangle className="h-3.5 w-3.5 text-amber-600" /> Moderate Acuity
          </p>
          <p className="text-2xl font-bold text-amber-900 dark:text-amber-200 mt-1">{summary.moderate_acuity_cases}</p>
        </div>

        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-card p-4 shadow-sm">
          <p className="text-xs font-semibold text-slate-500 flex items-center gap-1.5">
            <Cpu className="h-3.5 w-3.5 text-emerald-500" /> Triage Alerts
          </p>
          <p className="text-2xl font-bold text-slate-900 dark:text-gray-50 mt-1">{summary.triage_alert_count}</p>
        </div>
      </div>

      {/* Smart Triage Queue Table */}
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-card p-5 shadow-sm">
        <h2 className="text-sm font-bold text-slate-900 dark:text-gray-50 mb-4 flex items-center gap-2">
          <Users className="h-4 w-4 text-primary" /> Smart Prioritized ER Triage Queue
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-50 dark:bg-slate-800/60 uppercase font-semibold text-slate-600 dark:text-slate-400">
              <tr>
                <th className="px-4 py-3">Patient ID</th>
                <th className="px-4 py-3">Chief Complaint</th>
                <th className="px-4 py-3">Triage Acuity</th>
                <th className="px-4 py-3">Risk Score</th>
                <th className="px-4 py-3">Primary Differential</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
              {data?.smart_triage_queue.map((row) => (
                <tr key={row.intake_id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                  <td className="px-4 py-3 font-mono font-bold text-slate-900 dark:text-slate-100">{row.patient_id}</td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-300">{row.chief_complaint}</td>
                  <td className="px-4 py-3 font-semibold text-rose-600 dark:text-rose-400">{row.recommended_acuity}</td>
                  <td className="px-4 py-3 font-mono font-bold text-slate-900 dark:text-slate-100">{row.triage_score} / 10</td>
                  <td className="px-4 py-3 text-slate-800 dark:text-slate-200 font-medium">{row.primary_condition}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Operational Resource Recommendations */}
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-card p-5 shadow-sm">
        <h2 className="text-sm font-bold text-slate-900 dark:text-gray-50 mb-3 flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-emerald-500" /> Operational Equipment & Specialist Unit Recommendations
        </h2>
        <div className="space-y-4">
          {data?.operational_recommendations.map((rec, i) => (
            <div key={i} className="rounded-lg border border-slate-200 dark:border-slate-800 p-4 bg-slate-50/50 dark:bg-slate-900/40 space-y-2 text-xs">
              <div className="flex justify-between items-center">
                <span className="font-bold font-mono text-slate-900 dark:text-slate-100 text-sm">Patient: {rec.patient_id}</span>
                <span className="px-2 py-0.5 rounded bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300 font-bold">{rec.priority_level}</span>
              </div>
              <p className="text-slate-700 dark:text-slate-300"><span className="font-semibold text-slate-900 dark:text-slate-100">Recommended Unit:</span> {rec.recommended_unit}</p>
              <p className="text-slate-700 dark:text-slate-300"><span className="font-semibold text-slate-900 dark:text-slate-100">Specialist Consult:</span> {rec.specialist_consult}</p>
              <div>
                <span className="font-semibold text-slate-900 dark:text-slate-100">Equipment Needed:</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {rec.equipment_needed.map((eq, j) => (
                    <span key={j} className="px-2 py-0.5 bg-slate-200 dark:bg-slate-800 rounded font-mono text-[11px] text-slate-800 dark:text-slate-200">
                      {eq}
                    </span>
                  ))}
                </div>
              </div>
              <p className="text-slate-500 dark:text-slate-400 italic text-[11px] mt-1">{rec.rationale}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
