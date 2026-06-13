import { cn } from "@/lib/utils";
import type { Completeness } from "@/lib/mock-data";

const styles: Record<Completeness, string> = {
  LOW: "bg-[var(--color-severity-critical-soft)] text-[var(--color-severity-critical)] border-[var(--color-severity-critical)]/30",
  MODERATE: "bg-[var(--color-severity-moderate-soft)] text-[color-mix(in_oklab,var(--color-severity-moderate)_60%,black)] border-[var(--color-severity-moderate)]/30 dark:text-[var(--color-severity-moderate)]",
  HIGH: "bg-[var(--color-severity-low-soft)] text-[var(--color-severity-low)] border-[var(--color-severity-low)]/30",
};

export function EvidenceCompletenessPill({ level }: { level: Completeness }) {
  return (
    <div
      className={cn(
        "flex items-center gap-2 rounded-full border px-3 py-1 text-[10px] font-medium uppercase tracking-wider",
        styles[level],
      )}
      title="Evidence completeness across vitals, labs, imaging, and history"
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      Evidence · {level}
    </div>
  );
}
