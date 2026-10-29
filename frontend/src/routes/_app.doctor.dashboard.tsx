import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowRight,
  Bell,
  Brain,
  FileText,
  ShieldAlert,
  Stethoscope,
  Users,
  CheckCircle2,
  Clock,
  Loader2,
} from "lucide-react";
import { SectionHeader } from "@/components/section-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { fetchDoctorDashboardStats } from "@/lib/patient-queue-api";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_app/doctor/dashboard")({
  head: () => ({
    meta: [
      { title: "Doctor Dashboard — PRATHAM" },
      { name: "description", content: "ED Clinical review workstation dashboard." },
    ],
  }),
  component: DoctorDashboard,
});

function TrendBadge({ value }: { value: number }) {
  if (value > 0) {
    return (
      <span className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/20 px-2 py-0.5 rounded-full inline-flex items-center gap-0.5">
        ▲ +{value} today
      </span>
    );
  }
  return (
    <span className="text-[10px] font-semibold text-slate-400 dark:text-slate-500 bg-slate-50 dark:bg-slate-900 px-2 py-0.5 rounded-full inline-flex items-center">
      0 today
    </span>
  );
}

function DoctorDashboard() {
  const { data: stats, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ["doctor-dashboard-stats"],
    queryFn: fetchDoctorDashboardStats,
    refetchInterval: 15_000, // Update automatically every 15s
    staleTime: 10_000,
  });

  return (
    <div className="mx-auto max-w-7xl px-5 py-8 md:px-8">
      <SectionHeader
        eyebrow="Doctor workstation"
        title="Clinical Dashboard"
        description="Emergency clinical workflow tracker, investigation approvals, and report review status overview."
        actions={
          <Button
            size="sm"
            variant="outline"
            onClick={() => refetch()}
            disabled={isFetching}
          >
            <Loader2 className={cn("mr-1.5 h-3.5 w-3.5 hidden", isFetching && "inline animate-spin")} />
            Sync Dashboard
          </Button>
        }
      />

      {/* Stats Cards (Task 1 & Task 8) */}
      <div className="mt-6 grid gap-4 grid-cols-2 lg:grid-cols-4">
        {/* Card 1: Total Patients */}
        <Card className="shadow-sm">
          <CardContent className="p-5 flex flex-col justify-between h-full min-h-[110px]">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                👥 Total Patients
              </span>
              <Users className="h-4 w-4 text-slate-400" />
            </div>
            <div className="mt-3 flex items-baseline justify-between">
              <span className="font-display text-3xl font-semibold tabular-nums text-slate-800 dark:text-slate-100">
                {isLoading ? "…" : stats?.total_patients ?? 0}
              </span>
              {!isLoading && stats && <TrendBadge value={stats.total_patients_trend} />}
            </div>
          </CardContent>
        </Card>

        {/* Card 2: Cases Closed */}
        <Card className="shadow-sm">
          <CardContent className="p-5 flex flex-col justify-between h-full min-h-[110px]">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                ✅ Cases Closed
              </span>
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            </div>
            <div className="mt-3 flex items-baseline justify-between">
              <span className="font-display text-3xl font-semibold tabular-nums text-emerald-600 dark:text-emerald-400">
                {isLoading ? "…" : stats?.cases_closed ?? 0}
              </span>
              {!isLoading && stats && <TrendBadge value={stats.cases_closed_trend} />}
            </div>
          </CardContent>
        </Card>

        {/* Card 3: Pending Approvals */}
        <Card className="shadow-sm">
          <CardContent className="p-5 flex flex-col justify-between h-full min-h-[110px]">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                ⏳ Pending Approvals
              </span>
              <Clock className="h-4 w-4 text-amber-500" />
            </div>
            <div className="mt-3 flex items-baseline justify-between">
              <span className="font-display text-3xl font-semibold tabular-nums text-amber-600 dark:text-amber-500">
                {isLoading ? "…" : stats?.pending_approvals ?? 0}
              </span>
              {!isLoading && stats && <TrendBadge value={stats.pending_approvals_trend} />}
            </div>
          </CardContent>
        </Card>

        {/* Card 4: Clinical Reviews Remaining */}
        <Card className="shadow-sm">
          <CardContent className="p-5 flex flex-col justify-between h-full min-h-[110px]">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                📋 Reviews Remaining
              </span>
              <FileText className="h-4 w-4 text-sky-500" />
            </div>
            <div className="mt-3 flex items-baseline justify-between">
              <span className="font-display text-3xl font-semibold tabular-nums text-sky-600 dark:text-sky-400">
                {isLoading ? "…" : stats?.clinical_reviews_remaining ?? 0}
              </span>
              {!isLoading && stats && <TrendBadge value={stats.clinical_reviews_remaining_trend} />}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        {/* Left Side Info Panel */}
        <div className="space-y-6">
          <Card>
            <CardHeader className="pb-3 border-b border-slate-100 dark:border-slate-800">
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <Stethoscope className="h-4 w-4 text-primary" />
                Workstation Navigation
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-5 space-y-3">
              <Jump to="/doctor/review" icon={Stethoscope} label="Clinical Worklist" desc="Review active patient profiles, approve tests, or return to nurse." />
              <Jump to="/doctor/reports" icon={FileText} label="Clinical Reports" desc="Open generated AI diagnostic summaries and complete review closure." />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3 border-b border-slate-100 dark:border-slate-800">
              <CardTitle className="text-sm font-semibold">Diagnostic Support Modules</CardTitle>
            </CardHeader>
            <CardContent className="pt-5 space-y-3">
              <Jump to="/explainability" icon={Brain} label="Explainability Panel" desc="Inspect clinical references and deep AI rationale models." />
              <Jump to="/confidence" icon={ShieldAlert} label="Confidence Assessment" desc="Assess evidence metrics, completeness ratios, and reliability." />
            </CardContent>
          </Card>
        </div>

        {/* Right Side Overview Cards */}
        <div className="space-y-6">
          <Card>
            <CardHeader className="pb-3 border-b border-slate-100 dark:border-slate-800">
              <CardTitle className="text-sm font-semibold">Worklist Priority Gating</CardTitle>
            </CardHeader>
            <CardContent className="pt-5 text-sm leading-relaxed text-slate-600 dark:text-slate-400 space-y-4">
              <p>
                PRATHAM prioritizes cases based on operational severity levels:
              </p>
              <div className="flex flex-col gap-2">
                <div className="flex items-center gap-3">
                  <span className="h-2 w-2 rounded-full bg-rose-500" />
                  <span className="text-xs font-bold text-slate-700 dark:text-slate-300">Critical</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="h-2 w-2 rounded-full bg-orange-500" />
                  <span className="text-xs font-bold text-slate-700 dark:text-slate-300">High Priority</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="h-2 w-2 rounded-full bg-amber-500" />
                  <span className="text-xs font-bold text-slate-700 dark:text-slate-300">Moderate</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="h-2 w-2 rounded-full bg-emerald-500" />
                  <span className="text-xs font-bold text-slate-700 dark:text-slate-300">Routine</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function Jump({
  to,
  icon: Icon,
  label,
  desc,
}: {
  to: string;
  icon: typeof Stethoscope;
  label: string;
  desc: string;
}) {
  return (
    <Link
      to={to}
      className="flex items-start gap-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 bg-card p-4 transition-all hover:bg-slate-50 dark:hover:bg-slate-900/60 shadow-sm"
    >
      <div className="p-2.5 rounded-xl bg-teal-500/10 text-teal-600 dark:text-teal-400 shrink-0">
        <Icon className="h-5 w-5" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-bold text-slate-800 dark:text-slate-200">{label}</p>
        <p className="mt-0.5 text-xs text-slate-400 dark:text-slate-500 leading-normal">{desc}</p>
      </div>
      <ArrowRight className="h-4 w-4 text-slate-400 self-center shrink-0" />
    </Link>
  );
}
