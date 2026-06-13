import { Link, useRouterState } from "@tanstack/react-router";
import {
  Activity,
  Ambulance,
  Bell,
  Brain,
  ClipboardCheck,
  ClipboardList,
  FileImage,
  FlaskConical,
  LayoutDashboard,
  ShieldAlert,
  Stethoscope,
  Upload,
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

const nurseGroups = [
  {
    label: "Nurse station",
    items: [
      { title: "Dashboard", url: "/nurse/dashboard", icon: LayoutDashboard },
      { title: "Emergency Intake", url: "/nurse/intake", icon: Ambulance },
      { title: "Patient Queue", url: "/nurse/queue", icon: Users },
      { title: "Evidence Upload", url: "/evidence", icon: Upload },
      { title: "Investigations", url: "/investigations", icon: ClipboardList },
    ],
  },
];

const doctorGroups = [
  {
    label: "Doctor workstation",
    items: [
      { title: "Dashboard", url: "/doctor/dashboard", icon: LayoutDashboard },
      { title: "Approvals", url: "/doctor/approvals", icon: ClipboardCheck, badgeKey: "pending" as const },
      { title: "Patient Review", url: "/doctor/review", icon: Stethoscope },
    ],
  },
  {
    label: "Clinical intelligence",
    items: [
      { title: "Operational Risk", url: "/dashboard", icon: Bell },
      { title: "Imaging Analysis", url: "/imaging", icon: FileImage },
      { title: "Differential", url: "/differential", icon: FlaskConical },
      { title: "Explainability", url: "/explainability", icon: Brain },
      { title: "Confidence", url: "/confidence", icon: ShieldAlert },
    ],
  },
];

export function AppSidebar() {
  const { role, pendingCount } = useCase();
  const currentPath = useRouterState({ select: (s) => s.location.pathname });
  const isActive = (p: string) => currentPath === p;
  const groups = role === "doctor" ? doctorGroups : nurseGroups;

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
                  const showBadge =
                    "badgeKey" in item && item.badgeKey === "pending" && pendingCount > 0;
                  return (
                    <SidebarMenuItem key={item.url}>
                      <SidebarMenuButton asChild isActive={isActive(item.url)} tooltip={item.title}>
                        <Link to={item.url} className="flex items-center gap-2">
                          <item.icon className="h-4 w-4" />
                          <span className="flex-1">{item.title}</span>
                          {showBadge && (
                            <span className="ml-auto rounded-full bg-primary px-1.5 py-0.5 text-[10px] font-semibold text-primary-foreground group-data-[collapsible=icon]:hidden">
                              {pendingCount}
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
