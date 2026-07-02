/**
 * Doctor Report — Latest Patient Redirect
 *
 * Route: /doctor/report/latest
 *
 * Fetches the most recent patient from the queue and redirects to
 * /doctor/report/{intakeId}. If no patients exist, shows an
 * informational message with a link to the queue.
 */

import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { Activity, AlertCircle, FileText, Users } from "lucide-react";
import { fetchPatientQueue } from "@/lib/patient-queue-api";
import { SectionHeader } from "@/components/section-header";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/_app/doctor/report/latest")({
  head: () => ({
    meta: [
      { title: "Clinical Report — PRATHAM" },
      {
        name: "description",
        content: "Redirects to the most recent patient clinical report.",
      },
    ],
  }),
  component: LatestReportRedirect,
});

function LatestReportRedirect() {
  const navigate = useNavigate();

  const { data: queue, isLoading, isError } = useQuery({
    queryKey: ["patient-queue"],
    queryFn: fetchPatientQueue,
    staleTime: 30_000,
  });

  useEffect(() => {
    if (queue && queue.length > 0) {
      // Navigate to the most recent patient's report
      const latest = queue[0];
      navigate({
        to: "/doctor/report/$intakeId",
        params: { intakeId: latest.intake_id },
        replace: true,
      });
    }
  }, [queue, navigate]);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-7xl px-5 py-8 md:px-8">
        <div className="flex items-center justify-center py-20">
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <Activity className="h-5 w-5 animate-pulse text-primary" />
            Finding most recent patient…
          </div>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="mx-auto max-w-7xl px-5 py-8 md:px-8">
        <div className="flex items-center gap-3 rounded-lg border border-rose-500/20 bg-rose-500/5 p-6 text-sm text-rose-400">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <div>
            <p className="font-medium">Failed to load patient queue</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Could not fetch the patient list to find the latest report.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Queue loaded but empty — show a helpful message
  return (
    <div className="mx-auto max-w-7xl px-5 py-8 md:px-8">
      <SectionHeader
        eyebrow="Doctor workstation"
        title="Clinical Intelligence Report"
        description="Select a patient from the queue to view their full AI-powered clinical report."
      />

      <Card className="mt-8">
        <CardContent className="p-10 text-center">
          <FileText className="mx-auto h-10 w-10 text-muted-foreground/30" />
          <p className="mt-4 text-sm font-medium">No patients in queue</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Submit a new intake to generate a Clinical Intelligence Report.
          </p>
          <div className="mt-6 flex items-center justify-center gap-3">
            <Button asChild size="sm" variant="outline">
              <Link to="/nurse/queue">
                <Users className="mr-1.5 h-3.5 w-3.5" />
                View Patient Queue
              </Link>
            </Button>
            <Button asChild size="sm">
              <Link to="/nurse/intake">New Intake</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
