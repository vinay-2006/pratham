import { createFileRoute } from "@tanstack/react-router";
import { useState, useMemo, useRef } from "react";
import { useNavigate } from "@tanstack/react-router";
import { Ambulance, Send } from "lucide-react";
import axios from "axios";
import { useCase } from "@/lib/case-store";
import { SectionHeader } from "@/components/section-header";
import { SeverityBadge } from "@/components/severity-badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { MockUploadDropzone } from "@/components/mock-upload-dropzone";
import { toast } from "sonner";

export const Route = createFileRoute("/_app/nurse/intake")({
  head: () => ({
    meta: [
      { title: "Emergency Intake — PRATHAM" },
      { name: "description", content: "Capture vitals, symptoms, and ambulance context." },
    ],
  }),
  component: NurseIntakePage,
});

const API_BASE = "http://localhost:8000/api";

const SYMPTOMS = [
  "Chest Pain",
  "Breathlessness",
  "Trauma",
  "Bleeding",
  "Unconsciousness",
  "Neurological Symptoms",
];

/** Map display symptom labels → API field names */
const SYMPTOM_FIELD_MAP: Record<string, string> = {
  "Chest Pain": "chest_pain",
  "Breathlessness": "breathlessness",
  "Trauma": "trauma",
  "Bleeding": "bleeding",
  "Unconsciousness": "unconsciousness",
  "Neurological Symptoms": "neurological_symptoms",
};

