/**
 * PatientWorkspace
 *
 * Full expanded workspace for a single patient inside the Patient Queue.
 * Fetches GET /api/investigations/patient/{intakeId} and renders:
 *   - Vitals strip
 *   - Symptoms chips
 *   - Risk badges
 *   - Per-investigation list with upload controls
 *   - Evidence completeness indicator
 */

import { useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import {
  Activity,
  Thermometer,
  Wind,
  Heart,
  Droplets,
  AlertCircle,
} from "lucide-react";
import { InvestigationUploadRow } from "./investigation-upload-row";
import type { InvestigationRow } from "./investigation-upload-row";
import { PipelineStatus } from "./pipeline-status";
import { cn } from "@/lib/utils";

const API_BASE = "http://localhost:8000/api";

interface PatientDetail {
  intake_id: string;
  intake_status: string;
  patient: {
    name: string;
    age: number;
    sex: "M" | "F";
    arrival_time: string;
    eta: string;
    contact: string | null;
  };
  vitals: {
    heart_rate: number | null;
    spo2: number | null;
    blood_pressure: string;
    respiratory_rate: number | null;
    temperature: number | null;
  };
  symptoms: string[];
  risk: {
    severity: string;
    cardiac: number;
    respiratory: number;
    trauma: number;
    neurological: number;
  };
  investigations: InvestigationRow[];
  pipeline_status: {
    nlp: string;
    risk: string;
    lab: string;
    imaging: string;
    aggregation: string;
  };
  evidence_completeness: {
    uploaded: number;
    required: number;
    label: string;
  };
}

async function fetchPatientDetail(intakeId: string): Promise<PatientDetail> {
  const res = await axios.get(`${API_BASE}/investigations/patient/${intakeId}`);
  return res.data;
}

interface Props {
  intakeId: string;
}

const RISK_COLORS: Record<string, string> = {
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

export function PatientWorkspace({ intakeId }: Props) {
  const queryClient = useQueryClient();

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["patient-detail", intakeId],
    queryFn: () => fetchPatientDetail(intakeId),
    staleTime: 5_000,  // short stale time — evidence uploads need fast refresh
  });

  const refetch = () => {
    // Force immediate refetch of all related queries — not just invalidate
    queryClient.refetchQueries({ queryKey: ["patient-detail", intakeId] });
    queryClient.refetchQueries({ queryKey: ["patient-queue"] });
    queryClient.invalidateQueries({ queryKey: ["clinical-report"] });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Activity className="h-4 w-4 animate-pulse text-primary" />
          Loading patient data…
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-rose-500/20 bg-rose-500/5 p-4 text-sm text-rose-400">
        <AlertCircle className="h-4 w-4 shrink-0" />
        {axios.isAxiosError(error)
          ? error.response?.data?.detail ?? "Failed to load patient data."
          : "Failed to load patient data."}
      </div>
    );
  }

  if (!data) return null;

  const { patient, vitals, symptoms, risk, investigations, pipeline_status, evidence_completeness } = data;

  const approved = investigations.filter((i) => i.status === "approved");
  const rejected = investigations.filter((i) => i.status === "rejected");
  const pending = investigations.filter(
    (i) => i.status !== "approved" && i.status !== "rejected",
  );

  const completenessPercent =
    evidence_completeness.required > 0
      ? Math.round((evidence_completeness.uploaded / evidence_completeness.required) * 100)
      : 0;

  return (
    <div className="space-y-5 pt-2">
      {/* ── Vitals strip ──────────────────────────────────────── */}
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5">
        <VitalChip
          icon={Heart}
          label="HR"
          value={vitals.heart_rate != null ? `${vitals.heart_rate} bpm` : "—"}
          alert={(vitals.heart_rate ?? 0) > 100 || (vitals.heart_rate ?? 999) < 50}
        />
        <VitalChip
          icon={Droplets}
          label="SpO₂"
          value={vitals.spo2 != null ? `${vitals.spo2}%` : "—"}
          alert={(vitals.spo2 ?? 100) < 94}
        />
        <VitalChip
          icon={Activity}
          label="BP"
          value={vitals.blood_pressure || "—"}
        />
        <VitalChip
          icon={Wind}
          label="RR"
          value={vitals.respiratory_rate != null ? `${vitals.respiratory_rate}/min` : "—"}
          alert={(vitals.respiratory_rate ?? 0) > 20}
        />
        <VitalChip
          icon={Thermometer}
          label="Temp"
          value={vitals.temperature != null ? `${vitals.temperature}°C` : "—"}
          alert={(vitals.temperature ?? 0) > 38}
        />
      </div>

      {/* ── Symptoms + Risk ───────────────────────────────────── */}
      <div className="grid gap-4 lg:grid-cols-[1fr_auto]">
        {/* Symptoms */}
        {symptoms.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {symptoms.map((s) => (
              <span
                key={s}
                className="rounded-full border-2 border-slate-300 bg-slate-100 px-2.5 py-0.5 text-[11px] font-bold text-slate-800"
              >
                {s}
              </span>
            ))}
          </div>
        )}

        {/* Severity badge */}
        <span
          className={cn(
            "self-start rounded-md border-2 px-2.5 py-1 text-xs font-bold uppercase tracking-wider shadow-sm",
            RISK_COLORS[risk.severity] ?? RISK_COLORS.moderate,
          )}
        >
          {risk.severity}
        </span>
      </div>

      {/* Risk scores (compact) */}
      <div className="grid grid-cols-2 gap-x-6 gap-y-1.5 sm:grid-cols-4">
        {[
          { label: "Cardiac", value: risk.cardiac },
          { label: "Respiratory", value: risk.respiratory },
          { label: "Trauma", value: risk.trauma },
          { label: "Neuro", value: risk.neurological },
        ].map(({ label, value }) => (
          <div key={label} className="flex items-center justify-between text-xs">
            <span className="text-slate-700 font-bold">{label}</span>
            <span className={cn("font-bold tabular-nums", riskColor(value))}>{value}%</span>
          </div>
        ))}
      </div>

      {/* ── Evidence completeness ─────────────────────────────── */}
      {evidence_completeness.required > 0 && (
        <div className="rounded-lg border-2 border-slate-300 bg-slate-50 p-3">
          <div className="mb-2 flex items-center justify-between text-xs">
            <span className="font-bold text-slate-800">Evidence completeness</span>
            <span
              className={cn(
                "font-extrabold tabular-nums",
                completenessPercent === 100 ? "text-emerald-700" : "text-amber-700",
              )}
            >
              {evidence_completeness.uploaded} / {evidence_completeness.required} uploaded
            </span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-slate-200">
            <div
              className={cn(
                "h-full rounded-full transition-all duration-500",
                completenessPercent === 100 ? "bg-emerald-600" : "bg-amber-600",
              )}
              style={{ width: `${completenessPercent}%` }}
            />
          </div>
        </div>
      )}

      {/* ── AI Pipeline Status ─────────────────────────────────── */}
      {pipeline_status && (
        <div className="rounded-lg border-2 border-slate-300 bg-slate-50 p-3">
          <div className="mb-2 text-[11px] font-bold uppercase tracking-[0.15em] text-slate-800">
            AI Pipeline Status
          </div>
          <PipelineStatus status={pipeline_status} />
        </div>
      )}

      {/* ── Investigations ────────────────────────────────────── */}
      <div>
        <h3 className="mb-3 text-[11px] font-bold uppercase tracking-[0.15em] text-slate-800">
          Investigations
        </h3>

        <div className="space-y-2.5">
          {/* Approved first */}
          {approved.map((inv) => (
            <InvestigationUploadRow
              key={inv.id}
              intakeId={intakeId}
              investigation={inv}
              onUploaded={refetch}
            />
          ))}

          {/* Pending */}
          {pending.map((inv) => (
            <InvestigationUploadRow
              key={inv.id}
              intakeId={intakeId}
              investigation={inv}
              onUploaded={refetch}
            />
          ))}

          {/* Rejected last */}
          {rejected.map((inv) => (
            <InvestigationUploadRow
              key={inv.id}
              intakeId={intakeId}
              investigation={inv}
              onUploaded={refetch}
            />
          ))}

          {investigations.length === 0 && (
            <p className="rounded-lg border-2 border-dashed border-slate-300 p-6 text-center text-xs font-semibold text-slate-800 bg-slate-50">
              No investigations yet — doctor approval pending.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

function VitalChip({
  icon: Icon,
  label,
  value,
  alert,
}: {
  icon: typeof Heart;
  label: string;
  value: string;
  alert?: boolean;
}) {
  return (
    <div
      className={cn(
        "flex items-center gap-2 rounded-md border-2 px-3 py-2 text-xs shadow-sm",
        alert ? "border-rose-500 bg-rose-50/50" : "border-slate-300 bg-slate-50",
      )}
    >
      <Icon className={cn("h-3.5 w-3.5 shrink-0", alert ? "text-rose-700 font-bold" : "text-slate-700")} />
      <div className="min-w-0">
        <p className="text-[10px] font-bold text-slate-700">{label}</p>
        <p className={cn("font-extrabold tabular-nums text-sm", alert ? "text-rose-700" : "text-slate-900")}>
          {value}
        </p>
      </div>
    </div>
  );
}
