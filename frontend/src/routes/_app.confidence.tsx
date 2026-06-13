import { createFileRoute, Link } from "@tanstack/react-router";
import { ShieldAlert, ArrowRight } from "lucide-react";
import { useCase } from "@/lib/case-store";
import { SectionHeader } from "@/components/section-header";
import { MissingEvidenceList } from "@/components/missing-evidence-list";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/_app/confidence")({
  head: () => ({
    meta: [
      { title: "Confidence Suppression — PRATHAM" },
      { name: "description", content: "When evidence is insufficient, output is suppressed — by design." },
    ],
  }),
  component: ConfidencePage,
});

function ConfidencePage() {
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

  const isSuppressed = patientCase.evidenceCompleteness === "LOW";

  return (
    <div className="mx-auto max-w-6xl px-5 py-8 md:px-8">
      <SectionHeader
        eyebrow="Safety · Suppression"
        title="Confidence Suppression"
        description="PRATHAM withholds confident output when the underlying evidence cannot support it."
      />

      {isSuppressed ? (
        <Card className="mt-6 border-[var(--color-severity-critical)]/40 bg-[var(--color-severity-critical-soft)]">
          <CardContent className="p-6">
            <div className="flex items-start gap-4">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-background">
                <ShieldAlert className="h-6 w-6 text-[var(--color-severity-critical)]" />
              </div>
              <div>
                <p className="font-display text-xl font-semibold">
                  Insufficient evidence for reliable differential estimation.
                </p>
                <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted-foreground">
                  Available signal is too sparse to produce a trustworthy differential. PRATHAM is
                  withholding ranked estimates until more data arrives. Continue with standard
                  clinical workup; the panel will reactivate as evidence is added.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card className="mt-6">
          <CardContent className="p-6">
            <p className="text-sm">
              Evidence completeness is{" "}
              <span className="font-semibold">{patientCase.evidenceCompleteness}</span>. Estimates
              are released with explicit per-condition AI confidence. Switch to the
              <span className="font-medium"> Low-evidence case</span> in the top bar to see
              suppression in action.
            </p>
          </CardContent>
        </Card>
      )}

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <MissingEvidenceList items={patientCase.evidence.missing} />

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold">Low-confidence reasoning</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <p>
              Each available evidence piece is weak on its own, and key supporting investigations
              are missing. Producing a ranked differential at this stage would project false
              certainty.
            </p>
            <ul className="space-y-2">
              <li className="flex items-start gap-2">
                <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-primary" /> Probabilities
                kept low and AI confidence flagged as Low.
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-primary" /> Preparation
                alerts limited to precautionary actions only.
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-primary" /> Imaging
                interpretation withheld when no study is available.
              </li>
            </ul>
          </CardContent>
        </Card>
      </div>

      <div className="mt-6 flex flex-wrap items-center justify-between gap-3 rounded-lg border bg-muted/40 p-4">
        <p className="text-sm">
          Recommended next: complete missing investigations to lift suppression.
        </p>
        <Button asChild size="sm" variant="outline">
          <Link to="/investigations">
            Go to investigations <ArrowRight className="ml-1 h-3.5 w-3.5" />
          </Link>
        </Button>
      </div>


    </div>
  );
}
