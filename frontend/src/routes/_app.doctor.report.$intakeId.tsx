/**
 * Doctor Clinical Intelligence Report Page
 *
 * Route: /doctor/report/:intakeId
 *
 * Fetches and displays the read-only Clinical Intelligence Report.
 * Layout:
 *   - Left: Unified 17-section ClinicalReport view (strictly read-only).
 *   - Right: Patient Snapshot cover sheet, Journey Card, and Case History timeline logs.
 */

import { useRef, useState, useEffect } from "react";
import { createFileRoute, Link, useRouter } from "@tanstack/react-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Activity,
  Download,
  Loader2,
  AlertCircle,
  FileText,
  CheckCircle,
  ShieldCheck,
  Calendar,
  Clock,
  ArrowLeft,
} from "lucide-react";
import { SectionHeader } from "@/components/section-header";
import { ClinicalReport } from "@/components/clinical-report";
import { PatientJourneyCard } from "@/components/patient-journey-card";
import { PatientTimeline } from "@/components/patient-timeline";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { fetchWorkflowLogs, closeCase } from "@/lib/patient-queue-api";
import { fetchClinicalReport, markReportReviewed } from "@/lib/report-api";
import { WorkflowStatus } from "@/lib/mock-data";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/api-config";

export const Route = createFileRoute("/_app/doctor/report/$intakeId")({
  head: () => ({
    meta: [
      { title: "Clinical Report Workspace — PRATHAM" },
      { name: "description", content: "AI-powered diagnostics clinical workstation report page." },
    ],
  }),
  component: ReportPage,
});

