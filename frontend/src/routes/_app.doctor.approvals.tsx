import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/_app/doctor/approvals")({
  beforeLoad: () => {
    throw redirect({ to: "/doctor/review" });
  },
  component: () => null,
});
