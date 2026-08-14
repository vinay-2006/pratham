/**
 * Active Patients Queue — Nurse station
 *
 * Master operational tracker for all active emergency cases.
 * Sorted by arrival time (newest first). Excludes Case Closed and Offline Care cases.
 */

import { useState, useMemo, useEffect } from "react";
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
  Loader2,
  Calendar,
  Sparkles,
  ArrowRight,
  Shield,
  Truck,
  UserCheck,
  Building,
} from "lucide-react";
import { SectionHeader } from "@/components/section-header";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PatientWorkspace } from "@/components/patient-workspace";
import { PatientJourneyCard } from "@/components/patient-journey-card";
import { PatientTimeline } from "@/components/patient-timeline";
import { fetchPatientQueue, confirmArrival, type PatientQueueItem } from "@/lib/patient-queue-api";
import { WorkflowStatus, WORKFLOW_LABELS } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_app/nurse/queue")({
  head: () => ({
    meta: [
      { title: "Active Patients — PRATHAM" },
      { name: "description", content: "Live Emergency Department workflow tracker and operational queue." },
    ],
  }),
  component: NurseQueue,
});

type QueueItem = PatientQueueItem;

// ── Severity styling ────────────────────────────────────────────────────────

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

// ── Workflow status colored badges (Task 1 & Sprint Guidelines) ─────────────────

const STATUS_CONFIG: Record<
  WorkflowStatus,
  { label: string; color: string; border: string; bg: string }
> = {
  [WorkflowStatus.INTAKE_SUBMITTED]: {
    label: "Intake Submitted",
    color: "text-blue-700 dark:text-blue-400",
    border: "border-blue-200 dark:border-blue-800",
    bg: "bg-blue-50 dark:bg-blue-950/30",
  },
  [WorkflowStatus.EN_ROUTE]: {
    label: "En Route",
    color: "text-blue-700 dark:text-blue-400",
    border: "border-blue-200 dark:border-blue-800",
    bg: "bg-blue-50 dark:bg-blue-950/30",
  },
  [WorkflowStatus.ARRIVED]: {
    label: "Arrived",
    color: "text-amber-700 dark:text-amber-400",
    border: "border-amber-200 dark:border-amber-800",
    bg: "bg-amber-50 dark:bg-amber-950/30",
  },
  [WorkflowStatus.AWAITING_APPROVAL]: {
    label: "Awaiting Doctor Approval",
    color: "text-amber-700 dark:text-amber-400",
    border: "border-amber-200 dark:border-amber-800",
    bg: "bg-amber-50 dark:bg-amber-950/30",
  },
  [WorkflowStatus.APPROVED]: {
    label: "Investigations Approved",
    color: "text-orange-700 dark:text-orange-400",
    border: "border-orange-250 dark:border-orange-850",
    bg: "bg-orange-50 dark:bg-orange-950/30",
  },
  [WorkflowStatus.UPLOAD_PENDING]: {
    label: "Evidence Upload Pending",
    color: "text-orange-700 dark:text-orange-400",
    border: "border-orange-250 dark:border-orange-850",
    bg: "bg-orange-50 dark:bg-orange-950/30",
  },
  [WorkflowStatus.ANALYSIS_RUNNING]: {
    label: "Analysis Running",
    color: "text-orange-700 dark:text-orange-400",
    border: "border-orange-250 dark:border-orange-850",
    bg: "bg-orange-50 dark:bg-orange-950/30",
  },
  [WorkflowStatus.REPORT_READY]: {
    label: "Clinical Report Ready",
    color: "text-emerald-700 dark:text-emerald-400",
    border: "border-emerald-200 dark:border-emerald-800",
    bg: "bg-emerald-50 dark:bg-emerald-950/30",
  },
  [WorkflowStatus.UNDER_REVIEW]: {
    label: "Under Doctor Review",
    color: "text-emerald-700 dark:text-emerald-400",
    border: "border-emerald-200 dark:border-emerald-800",
    bg: "bg-emerald-50 dark:bg-emerald-950/30",
  },
  [WorkflowStatus.CLOSED]: {
    label: "Case Closed",
    color: "text-slate-600 dark:text-slate-400",
    border: "border-slate-200 dark:border-slate-800",
    bg: "bg-slate-50 dark:bg-slate-900/30",
  },
  [WorkflowStatus.OFFLINE]: {
    label: "Offline Care",
    color: "text-slate-600 dark:text-slate-400",
    border: "border-slate-200 dark:border-slate-800",
    bg: "bg-slate-50 dark:bg-slate-900/30",
  },
};

