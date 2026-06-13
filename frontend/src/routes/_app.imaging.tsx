import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { ShieldAlert } from "lucide-react";
import { useCase } from "@/lib/case-store";
import { SectionHeader } from "@/components/section-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { AIConfidenceBadge } from "@/components/severity-badge";
import xrayUrl from "@/assets/mock-xray.jpg";

export const Route = createFileRoute("/_app/imaging")({
  head: () => ({
    meta: [
      { title: "Imaging Analysis — PRATHAM" },
      { name: "description", content: "Chest X-ray with assistive interpretation and confidence." },
    ],
  }),
  component: ImagingPage,
});

function ImagingPage() {
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

  const [showHeatmap, setShowHeatmap] = useState(true);
  const { imaging } = patientCase;
  const prob = Math.round(imaging.pneumoniaProbability * 100);

  return (
    <div className="mx-auto max-w-7xl px-5 py-8 md:px-8">
      <SectionHeader
        eyebrow="Imaging"
        title="Imaging Analysis Viewer"
        description="AI evidence interpretation overlaid on the source image. Assistive only — not a diagnostic call."
      />

      <div className="mt-8 grid gap-6 lg:grid-cols-[1fr_360px]">
        <Card className="overflow-hidden">
          <CardHeader className="flex flex-row items-center justify-between gap-3 pb-3">
            <div>
              <CardTitle className="text-sm font-semibold">{imaging.studyType}</CardTitle>
              <p className="text-xs text-muted-foreground">Patient {patientCase.patient.name}</p>
            </div>
            <label className="flex items-center gap-2 text-xs">
              <span className="text-muted-foreground">Grad-CAM overlay</span>
              <Switch
                checked={showHeatmap && !imaging.suppressed}
                onCheckedChange={setShowHeatmap}
                disabled={imaging.suppressed}
              />
            </label>
          </CardHeader>
          <CardContent>
            <div className="relative overflow-hidden rounded-lg border bg-black">
              {imaging.suppressed ? (
                <div className="flex aspect-square w-full items-center justify-center bg-muted text-center">
                  <div className="px-6">
                    <ShieldAlert className="mx-auto h-8 w-8 text-[var(--color-severity-high)]" />
                    <p className="mt-3 font-medium">No imaging available</p>
                    <p className="mt-1 text-sm text-muted-foreground">
                      Interpretation suppressed for this case.
                    </p>
                  </div>
                </div>
              ) : (
                <>
                  <img
                    src={xrayUrl}
                    alt="Chest X-ray (mock)"
                    className="block w-full"
                    width={1024}
                    height={1024}
                  />
                  {showHeatmap && (
                    <div className="pointer-events-none absolute inset-0">
                      {imaging.heatmapHotspots.map((h, i) => (
                        <div
                          key={i}
                          className="absolute rounded-full mix-blend-screen"
                          style={{
                            left: `${h.x - h.r}%`,
                            top: `${h.y - h.r}%`,
                            width: `${h.r * 2}%`,
                            height: `${h.r * 2}%`,
                            background: `radial-gradient(circle, rgba(239,68,68,${h.intensity}) 0%, rgba(234,179,8,${h.intensity * 0.6}) 40%, transparent 70%)`,
                            filter: "blur(6px)",
                          }}
                        />
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          </CardContent>
        </Card>

        <div className="space-y-4">
          {imaging.suppressed ? (
            <Card className="border-[var(--color-severity-high)]/30 bg-[var(--color-severity-high-soft)]">
              <CardContent className="p-5">
                <div className="flex items-start gap-3">
                  <ShieldAlert className="h-5 w-5 text-[var(--color-severity-high)]" />
                  <div>
                    <p className="font-medium">Confidence suppressed</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Imaging unavailable. The interpretation panel will activate once a study is
                      uploaded.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold">Pneumonia probability</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-end justify-between">
                  <p className="font-display text-4xl font-semibold tabular-nums">{prob}%</p>
                  <AIConfidenceBadge level={imaging.aiConfidence} />
                </div>
                <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full bg-[var(--color-severity-moderate)]"
                    style={{ width: `${prob}%` }}
                  />
                </div>
                <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
                  Assistive estimate from a single imaging model. Confidence is decoupled from
                  probability.
                </p>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold">AI evidence interpretation</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed text-muted-foreground">
                {imaging.interpretation}
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
