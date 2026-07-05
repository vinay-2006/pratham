/**
 * KnowledgeBaseBrowser — Interactive YAML Disease Rule Inspector
 * Displays all 13 Emergency Condition YAML Rules cleanly.
 */

import { useState } from "react";
import { BookOpen, ShieldAlert, CheckCircle2, ChevronRight, FileCode } from "lucide-react";

interface DiseaseRule {
  id: string;
  name: string;
  category: string;
  key_findings: string[];
  score_triggers: string[];
  confidence_weights: Record<string, number>;
  recommendations: string[];
}

const DISEASE_KNOWLEDGE_BASE: DiseaseRule[] = [
  {
    id: "acs",
    name: "Acute Coronary Syndrome (ACS)",
    category: "Cardiac",
    key_findings: ["Retrosternal chest pain", "Troponin elevation >0.04", "ST-segment changes on ECG"],
    score_triggers: ["HEART Score ≥4"],
    confidence_weights: { troponin: 0.40, ecg_st_elevation: 0.35, ischemic_symptoms: 0.25 },
    recommendations: ["Stat ECG within 10 min", "Serial Troponins at 0h, 3h", "Cardiology Consult"],
  },
  {
    id: "heart_failure",
    name: "Acute Decompensated Heart Failure",
    category: "Cardiac",
    key_findings: ["Dyspnea on exertion", "Elevated NT-proBNP >450", "Pulmonary congestion / Kerley B lines"],
    score_triggers: ["Framingham Heart Failure Criteria"],
    confidence_weights: { bnp_elevation: 0.45, pulmonary_edema_xray: 0.35, orthopnea: 0.20 },
    recommendations: ["Echocardiogram", "NT-proBNP Level", "IV Loop Diuretic evaluation"],
  },
  {
    id: "arrhythmia",
    name: "Cardiac Arrhythmia",
    category: "Cardiac",
    key_findings: ["Palpitations / Dizziness", "Irregular pulse", "Hemodynamic instability"],
    score_triggers: ["CHADS2-VASc"],
    confidence_weights: { ecg_rhythm: 0.50, hemodynamic_compromise: 0.30, syncope: 0.20 },
    recommendations: ["Continuous telemetry", "12-Lead ECG", "Electrolyte Panel"],
  },
  {
    id: "pneumonia",
    name: "Community-Acquired Pneumonia",
    category: "Respiratory",
    key_findings: ["Fever / Productive cough", "Focal lung consolidation on CXR", "Leukocytosis WBC >12.0"],
    score_triggers: ["CURB-65 Score ≥2"],
    confidence_weights: { cxr_consolidation: 0.45, fever_wbc: 0.30, crackles: 0.25 },
    recommendations: ["Chest X-Ray", "Sputum Culture", "Empiric Antibiotic Guidance"],
  },
  {
    id: "pe",
    name: "Pulmonary Embolism (PE)",
    category: "Respiratory",
    key_findings: ["Pleuritic chest pain", "Elevated D-Dimer", "Sinus tachycardia"],
    score_triggers: ["Wells PE Score >4.0"],
    confidence_weights: { d_dimer: 0.40, wells_score: 0.35, hypoxemia: 0.25 },
    recommendations: ["CT Pulmonary Angiography (CTPA)", "D-Dimer Assay", "Lower Extremity Ultrasound"],
  },
  {
    id: "asthma",
    name: "Acute Asthma Exacerbation",
    category: "Respiratory",
    key_findings: ["Expiratory wheezing", "Accessory muscle use", "Decreased Peak Flow"],
    score_triggers: ["Severe Asthma Assessment"],
    confidence_weights: { wheezing: 0.40, peak_flow: 0.40, respiratory_rate: 0.20 },
    recommendations: ["Nebulized Bronchodilators", "Peak Flow Measurement", "Blood Gas Analysis"],
  },
  {
    id: "copd",
    name: "COPD Acute Exacerbation",
    category: "Respiratory",
    key_findings: ["Increased sputum volume/purulence", "Hypercapnia", "Bilateral rhonchi"],
    score_triggers: ["DECAF Score"],
    confidence_weights: { purulent_sputum: 0.35, abg_hypercapnia: 0.40, hypoxia: 0.25 },
    recommendations: ["Arterial Blood Gas", "BIPAP Assessment", "Empiric Antibiotics / Steroids"],
  },
  {
    id: "stroke",
    name: "Acute Ischemic Stroke",
    category: "Neurological",
    key_findings: ["Sudden focal neurological deficit", "Facial droop / Arm drift", "Normal non-contrast CT head"],
    score_triggers: ["NIHSS Score"],
    confidence_weights: { nihss_deficit: 0.50, sudden_onset: 0.35, ct_head_negative: 0.15 },
    recommendations: ["STAT Non-contrast Head CT", "Stroke Team Activation", "Thrombolytic Eligibility Window"],
  },
  {
    id: "seizure",
    name: "Acute Seizure / Status Epilepticus",
    category: "Neurological",
    key_findings: ["Tonic-clonic movements", "Post-ictal confusion", "Lactic acidosis"],
    score_triggers: ["Status Epilepticus Timeline (>5 min)"],
    confidence_weights: { convulsive_witness: 0.60, post_ictal: 0.25, serum_lactate: 0.15 },
    recommendations: ["EEG Monitoring", "Antiepileptic Drug Levels", "IV Benzodiazepine Protocol"],
  },
  {
    id: "hemorrhagic_shock",
    name: "Hemorragic / Hypovolemic Shock",
    category: "Vascular",
    key_findings: ["Severe hypotension SBP <90", "Tachycardia HR >120", "Acute Hemoglobin Drop"],
    score_triggers: ["Shock Index >1.0"],
    confidence_weights: { hypotension_tachycardia: 0.45, hgb_drop: 0.35, lactate_elevation: 0.20 },
    recommendations: ["STAT Blood Crossmatch", "Large Bore IV Access", "Rapid Fluid / Transfusion Protocol"],
  },
  {
    id: "dka",
    name: "Diabetic Ketoacidosis (DKA)",
    category: "Metabolic",
    key_findings: ["Hyperglycemia Glucose >250", "Anion Gap Metabolic Acidosis", "Ketonuria / Serum Ketones"],
    score_triggers: ["Anion Gap >12"],
    confidence_weights: { anion_gap_acidosis: 0.45, serum_ketones: 0.35, hyperglycemia: 0.20 },
    recommendations: ["Serum Electrolytes & Anion Gap", "Insulin Infusion Protocol", "Potassium Monitoring"],
  },
  {
    id: "aki",
    name: "Acute Kidney Injury (AKI)",
    category: "Renal",
    key_findings: ["Serum Creatinine >1.5x baseline", "Oliguria <0.5 mL/kg/h", "Hyperkalemia"],
    score_triggers: ["KDIGO AKI Criteria Stage 1-3"],
    confidence_weights: { creatinine_rise: 0.50, urine_output: 0.30, bun_elevation: 0.20 },
    recommendations: ["Renal Ultrasound", "Urine Electrolytes / FeNa", "Nephrotoxic Medication Pause"],
  },
  {
    id: "sepsis",
    name: "Sepsis & Septic Shock",
    category: "Infectious / Systemic",
    key_findings: ["Suspected infection source", "Lactate >2.0 mmol/L", "Hypotension SBP <90"],
    score_triggers: ["qSOFA ≥2", "NEWS2 ≥7"],
    confidence_weights: { lactate_elevation: 0.40, qsofa_score: 0.35, organ_dysfunction: 0.25 },
    recommendations: ["Blood Cultures x2", "STAT IV Antibiotics", "30 mL/kg Crystalloid Bolus"],
  },
];

