/**
 * ClinicalReport — 17-Section Clinical Decision-Support Report
 *
 * Renders the unified Report DTO from the backend into a clinician-facing
 * layout matching both the web UI and the PDF export structure.
 *
 * Section order:
 *   1.  Patient Summary
 *   2.  Clinical Overview (LLM narrative)
 *   3.  Vital Signs (highlight abnormal)
 *   4.  Key Clinical Findings (NLP + symptoms + risk)
 *   5.  Overall Clinical Impression
 *   6.  Alternative Considerations
 *   7.  Why This Condition Was Ranked Highest
 *   8.  Cardiac Assessment
 *   9.  Respiratory Assessment
 *   10. Laboratory Assessment
 *   11. Imaging Assessment
 *   12. Monitoring Priorities
 *   13. Immediate Clinical Precautions
 *   14. Recommended Next Clinical Steps
 *   15. Clinical Data Used for Analysis
 *   16. Report Quality & Evidence Completeness
 *   17. System Information & Disclaimer
 */

import { cn } from "@/lib/utils";
import type {
  ClinicalReport as ClinicalReportData,
  StageStatus,
} from "@/lib/report-api";
import { PipelineStatus } from "./pipeline-status";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  BarChart3,
  Brain,
  CheckCircle2,
  ClipboardList,
  Droplets,
  FileImage,
  FileText,
  FlaskConical,
  Heart,
  Info,
  Layers,
  ListChecks,
  Loader2,
  Microscope,
  MonitorCheck,
  Search,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Stethoscope,
  Thermometer,
  TrendingUp,
  Wind,
  XCircle,
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

// ── Severity helpers ────────────────────────────────────────────────────

const SEVERITY_COLORS: Record<string, string> = {
  critical: "text-rose-800 dark:text-rose-300 bg-rose-100 dark:bg-rose-950/60 border-rose-300 dark:border-rose-700",
  high: "text-orange-800 dark:text-orange-300 bg-orange-100 dark:bg-orange-950/60 border-orange-300 dark:border-orange-700",
  moderate: "text-amber-800 dark:text-amber-300 bg-amber-100 dark:bg-amber-950/60 border-amber-300 dark:border-amber-700",
  low: "text-emerald-800 dark:text-emerald-300 bg-emerald-100 dark:bg-emerald-950/60 border-emerald-300 dark:border-emerald-700",
};

const CONFIDENCE_COLORS: Record<string, string> = {
  "VERY HIGH": "text-emerald-800 dark:text-emerald-300 bg-emerald-100 dark:bg-emerald-950/60 border-emerald-300 dark:border-emerald-700",
  HIGH: "text-sky-800 dark:text-sky-300 bg-sky-100 dark:bg-sky-950/60 border-sky-300 dark:border-sky-700",
  MODERATE: "text-amber-800 dark:text-amber-300 bg-amber-100 dark:bg-amber-950/60 border-amber-300 dark:border-amber-700",
  LOW: "text-rose-800 dark:text-rose-300 bg-rose-100 dark:bg-rose-950/60 border-rose-300 dark:border-rose-700",
};

function riskColor(value: number): string {
  if (value >= 70) return "text-rose-700 dark:text-rose-400";
  if (value >= 50) return "text-orange-700 dark:text-orange-400";
  if (value >= 30) return "text-amber-700 dark:text-amber-400";
  return "text-emerald-700 dark:text-emerald-400";
}

function riskBg(value: number): string {
  if (value >= 70) return "bg-rose-600";
  if (value >= 50) return "bg-orange-600";
  if (value >= 30) return "bg-amber-600";
  return "bg-emerald-600";
}

// ── Section wrapper ─────────────────────────────────────────────────────

function Section({ title, icon: Icon, sectionNumber, children }: { title: string; icon: typeof Brain; sectionNumber?: number; children: React.ReactNode }) {
  return (
    <Card className="border-2 border-slate-300 dark:border-slate-600 shadow-sm">
      <CardHeader className="pb-3 border-b-2 border-slate-100 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-800/50">
        <CardTitle className="flex items-center gap-2 text-sm font-bold text-slate-900 dark:text-gray-50">
          <Icon className="h-4 w-4 text-primary shrink-0" />
          {sectionNumber != null && (
            <span className="flex items-center justify-center h-5 w-5 rounded-full bg-primary/10 text-primary text-[10px] font-extrabold shrink-0">{sectionNumber}</span>
          )}
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-4">{children}</CardContent>
    </Card>
  );
}

