/**
 * Clinical Worklist — Doctor Station
 *
 * Operational queue for doctors to review active emergency patient files.
 * Ordered by clinical priority (Critical → Routine) and registration time.
 */

import { useState, useMemo } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import {
  Users,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  AlertCircle,
  Stethoscope,
  ChevronDown,
  ChevronUp,
  Loader2,
  ArrowRight,
  ShieldAlert,
  Send,
  Plus,
  RefreshCw,
  Info,
  Layers,
  Sparkles,
  Calendar,
  XCircle,
} from "lucide-react";
import { SectionHeader } from "@/components/section-header";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PatientJourneyCard } from "@/components/patient-journey-card";
import { PatientTimeline } from "@/components/patient-timeline";
import {
  fetchDoctorReviewPatients,
  approveInvestigations,
  rejectInvestigations,
  returnToNurse,
  recommendInvestigation,
  type DoctorReviewPatient,
} from "@/lib/patient-queue-api";
import { WorkflowStatus, WORKFLOW_LABELS } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_app/doctor/review")({
  head: () => ({
    meta: [
      { title: "Clinical Worklist — PRATHAM" },
      { name: "description", content: "Doctor workstation for patient approvals, reviews, and clinical triage." },
    ],
  }),
  component: ClinicalWorklistPage,
});

const PRIORITY_RANK: Record<string, number> = {
  critical: 4,
  high: 3,
  moderate: 2,
  low: 1,
  routine: 1,
};

const SEVERITY_BADGES: Record<string, string> = {
  critical: "bg-rose-100 dark:bg-rose-950/60 text-rose-800 dark:text-rose-300 border-rose-250",
  high: "bg-orange-100 dark:bg-orange-950/60 text-orange-800 dark:text-orange-300 border-orange-250",
  moderate: "bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 border-amber-250",
  low: "bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border-emerald-250",
};

// ── Main Page Component ─────────────────────────────────────────────────────

