
import { createFileRoute, Link } from "@tanstack/react-router";
import { AlertTriangle, ArrowRight, Bell } from "lucide-react";
import { useCase } from "@/lib/case-store";
import { SectionHeader } from "@/components/section-header";
import { RiskCard } from "@/components/risk-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { useState } from "react";

export const Route = createFileRoute("/_app/dashboard")({
  head: () => ({
    meta: [
      { title: "Operational Risk Dashboard — PRATHAM" },
      { name: "description", content: "Hospital command center view of derived operational risk." },
    ],
  }),
  component: DashboardPage,
});

function DashboardPage() {
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

  const [alerts, setAlerts] = useState(patientCase.preparationAlerts);

  // sync alerts when case toggles
  if (alerts[0]?.label !== patientCase.preparationAlerts[0]?.label || alerts.length !== patientCase.preparationAlerts.length) {
    setAlerts(patientCase.preparationAlerts);
  }

  const topAlert = [...patientCase.operationalRiskEstimates].sort((a, b) => b.value - a.value)[0];

  return (
    <div className="mx-auto max-w-7xl px-5 py-8 md:px-8">
      <SectionHeader
        eyebrow="Stage 2 · Operational"
        title="Operational Risk Dashboard"
        description="Derived operational risk estimates that drive hospital preparation. Not clinical diagnoses."
        actions={
          <Button asChild size="sm" variant="outline">
            <Link to="/investigations">
              Investigations <ArrowRight className="ml-1 h-3.5 w-3.5" />
            </Link>
          </Button>
        }
      />

      <div className="mt-6 rounded-lg border border-[var(--color-severity-high)]/30 bg-[var(--color-severity-high-soft)] p-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-[var(--color-severity-high)]" />
          <div>
            <p className="font-medium">High {topAlert.label.toLowerCase()} detected.</p>
            <p className="mt-0.5 text-sm text-muted-foreground">{topAlert.note}</p>
          </div>
        </div>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {patientCase.operationalRiskEstimates.map((r) => (
          <RiskCard key={r.label} risk={r} />
        ))}
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm font-semibold">
              <Bell className="h-4 w-4 text-primary" />
              Preparation alerts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="divide-y">
              {alerts.map((a, i) => (
                <li key={a.label} className="flex items-center justify-between gap-3 py-3 first:pt-0 last:pb-0">
                  <div>
                    <p className="text-sm font-medium">{a.label}</p>
                    <p className="text-xs text-muted-foreground">{a.note}</p>
                  </div>
                  <Switch
                    checked={a.active}
                    onCheckedChange={(v) =>
                      setAlerts((prev) => prev.map((x, j) => (j === i ? { ...x, active: v } : x)))
                    }
                    aria-label={`Toggle ${a.label}`}
                  />
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold">Patient snapshot</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <Row k="Heart rate" v={patientCase.vitals.heartRate ? `${patientCase.vitals.heartRate} bpm` : "—"} />
            <Row k="SpO₂" v={patientCase.vitals.spo2 ? `${patientCase.vitals.spo2}%` : "—"} />
            <Row k="Blood pressure" v={patientCase.vitals.bloodPressure || "—"} />
            <Row k="Respiratory rate" v={patientCase.vitals.respiratoryRate ? String(patientCase.vitals.respiratoryRate) : "—"} />
            <Row k="Temperature" v={patientCase.vitals.temperature ? `${patientCase.vitals.temperature}°C` : "—"} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex items-center justify-between border-b pb-2 last:border-0 last:pb-0">
      <span className="text-xs text-muted-foreground">{k}</span>
      <span className="font-medium tabular-nums">{v}</span>
    </div>
  );
}
