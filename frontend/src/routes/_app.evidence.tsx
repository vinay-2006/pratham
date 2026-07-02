import { createFileRoute, redirect } from "@tanstack/react-router";

// Evidence uploads now live inside the Patient Queue workspace.
// This route redirects any bookmarks or old links gracefully.
export const Route = createFileRoute("/_app/evidence")({
  beforeLoad: () => {
    throw redirect({ to: "/nurse/queue", replace: true });
  },
  component: () => null,
});
