/**
 * Patient Registry — Nurse station
 *
 * Permanent historical archive of all emergency patient intakes.
 * Allows searching, filtering, and sorting across all closed and active records.
 */

import { useState, useMemo } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import {
  Search,
  Filter,
  ArrowUpDown,
  FileText,
  AlertCircle,
  FolderOpen,
  Calendar,
  Building,
  Truck,
  UserCheck,
  CheckCircle,
  HelpCircle,
  Loader2,
  RefreshCw,
  Archive,
} from "lucide-react";
import { SectionHeader } from "@/components/section-header";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { fetchRegistry, type RegistryItem } from "@/lib/patient-queue-api";
import { WorkflowStatus, WORKFLOW_LABELS } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_app/nurse/registry")({
  head: () => ({
    meta: [
      { title: "Patient Registry — PRATHAM" },
      { name: "description", content: "Historical permanent registry database of all emergency intakes." },
    ],
  }),
  component: PatientRegistry,
});

// Reuse status configs for rendering colored badges
const STATUS_BADGES: Record<
  WorkflowStatus,
  { label: string; bg: string; text: string; border: string }
> = {
  [WorkflowStatus.INTAKE_SUBMITTED]: {
    label: "Intake Submitted",
    bg: "bg-blue-50 dark:bg-blue-950/20",
    text: "text-blue-700 dark:text-blue-400",
    border: "border-blue-200 dark:border-blue-800",
  },
  [WorkflowStatus.EN_ROUTE]: {
    label: "En Route",
    bg: "bg-blue-50 dark:bg-blue-950/20",
    text: "text-blue-700 dark:text-blue-400",
    border: "border-blue-200 dark:border-blue-800",
  },
  [WorkflowStatus.ARRIVED]: {
    label: "Arrived",
    bg: "bg-amber-50 dark:bg-amber-950/20",
    text: "text-amber-700 dark:text-amber-400",
    border: "border-amber-200 dark:border-amber-800",
  },
  [WorkflowStatus.AWAITING_APPROVAL]: {
    label: "Awaiting Doctor Approval",
    bg: "bg-amber-50 dark:bg-amber-950/20",
    text: "text-amber-700 dark:text-amber-400",
    border: "border-amber-200 dark:border-amber-800",
  },
  [WorkflowStatus.APPROVED]: {
    label: "Investigations Approved",
    bg: "bg-orange-50 dark:bg-orange-950/20",
    text: "text-orange-700 dark:text-orange-400",
    border: "border-orange-200 dark:border-orange-850",
  },
  [WorkflowStatus.UPLOAD_PENDING]: {
    label: "Upload Pending",
    bg: "bg-orange-50 dark:bg-orange-950/20",
    text: "text-orange-700 dark:text-orange-400",
    border: "border-orange-200 dark:border-orange-850",
  },
  [WorkflowStatus.ANALYSIS_RUNNING]: {
    label: "Analysis Running",
    bg: "bg-orange-50 dark:bg-orange-950/20",
    text: "text-orange-700 dark:text-orange-400",
    border: "border-orange-200 dark:border-orange-850",
  },
  [WorkflowStatus.REPORT_READY]: {
    label: "Clinical Report Ready",
    bg: "bg-emerald-50 dark:bg-emerald-950/20",
    text: "text-emerald-700 dark:text-emerald-400",
    border: "border-emerald-200 dark:border-emerald-800",
  },
  [WorkflowStatus.UNDER_REVIEW]: {
    label: "Under Doctor Review",
    bg: "bg-emerald-50 dark:bg-emerald-950/20",
    text: "text-emerald-700 dark:text-emerald-400",
    border: "border-emerald-200 dark:border-emerald-800",
  },
  [WorkflowStatus.CLOSED]: {
    label: "Case Closed",
    bg: "bg-slate-100 dark:bg-slate-900/60",
    text: "text-slate-600 dark:text-slate-400",
    border: "border-slate-200 dark:border-slate-800",
  },
  [WorkflowStatus.OFFLINE]: {
    label: "Offline Care",
    bg: "bg-slate-100 dark:bg-slate-900/60",
    text: "text-slate-600 dark:text-slate-400",
    border: "border-slate-200 dark:border-slate-800",
  },
};

