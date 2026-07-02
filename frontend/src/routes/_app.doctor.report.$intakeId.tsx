/**
 * Doctor Clinical Intelligence Report Page
 *
 * Route: /doctor/report/:intakeId
 *
 * Fetches the consolidated report from GET /api/report/{intakeId}
 * and renders the full ClinicalReport component.
 * Includes PDF export capability.
 */

import { useRef } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { Activity, Download, Loader2, AlertCircle, FileText } from "lucide-react";
import { SectionHeader } from "@/components/section-header";
import { ClinicalReport } from "@/components/clinical-report";
import { fetchClinicalReport } from "@/lib/report-api";
import { Button } from "@/components/ui/button";
import { exportReportPdf } from "@/lib/pdf-export";

export const Route = createFileRoute("/_app/doctor/report/$intakeId")({
  head: () => ({
    meta: [
      { title: "Clinical Intelligence Report — PRATHAM" },
      { name: "description", content: "Full AI-powered clinical intelligence report with explainability." },
    ],
  }),
  component: ReportPage,
});

function ReportPage() {
  const { intakeId } = Route.useParams();
  const reportRef = useRef<HTMLDivElement>(null);

  const { data: report, isLoading, isError, error } = useQuery({
    queryKey: ["clinical-report", intakeId],
    queryFn: () => fetchClinicalReport(intakeId),
    staleTime: 30_000,
  });

  const handleExportPdf = async () => {
    if (!reportRef.current || !report) return;
    try {
      await exportReportPdf(report.patient_summary.name, reportRef.current);
    } catch (err) {
      console.error("PDF export failed:", err);
    }
  };

  if (isLoading) {
    return (
      <div className="mx-auto max-w-7xl px-5 py-8 md:px-8">
        <SectionHeader
          eyebrow="Doctor workstation"
          title="Clinical Intelligence Report"
          description={`Loading report for intake ${intakeId.slice(0, 8)}…`}
        />

        {/* Progressive skeleton — page structure visible immediately */}
        <div className="mt-6 space-y-6">
          {/* Patient summary + Vitals skeleton */}
          <div className="grid gap-6 lg:grid-cols-2">
            <div className="rounded-xl border p-6">
              <div className="h-4 w-32 animate-pulse rounded bg-muted mb-4" />
              <div className="space-y-3">
                <div className="h-3 w-48 animate-pulse rounded bg-muted" />
                <div className="h-3 w-36 animate-pulse rounded bg-muted" />
                <div className="h-3 w-40 animate-pulse rounded bg-muted" />
              </div>
            </div>
            <div className="rounded-xl border p-6">
              <div className="h-4 w-20 animate-pulse rounded bg-muted mb-4" />
              <div className="grid grid-cols-3 gap-3">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="rounded-md border bg-muted/20 p-3">
                    <div className="h-2 w-12 animate-pulse rounded bg-muted mb-2" />
                    <div className="h-5 w-16 animate-pulse rounded bg-muted" />
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* AI section skeletons — NLP, Risk, Lab, Imaging, Aggregation */}
          {["NLP Findings", "Risk Engine", "Lab Intelligence", "Imaging Intelligence", "Aggregation"].map((label) => (
            <div key={label} className="rounded-xl border p-6">
              <div className="flex items-center gap-2 mb-4">
                <Loader2 className="h-4 w-4 animate-spin text-primary/40" />
                <div className="h-4 w-32 animate-pulse rounded bg-muted" />
                <span className="text-[10px] uppercase tracking-wider text-muted-foreground/50">{label}</span>
              </div>
              <div className="space-y-2">
                <div className="h-3 w-full animate-pulse rounded bg-muted/60" />
                <div className="h-3 w-3/4 animate-pulse rounded bg-muted/40" />
                <div className="h-3 w-1/2 animate-pulse rounded bg-muted/30" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="mx-auto max-w-7xl px-5 py-8 md:px-8">
        <div className="flex items-center gap-3 rounded-lg border border-rose-500/20 bg-rose-500/5 p-6 text-sm text-rose-400">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <div>
            <p className="font-medium">Failed to load clinical report</p>
            <p className="mt-1 text-xs text-muted-foreground">
              {error instanceof Error ? error.message : "An unexpected error occurred."}
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!report) return null;

  return (
    <div className="mx-auto max-w-7xl px-5 py-8 md:px-8">
      <SectionHeader
        eyebrow="Doctor workstation"
        title="Clinical Intelligence Report"
        description={`Comprehensive AI-powered analysis for ${report.patient_summary.name} · Intake ${intakeId.slice(0, 8)}…`}
        actions={
          <div className="flex items-center gap-2">
            <Button size="sm" variant="outline" onClick={handleExportPdf}>
              <Download className="mr-1.5 h-3.5 w-3.5" />
              Export PDF
            </Button>
          </div>
        }
      />

      <div className="mt-6">
        <ClinicalReport report={report} reportRef={reportRef} />
      </div>
    </div>
  );
}
