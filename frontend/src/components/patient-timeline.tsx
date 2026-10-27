/**
 * PatientTimeline — Vertical timeline of patient journey events.
 *
 * Supports two modes:
 *  - Collapsed: Reconstructed clinical timeline (intake, recommendations, uploads, AI pipeline completion).
 *  - Expanded: Developer/auditor-facing status transition log trail (workflow_logs table).
 */

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  fetchPatientTimeline,
  fetchWorkflowLogs,
  type TimelineEvent,
  type WorkflowLog,
} from "@/lib/patient-queue-api";
import { WORKFLOW_LABELS, WorkflowStatus } from "@/lib/mock-data";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Ambulance,
  Brain,
  CheckCircle2,
  ClipboardList,
  FileImage,
  FileText,
  FlaskConical,
  Layers,
  Loader2,
  ShieldAlert,
  Upload,
  XCircle,
  AlertTriangle,
  History,
  Activity,
  User,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

const ICON_MAP: Record<string, typeof Brain> = {
  ambulance: Ambulance,
  "clipboard-list": ClipboardList,
  "check-circle": CheckCircle2,
  "x-circle": XCircle,
  upload: Upload,
  brain: Brain,
  "shield-alert": ShieldAlert,
  "flask-conical": FlaskConical,
  "file-image": FileImage,
  layers: Layers,
  "alert-triangle": AlertTriangle,
  "file-text": FileText,
};

const TYPE_COLORS: Record<string, { dot: string; line: string; text: string }> = {
  intake:             { dot: "bg-sky-500",     line: "bg-sky-300 dark:bg-sky-700",     text: "text-sky-800 dark:text-sky-300" },
  investigate:        { dot: "bg-slate-500",   line: "bg-slate-300 dark:bg-slate-600", text: "text-slate-800 dark:text-slate-300" },
  approved:           { dot: "bg-emerald-500", line: "bg-emerald-300 dark:bg-emerald-700", text: "text-emerald-800 dark:text-emerald-300" },
  rejected:           { dot: "bg-rose-500",    line: "bg-rose-300 dark:bg-rose-700",   text: "text-rose-800 dark:text-rose-300" },
  uploaded:           { dot: "bg-violet-500",  line: "bg-violet-300 dark:bg-violet-700", text: "text-violet-800 dark:text-violet-300" },
  pipeline_completed: { dot: "bg-emerald-500", line: "bg-emerald-300 dark:bg-emerald-700", text: "text-emerald-800 dark:text-emerald-300" },
  pipeline_failed:    { dot: "bg-rose-500",    line: "bg-rose-300 dark:bg-rose-700",   text: "text-rose-800 dark:text-rose-300" },
  report:             { dot: "bg-primary",     line: "bg-primary/40",                  text: "text-primary" },
};

function getColors(type: string) {
  return TYPE_COLORS[type] ?? TYPE_COLORS.investigate;
}

function formatTime(iso: string | null): string {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false });
  } catch {
    return "";
  }
}

function formatDate(iso: string | null): string {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    const today = new Date();
    const isToday = d.toDateString() === today.toDateString();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const isYesterday = d.toDateString() === yesterday.toDateString();

    if (isToday) return "Today";
    if (isYesterday) return "Yesterday";
    return d.toLocaleDateString([], { month: "short", day: "numeric" });
  } catch {
    return "";
  }
}

