import { createFileRoute } from "@tanstack/react-router";
import { AdminDashboard } from "@/components/admin-dashboard";

export const Route = createFileRoute("/_app/admin")({
  head: () => ({
    meta: [
      { title: "Admin Telemetry — PRATHAM" },
      { name: "description", content: "PRATHAM System Telemetry & Operational Health Dashboard." },
    ],
  }),
  component: AdminPage,
});

function AdminPage() {
  return <AdminDashboard />;
}
