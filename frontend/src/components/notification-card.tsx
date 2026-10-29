import { useState, useRef, useCallback } from "react";
import { Check, HelpCircle, X, Clock, Plus, ChevronRight, AlertTriangle, FileText, RefreshCw } from "lucide-react";
import { Link } from "@tanstack/react-router";
import axios from "axios";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { SeverityBadge } from "@/components/severity-badge";
import { cn } from "@/lib/utils";
import { useCase } from "@/lib/case-store";
import type { DoctorNotification } from "@/lib/mock-data";

import { toast } from "sonner";

import { API_BASE } from "@/lib/api-config";
import { apiErrorMessage } from "@/lib/api-error";

// ─── Styles ───────────────────────────────────────────────────────────────────

const urgencyStyles: Record<DoctorNotification["urgency"], string> = {
  Critical: "border-l-[var(--color-severity-critical)]",
  Urgent:   "border-l-[var(--color-severity-high)]",
  Routine:  "border-l-[var(--color-severity-moderate)]",
};

const urgencyBarStyles: Record<DoctorNotification["urgency"], string> = {
  Critical: "bg-[var(--color-severity-critical)]",
  Urgent:   "bg-[var(--color-severity-high)]",
  Routine:  "bg-[var(--color-severity-moderate)]",
};

const statusBadge: Record<DoctorNotification["status"], string> = {
  "Pending Approval": "bg-muted text-muted-foreground",
  Approved:    "bg-[var(--color-severity-low-soft)] text-[var(--color-severity-low)]",
  Rejected:    "bg-[var(--color-severity-critical-soft)] text-[var(--color-severity-critical)]",
  "Needs Info": "bg-[var(--color-severity-moderate-soft)] text-[color-mix(in_oklab,var(--color-severity-moderate)_55%,black)] dark:text-[var(--color-severity-moderate)]",
};

const riskBadgeStyles: Record<DoctorNotification["urgency"], string> = {
  Critical: "bg-red-500/15 text-red-500 border border-red-500/30",
  Urgent:   "bg-orange-500/15 text-orange-400 border border-orange-500/30",
  Routine:  "bg-yellow-500/15 text-yellow-500 border border-yellow-500/30",
};

const ALL_SYMPTOMS = [
  "Chest Pain",
  "Breathlessness",
  "Trauma",
  "Bleeding",
  "Unconsciousness",
  "Neurological Symptoms",
];

// ─── Helpers ──────────────────────────────────────────────────────────────────

function timeAgo(ts: string): string {
  const [h, m] = ts.split(":").map(Number);
  const now = new Date();
  const then = new Date();
  then.setHours(h, m, 0, 0);
  const diffMin = Math.max(0, Math.round((now.getTime() - then.getTime()) / 60000));
  if (diffMin < 1) return "just now";
  if (diffMin === 1) return "1 min ago";
  return `${diffMin} min ago`;
}

// ─── Vitals chip ──────────────────────────────────────────────────────────────

function VitalChip({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border bg-muted/30 px-3 py-2 text-center">
      <p className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</p>
      <p className="mt-0.5 font-mono text-sm font-semibold">{value || "—"}</p>
    </div>
  );
}

function Section({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="mb-5">
      <p className="mb-2 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
        {label}
      </p>
      <div className="space-y-1">{children}</div>
    </div>
  );
}
