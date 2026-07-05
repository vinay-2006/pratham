import { createFileRoute } from "@tanstack/react-router";
import { InteractiveArchitectureExplorer } from "@/components/interactive-architecture-explorer";

export const Route = createFileRoute("/_app/architecture")({
  head: () => ({
    meta: [
      { title: "Architecture Explorer — PRATHAM" },
      { name: "description", content: "Interactive 7-Layer Clinical AI Pipeline Architecture Explorer." },
    ],
  }),
  component: ArchitecturePage,
});

function ArchitecturePage() {
  return <InteractiveArchitectureExplorer />;
}