// ── Main component ──────────────────────────────────────────────────────

export function ClinicalReport({ report, reportRef, pipelineStages, isPolling }: Props) {
  const {
    patient_summary: p,
    vitals: v,
    symptoms,
    nlp_findings,
    risk_engine,
    lab_intelligence,
    imaging_intelligence,
    aggregation,
    evidence,
    pipeline_status,
    clinical_interpretation: interp,
    clinical_conclusions: conc,
  } = report;

  // Safely handle missing conclusions/interpretation (backward compat)
  const hasConclusions = conc && Object.keys(conc).length > 0;
  const hasInterp = interp && Object.keys(interp).length > 0;

  return (
    <div ref={reportRef} className="space-y-6">
      {/* ── Pipeline Status ── */}
      <div className="rounded-lg border-2 border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800/60 p-4 shadow-sm">
        <div className="mb-3 flex items-center gap-2">
          <span className="text-[11px] font-bold uppercase tracking-[0.15em] text-slate-800 dark:text-gray-200">
            AI Pipeline Status
          </span>
          {isPolling && (
            <span className="flex items-center gap-1 rounded-full bg-sky-100 dark:bg-sky-900/60 px-2 py-0.5 text-[9px] font-bold text-sky-700 dark:text-sky-300 border border-sky-300 dark:border-sky-700">
              <span className="relative flex h-1.5 w-1.5"><span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-sky-400 opacity-75" /><span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-sky-500" /></span>
              LIVE
            </span>
          )}
        </div>
        <PipelineStatus status={pipeline_status} stages={pipelineStages} />
      </div>

      {/* ── 1. Patient Summary ── */}
      <Section title="Patient Summary" icon={Activity} sectionNumber={1}>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <h3 className="text-xl font-bold text-slate-900 dark:text-gray-50">{p.name}</h3>
            <p className="text-sm font-semibold text-slate-700 dark:text-gray-300 mt-1">
              {p.age}y · {p.gender === "male" ? "Male" : p.gender === "female" ? "Female" : p.gender} · Contact: {p.contact || "—"}
            </p>
            {p.arrival_time && (
              <p className="text-xs font-semibold text-slate-600 dark:text-gray-400 mt-0.5">Arrival: {p.arrival_time}</p>
            )}
          </div>
          <div className="flex items-start justify-end gap-2">
            <span className={cn("rounded-md border-2 px-3 py-1.5 text-xs font-bold uppercase tracking-wider shadow-sm", SEVERITY_COLORS[p.severity] ?? SEVERITY_COLORS.moderate)}>
              {p.severity}
            </span>
          </div>
        </div>
        <div className="mt-4 space-y-2.5 text-sm">
          <div>
            <span className="text-slate-700 dark:text-gray-300 font-bold">Chief Complaint: </span>
            <span className="font-extrabold text-slate-900 dark:text-gray-50">{p.chief_complaint || "—"}</span>
          </div>
          <div>
            <span className="text-slate-700 dark:text-gray-300 font-bold">Emergency Description: </span>
            <span className="text-slate-900 dark:text-gray-100 font-semibold">{p.emergency_description || "—"}</span>
          </div>
          {p.allergies.length > 0 && (
            <div>
              <span className="text-slate-700 dark:text-gray-300 font-bold">Allergies: </span>
              <span className="text-rose-700 font-extrabold">{p.allergies.join(", ")}</span>
            </div>
          )}
          {p.medications.length > 0 && (
            <div>
              <span className="text-slate-700 dark:text-gray-300 font-bold">Medications: </span>
              <span className="text-slate-900 dark:text-gray-100 font-semibold">{p.medications.join(", ")}</span>
            </div>
          )}
        </div>
      </Section>

      {/* ── 2. Clinical Overview (LLM) ── */}
      {hasInterp && interp.clinical_overview && (
        <Section title="Clinical Overview" icon={Stethoscope} sectionNumber={2}>
          <p className="text-sm leading-relaxed font-semibold text-slate-800 dark:text-gray-200">{interp.clinical_overview}</p>
        </Section>
      )}

      {/* ── 3. Vital Signs ── */}
      <Section title="Vital Signs" icon={Heart} sectionNumber={3}>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          <VitalCard icon={Heart} label="Heart Rate" value={v.heart_rate != null ? `${v.heart_rate} bpm` : "—"} alert={(v.heart_rate ?? 0) > 100 || (v.heart_rate ?? 999) < 60} />
          <VitalCard icon={Droplets} label="SpO₂" value={v.spo2 != null ? `${v.spo2}%` : "—"} alert={(v.spo2 ?? 100) < 95} />
          <VitalCard icon={Activity} label="Blood Pressure" value={v.blood_pressure || "—"} alert={(v.bp_systolic ?? 120) > 140 || (v.bp_systolic ?? 120) < 90} />
          <VitalCard icon={Wind} label="Resp. Rate" value={v.respiratory_rate != null ? `${v.respiratory_rate}/min` : "—"} alert={(v.respiratory_rate ?? 0) > 20} />
          <VitalCard icon={Thermometer} label="Temperature" value={v.temperature != null ? `${v.temperature}°C` : "—"} alert={(v.temperature ?? 0) > 37.8 || ((v.temperature ?? 37) < 36.1 && v.temperature != null)} />
        </div>
      </Section>

      {/* ── 4. Key Clinical Findings ── */}
      <Section title="Key Clinical Findings" icon={Brain} sectionNumber={4}>
        {nlp_findings.summary && (
          <p className="mb-4 text-sm leading-relaxed font-semibold text-slate-800 dark:text-gray-200">
            {nlp_findings.summary}
          </p>
        )}
        {/* Active flags */}
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
          {Object.entries(nlp_findings.flags).map(([flag, active]) => (
            <div
              key={flag}
              className={cn(
                "flex items-center gap-2 rounded-md border-2 px-3 py-2 text-xs font-bold shadow-sm",
                active ? "border-rose-400 dark:border-rose-700 bg-rose-50 dark:bg-rose-950/50 text-rose-700 dark:text-rose-300" : "border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800/50 text-slate-700 dark:text-gray-300",
              )}
            >
              {active ? <CheckCircle2 className="h-3.5 w-3.5 text-rose-600 dark:text-rose-400" /> : <XCircle className="h-3.5 w-3.5 text-slate-400 dark:text-slate-500" />}
              <span className="capitalize">{flag.replace(/_/g, " ")}</span>
            </div>
          ))}
        </div>
        {symptoms.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {symptoms.map((s) => (
              <span key={s} className="rounded-full border-2 border-slate-300 dark:border-slate-600 bg-slate-100 dark:bg-slate-700/50 px-2.5 py-0.5 text-[11px] font-bold text-slate-800 dark:text-gray-200">
                {s}
              </span>
            ))}
          </div>
        )}
        {/* Risk scores */}
        <div className="mt-4 grid grid-cols-2 gap-3 lg:grid-cols-4">
          {[
            { label: "Cardiac", value: risk_engine.cardiac },
            { label: "Respiratory", value: risk_engine.respiratory },
            { label: "Trauma", value: risk_engine.trauma },
            { label: "Neurological", value: risk_engine.neurological },
          ].map(({ label, value }) => (
            <div key={label} className="rounded-md border-2 border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800/50 p-3 shadow-sm">
              <p className="text-[10px] font-bold text-slate-700 dark:text-gray-300">{label} Risk</p>
              <p className={cn("mt-1 text-xl font-extrabold tabular-nums", riskColor(value))}>{value}/100</p>
              <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
                <div className={cn("h-full rounded-full transition-all duration-700", riskBg(value))} style={{ width: `${value}%` }} />
              </div>
            </div>
          ))}
        </div>
      </Section>

      {/* ── 5. Overall Clinical Impression ── */}
      {hasConclusions && (
        <Section title="Overall Clinical Impression" icon={Layers} sectionNumber={5}>
          <div className="space-y-4">
            {/* Primary condition */}
            <div className="flex flex-wrap items-center gap-3">
              <div className="rounded-md border-2 bg-primary/10 border-primary/30 px-4 py-2">
                <p className="text-[10px] font-bold text-slate-700 dark:text-gray-300">Most Likely Condition</p>
                <p className="text-lg font-bold text-primary">{conc.primary_condition ?? "Pending"}</p>
              </div>
              <div className={cn("rounded-md border-2 px-3 py-2", CONFIDENCE_COLORS[conc.clinical_confidence] ?? CONFIDENCE_COLORS.MODERATE)}>
                <p className="text-[10px] font-bold">Clinical Confidence</p>
                <p className="text-lg font-extrabold">{conc.clinical_confidence}</p>
              </div>
            </div>

            {/* Confidence factors (audit trail) */}
            {conc.confidence_factors.length > 0 && (
              <div className="rounded-md border-2 border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 p-3">
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-600 dark:text-gray-400 mb-2">Confidence Calculated From</p>
                {conc.confidence_factors.map((f, i) => (
                  <p key={i} className="text-xs font-semibold text-slate-700 dark:text-gray-300 leading-relaxed">{f}</p>
                ))}
              </div>
            )}

            {/* Uncertainty reasons */}
            {conc.uncertainty_reasons.length > 0 && (
              <div className="rounded-md border-2 border-amber-300 dark:border-amber-700 bg-amber-50 dark:bg-amber-950/50 p-3">
                <p className="text-[10px] font-bold uppercase tracking-wider text-amber-700 dark:text-amber-400 mb-2">Why Certainty Is Reduced</p>
                {conc.uncertainty_reasons.map((r, i) => (
                  <p key={i} className="text-xs font-semibold text-amber-800 dark:text-amber-300 leading-relaxed">• {r}</p>
                ))}
              </div>
            )}

            {/* LLM overall impression */}
            {hasInterp && interp.overall_impression && (
              <p className="text-sm leading-relaxed font-semibold text-slate-800 dark:text-gray-200 border-l-4 border-primary/30 pl-3">
                {interp.overall_impression}
              </p>
            )}

            {/* Supporting evidence */}
            {conc.supporting_evidence.length > 0 && (
              <div>
                <p className="text-xs font-bold text-emerald-700 dark:text-emerald-400 mb-1">Supporting Evidence</p>
                {conc.supporting_evidence.map((e, i) => (
                  <p key={i} className="text-xs font-semibold text-slate-700 dark:text-gray-300 leading-relaxed flex items-start gap-1.5">
                    <CheckCircle2 className="h-3 w-3 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />{e}
                  </p>
                ))}
              </div>
            )}
            {conc.conflicting_evidence.length > 0 && (
              <div>
                <p className="text-xs font-bold text-amber-700 dark:text-amber-400 mb-1">Conflicting Evidence</p>
                {conc.conflicting_evidence.map((e, i) => (
                  <p key={i} className="text-xs font-semibold text-slate-700 dark:text-gray-300 leading-relaxed flex items-start gap-1.5">
                    <AlertTriangle className="h-3 w-3 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />{e}
                  </p>
                ))}
              </div>
            )}
          </div>
        </Section>
      )}

      {/* ── 6. Alternative Considerations ── */}
      {hasConclusions && (conc.alternative_conditions.length > 0 || (hasInterp && interp.alternative_considerations_narrative)) && (
        <Section title="Alternative Considerations" icon={Search} sectionNumber={6}>
          {hasInterp && interp.alternative_considerations_narrative && (
            <p className="text-sm leading-relaxed font-semibold text-slate-800 dark:text-gray-200 mb-4">
              {interp.alternative_considerations_narrative}
            </p>
          )}
          {conc.alternative_conditions.length > 0 && (
            <div className="space-y-2">
              {conc.alternative_conditions.map((alt) => (
                <div key={alt.condition_key} className="flex items-center justify-between rounded-md border-2 border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800/50 px-3 py-2 shadow-sm">
                  <span className="text-sm font-bold text-slate-800 dark:text-gray-200">{alt.condition}</span>
                  <span className="text-xs font-mono font-bold tabular-nums text-slate-600 dark:text-gray-400">{(alt.probability * 100).toFixed(1)}%</span>
                </div>
              ))}
            </div>
          )}
        </Section>
      )}

      {/* ── 7. Why This Condition Was Ranked Highest ── */}
      {hasConclusions && conc.ranking_justification && (conc.ranking_justification.primary_reasons.length > 0 || conc.ranking_justification.vs_alternatives.length > 0) && (
        <Section title="Why This Condition Was Ranked Highest" icon={BarChart3} sectionNumber={7}>
          {conc.ranking_justification.primary_reasons.length > 0 && (
            <div className="mb-4">
              <p className="text-xs font-bold text-primary mb-1.5">Supported By</p>
              {conc.ranking_justification.primary_reasons.map((r, i) => (
                <p key={i} className="text-xs font-semibold text-slate-700 dark:text-gray-300 leading-relaxed flex items-start gap-1.5">
                  <CheckCircle2 className="h-3 w-3 text-primary shrink-0 mt-0.5" />{r}
                </p>
              ))}
            </div>
          )}
          {conc.ranking_justification.vs_alternatives.map((alt) => (
            <div key={alt.condition} className="mb-3 rounded-md border-2 border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 p-3">
              <p className="text-xs font-bold text-slate-800 dark:text-gray-200 mb-1">Ranked above {alt.condition} because:</p>
              {alt.reasons.map((r, i) => (
                <p key={i} className="text-[11px] font-semibold text-slate-600 dark:text-gray-400 leading-relaxed">• {r}</p>
              ))}
            </div>
          ))}
        </Section>
      )}

      {/* ── 8. Cardiac Assessment ── */}
      <Section title="Cardiac Assessment" icon={Heart} sectionNumber={8}>
        {hasInterp && interp.cardiac_summary ? (
          <p className="text-sm leading-relaxed font-semibold text-slate-800 dark:text-gray-200">{interp.cardiac_summary}</p>
        ) : (
          <p className="text-sm font-semibold text-slate-600 dark:text-gray-400">
            Cardiac risk score: {risk_engine.cardiac}/100. {lab_intelligence.available
              ? `Lab prediction: ${lab_intelligence.prediction?.replace(/_/g, " ")} (probability: ${((lab_intelligence.risk_probability ?? 0) * 100).toFixed(1)}%).`
              : "Laboratory cardiac analysis not yet available."}
          </p>
        )}
      </Section>

      {/* ── 9. Respiratory Assessment ── */}
      <Section title="Respiratory Assessment" icon={Wind} sectionNumber={9}>
        {hasInterp && interp.respiratory_summary ? (
          <p className="text-sm leading-relaxed font-semibold text-slate-800 dark:text-gray-200">{interp.respiratory_summary}</p>
        ) : (
          <p className="text-sm font-semibold text-slate-600 dark:text-gray-400">
            Respiratory risk score: {risk_engine.respiratory}/100. {imaging_intelligence.available
              ? `Imaging: ${imaging_intelligence.prediction} (probability: ${((imaging_intelligence.pneumonia_probability ?? 0) * 100).toFixed(1)}%).`
              : "Imaging analysis not yet available."}
          </p>
        )}
      </Section>

      {/* ── 10. Laboratory Assessment ── */}
      <Section title="Laboratory Assessment" icon={FlaskConical} sectionNumber={10}>
        {lab_intelligence.available ? (
          <div className="space-y-4">
            {hasInterp && interp.laboratory_summary && (
              <p className="text-sm leading-relaxed font-semibold text-slate-800 dark:text-gray-200 border-l-4 border-primary/30 pl-3">{interp.laboratory_summary}</p>
            )}
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              <StatBox label="Prediction" value={lab_intelligence.prediction?.replace(/_/g, " ") ?? "—"} alert={lab_intelligence.prediction === "high_risk"} />
              <StatBox label="Risk Probability" value={lab_intelligence.risk_probability != null ? `${(lab_intelligence.risk_probability * 100).toFixed(1)}%` : "—"} alert={(lab_intelligence.risk_probability ?? 0) > 0.5} />
              <StatBox label="Confidence" value={hasConclusions ? conc.clinical_confidence : "—"} />
            </div>
            {lab_intelligence.top_features && Object.keys(lab_intelligence.top_features).length > 0 && (
              <div>
                <p className="mb-2 flex items-center gap-1.5 text-xs font-bold text-slate-800 dark:text-gray-200"><TrendingUp className="h-3.5 w-3.5" /> Key Contributing Factors</p>
                <div className="space-y-1.5">
                  {Object.entries(lab_intelligence.top_features).map(([feat, val]) => {
                    const absVal = Math.abs(Number(val));
                    const maxWidth = 60;
                    const width = Math.min(absVal * 200, maxWidth);
                    return (
                      <div key={feat} className="flex items-center gap-2 text-xs font-bold">
                        <span className="w-28 shrink-0 truncate text-slate-700 dark:text-gray-300">{feat.replace(/_/g, " ")}</span>
                        <div className="flex-1">
                          <div className={cn("h-2.5 rounded-full transition-all", Number(val) > 0 ? "bg-rose-500" : "bg-emerald-500")} style={{ width: `${width}%` }} />
                        </div>
                        <span className={cn("w-16 text-right font-mono tabular-nums", Number(val) > 0 ? "text-rose-700 dark:text-rose-400" : "text-emerald-700 dark:text-emerald-400")}>
                          {Number(val) > 0 ? "+" : ""}{Number(val).toFixed(4)}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        ) : (
          <EmptyState>Laboratory analysis has not been performed for this patient.</EmptyState>
        )}
      </Section>

      {/* ── 11. Imaging Assessment ── */}
      <Section title="Imaging Assessment" icon={FileImage} sectionNumber={11}>
        {imaging_intelligence.available ? (
          <div className="space-y-4">
            {hasInterp && interp.imaging_summary && (
              <p className="text-sm leading-relaxed font-semibold text-slate-800 dark:text-gray-200 border-l-4 border-primary/30 pl-3">{interp.imaging_summary}</p>
            )}
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              <StatBox label="Finding" value={imaging_intelligence.prediction?.replace(/_/g, " ") ?? "—"} alert={imaging_intelligence.prediction === "pneumonia"} />
              <StatBox label="Pneumonia Probability" value={imaging_intelligence.pneumonia_probability != null ? `${(imaging_intelligence.pneumonia_probability * 100).toFixed(1)}%` : "—"} alert={(imaging_intelligence.pneumonia_probability ?? 0) > 0.5} />
              <StatBox label="Confidence" value={hasConclusions ? conc.clinical_confidence : (imaging_intelligence.confidence != null ? `${(imaging_intelligence.confidence * 100).toFixed(1)}%` : "—")} />
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {imaging_intelligence.xray_url && (
                <div>
                  <p className="mb-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-700 dark:text-gray-300">Original X-ray</p>
                  <div className="overflow-hidden rounded-lg border-2 border-slate-300 dark:border-slate-600 bg-black">
                    <img src={imaging_intelligence.xray_url} alt="Original chest X-ray" className="block w-full" loading="lazy" />
                  </div>
                </div>
              )}
              {imaging_intelligence.gradcam_url && (
                <div>
                  <p className="mb-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-700 dark:text-gray-300">Grad-CAM Heatmap</p>
                  <div className="overflow-hidden rounded-lg border-2 border-slate-300 dark:border-slate-600 bg-black">
                    <img src={imaging_intelligence.gradcam_url} alt="Grad-CAM heatmap overlay" className="block w-full" loading="lazy" />
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <EmptyState>Imaging analysis has not been performed for this patient.</EmptyState>
        )}
      </Section>

      {/* ── 12. Monitoring Priorities ── */}
      {hasConclusions && conc.monitoring_priorities.length > 0 && (
        <Section title="Monitoring Priorities" icon={MonitorCheck} sectionNumber={12}>
          {hasInterp && interp.monitoring_narrative && (
            <p className="text-sm leading-relaxed font-semibold text-slate-800 dark:text-gray-200 mb-3">{interp.monitoring_narrative}</p>
          )}
          <div className="space-y-2">
            {conc.monitoring_priorities.map((m, i) => (
              <div key={i} className="flex items-start gap-3 rounded-md border-2 border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800/50 px-3 py-2 shadow-sm">
                <Activity className="h-4 w-4 text-sky-600 dark:text-sky-400 shrink-0 mt-0.5" />
                <div>
                  <p className="text-xs font-bold text-slate-900 dark:text-gray-50">{m.parameter}</p>
                  <p className="text-[11px] font-semibold text-slate-600 dark:text-gray-400">{m.reason}</p>
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* ── 13. Immediate Clinical Precautions ── */}
      {hasConclusions && conc.clinical_precautions.length > 0 && (
        <Section title="Immediate Clinical Precautions" icon={ShieldAlert} sectionNumber={13}>
          {hasInterp && interp.precautions_narrative && (
            <p className="text-sm leading-relaxed font-semibold text-slate-800 dark:text-gray-200 mb-3">{interp.precautions_narrative}</p>
          )}
          <div className="space-y-2">
            {conc.clinical_precautions.map((pc, i) => (
              <div key={i} className="flex items-start gap-3 rounded-md border-2 border-amber-300 dark:border-amber-700 bg-amber-50 dark:bg-amber-950/50 px-3 py-2 shadow-sm">
                <Shield className="h-4 w-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
                <div>
                  <p className="text-xs font-bold text-amber-900 dark:text-amber-200">{pc.action}</p>
                  <p className="text-[11px] font-semibold text-amber-700 dark:text-amber-400">{pc.reason}</p>
                </div>
              </div>
            ))}
          </div>
          <p className="mt-3 text-[10px] font-bold text-rose-800 dark:text-rose-400">
            ⚠ These are monitoring precautions only. They do not constitute treatment recommendations.
          </p>
        </Section>
      )}

      {/* ── 14. Recommended Next Clinical Steps ── */}
      {hasConclusions && conc.investigation_status.length > 0 && (
        <Section title="Recommended Next Clinical Steps" icon={ClipboardList} sectionNumber={14}>
          <div className="divide-y-2 divide-slate-200 dark:divide-slate-700 rounded-md border-2 border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800/50">
            {conc.investigation_status.map((inv) => (
              <div key={inv.investigation_type} className="flex items-center justify-between px-4 py-2.5 text-xs">
                <div className="flex items-center gap-2 font-bold text-slate-800 dark:text-gray-200">
                  <ListChecks className="h-3.5 w-3.5 text-primary shrink-0" />
                  {inv.investigation_type}
                </div>
                <div className="flex items-center gap-2">
                  <span className={cn(
                    "rounded border-2 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider shadow-sm",
                    inv.status === "approved"
                      ? "border-emerald-400 dark:border-emerald-700 bg-emerald-50 dark:bg-emerald-950/50 text-emerald-800 dark:text-emerald-300"
                      : inv.status === "rejected"
                        ? "border-rose-400 dark:border-rose-700 bg-rose-50 dark:bg-rose-950/50 text-rose-800 dark:text-rose-300"
                        : "border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700/50 text-slate-700 dark:text-gray-300",
                  )}>
                    {inv.status}
                  </span>
                  <span className={cn(
                    "rounded border-2 px-2 py-0.5 text-[9px] font-bold shadow-sm",
                    inv.ai_supported
                      ? "border-sky-300 dark:border-sky-700 bg-sky-50 dark:bg-sky-950/50 text-sky-800 dark:text-sky-300"
                      : "border-slate-300 dark:border-slate-600 bg-slate-100 dark:bg-slate-700/50 text-slate-600 dark:text-gray-400",
                  )}>
                    {inv.ai_status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* ── 15. Clinical Data Used for Analysis ── */}
      {evidence.length > 0 && (
        <Section title="Clinical Data Used for Analysis" icon={FileText} sectionNumber={15}>
          {/* Uploaded evidence files */}
          <div className="divide-y-2 divide-slate-200 dark:divide-slate-700 rounded-md border-2 border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800/50">
            {evidence.map((ev) => (
              <div key={ev.id} className="flex items-center gap-3 px-4 py-2.5 text-xs font-bold text-slate-800 dark:text-gray-200">
                <FileText className="h-3.5 w-3.5 shrink-0 text-slate-600 dark:text-gray-400" />
                <span className="flex-1 truncate">{ev.file_name}</span>
                <span className="rounded border-2 border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700/50 px-1.5 py-px text-[9px] uppercase tracking-wider text-slate-700 dark:text-gray-300 shadow-sm">
                  {ev.evidence_type}
                </span>
                {ev.file_url && (
                  <a href={ev.file_url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline font-bold">View</a>
                )}
              </div>
            ))}
          </div>

          {/* NLP extracted entities */}
          {nlp_findings.entities.length > 0 && (
            <div className="mt-4">
              <p className="text-xs font-bold text-slate-700 dark:text-gray-300 mb-2">Extracted Clinical Entities</p>
              <div className="flex flex-wrap gap-1.5">
                {nlp_findings.entities.map((e, i) => (
                  <span key={i} className="rounded border-2 border-primary/30 bg-primary/5 px-2 py-0.5 text-[10px] font-bold text-primary shadow-sm">
                    {typeof e === "string" ? e : JSON.stringify(e)}
                  </span>
                ))}
              </div>
            </div>
          )}
        </Section>
      )}

      {/* ── 16. Report Quality & Evidence Completeness ── */}
      {hasConclusions && (
        <Section title="Report Quality & Evidence Completeness" icon={ShieldCheck} sectionNumber={16}>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 mb-4">
            <StatBox label="Evidence Completeness" value={`${conc.report_quality.evidence_completeness_pct}%`} />
            <StatBox label="Subsystem Agreement" value={conc.report_quality.subsystem_agreement} />
            <StatBox label="Pipeline Integrity" value={conc.report_quality.pipeline_integrity} alert={conc.report_quality.pipeline_integrity !== "PASS"} />
            <StatBox label="Missing Critical" value={conc.report_quality.missing_critical_inputs.length === 0 ? "None" : conc.report_quality.missing_critical_inputs.join(", ")} alert={conc.report_quality.missing_critical_inputs.length > 0} />
          </div>

          {/* Clinical limitations */}
          {hasInterp && interp.limitations_narrative && (
            <p className="text-sm leading-relaxed font-semibold text-slate-800 dark:text-gray-200 mb-3 border-l-4 border-amber-300 pl-3">{interp.limitations_narrative}</p>
          )}
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
            {conc.clinical_limitations.map((lim, i) => (
              <div
                key={i}
                className={cn(
                  "flex items-center gap-2 rounded-md border-2 px-3 py-2 text-xs font-bold shadow-sm",
                  lim.available
                    ? "border-emerald-400 dark:border-emerald-700 bg-emerald-50 dark:bg-emerald-950/50 text-emerald-800 dark:text-emerald-300"
                    : "border-rose-300 dark:border-rose-700 bg-rose-50 dark:bg-rose-950/50 text-rose-700 dark:text-rose-300",
                )}
              >
                {lim.available ? <CheckCircle2 className="h-3.5 w-3.5 shrink-0" /> : <XCircle className="h-3.5 w-3.5 shrink-0" />}
                <span>{lim.source}</span>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* ── 17. System Information & Disclaimer ── */}
      <Section title="System Information & Disclaimer" icon={Info} sectionNumber={17}>
        <div className="space-y-3">
          <div className="rounded-md border-2 border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 p-3">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-600 dark:text-gray-400 mb-2">Analysis Generated Using</p>
            <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-3">
              {[
                "Clinical NLP",
                "Rule-based Risk Engine",
                "Laboratory ML Analysis",
                "Medical Imaging AI",
                "Evidence Aggregation Engine",
                "Grounded Clinical Language Model",
              ].map((tech) => (
                <p key={tech} className="text-[11px] font-semibold text-slate-700 dark:text-gray-300 flex items-center gap-1.5">
                  <CheckCircle2 className="h-3 w-3 text-primary shrink-0" />{tech}
                </p>
              ))}
            </div>
          </div>
          <div className="text-center text-[10px] font-semibold text-slate-600 dark:text-gray-400 space-y-1">
            <p>PRATHAM v{report.report_version || "1.0"} · Report Generated {new Date(report.generated_at).toLocaleString()}</p>
            <p className="text-rose-800 dark:text-rose-400 font-bold">
              ⚠ This system supports clinical decision-making and does not replace physician judgment. Final diagnosis and treatment remain the responsibility of the attending physician.
            </p>
          </div>
        </div>
      </Section>
    </div>
  );
}

// ── Subcomponents ────────────────────────────────────────────────────────

function VitalCard({ icon: Icon, label, value, alert }: { icon: typeof Heart; label: string; value: string; alert?: boolean }) {
  return (
    <div className={cn("rounded-md border-2 p-3 shadow-sm", alert ? "border-rose-500 dark:border-rose-700 bg-rose-50/50 dark:bg-rose-950/40" : "border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800/50")}>
      <div className="flex items-center gap-1.5">
        <Icon className={cn("h-3.5 w-3.5", alert ? "text-rose-700 dark:text-rose-400" : "text-slate-600 dark:text-gray-400")} />
        <p className="text-[10px] font-bold text-slate-700 dark:text-gray-300">{label}</p>
      </div>
      <p className={cn("mt-1 text-lg font-extrabold tabular-nums", alert ? "text-rose-700 dark:text-rose-400" : "text-slate-900 dark:text-gray-50")}>
        {value}
      </p>
    </div>
  );
}

function StatBox({ label, value, alert }: { label: string; value: string; alert?: boolean }) {
  return (
    <div className="rounded-md border-2 border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800/50 p-3 shadow-sm">
      <p className="text-[10px] font-bold text-slate-700 dark:text-gray-300">{label}</p>
      <p className={cn("mt-1 text-sm font-bold", alert ? "text-rose-700 dark:text-rose-400" : "text-slate-900 dark:text-gray-50")}>{value}</p>
    </div>
  );
}

function EmptyState({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-md border-2 border-dashed border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800/50 px-4 py-6 text-center text-xs font-bold text-slate-800 dark:text-gray-200">
      {children}
    </div>
  );
}