function StatusBadge({ status, arrivalType }: { status: WorkflowStatus; arrivalType?: string }) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG[WorkflowStatus.INTAKE_SUBMITTED];
  let label = config.label;
  if (status === WorkflowStatus.INTAKE_SUBMITTED && arrivalType === "referral") {
    label = "Awaiting Arrival Confirmation";
  }

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider shadow-sm",
        config.bg,
        config.border,
        config.color
      )}
    >
      {status === WorkflowStatus.ANALYSIS_RUNNING && (
        <Loader2 className="h-2.5 w-2.5 animate-spin mr-0.5" />
      )}
      {label}
    </span>
  );
}

// ── Live Ambulance ETA Timer Component (Task 2) ─────────────────────────────

function AmbulanceTimer({
  createdAt,
  etaMins,
  onExpired,
}: {
  createdAt: string;
  etaMins: number;
  onExpired: () => void;
}) {
  const [timeLeft, setTimeLeft] = useState<number>(0);

  useEffect(() => {
    const calculateTimeLeft = () => {
      const start = new Date(createdAt).getTime();
      const end = start + etaMins * 60 * 1000;
      const remaining = Math.max(0, Math.floor((end - Date.now()) / 1000));
      setTimeLeft(remaining);
      if (remaining === 0) {
        onExpired();
      }
    };

    calculateTimeLeft();
    const interval = setInterval(calculateTimeLeft, 1000);
    return () => clearInterval(interval);
  }, [createdAt, etaMins, onExpired]);

  if (timeLeft === 0) {
    return (
      <span className="inline-flex items-center text-[10px] font-bold text-emerald-600 uppercase">
        Arrived
      </span>
    );
  }

  const mins = Math.floor(timeLeft / 60);
  const secs = timeLeft % 60;
  return (
    <span className="inline-flex items-center gap-1 rounded-md bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 text-[10px] font-bold font-mono text-amber-600 dark:text-amber-400">
      <Truck className="h-3 w-3 animate-pulse" />
      {mins}m {secs}s remaining
    </span>
  );
}

// ── Relative elapsed time ───────────────────────────────────────────────────

function timeAgo(iso: string | undefined): string {
  if (!iso) return "";
  try {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "Just now";
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    return `${days}d ago`;
  } catch {
    return "";
  }
}

// ── Queue Row ───────────────────────────────────────────────────────────────

