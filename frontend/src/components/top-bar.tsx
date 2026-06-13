import { Bell, Moon, Siren, Sun, UserRound } from "lucide-react";
import { Link, useNavigate } from "@tanstack/react-router";
import { useCase, type Role } from "@/lib/case-store";
import { Button } from "@/components/ui/button";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import { EvidenceCompletenessPill } from "@/components/evidence-completeness-pill";
import { cn } from "@/lib/utils";

export function TopBar() {
  const navigate = useNavigate();
  const {
    patientCase,
    theme,
    toggleTheme,
    role,
    setRole,
    pendingCount,
    activeEmergencyCount,
  } = useCase();

  const handleRoleChange = (newRole: Role) => {
    setRole(newRole);
    if (newRole === "nurse") {
      navigate({ to: "/nurse/dashboard" });
    } else {
      navigate({ to: "/doctor/dashboard" });
    }
  };

  return (
    <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b bg-background/85 px-3 backdrop-blur md:px-5">
      <SidebarTrigger />
      <Separator orientation="vertical" className="h-6" />

      <RoleSwitcher role={role} onChange={handleRoleChange} />

      <Separator orientation="vertical" className="hidden h-6 md:block" />

      {patientCase ? (
        <div className="hidden items-center gap-2 md:flex">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-muted">
            <UserRound className="h-3.5 w-3.5 text-muted-foreground" />
          </div>
          <div className="flex flex-col leading-tight">
            <span className="text-xs font-medium">
              {patientCase.patient.name} · {patientCase.patient.age}{patientCase.patient.sex}
            </span>
            <span className="text-[10px] text-muted-foreground">
              Arrival {patientCase.patient.arrival} · ETA {patientCase.patient.eta}
            </span>
          </div>
        </div>
      ) : (
        <div className="hidden items-center gap-2 md:flex">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-muted">
            <UserRound className="h-3.5 w-3.5 text-muted-foreground" />
          </div>
          <span className="text-xs text-muted-foreground">No patient selected</span>
        </div>
      )}

      <div className="ml-auto flex items-center gap-2">
        <Counter
          icon={Siren}
          label="Active"
          value={activeEmergencyCount}
          tone="high"
        />
        <Link
          to={role === "doctor" ? "/doctor/approvals" : "/nurse/dashboard"}
          className="hidden sm:block"
        >
          <Counter icon={Bell} label="Pending" value={pendingCount} tone="primary" />
        </Link>

        {patientCase && <EvidenceCompletenessPill level={patientCase.evidenceCompleteness} />}

        <Button
          variant="ghost"
          size="icon"
          aria-label="Toggle theme"
          onClick={toggleTheme}
          className="h-8 w-8"
        >
          {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </Button>
      </div>
    </header>
  );
}

function RoleSwitcher({ role, onChange }: { role: Role; onChange: (r: Role) => void }) {
  return (
    <div className="inline-flex items-center rounded-md border bg-card p-0.5 text-xs">
      {(["nurse", "doctor"] as const).map((r) => (
        <button
          key={r}
          onClick={() => onChange(r)}
          className={cn(
            "rounded-[5px] px-2.5 py-1 font-medium capitalize transition-colors",
            role === r
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:text-foreground",
          )}
        >
          {r}
        </button>
      ))}
    </div>
  );
}

function Counter({
  icon: Icon,
  label,
  value,
  tone,
}: {
  icon: typeof Bell;
  label: string;
  value: number;
  tone: "primary" | "high";
}) {
  const toneCls =
    tone === "high"
      ? "text-[var(--color-severity-high)] bg-[var(--color-severity-high-soft)] border-[var(--color-severity-high)]/30"
      : "text-primary bg-primary/10 border-primary/30";
  return (
    <div
      className={cn(
        "hidden items-center gap-1.5 rounded-md border px-2 py-1 text-[11px] font-medium md:inline-flex",
        toneCls,
      )}
      title={`${label}: ${value}`}
    >
      <Icon className="h-3.5 w-3.5" />
      <span className="uppercase tracking-wider">{label}</span>
      <span className="tabular-nums font-semibold">{value}</span>
    </div>
  );
}
