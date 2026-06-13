import { createFileRoute } from "@tanstack/react-router";
import { Info } from "lucide-react";
import { useCase } from "@/lib/case-store";
import { SectionHeader } from "@/components/section-header";
import { ProbabilityRow } from "@/components/probability-row";
import { MissingEvidenceList } from "@/components/missing-evidence-list";

export const Route = createFileRoute("/_app/differential")({
  head: () => ({
    meta: [
      { title: "Differential Diagnosis — PRATHAM" },
      { name: "description", content: "Assistive ranked differential with probability and AI confidence." },
    ],
  }),
  component: DifferentialPage,
});

function DifferentialPage() {
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

  return (
    <div className="mx-auto max-w-7xl px-5 py-8 md:px-8">
      <SectionHeader
        eyebrow="Stage 3 · Reasoning"
        title="Differential Diagnosis"
        description="Ranked possibilities to support clinical reasoning, not replace it."
      />

      <div className="mt-6 flex items-start gap-3 rounded-lg border border-primary/20 bg-primary/5 p-4">
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
        <p className="text-sm text-foreground">
          Probabilities are assistive estimates, not final diagnosis. <span className="text-muted-foreground">AI confidence is shown separately from probability — high probability does not imply high certainty.</span>
        </p>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_340px]">
        <div className="space-y-3">
          {patientCase.assistiveDifferential.map((d) => (
            <ProbabilityRow key={d.condition} item={d} />
          ))}
        </div>
        <MissingEvidenceList items={patientCase.evidence.missing} />
      </div>
    </div>
  );
}
