import { createFileRoute } from "@tanstack/react-router";
import { useCase } from "@/lib/case-store";
import { SectionHeader } from "@/components/section-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ProbabilityRow } from "@/components/probability-row";
import { MissingEvidenceList } from "@/components/missing-evidence-list";
import { SeverityBadge } from "@/components/severity-badge";
import { StatusPipeline } from "@/components/status-pipeline";
import xrayUrl from "@/assets/mock-xray.jpg";

export const Route = createFileRoute("/_app/doctor/review")({
  head: () => ({
    meta: [
      { title: "Patient Review — PRATHAM" },
      { name: "description", content: "Patient review workspace for on-arrival clinical review." },
    ],
  }),
  component: ReviewPage,
});

function ReviewPage() {
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

  const v = patientCase.vitals;

  return (
    <div className="mx-auto max-w-7xl px-5 py-8 md:px-8">
      <SectionHeader
        eyebrow="Doctor workstation"
        title="Patient Review"
        description="Consolidated workstation. Raw evidence on the left; AI-assisted summary on the right."
        actions={<SeverityBadge severity={patientCase.overallSeverity}>{patientCase.priorityLabel}</SeverityBadge>}
      />

      <div className="mt-4">
        <StatusPipeline current="In Progress" />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1.2fr_1fr]">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold">Raw evidence</CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="vitals">
              <TabsList>
                <TabsTrigger value="vitals">Vitals</TabsTrigger>
                <TabsTrigger value="labs">Labs</TabsTrigger>
                <TabsTrigger value="imaging">Imaging</TabsTrigger>
                <TabsTrigger value="notes">Notes</TabsTrigger>
              </TabsList>

              <TabsContent value="vitals" className="mt-4 grid gap-3 sm:grid-cols-2">
                <Stat l="Heart rate" v={v.heartRate ? `${v.heartRate} bpm` : "—"} />
                <Stat l="SpO₂" v={v.spo2 ? `${v.spo2}%` : "—"} />
                <Stat l="Blood pressure" v={v.bloodPressure || "—"} />
                <Stat l="Respiratory rate" v={v.respiratoryRate ? String(v.respiratoryRate) : "—"} />
                <Stat l="Temperature" v={v.temperature ? `${v.temperature}°C` : "—"} />
              </TabsContent>

              <TabsContent value="labs" className="mt-4">
                <ul className="divide-y rounded-md border">
                  {patientCase.recommendedInvestigations
                    .filter((i) => /trop|cbc|lab/i.test(i.name))
                    .map((l) => (
                      <li key={l.name} className="flex items-center justify-between px-4 py-3">
                        <span className="text-sm">{l.name}</span>
                        <span className="text-xs text-muted-foreground">{l.status}</span>
                      </li>
                    ))}
                </ul>
              </TabsContent>

              <TabsContent value="imaging" className="mt-4">
                {patientCase.imaging.suppressed ? (
                  <p className="text-sm text-muted-foreground">No imaging available.</p>
                ) : (
                  <div className="overflow-hidden rounded-md border bg-black">
                    <img src={xrayUrl} alt="X-ray" loading="lazy" className="block w-full" width={1024} height={1024} />
                  </div>
                )}
              </TabsContent>

              <TabsContent value="notes" className="mt-4">
                <div className="rounded-md border bg-muted/40 p-4 text-sm leading-relaxed">
                  {patientCase.freeText}
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold">AI summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <p className="leading-relaxed">
                {patientCase.patient.name}, {patientCase.patient.age}{patientCase.patient.sex}.
                Presenting with {patientCase.symptoms.join(", ").toLowerCase() || "non-specific symptoms"}.
                Evidence completeness is <span className="font-medium">{patientCase.evidenceCompleteness}</span>.
              </p>
              <p className="text-xs text-muted-foreground">
                Probability and AI confidence are reported independently. Suppression rules apply
                when evidence is insufficient.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold">Condition probabilities</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {patientCase.assistiveDifferential.slice(0, 3).map((d) => (
                <ProbabilityRow key={d.condition} item={d} />
              ))}
            </CardContent>
          </Card>

          <MissingEvidenceList items={patientCase.evidence.missing} />
        </div>
      </div>
    </div>
  );
}

function Stat({ l, v }: { l: string; v: string }) {
  return (
    <div className="rounded-md border bg-muted/30 p-3">
      <p className="text-[11px] uppercase tracking-wider text-muted-foreground">{l}</p>
      <p className="mt-1 font-display text-lg font-semibold tabular-nums">{v}</p>
    </div>
  );
}