export function KnowledgeBaseBrowser() {
  const [selectedRule, setSelectedRule] = useState<DiseaseRule>(DISEASE_KNOWLEDGE_BASE[0]);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between border-b pb-4 border-slate-200 dark:border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-gray-50 flex items-center gap-2">
            <BookOpen className="h-6 w-6 text-primary" /> Clinical Knowledge Base Inspector
          </h1>
          <p className="text-xs text-slate-500 font-medium">13 Standardized Emergency Disease YAML Rule Specification & Confidence Weights</p>
        </div>
        <span className="px-3 py-1 rounded-full border border-emerald-500/30 bg-emerald-50 dark:bg-emerald-950/40 text-xs font-bold text-emerald-700 dark:text-emerald-300">
          13 Diseases Operational (v2.0)
        </span>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 md:grid-cols-[300px_1fr] gap-6">
        {/* Sidebar Rule Selection List */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-card p-3 shadow-sm space-y-1 max-h-[600px] overflow-y-auto">
          <p className="px-2 py-1 text-[11px] font-bold uppercase tracking-wider text-slate-400">Select Emergency Condition</p>
          {DISEASE_KNOWLEDGE_BASE.map((rule) => (
            <button
              key={rule.id}
              onClick={() => setSelectedRule(rule)}
              className={`w-full text-left p-2.5 rounded-lg text-xs transition-colors flex items-center justify-between ${
                selectedRule.id === rule.id
                  ? "bg-primary text-primary-foreground font-bold"
                  : "hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium"
              }`}
            >
              <div>
                <span className="block font-semibold">{rule.name}</span>
                <span className={`text-[10px] ${selectedRule.id === rule.id ? "text-primary-foreground/80" : "text-slate-400"}`}>{rule.category}</span>
              </div>
              <ChevronRight className="h-3.5 w-3.5 opacity-60" />
            </button>
          ))}
        </div>

        {/* Detailed YAML Spec Viewer */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-card p-6 shadow-sm space-y-5">
          <div className="flex justify-between items-center border-b pb-3 border-slate-200 dark:border-slate-800">
            <div>
              <span className="text-[10px] font-bold uppercase font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                RULE ID: {selectedRule.id}.yaml
              </span>
              <h2 className="text-xl font-bold text-slate-900 dark:text-slate-50 mt-1">{selectedRule.name}</h2>
            </div>
            <span className="px-2.5 py-1 rounded bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300 text-xs font-semibold">
              Category: {selectedRule.category}
            </span>
          </div>

          {/* Key Findings */}
          <div>
            <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 mb-2 flex items-center gap-1.5">
              <CheckCircle2 className="h-4 w-4 text-emerald-500" /> Key Diagnostic Criteria & Findings
            </h4>
            <ul className="space-y-1.5 text-xs text-slate-600 dark:text-slate-300">
              {selectedRule.key_findings.map((f, i) => (
                <li key={i} className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                  {f}
                </li>
              ))}
            </ul>
          </div>

          {/* Confidence Weights */}
          <div>
            <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 mb-2 flex items-center gap-1.5">
              <FileCode className="h-4 w-4 text-primary" /> Confidence Weight Distribution
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              {Object.entries(selectedRule.confidence_weights).map(([key, val]) => (
                <div key={key} className="p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/40 text-xs">
                  <span className="text-[10px] font-mono text-slate-500 uppercase block">{key}</span>
                  <span className="font-mono font-bold text-slate-900 dark:text-slate-100 text-sm mt-0.5 block">
                    {(val * 100).toFixed(0)}% Weight
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Clinical Recommendations */}
          <div>
            <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 mb-2 flex items-center gap-1.5">
              <ShieldAlert className="h-4 w-4 text-amber-500" /> Standard Next-Step Clinical Investigations
            </h4>
            <div className="flex flex-wrap gap-2">
              {selectedRule.recommendations.map((rec, i) => (
                <span key={i} className="px-3 py-1 rounded-md bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/40 text-amber-800 dark:text-amber-300 text-xs font-medium">
                  {rec}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
