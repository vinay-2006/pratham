/**
 * ExplainabilityExplorer — Deep Diagnostic Evidence Tree & Rule Agreement Matrix
 */

import { useEffect, useState } from "react";
import axios from "axios";
import { Brain, Network, GitCommit, CheckCircle2, AlertCircle, HelpCircle } from "lucide-react";

const API_BASE = "http://localhost:8000/api";

interface EvidenceTreeData {
  intake_id: string;
  top_condition: string;
  confidence_pct: number;
  evidence_nodes: Array<{
    category: string;
    finding: string;
    weight: number;
    support_type: "SUPPORTIVE" | "CONFLICTING" | "NEUTRAL";
  }>;
  agreement_matrix: Array<{
    rule_id: string;
    rule_name: string;
    status: "MATCHED" | "NOT_MATCHED" | "MISSING_DATA";
    confidence: number;
  }>;
}

export function ExplainabilityExplorer({ intakeId = "DEMO-INTAKE" }: { intakeId?: string }) {
  const [tree, setTree] = useState<EvidenceTreeData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchTree() {
      try {
        const res = await axios.get(`${API_BASE}/explainability/tree/${intakeId}`);
        setTree(res.data);
      } catch {
        // Fallback mockup
        setTree({
          intake_id: intakeId,
          top_condition: "Acute Coronary Syndrome",
          confidence_pct: 92,
          evidence_nodes: [
            { category: "Symptoms", finding: "Crushing retrosternal chest pain radiating to left arm", weight: +0.35, support_type: "SUPPORTIVE" },
            { category: "Labs", finding: "Troponin T = 0.84 ng/mL (Reference <0.04 - HIGH)", weight: +0.40, support_type: "SUPPORTIVE" },
            { category: "Imaging", finding: "ST-elevation in lead II, III, aVF on 12-lead ECG", weight: +0.25, support_type: "SUPPORTIVE" },
            { category: "Labs", finding: "D-Dimer = 0.22 ug/mL (Normal - rules out PE)", weight: -0.10, support_type: "CONFLICTING" },
          ],
          agreement_matrix: [
            { rule_id: "ACS-01", rule_name: "Ischemic ECG Pattern Match", status: "MATCHED", confidence: 0.95 },
            { rule_id: "ACS-02", rule_name: "Elevated Cardiac Biomarkers", status: "MATCHED", confidence: 0.98 },
            { rule_id: "PE-01", rule_name: "Pulmonary Embolism D-Dimer Rule", status: "NOT_MATCHED", confidence: 0.10 },
            { rule_id: "HF-01", rule_name: "Acute Decompensated Heart Failure NT-proBNP", status: "MISSING_DATA", confidence: 0.0 },
          ],
        });
      } finally {
        setLoading(false);
      }
    }
    fetchTree();
  }, [intakeId]);

  if (loading) {
    return <div className="p-8 text-center text-slate-500 font-medium">Loading Explainability Graph…</div>;
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between border-b pb-4 border-slate-200 dark:border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-gray-50 flex items-center gap-2">
            <Brain className="h-6 w-6 text-primary" /> Explainability & Reasoning Explorer
          </h1>
          <p className="text-xs text-slate-500 font-medium">Diagnostic Evidence Tree, Rule Agreement Matrix, and Provenance Graph</p>
        </div>
        <div className="flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-bold text-primary">
          Top Diagnosis: {tree?.top_condition} ({tree?.confidence_pct}%)
        </div>
      </div>

      {/* Evidence Graph / Nodes */}
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-card p-5 shadow-sm">
        <h2 className="text-sm font-bold text-slate-900 dark:text-gray-50 mb-4 flex items-center gap-2">
          <Network className="h-4 w-4 text-primary" /> Diagnostic Evidence Contribution Tree
        </h2>
        <div className="space-y-3">
          {tree?.evidence_nodes.map((node, i) => (
            <div
              key={i}
              className={`rounded-lg border p-4 text-xs flex items-start justify-between ${
                node.support_type === "SUPPORTIVE"
                  ? "border-emerald-300 dark:border-emerald-900/50 bg-emerald-50/40 dark:bg-emerald-950/20"
                  : "border-rose-300 dark:border-rose-900/50 bg-rose-50/40 dark:bg-rose-950/20"
              }`}
            >
              <div className="space-y-1">
                <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                  {node.category}
                </span>
                <p className="font-semibold text-slate-900 dark:text-slate-100 text-xs mt-1">{node.finding}</p>
              </div>
              <div className="text-right">
                <span className={`font-mono font-bold text-xs ${node.weight > 0 ? "text-emerald-700 dark:text-emerald-400" : "text-rose-700 dark:text-rose-400"}`}>
                  {node.weight > 0 ? `+${node.weight}` : node.weight}
                </span>
                <span className="block text-[10px] text-slate-500 font-semibold uppercase">{node.support_type}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Rule Agreement Matrix */}
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-card p-5 shadow-sm">
        <h2 className="text-sm font-bold text-slate-900 dark:text-gray-50 mb-4 flex items-center gap-2">
          <GitCommit className="h-4 w-4 text-primary" /> Multi-Engine Rule Agreement Matrix
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {tree?.agreement_matrix.map((rule) => (
            <div key={rule.rule_id} className="rounded-lg border border-slate-200 dark:border-slate-800 p-3 bg-slate-50 dark:bg-slate-900/40 flex items-center justify-between text-xs">
              <div>
                <span className="font-mono text-[10px] text-slate-500 font-bold">{rule.rule_id}</span>
                <p className="font-semibold text-slate-800 dark:text-slate-200">{rule.rule_name}</p>
              </div>
              <div>
                {rule.status === "MATCHED" && (
                  <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-bold text-[11px]">
                    <CheckCircle2 className="h-3.5 w-3.5" /> MATCHED
                  </span>
                )}
                {rule.status === "NOT_MATCHED" && (
                  <span className="flex items-center gap-1 text-rose-600 dark:text-rose-400 font-bold text-[11px]">
                    <AlertCircle className="h-3.5 w-3.5" /> UNMATCHED
                  </span>
                )}
                {rule.status === "MISSING_DATA" && (
                  <span className="flex items-center gap-1 text-amber-600 dark:text-amber-400 font-bold text-[11px]">
                    <HelpCircle className="h-3.5 w-3.5" /> NO DATA
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
