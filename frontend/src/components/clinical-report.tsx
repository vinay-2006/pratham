/**
 * ClinicalReport — 12-Section Clinician-First Diagnostic Summary
 *
 * Renders the clinical report in a structured medical layout.
 * Strictly avoids engineering jargon in clinical sections (1-11).
 * Moves developer diagnostics to Section 12 (Technical Appendix).
 */

import { useState } from "react";
import { cn } from "@/lib/utils";
import type { ClinicalReport as ClinicalReportData, StageStatus } from "@/lib/report-api";
import { PipelineStatus } from "./pipeline-status";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ClipboardList,
  Clock,
  FlaskConical,
  Heart,
  Info,
  ListChecks,
  MonitorCheck,
  Search,
  ShieldAlert,
  ShieldCheck,
  Stethoscope,
  TrendingUp,
  Wind,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Props {
  report: ClinicalReportData;
  reportRef?: React.RefObject<HTMLDivElement | null>;
  pipelineStages?: {
    nlp: StageStatus;
    risk: StageStatus;
    lab: StageStatus;
    imaging: StageStatus;
    aggregation: StageStatus;
  };
  isPolling?: boolean;
}

// ── Minimal monochrome section wrapper ──────────────────────────────────────

function Section({
  title,
  icon: Icon,
  sectionNumber,
  children,
}: {
  title: string;
  icon: typeof Stethoscope;
  sectionNumber: number;
  children: React.ReactNode;
}) {
  return (
    <Card className="border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 shadow-sm overflow-hidden rounded-xl">
      <CardHeader className="pb-3 border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/40">
        <CardTitle className="flex items-center gap-3 text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider">
          <span className="flex items-center justify-center h-5 w-5 rounded-full bg-slate-200 dark:bg-slate-800 text-[10px] font-black text-slate-700 dark:text-slate-350 shrink-0">
            {sectionNumber}
          </span>
          <Icon className="h-4 w-4 text-slate-500 shrink-0" />
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-4 text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
        {children}
      </CardContent>
    </Card>
  );
}

// ── Main Component ──────────────────────────────────────────────────────────