function NurseIntakePage() {
  const { patientCase, pushNotification, loadIntake } = useCase();
  const navigate = useNavigate();

  // Controlled patient fields
  const [name, setName] = useState("");
  const [age, setAge] = useState("");
  const [sex, setSex] = useState<"M" | "F">("M");
  // Controlled vitals
  const [hr, setHr] = useState("");
  const [spo2, setSpo2] = useState("");
  const [bp, setBp] = useState("");
  // Scenario / description
  const [scenario, setScenario] = useState("");
  // Symptoms
  const [selected, setSelected] = useState<string[]>([]);
  // Loading state
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Refs for uncontrolled fields (respiratory rate, temperature, ETA)
  const rrRef = useRef<HTMLInputElement>(null);
  const tempRef = useRef<HTMLInputElement>(null);
  const etaRef = useRef<HTMLInputElement>(null);

  const severity = useMemo(() => {
    const count = selected.length;
    const lowSpo2 = Number(spo2) > 0 && Number(spo2) < 90;
    if (selected.includes("Unconsciousness") || lowSpo2) return "critical" as const;
    if (count >= 2) return "high" as const;
    if (count === 1) return "moderate" as const;
    return "low" as const;
  }, [selected, spo2]);

  const recommended = useMemo(() => {
    const recs: string[] = [];
    if (selected.includes("Chest Pain")) recs.push("ECG", "Troponin");
    if (selected.includes("Breathlessness")) recs.push("Chest X-ray", "ABG");
    if (selected.includes("Trauma") || selected.includes("Bleeding")) recs.push("FAST scan", "CBC");
    if (selected.includes("Unconsciousness") || selected.includes("Neurological Symptoms"))
      recs.push("CT Brain");
    if (!recs.includes("CBC")) recs.push("CBC");
    return Array.from(new Set(recs));
  }, [selected]);

  const toggle = (s: string) =>
    setSelected((curr) => (curr.includes(s) ? curr.filter((x) => x !== s) : [...curr, s]));

  /** Parse "120/80" → { systolic: 120, diastolic: 80 } */
  const parseBP = (raw: string) => {
    const parts = raw.split("/");
    return {
      bp_systolic: parts[0] ? parseInt(parts[0], 10) || null : null,
      bp_diastolic: parts[1] ? parseInt(parts[1], 10) || null : null,
    };
  };

  /** Split "First Last" → { first_name, last_name } */
  const parseName = (full: string) => {
    const parts = full.trim().split(/\s+/);
    const first_name = parts[0] ?? "";
    const last_name = parts.slice(1).join(" ") || (parts[0] ?? "");
    return { first_name, last_name };
  };

  const submit = async () => {
    setIsSubmitting(true);
    try {
      const { first_name, last_name } = parseName(name);
      const { bp_systolic, bp_diastolic } = parseBP(bp);

      // Build symptoms object — all false by default, set true for selected
      const symptomsPayload = Object.fromEntries(
        Object.values(SYMPTOM_FIELD_MAP).map((key) => [key, false])
      ) as Record<string, boolean>;
      for (const label of selected) {
        const field = SYMPTOM_FIELD_MAP[label];
        if (field) symptomsPayload[field] = true;
      }

      const response = await axios.post(`${API_BASE}/intake`, {
        patient: {
          first_name,
          last_name,
          date_of_birth: age,
          gender: sex === "M" ? "male" : "female",
          contact_number: null,
          allergies: [],
          current_medications: [],
          past_medical_history: [],
        },
        vitals: {
          heart_rate: parseInt(hr, 10) || null,
          spo2: parseFloat(spo2) || null,
          bp_systolic,
          bp_diastolic,
          temperature: parseFloat(tempRef.current?.value ?? "") || null,
          respiratory_rate: parseInt(rrRef.current?.value ?? "", 10) || null,
        },
        symptoms: symptomsPayload,
        ambulance_eta: parseInt(etaRef.current?.value ?? "", 10) || null,
        emergency_description: scenario || null,
        chief_complaint: scenario ? scenario.split(".")[0] : null,
      });

      // Persist IDs for downstream pipeline steps
      localStorage.setItem("current_intake_id", response.data.intake_id);
      localStorage.setItem("current_patient_id", response.data.patient_id);
      await loadIntake(response.data.intake_id);

      // Also update local case store so the rest of the UI has context
      pushNotification({
        intake_id: response.data.intake_id,
        patientName: name,
        age: Number(age) || 0,
        sex,
        severity,
        symptoms: selected,
        vitalsSummary: `HR ${hr || "—"} · SpO₂ ${spo2 ? `${spo2}%` : "—"} · BP ${bp || "—"}`,
        recommendedInvestigations: recommended,
        urgency: severity === "critical" ? "Critical" : severity === "high" ? "Urgent" : "Routine",
      });

      toast.success("Intake submitted", {
        description: `Patient registered (ID: ${response.data.patient_id.slice(0, 8)}…). Doctor notified.`,
      });

      navigate({ to: "/nurse/dashboard" });
    } catch (error) {
      console.error("Intake submission failed:", error);
      toast.error("Submission failed", {
        description: axios.isAxiosError(error)
          ? error.response?.data?.detail ?? error.message
          : "An unexpected error occurred. Please try again.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-5 py-8 md:px-8">
      <SectionHeader
        eyebrow="Stage 1 · Intake"
        title="Emergency Intake"
        description="Captured by the nurse on arrival or in-transit. On submit, the system generates the operational risk analysis and forwards the recommended investigations to the on-call doctor for approval."
      />

      <div className="mt-8 grid gap-6 lg:grid-cols-[1fr_340px]">
        <div className="space-y-6">
          <Card>
            <CardHeader><CardTitle className="text-base">Patient information</CardTitle></CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-2">
              <Field label="Full name" value={name} onChange={setName} />
              <Field label="Age" value={age} onChange={setAge} />
              <div className="space-y-1.5">
                <Label className="text-xs">Sex</Label>
                <div className="flex gap-2">
                  {(["M", "F"] as const).map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => setSex(s)}
                      className={
                        "h-10 flex-1 rounded-md border text-sm transition-colors " +
                        (sex === s ? "border-primary bg-primary/5" : "hover:bg-muted/50")
                      }
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
              <Field label="Ambulance / ETA (mins)" defaultValue="" ref={etaRef} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle className="text-base">Vitals</CardTitle></CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <Field label="Heart Rate (bpm)" value={hr} onChange={setHr} />
              <Field label="SpO₂ (%)" value={spo2} onChange={setSpo2} />
              <Field label="Blood Pressure" value={bp} onChange={setBp} />
              <Field label="Respiratory Rate" defaultValue="" ref={rrRef} />
              <Field label="Temperature (°C)" defaultValue="" ref={tempRef} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle className="text-base">Symptoms</CardTitle></CardHeader>
            <CardContent>
              <div className="grid gap-2 sm:grid-cols-2 md:grid-cols-3">
                {SYMPTOMS.map((s) => {
                  const checked = selected.includes(s);
                  return (
                    <label
                      key={s}
                      className={
                        "flex cursor-pointer items-center gap-2 rounded-md border p-3 text-sm transition-colors " +
                        (checked ? "border-primary bg-primary/5" : "hover:bg-muted/50")
                      }
                    >
                      <Checkbox checked={checked} onCheckedChange={() => toggle(s)} />
                      <span>{s}</span>
                    </label>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle className="text-base">Emergency scenario</CardTitle></CardHeader>
            <CardContent>
              <Textarea
                rows={5}
                value={scenario}
                onChange={(e) => setScenario(e.target.value)}
                placeholder="Patient unconscious after road accident with breathing difficulty…"
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle className="text-base">Upload evidence (optional)</CardTitle></CardHeader>
            <CardContent>
              <MockUploadDropzone label="Evidence" hint="X-ray, ECG, labs, or notes" />
            </CardContent>
          </Card>
        </div>

        <aside className="lg:sticky lg:top-20 lg:self-start">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-sm">
                <Ambulance className="h-4 w-4 text-primary" />
                System preview
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-lg border bg-muted/30 p-4">
                <p className="text-[11px] uppercase tracking-wider text-muted-foreground">
                  Derived severity
                </p>
                <div className="mt-2 flex items-center justify-between">
                  <SeverityBadge severity={severity}>{severity}</SeverityBadge>
                  <span className="text-xs text-muted-foreground">
                    {selected.length} symptom{selected.length === 1 ? "" : "s"}
                  </span>
                </div>
              </div>

              <div className="rounded-lg border p-4">
                <p className="text-[11px] uppercase tracking-wider text-muted-foreground">
                  Will be sent to doctor
                </p>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {recommended.map((r) => (
                    <span key={r} className="rounded border bg-background px-2 py-0.5 text-xs">
                      {r}
                    </span>
                  ))}
                </div>
              </div>

              <Button className="w-full" size="lg" onClick={submit} disabled={isSubmitting}>
                <Send className="mr-2 h-4 w-4" />
                {isSubmitting ? "Submitting…" : "Submit intake"}
              </Button>

              <p className="text-[11px] leading-relaxed text-muted-foreground">
                On submit, the system creates a doctor notification with vitals, symptoms, severity,
                and recommended investigations. No staff member forwards it manually.
              </p>
            </CardContent>
          </Card>
        </aside>
      </div>
    </div>
  );
}

import { forwardRef } from "react";

const Field = forwardRef<
  HTMLInputElement,
  {
    label: string;
    defaultValue?: string;
    value?: string;
    onChange?: (v: string) => void;
  }
>(function Field({ label, defaultValue, value, onChange }, ref) {
  return (
    <div className="space-y-1.5">
      <Label className="text-xs">{label}</Label>
      {onChange ? (
        <Input ref={ref} value={value} onChange={(e) => onChange(e.target.value)} />
      ) : (
        <Input ref={ref} defaultValue={defaultValue} />
      )}
    </div>
  );
});
