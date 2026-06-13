import { Card, CardContent } from "@/components/ui/card";
import { SeverityBadge } from "@/components/severity-badge";
import type { RiskEstimate } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

const fillColor: Record<RiskEstimate["severity"], string> = {
  critical: "bg-[var(--color-severity-critical)]",
  high: "bg-[var(--color-severity-high)]",
  moderate: "bg-[var(--color-severity-moderate)]",
  low: "bg-[var(--color-severity-low)]",
};

export function RiskCard({ risk }: { risk: RiskEstimate }) {
  return (
    <Card className="overflow-hidden">
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              {risk.label}
            </p>
            <p className="mt-1 font-display text-3xl font-semibold tabular-nums">
              {risk.value}
              <span className="text-base font-normal text-muted-foreground">/100</span>
            </p>
          </div>
          <SeverityBadge severity={risk.severity}>{risk.severity}</SeverityBadge>
        </div>

        <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-muted">
          <div
            className={cn("h-full rounded-full transition-all", fillColor[risk.severity])}
            style={{ width: `${risk.value}%` }}
          />
        </div>

        <p className="mt-3 text-xs leading-relaxed text-muted-foreground">{risk.note}</p>
      </CardContent>
    </Card>
  );
}
