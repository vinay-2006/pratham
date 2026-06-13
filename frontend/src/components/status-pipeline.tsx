import { Check } from "lucide-react";
import { workflowOrder, type WorkflowStatus } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

export function StatusPipeline({
  current,
  className,
}: {
  current: WorkflowStatus;
  className?: string;
}) {
  const idx = workflowOrder.indexOf(current);
  return (
    <ol className={cn("flex flex-wrap items-center gap-1.5 text-[11px]", className)}>
      {workflowOrder.map((s, i) => {
        const done = i < idx;
        const active = i === idx;
        return (
          <li key={s} className="flex items-center gap-1.5">
            <span
              className={cn(
                "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 font-medium",
                active && "border-primary bg-primary/10 text-primary",
                done && "border-[var(--color-severity-low)]/40 text-[var(--color-severity-low)]",
                !active && !done && "border-border text-muted-foreground",
              )}
            >
              {done && <Check className="h-3 w-3" />}
              {s}
            </span>
            {i < workflowOrder.length - 1 && (
              <span className="h-px w-3 bg-border md:w-4" aria-hidden />
            )}
          </li>
        );
      })}
    </ol>
  );
}

export function PatientStatusChip({ status }: { status: string }) {
  const styles: Record<string, string> = {
    "Intake Pending": "bg-muted text-muted-foreground border-border",
    "Awaiting Doctor Approval":
      "bg-[var(--color-severity-moderate-soft)] text-[color-mix(in_oklab,var(--color-severity-moderate)_55%,black)] dark:text-[var(--color-severity-moderate)] border-[var(--color-severity-moderate)]/30",
    "Investigation Approved":
      "bg-primary/10 text-primary border-primary/30",
    "Investigation Running":
      "bg-[var(--color-severity-high-soft)] text-[color-mix(in_oklab,var(--color-severity-high)_70%,black)] dark:text-[var(--color-severity-high)] border-[var(--color-severity-high)]/30",
    "Results Available":
      "bg-[var(--color-severity-low-soft)] text-[var(--color-severity-low)] border-[var(--color-severity-low)]/30",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide",
        styles[status] ?? "border-border bg-muted text-muted-foreground",
      )}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {status}
    </span>
  );
}