function PatientRegistry() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [arrivalFilter, setArrivalFilter] = useState<string>("all");
  const [sortField, setSortField] = useState<"created_at" | "patient_name">("created_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  const { data: registry, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ["patient-registry"],
    queryFn: fetchRegistry,
    staleTime: 30_000,
  });

  // Handle Search, Filters, and Sorting
  const processedData = useMemo(() => {
    if (!registry) return [];

    let result = [...registry];

    // 1. Search filter
    const q = search.toLowerCase().trim();
    if (q) {
      result = result.filter(
        (item) =>
          item.patient_name.toLowerCase().includes(q) ||
          item.case_id.toLowerCase().includes(q)
      );
    }

    // 2. Status filter
    if (statusFilter !== "all") {
      result = result.filter((item) => item.status === statusFilter);
    }

    // 3. Arrival filter
    if (arrivalFilter !== "all") {
      result = result.filter((item) => item.arrival_type === arrivalFilter);
    }

    // 4. Sort fields
    result.sort((a, b) => {
      let comparison = 0;
      if (sortField === "created_at") {
        comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      } else if (sortField === "patient_name") {
        comparison = a.patient_name.localeCompare(b.patient_name);
      }

      return sortOrder === "desc" ? -comparison : comparison;
    });

    return result;
  }, [registry, search, statusFilter, arrivalFilter, sortField, sortOrder]);

  const toggleSort = (field: "created_at" | "patient_name") => {
    if (sortField === field) {
      setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortOrder("desc");
    }
  };

  const formatDateString = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString([], {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return "—";
    }
  };

  const getArrivalIcon = (type: string) => {
    if (type === "ambulance") return <Truck className="h-3.5 w-3.5 mr-1.5" />;
    if (type === "referral") return <Building className="h-3.5 w-3.5 mr-1.5" />;
    return <UserCheck className="h-3.5 w-3.5 mr-1.5" />;
  };

  return (
    <div className="mx-auto max-w-6xl px-5 py-8 md:px-8">
      <SectionHeader
        eyebrow="Database Desk"
        title="Patient Registry"
        description="Permanent clinical archive of all intakes, statuses, case timelines, and archived diagnostic records."
        actions={
          <Button
            size="sm"
            variant="outline"
            onClick={() => refetch()}
            disabled={isFetching}
          >
            <RefreshCw className={cn("mr-1.5 h-3.5 w-3.5", isFetching && "animate-spin")} />
            Sync Database
          </Button>
        }
      />

      {/* Modern Filter controls */}
      <div className="mt-6 gap-4 grid sm:grid-cols-2 md:grid-cols-[2fr_1.2fr_1.2fr] bg-slate-50 dark:bg-slate-900/50 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search by Case ID, patient name…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-xl border bg-white dark:bg-slate-900 py-2.5 pl-10 pr-4 text-xs outline-none focus:border-teal-500/60"
          />
        </div>

        {/* Status Filter */}
        <div className="relative">
          <Filter className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full rounded-xl border bg-white dark:bg-slate-900 py-2.5 pl-9 pr-4 text-xs outline-none appearance-none"
          >
            <option value="all">All Statuses</option>
            {Object.entries(WORKFLOW_LABELS).map(([val, label]) => (
              <option key={val} value={val}>
                {label}
              </option>
            ))}
          </select>
        </div>

        {/* Arrival Filter */}
        <div className="relative">
          <Filter className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
          <select
            value={arrivalFilter}
            onChange={(e) => setArrivalFilter(e.target.value)}
            className="w-full rounded-xl border bg-white dark:bg-slate-900 py-2.5 pl-9 pr-4 text-xs outline-none appearance-none"
          >
            <option value="all">All Arrivals</option>
            <option value="walk_in">Walk-in</option>
            <option value="ambulance">Ambulance</option>
            <option value="referral">Referral</option>
          </select>
        </div>
      </div>

      {/* Registry Table List */}
      <div className="mt-6 overflow-hidden rounded-2xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/80 text-slate-400 font-bold uppercase tracking-wider">
                <th className="px-6 py-4">Case ID</th>
                <th className="px-6 py-4 cursor-pointer hover:bg-slate-100/50 dark:hover:bg-slate-800/40" onClick={() => toggleSort("patient_name")}>
                  <div className="flex items-center gap-1">
                    Patient Name
                    <ArrowUpDown className="h-3 w-3" />
                  </div>
                </th>
                <th className="px-6 py-4 cursor-pointer hover:bg-slate-100/50 dark:hover:bg-slate-800/40" onClick={() => toggleSort("created_at")}>
                  <div className="flex items-center gap-1">
                    Registered On
                    <ArrowUpDown className="h-3 w-3" />
                  </div>
                </th>
                <th className="px-6 py-4">Arrival Type</th>
                <th className="px-6 py-4">Current Status</th>
                <th className="px-6 py-4">Closed By</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800 font-medium">
              {isLoading && (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-slate-400">
                    <div className="flex items-center justify-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin text-teal-600" />
                      Loading registry archive…
                    </div>
                  </td>
                </tr>
              )}

              {isError && (
                <tr>
                  <td colSpan={7} className="px-6 py-10">
                    <div className="flex items-center justify-center gap-2 text-rose-500 font-semibold">
                      <AlertCircle className="h-4 w-4" />
                      Failed to fetch patient registry.
                    </div>
                  </td>
                </tr>
              )}

              {!isLoading && !isError && processedData.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-slate-400 dark:text-slate-500">
                    <Archive className="mx-auto h-8 w-8 text-slate-300 dark:text-slate-700 mb-2" />
                    No historical patient cases found.
                  </td>
                </tr>
              )}

              {!isLoading &&
                !isError &&
                processedData.map((item) => {
                  const statusConf = STATUS_BADGES[item.status] || {
                    label: item.status,
                    bg: "bg-slate-100",
                    text: "text-slate-700",
                    border: "border-slate-200",
                  };

                  return (
                    <tr
                      key={item.intake_id}
                      className="hover:bg-slate-50/40 dark:hover:bg-slate-800/10 transition-colors"
                    >
                      <td className="px-6 py-4 font-mono font-bold text-slate-800 dark:text-slate-200">
                        {item.case_id}
                      </td>
                      <td className="px-6 py-4 font-bold text-slate-900 dark:text-slate-100">
                        {item.patient_name}
                      </td>
                      <td className="px-6 py-4 text-slate-500">
                        {formatDateString(item.created_at)}
                      </td>
                      <td className="px-6 py-4 text-slate-700 dark:text-slate-300">
                        <div className="flex items-center">
                          {getArrivalIcon(item.arrival_type)}
                          <span className="capitalize">{item.arrival_type.replace("_", " ")}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={cn(
                            "inline-flex items-center rounded-full border px-2 py-0.5 text-[9px] font-extrabold uppercase tracking-wider",
                            statusConf.bg,
                            statusConf.border,
                            statusConf.text
                          )}
                        >
                          {statusConf.label}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-slate-500 italic">
                        {item.closed_by || "—"}
                      </td>
                      <td className="px-6 py-4 text-right">
                        {item.report_available ? (
                          <Button asChild size="xs" variant="outline" className="h-7 border-teal-500/20 text-teal-600 hover:text-teal-500 hover:bg-teal-50/50">
                            <Link to="/doctor/report/$intakeId" params={{ intakeId: item.intake_id }}>
                              <FileText className="mr-1 h-3 w-3" />
                              View Report
                            </Link>
                          </Button>
                        ) : (
                          <span className="text-[10px] font-semibold text-slate-400 uppercase">
                            Processing
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
