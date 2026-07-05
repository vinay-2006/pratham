import { createFileRoute } from "@tanstack/react-router";
import { CaseComparisonExplorer } from "@/components/case-comparison-explorer";

export const Route = createFileRoute("/_app/comparison")({
  head: () => ({
    meta: [
      { title: "Case Comparison Explorer — PRATHAM" },
      { name: "description", content: "Side-by-side multi-visit patient trajectory delta viewer." },
    ],
  }),
  component: ComparisonPage,
});

function ComparisonPage() {
  return <CaseComparisonExplorer />;
}
