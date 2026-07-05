import { createFileRoute } from "@tanstack/react-router";
import Landing from "../components/landing";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "PRATHAM — AI-Assisted Emergency Coordination & Clinical Intelligence" },
      {
        name: "description",
        content:
          "PRATHAM helps emergency teams prepare faster, prioritize better, and understand clinical situations under pressure.",
      },
    ],
  }),
  component: Landing,
});
