import { UserRound } from "lucide-react";
import { SeverityBadge } from "@/components/severity-badge";
import { PatientStatusChip } from "@/components/status-pipeline";
import { Button } from "@/components/ui/button";
import type { QueuePatient } from "@/lib/mock-data";

export function PatientQueueRow({ p }: { p: QueuePatient }) {
  return (
    <li className="flex flex-wrap items-center gap-3 px-4 py-3 md:flex-nowrap">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-muted">
        <UserRound className="h-4 w-4 text-muted-foreground" />
      </div>
      <div className="min-w-[140px] flex-1">
        <p className="text-sm font-medium">
          {p.name} <span className="text-muted-foreground">· {p.age}{p.sex}</span>
        </p>
        <p className="text-[11px] text-muted-foreground">{p.symptoms.join(", ")}</p>
      </div>
      <div className="hidden text-xs text-muted-foreground sm:block sm:w-20">{p.bed}</div>
      <div className="hidden text-xs text-muted-foreground sm:block sm:w-16">{p.eta}</div>
      <SeverityBadge severity={p.severity}>{p.severity}</SeverityBadge>
      <PatientStatusChip status={p.status} />
      <Button
        size="sm"
        variant="outline"
        className="ml-auto"
        disabled
      >
        Open
      </Button>
    </li>
  );
}

