import { createFileRoute, Link } from "@tanstack/react-router";
import { Plus } from "lucide-react";
import { SectionHeader } from "@/components/section-header";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { PatientStatus } from "@/lib/mock-data";

export const Route = createFileRoute("/_app/nurse/queue")({
  head: () => ({
    meta: [
      { title: "Patient Queue — PRATHAM" },
      { name: "description", content: "Full emergency patient queue grouped by status." },
    ],
  }),
  component: NurseQueue,
});

const GROUPS: PatientStatus[] = [
  "Intake Pending",
  "Awaiting Doctor Approval",
  "Investigation Approved",
  "Investigation Running",
  "Results Available",
];

function NurseQueue() {
  return (
    <div className="mx-auto max-w-7xl px-5 py-8 md:px-8">
      <SectionHeader
        eyebrow="Nurse station"
        title="Patient Queue"
        description="Grouped by workflow status across the emergency floor."
      />

      <div className="mt-8 space-y-6">
        {GROUPS.map((g) => (
          <section key={g}>
            <h2 className="mb-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              {g} · 0
            </h2>
            <Card>
              <CardContent className="p-6 text-center text-sm text-muted-foreground">
                No patients
              </CardContent>
            </Card>
          </section>
        ))}

        <Card>
          <CardContent className="p-8 text-center">
            <p className="text-sm text-muted-foreground">
              Queue empty — submit a new intake to begin
            </p>
            <Button asChild size="sm" variant="outline" className="mt-4">
              <Link to="/nurse/intake">
                <Plus className="mr-1.5 h-3.5 w-3.5" /> New intake
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
