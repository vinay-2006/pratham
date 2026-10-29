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
import { apiErrorMessage } from "@/lib/api-error";
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
      const status = data?.status;
      // Stop polling once the case is terminal or actively being reviewed
      if (status === "case_closed" || status === "offline_care" || status === "under_doctor_review") {
        return false;
      }
      return 30_000;
    },
    staleTime: 15_000,
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
      setInitialEvidenceCount(report.evidence?.length || 0);
    }
  }, [report, initialEvidenceCount]);

  useEffect(() => {