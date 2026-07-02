/**
 * ClinicalReport — Full 8-section Clinical Intelligence Report
 *
 * Renders a comprehensive, clinician-facing report with:
 *   1. Patient Summary
 *   2. Vitals
 *   3. NLP Findings
 *   4. Risk Engine
 *   5. Lab Intelligence
 *   6. Imaging Intelligence (+ Grad-CAM)
 *   7. Aggregation Engine
 *   8. Evidence Breakdown
 */

import { cn } from "@/lib/utils";
import type { ClinicalReport as ClinicalReportData } from "@/lib/report-api";
import { PipelineStatus } from "./pipeline-status";
import {
  Activity,
  AlertCircle,
  Brain,
  CheckCircle2,
  Droplets,
  FileImage,
  FileText,
  FlaskConical,
  Heart,
  Layers,
  ShieldAlert,
  Thermometer,
  TrendingUp,
  Wind,
  XCircle,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Props {
  report: ClinicalReportData;
  /** Ref to the report container for PDF export */
  reportRef?: React.RefObject<HTMLDivElement | null>;
}

// ── Severity helpers ────────────────────────────────────────────────────

const SEVERITY_COLORS: Record<string, string> = {
  critical: "text-rose-800 bg-rose-100 border-rose-300",
  high: "text-orange-800 bg-orange-100 border-orange-300",
  moderate: "text-amber-800 bg-amber-100 border-amber-300",
  low: "text-emerald-800 bg-emerald-100 border-emerald-300",
};

function riskColor(value: number): string {
  if (value >= 70) return "text-rose-700";
  if (value >= 50) return "text-orange-700";
  if (value >= 30) return "text-amber-700";
  return "text-emerald-700";
}

function riskBg(value: number): string {
  if (value >= 70) return "bg-rose-600";
  if (value >= 50) return "bg-orange-600";
  if (value >= 30) return "bg-amber-600";
  return "bg-emerald-600";
}

// ── Section wrapper ─────────────────────────────────────────────────────

function Section({ title, icon: Icon, children }: { title: string; icon: typeof Brain; children: React.ReactNode }) {
  return (
    <Card className="border-2 border-slate-300 shadow-sm">
      <CardHeader className="pb-3 border-b-2 border-slate-100 bg-slate-50/50">
        <CardTitle className="flex items-center gap-2 text-sm font-bold text-slate-900">
          <Icon className="h-4 w-4 text-primary shrink-0" />
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-4">{children}</CardContent>
    </Card>
  );
}

// ── Main component ──────────────────────────────────────────────────────

export function ClinicalReport({ report, reportRef }: Props) {
  const { patient_summary: p, vitals: v, symptoms, nlp_findings, risk_engine, lab_intelligence, imaging_intelligence, aggregation, evidence, pipeline_status } = report;

  return (
    <div ref={reportRef} className="space-y-6">
      {/* ── Pipeline Status ── */}
      <div className="rounded-lg border-2 border-slate-300 bg-slate-50 p-4 shadow-sm">
        <div className="mb-3 text-[11px] font-bold uppercase tracking-[0.15em] text-slate-800">
          AI Pipeline Status
        </div>
        <PipelineStatus status={pipeline_status} />
      </div>

      {/* ── 1. Patient Summary ── */}
      <Section title="Patient Summary" icon={Activity}>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <h3 className="text-xl font-bold text-slate-900">{p.name}</h3>
            <p className="text-sm font-semibold text-slate-700 mt-1">
              {p.age}y · {p.gender === "male" ? "Male" : p.gender === "female" ? "Female" : p.gender} · Contact: {p.contact || "—"}
            </p>
          </div>
          <div className="flex items-start justify-end gap-2">
            <span
              className={cn(
                "rounded-md border-2 px-3 py-1.5 text-xs font-bold uppercase tracking-wider shadow-sm",
                SEVERITY_COLORS[p.severity] ?? SEVERITY_COLORS.moderate,
              )}
            >
              {p.severity}
            </span>
          </div>
        </div>
        <div className="mt-4 space-y-2.5 text-sm">
          <div>
            <span className="text-slate-700 font-bold">Chief Complaint: </span>
            <span className="font-extrabold text-slate-900">{p.chief_complaint || "—"}</span>
          </div>
          <div>
            <span className="text-slate-700 font-bold">Emergency Description: </span>
            <span className="text-slate-900 font-semibold">{p.emergency_description || "—"}</span>
          </div>
          {p.allergies.length > 0 && (
            <div>
              <span className="text-slate-700 font-bold">Allergies: </span>
              <span className="text-rose-700 font-extrabold">{p.allergies.join(", ")}</span>
            </div>
          )}
          {p.medications.length > 0 && (
            <div>
              <span className="text-slate-700 font-bold">Medications: </span>
              <span className="text-slate-900 font-semibold">{p.medications.join(", ")}</span>
            </div>
          )}
        </div>
        {symptoms.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {symptoms.map((s) => (
              <span key={s} className="rounded-full border-2 border-slate-300 bg-slate-100 px-2.5 py-0.5 text-[11px] font-bold text-slate-800">
                {s}
              </span>
            ))}
          </div>
        )}
      </Section>

      {/* ── 2. Vitals ── */}
      <Section title="Vitals" icon={Heart}>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          <VitalCard icon={Heart} label="Heart Rate" value={v.heart_rate != null ? `${v.heart_rate} bpm` : "—"} alert={(v.heart_rate ?? 0) > 100 || (v.heart_rate ?? 999) < 50} />
          <VitalCard icon={Droplets} label="SpO₂" value={v.spo2 != null ? `${v.spo2}%` : "—"} alert={(v.spo2 ?? 100) < 94} />
          <VitalCard icon={Activity} label="Blood Pressure" value={v.blood_pressure || "—"} />
          <VitalCard icon={Wind} label="Resp. Rate" value={v.respiratory_rate != null ? `${v.respiratory_rate}/min` : "—"} alert={(v.respiratory_rate ?? 0) > 20} />
          <VitalCard icon={Thermometer} label="Temperature" value={v.temperature != null ? `${v.temperature}°C` : "—"} alert={(v.temperature ?? 0) > 38} />
        </div>
      </Section>

      {/* ── 3. NLP Findings ── */}
      <Section title="NLP Findings" icon={Brain}>
        {nlp_findings.summary && (
          <p className="mb-4 text-sm leading-relaxed font-semibold text-slate-800">
            {nlp_findings.summary}
          </p>
        )}
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
          {Object.entries(nlp_findings.flags).map(([flag, active]) => (
            <div
              key={flag}
              className={cn(
                "flex items-center gap-2 rounded-md border-2 px-3 py-2 text-xs font-bold shadow-sm",
                active ? "border-rose-400 bg-rose-50 text-rose-700" : "border-slate-300 bg-slate-50 text-slate-700",
              )}
            >
              {active ? <CheckCircle2 className="h-3.5 w-3.5 text-rose-600" /> : <XCircle className="h-3.5 w-3.5 text-slate-400" />}
              <span className="capitalize">{flag.replace(/_/g, " ")}</span>
            </div>
          ))}
        </div>
        {nlp_findings.entities.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-1.5">
            {nlp_findings.entities.map((e, i) => (
              <span key={i} className="rounded border-2 border-primary/30 bg-primary/5 px-2 py-0.5 text-[10px] font-bold text-primary shadow-sm">
                {typeof e === "string" ? e : JSON.stringify(e)}
              </span>
            ))}
          </div>
        )}
      </Section>

      {/* ── 4. Risk Engine ── */}
      <Section title="Risk Engine" icon={ShieldAlert}>
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {[
            { label: "Cardiac", value: risk_engine.cardiac },
            { label: "Respiratory", value: risk_engine.respiratory },
            { label: "Trauma", value: risk_engine.trauma },
            { label: "Neurological", value: risk_engine.neurological },
          ].map(({ label, value }) => (
            <div key={label} className="rounded-md border-2 border-slate-300 bg-slate-50 p-3 shadow-sm">
              <p className="text-[11px] font-bold text-slate-700">{label}</p>
              <p className={cn("mt-1 text-2xl font-extrabold tabular-nums", riskColor(value))}>
                {value}%
              </p>
              <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-200">
                <div
                  className={cn("h-full rounded-full transition-all duration-700", riskBg(value))}
                  style={{ width: `${value}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </Section>

      {/* ── 5. Lab Intelligence ── */}
      <Section title="Lab Intelligence (XGBoost)" icon={FlaskConical}>
        {lab_intelligence.available ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              <StatBox label="Model" value={lab_intelligence.model_name?.replace(/_/g, " ") ?? "—"} />
              <StatBox
                label="Prediction"
                value={lab_intelligence.prediction?.replace(/_/g, " ") ?? "—"}
                alert={lab_intelligence.prediction === "high_risk"}
              />
              <StatBox
                label="Risk Probability"
                value={lab_intelligence.risk_probability != null ? `${(lab_intelligence.risk_probability * 100).toFixed(1)}%` : "—"}
                alert={(lab_intelligence.risk_probability ?? 0) > 0.5}
              />
            </div>

            {/* SHAP Top Features */}
            {lab_intelligence.top_features && Object.keys(lab_intelligence.top_features).length > 0 && (
              <div>
                <p className="mb-2 flex items-center gap-1.5 text-xs font-bold text-slate-800">
                  <TrendingUp className="h-3.5 w-3.5" /> SHAP Top Contributors
                </p>
                <div className="space-y-1.5">
                  {Object.entries(lab_intelligence.top_features).map(([feat, val]) => {
                    const absVal = Math.abs(Number(val));
                    const maxWidth = 60;
                    const width = Math.min(absVal * 200, maxWidth);
                    return (
                      <div key={feat} className="flex items-center gap-2 text-xs font-bold">
                        <span className="w-28 shrink-0 truncate text-slate-700">{feat.replace(/_/g, " ")}</span>
                        <div className="flex-1">
                          <div
                            className={cn(
                              "h-2.5 rounded-full transition-all",
                              Number(val) > 0 ? "bg-rose-500" : "bg-emerald-500",
                            )}
                            style={{ width: `${width}%` }}
                          />
                        </div>
                        <span className={cn("w-16 text-right font-mono tabular-nums", Number(val) > 0 ? "text-rose-700" : "text-emerald-700")}>
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
          <EmptyState>Lab analysis has not been run for this patient.</EmptyState>
        )}
      </Section>

      {/* ── 6. Imaging Intelligence ── */}
      <Section title="Imaging Intelligence (EfficientNetB0)" icon={FileImage}>
        {imaging_intelligence.available ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              <StatBox label="Model" value={imaging_intelligence.model_name?.replace(/_/g, " ") ?? "—"} />
              <StatBox
                label="Prediction"
                value={imaging_intelligence.prediction ?? "—"}
                alert={imaging_intelligence.prediction === "pneumonia"}
              />
              <StatBox
                label="Pneumonia Probability"
                value={imaging_intelligence.pneumonia_probability != null ? `${(imaging_intelligence.pneumonia_probability * 100).toFixed(1)}%` : "—"}
                alert={(imaging_intelligence.pneumonia_probability ?? 0) > 0.5}
              />
            </div>
            {imaging_intelligence.confidence != null && (
              <div className="rounded-md border-2 border-slate-300 bg-slate-50 px-3 py-2 text-xs font-bold text-slate-800">
                <span>Model Confidence: </span>
                <span className="font-extrabold tabular-nums">{(imaging_intelligence.confidence * 100).toFixed(1)}%</span>
              </div>
            )}

            {/* X-ray + Grad-CAM side by side */}
            <div className="grid gap-3 sm:grid-cols-2">
              {imaging_intelligence.xray_url && (
                <div>
                  <p className="mb-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-700">Original X-ray</p>
                  <div className="overflow-hidden rounded-lg border-2 border-slate-300 bg-black">
                    <img
                      src={imaging_intelligence.xray_url}
                      alt="Original chest X-ray"
                      className="block w-full"
                      loading="lazy"
                    />
                  </div>
                </div>
              )}
              {imaging_intelligence.gradcam_url && (
                <div>
                  <p className="mb-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-700">Grad-CAM Heatmap</p>
                  <div className="overflow-hidden rounded-lg border-2 border-slate-300 bg-black">
                    <img
                      src={imaging_intelligence.gradcam_url}
                      alt="Grad-CAM heatmap overlay"
                      className="block w-full"
                      loading="lazy"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <EmptyState>Imaging analysis has not been run for this patient.</EmptyState>
        )}
      </Section>

      {/* ── 7. Aggregation Engine ── */}
      <Section title="Aggregation Engine" icon={Layers}>
        {aggregation.available ? (
          <div className="space-y-4">
            {/* Primary condition + suppression */}
            <div className="flex items-center gap-3">
              <div className="rounded-md border-2 bg-primary/10 border-primary/30 px-4 py-2">
                <p className="text-[10px] font-bold text-slate-700">Primary Condition</p>
                <p className="text-lg font-bold text-primary">{aggregation.primary_condition ?? "—"}</p>
              </div>
              {aggregation.confidence_suppressed && (
                <div className="flex items-center gap-1.5 rounded-md border-2 border-amber-500 bg-amber-50 px-3 py-2 text-xs font-bold text-amber-800">
                  <AlertCircle className="h-3.5 w-3.5 shrink-0 text-amber-700" />
                  <span>Confidence Suppressed: {aggregation.suppression_reason ?? "insufficient evidence"}</span>
                </div>
              )}
            </div>

            {/* Probability bars */}
            <div className="space-y-2">
              <p className="text-xs font-bold text-slate-700">Condition Probabilities</p>
              {Object.entries(aggregation.probabilities).map(([condition, prob]) => (
                <div key={condition} className="flex items-center gap-3 text-sm">
                  <span className="w-28 shrink-0 font-bold text-slate-800">{condition}</span>
                  <div className="flex-1 h-3 overflow-hidden rounded-full bg-slate-200">
                    <div
                      className={cn(
                        "h-full rounded-full transition-all duration-700",
                        condition === aggregation.primary_condition ? "bg-primary" : "bg-slate-500",
                      )}
                      style={{ width: `${Math.max(prob * 100, 1)}%` }}
                    />
                  </div>
                  <span className="w-14 text-right font-mono font-bold tabular-nums text-xs text-slate-900">
                    {(prob * 100).toFixed(1)}%
                  </span>
                </div>
              ))}
            </div>

            {/* Source summary */}
            {Object.keys(aggregation.source_summary).length > 0 && (
              <div>
                <p className="mb-1.5 text-xs font-bold text-slate-700">Data Sources</p>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(aggregation.source_summary).map(([src, present]) => (
                    <span
                      key={src}
                      className={cn(
                        "rounded border-2 px-2 py-0.5 text-[10px] font-bold shadow-sm",
                        present
                          ? "border-emerald-400 bg-emerald-50 text-emerald-800"
                          : "border-slate-300 bg-slate-100 text-slate-600",
                      )}
                    >
                      {present ? "✓" : "✗"} {src.replace(/_/g, " ")}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <EmptyState>Aggregation has not been run for this patient.</EmptyState>
        )}
      </Section>

      {/* ── 8. Evidence Breakdown (Explainability) ── */}
      {aggregation.available && Object.keys(aggregation.evidence_breakdown).length > 0 && (
        <Section title="Evidence Breakdown (Explainability)" icon={FileText}>
          <div className="space-y-3">
            {Object.entries(aggregation.evidence_breakdown).map(([condition, items]) => (
              <div key={condition} className="rounded-md border-2 border-slate-300 bg-slate-50 p-3 shadow-sm">
                <p className="mb-2 text-xs font-bold text-slate-900">{condition}</p>
                <div className="space-y-1">
                  {(Array.isArray(items) ? items : []).map((item, i) => (
                    <div key={i} className="flex items-center gap-2 text-[11px] font-medium text-slate-700">
                      <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                      <span>{item}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* ── Evidence List ── */}
      {evidence.length > 0 && (
        <Section title={`Uploaded Evidence (${evidence.length})`} icon={FileText}>
          <div className="divide-y-2 divide-slate-200 rounded-md border-2 border-slate-300 bg-slate-50">
            {evidence.map((ev) => (
              <div key={ev.id} className="flex items-center gap-3 px-4 py-2.5 text-xs font-bold text-slate-800">
                <FileText className="h-3.5 w-3.5 shrink-0 text-slate-600" />
                <span className="flex-1 truncate">{ev.file_name}</span>
                <span className="rounded border-2 border-slate-350 bg-white px-1.5 py-px text-[9px] uppercase tracking-wider text-slate-700 shadow-sm">
                  {ev.evidence_type}
                </span>
                {ev.file_url && (
                  <a
                    href={ev.file_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline font-bold"
                  >
                    View
                  </a>
                )}
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* ── Footer ── */}
      <div className="border-t pt-3 text-center text-[10px] font-semibold text-slate-600">
        <p>PRATHAM Clinical Intelligence Report · Generated {new Date(report.generated_at).toLocaleString()}</p>
        <p className="mt-0.5 text-rose-800 font-bold">⚠ This is an AI-assisted analysis. Not a substitute for clinical judgment.</p>
      </div>
    </div>
  );
}

// ── Subcomponents ────────────────────────────────────────────────────────

function VitalCard({ icon: Icon, label, value, alert }: { icon: typeof Heart; label: string; value: string; alert?: boolean }) {
  return (
    <div className={cn("rounded-md border-2 p-3 shadow-sm", alert ? "border-rose-500 bg-rose-50/50" : "border-slate-300 bg-slate-50")}>
      <div className="flex items-center gap-1.5">
        <Icon className={cn("h-3.5 w-3.5", alert ? "text-rose-700 font-bold" : "text-slate-650")} />
        <p className="text-[10px] font-bold text-slate-700">{label}</p>
      </div>
      <p className={cn("mt-1 text-lg font-extrabold tabular-nums", alert ? "text-rose-700" : "text-slate-900")}>
        {value}
      </p>
    </div>
  );
}

function StatBox({ label, value, alert }: { label: string; value: string; alert?: boolean }) {
  return (
    <div className="rounded-md border-2 border-slate-300 bg-slate-50 p-3 shadow-sm">
      <p className="text-[10px] font-bold text-slate-700">{label}</p>
      <p className={cn("mt-1 text-sm font-bold", alert ? "text-rose-700" : "text-slate-900")}>{value}</p>
    </div>
  );
}

function EmptyState({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-md border-2 border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-center text-xs font-bold text-slate-800">
      {children}
    </div>
  );
}
