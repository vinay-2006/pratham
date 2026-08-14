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
import { useState } from "react";
import axios from "axios";
import {
  Activity,
  Thermometer,
  Wind,
  Heart,
  Droplets,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Clock,
} from "lucide-react";
import { InvestigationUploadRow } from "./investigation-upload-row";
import type { InvestigationRow } from "./investigation-upload-row";
import { PipelineStatus } from "./pipeline-status";
import { PatientTimeline } from "./patient-timeline";
import { cn } from "@/lib/utils";
import { Plus, Check, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { API_BASE } from "@/lib/api-config";

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
  critical: "text-rose-800 dark:text-rose-300 bg-rose-100 dark:bg-rose-950/60 border-rose-300 dark:border-rose-700",
  high: "text-orange-800 dark:text-orange-300 bg-orange-100 dark:bg-orange-950/60 border-orange-300 dark:border-orange-700",
  moderate: "text-amber-800 dark:text-amber-300 bg-amber-100 dark:bg-amber-950/60 border-amber-300 dark:border-amber-700",
  low: "text-emerald-800 dark:text-emerald-300 bg-emerald-100 dark:bg-emerald-950/60 border-emerald-300 dark:border-emerald-700",
};

function riskColor(value: number): string {
  if (value >= 70) return "text-rose-700 dark:text-rose-400";
  if (value >= 50) return "text-orange-700 dark:text-orange-400";
  if (value >= 30) return "text-amber-700 dark:text-amber-400";
  return "text-emerald-700 dark:text-emerald-400";
}

