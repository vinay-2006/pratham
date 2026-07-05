/**
 * PatientTimeline — Vertical timeline of patient journey events.
 *
 * Reconstructed from existing database timestamps — no new table needed.
 * Shows chronological events from intake through report generation.
 */

import { useQuery } from "@tanstack/react-query";
import { fetchPatientTimeline, type TimelineEvent } from "@/lib/patient-queue-api";
import { cn } from "@/lib/utils";
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
} from "lucide-react";

// Map icon names from backend to lucide components
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

// Color mapping by event type
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

interface PatientTimelineProps {
  intakeId: string;
}

export function PatientTimeline({ intakeId }: PatientTimelineProps) {
  const { data: events, isLoading, isError } = useQuery({
    queryKey: ["patient-timeline", intakeId],
    queryFn: () => fetchPatientTimeline(intakeId),
    staleTime: 30_000,
  });

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 py-4 text-xs text-muted-foreground">
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
        Loading timeline…
      </div>
    );
  }

  if (isError || !events || events.length === 0) {
    return (
      <p className="py-3 text-xs text-muted-foreground">
        No timeline events available.
      </p>
    );
  }

  return (
    <div className="py-1">
      {events.map((event, idx) => (
        <TimelineItem
          key={`${event.timestamp}-${idx}`}
          event={event}
          isLast={idx === events.length - 1}
        />
      ))}
    </div>
  );
}
