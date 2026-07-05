import { createFileRoute } from "@tanstack/react-router";
import { ExplainabilityExplorer } from "@/components/explainability-explorer";

export const Route = createFileRoute("/_app/explainability")({
  head: () => ({
    meta: [
      { title: "Explainability Explorer — PRATHAM" },
      { name: "description", content: "Contributing evidence, provenance, rule agreement matrix, and uncertainty for every diagnostic estimate." },
    ],
  }),
  component: ExplainabilityPage,
});

function ExplainabilityPage() {
  return <ExplainabilityExplorer />;
}
