/**
 * Patient Queue — Nurse workstation
 *
 * Master operational queue for all emergency patients.
 * Every intake appears from creation, sorted by arrival time (newest first).
 * Each row shows workflow status, chief complaint, relative time, evidence progress,
 * and pipeline status.
 *
 * Fetches GET /api/investigations/queue for the lightweight summary list.
 * Clicking a patient row expands the full PatientWorkspace inline,
 * which fetches GET /api/investigations/patient/{intake_id} on demand.
 */

import { useState, useMemo } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import {
  Users,
  Plus,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  CheckCircle2,
  Clock,
  Search,
  FileText,
  Upload,
  Loader2,
  XCircle,
} from "lucide-react";
import { SectionHeader } from "@/components/section-header";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PatientWorkspace } from "@/components/patient-workspace";
import { PipelineStatus } from "@/components/pipeline-status";
import { fetchPatientQueue, type PatientQueueItem } from "@/lib/patient-queue-api";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_app/nurse/queue")({
  head: () => ({
    meta: [
      { title: "Patient Queue — PRATHAM" },
      { name: "description", content: "Live emergency patient queue with evidence upload workspace." },
    ],
  }),
  component: NurseQueue,
});

type QueueItem = PatientQueueItem;

// ── Severity helpers ───────────────────────────────────────────────────────

const SEVERITY_STYLES: Record<string, { dot: string; badge: string }> = {
  critical: {
    dot: "bg-rose-500",
    badge: "bg-rose-100 dark:bg-rose-950/60 text-rose-800 dark:text-rose-300 border-rose-300 dark:border-rose-700",
  },
  high: {
    dot: "bg-orange-500",
    badge: "bg-orange-100 dark:bg-orange-950/60 text-orange-800 dark:text-orange-300 border-orange-300 dark:border-orange-700",
  },
  moderate: {
    dot: "bg-amber-500",
    badge: "bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 border-amber-300 dark:border-amber-700",
  },
  low: {
    dot: "bg-emerald-500",
    badge: "bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border-emerald-300 dark:border-emerald-700",
  },
};

function sevStyle(s: string) {
  return SEVERITY_STYLES[s] ?? SEVERITY_STYLES.moderate;
}

// ── Workflow badge ─────────────────────────────────────────────────────────

const WORKFLOW_CONFIG: Record<
  string,
  { label: string; icon: typeof Clock; color: string; bgColor: string }
> = {
  doctor_review_required: {
    label: "Doctor Review Required",
    icon: Clock,
    color: "text-amber-700 dark:text-amber-300",
    bgColor: "bg-amber-100/80 dark:bg-amber-950/50 border-amber-300 dark:border-amber-700",
  },
  evidence_collection: {
    label: "Awaiting Evidence Upload",
    icon: Upload,
    color: "text-amber-700 dark:text-amber-300",
    bgColor: "bg-amber-100/80 dark:bg-amber-950/50 border-amber-300 dark:border-amber-700",
  },
  ai_processing: {
    label: "AI Analysis Running",
    icon: Loader2,
    color: "text-sky-700 dark:text-sky-300",
    bgColor: "bg-sky-100/80 dark:bg-sky-950/50 border-sky-300 dark:border-sky-700",
  },
  report_ready: {
    label: "Clinical Report Ready",
    icon: CheckCircle2,
    color: "text-emerald-700 dark:text-emerald-300",
    bgColor: "bg-emerald-100/80 dark:bg-emerald-950/50 border-emerald-300 dark:border-emerald-700",
  },
  no_approved: {
    label: "No Approved Investigations",
    icon: XCircle,
    color: "text-rose-700 dark:text-rose-300",
    bgColor: "bg-rose-100/80 dark:bg-rose-950/50 border-rose-300 dark:border-rose-700",
  },
};

function WorkflowBadge({ status }: { status: string }) {
  const config = WORKFLOW_CONFIG[status] ?? WORKFLOW_CONFIG.doctor_review_required;
  const Icon = config.icon;
  const isSpinning = status === "ai_processing";

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider",
        config.bgColor,
        config.color,
      )}
    >
      <Icon className={cn("h-3 w-3", isSpinning && "animate-spin")} />
      {config.label}
    </span>
  );
}

// ── Relative time ──────────────────────────────────────────────────────────

function timeAgo(iso: string | undefined): string {
  if (!iso) return "";
  try {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "Just now";
    if (mins < 60) return `${mins} min ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs} hr ago`;
    const days = Math.floor(hrs / 24);
    if (days === 1) return "Yesterday";
    return `${days}d ago`;
  } catch {
    return "";
  }
}

// ── Sub-components ─────────────────────────────────────────────────────────

