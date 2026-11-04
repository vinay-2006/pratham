import { Outlet, useNavigate } from "@tanstack/react-router";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { TopBar } from "@/components/top-bar";
import { useEffect } from "react";
import { ROLE_HOME, canAccess, useAuth } from "@/lib/auth";
import { useRouterState } from "@tanstack/react-router";

export function AppShell() {
  const navigate = useNavigate();
  const { user, ready } = useAuth();
  const pathname = useRouterState({ select: (st) => st.location.pathname });

  // Gate: not signed in → /login; signed in but page not allowed for this role → role home.
  useEffect(() => {
    if (!ready) return;
    if (!user) navigate({ to: "/login" });
    else if (!canAccess(user.role, pathname)) navigate({ to: ROLE_HOME[user.role] });
  }, [ready, user, pathname, navigate]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      if (
        tag === "INPUT" ||
        tag === "TEXTAREA" ||
        tag === "SELECT" ||
        (e.target as HTMLElement)?.isContentEditable
      ) {
        return;
      }
      if (e.key === "p" || e.key === "P" || e.key === "Escape") {
        e.preventDefault();
        navigate({ to: "/" });
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [navigate]);

  if (!ready || !user || !canAccess(user.role, pathname)) {
    return <div className="flex min-h-dvh items-center justify-center text-sm text-muted-foreground">Loading…</div>;
  }

  return (
    <SidebarProvider>
      <div className="flex min-h-dvh w-full bg-background">
        <AppSidebar />
        <SidebarInset className="min-w-0">
          <TopBar />
          <div className="flex-1">
            <Outlet />
          </div>
        </SidebarInset>
      </div>
    </SidebarProvider>
  );
}
