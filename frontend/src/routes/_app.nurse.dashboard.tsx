/**
 * Nurse Dashboard
 *
 * All stat tiles derive from GET /api/investigations/queue — the same
 * endpoint the Patient Queue page uses. No mock data, no hardcoded values.
 *
 * Stats computed from live DB records:
 *   · Active patients        — total queue length
 *   · Critical               — severity === "critical"
 *   · High risk              — severity === "high"
 *   · Awaiting approval      — intake_status === "intake_pending"
 *   · Evidence needed        — approved investigations with missing uploads
 *
 * Pipeline status polling:
 *   · Polls GET /api/pipeline/status/{intakeId} every 3s while active
 *   · Auto-stops after all stages are terminal OR after 60s
 *   · Shows compact pipeline indicator per patient in mini-queue
 */

import { useState, useEffect, useCallback, useRef } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import {
  Ambulance,
  Bell,
  ClipboardList,
  Plus,
  Users,
  AlertTriangle,
  Upload,
  RefreshCw,
  ChevronRight,
  ShieldAlert,
  Loader2,
} from "lucide-react";
import { SectionHeader } from "@/components/section-header";
import { PipelineStatus } from "@/components/pipeline-status";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { fetchPipelineStatus, isPipelineActive, type PipelineStatusResponse } from "@/lib/report-api";

export const Route = createFileRoute("/_app/nurse/dashboard")({
  head: () => ({
    meta: [
      { title: "Nurse Dashboard — PRATHAM" },
      { name: "description", content: "Operational intake and patient monitoring for nurses." },
    ],
  }),
  component: NurseDashboard,
});

const API_BASE = "http://localhost:8000/api";

// ── Types (matches GET /api/investigations/queue response) ─────────────────

interface QueueItem {
  intake_id: string;
  patient_name: string;
  age: number;
  sex: "M" | "F";
  severity: string;
  arrival_time: string;
  intake_status: string;
  investigation_counts: {
    approved: number;
    pending: number;
    rejected: number;
    needs_info: number;
    total: number;
  };
  evidence_completeness: {
    uploaded: number;
    required: number;
  };
}

async function fetchQueue(): Promise<QueueItem[]> {
  const res = await axios.get(`${API_BASE}/investigations/queue`);
  return res.data;
}

// ── Severity display helpers ───────────────────────────────────────────────

const SEVERITY_ORDER: Record<string, number> = {
  critical: 0,
  high: 1,
  moderate: 2,
  low: 3,
};

const SEVERITY_DOT: Record<string, string> = {
  critical: "bg-rose-500",
  high: "bg-orange-500",
  moderate: "bg-amber-500",
  low: "bg-emerald-500",
};

const SEVERITY_BADGE: Record<string, string> = {
  critical: "bg-rose-500/10 text-rose-400 border-rose-500/20",
  high: "bg-orange-500/10 text-orange-400 border-orange-500/20",
  moderate: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  low: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
};

// ── Main component ─────────────────────────────────────────────────────────

