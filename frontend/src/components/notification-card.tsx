import { useState, useRef, useCallback } from "react";
import { Check, HelpCircle, X, Clock, Plus, ChevronRight, AlertTriangle } from "lucide-react";
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

const API_BASE = "http://localhost:8000/api";

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

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-4 border-b border-border/30 py-1 last:border-0">
      <span className="text-xs text-muted-foreground shrink-0">{label}</span>
      <span className="text-xs text-right">{value || "—"}</span>
    </div>
  );
}

// ─── Investigation checklist (used both in card and modal) ────────────────────

interface ChecklistProps {
  investigations: string[];
  intakeId: string;
  notificationId: string;
  patientName: string;
  onApprove: () => void;
  onClose?: () => void;
  submitRef?: React.MutableRefObject<() => void>;
  /** When true, renders the full Approve + Reject + Request buttons */
  showActions?: boolean;
}

function InvestigationChecklist({
  investigations,
  intakeId,
  notificationId,
  patientName,
  onApprove,
  onClose,
  submitRef,
  showActions = false,
}: ChecklistProps) {
  const { rejectNotification, requestInfoNotification, refreshNotifications } = useCase();
  const [checked, setChecked] = useState<Record<string, boolean>>(
    () => Object.fromEntries(investigations.map((inv) => [inv, true]))
  );
  const [customTests, setCustomTests] = useState<string[]>([]);
  const [customInput, setCustomInput] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const toggleCheck = (key: string) =>
    setChecked((prev) => ({ ...prev, [key]: !prev[key] }));

  const addCustom = () => {
    const val = customInput.trim();
    if (!val) return;
    if (checked[val] !== undefined || customTests.includes(val)) {
      toast.error("Test already in list");
      return;
    }
    setCustomTests((prev) => [...prev, val]);
    setChecked((prev) => ({ ...prev, [val]: true }));
    setCustomInput("");
    inputRef.current?.focus();
  };

  const handleSubmit = useCallback(async () => {
    const approvedTests = investigations.filter((inv) => checked[inv]);
    const approvedCustom = customTests.filter((t) => checked[t]);
    const payload = {
      intake_id: intakeId,
      approved_tests: approvedTests,
      custom_tests: approvedCustom,
      doctor_notes: "",
    };
    try {
      await axios.post(`${API_BASE}/investigations/approve`, payload);
      toast.success("Investigations approved", {
        description: `${patientName} · ${approvedTests.length + approvedCustom.length} order(s) released.`,
      });
      onApprove();
      onClose?.();
      // Refresh from DB so approved items leave the pending queue
      refreshNotifications();
    } catch (error) {
      console.error("[PRATHAM] Approval failed:", error);
      toast.error("Approval failed", {
        description: axios.isAxiosError(error)
          ? error.response?.data?.detail ?? error.message
          : "Unexpected error — please retry.",
      });
    }
  }, [checked, customTests, investigations, intakeId, patientName, onApprove, onClose, refreshNotifications]);

  // Expose submit to parent card button via ref
  if (submitRef) submitRef.current = handleSubmit;

  const allTests = [...investigations, ...customTests];

  return (
    <div>
      {/* Test list */}
      <div className="space-y-1.5 rounded-md border bg-muted/20 p-3">
        <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
          Investigations — check to approve
        </p>
        {allTests.map((inv) => (
          <label
            key={inv}
            className="flex cursor-pointer items-center gap-2.5 rounded px-1 py-1 text-sm hover:bg-muted/40 select-none"
          >
            <Checkbox
              id={`chk-${notificationId}-${inv}`}
              checked={!!checked[inv]}
              onCheckedChange={() => toggleCheck(inv)}
            />
            <span className={cn(!checked[inv] && "text-muted-foreground line-through")}>
              {inv}
              {customTests.includes(inv) && (
                <span className="ml-1.5 rounded bg-primary/15 px-1 py-0.5 text-[9px] font-medium text-primary">
                  custom
                </span>
              )}
            </span>
          </label>
        ))}
      </div>

      {/* Add custom test */}
      <div className="mt-3 flex gap-2">
        <Input
          ref={inputRef}
          value={customInput}
          onChange={(e) => setCustomInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && addCustom()}
          placeholder="Add custom test — e.g. D-Dimer, MRI Brain"
          className="h-8 text-xs"
        />
        <Button size="sm" variant="outline" className="h-8 shrink-0 px-3 text-xs" onClick={addCustom}>
          <Plus className="mr-1 h-3 w-3" /> Add
        </Button>
      </div>

      {/* Action buttons (shown inside modal) */}
      {showActions && (
        <div className="mt-4 flex flex-wrap gap-2 border-t border-border/40 pt-4">
          <Button className="flex-1" onClick={handleSubmit}>
            <Check className="mr-1.5 h-4 w-4" />
            Approve ({allTests.filter((t) => checked[t]).length} tests)
          </Button>
          <Button
            variant="outline"
            onClick={async () => {
              try {
                await axios.post(`${API_BASE}/investigations/reject`, { intake_id: intakeId });
                toast.success("Investigations rejected", { description: patientName });
                rejectNotification(notificationId);
                onClose?.();
                refreshNotifications();
              } catch (error) {
                console.error("[PRATHAM] Rejection failed:", error);
                toast.error("Rejection failed", {
                  description: axios.isAxiosError(error)
                    ? error.response?.data?.detail ?? error.message
                    : "Unexpected error — please retry.",
                });
              }
            }}
          >
            <X className="mr-1.5 h-4 w-4" />
            Reject
          </Button>
          <Button
            variant="ghost"
            onClick={async () => {
              try {
                await axios.post(`${API_BASE}/investigations/needs-info`, { intake_id: intakeId });
                requestInfoNotification(notificationId);
                toast.success("More info requested", { description: patientName });
                onClose?.();
                refreshNotifications();
              } catch (error) {
                console.error("[PRATHAM] Needs info request failed:", error);
                toast.error("Request failed");
              }
            }}
          >
            <HelpCircle className="mr-1.5 h-4 w-4" />
            Request info
          </Button>
        </div>
      )}
    </div>
  );
}