export function PatientWorkspace({ intakeId }: Props) {
  const queryClient = useQueryClient();
  const [newInvName, setNewInvName] = useState("");
  const [isAdding, setIsAdding] = useState(false);

  const handleAddInvestigation = async () => {
    const val = newInvName.trim();
    if (!val) return;
    setIsAdding(true);
    try {
      await axios.post(`${API_BASE}/investigations/add`, {
        intake_id: intakeId,
        investigation_name: val,
        doctor_name: "Doctor",
        doctor_notes: "Added via Workspace"
      });
      toast.success("Investigation added", {
        description: `Successfully added and approved "${val}".`
      });
      setNewInvName("");
      refetch();
    } catch (error) {
      console.error("[PRATHAM] Add investigation failed:", error);
      toast.error("Failed to add", {
        description: axios.isAxiosError(error)
          ? error.response?.data?.detail ?? error.message
          : "Unexpected error — please retry."
      });
    } finally {
      setIsAdding(false);
    }
  };

  const { data, isLoading, isError, error, refetch: refetchDetail } = useQuery({
    queryKey: ["patient-detail", intakeId],
    queryFn: () => fetchPatientDetail(intakeId),
    staleTime: 5_000,  // short stale time — evidence uploads need fast refresh
    retry: 2,
  });

  const refetch = () => {
    // Force immediate refetch of all related queries — not just invalidate
    queryClient.refetchQueries({ queryKey: ["patient-detail", intakeId] });
    queryClient.refetchQueries({ queryKey: ["patient-queue"] });
    queryClient.invalidateQueries({ queryKey: ["clinical-report"] });
  };

  if (isLoading) {
    return (
      <div className="space-y-6 py-6 animate-pulse">
        {/* Vitals Skeleton */}
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-14 rounded-xl bg-slate-100 dark:bg-slate-800" />
          ))}
        </div>
        {/* Symptoms Skeleton */}
        <div className="space-y-2">
          <div className="h-4 w-24 bg-slate-200 dark:bg-slate-700 rounded" />
          <div className="flex gap-2 flex-wrap">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-8 w-20 bg-slate-100 dark:bg-slate-800 rounded-full" />
            ))}
          </div>
        </div>
        {/* Investigations Skeleton */}
        <div className="space-y-3">
          <div className="h-4 w-32 bg-slate-200 dark:bg-slate-700 rounded" />
          {[...Array(2)].map((_, i) => (
            <div key={i} className="h-16 rounded-xl bg-slate-100 dark:bg-slate-800" />
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-5 text-sm text-rose-800 dark:text-rose-400 space-y-3">
        <div className="flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-500" />
          <span className="font-bold">Failed to load patient data</span>
        </div>
        <p className="text-xs text-rose-600 dark:text-rose-400/80">
          {axios.isAxiosError(error)
            ? error.response?.data?.detail ?? error.message
            : "An unexpected error occurred while querying the server."}
        </p>
        <Button
          size="sm"
          variant="outline"
          onClick={() => refetchDetail()}
          className="border-rose-500/30 hover:bg-rose-500/10 text-rose-700 dark:text-rose-300 font-semibold"
        >
          Retry Load
        </Button>
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
                className="rounded-full border-2 border-slate-300 dark:border-slate-600 bg-slate-100 dark:bg-slate-700/50 px-2.5 py-0.5 text-[11px] font-bold text-slate-800 dark:text-gray-200"
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
            <span className="text-slate-700 dark:text-gray-300 font-bold">{label}</span>
            <span className={cn("font-bold tabular-nums", riskColor(value))}>{value}%</span>
          </div>
        ))}
      </div>

      {/* ── Evidence completeness ─────────────────────────────── */}
      {evidence_completeness.required > 0 && (
        <div className="rounded-lg border-2 border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800/50 p-3">
          <div className="mb-2 flex items-center justify-between text-xs">
            <span className="font-bold text-slate-800 dark:text-gray-200">Evidence completeness</span>
            <span
              className={cn(
                "font-extrabold tabular-nums",
                completenessPercent === 100 ? "text-emerald-700" : "text-amber-700",
              )}
            >
              {evidence_completeness.uploaded} / {evidence_completeness.required} uploaded
            </span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
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


      {/* ── Investigations ────────────────────────────────────── */}
      <div>
        <h3 className="mb-3 text-[11px] font-bold uppercase tracking-[0.15em] text-slate-800 dark:text-gray-200">
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
            <p className="rounded-lg border-2 border-dashed border-slate-300 dark:border-slate-600 p-6 text-center text-xs font-semibold text-slate-800 dark:text-gray-200 bg-slate-50 dark:bg-slate-800/50">
              No investigations yet — doctor approval pending.
            </p>
          )}
        </div>

        {/* Add Manual Investigation inline form */}
        <div className="mt-4 flex flex-col gap-2 rounded-lg border bg-muted/20 p-4">
          <h4 className="text-xs font-semibold text-foreground">
            Add New Investigation
          </h4>
          <div className="flex gap-2">
            <Input
              value={newInvName}
              onChange={(e) => setNewInvName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !isAdding) {
                  handleAddInvestigation();
                }
              }}
              placeholder="e.g. CBC, Troponin, MRI Brain..."
              className="h-9 text-xs"
              disabled={isAdding}
            />
            <Button
              onClick={handleAddInvestigation}
              disabled={isAdding || !newInvName.trim()}
              size="sm"
              className="h-9 shrink-0 px-4 text-xs font-semibold"
            >
              {isAdding ? (
                <>
                  <Loader2 className="mr-1.5 h-3 w-3 animate-spin" />
                  Adding...
                </>
              ) : (
                <>
                  <Plus className="mr-1.5 h-3.5 w-3.5" />
                  Add Test
                </>
              )}
            </Button>
          </div>
          <p className="text-[10px] text-muted-foreground leading-normal">
            Supported investigations (CBC, ECG, BMP, Chest X-ray, Blood Glucose, Urinalysis, Troponin, etc.) will have full upload and AI analysis capabilities. Others will be approved for documentation only.
          </p>
        </div>
      </div>

      {/* Patient Timeline */}
      <TimelineSection intakeId={intakeId} />
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
        alert ? "border-rose-500 dark:border-rose-700 bg-rose-50/50 dark:bg-rose-950/40" : "border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800/50",
      )}
    >
      <Icon className={cn("h-3.5 w-3.5 shrink-0", alert ? "text-rose-700 dark:text-rose-400 font-bold" : "text-slate-700 dark:text-gray-400")} />
      <div className="min-w-0">
        <p className="text-[10px] font-bold text-slate-700 dark:text-gray-300">{label}</p>
        <p className={cn("font-extrabold tabular-nums text-sm", alert ? "text-rose-700 dark:text-rose-400" : "text-slate-900 dark:text-gray-50")}>
          {value}
        </p>
      </div>
    </div>
  );
}

function TimelineSection({ intakeId }: { intakeId: string }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="mt-6 rounded-lg border-2 border-slate-300 dark:border-slate-600 overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-4 py-3 text-left bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
      >
        <span className="flex items-center gap-2 text-xs font-bold text-slate-800 dark:text-gray-200">
          <Clock className="h-3.5 w-3.5 text-slate-600 dark:text-gray-400" />
          Patient Timeline
        </span>
        {open ? (
          <ChevronUp className="h-3.5 w-3.5 text-slate-600 dark:text-gray-400" />
        ) : (
          <ChevronDown className="h-3.5 w-3.5 text-slate-600 dark:text-gray-400" />
        )}
      </button>
      {open && (
        <div className="border-t border-slate-200 dark:border-slate-700 px-4 py-3">
          <PatientTimeline intakeId={intakeId} />
        </div>
      )}
    </div>
  );
}

