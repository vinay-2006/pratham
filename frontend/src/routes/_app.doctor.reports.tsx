/**
 * Clinical Reports List — Doctor Station
 *
 * Operational reports queue. Displays cases whose diagnostic pipeline is finished
 * and are ready for doctor signature or currently under review.
 */

import { useState, useMemo } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import {
  FileText,
  Search,
  ArrowRight,
  Loader2,
  AlertCircle,
  Clock,
  Sparkles,
  RefreshCw,
  Award,
  CheckCircle,
} from "lucide-react";
import { SectionHeader } from "@/components/section-header";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { fetchDoctorReportsList, type DoctorReportItem } from "@/lib/patient-queue-api";
import { WorkflowStatus, WORKFLOW_LABELS } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_app/doctor/reports")({
  head: () => ({
    meta: [
      { title: "Clinical Reports — PRATHAM" },
      { name: "description", content: "List of completed AI-powered clinical intelligence reports." },
    ],
  }),
  component: ClinicalReportsPage,
});

const SEVERITY_STYLES: Record<string, string> = {
  critical: "bg-rose-100 dark:bg-rose-950/60 text-rose-800 dark:text-rose-300 border-rose-250",
  high: "bg-orange-100 dark:bg-orange-950/60 text-orange-800 dark:text-orange-300 border-orange-250",
  moderate: "bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 border-amber-250",
  low: "bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border-emerald-250",
};

