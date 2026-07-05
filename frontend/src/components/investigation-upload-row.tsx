/**
 * InvestigationUploadRow — Clinical Investigation Card
 *
 * For each investigation, renders:
 *  - Status badge (approved / rejected / pending_approval / needs_info)
 *  - Evidence type label (ecg / xray / lab_report / clinical_notes)
 *  - Drag-and-drop upload zone
 *  - Uploaded files with View / Replace / Delete actions
 *  - "Run Analysis" button for xray / lab_report evidence types
 *  - Inline analysis results when available
 */

import { useRef, useState } from "react";
import axios from "axios";
import {
  CheckCircle2,
  Clock,
  FileText,
  Upload,
  XCircle,
  AlertCircle,
  Loader2,
  ExternalLink,
  FlaskConical,
  Trash2,
  Play,
  Brain,
  TrendingUp,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

const API_BASE = "http://localhost:8000/api";

export interface EvidenceFile {
  evidence_id: string;
  file_name: string;
  file_url: string;
  uploaded_at: string;
}

export interface AnalysisResult {
  type: "imaging" | "lab";
  model_name: string;
  prediction: string;
  probability: number;
  confidence?: number;
  top_features?: Record<string, number>;
  gradcam_url?: string;
  created_at: string;
}

export interface InvestigationRow {
  id: string;
  investigation_type: string;
  evidence_type: string;
  status: "approved" | "rejected" | "pending_approval" | "needs_info";
  progress: "awaiting_upload" | "uploaded" | null;
  approved_at: string | null;
  rejected_at: string | null;
  review_notes: string | null;
  evidence: EvidenceFile[];
  analysis_result?: AnalysisResult | null;
  analysis_status?: string;
}

interface Props {
  intakeId: string;
  investigation: InvestigationRow;
  onUploaded: () => void;
}

const EVIDENCE_TYPE_LABELS: Record<string, string> = {
  ecg: "ECG",
  xray: "Imaging",
  lab_report: "Lab Report",
  clinical_notes: "Clinical Notes",
};

const EVIDENCE_TYPE_COLORS: Record<string, string> = {
  ecg: "bg-violet-100 dark:bg-violet-950/60 text-violet-800 dark:text-violet-300 border-violet-300 dark:border-violet-700",
  xray: "bg-sky-100 dark:bg-sky-950/60 text-sky-800 dark:text-sky-300 border-sky-300 dark:border-sky-700",
  lab_report: "bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 border-amber-300 dark:border-amber-700",
  clinical_notes: "bg-slate-100 dark:bg-slate-700/50 text-slate-800 dark:text-gray-200 border-slate-300 dark:border-slate-600",
};

/** Format an ISO timestamp → "14 Jun 2026 · 11:31 AM" */
function formatUploadedAt(iso: string): string {
  try {
    const d = new Date(iso);
    const date = d.toLocaleDateString("en-GB", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
    const time = d.toLocaleTimeString("en-GB", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    });
    return `${date} · ${time.toUpperCase()}`;
  } catch {
    return iso;
  }
}

export function InvestigationUploadRow({ intakeId, investigation, onUploaded }: Props) {
  const { id, investigation_type, evidence_type, status, progress, review_notes, evidence, analysis_result, analysis_status } =
    investigation;

  const [uploading, setUploading] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const isApproved = status === "approved";
  const isRejected = status === "rejected";
  const isPending = status === "pending_approval";
  const isNeedsInfo = status === "needs_info";
  const hasFiles = evidence.length > 0;

  const handleFile = async (file: File) => {
    if (!file) return;
    setUploading(true);
    try {
      // In Replace mode: delete all existing evidence for this investigation first
      if (hasFiles) {
        await Promise.all(
          evidence.map((ev) =>
            axios.delete(`${API_BASE}/evidence/${ev.evidence_id}`).catch(() => {
              // Non-fatal: continue with upload even if delete partially fails
            })
          )
        );
      }

      const formData = new FormData();
      formData.append("intake_id", intakeId);
      formData.append("evidence_type", evidence_type);
      formData.append("investigation_id", id);
      formData.append("file", file);

      await axios.post(`${API_BASE}/evidence/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      toast.success(hasFiles ? "Evidence replaced" : "Evidence uploaded", {
        description: `${file.name} linked to ${investigation_type}.`,
      });
      onUploaded();
    } catch (err) {
      toast.error("Upload failed", {
        description: axios.isAxiosError(err)
          ? err.response?.data?.detail ?? err.message
          : "An unexpected error occurred.",
      });
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (evidenceId: string, fileName: string) => {
    const confirmed = window.confirm(`Are you sure you want to delete the evidence file "${fileName}"?`);
    if (!confirmed) return;

    setDeleting(evidenceId);
    try {
      await axios.delete(`${API_BASE}/evidence/${evidenceId}`);
      toast.success("Evidence deleted", {
        description: `${fileName} removed from ${investigation_type}.`,
      });
      onUploaded();
    } catch (err) {
      toast.error("Delete failed", {
        description: axios.isAxiosError(err)
          ? err.response?.data?.detail ?? err.message
          : "An unexpected error occurred.",
      });
    } finally {
      setDeleting(null);
    }
  };

  const SUPPORTED_INVESTIGATIONS = [
    "Chest X-ray", "CT Brain", "CT Chest", "Echocardiogram", "FAST Ultrasound",
    "CBC", "Basic Metabolic Panel", "Urinalysis", "Blood Glucose", "Troponin",
    "ABG", "D-Dimer", "Cardiac Enzymes", "Coagulation Profile", "Blood Group & Cross-match", "Electrolytes"
  ];
  const isSupported = SUPPORTED_INVESTIGATIONS.includes(investigation_type);
  const canAnalyze = isApproved && hasFiles && !analysis_result && isSupported && (evidence_type === "xray" || evidence_type === "lab_report");

  const handleRunAnalysis = async () => {
    setAnalyzing(true);
    try {
      if (evidence_type === "xray") {
        const xrayEvidence = evidence[0];
        await axios.post(`${API_BASE}/imaging/analyze`, {
          intake_id: intakeId,
          evidence_id: xrayEvidence.evidence_id,
        });
        toast.success("Imaging analysis complete", {
          description: "Chest imaging classification finished.",
        });
      } else if (evidence_type === "lab_report") {
        await axios.post(`${API_BASE}/lab/analyze`, {
          intake_id: intakeId,
        });
        toast.success("Lab analysis complete", {
          description: "Laboratory risk evaluation finished.",
        });
      }
      onUploaded();
    } catch (err) {
      toast.error("Analysis failed", {
        description: axios.isAxiosError(err)
          ? err.response?.data?.detail ?? err.message
          : "An unexpected error occurred.",
      });
    } finally {
      setAnalyzing(false);
    }
  };

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    e.target.value = "";
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  return (
    <div
      className={cn(
        "rounded-lg border-2 p-4 transition-colors",
        isApproved && "border-emerald-500/30 bg-emerald-500/5",
        isRejected && "border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800/50 opacity-80",
        isPending && "border-slate-300 dark:border-slate-600 bg-card",
        isNeedsInfo && "border-amber-500/30 bg-amber-500/5",
      )}
    >
      {/* ── Header row ─────────────────────────────────────────── */}
      <div className="flex items-start gap-3">
        {/* Status icon */}
        <div className="mt-0.5 shrink-0">
          {isApproved && progress === "uploaded" && (
            <CheckCircle2 className="h-[18px] w-[18px] text-emerald-600" />
          )}
          {isApproved && progress === "awaiting_upload" && (
            <Clock className="h-[18px] w-[18px] text-amber-600" />
          )}
          {isRejected && <XCircle className="h-[18px] w-[18px] text-rose-600" />}
          {isPending && <Clock className="h-[18px] w-[18px] text-slate-500 dark:text-slate-400" />}
          {isNeedsInfo && <AlertCircle className="h-[18px] w-[18px] text-amber-600" />}
        </div>

        {/* Name + badges */}
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={cn(
                "font-semibold text-sm text-slate-900 dark:text-gray-50",
                isRejected && "text-slate-500 dark:text-slate-400 line-through",
              )}
            >
              {investigation_type}
            </span>
            {/* Evidence type pill */}
            <span
              className={cn(
                "rounded border px-1.5 py-px text-[10px] font-bold uppercase tracking-wider",
                EVIDENCE_TYPE_COLORS[evidence_type] ?? EVIDENCE_TYPE_COLORS.clinical_notes,
              )}
            >
              {EVIDENCE_TYPE_LABELS[evidence_type] ?? evidence_type}
            </span>
            {/* Analysis status pill */}
            {analysis_status === "completed" && (
              <span className="rounded border border-emerald-500/30 bg-emerald-50 dark:bg-emerald-950/50 px-1.5 py-px text-[10px] font-bold uppercase tracking-wider text-emerald-800 dark:text-emerald-300">
                Analyzed
              </span>
            )}
          </div>

          {/* Status sub-text */}
          <p className="mt-0.5 text-[11px] text-slate-700 dark:text-gray-300 font-medium">
            {isApproved && progress === "uploaded" && "Evidence uploaded ✓"}
            {isApproved && progress === "awaiting_upload" && "Awaiting upload"}
            {isRejected && (review_notes ? `Rejected — ${review_notes}` : "Rejected by doctor")}
            {isPending && "Pending doctor approval"}
            {isNeedsInfo && "Doctor requested more info"}
          </p>
        </div>

        {/* Upload / Replace button */}
        {isApproved && !uploading && (
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            className={cn(
              "flex shrink-0 items-center gap-1.5 rounded-md border-2 px-3 py-1.5 text-xs font-bold transition-all shadow-sm",
              hasFiles
                ? "border-slate-300 dark:border-slate-600 bg-slate-100 dark:bg-slate-700/50 text-slate-800 dark:text-gray-200 hover:border-slate-400 hover:bg-slate-200 dark:hover:bg-slate-600 hover:text-slate-900 dark:hover:text-gray-50"
                : "border-emerald-600 bg-emerald-600 text-white hover:bg-emerald-700 hover:border-emerald-700",
            )}
          >
            <Upload className="h-3.5 w-3.5" />
            {hasFiles ? "Replace" : "Upload"}
          </button>
        )}
        {uploading && (
          <div className="flex shrink-0 items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 dark:text-gray-300">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            Uploading…
          </div>
        )}

        <input
          ref={fileRef}
          type="file"
          className="hidden"
          accept=".jpg,.jpeg,.png,.pdf,.txt"
          onChange={onInputChange}
        />
      </div>

      {/* ── Drag & drop zone ── */}
      {isApproved && (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          onClick={() => fileRef.current?.click()}
          className={cn(
            "mt-3 flex cursor-pointer flex-col items-center justify-center gap-1.5 rounded-md border-2 border-dashed py-4 text-xs font-semibold text-slate-800 dark:text-gray-200 transition-colors",
            dragOver
              ? "border-emerald-600 bg-emerald-50 dark:bg-emerald-950/40"
              : "border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800/50 hover:border-emerald-600 hover:bg-emerald-50/50 dark:hover:bg-emerald-950/30",
          )}
        >
          <Upload className="h-4 w-4 text-slate-700 dark:text-gray-300" />
          <span>
            {hasFiles ? (
              <>Drop to replace or <span className="text-primary hover:underline">browse</span></>
            ) : (
              <>Drop file here or <span className="text-emerald-700 hover:underline">browse</span></>
            )}
          </span>
          <span className="text-[10px] text-slate-600 dark:text-gray-400 font-medium">JPG · PNG · PDF · TXT · max 10 MB</span>
        </div>
      )}

      {/* ── Existing uploaded files with View / Delete actions ── */}
      {hasFiles && (
        <ul className="mt-3 space-y-2">
          {evidence.map((ev) => (
            <li
              key={ev.evidence_id}
              className="rounded-md border-2 border-slate-300 dark:border-slate-600 bg-background px-3 py-2.5"
            >
              <div className="flex items-center gap-2">
                <FileText className="h-3.5 w-3.5 shrink-0 text-slate-700 dark:text-gray-400" />
                <span className="min-w-0 flex-1 truncate text-xs font-bold text-slate-900 dark:text-gray-50">
                  {ev.file_name}
                </span>
                <div className="flex shrink-0 items-center gap-1.5">
                  {/* View */}
                  {ev.file_url && (
                    <a
                      href={ev.file_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="rounded border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/50 p-1.5 text-slate-700 dark:text-gray-300 transition-colors hover:bg-slate-200 dark:hover:bg-slate-600 hover:text-slate-900 dark:hover:text-gray-50"
                      title="View file"
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                  )}
                  {/* Delete */}
                  <button
                    type="button"
                    onClick={() => handleDelete(ev.evidence_id, ev.file_name)}
                    disabled={deleting === ev.evidence_id}
                    className="rounded border border-rose-200 bg-rose-50 p-1.5 text-rose-700 transition-colors hover:bg-rose-100 hover:text-rose-900 disabled:opacity-50"
                    title="Delete file"
                  >
                    {deleting === ev.evidence_id ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <Trash2 className="h-3.5 w-3.5" />
                    )}
                  </button>
                </div>
              </div>
              {/* Full upload timestamp — audit trail */}
              {ev.uploaded_at && (
                <p className="mt-1 pl-5 text-[10px] font-semibold text-slate-600 dark:text-gray-400">
                  Uploaded: {formatUploadedAt(ev.uploaded_at)}
                </p>
              )}
            </li>
          ))}
        </ul>
      )}

      {/* ── Run Analysis button ── */}
      {canAnalyze && (
        <button
          type="button"
          onClick={handleRunAnalysis}
          disabled={analyzing}
          className={cn(
            "mt-3 flex w-full items-center justify-center gap-2 rounded-md border-2 py-2.5 text-xs font-bold transition-all shadow-sm",
            analyzing
              ? "border-slate-300 dark:border-slate-600 bg-slate-100 dark:bg-slate-700/50 text-slate-500 dark:text-slate-400"
              : "border-primary bg-primary text-white hover:bg-primary/90",
          )}
        >
          {analyzing ? (
            <>
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Running AI Analysis…
            </>
          ) : (
            <>
              <Play className="h-3.5 w-3.5" />
              Run {evidence_type === "xray" ? "Imaging" : "Lab"} Analysis
            </>
          )}
        </button>
      )}

      {/* ── Inline Analysis Results ── */}
      {analysis_result && (
        <div className="mt-3 rounded-md border-2 border-primary/40 bg-primary/5 px-3 py-3">
          <div className="flex items-center gap-2 mb-2">
            <Brain className="h-3.5 w-3.5 text-primary" />
            <span className="text-[11px] font-bold text-primary">
              AI Analysis Results
            </span>
            <span className="ml-auto text-[10px] font-semibold text-slate-700 dark:text-gray-300">
              {analysis_result.model_name?.replace(/_/g, " ")}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="rounded border-2 border-slate-300 dark:border-slate-600 bg-background px-2.5 py-1.5">
              <p className="text-[10px] font-bold text-slate-600 dark:text-gray-400">Prediction</p>
              <p className={cn(
                "text-xs font-bold capitalize",
                analysis_result.prediction === "pneumonia" || analysis_result.prediction === "high_risk"
                  ? "text-rose-700"
                  : "text-emerald-700"
              )}>
                {analysis_result.prediction?.replace(/_/g, " ")}
              </p>
            </div>
            <div className="rounded border-2 border-slate-300 dark:border-slate-600 bg-background px-2.5 py-1.5">
              <p className="text-[10px] font-bold text-slate-600 dark:text-gray-400">Probability</p>
              <p className="text-xs font-bold tabular-nums text-slate-900 dark:text-gray-50">
                {((analysis_result.probability ?? 0) * 100).toFixed(1)}%
              </p>
            </div>
          </div>

          {/* SHAP top features for lab results */}
          {analysis_result.type === "lab" && analysis_result.top_features && (
            <div className="mt-2">
              <p className="text-[10px] font-bold text-slate-700 dark:text-gray-300 mb-1 flex items-center gap-1">
                <TrendingUp className="h-3 w-3" /> Top Contributors
              </p>
              <div className="space-y-1">
                {Object.entries(analysis_result.top_features).slice(0, 3).map(([feat, val]) => (
                  <div key={feat} className="flex items-center gap-2 text-[10px]">
                    <span className="flex-1 truncate font-medium text-slate-700 dark:text-gray-300">{feat.replace(/_/g, " ")}</span>
                    <span className={cn("font-mono font-bold tabular-nums", Number(val) > 0 ? "text-rose-700" : "text-emerald-700")}>
                      {Number(val) > 0 ? "+" : ""}{Number(val).toFixed(3)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {analysis_result.created_at && (
            <p className="mt-2 text-[9px] font-semibold text-slate-600 dark:text-gray-400">
              Generated: {formatUploadedAt(analysis_result.created_at)}
            </p>
          )}
        </div>
      )}

      {/* ── No analysis placeholder (only for non-analyzable / unsupported types) ── */}
      {isApproved && !analysis_result && !canAnalyze && (
        <div className="mt-3 rounded-md border-2 border-dashed border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800/50 px-3 py-2.5">
          <div className="flex items-center gap-2">
            <FlaskConical className="h-3.5 w-3.5 shrink-0 text-slate-700 dark:text-gray-400" />
            <span className="text-[11px] font-bold text-slate-800 dark:text-gray-200">
              Analysis Status
            </span>
            <span className="ml-auto rounded border-2 border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700/50 px-1.5 py-px text-[9px] font-bold uppercase tracking-wider text-slate-700 dark:text-gray-300">
              Approved
            </span>
          </div>
          <p className="mt-1 pl-5 text-[10px] font-medium text-slate-700 dark:text-gray-400">
            {!isSupported ? "Analysis not available in this version" : "No AI analysis model available for this file type."}
          </p>
        </div>
      )}
    </div>
  );
}