export function ClinicalReport({ report, reportRef, pipelineStages, isPolling }: Props) {
  // If backend clinician_report is missing, show a loading placeholder
  const clin = (report as any).clinician_report;
  if (!clin) {
    return (
      <div className="p-8 text-center text-slate-400 text-xs italic">
        Awaiting clinician report assembly…
      </div>
    );
  }

  const snap = clin.patient_snapshot;
  const pc = clin.presenting_complaint;
  const vitals = clin.vitals_list;

  // Required-field visibility — log when expected backend fields are absent
  if (!snap) console.error("[PRATHAM] ClinicalReport: missing required field clin.patient_snapshot");
  if (!pc) console.error("[PRATHAM] ClinicalReport: missing required field clin.presenting_complaint");
  if (!vitals) console.error("[PRATHAM] ClinicalReport: missing required field clin.vitals_list");
  if (!clin.timeline) console.error("[PRATHAM] ClinicalReport: missing required field clin.timeline");
  if (!clin.investigations_matrix) console.error("[PRATHAM] ClinicalReport: missing required field clin.investigations_matrix");
  if (!clin.differential_diagnosis) console.error("[PRATHAM] ClinicalReport: missing required field clin.differential_diagnosis");
  if (!clin.recommendations) console.error("[PRATHAM] ClinicalReport: missing required field clin.recommendations");
  if (!clin.evidence_quality) console.error("[PRATHAM] ClinicalReport: missing required field clin.evidence_quality");
  if (snap && !snap.priority) console.error("[PRATHAM] ClinicalReport: missing required field snap.priority");

  return (
    <div ref={reportRef} className="space-y-6">
      {/* ── Section 1: Patient Snapshot Cover Sheet ────────────────────────── */}
      <Section title="Patient Snapshot Cover Sheet" icon={ClipboardList} sectionNumber={1}>
        <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-4">
          <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/30">
            <span className="text-[10px] text-slate-400 dark:text-slate-500 block font-bold uppercase mb-0.5">Case ID</span>
            <span className="font-mono font-bold text-slate-800 dark:text-slate-200">{snap.case_id}</span>
          </div>
          <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/30">
            <span className="text-[10px] text-slate-400 dark:text-slate-500 block font-bold uppercase mb-0.5">Patient Name</span>
            <span className="font-bold text-slate-800 dark:text-slate-200">{snap.patient_name}</span>
          </div>
          <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/30">
            <span className="text-[10px] text-slate-400 dark:text-slate-500 block font-bold uppercase mb-0.5">Age / Gender</span>
            <span className="font-bold text-slate-800 dark:text-slate-200">{snap.age} / {snap.gender}</span>
          </div>
          <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/30">
            <span className="text-[10px] text-slate-400 dark:text-slate-500 block font-bold uppercase mb-0.5">Arrival Type</span>
            <span className="font-bold text-slate-800 dark:text-slate-200">{snap.arrival_type}</span>
          </div>
          <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/30">
            <span className="text-[10px] text-slate-400 dark:text-slate-500 block font-bold uppercase mb-0.5">Clinical Priority</span>
            <span className={cn(
              "font-bold uppercase",
              snap?.priority?.toUpperCase() === "CRITICAL" ? "text-rose-600" :
              snap?.priority?.toUpperCase() === "HIGH PRIORITY" ? "text-orange-500" :
              "text-slate-700 dark:text-slate-355"
            )}>{snap?.priority || "Unknown"}</span>
          </div>
          <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/30">
            <span className="text-[10px] text-slate-400 dark:text-slate-500 block font-bold uppercase mb-0.5">Report Version</span>
            <span className="font-bold text-slate-800 dark:text-slate-200">{snap.report_version}</span>
          </div>
          <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/30">
            <span className="text-[10px] text-slate-400 dark:text-slate-500 block font-bold uppercase mb-0.5">Tests Completed</span>
            <span className="font-bold text-slate-800 dark:text-slate-200">{snap.completed_tests}</span>
          </div>
          <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/30">
            <span className="text-[10px] text-slate-400 dark:text-slate-500 block font-bold uppercase mb-0.5">Generated</span>
            <span className="font-bold text-slate-800 dark:text-slate-200 font-mono text-[10px]">{snap.generated_time || "—"}</span>
          </div>
        </div>
      </Section>

      {/* ── Section 2: Clinical Timeline ── */}
      <Section title="Clinical Timeline" icon={Clock} sectionNumber={2}>
        <div className="relative border-l border-slate-200 dark:border-slate-800 ml-2 pl-6 space-y-4 pt-1">
          {(clin.timeline || []).map((evt: any, idx: number) => (
            <div key={idx} className="relative">
              <span className="absolute -left-[31px] top-1 h-2.5 w-2.5 rounded-full border-2 border-white bg-slate-400 dark:border-slate-900" />
              <div className="flex flex-col gap-0.5">
                <span className="text-[10px] font-bold text-slate-400 font-mono">{evt.time}</span>
                <span className="font-bold text-slate-800 dark:text-slate-200">{evt.event}</span>
                <span className="text-slate-500 text-[10px]">{evt.actor} {evt.reason && `· ${evt.reason}`}</span>
              </div>
            </div>
          ))}
        </div>
      </Section>

      {/* ── Section 3: Presenting Complaint ── */}
      <Section title="Presenting Complaint" icon={Stethoscope} sectionNumber={3}>
        <div className="space-y-3">
          <div>
            <h4 className="font-bold text-slate-850 dark:text-slate-350">Chief Complaint:</h4>
            <p className="mt-0.5 font-bold text-sm text-slate-900 dark:text-slate-100">{pc.chief_complaint}</p>
          </div>
          <div>
            <h4 className="font-bold text-slate-850 dark:text-slate-350">Emergency Intake Narrative:</h4>
            <p className="mt-0.5 text-slate-700 dark:text-slate-300 whitespace-pre-wrap">{pc.emergency_description}</p>
          </div>
        </div>
      </Section>

      {/* ── Section 4: History of Present Illness ── */}
      <Section title="History of Present Illness (HPI)" icon={Info} sectionNumber={4}>
        <p className="text-slate-700 dark:text-slate-300">{clin.hpi}</p>
      </Section>

      {/* ── Section 5: Vital Signs (Highlight abnormal) ── */}
      <Section title="Vital Signs Assessment" icon={Activity} sectionNumber={5}>
        <div className="border rounded-xl overflow-hidden divide-y bg-slate-50/10">
          <div className="grid grid-cols-[1.5fr_1fr_1fr_1fr] p-3 font-bold text-slate-400 text-[10px] uppercase tracking-wider bg-slate-50 dark:bg-slate-900/50">
            <span>Vital Sign</span>
            <span>Recorded Value</span>
            <span>Normal Range</span>
            <span>Assessment</span>
          </div>

          {[
            { label: "Heart Rate", val: vitals.heart_rate, unit: " bpm", range: "60–100 bpm", abn: vitals.heart_rate && !(60 <= vitals.heart_rate && vitals.heart_rate <= 100) },
            { label: "Oxygen Saturation (SpO₂)", val: vitals.spo2, unit: "%", range: "95–100%", abn: vitals.spo2 && !(95 <= vitals.spo2 && vitals.spo2 <= 100) },
            { label: "Blood Pressure", val: vitals.blood_pressure, unit: "", range: "90-140/60-90 mmHg", abn: vitals.bp_systolic && (vitals.bp_systolic > 140 || vitals.bp_systolic < 90) },
            { label: "Body Temperature", val: vitals.temperature, unit: "°C", range: "36.1–37.8°C", abn: vitals.temperature && !(36.1 <= vitals.temperature && vitals.temperature <= 37.8) },
            { label: "Respiratory Rate", val: vitals.respiratory_rate, unit: "/min", range: "12–20 breath/min", abn: vitals.respiratory_rate && !(12 <= vitals.respiratory_rate && vitals.respiratory_rate <= 20) },
          ].map((item) => (
            <div key={item.label} className="grid grid-cols-[1.5fr_1fr_1fr_1fr] p-3 items-center text-xs">
              <span className="font-bold text-slate-800 dark:text-slate-200">{item.label}</span>
              <span className={cn("font-mono font-bold", item.abn && "text-rose-600 dark:text-rose-400")}>
                {item.val ?? "—"}{item.unit}
              </span>
              <span className="text-slate-500">{item.range}</span>
              <span className={cn("font-bold uppercase text-[9px] px-2 py-0.5 rounded inline-flex self-start", item.abn ? "bg-rose-500/10 text-rose-600 dark:text-rose-400" : "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400")}>
                {item.abn ? "Abnormal" : "Normal"}
              </span>
            </div>
          ))}
        </div>
      </Section>

      {/* ── Section 6: Investigations Reviewed ── */}
      <Section title="Investigations Reviewed" icon={ListChecks} sectionNumber={6}>
        <div className="grid gap-2 sm:grid-cols-2">
          {(clin.investigations_matrix || []).map((t: any) => {
            const isCompleted = t.status === "Completed";
            const isPending = t.status === "Pending";
            return (
              <div key={t.test_name} className="flex items-center justify-between p-3.5 border rounded-xl bg-slate-50/20">
                <span className="font-bold text-slate-850 dark:text-slate-250">{t.test_name}</span>
                <span className={cn(
                  "px-2.5 py-0.5 rounded text-[9px] font-black uppercase tracking-wider",
                  isCompleted ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400" :
                  isPending ? "bg-amber-500/10 text-amber-600 dark:text-amber-400" :
                  "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400"
                )}>
                  {isCompleted ? "🟢 Completed" : isPending ? "🟡 Pending" : "⚪ Not Requested"}
                </span>
              </div>
            );
          })}
        </div>
      </Section>

      {/* ── Section 7: Clinical Findings ── */}
      <Section title="Clinical Findings" icon={Wind} sectionNumber={7}>
        <div className="space-y-4">
          {clin.clinical_findings.cardiac && (
            <div>
              <h4 className="font-bold text-slate-850 dark:text-slate-350">Cardiac Findings:</h4>
              <p className="mt-1 text-slate-700 dark:text-slate-300">{clin.clinical_findings.cardiac}</p>
            </div>
          )}
          {clin.clinical_findings.respiratory && (
            <div>
              <h4 className="font-bold text-slate-850 dark:text-slate-350">Respiratory Findings:</h4>
              <p className="mt-1 text-slate-700 dark:text-slate-300">{clin.clinical_findings.respiratory}</p>
            </div>
          )}
          {!clin.clinical_findings.cardiac && !clin.clinical_findings.respiratory && (
            <p className="text-slate-700 dark:text-slate-300">{clin.clinical_findings.general}</p>
          )}
        </div>
      </Section>

      {/* ── Section 8: Differential Diagnosis ── */}
      <Section title="Differential Diagnosis" icon={TrendingUp} sectionNumber={8}>
        <div className="space-y-4">
          {(clin.differential_diagnosis || []).map((diff: any) => (
            <div key={diff.condition} className="p-4 border border-slate-200 dark:border-slate-800 bg-slate-50/20 rounded-xl space-y-2">
              <h4 className="font-bold text-sm text-slate-900 dark:text-slate-100">
                Condition: {diff.condition}
              </h4>
              <div className="grid gap-2 sm:grid-cols-2 text-xs">
                <div>
                  <span className="font-bold text-slate-500 uppercase text-[9px] tracking-wider block mb-1">Supporting Findings:</span>
                  {(diff.supporting || []).length > 0 ? (
                    <ul className="list-disc list-inside space-y-0.5 text-slate-700 dark:text-slate-300">
                      {(diff.supporting || []).map((s: string) => <li key={s}>{s}</li>)}
                    </ul>
                  ) : <span className="text-slate-400 italic">None identified</span>}
                </div>
                <div>
                  <span className="font-bold text-slate-500 uppercase text-[9px] tracking-wider block mb-1">Contradicting Findings:</span>
                  {(diff.contradicting || []).length > 0 ? (
                    <ul className="list-disc list-inside space-y-0.5 text-rose-700 dark:text-rose-350">
                      {(diff.contradicting || []).map((c: string) => <li key={c}>{c}</li>)}
                    </ul>
                  ) : <span className="text-slate-400 italic">None identified</span>}
                </div>
              </div>
              <div className="pt-2 border-t text-xs">
                <span className="font-bold text-slate-500 uppercase text-[9px] tracking-wider block mb-0.5">Further Evidence Required:</span>
                <span className="italic text-slate-600 dark:text-slate-400">{diff.further_evidence}</span>
              </div>
            </div>
          ))}
        </div>
      </Section>

      {/* ── Section 9: Clinical Impression ── */}
      <Section title="Clinical Impression" icon={ShieldAlert} sectionNumber={9}>
        <div className="space-y-3">
          <div>
            <span className="font-bold text-slate-850 dark:text-slate-350 block">Primary Impression:</span>
            <span className="text-slate-900 dark:text-slate-100 font-bold">{clin.clinical_impression.primary}</span>
          </div>
          {clin.clinical_impression.secondary && (
            <div>
              <span className="font-bold text-slate-850 dark:text-slate-350 block">Secondary Considerations:</span>
              <span className="text-slate-700 dark:text-slate-300">{clin.clinical_impression.secondary}</span>
            </div>
          )}
          <div>
            <span className="font-bold text-slate-850 dark:text-slate-350 block">Clinical Assessment Note:</span>
            <p className="mt-1 text-slate-750 dark:text-slate-350 whitespace-pre-wrap">{clin.clinical_impression.assessment}</p>
          </div>
        </div>
      </Section>

      {/* ── Section 10: Recommended Next Steps ── */}
      <Section title="Recommended Next Steps" icon={ListChecks} sectionNumber={10}>
        <div className="space-y-3">
          <div>
            <h4 className="font-bold text-slate-850 dark:text-slate-350 uppercase text-[10px] tracking-wider mb-1">Immediate Actions:</h4>
            <ul className="list-disc list-inside space-y-0.5 text-slate-700 dark:text-slate-300">
              {(clin.recommendations?.immediate || []).map((r: string) => <li key={r}>{r}</li>)}
            </ul>
          </div>
          <div>
            <h4 className="font-bold text-slate-850 dark:text-slate-350 uppercase text-[10px] tracking-wider mb-1">Short-Term Observation:</h4>
            <ul className="list-disc list-inside space-y-0.5 text-slate-700 dark:text-slate-300">
              {(clin.recommendations?.short_term || []).map((r: string) => <li key={r}>{r}</li>)}
            </ul>
          </div>
          <div>
            <h4 className="font-bold text-slate-850 dark:text-slate-350 uppercase text-[10px] tracking-wider mb-1">Additional Investigations Required:</h4>
            <ul className="list-disc list-inside space-y-0.5 text-slate-700 dark:text-slate-300">
              {(clin.recommendations?.additional || []).map((r: string) => <li key={r}>{r}</li>)}
            </ul>
          </div>
        </div>
      </Section>

      {/* ── Section 11: Evidence Quality & Summary ── */}
      <Section title="Evidence Quality & Summary" icon={ShieldCheck} sectionNumber={11}>
        <div className="space-y-4">
          <div className="p-3.5 border rounded-xl bg-slate-50/20 space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-850 dark:text-slate-250">Overall Reliability Assessment:</span>
              <span className={cn(
                "px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-wider",
                clin.evidence_quality.reliability === "High" ? "bg-emerald-500/10 text-emerald-600" : "bg-amber-500/10 text-amber-600"
              )}>
                {clin.evidence_quality.reliability}
              </span>
            </div>
            <p className="text-slate-500 text-[10px] leading-relaxed pt-1">{clin.evidence_quality.reason}</p>
          </div>

          <div>
            <h4 className="font-bold text-slate-850 dark:text-slate-350 uppercase text-[10px] tracking-wider mb-2">Version History:</h4>
            <div className="border rounded-xl overflow-hidden divide-y">
              {(clin.evidence_quality?.history || []).map((v: any) => (
                <div key={v.version} className="grid grid-cols-[80px_100px_1fr] p-3 text-xs">
                  <span className="font-bold text-slate-900 dark:text-slate-100">{v.version}</span>
                  <span className="font-mono text-slate-400">{v.time}</span>
                  <span className="text-slate-600 dark:text-slate-400">{v.event}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Section>

      {/* ── Section 12: Technical Appendix (Task B8) ── */}
      <Section title="Technical Appendix & Platform Diagnostics" icon={MonitorCheck} sectionNumber={12}>
        <div className="space-y-4">
          <p className="italic text-slate-400 dark:text-slate-500 text-[11px]">
            This appendix contains machine learning metrics, SHAP diagnostics, and runtimes intended solely for system administrators and engineering audits.
          </p>

          {/* Aggregate probabilities */}
          {report.aggregation?.available && (
            <div>
              <h4 className="font-bold text-slate-800 dark:text-slate-200 mb-2">Aggregated Model Probabilities:</h4>
              <div className="border rounded-xl overflow-hidden divide-y">
                {Object.entries(report.aggregation.probabilities || {}).map(([cond, prob]) => (
                  <div key={cond} className="grid grid-cols-2 p-3 text-xs">
                    <span className="font-bold text-slate-700 dark:text-slate-300">{cond}</span>
                    <span className="font-mono text-slate-500">
                      {prob !== null ? `${(prob as number * 100).toFixed(1)}%` : "—"}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Subsystem Runtimes and Model Info */}
          <div>
            <h4 className="font-bold text-slate-800 dark:text-slate-200 mb-2">Subsystem Runtimes:</h4>
            <div className="grid gap-2 sm:grid-cols-2">
              <div className="p-3 border rounded-xl bg-slate-50/20">
                <span className="font-bold block text-slate-700">Lab Subsystem Model:</span>
                <span className="text-slate-400 font-mono text-[10px]">{report.lab_intelligence?.model_name || "XGBoost Cardiac"}</span>
              </div>
              <div className="p-3 border rounded-xl bg-slate-50/20">
                <span className="font-bold block text-slate-700">Imaging Subsystem Model:</span>
                <span className="text-slate-400 font-mono text-[10px]">{report.imaging_intelligence?.model_name || "EfficientNet X-ray"}</span>
              </div>
            </div>
          </div>
        </div>
      </Section>
    </div>
  );
}