function QueueRow({ item, expanded, onToggle }: {
  item: QueueItem;
  expanded: boolean;
  onToggle: () => void;
}) {
  const { investigation_counts: counts, evidence_completeness: ec } = item;
  const sev = sevStyle(item.severity);
  const complete = ec.required > 0 && ec.uploaded === ec.required;
  const completePct = ec.required > 0 ? Math.round((ec.uploaded / ec.required) * 100) : 0;
  const relTime = timeAgo(item.created_at);

  return (
    <div
      className={cn(
        "overflow-hidden rounded-xl border-2 transition-all duration-200",
        expanded
          ? "border-primary shadow-[0_0_0_1px_hsl(var(--primary)/0.15)] bg-slate-50/30 dark:bg-slate-800/30"
          : "border-slate-300 dark:border-slate-600 hover:border-slate-400 dark:hover:border-slate-500 hover:shadow-sm",
      )}
    >
      {/* Summary row — always visible, click to expand */}
      <button
        type="button"
        id={`queue-row-${item.intake_id}`}
        onClick={onToggle}
        className="flex w-full items-start gap-4 px-5 py-4 text-left transition-colors hover:bg-slate-50 dark:hover:bg-slate-800/40"
      >
        {/* Severity dot */}
        <div className="mt-1.5 shrink-0">
          <div className={cn("h-2.5 w-2.5 rounded-full ring-4 ring-current/15", sev.dot)} />
        </div>

        {/* Patient info */}
        <div className="min-w-0 flex-1">
          {/* Row 1: Name, age, severity, relative time */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-bold text-slate-900 dark:text-gray-50 text-sm">{item.patient_name}</span>
            <span className="text-xs font-bold text-slate-700 dark:text-gray-300">
              {item.age}{item.sex}
            </span>
            <span
              className={cn(
                "rounded border px-1.5 py-px text-[10px] font-extrabold uppercase tracking-wider",
                sev.badge,
              )}
            >
              {item.severity}
            </span>
            {relTime && (
              <span className="text-[11px] font-bold text-slate-500 dark:text-gray-400">
                {relTime}
              </span>
            )}
          </div>

          {/* Row 2: Chief complaint */}
          {item.chief_complaint && (
            <p className="mt-1 text-xs font-medium text-slate-600 dark:text-gray-400 truncate max-w-md">
              {item.chief_complaint}
            </p>
          )}

          {/* Row 3: Workflow status badge */}
          <div className="mt-2">
            <WorkflowBadge status={item.workflow_status} />
          </div>

          {/* Row 4: Investigation + evidence summary */}
          <div className="mt-2 flex flex-wrap items-center gap-3 text-xs font-semibold text-slate-800 dark:text-gray-200">
            {counts.approved > 0 && (
              <span className="flex items-center gap-1 text-emerald-700 dark:text-emerald-400">
                <CheckCircle2 className="h-3 w-3" />
                {counts.approved} approved
              </span>
            )}
            {counts.pending > 0 && (
              <span className="flex items-center gap-1 text-amber-700 dark:text-amber-400">
                <Clock className="h-3 w-3" />
                {counts.pending} pending
              </span>
            )}
            {counts.rejected > 0 && (
              <span className="flex items-center gap-1 text-rose-700 dark:text-rose-400">
                <AlertCircle className="h-3 w-3" />
                {counts.rejected} rejected
              </span>
            )}
            {counts.total === 0 && (
              <span className="text-slate-600 dark:text-gray-400">No investigations yet</span>
            )}
          </div>

          {/* Row 5: Evidence completeness bar */}
          {ec.required > 0 && (
            <div className="mt-2 flex items-center gap-2">
              <div className="h-1.5 w-20 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
                <div
                  className={cn(
                    "h-full rounded-full transition-all duration-500",
                    complete ? "bg-emerald-600" : "bg-amber-600",
                  )}
                  style={{ width: `${completePct}%` }}
                />
              </div>
              <span className={cn("text-[10px] font-bold", complete ? "text-emerald-700 dark:text-emerald-400" : "text-amber-700 dark:text-amber-400")}>
                {ec.uploaded} / {ec.required} evidence
              </span>
            </div>
          )}
        </div>

        {/* Expand / collapse toggle */}
        <div className="shrink-0 self-center">
          {expanded ? (
            <ChevronUp className="h-4 w-4 text-slate-800 dark:text-gray-200 font-extrabold" />
          ) : (
            <ChevronDown className="h-4 w-4 text-slate-800 dark:text-gray-200 font-extrabold" />
          )}
        </div>
      </button>

      <div className="flex flex-wrap items-center justify-between gap-3 border-t-2 border-slate-350 dark:border-slate-600 bg-slate-50 dark:bg-slate-800/50 px-5 py-2.5">
        <PipelineStatus status={item.pipeline_status} compact />
        <Button asChild size="sm" variant="outline" className="border-slate-300 dark:border-slate-600 font-bold bg-white dark:bg-slate-800 text-slate-800 dark:text-gray-200 hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-slate-900 dark:hover:text-gray-50 shadow-sm">
          <Link to="/doctor/report/$intakeId" params={{ intakeId: item.intake_id }}>
            <FileText className="mr-1.5 h-3.5 w-3.5" />
            View report
          </Link>
        </Button>
      </div>

      {/* Expanded workspace */}
      {expanded && (
        <div className="border-t-2 border-slate-350 dark:border-slate-600 bg-white dark:bg-card px-5 py-5">
          <PatientWorkspace intakeId={item.intake_id} />
        </div>
      )}
    </div>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────

function NurseQueue() {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const { data: queue, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ["patient-queue"],
    queryFn: fetchPatientQueue,
    refetchInterval: 60_000, // auto-refresh every 60 s
    staleTime: 10_000,
  });

  // Filter by search (name, severity, chief complaint) — NO re-sorting.
  // Backend already returns ORDER BY created_at DESC (newest first).
  const filtered = useMemo(() => {
    if (!queue) return [];
    const q = search.toLowerCase().trim();
    if (!q) return queue;
    return queue.filter((p) =>
      p.patient_name.toLowerCase().includes(q) ||
      p.severity.toLowerCase().includes(q) ||
      (p.chief_complaint || "").toLowerCase().includes(q)
    );
  }, [queue, search]);

  const toggle = (id: string) => setExpandedId((curr) => (curr === id ? null : id));

  return (
    <div className="mx-auto max-w-4xl px-5 py-8 md:px-8">
      <SectionHeader
        eyebrow="Nurse station"
        title="Patient Queue"
        description="Live emergency queue sorted by arrival time. Select a patient to upload evidence and view investigation status."
        actions={
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => refetch()}
              disabled={isFetching}
              id="refresh-queue-btn"
            >
              <RefreshCw className={cn("mr-1.5 h-3.5 w-3.5", isFetching && "animate-spin")} />
              Refresh
            </Button>
            <Button asChild size="sm" id="new-intake-btn">
              <Link to="/nurse/intake">
                <Plus className="mr-1.5 h-3.5 w-3.5" />
                New intake
              </Link>
            </Button>
          </div>
        }
      />

      {/* Search */}
      <div className="relative mt-6">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          id="queue-search"
          type="text"
          placeholder="Search by name, severity, or chief complaint…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-lg border bg-muted/20 py-2.5 pl-9 pr-4 text-sm outline-none transition-colors placeholder:text-muted-foreground focus:border-primary/60 focus:bg-background"
        />
      </div>

      <div className="mt-4 space-y-3">
        {/* Loading skeleton */}
        {isLoading && (
          <div className="space-y-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="rounded-xl border p-5">
                <div className="flex items-start gap-4">
                  <div className="mt-1.5 h-2.5 w-2.5 animate-pulse rounded-full bg-muted" />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <div className="h-4 w-32 animate-pulse rounded bg-muted" />
                      <div className="h-3 w-12 animate-pulse rounded bg-muted" />
                      <div className="h-4 w-16 animate-pulse rounded-md bg-muted" />
                    </div>
                    <div className="mt-2 h-4 w-40 animate-pulse rounded-md bg-muted/60" />
                    <div className="mt-2 flex gap-3">
                      <div className="h-3 w-20 animate-pulse rounded bg-muted/60" />
                      <div className="h-3 w-20 animate-pulse rounded bg-muted/60" />
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Error state */}
        {isError && (
          <Card>
            <CardContent className="flex items-center gap-3 p-6">
              <AlertCircle className="h-5 w-5 shrink-0 text-rose-400" />
              <div className="min-w-0">
                <p className="text-sm font-medium">Failed to load queue</p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  {axios.isAxiosError(error)
                    ? error.response?.data?.detail ?? error.message
                    : "An unexpected error occurred."}
                </p>
              </div>
              <Button size="sm" variant="outline" onClick={() => refetch()} className="ml-auto shrink-0">
                Retry
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Empty state */}
        {!isLoading && !isError && filtered.length === 0 && (
          <Card>
            <CardContent className="p-10 text-center">
              <Users className="mx-auto h-8 w-8 text-muted-foreground/40" />
              <p className="mt-3 text-sm font-medium">
                {search ? "No patients match your search" : "Queue is empty"}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                {search
                  ? "Try a different name, severity, or chief complaint."
                  : "Submit a new intake to add a patient."}
              </p>
              {!search && (
                <Button asChild size="sm" variant="outline" className="mt-4">
                  <Link to="/nurse/intake">
                    <Plus className="mr-1.5 h-3.5 w-3.5" />
                    New intake
                  </Link>
                </Button>
              )}
            </CardContent>
          </Card>
        )}

        {/* Patient rows */}
        {!isLoading &&
          !isError &&
          filtered.map((item) => (
            <QueueRow
              key={item.intake_id}
              item={item}
              expanded={expandedId === item.intake_id}
              onToggle={() => toggle(item.intake_id)}
            />
          ))}
      </div>

      {/* Footer count */}
      {!isLoading && !isError && filtered.length > 0 && (
        <p className="mt-4 text-center text-[11px] text-muted-foreground">
          {filtered.length} patient{filtered.length !== 1 ? "s" : ""} in queue
          {isFetching && " · refreshing…"}
        </p>
      )}
    </div>
  );
}
