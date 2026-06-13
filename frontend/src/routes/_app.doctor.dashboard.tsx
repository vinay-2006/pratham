import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight, Bell, Brain, ShieldAlert, Stethoscope } from "lucide-react";
import { useCase } from "@/lib/case-store";
import { SectionHeader } from "@/components/section-header";
import { NotificationCard } from "@/components/notification-card";
import { StatusPipeline } from "@/components/status-pipeline";
import { RiskCard } from "@/components/risk-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/_app/doctor/dashboard")({
  head: () => ({
    meta: [
      { title: "Doctor Dashboard — PRATHAM" },
      { name: "description", content: "Clinical review workstation with pending approvals." },
    ],
  }),
  component: DoctorDashboard,
});

function DoctorDashboard() {
  const { notifications, patientCase, pendingCount, activeEmergencyCount } = useCase();
  const pending = notifications.filter((n) => n.status === "Pending Approval");
  const recent = notifications.filter((n) => n.status !== "Pending Approval").slice(0, 3);

  return (
    <div className="mx-auto max-w-7xl px-5 py-8 md:px-8">
      <SectionHeader
        eyebrow="Doctor workstation"
        title="Clinical Dashboard"
        description="System-generated investigation requests, emergency priority queue, and the AI-assisted review workspace."
        actions={
          <Button asChild size="sm" variant="outline">
            <Link to="/doctor/approvals">
              All approvals <ArrowRight className="ml-1 h-3.5 w-3.5" />
            </Link>
          </Button>
        }
      />

      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        <Tile label="Pending approvals" value={pendingCount} accent="primary" />
        <Tile label="Active emergencies" value={activeEmergencyCount} accent="high" />
        <Tile label="Current case" value={patientCase?.priorityLabel ?? "—"} accent="moderate" />
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="flex items-center gap-2 text-sm font-semibold">
              <Bell className="h-4 w-4 text-primary" />
              Pending investigation requests
              <span className="rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-semibold text-primary">
                {pending.length}
              </span>
            </h2>
          </div>

          {pending.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center text-sm text-muted-foreground">
                No pending requests. The system will notify you when a new intake exceeds risk
                thresholds.
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {pending.map((n) => (
                <NotificationCard key={n.id} n={n} />
              ))}
            </div>
          )}

          {recent.length > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold">Recently actioned</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {recent.map((n) => (
                  <div key={n.id} className="flex items-center justify-between border-b pb-2 last:border-0 last:pb-0">
                    <div>
                      <p className="text-sm font-medium">{n.patientName}</p>
                      <p className="text-[11px] text-muted-foreground">
                        {n.symptoms.join(", ")} · {n.timestamp}
                      </p>
                    </div>
                    <span className="text-[11px] font-medium text-muted-foreground">{n.status}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold">Current patient · operational risk</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3 sm:grid-cols-2">
              {(patientCase?.operationalRiskEstimates ?? []).slice(0, 4).map((r) => (
                <RiskCard key={r.label} risk={r} />
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold">Investigation pipeline</CardTitle>
            </CardHeader>
            <CardContent>
              <StatusPipeline current="In Progress" />
              <p className="mt-3 text-[11px] leading-relaxed text-muted-foreground">
                Current case is in the workup phase. Results will appear in the review workstation.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold">Jump to</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Jump to="/doctor/review" icon={Stethoscope} label="Patient review workspace" />
              <Jump to="/explainability" icon={Brain} label="Explainability panel" />
              <Jump to="/confidence" icon={ShieldAlert} label="Confidence assessment" />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function Tile({
  label,
  value,
  accent,
}: {
  label: string;
  value: string | number;
  accent: "primary" | "high" | "moderate";
}) {
  const accentVar =
    accent === "high"
      ? "var(--color-severity-high)"
      : accent === "moderate"
      ? "var(--color-severity-moderate)"
      : "var(--color-primary)";
  return (
    <Card>
      <CardContent className="p-5">
        <p className="text-[11px] uppercase tracking-wider text-muted-foreground">{label}</p>
        <p className="mt-1 font-display text-3xl font-semibold tabular-nums" style={{ color: accentVar }}>
          {value}
        </p>
      </CardContent>
    </Card>
  );
}

function Jump({ to, icon: Icon, label }: { to: string; icon: typeof Bell; label: string }) {
  return (
    <Link
      to={to}
      className="flex items-center gap-3 rounded-md border bg-card px-3 py-2.5 text-sm transition-colors hover:bg-muted/60"
    >
      <Icon className="h-4 w-4 text-primary" />
      <span className="flex-1">{label}</span>
      <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
    </Link>
  );
}
