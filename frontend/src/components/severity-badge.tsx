import { cn } from "@/lib/utils";
import type { Severity, AIConfidence } from "@/lib/mock-data";

const severityStyles: Record<Severity, string> = {
  critical: "bg-[var(--color-severity-critical-soft)] text-[var(--color-severity-critical)]",
  high: "bg-[var(--color-severity-high-soft)] text-[color-mix(in_oklab,var(--color-severity-high)_70%,black)] dark:text-[var(--color-severity-high)]",
  moderate: "bg-[var(--color-severity-moderate-soft)] text-[color-mix(in_oklab,var(--color-severity-moderate)_55%,black)] dark:text-[var(--color-severity-moderate)]",
  low: "bg-[var(--color-severity-low-soft)] text-[var(--color-severity-low)]",
};

export function SeverityBadge({
  severity,
  children,
  className,
}: {
  severity: Severity;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-[11px] font-medium",
        severityStyles[severity],
        className,
      )}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {children}
    </span>
  );
}

const confidenceStyles: Record<AIConfidence, string> = {
  High: "border-[var(--color-severity-low)]/30 text-[var(--color-severity-low)] bg-[var(--color-severity-low-soft)]",
  Moderate: "border-[var(--color-severity-moderate)]/30 text-[color-mix(in_oklab,var(--color-severity-moderate)_55%,black)] dark:text-[var(--color-severity-moderate)] bg-[var(--color-severity-moderate-soft)]",
  Low: "border-muted-foreground/30 text-muted-foreground bg-muted",
};

export function AIConfidenceBadge({ level }: { level: AIConfidence }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide",
        confidenceStyles[level],
      )}
      title="AI confidence is independent of probability. It reflects how trustworthy the estimate is given available evidence."
    >
      AI {level}
    </span>
  );
}
