import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { CheckCircle2, Circle, Clock } from "lucide-react";
import { useCase } from "@/lib/case-store";
import { SectionHeader } from "@/components/section-header";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { InvestigationStatus } from "@/lib/mock-data";

export const Route = createFileRoute("/_app/investigations")({
  head: () => ({
    meta: [
      { title: "Investigation Recommendations — PRATHAM" },
      { name: "description", content: "Recommended investigations with doctor confirmation flow." },
    ],
  }),
  component: InvestigationsPage,
});

const STATUS_META: Record<
  InvestigationStatus,
  { icon: typeof Circle; cls: string; ring: string }
> = {
  Pending: { icon: Circle, cls: "text-muted-foreground", ring: "border-border" },
  "In progress": {
    icon: Clock,
    cls: "text-[var(--color-severity-moderate)]",
    ring: "border-[var(--color-severity-moderate)]/40",
  },
  Confirmed: {
    icon: CheckCircle2,
    cls: "text-[var(--color-severity-low)]",
    ring: "border-[var(--color-severity-low)]/40",
  },
};

function InvestigationsPage() {
  const { patientCase } = useCase();

  if (!patientCase) {
    return (
      <div className="mx-auto max-w-5xl px-5 py-8 md:px-8">
        <div className="rounded-lg border bg-muted/30 p-12 text-center">
          <p className="text-sm text-muted-foreground">No patient selected. Submit a new intake to begin.</p>
        </div>
      </div>
    );
  }

  const [list, setList] = useState(patientCase.recommendedInvestigations);

  if (list[0]?.name !== patientCase.recommendedInvestigations[0]?.name) {
    setList(patientCase.recommendedInvestigations);
  }

  const advance = (i: number) =>
    setList((curr) =>
      curr.map((it, idx) => {
        if (idx !== i) return it;
        const next: InvestigationStatus =
          it.status === "Pending" ? "In progress" : it.status === "In progress" ? "Confirmed" : "Confirmed";
        return { ...it, status: next };
      }),
    );

  return (
    <div className="mx-auto max-w-5xl px-5 py-8 md:px-8">
      <SectionHeader
        eyebrow="Stage 2 · Workup"
        title="Investigation Recommendations"
        description="Assistive checklist. Doctors confirm each step — nothing is auto-ordered."
      />

      <Card className="mt-6">
        <CardContent className="p-0">
          <ul className="divide-y">
            {list.map((inv, i) => {
              const meta = STATUS_META[inv.status];
              const Icon = meta.icon;
              return (
                <li key={inv.name} className="flex items-center gap-4 px-5 py-4">
                  <div
                    className={cn(
                      "flex h-9 w-9 shrink-0 items-center justify-center rounded-full border",
                      meta.ring,
                    )}
                  >
                    <Icon className={cn("h-4 w-4", meta.cls)} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="font-medium">{inv.name}</p>
                    <p className="text-xs text-muted-foreground">{inv.rationale}</p>
                  </div>
                  <span className={cn("text-xs font-medium", meta.cls)}>{inv.status}</span>
                  <Button
                    size="sm"
                    variant={inv.status === "Confirmed" ? "outline" : "default"}
                    disabled={inv.status === "Confirmed"}
                    onClick={() => advance(i)}
                  >
                    {inv.status === "Pending"
                      ? "Start"
                      : inv.status === "In progress"
                      ? "Confirm"
                      : "Done"}
                  </Button>
                </li>
              );
            })}
          </ul>
        </CardContent>
      </Card>

      <p className="mt-6 text-xs leading-relaxed text-muted-foreground">
        Doctor confirmation is required before any investigation is acted upon. PRATHAM does not
        order tests autonomously.
      </p>
    </div>
  );
}
