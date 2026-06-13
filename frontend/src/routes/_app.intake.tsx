import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/_app/intake")({
  beforeLoad: () => {
    throw redirect({ to: "/nurse/intake" });
  },
});
