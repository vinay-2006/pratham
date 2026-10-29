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
import { fetchDoctorReportsList, type DoctorReportItem, type PipelineStatusMap } from "@/lib/patient-queue-api";
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