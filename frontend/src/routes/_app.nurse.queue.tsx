/**
 * Patient Queue — Nurse workstation
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

const SEVERITY_ORDER: Record<string, number> = {
  critical: 0,
  high: 1,
  moderate: 2,
  low: 3,
};

const SEVERITY_STYLES: Record<string, { dot: string; badge: string }> = {
  critical: {
    dot: "bg-rose-500",
    badge: "bg-rose-100 text-rose-800 border-rose-300",
  },
  high: {
    dot: "bg-orange-500",
    badge: "bg-orange-100 text-orange-800 border-orange-300",
  },
  moderate: {
    dot: "bg-amber-500",
    badge: "bg-amber-100 text-amber-800 border-amber-300",
  },
  low: {
    dot: "bg-emerald-500",
    badge: "bg-emerald-100 text-emerald-800 border-emerald-300",
  },
};

function sevStyle(s: string) {
  return SEVERITY_STYLES[s] ?? SEVERITY_STYLES.moderate;
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

  // Action Required: approved investigations exist but uploads are missing
  const awaitingUploads = ec.required - ec.uploaded;
  const actionRequired = counts.approved > 0 && awaitingUploads > 0;

  return (
    <div
      className={cn(
        "overflow-hidden rounded-xl border-2 transition-all duration-200",
        expanded
          ? "border-primary shadow-[0_0_0_1px_hsl(var(--primary)/0.15)] bg-slate-50/30"
          : "border-slate-300 hover:border-slate-400 hover:shadow-sm",
      )}
    >
      {/* Summary row — always visible, click to expand */}
      <button
        type="button"
        id={`queue-row-${item.intake_id}`}
        onClick={onToggle}
        className="flex w-full items-start gap-4 px-5 py-4 text-left transition-colors hover:bg-slate-50"
      >
        {/* Severity dot */}
        <div className="mt-1.5 shrink-0">
          <div className={cn("h-2.5 w-2.5 rounded-full ring-4 ring-current/15", sev.dot)} />
        </div>

        {/* Patient info */}
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-bold text-slate-900 text-sm">{item.patient_name}</span>
            <span className="text-xs font-bold text-slate-700">
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
            {item.arrival_time && (
              <span className="text-[11px] font-bold text-slate-700">
                Arrived {item.arrival_time}
              </span>
            )}
            {/* Action Required badge */}
            {actionRequired && (
              <span className="flex items-center gap-1 rounded-md border border-amber-400 bg-amber-50 px-2 py-px text-[10px] font-bold uppercase tracking-wider text-amber-800">
                <AlertCircle className="h-3 w-3" />
                {awaitingUploads === 1
                  ? "1 upload needed"
                  : `${awaitingUploads} uploads needed`}
              </span>
            )}
            {ec.required > 0 && complete && (
              <span className="flex items-center gap-1 rounded-md border border-emerald-400 bg-emerald-50 px-2 py-px text-[10px] font-bold uppercase tracking-wider text-emerald-800">
                <CheckCircle2 className="h-3 w-3" />
                All uploaded
              </span>
            )}
          </div>

          {/* Investigation + evidence summary */}
          <div className="mt-1.5 flex flex-wrap items-center gap-3 text-xs font-semibold text-slate-800">
            {counts.approved > 0 && (
              <span className="flex items-center gap-1 text-emerald-800">
                <CheckCircle2 className="h-3 w-3" />
                {counts.approved} approved
              </span>
            )}
            {counts.pending > 0 && (
              <span className="flex items-center gap-1 text-amber-800">
                <Clock className="h-3 w-3" />
                {counts.pending} pending
              </span>
            )}
            {counts.rejected > 0 && (
              <span className="flex items-center gap-1 text-rose-800">
                <AlertCircle className="h-3 w-3" />
                {counts.rejected} rejected
              </span>
            )}
            {counts.total === 0 && (
              <span className="text-slate-600">No investigations yet</span>
            )}
          </div>

          {/* Evidence completeness pill */}
          {ec.required > 0 && (
            <div className="mt-2 flex items-center gap-2">
              <div className="h-2 w-20 overflow-hidden rounded-full bg-slate-200">
                <div
                  className={cn(
                    "h-full rounded-full transition-all duration-500",
                    complete ? "bg-emerald-600" : "bg-amber-600",
                  )}
                  style={{ width: `${completePct}%` }}
                />
              </div>
              <span className={cn("text-[10px] font-bold", complete ? "text-emerald-850" : "text-amber-850")}>
                {ec.uploaded} / {ec.required} evidence
              </span>
            </div>
          )}
        </div>

        {/* Expand / collapse toggle */}
        <div className="shrink-0 self-center">
          {expanded ? (
            <ChevronUp className="h-4 w-4 text-slate-800 font-extrabold" />
          ) : (
            <ChevronDown className="h-4 w-4 text-slate-800 font-extrabold" />
          )}
        </div>
      </button>

      <div className="flex flex-wrap items-center justify-between gap-3 border-t-2 border-slate-350 bg-slate-50 px-5 py-2.5">
        <PipelineStatus status={item.pipeline_status} compact />
        <Button asChild size="sm" variant="outline" className="border-slate-300 font-bold bg-white text-slate-800 hover:bg-slate-100 hover:text-slate-900 shadow-sm">
          <Link to="/doctor/report/$intakeId" params={{ intakeId: item.intake_id }}>
            <FileText className="mr-1.5 h-3.5 w-3.5" />
            View report
          </Link>
        </Button>
      </div>

      {/* Expanded workspace */}
      {expanded && (
        <div className="border-t-2 border-slate-350 bg-white px-5 py-5">
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

  // Sort by severity, then filter by search
  const filtered = useMemo(() => {
    if (!queue) return [];
    const q = search.toLowerCase().trim();
    return queue
      .filter((p) =>
        !q || p.patient_name.toLowerCase().includes(q) || p.severity.toLowerCase().includes(q),
      )
      .sort((a, b) => (SEVERITY_ORDER[a.severity] ?? 3) - (SEVERITY_ORDER[b.severity] ?? 3));
  }, [queue, search]);

  const toggle = (id: string) => setExpandedId((curr) => (curr === id ? null : id));

  return (
    <div className="mx-auto max-w-4xl px-5 py-8 md:px-8">
      <SectionHeader
        eyebrow="Nurse station"
        title="Patient Queue"
        description="Live emergency queue sorted by severity. Select a patient to upload evidence and view investigation status."
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
          placeholder="Search by name or severity…"
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
                    <div className="mt-2 flex gap-3">
                      <div className="h-3 w-20 animate-pulse rounded bg-muted/60" />
                      <div className="h-3 w-20 animate-pulse rounded bg-muted/60" />
                    </div>
                    <div className="mt-3 flex items-center gap-2">
                      <div className="h-1 w-20 animate-pulse rounded-full bg-muted" />
                      <div className="h-2 w-16 animate-pulse rounded bg-muted" />
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
                  ? "Try a different name or severity level."
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
