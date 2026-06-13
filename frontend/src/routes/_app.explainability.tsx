import { createFileRoute } from "@tanstack/react-router";
import { AlertTriangle } from "lucide-react";
import { useCase } from "@/lib/case-store";
import { SectionHeader } from "@/components/section-header";
import { EvidenceCard } from "@/components/evidence-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export const Route = createFileRoute("/_app/explainability")({
  head: () => ({
    meta: [
      { title: "Explainability — PRATHAM" },
      { name: "description", content: "Contributing evidence, provenance, and uncertainty for every estimate." },
    ],
  }),
  component: ExplainabilityPage,
});

function ExplainabilityPage() {
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

  const top = patientCase.assistiveDifferential[0];

  return (
    <div className="mx-auto max-w-7xl px-5 py-8 md:px-8">
      <SectionHeader
        eyebrow="Stage 3 · Reasoning"
        title="Explainability Panel"
        description="What contributed to the estimates, where it came from, and how confident the model is."
      />

      <div
        className={
          "mt-6 flex items-start gap-3 rounded-lg border p-4 " +
          (patientCase.evidenceCompleteness === "LOW"
            ? "border-[var(--color-severity-critical)]/30 bg-[var(--color-severity-critical-soft)]"
            : "border-[var(--color-severity-moderate)]/30 bg-[var(--color-severity-moderate-soft)]")
        }
      >
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[var(--color-severity-high)]" />
        <div>
          <p className="text-sm font-medium">
            Evidence completeness: {patientCase.evidenceCompleteness}.
          </p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Estimates may shift as more evidence arrives. AI confidence is reported separately for
            each condition.
          </p>
        </div>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_340px]">
        <div className="space-y-3">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            Contributing evidence
          </p>
          {patientCase.evidence.available.map((e) => (
            <EvidenceCard key={e.id} evidence={e} />
          ))}
        </div>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold">Why probability increased</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <p className="font-medium">{top.condition} · {top.probability}%</p>
            <ul className="space-y-2 text-sm text-muted-foreground">
              {top.contributingEvidence.map((c) => (
                <li key={c} className="flex items-start gap-2">
                  <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-primary" />
                  {c}
                </li>
              ))}
            </ul>
            <div className="rounded-md border bg-muted/40 p-3 text-xs leading-relaxed text-muted-foreground">
              <span className="font-semibold text-foreground">Uncertainty: </span>
              {top.uncertainty}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