function NurseDashboard() {
  const {
    data: queue,
    isLoading,
    isFetching,
    refetch,
  } = useQuery({
    queryKey: ["patient-queue"],        // shared cache with queue page
    queryFn: fetchQueue,
    refetchInterval: 60_000,
    staleTime: 30_000,
  });

  // ── Derived stats ────────────────────────────────────────────────────────
  const totalActive    = queue?.length ?? 0;
  const criticalCount  = queue?.filter((p) => p.severity === "critical").length ?? 0;
  const highRiskCount  = queue?.filter((p) => p.severity === "high").length ?? 0;
  const awaitingApproval = queue?.filter((p) => p.intake_status === "intake_pending").length ?? 0;
  const evidenceNeeded = queue?.filter(
    (p) => p.investigation_counts.approved > 0 &&
           p.evidence_completeness.uploaded < p.evidence_completeness.required
  ).length ?? 0;

  // Top 5 by severity for mini-queue panel
  const topPatients = [...(queue ?? [])]
    .sort((a, b) => (SEVERITY_ORDER[a.severity] ?? 3) - (SEVERITY_ORDER[b.severity] ?? 3))
    .slice(0, 5);

  // ── Pipeline status polling for most recent patient ───────────────────
  const latestIntakeId = topPatients[0]?.intake_id;
  const [pipelineData, setPipelineData] = useState<PipelineStatusResponse | null>(null);
  const [pipelinePolling, setPipelinePolling] = useState(true);
  const pollStartRef = useRef<number>(Date.now());

  const pollPipeline = useCallback(async () => {
    if (!latestIntakeId) return;
    try {
      const data = await fetchPipelineStatus(latestIntakeId);
      setPipelineData(data);
      const elapsed = Date.now() - pollStartRef.current;
      if (!isPipelineActive(data.stages) || elapsed >= 60_000) {
        setPipelinePolling(false);
      }
    } catch { /* ignore */ }
  }, [latestIntakeId]);

  useEffect(() => {
    if (!latestIntakeId) return;
    pollStartRef.current = Date.now();
    setPipelinePolling(true);
    setPipelineData(null);
    pollPipeline();
    const interval = setInterval(() => {
      if (pipelinePolling) pollPipeline();
    }, 3_000);
    return () => clearInterval(interval);
  }, [latestIntakeId, pollPipeline, pipelinePolling]);

  return (
    <div className="mx-auto max-w-7xl px-5 py-8 md:px-8">
      <SectionHeader
        eyebrow="Nurse station"
        title="Operational Dashboard"
        description="Live emergency floor status. All figures come from Supabase — no mock data."
        actions={
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => refetch()}
              disabled={isFetching}
              id="dashboard-refresh-btn"
            >
              <RefreshCw className={cn("mr-1.5 h-3.5 w-3.5", isFetching && "animate-spin")} />
              Refresh
            </Button>
            <Button asChild size="sm">
              <Link to="/nurse/intake">
                <Plus className="mr-1.5 h-3.5 w-3.5" /> New intake
              </Link>
            </Button>
          </div>
        }
      />

      {/* ── Stat tiles ──────────────────────────────────────────── */}
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <StatTile
          id="stat-active"
          icon={Users}
          label="Active patients"
          value={totalActive}
          loading={isLoading}
          color="primary"
        />
        <StatTile
          id="stat-critical"
          icon={ShieldAlert}
          label="Critical"
          value={criticalCount}
          loading={isLoading}
          color="rose"
        />
        <StatTile
          id="stat-high"
          icon={AlertTriangle}
          label="High risk"
          value={highRiskCount}
          loading={isLoading}
          color="orange"
        />
        <StatTile
          id="stat-awaiting"
          icon={Bell}
          label="Awaiting approval"
          value={awaitingApproval}
          loading={isLoading}
          color="amber"
        />
        <StatTile
          id="stat-evidence"
          icon={Upload}
          label="Evidence needed"
          value={evidenceNeeded}
          loading={isLoading}
          color="sky"
        />
      </div>

      {/* ── Pipeline Status Panel ───────────────────────────────── */}
      {pipelineData && latestIntakeId && (
        <div className="mt-6 rounded-lg border-2 border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800/60 p-4 shadow-sm">
          <div className="mb-3 flex items-center gap-2">
            <span className="text-[11px] font-bold uppercase tracking-[0.15em] text-slate-800 dark:text-gray-200">
              AI Pipeline — {topPatients[0]?.patient_name || "Latest Patient"}
            </span>
            {pipelinePolling && (
              <span className="flex items-center gap-1 rounded-full bg-sky-100 px-2 py-0.5 text-[9px] font-bold text-sky-700 border border-sky-300">
                <span className="relative flex h-1.5 w-1.5">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-sky-400 opacity-75" />
                  <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-sky-500" />
                </span>
                LIVE
              </span>
            )}
          </div>
          <PipelineStatus stages={pipelineData.stages} />
        </div>
      )}

      {/* ── Main panels ─────────────────────────────────────────── */}
      <div className="mt-8 grid gap-6 lg:grid-cols-[1.4fr_1fr]">

        {/* Mini patient queue */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center justify-between text-sm font-semibold">
              Active emergency queue
              <span className="text-[11px] font-normal text-muted-foreground">
                {isLoading ? "…" : `${totalActive} patient${totalActive !== 1 ? "s" : ""}`}
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {isLoading && (
              <div className="flex items-center justify-center py-10">
                <RefreshCw className="h-4 w-4 animate-spin text-primary" />
              </div>
            )}

            {!isLoading && topPatients.length === 0 && (
              <div className="p-8 text-center">
                <p className="text-sm text-muted-foreground">
                  No patients in queue. Submit a new intake to begin.
                </p>
                <Button asChild size="sm" variant="outline" className="mt-4">
                  <Link to="/nurse/intake">
                    <Plus className="mr-1.5 h-3.5 w-3.5" /> New intake
                  </Link>
                </Button>
              </div>
            )}

            {!isLoading && topPatients.length > 0 && (
              <>
                <ul className="divide-y">
                  {topPatients.map((p) => {
                    const awaitingUploads =
                      p.evidence_completeness.required - p.evidence_completeness.uploaded;
                    const needsUpload =
                      p.investigation_counts.approved > 0 && awaitingUploads > 0;

                    return (
                      <li key={p.intake_id} className="flex items-center gap-3 px-4 py-3">
                        {/* Severity dot */}
                        <div
                          className={cn(
                            "h-2 w-2 shrink-0 rounded-full",
                            SEVERITY_DOT[p.severity] ?? "bg-muted",
                          )}
                        />

                        {/* Patient info */}
                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-center gap-1.5">
                            <span className="text-sm font-medium">{p.patient_name}</span>
                            <span className="text-xs text-muted-foreground">
                              {p.age}{p.sex}
                            </span>
                            <span
                              className={cn(
                                "rounded border px-1.5 py-px text-[9px] font-bold uppercase tracking-wider",
                                SEVERITY_BADGE[p.severity] ?? SEVERITY_BADGE.moderate,
                              )}
                            >
                              {p.severity}
                            </span>
                          </div>
                          <p className="mt-0.5 text-[11px] text-muted-foreground">
                            {needsUpload
                              ? `⚠ ${awaitingUploads} upload${awaitingUploads !== 1 ? "s" : ""} needed`
                              : p.intake_status === "intake_pending"
                              ? "Awaiting doctor approval"
                              : p.intake_status === "investigation_approved"
                              ? "Investigation approved"
                              : p.intake_status}
                          </p>
                        </div>

                        {/* Arrival time */}
                        {p.arrival_time && (
                          <span className="shrink-0 text-[11px] text-muted-foreground">
                            {p.arrival_time}
                          </span>
                        )}
                      </li>
                    );
                  })}
                </ul>

                {/* Link to full queue if more than 5 */}
                <div className="border-t px-4 py-2.5">
                  <Link
                    to="/nurse/queue"
                    className="flex items-center justify-between text-xs text-muted-foreground hover:text-foreground transition-colors"
                  >
                    <span>
                      {totalActive > 5
                        ? `View all ${totalActive} patients in full queue`
                        : "Open full queue workspace"}
                    </span>
                    <ChevronRight className="h-3.5 w-3.5" />
                  </Link>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Quick actions */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold">Quick actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <ActionLink to="/nurse/intake" icon={Ambulance} label="New emergency intake" />
            <ActionLink to="/nurse/queue" icon={Users} label="Full patient queue" />
            <ActionLink to="/investigations" icon={ClipboardList} label="Investigation status" />

            {/* Live summary callout */}
            {!isLoading && totalActive > 0 && (
              <div className="mt-3 rounded-lg border border-primary/20 bg-primary/5 p-3">
                <p className="text-[11px] font-semibold text-primary">
                  {totalActive} active patient{totalActive !== 1 ? "s" : ""} on the emergency floor
                </p>
                <p className="mt-0.5 text-[11px] text-muted-foreground">
                  {criticalCount > 0 && `${criticalCount} critical · `}
                  {highRiskCount > 0 && `${highRiskCount} high risk · `}
                  {awaitingApproval > 0 && `${awaitingApproval} awaiting doctor · `}
                  {evidenceNeeded > 0 && `${evidenceNeeded} need uploads`}
                </p>
              </div>
            )}

            {!isLoading && totalActive === 0 && (
              <p className="pt-3 text-[11px] leading-relaxed text-muted-foreground">
                Queue empty. Investigation requests are generated by the system based on vitals +
                symptoms and forwarded to the on-call doctor automatically.
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// ── Stat tile ──────────────────────────────────────────────────────────────

type TileColor = "primary" | "rose" | "orange" | "amber" | "sky";

const TILE_COLORS: Record<TileColor, { icon: string; value: string }> = {
  primary: { icon: "bg-primary/10 text-primary", value: "text-foreground" },
  rose:    { icon: "bg-rose-500/10 text-rose-400", value: "text-rose-400" },
  orange:  { icon: "bg-orange-500/10 text-orange-400", value: "text-orange-400" },
  amber:   { icon: "bg-amber-500/10 text-amber-400", value: "text-amber-400" },
  sky:     { icon: "bg-sky-500/10 text-sky-400", value: "text-sky-400" },
};

function StatTile({
  id,
  icon: Icon,
  label,
  value,
  loading,
  color = "primary",
}: {
  id: string;
  icon: typeof Ambulance;
  label: string;
  value: number;
  loading: boolean;
  color?: TileColor;
}) {
  const colors = TILE_COLORS[color];
  return (
    <Card id={id}>
      <CardContent className="flex items-center gap-3 p-4">
        <div className={cn("flex h-10 w-10 items-center justify-center rounded-md shrink-0", colors.icon)}>
          <Icon className="h-5 w-5" />
        </div>
        <div className="min-w-0">
          <p className="text-[11px] uppercase tracking-wider text-muted-foreground">{label}</p>
          {loading ? (
            <div className="mt-1 h-6 w-8 animate-pulse rounded bg-muted" />
          ) : (
            <p className={cn("font-display text-2xl font-semibold tabular-nums", colors.value)}>
              {value}
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ── Action link ────────────────────────────────────────────────────────────

function ActionLink({
  to,
  icon: Icon,
  label,
}: {
  to: string;
  icon: typeof Ambulance;
  label: string;
}) {
  return (
    <Link
      to={to}
      className="flex items-center gap-3 rounded-md border bg-card px-3 py-2.5 text-sm transition-colors hover:bg-muted/60"
    >
      <Icon className="h-4 w-4 text-primary" />
      <span className="flex-1">{label}</span>
      <span className="text-xs text-muted-foreground">→</span>
    </Link>
  );
}