// ─── Patient detail dialog (centered, scrollable) ─────────────────────────────

function PatientDetailDialog({
  n,
  open,
  onOpenChange,
  onApprove,
}: {
  n: DoctorNotification;
  open: boolean;
  onOpenChange: (v: boolean) => void;
  onApprove: () => void;
}) {
  const vitals = n.vitals ? {
    heartRate: n.vitals.heartRate,
    spo2: n.vitals.spo2,
    bloodPressure: n.vitals.bloodPressure,
    respiratoryRate: n.vitals.respiratoryRate,
    temperature: n.vitals.temperature,
  } : null;
  const bpParts = vitals?.bloodPressure ? vitals.bloodPressure.split("/") : [];
  const bpSys = bpParts[0] ?? "—";
  const bpDia = bpParts[1] ?? "—";
  const pending = n.status === "Pending Approval";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="!flex !flex-col gap-0 p-0 sm:max-w-2xl w-full overflow-hidden max-h-[90vh]"
      >
        {/* Urgency colour bar */}
        <div className={cn("h-1 w-full rounded-t-lg shrink-0", urgencyBarStyles[n.urgency])} />

        {/* Fixed header */}
        <DialogHeader className="shrink-0 px-6 pt-5 pb-4 border-b border-border/50">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <SeverityBadge severity={n.severity}>{n.urgency}</SeverityBadge>
            <span className={cn("rounded-md px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider", statusBadge[n.status])}>
              {n.status}
            </span>
          </div>
          <DialogTitle className="text-xl">{n.patientName}</DialogTitle>
          <DialogDescription>
            {n.age}y · {n.sex === "M" ? "Male" : "Female"} · Arrived {n.timestamp} · {timeAgo(n.timestamp)}
          </DialogDescription>
        </DialogHeader>

        {/* Scrollable body */}
        <div className="flex-1 overflow-y-auto min-h-0">
          <div className="px-6 py-5">

            {/* PATIENT INFO */}
            <Section label="Patient Info">
              <Row label="Full name" value={n.patientName} />
              <Row label="Age" value={`${n.age} years`} />
              <Row label="Gender" value={n.sex === "M" ? "Male" : "Female"} />
              <Row label="Date of birth" value="—" />
              <Row label="Contact" value="—" />
            </Section>

            {/* EMERGENCY CONTEXT */}
            <Section label="Emergency Context">
              <Row label="Chief complaint" value={n.symptoms.join(", ")} />
              <Row label="Ambulance ETA" value={"—"} />
              {n.emergencyDescription && (
                <div className="mt-2">
                  <p className="text-[11px] text-muted-foreground mb-1">Emergency description</p>
                  <p className="text-sm leading-relaxed rounded-md border bg-muted/20 p-3">
                    {n.emergencyDescription}
                  </p>
                </div>
              )}
            </Section>

            {/* VITALS */}
            <Section label="Vitals">
              <div className="grid grid-cols-3 gap-2">
                <VitalChip
                  label="Heart Rate"
                  value={vitals?.heartRate ? `${vitals.heartRate} bpm` : (n.vitalsSummary.match(/HR (\S+)/)?.[1] ?? "—")}
                />
                <VitalChip
                  label="SpO₂"
                  value={vitals?.spo2 ? `${vitals.spo2}%` : (n.vitalsSummary.match(/SpO₂ (\S+)/)?.[1] ?? "—")}
                />
                <VitalChip label="BP Systolic"   value={vitals?.bloodPressure && bpSys !== "—" ? `${bpSys} mmHg` : "—"} />
                <VitalChip label="BP Diastolic"  value={vitals?.bloodPressure && bpDia !== "—" ? `${bpDia} mmHg` : "—"} />
                <VitalChip label="Temperature"   value={vitals?.temperature ? `${vitals.temperature} °C` : "—"} />
                <VitalChip label="Resp Rate"     value={vitals?.respiratoryRate ? `${vitals.respiratoryRate}/min` : "—"} />
              </div>
            </Section>

            {/* SYMPTOMS */}
            <Section label="Symptoms">
              <div className="flex flex-wrap gap-1.5">
                {ALL_SYMPTOMS.map((s) => {
                  const active = n.symptoms.includes(s);
                  return (
                    <span
                      key={s}
                      className={cn(
                        "rounded-full border px-2.5 py-1 text-xs font-medium",
                        active
                          ? "border-primary bg-primary/10 text-primary"
                          : "border-border bg-muted/20 text-muted-foreground line-through"
                      )}
                    >
                      {s}
                    </span>
                  );
                })}
              </div>
            </Section>

            {/* CLINICAL FLAGS */}
            <Section label="Clinical Flags">
              <div className="grid grid-cols-2 gap-1.5">
                {ALL_SYMPTOMS.map((s) => {
                  const active = n.symptoms.includes(s);
                  return (
                    <div
                      key={s}
                      className={cn(
                        "flex items-center gap-2 rounded-md border px-2.5 py-1.5 text-xs",
                        active
                          ? "border-red-500/40 bg-red-500/10 text-red-400"
                          : "border-border text-muted-foreground"
                      )}
                    >
                      {active
                        ? <AlertTriangle className="h-3 w-3 shrink-0 text-red-400" />
                        : <span className="h-3 w-3 shrink-0 rounded-full border border-muted-foreground/30" />}
                      {s}
                    </div>
                  );
                })}
              </div>
            </Section>

            {/* INVESTIGATIONS + APPROVE (pending only) */}
            {pending && (
              <Section label="Investigation Approval">
                <InvestigationChecklist
                  investigations={n.recommendedInvestigations}
                  intakeId={n.intake_id}
                  notificationId={n.id}
                  patientName={n.patientName}
                  onApprove={onApprove}
                  onClose={() => onOpenChange(false)}
                  showActions
                />
              </Section>
            )}

            {/* Read-only pills for approved/rejected cards */}
            {!pending && (
              <Section label="Investigations">
                <div className="flex flex-wrap gap-1.5">
                  {n.recommendedInvestigations.map((inv) => (
                    <span key={inv} className="rounded-md border bg-background px-2 py-1 text-xs font-medium">
                      {inv}
                    </span>
                  ))}
                </div>
              </Section>
            )}

          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ─── Main card ────────────────────────────────────────────────────────────────

export function NotificationCard({ n }: { n: DoctorNotification }) {
  const { approveNotification, rejectNotification, requestInfoNotification, refreshNotifications } = useCase();
  const [dialogOpen, setDialogOpen] = useState(false);
  const submitRef = useRef<() => void>(() => {});
  const pending = n.status === "Pending Approval";

  const hasEvidence = false;
  const evidenceLabel = "No evidence yet";
  const descSnippet = n.emergencyDescription
    ? n.emergencyDescription.length > 80
      ? n.emergencyDescription.slice(0, 80) + "…"
      : n.emergencyDescription
    : null;

  return (
    <>
      {/* ── Card (click anywhere except buttons → open modal) ── */}
      <Card
        className={cn("overflow-hidden border-l-4 cursor-pointer hover:shadow-md", urgencyStyles[n.urgency])}
        onClick={() => setDialogOpen(true)}
      >
        <CardContent className="p-5">
          {/* Header */}
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <p className="font-display text-base font-semibold">
                  {n.patientName}
                  <span className="ml-2 text-sm font-normal text-muted-foreground">· {n.age}{n.sex}</span>
                </p>
                <span className={cn("rounded-md px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider", riskBadgeStyles[n.urgency])}>
                  {n.urgency}
                </span>
                <span className={cn("inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider", statusBadge[n.status])}>
                  {n.status}
                </span>
              </div>
              <p className="mt-1.5 text-xs text-muted-foreground">
                Symptoms: <span className="text-foreground">{n.symptoms.join(", ")}</span>
              </p>
              <p className="mt-0.5 text-xs text-muted-foreground">
                Vitals: <span className="font-mono text-foreground">{n.vitalsSummary}</span>
              </p>
              {descSnippet && (
                <p className="mt-1 text-[11px] italic text-muted-foreground leading-snug">{descSnippet}</p>
              )}
            </div>

            <div className="flex flex-col items-end gap-1 shrink-0">
              <div className="flex items-center gap-1 text-[11px] text-muted-foreground">
                <Clock className="h-3 w-3" />
                <span className="font-mono">{n.timestamp}</span>
                <span className="text-muted-foreground/60">·</span>
                <span>{timeAgo(n.timestamp)}</span>
              </div>
              <span className={cn("rounded px-1.5 py-0.5 text-[10px]", hasEvidence ? "bg-blue-500/10 text-blue-400" : "bg-muted/50 text-muted-foreground")}>
                {evidenceLabel}
              </span>
              <span className="flex items-center gap-0.5 text-[10px] text-muted-foreground/50">
                View details <ChevronRight className="h-3 w-3" />
              </span>
            </div>
          </div>

          {/* Investigation checklist on card (pending only) */}
          {pending && (
            <div onClick={(e) => e.stopPropagation()}>
              <InvestigationChecklist
                investigations={n.recommendedInvestigations}
                intakeId={n.intake_id}
                notificationId={n.id}
                patientName={n.patientName}
                onApprove={() => approveNotification(n.id)}
                submitRef={submitRef}
                showActions={false}
              />
            </div>
          )}

          {/* Pills for non-pending */}
          {!pending && (
            <div className="mt-4 rounded-md border bg-muted/30 p-3">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                System-recommended investigations
              </p>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {n.recommendedInvestigations.map((inv) => (
                  <span key={inv} className="rounded-md border bg-background px-2 py-1 text-xs font-medium">{inv}</span>
                ))}
              </div>
            </div>
          )}

          {/* Card action buttons */}
          {pending && (
            <div className="mt-4 flex flex-wrap items-center gap-2" onClick={(e) => e.stopPropagation()}>
              <Button size="sm" onClick={(e) => { e.stopPropagation(); submitRef.current(); }}>
                <Check className="mr-1.5 h-3.5 w-3.5" /> Submit Approval
              </Button>
              <Button size="sm" variant="outline" onClick={async (e) => { e.stopPropagation(); try { await axios.post(`${API_BASE}/investigations/reject`, { intake_id: n.intake_id }); rejectNotification(n.id); toast.success("Request rejected", { description: n.patientName }); refreshNotifications(); } catch (error) { console.error("[PRATHAM] Card rejection failed:", error); toast.error("Rejection failed", { description: axios.isAxiosError(error) ? error.response?.data?.detail ?? error.message : "Unexpected error — please retry." }); } }}>
                <X className="mr-1.5 h-3.5 w-3.5" /> Reject
              </Button>
              <Button size="sm" variant="ghost" onClick={async (e) => { e.stopPropagation(); try { await axios.post(`${API_BASE}/investigations/needs-info`, { intake_id: n.intake_id }); requestInfoNotification(n.id); toast.success("More info requested", { description: n.patientName }); refreshNotifications(); } catch (error) { console.error("[PRATHAM] Needs info request failed:", error); toast.error("Request failed"); } }}>
                <HelpCircle className="mr-1.5 h-3.5 w-3.5" /> Request more info
              </Button>
            </div>
          )}

          {!pending && (
            <div className="mt-4 space-y-1">
              {n.audit?.reviewedBy && (
                <p className="text-[11px] text-muted-foreground">
                  <span className="font-medium text-foreground">{n.status}</span> by {n.audit.reviewedBy}
                  {n.audit.reviewedAt && (
                    <span> · {new Date(n.audit.reviewedAt).toLocaleString()}</span>
                  )}
                </p>
              )}
              {n.audit?.reviewNotes && (
                <p className="text-[11px] italic text-muted-foreground">Notes: {n.audit.reviewNotes}</p>
              )}
              {!n.audit?.reviewedBy && (
                <p className="text-[11px] text-muted-foreground">
                  System-generated · No nurse manually forwarded this request.
                </p>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Centered patient detail dialog */}
      <PatientDetailDialog
        n={n}
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onApprove={() => approveNotification(n.id)}
      />
    </>
  );
}
