/**
 * PipelineStatus — Visual 5-step AI pipeline indicator
 *
 * Shows the status of each subsystem:
 *   NLP → Risk → Lab → Imaging → Aggregation
 */

import { cn } from "@/lib/utils";
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
  status: {
    nlp: string;
    risk: string;
    lab: string;
    imaging: string;
    aggregation: string;
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

const STATUS_CONFIG: Record<string, { color: string; icon: typeof CheckCircle2; label: string }> = {
  completed: { color: "text-emerald-800 border-emerald-300 bg-emerald-50", icon: CheckCircle2, label: "Done" },
  running: { color: "text-primary border-primary/40 bg-primary/5 font-bold", icon: Loader2, label: "Running" },
  pending: { color: "text-slate-700 border-slate-300 bg-slate-100", icon: Clock, label: "Pending" },
  failed: { color: "text-rose-800 border-rose-300 bg-rose-50", icon: XCircle, label: "Failed" },
};

export function PipelineStatus({ status, compact = false }: PipelineStatusProps) {
  return (
    <div className={cn("flex items-center", compact ? "gap-1" : "gap-2")}>
      {STEPS.map((step, idx) => {
        const st = status[step.key as keyof typeof status] || "pending";
        const config = STATUS_CONFIG[st] || STATUS_CONFIG.pending;
        const StepIcon = step.icon;
        const StatusIcon = config.icon;

        return (
          <div key={step.key} className="flex items-center">
            <div
              className={cn(
                "flex items-center gap-1.5 rounded-md border-2 px-2 py-1 transition-all shadow-sm",
                config.color,
                compact && "px-1.5 py-0.5",
              )}
              title={`${step.label}: ${config.label}`}
            >
              <StepIcon className={cn("shrink-0", compact ? "h-3 w-3" : "h-3.5 w-3.5")} />
              {!compact && (
                <span className="text-[10px] font-bold text-slate-800">{step.label}</span>
              )}
              <StatusIcon
                className={cn(
                  "shrink-0",
                  compact ? "h-2.5 w-2.5" : "h-3 w-3",
                  st === "running" && "animate-spin",
                )}
              />
            </div>
            {/* Connector line */}
            {idx < STEPS.length - 1 && (
              <div
                className={cn(
                  "h-[2px] bg-slate-300",
                  compact ? "w-1" : "w-3",
                  st === "completed" && "bg-emerald-600",
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
