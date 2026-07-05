import { createFileRoute } from "@tanstack/react-router";
import { CommandCenterView } from "@/components/command-center-view";

export const Route = createFileRoute("/_app/command-center")({
  head: () => ({
    meta: [
      { title: "ED Command Center — PRATHAM" },
      { name: "description", content: "Emergency Department Active Cases & Smart Triage Queue." },
    ],
  }),
  component: CommandCenterPage,
});

function CommandCenterPage() {
  return <CommandCenterView />;
}