function ClinicalWorklistPage() {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [arrivalFilter, setArrivalFilter] = useState("all");

  // Selection states for bulk actions
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [bulkConfirmOpen, setBulkConfirmOpen] = useState(false);
  const [bulkLoading, setBulkLoading] = useState(false);

  const { data: queue, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ["doctor-review-patients"],
    queryFn: fetchDoctorReviewPatients,
    refetchInterval: 10_000, // Refresh every 10s to keep counters sync'd
    staleTime: 5_000,
  });

  // Filter and Sort: Clinical Priority (Critical -> High -> Moderate -> Routine)
  const processedData = useMemo(() => {
    if (!queue) return [];

    let result = [...queue];

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

    // 2. Filters
    if (priorityFilter !== "all") {
      result = result.filter((p) => p.severity === priorityFilter);
    }
    if (statusFilter !== "all") {
      result = result.filter((p) => p.workflow_status === statusFilter);
    }
    if (arrivalFilter !== "all") {
      result = result.filter((p) => p.arrival_type === arrivalFilter);
    }

    // 3. Clinical Priority Sorting Hierarchy
    result.sort((a, b) => {
      const rankA = PRIORITY_RANK[a.severity] ?? 1;
      const rankB = PRIORITY_RANK[b.severity] ?? 1;
      if (rankB !== rankA) {
        return rankB - rankA; // Higher rank first (Critical -> High -> Moderate -> Routine)
      }
      // If same priority, sort by newest registered
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    });

    return result;
  }, [queue, search, priorityFilter, statusFilter, arrivalFilter]);

  const toggleSelectRow = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === processedData.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(processedData.map((p) => p.intake_id)));
    }
  };

  // Perform Bulk Approvals
  const handleBulkApprove = async () => {
    setBulkLoading(true);
    try {
      const promises = Array.from(selectedIds).map(async (id) => {
        const patient = queue?.find((p) => p.intake_id === id);
        if (!patient) return;
        const pendingTests = patient.investigations
          .filter((inv) => inv.status === "pending_approval")
          .map((inv) => inv.investigation_type);
        if (pendingTests.length > 0) {
          await approveInvestigations(
            id,
            pendingTests,
            [],
            "Dr. Clinician (Bulk)",
            "Bulk approved via Worklist Panel."
          );
        }
      });
      await Promise.all(promises);
      setSelectedIds(new Set());
      setBulkConfirmOpen(false);
      refetch();
    } catch (err) {
      console.error("Bulk approval error:", err);
    } finally {
      setBulkLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-5xl px-5 py-8 md:px-8">
      <SectionHeader
        eyebrow="Doctor Station"
        title="Clinical Worklist"
        description="ED diagnostic Worklist. Approve recommendations, request additional tests, or return to nurse."
        actions={
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => refetch()}
              disabled={isFetching}
            >
              <RefreshCw className={cn("mr-1.5 h-3.5 w-3.5", isFetching && "animate-spin")} />
              Sync Worklist
            </Button>
          </div>
        }
      />

      {/* Floating Bulk Actions Bar (Task 4 Option) */}
      {selectedIds.size > 0 && (
        <div className="mt-4 p-4 rounded-xl bg-teal-500/10 border border-teal-500/20 text-teal-700 dark:text-teal-400 flex items-center justify-between shadow-sm animate-in fade-in slide-in-from-top-2">
          <span className="text-xs font-bold">
            Selected {selectedIds.size} patient case{selectedIds.size !== 1 ? "s" : ""}
          </span>
          <div className="flex gap-2">
            <Button size="xs" variant="outline" onClick={() => setSelectedIds(new Set())} className="border-teal-500/30 text-teal-700">
              Clear
            </Button>
            <Button size="xs" onClick={() => setBulkConfirmOpen(true)} className="bg-teal-600 hover:bg-teal-500 text-white font-bold">
              Bulk Approve
            </Button>
          </div>
        </div>
      )}

      {/* Search & Operational Filters (Task 10) */}
      <div className="mt-6 gap-4 grid sm:grid-cols-2 md:grid-cols-[1.5fr_1fr_1fr_1fr] bg-slate-50 dark:bg-slate-900/50 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search Case ID, patient name…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-xl border bg-white dark:bg-slate-900 py-2.5 pl-10 pr-4 text-xs outline-none focus:border-teal-500/60"
          />
        </div>

        <select
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value)}
          className="w-full rounded-xl border bg-white dark:bg-slate-900 py-2.5 px-3 text-xs outline-none appearance-none"
        >
          <option value="all">All Priorities</option>
          <option value="critical">Critical Only</option>
          <option value="high">High Priority</option>
          <option value="moderate">Moderate</option>
          <option value="low">Routine</option>
        </select>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="w-full rounded-xl border bg-white dark:bg-slate-900 py-2.5 px-3 text-xs outline-none appearance-none"
        >
          <option value="all">All Work stages</option>
          <option value="awaiting_doctor_approval">Awaiting Approval</option>
          <option value="investigations_approved">Investigations Approved</option>
          <option value="evidence_upload_pending">Upload Pending</option>
          <option value="analysis_running">Analysis Running</option>
        </select>

        <select
          value={arrivalFilter}
          onChange={(e) => setArrivalFilter(e.target.value)}
          className="w-full rounded-xl border bg-white dark:bg-slate-900 py-2.5 px-3 text-xs outline-none appearance-none"
        >
          <option value="all">All Arrival Types</option>
          <option value="walk_in">Walk-in</option>
          <option value="ambulance">Ambulance</option>
          <option value="referral">Referral</option>
        </select>
      </div>

      {/* Patient Listing */}
      <div className="mt-4 space-y-3">
        {isLoading && (
          <div className="space-y-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="rounded-xl border p-5 bg-slate-50/20 dark:bg-slate-900/20 animate-pulse h-[80px]" />
            ))}
          </div>
        )}

        {isError && (
          <Card className="border-rose-500/20 bg-rose-500/5">
            <CardContent className="flex items-center gap-3 p-6 text-sm text-rose-500">
              <AlertCircle className="h-5 w-5 shrink-0" />
              <div>
                <p className="font-semibold">Failed to fetch Clinical Worklist</p>
                <p className="text-xs mt-0.5 text-muted-foreground">{error?.message}</p>
              </div>
            </CardContent>
          </Card>
        )}

        {!isLoading && !isError && processedData.length === 0 && (
          <Card>
            <CardContent className="p-12 text-center text-slate-400">
              <Users className="mx-auto h-8 w-8 text-slate-300 dark:text-slate-700 mb-2" />
              No active cases matching your filters.
            </CardContent>
          </Card>
        )}

        {!isLoading && !isError && processedData.length > 0 && (
          <div className="flex items-center gap-2 px-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            <input
              type="checkbox"
              checked={selectedIds.size === processedData.length}
              onChange={toggleSelectAll}
              className="rounded border-slate-300 text-teal-600 focus:ring-teal-500 shrink-0 h-3.5 w-3.5 cursor-pointer"
            />
            <span>Select All for bulk approval</span>
          </div>
        )}

        {!isLoading &&
          !isError &&
          processedData.map((item) => (
            <WorklistRow
              key={item.intake_id}
              item={item}
              expanded={expandedId === item.intake_id}
              onToggle={() => setExpandedId((prev) => (prev === item.intake_id ? null : item.intake_id))}
              isSelected={selectedIds.has(item.intake_id)}
              onSelect={(e) => toggleSelectRow(item.intake_id, e)}
              refetchQueue={refetch}
            />
          ))}
      </div>

      {/* Bulk Approval Modal */}
      {bulkConfirmOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 max-w-md w-full shadow-2xl animate-in zoom-in-95 duration-200">
            <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <CheckCircle2 className="h-4.5 w-4.5 text-teal-600" />
              Approve Multiple Cases
            </h3>
            <p className="mt-3 text-xs leading-relaxed text-slate-500">
              Are you sure you want to approve all recommended investigations for the{" "}
              <strong className="text-slate-800 dark:text-slate-200">{selectedIds.size}</strong> selected cases?
            </p>
            <div className="mt-6 flex justify-end gap-2">
              <Button size="sm" variant="outline" onClick={() => setBulkConfirmOpen(false)} disabled={bulkLoading}>
                Cancel
              </Button>
              <Button size="sm" onClick={handleBulkApprove} disabled={bulkLoading} className="bg-teal-600 hover:bg-teal-500 text-white">
                {bulkLoading ? <Loader2 className="h-4.5 w-4.5 animate-spin mr-1" /> : null}
                Approve {selectedIds.size} Cases
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Worklist Item Row ────────────────────────────────────────────────────────

/** Convert an ISO timestamp into a human-readable relative time string. */
function timeAgo(iso: string | undefined): string {
  if (!iso) return "—";
  const now = Date.now();
  const then = new Date(iso).getTime();
  if (isNaN(then)) return "—";
  const diff = Math.max(0, now - then);
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

function WorklistRow({
  item,
  expanded,
  onToggle,
  isSelected,
  onSelect,
  refetchQueue,
}: {
  item: DoctorReviewPatient;
  expanded: boolean;
  onToggle: () => void;
  isSelected: boolean;
  onSelect: (e: React.MouseEvent) => void;
  refetchQueue: () => void;
}) {
  const sevBadge = SEVERITY_BADGES[item.severity] || "bg-slate-100";
  const registeredTime = timeAgo(item.created_at);

  // Return to Nurse template and notes variables
  const [returnOpen, setReturnOpen] = useState(false);
  const [returnTemplate, setReturnTemplate] = useState("Poor image quality");
  const [returnNotes, setReturnNotes] = useState("");
  const [returnLoading, setReturnLoading] = useState(false);

  // Custom recommended test variables
  const [newTest, setNewTest] = useState("");
  const [recommendLoading, setRecommendLoading] = useState(false);

  // Action notes during approvals
  const [actionNotes, setActionNotes] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  // Per-test selection for granular approval/rejection
  const [selectedTests, setSelectedTests] = useState<Set<string>>(() => {
    // Default: all pending tests are pre-selected
    return new Set(
      item.investigations
        .filter((inv) => inv.status === "pending_approval")
        .map((inv) => inv.investigation_type)
    );
  });

  const toggleTest = (testType: string) => {
    setSelectedTests((prev) => {
      const next = new Set(prev);
      if (next.has(testType)) next.delete(testType);
      else next.add(testType);
      return next;
    });
  };

  const selectAllPending = () => {
    setSelectedTests(new Set(
      item.investigations
        .filter((inv) => inv.status === "pending_approval")
        .map((inv) => inv.investigation_type)
    ));
  };

  const deselectAll = () => setSelectedTests(new Set());

  // Handle Approvals — only selected tests
  const handleApprove = async () => {
    const approveList = Array.from(selectedTests);
    if (approveList.length === 0) return;

    setActionLoading(true);
    try {
      await approveInvestigations(item.intake_id, approveList, [], "Dr. Clinician", actionNotes || "Approved selected investigations.");
      setActionNotes("");
      setSelectedTests(new Set());
      refetchQueue();
    } catch (err) {
      console.error(err);
    } finally {
      setActionLoading(false);
    }
  };

  // Handle Rejections
  const handleReject = async () => {
    setActionLoading(true);
    try {
      await rejectInvestigations(item.intake_id, "Dr. Clinician", actionNotes || "Rejected recommended investigations.");
      setActionNotes("");
      refetchQueue();
    } catch (err) {
      console.error(err);
    } finally {
      setActionLoading(false);
    }
  };

  // Handle Return to Nurse
  const handleReturnToNurseSubmit = async () => {
    setReturnLoading(true);
    try {
      const formattedReason = returnNotes.trim()
        ? `${returnTemplate} - ${returnNotes.trim()}`
        : returnTemplate;
      await returnToNurse(item.intake_id, "Dr. Clinician", formattedReason);
      setReturnOpen(false);
      refetchQueue();
    } catch (err) {
      console.error(err);
    } finally {
      setReturnLoading(false);
    }
  };

  // Handle Recommend Custom test
  const handleRecommendTest = async () => {
    if (!newTest.trim()) return;
    setRecommendLoading(true);
    try {
      await recommendInvestigation(item.intake_id, newTest.trim(), "Dr. Clinician");
      setNewTest("");
      refetchQueue();
    } catch (err) {
      console.error(err);
    } finally {
      setRecommendLoading(false);
    }
  };

  const hasPendingTests = item.investigations.some((inv) => inv.status === "pending_approval");

  return (
    <div
      className={cn(
        "rounded-2xl border bg-white dark:bg-slate-900 transition-all duration-300 shadow-sm overflow-hidden",
        expanded
          ? "border-teal-500 dark:border-teal-400 bg-slate-50/50 dark:bg-slate-900/90"
          : "border-slate-200 dark:border-slate-800 hover:border-slate-300"
      )}
    >
      {/* List Item Trigger */}
      <div
        onClick={onToggle}
        className="flex items-center gap-4 px-6 py-5 cursor-pointer hover:bg-slate-50/50 dark:hover:bg-slate-800/30 text-left text-xs"
      >
        <input
          type="checkbox"
          checked={isSelected}
          onChange={(e) => {}}
          onClick={onSelect}
          className="rounded border-slate-300 text-teal-600 focus:ring-teal-500 shrink-0 h-4 w-4 cursor-pointer"
        />

        <div className="flex-1 grid gap-2 md:grid-cols-[1.5fr_1fr_1.2fr_auto] md:items-center min-w-0">
          {/* Demographics & CC */}
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-slate-400 font-bold">{item.case_id}</span>
              <span className="font-bold text-slate-900 dark:text-slate-100 text-sm">
                {item.patient_name}
              </span>
              <span className="text-slate-500 font-semibold">{item.age}{item.sex}</span>
            </div>
            {item.chief_complaint && (
              <p className="mt-1 text-slate-500 truncate max-w-xs">{item.chief_complaint}</p>
            )}
          </div>

          {/* Arrival type & Status */}
          <div className="flex items-center gap-2 font-bold uppercase tracking-wider text-[10px] text-slate-500">
            <span className="rounded bg-slate-100 dark:bg-slate-800 px-2 py-0.5 capitalize">
              {item.arrival_type}
            </span>
          </div>

          {/* Workflow Stage */}
          <div>
            <span className="inline-flex items-center gap-1 rounded-full border border-teal-200 bg-teal-50 dark:bg-teal-950/20 px-2.5 py-0.5 text-[9px] font-extrabold uppercase tracking-wider text-teal-700 dark:text-teal-400">
              {item.status === WorkflowStatus.AWAITING_APPROVAL ? "Awaiting Approval" : WORKFLOW_LABELS[item.status] || item.status}
            </span>
            <div className="mt-1.5 flex items-center gap-2">
              <div className="h-1 w-20 bg-slate-100 dark:bg-slate-850 rounded-full overflow-hidden">
                <div className="h-full bg-teal-500 rounded-full" style={{ width: `${item.progress}%` }} />
              </div>
              <span className="text-[9px] font-bold text-slate-400">{item.progress}%</span>
            </div>
          </div>

          {/* Priority & registered relative time */}
          <div className="text-right flex md:flex-col items-center md:items-end justify-between md:justify-center gap-2">
            <span className={cn("rounded-full border px-2 py-0.5 text-[9px] font-extrabold uppercase tracking-wider", sevBadge)}>
              {item.severity}
            </span>
            <span className="text-[9px] font-bold font-mono text-slate-400">{registeredTime}</span>
          </div>
        </div>

        <div className="shrink-0">
          {expanded ? <ChevronUp className="h-4 w-4 text-slate-400" /> : <ChevronDown className="h-4 w-4 text-slate-400" />}
        </div>
      </div>

      {/* Expanded Workstation Dashboard */}
      {expanded && (
        <div className="border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6">
          {/* Sticky Context Panel (Task 4 Requirement / Context Panel) */}
          <div className="sticky top-0 z-10 -mx-6 -mt-6 mb-6 bg-slate-50 dark:bg-slate-850/85 backdrop-blur border-b border-slate-200 dark:border-slate-800 px-6 py-4 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <span className="font-mono text-xs font-bold text-slate-400">{item.case_id}</span>
              <span className="font-bold text-slate-900 dark:text-slate-100 text-sm">{item.patient_name}</span>
              <span className="text-xs text-slate-500 font-semibold">{item.age}{item.sex}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-extrabold uppercase bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded text-slate-600">
                Arrival: {item.arrival_type}
              </span>
              <span className={cn("rounded-full border px-2 py-0.5 text-[9px] font-extrabold uppercase tracking-wider", sevBadge)}>
                {item.severity}
              </span>
              <span className="text-[10px] font-bold uppercase bg-teal-500/10 text-teal-600 dark:text-teal-400 px-2 py-0.5 rounded">
                Stage: {WORKFLOW_LABELS[item.status] || item.status}
              </span>
            </div>
          </div>

          <div className="grid gap-6 lg:grid-cols-[1.3fr_1fr]">
            {/* Left side: Doctor Decisions & Action panels */}
            <div className="space-y-6">
              {/* Part A: Current Recommended Investigations list */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                    Current Recommendations
                  </h4>
                  {hasPendingTests && (
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-bold text-teal-600 dark:text-teal-400">
                        {selectedTests.size} selected
                      </span>
                      <button onClick={selectAllPending} className="text-[10px] font-bold text-teal-600 hover:underline">
                        All
                      </button>
                      <span className="text-slate-300">|</span>
                      <button onClick={deselectAll} className="text-[10px] font-bold text-slate-400 hover:underline">
                        None
                      </button>
                    </div>
                  )}
                </div>
                {item.investigations.length === 0 ? (
                  <p className="text-xs text-slate-400 italic">No investigations recommended yet.</p>
                ) : (
                  <div className="rounded-xl border border-slate-200 dark:border-slate-855 overflow-hidden divide-y dark:divide-slate-855 bg-slate-50/20">
                    {item.investigations.map((inv) => {
                      const isPending = inv.status === "pending_approval";
                      const isChecked = selectedTests.has(inv.investigation_type);
                      return (
                        <div
                          key={inv.id}
                          className={cn(
                            "flex items-center gap-3 p-3.5 text-xs transition-colors",
                            isPending && isChecked && "bg-teal-50/50 dark:bg-teal-950/20",
                            isPending && "cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/30"
                          )}
                          onClick={() => isPending && toggleTest(inv.investigation_type)}
                        >
                          {isPending ? (
                            <input
                              type="checkbox"
                              checked={isChecked}
                              onChange={() => toggleTest(inv.investigation_type)}
                              onClick={(e) => e.stopPropagation()}
                              className="rounded border-slate-300 text-teal-600 focus:ring-teal-500 shrink-0 h-4 w-4 cursor-pointer"
                            />
                          ) : (
                            <div className="w-4 shrink-0" />
                          )}
                          <div className="flex-1 min-w-0">
                            <span className="font-bold text-slate-800 dark:text-slate-200">{inv.investigation_type}</span>
                            {inv.review_notes && (
                              <p className="mt-0.5 text-[10px] text-slate-400 font-medium">{inv.review_notes}</p>
                            )}
                          </div>
                          <span
                            className={cn(
                              "rounded font-bold px-2 py-0.5 text-[9px] uppercase tracking-wider shrink-0",
                              inv.status === "approved"
                                ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-300"
                                : inv.status === "rejected"
                                ? "bg-rose-100 text-rose-800 dark:bg-rose-950/50 dark:text-rose-300"
                                : "bg-amber-100 text-amber-800 dark:bg-amber-950/50 dark:text-amber-300 animate-pulse"
                            )}
                          >
                            {inv.status === "pending_approval" ? "PENDING" : inv.status}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Part B: Actions Desk */}
              {hasPendingTests && (
                <div className="border border-slate-200 dark:border-slate-800 rounded-2xl p-5 bg-slate-50/30 dark:bg-slate-900/50 space-y-4">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                    Clinical Approvals Panel
                  </h4>
                  
                  {/* Approval Notes textarea */}
                  <div>
                    <label className="text-[10px] font-bold text-slate-400 uppercase block mb-1">
                      Clinical Notes / Approvals Reason
                    </label>
                    <textarea
                      placeholder="Enter approvals justifications, clinical priority directions, or rationale notes…"
                      value={actionNotes}
                      onChange={(e) => setActionNotes(e.target.value)}
                      className="w-full rounded-xl border bg-white dark:bg-slate-900 p-3 text-xs outline-none focus:border-teal-500/60 min-h-[70px] resize-none"
                    />
                  </div>

                  {/* Actions buttons */}
                  <div className="flex flex-wrap items-center gap-2">
                    <Button
                      size="sm"
                      onClick={handleApprove}
                      disabled={actionLoading || selectedTests.size === 0}
                      className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold disabled:opacity-40"
                    >
                      {actionLoading ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <CheckCircle2 className="h-3.5 w-3.5 mr-1.5" />}
                      Approve Selected ({selectedTests.size})
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={handleReject}
                      disabled={actionLoading}
                      className="border-rose-500/20 text-rose-600 hover:text-rose-500 hover:bg-rose-50/50 font-bold"
                    >
                      Reject All
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setReturnOpen(true)}
                      className="border-amber-500/20 text-amber-600 hover:bg-amber-50 hover:text-amber-500"
                    >
                      Return to Nurse
                    </Button>
                  </div>
                </div>
              )}

              {/* Part C: Request Additional Investigation */}
              <div className="border border-slate-200 dark:border-slate-800 rounded-2xl p-5 bg-slate-50/30 dark:bg-slate-900/50 space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                  Recommend Additional Investigation
                </h4>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="e.g. Troponin, Chest X-ray, EKG, Cardiac Enzymes…"
                    value={newTest}
                    onChange={(e) => setNewTest(e.target.value)}
                    className="flex-1 rounded-xl border bg-white dark:bg-slate-900 px-3 py-2 text-xs outline-none focus:border-teal-500/60"
                  />
                  <Button
                    size="sm"
                    onClick={handleRecommendTest}
                    disabled={recommendLoading || !newTest.trim()}
                    className="bg-teal-600 hover:bg-teal-500 text-white"
                  >
                    {recommendLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Plus className="h-4 w-4 mr-1" />}
                    Request Test
                  </Button>
                </div>
              </div>
            </div>

            {/* Right side: Journey checklist card & Timeline Case history */}
            <div className="space-y-6 lg:border-l lg:border-slate-100 lg:dark:border-slate-800 lg:pl-6">
              <PatientJourneyCard
                caseId={item.case_id}
                status={item.status}
                arrivalType={item.arrival_type}
                createdAt={item.created_at}
              />
              <PatientTimeline intakeId={item.intake_id} />
            </div>
          </div>
        </div>
      )}

      {/* Return to Nurse dialog overlay */}
      {returnOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 max-w-md w-full shadow-2xl animate-in zoom-in-95 duration-200">
            <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <Clock className="h-4.5 w-4.5 text-amber-500" />
              Return Case to Nurse Station
            </h3>
            
            {/* Quick Templates select (Task 4 return template choices) */}
            <div className="mt-4 space-y-2">
              <label className="text-[10px] font-bold text-slate-400 uppercase">
                Return Reason Category
              </label>
              <div className="grid grid-cols-1 gap-2 pt-1.5">
                {[
                  "Poor image quality",
                  "Wrong patient evidence",
                  "Missing required investigation",
                  "Repeat acquisition required",
                  "Other",
                ].map((tmpl) => (
                  <label
                    key={tmpl}
                    className={cn(
                      "flex items-center gap-2 p-2.5 rounded-lg border text-xs font-semibold cursor-pointer transition-colors",
                      returnTemplate === tmpl
                        ? "border-teal-500 bg-teal-50/50 text-teal-700 dark:bg-teal-950/20 dark:text-teal-400"
                        : "border-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800"
                    )}
                  >
                    <input
                      type="radio"
                      name="return_template"
                      checked={returnTemplate === tmpl}
                      onChange={() => setReturnTemplate(tmpl)}
                      className="text-teal-600 focus:ring-teal-500 shrink-0 h-3.5 w-3.5"
                    />
                    {tmpl}
                  </label>
                ))}
              </div>
            </div>

            {/* Custom Notes text area */}
            <div className="mt-4">
              <label className="text-[10px] font-bold text-slate-400 uppercase block mb-1">
                Additional Explanation / Nursing Instructions
              </label>
              <textarea
                placeholder="Describe why this case is returned (e.g. which files are missing or blurred)…"
                value={returnNotes}
                onChange={(e) => setReturnNotes(e.target.value)}
                className="w-full rounded-xl border bg-slate-50 dark:bg-slate-900 p-3 text-xs outline-none focus:border-teal-500/60 min-h-[60px] resize-none"
              />
            </div>

            <div className="mt-6 flex justify-end gap-2">
              <Button size="sm" variant="outline" onClick={() => setReturnOpen(false)} disabled={returnLoading}>
                Cancel
              </Button>
              <Button size="sm" onClick={handleReturnToNurseSubmit} disabled={returnLoading} className="bg-amber-600 hover:bg-amber-500 text-white font-bold">
                {returnLoading ? <Loader2 className="h-4.5 w-4.5 animate-spin mr-1" /> : null}
                Return Case
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
