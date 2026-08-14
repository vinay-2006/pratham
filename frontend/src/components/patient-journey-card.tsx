import { useMemo } from "react";
import { CheckCircle2, Circle, Clock, Loader2, PlayCircle } from "lucide-react";
import { WorkflowStatus, WORKFLOW_LABELS } from "@/lib/mock-data";

interface PatientJourneyCardProps {
  caseId: string;
  status: WorkflowStatus;
  arrivalType: string;
  createdAt: string;
  updatedAt?: string;
}

export function PatientJourneyCard({
  caseId,
  status,
  arrivalType,
  createdAt,
  updatedAt,
}: PatientJourneyCardProps) {
  // Define the core milestones for the checklist
  const milestones = useMemo(() => {
    return [
      {
        id: "intake",
        label: "Intake Submitted",
        statuses: [
          WorkflowStatus.INTAKE_SUBMITTED,
          WorkflowStatus.EN_ROUTE,
          WorkflowStatus.ARRIVED,
          WorkflowStatus.AWAITING_APPROVAL,
          WorkflowStatus.APPROVED,
          WorkflowStatus.UPLOAD_PENDING,
          WorkflowStatus.ANALYSIS_RUNNING,
          WorkflowStatus.REPORT_READY,
          WorkflowStatus.UNDER_REVIEW,
          WorkflowStatus.CLOSED,
        ],
      },
      {
        id: "arrival",
        label: "Arrival Confirmed",
        statuses: [
          WorkflowStatus.ARRIVED,
          WorkflowStatus.AWAITING_APPROVAL,
          WorkflowStatus.APPROVED,
          WorkflowStatus.UPLOAD_PENDING,
          WorkflowStatus.ANALYSIS_RUNNING,
          WorkflowStatus.REPORT_READY,
          WorkflowStatus.UNDER_REVIEW,
          WorkflowStatus.CLOSED,
        ],
      },
      {
        id: "approval",
        label: "Doctor Approval",
        statuses: [
          WorkflowStatus.APPROVED,
          WorkflowStatus.UPLOAD_PENDING,
          WorkflowStatus.ANALYSIS_RUNNING,
          WorkflowStatus.REPORT_READY,
          WorkflowStatus.UNDER_REVIEW,
          WorkflowStatus.CLOSED,
        ],
      },
      {
        id: "evidence",
        label: "Evidence Upload",
        statuses: [
          WorkflowStatus.UPLOAD_PENDING,
          WorkflowStatus.ANALYSIS_RUNNING,
          WorkflowStatus.REPORT_READY,
          WorkflowStatus.UNDER_REVIEW,
          WorkflowStatus.CLOSED,
        ],
      },
      {
        id: "analysis",
        label: "Analysis Running",
        statuses: [
          WorkflowStatus.ANALYSIS_RUNNING,
          WorkflowStatus.REPORT_READY,
          WorkflowStatus.UNDER_REVIEW,
          WorkflowStatus.CLOSED,
        ],
      },
      {
        id: "report",
        label: "Report Ready",
        statuses: [
          WorkflowStatus.REPORT_READY,
          WorkflowStatus.UNDER_REVIEW,
          WorkflowStatus.CLOSED,
        ],
      },
      {
        id: "closed",
        label: "Case Closed",
        statuses: [WorkflowStatus.CLOSED],
      },
    ];
  }, []);

  // Determine current active milestone index
  const activeMilestoneIndex = useMemo(() => {
    // Find the latest milestone that includes the current status
    for (let i = milestones.length - 1; i >= 0; i--) {
      if (milestones[i].statuses.includes(status)) {
        return i;
      }
    }
    return -1;
  }, [status, milestones]);

  // Format date helper
  const formatTime = (isoString?: string) => {
    if (!isoString) return "—";
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    } catch {
      return "—";
    }
  };

  const isOffline = status === WorkflowStatus.OFFLINE;

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xl transition-all duration-300">
      {/* Card Header with Case ID */}
      <div className="bg-gradient-to-r from-teal-500 to-emerald-600 px-6 py-4 text-white">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider opacity-75">
              Emergency Case
            </span>
            <h3 className="font-mono text-lg font-bold tracking-tight">{caseId}</h3>
          </div>
          <span className="rounded-full bg-white/20 px-3 py-1 text-xs font-semibold capitalize backdrop-blur-sm">
            {arrivalType.replace("_", " ")}
          </span>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Status display */}
        <div>
          <span className="text-xs font-medium text-slate-400 dark:text-slate-500">
            Current Status
          </span>
          <div className="mt-1 flex items-center gap-2">
            {status === WorkflowStatus.ANALYSIS_RUNNING && (
              <Loader2 className="h-4 w-4 animate-spin text-amber-500" />
            )}
            <span className="text-base font-bold text-slate-800 dark:text-slate-100">
              {WORKFLOW_LABELS[status] || status}
            </span>
          </div>
        </div>


        {/* Checklist Timeline */}
        <div className="border-t border-slate-100 dark:border-slate-800 pt-4">
          <span className="text-xs font-medium text-slate-400 dark:text-slate-500 block mb-3">
            Milestones Checklist
          </span>
          <div className="space-y-3">
            {milestones.map((m, idx) => {
              const isCompleted = idx < activeMilestoneIndex;
              const isActive = idx === activeMilestoneIndex;

              return (
                <div key={m.id} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {isOffline ? (
                      <Circle className="h-4 w-4 text-slate-300 dark:text-slate-700" />
                    ) : isCompleted ? (
                      <CheckCircle2 className="h-4.5 w-4.5 text-emerald-500 fill-emerald-50/50 dark:fill-emerald-950/20" />
                    ) : isActive ? (
                      <PlayCircle className="h-4.5 w-4.5 text-teal-500 fill-teal-50/50 dark:fill-teal-950/20 animate-pulse" />
                    ) : (
                      <Circle className="h-4.5 w-4.5 text-slate-300 dark:text-slate-700" />
                    )}
                    <span
                      className={`text-xs font-medium ${
                        isCompleted
                          ? "text-slate-800 dark:text-slate-200 line-through decoration-slate-300 dark:decoration-slate-700"
                          : isActive
                          ? "text-teal-600 dark:text-teal-400 font-bold"
                          : "text-slate-400 dark:text-slate-600"
                      }`}
                    >
                      {m.label}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Meta Timestamps */}
        <div className="border-t border-slate-100 dark:border-slate-800 pt-4 flex justify-between text-[11px] text-slate-400 dark:text-slate-500">
          <div className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            <span>Intake: {formatTime(createdAt)}</span>
          </div>
          {updatedAt && (
            <span>Last Update: {formatTime(updatedAt)}</span>
          )}
        </div>
      </div>
    </div>
  );
}
