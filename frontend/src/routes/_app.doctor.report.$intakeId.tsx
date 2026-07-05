/**
 * Doctor Clinical Intelligence Report Page
 *
 * Route: /doctor/report/:intakeId
 *
 * Fetches the consolidated report from GET /api/report/{intakeId}
 * and renders the full ClinicalReport component.
 *
 * Pipeline status polling:
 *   - Polls GET /api/pipeline/status/{intakeId} every 3s while active
 *   - Auto-stops after all stages are terminal OR after 60s max
 *   - Displays live execution state at the top of the report
 */

import { useRef, useState, useEffect, useCallback } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { Activity, Download, Loader2, AlertCircle, FileText } from "lucide-react";
import { SectionHeader } from "@/components/section-header";
import { ClinicalReport } from "@/components/clinical-report";
import { PipelineStatus } from "@/components/pipeline-status";
import {
  fetchClinicalReport,
  fetchPipelineStatus,
  isPipelineActive,
  type PipelineStatusResponse,
} from "@/lib/report-api";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/_app/doctor/report/$intakeId")({
  head: () => ({
    meta: [
      { title: "Clinical Intelligence Report — PRATHAM" },
      { name: "description", content: "Full AI-powered clinical intelligence report with explainability." },
    ],
  }),
  component: ReportPage,
});

const POLL_INTERVAL = 3_000;    // 3 seconds
const POLL_MAX_DURATION = 60_000; // 60 seconds maximum

function ReportPage() {
  const { intakeId } = Route.useParams();
  const reportRef = useRef<HTMLDivElement>(null);
  const [pipelineData, setPipelineData] = useState<PipelineStatusResponse | null>(null);
  const [isPolling, setIsPolling] = useState(true);
  const pollStartRef = useRef<number>(Date.now());

  // ── Pipeline status polling ───────────────────────────────────────────
  const pollPipeline = useCallback(async () => {
    try {
      const data = await fetchPipelineStatus(intakeId);
      setPipelineData(data);

      const elapsed = Date.now() - pollStartRef.current;
      const stillActive = isPipelineActive(data.stages);

      // Stop polling if all stages are terminal OR timeout reached
      if (!stillActive || elapsed >= POLL_MAX_DURATION) {
        setIsPolling(false);
      }
    } catch {
      // Non-fatal: pipeline endpoint may not be available yet
    }
  }, [intakeId]);

  useEffect(() => {
    pollStartRef.current = Date.now();
    setIsPolling(true);
    pollPipeline(); // Initial fetch

    const interval = setInterval(() => {
      if (!isPolling) return;
      pollPipeline();
    }, POLL_INTERVAL);

    return () => clearInterval(interval);
  }, [intakeId, pollPipeline, isPolling]);

  // Stop polling effect
  useEffect(() => {
    if (!isPolling) return;
    const timeout = setTimeout(() => setIsPolling(false), POLL_MAX_DURATION);
    return () => clearTimeout(timeout);
  }, [isPolling]);

  const { data: report, isLoading, isError, error } = useQuery({
    queryKey: ["clinical-report", intakeId],
    queryFn: () => fetchClinicalReport(intakeId),
    staleTime: 30_000,
  });

  const [pdfLoading, setPdfLoading] = useState(false);

  const handleExportPdf = async () => {
    if (!report) return;
    setPdfLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/api/report/${intakeId}/pdf`);
      if (!res.ok) throw new Error(`PDF download failed: ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      // Extract filename from Content-Disposition or use fallback
      const cd = res.headers.get("content-disposition");
      const match = cd?.match(/filename="?(.+?)"?$/);
      a.download = match?.[1] ?? `pratham_report_${report.patient_summary.name.replace(/\s+/g, "_")}_${new Date().toISOString().slice(0, 10)}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("PDF export failed:", err);
    } finally {
      setPdfLoading(false);
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

        {/* Pipeline status during loading */}
        {pipelineData && (
          <div className="mt-4 rounded-lg border-2 border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800/60 p-4 shadow-sm">
            <div className="mb-3 flex items-center gap-2">
              <span className="text-[11px] font-bold uppercase tracking-[0.15em] text-slate-800 dark:text-gray-200">
                AI Pipeline Status
              </span>
              {isPolling && (
                <span className="flex items-center gap-1 text-[10px] text-sky-600 font-semibold">
                  <Loader2 className="h-3 w-3 animate-spin" /> Live
                </span>
              )}
            </div>
            <PipelineStatus stages={pipelineData.stages} />
          </div>
        )}

        {/* Progressive skeleton */}
        <div className="mt-6 space-y-6">
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
            <Button size="sm" variant="outline" onClick={handleExportPdf} disabled={pdfLoading}>
              {pdfLoading ? (
                <><Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />Generating…</>
              ) : (
                <><Download className="mr-1.5 h-3.5 w-3.5" />Export PDF</>
              )}
            </Button>
          </div>
        }
      />

      <div className="mt-6">
        <ClinicalReport
          report={report}
          reportRef={reportRef}
          pipelineStages={pipelineData?.stages}
          isPolling={isPolling}
        />
      </div>
    </div>
  );
}