function ClinicalReportsPage() {
  const [search, setSearch] = useState("");
  const [sortField, setSortField] = useState<"updated_at" | "patient_name">("updated_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  const { data: reports, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ["doctor-reports-list"],
    queryFn: fetchDoctorReportsList,
    refetchInterval: 15_000,
    staleTime: 10_000,
  });

  const filtered = useMemo(() => {
    if (!reports) return [];
    
    let result = [...reports];

    // 1. Search Query
    const q = search.toLowerCase().trim();
    if (q) {
      result = result.filter(
        (p) =>
          p.patient_name.toLowerCase().includes(q) ||
          p.case_id.toLowerCase().includes(q) ||
          (p.chief_complaint || "").toLowerCase().includes(q)
      );
    }

    // 2. Sorting
    result.sort((a, b) => {
      let comparison = 0;
      if (sortField === "updated_at") {
        const timeA = new Date(a.updated_at || a.created_at).getTime();
        const timeB = new Date(b.updated_at || b.created_at).getTime();
        comparison = timeA - timeB;
      } else if (sortField === "patient_name") {
        comparison = a.patient_name.localeCompare(b.patient_name);
      }
      return sortOrder === "desc" ? -comparison : comparison;
    });

    return result;
  }, [reports, search, sortField, sortOrder]);

  const formatDate = (iso?: string) => {
    if (!iso) return "—";
    try {
      const date = new Date(iso);
      return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    } catch {
      return "—";
    }
  };

  // Status mapping matching clinical colors
  const statusBadge = (status: WorkflowStatus) => {
    if (status === WorkflowStatus.REPORT_READY) {
      return "bg-emerald-50 dark:bg-emerald-950/20 text-emerald-700 border-emerald-250";
    }
    return "bg-teal-50 dark:bg-teal-950/20 text-teal-700 border-teal-250";
  };

  return (
    <div className="mx-auto max-w-5xl px-5 py-8 md:px-8">
      <SectionHeader
        eyebrow="Clinical Worklist"
        title="Clinical Reports"
        description="Comprehensive diagnostic report repository. Select a patient case to review diagnostic summaries and sign off closure."
        actions={
          <Button
            size="sm"
            variant="outline"
            onClick={() => refetch()}
            disabled={isFetching}
          >
            <RefreshCw className={cn("mr-1.5 h-3.5 w-3.5", isFetching && "animate-spin")} />
            Sync Reports
          </Button>
        }
      />

      {/* Search Filter */}
      <div className="relative mt-6">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input
          type="text"
          placeholder="Search by Case ID, name, or chief complaint…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-xl border bg-slate-50 dark:bg-slate-900 py-3 pl-10 pr-4 text-xs outline-none focus:border-teal-500/60 focus:bg-background"
        />
      </div>

      {/* Reports Queue Cards List */}
      <div className="mt-6 space-y-4">
        {isLoading && (
          <div className="space-y-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="rounded-2xl border p-6 bg-slate-50/20 dark:bg-slate-900/20 animate-pulse h-[110px]" />
            ))}
          </div>
        )}

        {isError && (
          <Card className="border-rose-500/20 bg-rose-500/5">
            <CardContent className="flex items-center gap-3 p-6 text-sm text-rose-500">
              <AlertCircle className="h-5 w-5 shrink-0" />
              <div>
                <p className="font-semibold">Failed to fetch Clinical Reports</p>
                <p className="text-xs mt-0.5 text-muted-foreground">{error?.message}</p>
              </div>
            </CardContent>
          </Card>
        )}

        {!isLoading && !isError && filtered.length === 0 && (
          <Card>
            <CardContent className="p-12 text-center text-slate-400">
              <FileText className="mx-auto h-8 w-8 text-slate-300 dark:text-slate-700 mb-2" />
              No clinical reports pending review.
            </CardContent>
          </Card>
        )}

        {!isLoading &&
          !isError &&
          filtered.map((item) => {
            const sevBadge = SEVERITY_STYLES[item.severity] || "bg-slate-100";
            
            // Reconstruct Completed vs Pending tests status icons
            const completedTests = item.completed_analyses || [];
            
            return (
              <Card
                key={item.intake_id}
                className="overflow-hidden border border-slate-200 hover:border-slate-350 dark:border-slate-800 dark:hover:border-slate-700 shadow-sm transition-all"
              >
                <CardContent className="p-5 flex flex-wrap items-center justify-between gap-4 text-xs">
                  {/* Case demographics */}
                  <div className="min-w-[200px]">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-slate-400 font-bold">{item.case_id}</span>
                      <span className="font-bold text-slate-900 dark:text-slate-100 text-sm">
                        {item.patient_name}
                      </span>
                      <span className="text-slate-500 font-semibold">{item.age}{item.sex}</span>
                    </div>
                    {item.chief_complaint && (
                      <p className="mt-1 text-slate-500 leading-normal line-clamp-1 max-w-sm">
                        {item.chief_complaint}
                      </p>
                    )}
                  </div>

                  {/* Diagnostic Completed Tests Indicators (Task 5 & Reports status indicator) */}
                  <div className="flex flex-col gap-1.5 min-w-[150px]">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                      Diagnostic Analyses
                    </span>
                    <div className="flex flex-wrap items-center gap-2">
                      {["nlp", "risk", "lab", "imaging"].map((stage) => {
                        const status = item.pipeline_status?.[stage as any];
                        const isDone = status === "completed";
                        
                        return (
                          <span
                            key={stage}
                            className={cn(
                              "inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold uppercase",
                              isDone
                                ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                                : "bg-amber-500/10 text-amber-600 dark:text-amber-400"
                            )}
                          >
                            <span className={cn("h-1.5 w-1.5 rounded-full", isDone ? "bg-emerald-500" : "bg-amber-500")} />
                            {stage}
                          </span>
                        );
                      })}
                    </div>
                  </div>

                  {/* Status, Progress and Time */}
                  <div className="flex flex-col gap-1 min-w-[120px]">
                    <div>
                      <span className={cn("inline-flex items-center rounded-full border px-2 py-0.5 text-[9px] font-extrabold uppercase tracking-wider", statusBadge(item.status))}>
                        {WORKFLOW_LABELS[item.status] || item.status}
                      </span>
                    </div>
                    <span className="text-[10px] font-semibold text-slate-400 font-mono flex items-center gap-1 mt-1">
                      <Clock className="h-3.5 w-3.5" />
                      Report: {formatDate(item.updated_at || item.created_at)}
                    </span>
                  </div>

                  {/* Actions & Priorities */}
                  <div className="flex items-center gap-3 shrink-0 ml-auto">
                    <span className={cn("rounded-full border px-2 py-0.5 text-[9px] font-extrabold uppercase tracking-wider", sevBadge)}>
                      {item.severity}
                    </span>
                    <Button asChild size="sm" className="bg-teal-600 hover:bg-teal-500 text-white font-bold">
                      <Link to="/doctor/report/$intakeId" params={{ intakeId: item.intake_id }}>
                        Open Report
                        <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
                      </Link>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
      </div>
    </div>
  );
}
