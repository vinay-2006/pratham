/**
 * PipelineStatus — Visual 5-step AI pipeline indicator
 *
 * Shows the status of each subsystem with duration and error info:
 *   NLP → Risk → Lab → Imaging → Aggregation
 *
 * Status display:
 *   🟡 Pending  ·  🔵 Running  ·  🟢 Completed  ·  🔴 Failed
 *
 * Dark-mode aware: all colors use dark: variants for WCAG AA contrast.
 */

import { cn } from "@/lib/utils";
import type { StageStatus } from "@/lib/report-api";
import {
  Brain,
  ShieldAlert,
  FlaskConical,
  FileImage,
  Layers,
  CheckCircle2,
  Clock,
  Loader2,
  XCircle,
} from "lucide-react";

interface PipelineStatusProps {
  /** Simple status map (from report endpoint) */
  status?: {
    nlp: string;
    risk: string;
    lab: string;
    imaging: string;
    aggregation: string;
  };
  /** Rich status map (from dedicated pipeline endpoint) */
  stages?: {
    nlp: StageStatus;
    risk: StageStatus;
    lab: StageStatus;
    imaging: StageStatus;
    aggregation: StageStatus;
  };
  compact?: boolean;
}

const STEPS = [
  { key: "nlp", label: "NLP", icon: Brain },
  { key: "risk", label: "Risk", icon: ShieldAlert },
  { key: "lab", label: "Lab AI", icon: FlaskConical },
  { key: "imaging", label: "Imaging AI", icon: FileImage },
  { key: "aggregation", label: "Aggregation", icon: Layers },
] as const;

/* Dark-aware status colors — light/dark pairs for WCAG AA contrast */
const STATUS_CONFIG: Record<string, { color: string; dotColor: string; icon: typeof CheckCircle2; label: string; durationColor: string; errorColor: string }> = {
  completed: {
    color: "text-emerald-800 dark:text-emerald-300 border-emerald-300 dark:border-emerald-700 bg-emerald-50 dark:bg-emerald-950/60",
    dotColor: "bg-emerald-500",
    icon: CheckCircle2,
    label: "Completed",
    durationColor: "text-emerald-700 dark:text-emerald-400",
    errorColor: "",
  },
  running: {
    color: "text-sky-800 dark:text-sky-300 border-sky-300 dark:border-sky-700 bg-sky-50 dark:bg-sky-950/60 font-bold",
    dotColor: "bg-sky-500",
    icon: Loader2,
    label: "Running",
    durationColor: "",
    errorColor: "",
  },
  pending: {
    color: "text-amber-800 dark:text-amber-300 border-amber-300 dark:border-amber-700 bg-amber-50 dark:bg-amber-950/60",
    dotColor: "bg-amber-500",
    icon: Clock,
    label: "Pending",
    durationColor: "",
    errorColor: "",
  },
  failed: {
    color: "text-rose-800 dark:text-rose-300 border-rose-300 dark:border-rose-700 bg-rose-50 dark:bg-rose-950/60",
    dotColor: "bg-rose-500",
    icon: XCircle,
    label: "Failed",
    durationColor: "",
    errorColor: "text-rose-700 dark:text-rose-400",
  },
};

function formatDuration(ms: number | null | undefined): string {
  if (ms == null) return "";
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export function PipelineStatus({ status, stages, compact = false }: PipelineStatusProps) {
  return (
    <div className={cn("flex flex-wrap items-stretch", compact ? "gap-1" : "gap-2")}>
      {STEPS.map((step, idx) => {
        // Get status from rich stages or fall back to simple status map
        const stageData = stages?.[step.key as keyof typeof stages];
        const st = stageData?.status || status?.[step.key as keyof typeof status] || "pending";
        const config = STATUS_CONFIG[st] || STATUS_CONFIG.pending;
        const StepIcon = step.icon;
        const StatusIcon = config.icon;

        const duration = stageData?.duration_ms;
        const errorMsg = stageData?.error_message;
        const attemptCount = stageData?.attempt_count ?? 0;

        return (
          <div key={step.key} className="flex items-center">
            <div
              className={cn(
                "flex flex-col rounded-md border-2 px-2.5 py-1.5 transition-all shadow-sm",
                config.color,
                compact && "px-1.5 py-0.5",
              )}
              title={[
                `${step.label}: ${config.label}`,
                duration != null ? `Duration: ${formatDuration(duration)}` : null,
                attemptCount > 1 ? `Attempt: ${attemptCount}` : null,
                errorMsg ? `Error: ${errorMsg}` : null,
              ].filter(Boolean).join("\n")}
            >
              {/* Top row: icon + label + status icon */}
              <div className="flex items-center gap-1.5">
                <StepIcon className={cn("shrink-0", compact ? "h-3 w-3" : "h-3.5 w-3.5")} />
                {!compact && (
                  <span className="text-[10px] font-bold">{step.label}</span>
                )}
                <StatusIcon
                  className={cn(
                    "shrink-0",
                    compact ? "h-2.5 w-2.5" : "h-3 w-3",
                    st === "running" && "animate-spin",
                  )}
                />
              </div>

              {/* Duration line — only in non-compact mode when available */}
              {!compact && st === "completed" && duration != null && (
                <span className={cn("mt-0.5 text-[9px] font-semibold tabular-nums opacity-80", config.durationColor)}>
                  {formatDuration(duration)}
                </span>
              )}

              {/* Error line — only in non-compact mode for failed stages */}
              {!compact && st === "failed" && errorMsg && (
                <span className={cn("mt-0.5 max-w-[120px] truncate text-[9px] font-semibold opacity-80", config.errorColor)}>
                  {errorMsg.slice(0, 40)}{errorMsg.length > 40 ? "…" : ""}
                </span>
              )}

              {/* Attempt badge */}
              {!compact && attemptCount > 1 && (
                <span className="mt-0.5 text-[8px] font-bold opacity-60">
                  Attempt {attemptCount}
                </span>
              )}
            </div>

            {/* Connector line */}
            {idx < STEPS.length - 1 && (
              <div
                className={cn(
                  "h-[2px]",
                  compact ? "w-1" : "w-3",
                  st === "completed" ? "bg-emerald-500" : "bg-slate-300 dark:bg-slate-600",
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