function ReportPage() {
  const { intakeId } = Route.useParams();
  const reportRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const queryClient = useQueryClient();

  // ── Query complete report with polling for live locks (Task 8) ────────────
  const { data: report, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["clinical-report", intakeId],
    queryFn: () => fetchClinicalReport(intakeId),
    refetchInterval: (query) => {
      const data = query.state.data;
      const status = data?.patient_summary?.status;
      if (status === "case_closed" || status === "offline_care") {
        return false;
      }
      return 5_000;
    },
    staleTime: 2_500,
  });

  // ── Explicit status transition on mount ──────────────────────────────────
  useEffect(() => {
    if (intakeId) {
      markReportReviewed(intakeId, "Dr. Clinician")
        .then(() => {
          // Invalidate queries to refresh lists and dashboard
          queryClient.invalidateQueries({ queryKey: ["doctor-dashboard-stats"] });
          queryClient.invalidateQueries({ queryKey: ["doctor-reports-list"] });
          queryClient.invalidateQueries({ queryKey: ["patient-queue"] });
        })
        .catch((err) => console.warn("Failed to mark report reviewed:", err));
    }
  }, [intakeId, queryClient]);

  // ── Mismatch live warning logic (Additions 4: Report Lock) ──────────────
  const [initialEvidenceCount, setInitialEvidenceCount] = useState<number | null>(null);
  const [showRefreshWarning, setShowRefreshWarning] = useState(false);

  useEffect(() => {
    if (report && initialEvidenceCount === null) {
      setInitialEvidenceCount(report.evidence_list?.length || 0);
    }
  }, [report, initialEvidenceCount]);

  useEffect(() => {
    if (report && initialEvidenceCount !== null) {
      const currentCount = report.evidence_list?.length || 0;
      if (currentCount > initialEvidenceCount) {
        setShowRefreshWarning(true);
      }
    }
  }, [report, initialEvidenceCount]);

  const handleRefreshReview = () => {
    if (report) {
      setInitialEvidenceCount(report.evidence_list?.length || 0);
      setShowRefreshWarning(false);
      refetch();
    }
  };

  // ── Close Case states ──────────────────────────────────────────────────────
  const [closeModalOpen, setCloseModalOpen] = useState(false);
  const [reviewSummary, setReviewSummary] = useState("");
  const [closeLoading, setCloseLoading] = useState(false);

  const handleCloseCaseSubmit = async () => {
    if (!reviewSummary.trim()) return;
    setCloseLoading(true);
    try {
      await closeCase(intakeId, "Dr. Clinician", reviewSummary.trim());
      setCloseModalOpen(false);
      // Invalidate queries to refresh lists and dashboard
      queryClient.invalidateQueries({ queryKey: ["doctor-dashboard-stats"] });
      queryClient.invalidateQueries({ queryKey: ["doctor-reports-list"] });
      queryClient.invalidateQueries({ queryKey: ["patient-registry"] });
      // Redirect back to Clinical Reports List page
      router.navigate({ to: "/doctor/reports" });
    } catch (err) {
      console.error("Failed to close case:", err);
    } finally {
      setCloseLoading(false);
    }
  };

  // ── PDF export loader ──────────────────────────────────────────────────────
  const [pdfLoading, setPdfLoading] = useState(false);
  const handleExportPdf = async () => {
    if (!report) return;
    setPdfLoading(true);
    try {
      const res = await fetch(`${API_BASE}/report/${intakeId}/pdf`);
      if (!res.ok) throw new Error(`PDF download failed: ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `pratham_report_${report.patient_summary?.name?.replace(/\s+/g, "_") || "patient"}.pdf`;
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
      <div className="mx-auto max-w-7xl px-5 py-12 md:px-8 text-center text-slate-400">
        <Loader2 className="h-8 w-8 animate-spin text-teal-600 mx-auto mb-4" />
        Loading clinical report workspace…
      </div>
    );
  }

  if (isError || !report) {
    return (
      <div className="mx-auto max-w-7xl px-5 py-8 md:px-8">
        <div className="flex items-center gap-3 rounded-xl border border-rose-500/20 bg-rose-500/5 p-6 text-sm text-rose-500">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <div>
            <p className="font-semibold">Failed to load clinical report</p>
            <p className="mt-1 text-xs text-muted-foreground">{error?.message}</p>
          </div>
        </div>
      </div>
    );
  }

  const patient = report.patient_summary || {};
  const status = report.status || "clinical_report_ready";
  const isClosed = status === WorkflowStatus.CLOSED || status === WorkflowStatus.OFFLINE;

  // Derive version number and count of completed analysis stages (Cover sheet)
  const reportVersion = report.evidence_list?.length || 1;
  const completedStagesCount = Object.values(report.pipeline_status || {}).filter(
    (s) => s === "completed"
  ).length;

  // Safety warning calculation for case closure (Additions 5: Pending Check)
  const hasPendingInvs = report.clinician_report?.investigations_matrix?.some((t: any) => t.status === "Pending") ?? false;

  return (
    <div className="mx-auto max-w-7xl px-5 py-8 md:px-8 space-y-6">
      {/* Return to Worklist button */}
      <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
        <Button asChild size="sm" variant="ghost" className="text-slate-500 hover:text-slate-900">
          <Link to="/doctor/reports" className="flex items-center gap-1.5 font-bold">
            <ArrowLeft className="h-4 w-4" />
            Back to Reports List
          </Link>
        </Button>
      </div>

      <SectionHeader
        eyebrow="Doctor workstation"
        title="Clinical Intelligence Report"
        description={`Comprehensive diagnostic summary analysis for patient intake ${intakeId.slice(0, 8)}…`}
        actions={
          <div className="flex items-center gap-2">
            <Button size="sm" variant="outline" onClick={handleExportPdf} disabled={pdfLoading}>
              {pdfLoading ? (
                <><Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />Generating…</>
              ) : (
                <><Download className="mr-1.5 h-3.5 w-3.5" />Export PDF</>
              )}
            </Button>
            
            {/* Close Case Trigger (Task 7) */}
            {!isClosed ? (
              <Button size="sm" onClick={() => setCloseModalOpen(true)} className="bg-teal-600 hover:bg-teal-500 text-white font-bold">
                ✓ Close Case
              </Button>
            ) : (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 dark:bg-slate-800 border px-3 py-1 text-xs font-bold text-slate-500">
                <ShieldCheck className="h-4 w-4 text-emerald-500" />
                Case Closed
              </span>
            )}
          </div>
        }
      />

      {/* Mismatch Warning Alert (Additions 4: Report Lock Warning) */}
      {showRefreshWarning && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-700 dark:text-amber-400 flex items-center justify-between shadow-sm animate-in fade-in duration-300">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4.5 w-4.5 animate-bounce" />
            <span className="text-xs font-bold">
              ⚠ New evidence received. Report updated to Version {reportVersion} in background.
            </span>
          </div>
          <Button size="xs" onClick={handleRefreshReview} className="bg-amber-600 hover:bg-amber-500 text-white font-bold">
            Refresh Review
          </Button>
        </div>
      )}

      {/* Two-Column split workspace layout (Task 6) */}
      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        {/* Left Column: Strictly read-only clinical report view */}
        <div className="space-y-4">
          <Card className="shadow-sm border border-slate-200/80 dark:border-slate-800">
            <CardHeader className="pb-3 border-b border-slate-100 dark:border-slate-800 bg-slate-50/30">
              <CardTitle className="text-sm font-bold text-slate-800 dark:text-slate-200">
                Consolidated Findings Sheet
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <ClinicalReport
                report={report}
                reportRef={reportRef}
                pipelineStages={report.pipeline_status}
                isPolling={false} // Ensure strictly read-only, no active poll controls inside report
              />
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Patient Snapshot cover sheet, Journey Card, Timeline history logs */}
        <div className="space-y-6 lg:sticky lg:top-6 lg:self-start">
          {/* Cover Sheet: Patient Snapshot */}
          <Card className="shadow-sm border border-slate-200/80 dark:border-slate-800">
            <CardHeader className="pb-3 border-b border-slate-100 dark:border-slate-800 bg-slate-50/30">
              <CardTitle className="text-sm font-bold text-slate-800 dark:text-slate-200">
                Patient Snapshot Cover Sheet
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-5 space-y-4 text-xs font-medium">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-50/50 dark:bg-slate-900/50 p-3 rounded-xl border">
                  <span className="text-[10px] text-slate-400 block font-bold uppercase mb-0.5">Case ID</span>
                  <span className="font-mono font-bold text-slate-800 dark:text-slate-200">{patient.case_id || report.case_id || "Case"}</span>
                </div>
                <div className="bg-slate-50/50 dark:bg-slate-900/50 p-3 rounded-xl border">
                  <span className="text-[10px] text-slate-400 block font-bold uppercase mb-0.5">Report Version</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">Version {reportVersion}</span>
                </div>
                <div className="bg-slate-50/50 dark:bg-slate-900/50 p-3 rounded-xl border">
                  <span className="text-[10px] text-slate-400 block font-bold uppercase mb-0.5">Demographics</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">{patient.name}, {patient.age}{patient.gender?.slice(0,1)?.toUpperCase()}</span>
                </div>
                <div className="bg-slate-50/50 dark:bg-slate-900/50 p-3 rounded-xl border">
                  <span className="text-[10px] text-slate-400 block font-bold uppercase mb-0.5">Arrival mode</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200 capitalize">{report.arrival_type || "walk_in"}</span>
                </div>
                <div className="bg-slate-50/50 dark:bg-slate-900/50 p-3 rounded-xl border">
                  <span className="text-[10px] text-slate-400 block font-bold uppercase mb-0.5">Clinical Priority</span>
                  <span className="font-bold text-rose-600 uppercase">{report.severity}</span>
                </div>
                <div className="bg-slate-50/50 dark:bg-slate-900/50 p-3 rounded-xl border">
                  <span className="text-[10px] text-slate-400 block font-bold uppercase mb-0.5">Analyses Completed</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">{completedStagesCount} / 5 Stages</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Journey card tracker */}
          <PatientJourneyCard
            caseId={patient.case_id || report.case_id || "Case"}
            status={status}
            arrivalType={report.arrival_type || "walk_in"}
            createdAt={report.created_at}
          />

          {/* Timeline and case log histories */}
          <PatientTimeline intakeId={intakeId} />
        </div>
      </div>

      {/* Close Case Dialog Overlay */}
      {closeModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 max-w-md w-full shadow-2xl animate-in zoom-in-95 duration-200">
            <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <CheckCircle className="h-4.5 w-4.5 text-teal-600" />
              Close Patient Emergency Case
            </h3>
            
            {/* Warning if pending investigations (Additions 5) */}
            {hasPendingInvs && (
              <div className="mt-3 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-700 dark:text-amber-400 text-xs font-semibold flex items-start gap-2">
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <span>⚠ Pending investigations detected. Some recommendations have no uploaded evidence files. Close anyway?</span>
              </div>
            )}

            {/* Required Clinical Review Summary text area (Additions 3) */}
            <div className="mt-4">
              <label className="text-[10px] font-bold text-slate-400 uppercase block mb-1">
                Clinical Review Summary *
              </label>
              <textarea
                placeholder="Enter patient review findings summary details before closing case file (required)…"
                value={reviewSummary}
                onChange={(e) => setReviewSummary(e.target.value)}
                className="w-full rounded-xl border bg-slate-50 dark:bg-slate-900 p-3 text-xs outline-none focus:border-teal-500/60 min-h-[90px] resize-none"
                required
              />
            </div>

            <div className="mt-6 flex justify-end gap-2">
              <Button size="sm" variant="outline" onClick={() => setCloseModalOpen(false)} disabled={closeLoading}>
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={handleCloseCaseSubmit}
                disabled={closeLoading || !reviewSummary.trim()}
                className="bg-teal-600 hover:bg-teal-500 text-white font-bold"
              >
                {closeLoading ? <Loader2 className="h-4.5 w-4.5 animate-spin mr-1" /> : null}
                Confirm Close Case
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