function QueueRow({
  item,
  expanded,
  onToggle,
  refetchQueue,
}: {
  item: QueueItem;
  expanded: boolean;
  onToggle: () => void;
  refetchQueue: () => void;
}) {
  const [confirmLoading, setConfirmLoading] = useState(false);
  const { investigation_counts: counts, evidence_completeness: ec } = item;
  const sev = sevStyle(item.severity);
  const relTime = timeAgo(item.created_at);

  const handleConfirmArrival = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setConfirmLoading(true);
    try {
      await confirmArrival(item.intake_id, "Nurse Station Desk");
      refetchQueue();
    } catch (err) {
      console.error("Arrival confirmation failed:", err);
    } finally {
      setConfirmLoading(false);
    }
  };

  // Helper for arrival type icons
  const ArrivalIcon = () => {
    if (item.arrival_type === "ambulance") return <Truck className="h-3.5 w-3.5 text-slate-500" />;
    if (item.arrival_type === "referral") return <Building className="h-3.5 w-3.5 text-slate-500" />;
    return <UserCheck className="h-3.5 w-3.5 text-slate-500" />;
  };

  return (
    <div
      className={cn(
        "overflow-hidden rounded-2xl border-2 transition-all duration-300 bg-white dark:bg-slate-900/50 shadow-sm",
        expanded
          ? "border-teal-500 dark:border-teal-400 shadow-md bg-slate-50/50 dark:bg-slate-900/90"
          : "border-slate-200/80 dark:border-slate-800/80 hover:border-slate-350 dark:hover:border-slate-700"
      )}
    >
      {/* Primary list trigger */}
      <button
        type="button"
        id={`queue-row-${item.intake_id}`}
        onClick={onToggle}
        className="flex w-full items-start gap-4 px-6 py-5 text-left transition-colors hover:bg-slate-50/50 dark:hover:bg-slate-800/30"
      >
        {/* Severity Dot */}
        <div className="mt-1.5 shrink-0">
          <div className={cn("h-3 w-3 rounded-full ring-4 ring-current/10", sev.dot)} />
        </div>

        {/* Core content */}
        <div className="min-w-0 flex-1 grid gap-2 md:grid-cols-[1.5fr_1fr_1fr_auto] md:items-center">
          {/* Col 1: Case ID, Name, CC */}
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-slate-400 dark:text-slate-500">
                {item.case_id || "Case"}
              </span>
              <span className="font-bold text-slate-900 dark:text-slate-100 text-sm">
                {item.patient_name}
              </span>
              <span className="text-xs text-slate-500 font-semibold">
                {item.age}{item.sex}
              </span>
            </div>
            {item.chief_complaint && (
              <p className="mt-1 text-xs font-medium text-slate-500 dark:text-gray-400 truncate max-w-xs md:max-w-md">
                {item.chief_complaint}
              </p>
            )}
          </div>

          {/* Col 2: Arrival Type & Countdown ETA */}
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center justify-center p-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 shrink-0">
              <ArrivalIcon />
            </span>
            <div className="flex flex-col">
              <span className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                {item.arrival_type.replace("_", " ")}
              </span>
              <div className="mt-0.5">
                {item.arrival_type === "ambulance" && item.ambulance_eta && item.workflow_status === WorkflowStatus.EN_ROUTE ? (
                  <AmbulanceTimer
                    createdAt={item.created_at}
                    etaMins={item.ambulance_eta}
                    onExpired={refetchQueue}
                  />
                ) : item.arrival_type === "referral" && item.workflow_status === WorkflowStatus.INTAKE_SUBMITTED ? (
                  <Button
                    size="xs"
                    onClick={handleConfirmArrival}
                    disabled={confirmLoading}
                    className="h-6 px-2.5 text-[10px] font-bold bg-teal-600 hover:bg-teal-500 text-white"
                  >
                    {confirmLoading ? (
                      <Loader2 className="h-3 w-3 animate-spin mr-1" />
                    ) : (
                      "Confirm Arrival"
                    )}
                  </Button>
                ) : (
                  <span className="text-[11px] font-bold text-slate-600 dark:text-slate-400">
                    Arrived
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Col 3: Status & Progress bar */}
          <div>
            <div className="flex items-center gap-1.5">
              <StatusBadge status={item.workflow_status} arrivalType={item.arrival_type} />
            </div>
            <div className="mt-2 flex items-center gap-2">
              <div className="h-1.5 w-24 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                <div
                  className="h-full bg-gradient-to-r from-teal-500 to-emerald-500 rounded-full transition-all duration-300"
                  style={{ width: `${item.progress}%` }}
                />
              </div>
              <span className="text-[10px] font-bold text-slate-500">
                {item.progress}%
              </span>
            </div>
          </div>

          {/* Col 4: Priorities and Relative time */}
          <div className="text-right flex md:flex-col items-center md:items-end justify-between md:justify-center gap-2 md:gap-1">
            <span
              className={cn(
                "rounded-full border px-2 py-0.5 text-[9px] font-extrabold uppercase tracking-wider",
                sev.badge
              )}
            >
              {item.severity}
            </span>
            <span className="text-[10px] font-bold font-mono text-slate-400 dark:text-slate-500 flex items-center gap-1">
              <Clock className="h-3 w-3 shrink-0" />
              {relTime}
            </span>
          </div>
        </div>

        {/* Caret icon */}
        <div className="shrink-0 self-center ml-2">
          {expanded ? (
            <ChevronUp className="h-4 w-4 text-slate-400" />
          ) : (
            <ChevronDown className="h-4 w-4 text-slate-400" />
          )}
        </div>
      </button>

      {/* Action Footer */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200/60 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/30 px-6 py-3">
        <div className="flex items-center gap-3 text-[11px] font-semibold text-slate-500">
          <span>{ec.uploaded} of {ec.required} files uploaded</span>
        </div>
        <Button asChild size="sm" variant="ghost" className="h-8 font-bold text-teal-600 hover:text-teal-500 dark:text-teal-400">
          <Link to="/doctor/report/$intakeId" params={{ intakeId: item.intake_id }}>
            <FileText className="mr-1.5 h-3.5 w-3.5" />
            Open Report
          </Link>
        </Button>
      </div>

      {/* Expanded Journey workspace */}
      {expanded && (
        <div className="border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6">
          <div className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
            {/* Left side Workspace */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 pb-2 border-b border-slate-100 dark:border-slate-800">
                <span className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider">
                  Investigations & Uploads Desk
                </span>
              </div>
              <PatientWorkspace intakeId={item.intake_id} />
            </div>

            {/* Right side Journey & Timeline Checklist */}
            <div className="space-y-6 lg:border-l lg:border-slate-100 lg:dark:border-slate-800 lg:pl-6">
              <PatientJourneyCard
                caseId={item.case_id || `PRA-2026-${item.intake_id.slice(0, 6).toUpperCase()}`}
                status={item.workflow_status}
                arrivalType={item.arrival_type}
                createdAt={item.created_at}
              />
              <PatientTimeline intakeId={item.intake_id} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main Page Component ─────────────────────────────────────────────────────

function NurseQueue() {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const { data: queue, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ["patient-queue"],
    queryFn: fetchPatientQueue,
    refetchInterval: 15_000,
    staleTime: 10_000,
    retry: 2,
  });

  const filtered = useMemo(() => {
    if (!queue) return [];
    const q = search.toLowerCase().trim();
    if (!q) return queue;
    return queue.filter((p) =>
      p.patient_name.toLowerCase().includes(q) ||
      p.severity.toLowerCase().includes(q) ||
      (p.case_id || "").toLowerCase().includes(q) ||
      (p.chief_complaint || "").toLowerCase().includes(q)
    );
  }, [queue, search]);

  const toggle = (id: string) => setExpandedId((curr) => (curr === id ? null : id));

  return (
    <div className="mx-auto max-w-5xl px-5 py-8 md:px-8">
      <SectionHeader
        eyebrow="Triage Desk"
        title="Active Patients"
        description="Emergency tracker for arrivals, doctor approval gates, and running AI diagnostic queues."
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
            <Button asChild size="sm" id="new-intake-btn" className="bg-teal-600 hover:bg-teal-500">
              <Link to="/nurse/intake">
                <Plus className="mr-1.5 h-3.5 w-3.5" />
                New Intake
              </Link>
            </Button>
          </div>
        }
      />

      {/* Search Input */}
      <div className="relative mt-6">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input
          id="queue-search"
          type="text"
          placeholder="Search by Case ID, name, severity, or chief complaint…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-xl border bg-slate-50 dark:bg-slate-900 py-3 pl-10 pr-4 text-sm outline-none transition-all placeholder:text-slate-400 focus:border-teal-500/60 focus:bg-background"
        />
      </div>

      {/* Active Patients Queue List */}
      <div className="mt-6 space-y-4">
        {isLoading && (
          <div className="space-y-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="rounded-2xl border p-6 bg-slate-50/20 dark:bg-slate-900/20 animate-pulse">
                <div className="flex items-center justify-between">
                  <div className="h-4 w-32 bg-slate-200 dark:bg-slate-800 rounded" />
                  <div className="h-3 w-16 bg-slate-200 dark:bg-slate-800 rounded" />
                </div>
                <div className="mt-3 h-3 w-48 bg-slate-200 dark:bg-slate-800 rounded" />
                <div className="mt-4 flex gap-4">
                  <div className="h-3 w-24 bg-slate-200 dark:bg-slate-800 rounded" />
                  <div className="h-3 w-20 bg-slate-200 dark:bg-slate-800 rounded" />
                </div>
              </div>
            ))}
          </div>
        )}

        {isError && (
          <Card className="border-rose-500/20 bg-rose-500/5">
            <CardContent className="flex items-center gap-3 p-6">
              <AlertCircle className="h-5 w-5 shrink-0 text-rose-500" />
              <div className="min-w-0">
                <p className="text-sm font-semibold text-rose-700 dark:text-rose-400">Failed to load active patients queue</p>
                <p className="mt-0.5 text-xs text-rose-600">
                  {axios.isAxiosError(error)
                    ? error.response?.data?.detail ?? error.message
                    : "An unexpected error occurred."}
                </p>
              </div>
              <Button size="sm" variant="outline" onClick={() => refetch()} className="ml-auto shrink-0 border-rose-300">
                Retry
              </Button>
            </CardContent>
          </Card>
        )}

        {!isLoading && !isError && filtered.length === 0 && (
          <Card className="border-slate-200 dark:border-slate-800 bg-slate-50/50">
            <CardContent className="p-12 text-center">
              <Users className="mx-auto h-10 w-10 text-slate-400/60" />
              <p className="mt-4 text-base font-bold text-slate-700 dark:text-slate-350">
                {search ? "No matches found" : "No active patients"}
              </p>
              <p className="mt-2 text-xs text-slate-500">
                {search
                  ? "Try looking for another Case ID or spelling."
                  : "All patient files have been processed and closed."}
              </p>
              {!search && (
                <Button asChild size="sm" className="mt-6 bg-teal-600 hover:bg-teal-500">
                  <Link to="/nurse/intake">
                    <Plus className="mr-1.5 h-3.5 w-3.5" />
                    Register New Intake
                  </Link>
                </Button>
              )}
            </CardContent>
          </Card>
        )}

        {!isLoading &&
          !isError &&
          filtered.map((item) => (
            <QueueRow
              key={item.intake_id}
              item={item}
              expanded={expandedId === item.intake_id}
              onToggle={() => toggle(item.intake_id)}
              refetchQueue={refetch}
            />
          ))}
      </div>

      {/* Footer queue count info */}
      {!isLoading && !isError && filtered.length > 0 && (
        <p className="mt-6 text-center text-xs font-semibold text-slate-400 dark:text-slate-500">
          {filtered.length} active patient{filtered.length !== 1 ? "s" : ""} currently in queue
          {isFetching && " · refreshing…"}
        </p>
      )}
    </div>
  );
}
