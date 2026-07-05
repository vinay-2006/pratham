import { Link, useRouterState } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  Ambulance,
  Bell,
  BookOpen,
  Brain,
  ClipboardCheck,
  ClipboardList,
  FileImage,
  FileText,
  FlaskConical,
  GitCompare,
  Layers,
  LayoutDashboard,
  Search,
  ShieldAlert,
  Stethoscope,
  Users,
} from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { useCase } from "@/lib/case-store";
import { fetchQueueStats } from "@/lib/patient-queue-api";

interface NavItem {
  title: string;
  url: string;
  icon: typeof Users;
  badgeKey?: "pending" | "queue";
}

interface NavGroup {
  label: string;
  items: NavItem[];
}

const nurseGroups: NavGroup[] = [
  {
    label: "Nurse station",
    items: [
      { title: "Dashboard", url: "/nurse/dashboard", icon: LayoutDashboard },
      { title: "Emergency Intake", url: "/nurse/intake", icon: Ambulance },
      { title: "Patient Queue", url: "/nurse/queue", icon: Users, badgeKey: "queue" },
      { title: "Investigations", url: "/investigations", icon: ClipboardList },
    ],
  },
  {
    label: "Hospital Platform",
    items: [
      { title: "AI Copilot", url: "/copilot", icon: Brain },
      { title: "ED Command Center", url: "/command-center", icon: Activity },
      { title: "Clinical Search", url: "/search", icon: Search },
      { title: "Admin Telemetry", url: "/admin", icon: LayoutDashboard },
    ],
  },
];

const doctorGroups: NavGroup[] = [
  {
    label: "Doctor workstation",
    items: [
      { title: "Dashboard", url: "/doctor/dashboard", icon: LayoutDashboard },
      { title: "Approvals", url: "/doctor/approvals", icon: ClipboardCheck, badgeKey: "pending" },
      { title: "Patient Queue", url: "/nurse/queue", icon: Users, badgeKey: "queue" },
      { title: "Patient Review", url: "/doctor/review", icon: Stethoscope },
      { title: "Clinical Report", url: "/doctor/report/latest", icon: FileText },
    ],
  },
  {
    label: "Clinical intelligence",
    items: [
      { title: "Operational Risk", url: "/dashboard", icon: Bell },
      { title: "AI Copilot", url: "/copilot", icon: Brain },
      { title: "Imaging Analysis", url: "/imaging", icon: FileImage },
      { title: "Differential", url: "/differential", icon: FlaskConical },
      { title: "Explainability", url: "/explainability", icon: Brain },
      { title: "Confidence", url: "/confidence", icon: ShieldAlert },
    ],
  },
  {
    label: "Hospital Platform",
    items: [
      { title: "ED Command Center", url: "/command-center", icon: Activity },
      { title: "Case Comparison", url: "/comparison", icon: GitCompare },
      { title: "Clinical Search", url: "/search", icon: Search },
      { title: "Knowledge Base", url: "/knowledge", icon: BookOpen },
      { title: "Architecture", url: "/architecture", icon: Layers },
      { title: "Admin Telemetry", url: "/admin", icon: LayoutDashboard },
    ],
  },
];

const showcaseGroup: NavGroup = {
  label: "Showcase & Portfolio",
  items: [
    { title: "SaaS Landing Page", url: "/", icon: Activity },
    { title: "Knowledge Base", url: "/knowledge", icon: BookOpen },
    { title: "Architecture", url: "/architecture", icon: Layers },
    { title: "Admin Telemetry", url: "/admin", icon: LayoutDashboard },
  ],
};

export function AppSidebar() {
  const { role, pendingCount } = useCase();
  const currentPath = useRouterState({ select: (s) => s.location.pathname });
  const isActive = (p: string) => currentPath === p;
  const groups = [...(role === "doctor" ? doctorGroups : nurseGroups), showcaseGroup];

  // Lightweight queue stats for sidebar badge
  const { data: queueStats } = useQuery({
    queryKey: ["queue-stats"],
    queryFn: fetchQueueStats,
    refetchInterval: 30_000,
    staleTime: 15_000,
  });

  const queueBadgeCount = queueStats?.pending_approval_patients ?? 0;

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <Link to="/" className="flex items-center gap-2 px-2 py-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Activity className="h-4 w-4" />
          </div>
          <div className="flex flex-col leading-tight group-data-[collapsible=icon]:hidden">
            <span className="font-display text-sm font-semibold tracking-tight">PRATHAM</span>
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
              {role === "doctor" ? "Doctor view" : "Nurse view"}
            </span>
          </div>
        </Link>
      </SidebarHeader>
      <SidebarContent>
        {groups.map((g) => (
          <SidebarGroup key={g.label}>
            <SidebarGroupLabel>{g.label}</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {g.items.map((item) => {
                  // Determine badge value
                  let badgeValue = 0;
                  if (item.badgeKey === "pending") badgeValue = pendingCount;
                  if (item.badgeKey === "queue") badgeValue = queueBadgeCount;
                  const showBadge = badgeValue > 0;

                  return (
                    <SidebarMenuItem key={item.url}>
                      <SidebarMenuButton asChild isActive={isActive(item.url)} tooltip={item.title}>
                        <Link to={item.url} className="flex items-center gap-2">
                          <item.icon className="h-4 w-4" />
                          <span className="flex-1">{item.title}</span>
                          {showBadge && (
                            <span className="ml-auto inline-flex items-center gap-1 rounded-full bg-amber-500 px-1.5 py-0.5 text-[10px] font-bold text-white group-data-[collapsible=icon]:hidden">
                              <span className="inline-block h-1.5 w-1.5 rounded-full bg-white/80" />
                              {badgeValue}
                            </span>
                          )}
                        </Link>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  );
                })}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>
      <SidebarFooter>
        <div className="px-3 py-2 text-[10px] leading-snug text-muted-foreground group-data-[collapsible=icon]:hidden">
          Prototype — not for clinical use.
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