function TimelineItem({ event, isLast }: { event: TimelineEvent; isLast: boolean }) {
  const colors = getColors(event.type);
  const IconComponent = ICON_MAP[event.icon] ?? CheckCircle2;
  const time = formatTime(event.timestamp);
  const date = formatDate(event.timestamp);

  return (
    <div className="flex gap-3">
      {/* Time column */}
      <div className="w-12 shrink-0 pt-0.5 text-right">
        <span className="text-[10px] font-bold tabular-nums text-slate-600 dark:text-gray-400">
          {time}
        </span>
      </div>

      {/* Dot + line */}
      <div className="relative flex flex-col items-center">
        <div
          className={cn(
            "flex h-6 w-6 shrink-0 items-center justify-center rounded-full ring-2 ring-white dark:ring-slate-900",
            colors.dot,
          )}
        >
          <IconComponent className="h-3 w-3 text-white" />
        </div>
        {!isLast && (
          <div className={cn("w-0.5 flex-1 min-h-[20px]", colors.line)} />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 pb-4">
        <p className={cn("text-xs font-bold leading-tight", colors.text)}>
          {event.event}
        </p>
        {event.detail && (
          <p className="mt-0.5 text-[10px] font-medium text-slate-600 dark:text-gray-400 truncate max-w-[250px]">
            {event.detail}
          </p>
        )}
        {date && date !== "Today" && (
          <p className="mt-0.5 text-[9px] font-semibold text-slate-500 dark:text-gray-500">
            {date}
          </p>
        )}
      </div>
    </div>
  );
}

function WorkflowLogItem({ log, isLast }: { log: WorkflowLog; isLast: boolean }) {
  const time = formatTime(log.changed_at);
  
  // Custom tag color by actor type
  const actorColor = 
    log.actor_type === "Doctor" 
      ? "bg-sky-500/10 text-sky-600 dark:text-sky-400"
      : log.actor_type === "Nurse"
      ? "bg-teal-500/10 text-teal-600 dark:text-teal-400"
      : "bg-slate-500/10 text-slate-600 dark:text-slate-400";

  return (
    <div className="flex gap-3">
      {/* Time column */}
      <div className="w-12 shrink-0 pt-0.5 text-right">
        <span className="text-[10px] font-bold tabular-nums text-slate-600 dark:text-gray-400">
          {time}
        </span>
      </div>

      {/* Dot + line */}
      <div className="relative flex flex-col items-center">
        <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800 ring-2 ring-white dark:ring-slate-900">
          <Activity className="h-3 w-3 text-slate-500" />
        </div>
        {!isLast && (
          <div className="w-0.5 flex-1 min-h-[24px] bg-slate-200 dark:bg-slate-800" />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 pb-4">
        <div className="flex flex-wrap items-center gap-1.5 leading-tight">
          {log.old_status && (
            <>
              <span className="text-[10px] font-semibold text-slate-400 line-through">
                {WORKFLOW_LABELS[log.old_status as WorkflowStatus] || log.old_status}
              </span>
              <span className="text-[10px] text-slate-400">→</span>
            </>
          )}
          <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
            {WORKFLOW_LABELS[log.new_status as WorkflowStatus] || log.new_status}
          </span>
        </div>
        
        <div className="mt-1 flex items-center gap-1 text-[10px] text-slate-500">
          <span className={cn("px-1.5 py-0.5 rounded font-bold text-[9px] uppercase", actorColor)}>
            {log.actor_type}
          </span>
          <span className="font-semibold text-slate-600 dark:text-gray-400">
            {log.actor_name}
          </span>
        </div>
        
        {log.reason && (
          <p className="mt-1 rounded bg-slate-50 dark:bg-slate-800/40 p-2 text-[10px] leading-relaxed text-slate-600 dark:text-slate-400 border border-slate-100/50 dark:border-slate-800/30">
            {log.reason}
          </p>
        )}
      </div>
    </div>
  );
}

interface PatientTimelineProps {
  intakeId: string;
}

export function PatientTimeline({ intakeId }: PatientTimelineProps) {
  const [showFullLogs, setShowFullLogs] = useState(false);

  // Fetch reconstructed clinical events (default collapsed view)
  const clinicalQuery = useQuery({
    queryKey: ["patient-timeline", intakeId],
    queryFn: () => fetchPatientTimeline(intakeId),
    staleTime: 10_000,
    enabled: !showFullLogs,
  });

  // Fetch status transitions (developer/audit logs view)
  const logsQuery = useQuery({
    queryKey: ["workflow-logs", intakeId],
    queryFn: () => fetchWorkflowLogs(intakeId),
    staleTime: 10_000,
    enabled: showFullLogs,
  });

  const isLoading = showFullLogs ? logsQuery.isLoading : clinicalQuery.isLoading;
  const isError = showFullLogs ? logsQuery.isError : clinicalQuery.isError;

  return (
    <div className="space-y-4">
      {/* Header Action Toggle */}
      <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-2">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
          Case History
        </span>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setShowFullLogs((prev) => !prev)}
          className="h-7 text-[10px] font-bold text-slate-600 dark:text-gray-400 hover:text-primary"
        >
          {showFullLogs ? (
            <>
              <ChevronDown className="mr-1 h-3.5 w-3.5" />
              Clinical Stages
            </>
          ) : (
            <>
              <History className="mr-1 h-3.5 w-3.5" />
              Audit Logs
            </>
          )}
        </Button>
      </div>

      {/* Timeline Items Listing */}
      {isLoading ? (
        <div className="flex items-center gap-2 py-4 text-xs text-muted-foreground">
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
          Loading logs…
        </div>
      ) : isError ? (
        <p className="py-3 text-xs text-rose-500 font-medium">
          Failed to load case timeline logs.
        </p>
      ) : showFullLogs ? (
        // Render expanded workflow logs (audit trail)
        !logsQuery.data || logsQuery.data.length === 0 ? (
          <p className="py-3 text-xs text-muted-foreground">
            No status logs found for this case.
          </p>
        ) : (
          <div className="py-1 space-y-1">
            {logsQuery.data.map((log, idx) => (
              <WorkflowLogItem
                key={log.id}
                log={log}
                isLast={idx === logsQuery.data.length - 1}
              />
            ))}
          </div>
        )
      ) : (
        // Render collapsed clinical timeline events
        !clinicalQuery.data || clinicalQuery.data.length === 0 ? (
          <p className="py-3 text-xs text-muted-foreground">
            No clinical milestones recorded yet.
          </p>
        ) : (
          <div className="py-1">
            {clinicalQuery.data.map((event, idx) => (
              <TimelineItem
                key={`${event.timestamp}-${idx}`}
                event={event}
                isLast={idx === clinicalQuery.data.length - 1}
              />
            ))}
          </div>
        )
      )}
    </div>
  );
}
