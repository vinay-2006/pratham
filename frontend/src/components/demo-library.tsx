/**
 * DemoLibrary — Portfolio Demonstration Patient Library UI
 * Handles loading 10 curated clinical cases and database reset.
 */

import { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import { Users, RotateCcw, AlertTriangle, ShieldCheck, CheckCircle2, PlayCircle } from "lucide-react";

const API_BASE = "http://localhost:8000/api";

interface DemoCase {
  id: string;
  name: string;
  age: number;
  sex: string;
  chief_complaint: string;
}

export function DemoLibrary({ onCaseLoaded }: { onCaseLoaded?: (intakeId: string) => void }) {
  const [cases, setCases] = useState<DemoCase[]>([]);
  const [loadingCase, setLoadingCase] = useState<string | null>(null);
  const [resetting, setResetting] = useState(false);
  const [demoEnabled, setDemoEnabled] = useState(true);

  useEffect(() => {
    async function fetchCases() {
      try {
        const res = await axios.get(`${API_BASE}/demo/cases`);
        setCases(res.data.cases);
      } catch (err: any) {
        if (err.response?.status === 403) {
          setDemoEnabled(false);
        } else {
          // Fallback static demo list
          setCases([
            { id: "healthy", name: "Healthy Adult Checkup", age: 28, sex: "female", chief_complaint: "Routine health screening." },
            { id: "routine", name: "Routine Checkup Baseline", age: 45, sex: "male", chief_complaint: "Annual physical checkup." },
            { id: "pneumonia", name: "Community Acquired Pneumonia", age: 62, sex: "male", chief_complaint: "Progressive dyspnea, fever, cough." },
            { id: "acs", name: "Acute Coronary Syndrome", age: 58, sex: "male", chief_complaint: "Crushing chest pain radiating to left arm." },
            { id: "stroke", name: "Acute Ischemic Stroke", age: 71, sex: "female", chief_complaint: "Left-sided facial droop and arm drift." },
            { id: "pe", name: "Pulmonary Embolism", age: 42, sex: "female", chief_complaint: "Sudden chest pain, swelling in leg." },
            { id: "sepsis", name: "Sepsis & Septic Shock", age: 69, sex: "male", chief_complaint: " कमजोरी, high fever, low blood pressure." },
            { id: "polytrauma", name: "Polytrauma / Hemorrhagic Shock", age: 31, sex: "male", chief_complaint: "Abdominal pain, fracture, bleeding." },
            { id: "dka", name: "Diabetic Ketoacidosis (DKA)", age: 24, sex: "female", chief_complaint: "Nausea, vomiting, rapid breathing." },
            { id: "heart_failure", name: "Acute Decompensated Heart Failure", age: 75, sex: "female", chief_complaint: "Bilateral ankle swelling and orthopnea." },
          ]);
        }
      }
    }
    fetchCases();
  }, []);

  const handleReset = async () => {
    const confirm = window.confirm("WARNING: This will safely clear all database tables (patient details and intakes). Proceed?");
    if (!confirm) return;

    setResetting(true);
    try {
      await axios.post(`${API_BASE}/demo/reset`);
      toast.success("Database Reset Success", {
        description: "Cleared all records safely without affecting SQL schema schemas.",
      });
    } catch {
      toast.error("Database Reset Failed", {
        description: "Verify ENABLE_DEMO_MODE=true is configured in your backend environment.",
      });
    } finally {
      setResetting(false);
    }
  };

  const handleLoadCase = async (id: string) => {
    setLoadingCase(id);
    try {
      const res = await axios.post(`${API_BASE}/demo/load/${id}`);
      toast.success("Demo Case Loaded", {
        description: `Patient successfully ingested into Supabase database.`,
      });
      if (onCaseLoaded && res.data.intake_id) {
        onCaseLoaded(res.data.intake_id);
      }
    } catch {
      toast.error("Failed to Load Case", {
        description: "Verify ENABLE_DEMO_MODE=true is configured in your backend environment.",
      });
    } finally {
      setLoadingCase(null);
    }
  };

  if (!demoEnabled) {
    return (
      <div className="p-6 rounded-xl border border-slate-200 dark:border-slate-800 bg-card text-center space-y-3">
        <AlertTriangle className="h-8 w-8 text-amber-500 mx-auto" />
        <h3 className="font-bold text-sm">Demo Workspace Locked</h3>
        <p className="text-xs text-slate-500 max-w-md mx-auto">
          To run resets or load test datasets, ensure you set <code className="px-1.5 py-0.5 rounded bg-muted">ENABLE_DEMO_MODE=true</code> in your backend <code className="px-1.5 py-0.5 rounded bg-muted">.env</code> configuration.
        </p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto bg-background text-foreground">
      {/* Top Controls */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center border-b pb-4 border-slate-200 dark:border-slate-800 gap-4">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2">
            <Users className="h-5 w-5 text-primary" /> Showcase Demo Case Library
          </h2>
          <p className="text-xs text-slate-500 font-medium">Reset workspace and load any of the 10 high-fidelity emergency patient profiles in one click.</p>
        </div>
        <button
          onClick={handleReset}
          disabled={resetting}
          className="flex items-center gap-2 px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-rose-600/10 transition-colors"
        >
          <RotateCcw className="h-4 w-4" /> {resetting ? "Purging…" : "Reset Database"}
        </button>
      </div>

      {/* Grid of Cases */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {cases.map((c) => (
          <div
            key={c.id}
            className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-card shadow-sm flex flex-col justify-between space-y-3 hover:border-primary/30 transition-colors"
          >
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-primary px-2 py-0.5 rounded bg-primary/10">
                {c.sex} · {c.age}y
              </span>
              <h4 className="font-bold text-sm text-slate-900 dark:text-slate-50 mt-2">{c.name}</h4>
              <p className="text-xs text-slate-500 line-clamp-3 mt-1 leading-relaxed">{c.chief_complaint}</p>
            </div>
            <button
              onClick={() => handleLoadCase(c.id)}
              disabled={loadingCase !== null}
              className="w-full py-2 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-primary hover:text-white font-bold text-[11px] text-slate-700 dark:text-slate-300 transition-colors flex items-center justify-center gap-1.5"
            >
              <PlayCircle className="h-4 w-4" /> {loadingCase === c.id ? "Loading…" : "Load Case"}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
