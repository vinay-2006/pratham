import { AIConfidenceBadge } from "@/components/severity-badge";
import type { DifferentialItem } from "@/lib/mock-data";

export function ProbabilityRow({ item }: { item: DifferentialItem }) {
  return (
    <div className="rounded-lg border bg-card p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="font-medium">{item.condition}</p>
          <p className="mt-0.5 text-xs text-muted-foreground">{item.uncertainty}</p>
        </div>
        <div className="flex shrink-0 items-center gap-3">
          <div className="text-right">
            <p className="font-display text-xl font-semibold tabular-nums leading-none">
              {item.probability}%
            </p>
            <p className="mt-0.5 text-[10px] uppercase tracking-wider text-muted-foreground">
              probability
            </p>
          </div>
          <AIConfidenceBadge level={item.aiConfidence} />
        </div>
      </div>

      <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-primary"
          style={{ width: `${item.probability}%` }}
        />
      </div>

      {item.contributingEvidence.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {item.contributingEvidence.map((e) => (
            <span
              key={e}
              className="rounded-md bg-muted px-2 py-0.5 text-[11px] text-muted-foreground"
            >
              {e}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
