import { ChevronDown, FileText } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import type { EvidencePiece } from "@/lib/mock-data";
import { SeverityBadge } from "@/components/severity-badge";

export function EvidenceCard({ evidence }: { evidence: EvidencePiece }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded-lg border bg-card">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left"
        aria-expanded={open}
      >
        <div className="flex min-w-0 items-start gap-3">
          <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-muted">
            <FileText className="h-3.5 w-3.5 text-muted-foreground" />
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-medium">{evidence.label}</p>
            <p className="truncate text-xs text-muted-foreground">{evidence.finding}</p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <SeverityBadge severity={evidence.weight}>{evidence.weight}</SeverityBadge>
          <ChevronDown
            className={cn("h-4 w-4 text-muted-foreground transition-transform", open && "rotate-180")}
          />
        </div>
      </button>

      {open && (
        <div className="space-y-3 border-t bg-muted/30 px-4 py-3">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              Contribution
            </p>
            <p className="mt-1 text-sm leading-relaxed">{evidence.contribution}</p>
          </div>
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              Provenance
            </p>
            <p className="mt-1 font-mono text-xs text-muted-foreground">{evidence.source}</p>
          </div>
        </div>
      )}
    </div>
  );
}
