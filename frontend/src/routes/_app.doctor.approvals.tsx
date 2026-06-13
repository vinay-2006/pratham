import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useCase } from "@/lib/case-store";
import { SectionHeader } from "@/components/section-header";
import { NotificationCard } from "@/components/notification-card";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_app/doctor/approvals")({
  head: () => ({
    meta: [
      { title: "Investigation Approvals — PRATHAM" },
      { name: "description", content: "Review and approve system-generated investigation requests." },
    ],
  }),
  component: ApprovalsPage,
});

const FILTERS = ["All", "Pending Approval", "Approved", "Rejected", "Needs Info"] as const;
type Filter = (typeof FILTERS)[number];

function ApprovalsPage() {
  const { notifications, isLoadingNotifications, refreshNotifications } = useCase();
  const [filter, setFilter] = useState<Filter>("Pending Approval");

  const filtered =
    filter === "All" ? notifications : notifications.filter((n) => n.status === filter);

  return (
    <div className="mx-auto max-w-5xl px-5 py-8 md:px-8">
      <SectionHeader
        eyebrow="Doctor workstation"
        title="Investigation Approvals"
        description="System-generated requests. Each request includes patient context, severity, and the recommended investigation set."
      />

      <div className="mt-6 flex flex-wrap items-center gap-2">
        {FILTERS.map((f) => {
          const count = f === "All" ? notifications.length : notifications.filter((n) => n.status === f).length;
          return (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={cn(
                "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
                filter === f ? "border-primary bg-primary/10 text-primary" : "hover:bg-muted",
              )}
            >
              {f} <span className="ml-1 text-muted-foreground">· {count}</span>
            </button>
          );
        })}

        {/* Refresh button */}
        <button
          onClick={() => refreshNotifications()}
          className="ml-auto rounded-full border px-3 py-1 text-xs font-medium text-muted-foreground hover:bg-muted transition-colors"
        >
          ↻ Refresh
        </button>
      </div>

      <div className="mt-6 space-y-3">
        {isLoadingNotifications ? (
          <Card>
            <CardContent className="flex items-center justify-center gap-2 p-8 text-sm text-muted-foreground">
              <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Loading pending approvals from database…
            </CardContent>
          </Card>
        ) : filtered.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center text-sm text-muted-foreground">
              {notifications.length === 0
                ? "No pending investigation requests in the database."
                : "Nothing here."}
            </CardContent>
          </Card>
        ) : (
          filtered.map((n) => <NotificationCard key={n.id} n={n} />)
        )}
      </div>
    </div>
  );
}
