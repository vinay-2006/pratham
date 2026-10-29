import { createFileRoute } from "@tanstack/react-router";
import { useState, useMemo, useEffect } from "react";
import { useNavigate } from "@tanstack/react-router";
import { Ambulance, Send, ShieldCheck, AlertCircle } from "lucide-react";
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
import { toast } from "sonner";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_app/nurse/intake")({
  head: () => ({
    meta: [
      { title: "Emergency Intake — PRATHAM" },
      { name: "description", content: "Capture vitals, symptoms, and ambulance context." },
    ],
  }),
  component: NurseIntakePage,
});

import { API_BASE } from "@/lib/api-config";

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

// Draft recovery helper functions with SSR safety and 24-hour expiration check
const getDraftValue = (key: string, defaultValue: string): string => {
  if (typeof window === "undefined" || typeof localStorage === "undefined") {
    return defaultValue;
  }
  const savedAt = localStorage.getItem("intake_saved_at");
  if (savedAt) {
    const elapsed = Date.now() - parseInt(savedAt, 10);
    if (elapsed > 24 * 60 * 60 * 1000) {
      return defaultValue;
    }
  }
  return localStorage.getItem(key) ?? defaultValue;
};

const getDraftJSON = (key: string, defaultValue: any): any => {
  if (typeof window === "undefined" || typeof localStorage === "undefined") {
    return defaultValue;
  }
  const savedAt = localStorage.getItem("intake_saved_at");
  if (savedAt) {
    const elapsed = Date.now() - parseInt(savedAt, 10);
    if (elapsed > 24 * 60 * 60 * 1000) {
      return defaultValue;
    }
  }
  try {
    const saved = localStorage.getItem(key);
    return saved ? JSON.parse(saved) : defaultValue;
  } catch {
    return defaultValue;
  }
};

// ── Strict Clinical Validators ──────────────────────────────────────────────
// Each returns an error string if invalid, or null if valid.
// Empty strings are not validated here (handled by "Required" logic).

function validateAge(v: string): string | null {
  if (!v.trim()) return null;
  if (!/^\d+$/.test(v.trim())) return "Must be a whole number";
  const n = parseInt(v, 10);
  if (n < 0 || n > 120) return "Range: 0–120";
  return null;
}

function validateHR(v: string): string | null {
  if (!v.trim()) return null;
  if (!/^\d+$/.test(v.trim())) return "Must be a whole number";
  const n = parseInt(v, 10);
  if (n < 20 || n > 250) return "Range: 20–250 bpm";
  return null;
}

function validateSpO2(v: string): string | null {
  if (!v.trim()) return null;
  if (!/^\d+$/.test(v.trim())) return "Must be a whole number";
  const n = parseInt(v, 10);
  if (n < 0 || n > 100) return "Range: 0–100%";
  return null;
}

function validateRR(v: string): string | null {
  if (!v.trim()) return null;
  if (!/^\d+$/.test(v.trim())) return "Must be a whole number";
  const n = parseInt(v, 10);
  if (n < 5 || n > 60) return "Range: 5–60 breaths/min";
  return null;
}

function validateTemp(v: string): string | null {
  if (!v.trim()) return null;
  if (!/^\d+(\.\d+)?$/.test(v.trim())) return "Must be a number (e.g. 36.8)";
  const n = parseFloat(v);
  if (n < 30 || n > 45) return "Range: 30–45 °C";
  return null;
}

function validateBP(v: string): string | null {
  if (!v.trim()) return null;
  const match = v.trim().match(/^(\d+)\/(\d+)$/);
  if (!match) return "Format: systolic/diastolic (e.g. 120/80)";
  const sys = parseInt(match[1], 10);
  const dia = parseInt(match[2], 10);
  if (sys < 50 || sys > 300) return "Systolic range: 50–300";
  if (dia < 20 || dia > 200) return "Diastolic range: 20–200";
  if (dia >= sys) return "Diastolic must be less than systolic";
  return null;
}

function NurseIntakePage() {
  const { loadIntake, pushNotification } = useCase();
  const navigate = useNavigate();

  // Controlled patient fields
  const [name, setName] = useState(() => getDraftValue("intake_name", ""));
  const [age, setAge] = useState(() => getDraftValue("intake_age", ""));
  const [sex, setSex] = useState<"M" | "F">(
    () => (getDraftValue("intake_sex", "M") as "M" | "F") ?? "M"
  );
  const [arrivalType, setArrivalType] = useState(() => getDraftValue("intake_arrival_type", "walk_in"));
  const [eta, setEta] = useState(() => getDraftValue("intake_eta", ""));

  // Controlled vitals
  const [hr, setHr] = useState(() => getDraftValue("intake_hr", ""));
  const [spo2, setSpo2] = useState(() => getDraftValue("intake_spo2", ""));
  const [bp, setBp] = useState(() => getDraftValue("intake_bp", ""));
  const [rr, setRr] = useState(() => getDraftValue("intake_rr", ""));
  const [temp, setTemp] = useState(() => getDraftValue("intake_temp", ""));

  // Scenario / description
  const [scenario, setScenario] = useState(() => getDraftValue("intake_scenario", ""));
  // Symptoms
  const [selected, setSelected] = useState<string[]>(() => getDraftJSON("intake_selected", []));
  // Routine Screening Mode
  const [isRoutine, setIsRoutine] = useState(() => getDraftValue("intake_is_routine", "false") === "true");

  // Loading state
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Strict clinical validation errors (null = valid, string = error message)
  const ageError = useMemo(() => validateAge(age), [age]);
  const hrError = useMemo(() => validateHR(hr), [hr]);
  const spo2Error = useMemo(() => validateSpO2(spo2), [spo2]);
  const rrError = useMemo(() => validateRR(rr), [rr]);
  const tempError = useMemo(() => validateTemp(temp), [temp]);
  const bpError = useMemo(() => validateBP(bp), [bp]);

  // Autosave Draft effect
  useEffect(() => {
    if (typeof window === "undefined" || typeof localStorage === "undefined") {
      return;
    }
    localStorage.setItem("intake_name", name);
    localStorage.setItem("intake_age", age);
    localStorage.setItem("intake_sex", sex);
    localStorage.setItem("intake_arrival_type", arrivalType);
    localStorage.setItem("intake_eta", eta);
    localStorage.setItem("intake_hr", hr);
    localStorage.setItem("intake_spo2", spo2);
    localStorage.setItem("intake_bp", bp);
    localStorage.setItem("intake_rr", rr);
    localStorage.setItem("intake_temp", temp);
    localStorage.setItem("intake_scenario", scenario);
    localStorage.setItem("intake_selected", JSON.stringify(selected));
    localStorage.setItem("intake_is_routine", String(isRoutine));
    localStorage.setItem("intake_saved_at", String(Date.now()));
  }, [name, age, sex, arrivalType, eta, hr, spo2, bp, rr, temp, scenario, selected, isRoutine]);

  const clearAutosave = () => {
    if (typeof window === "undefined" || typeof localStorage === "undefined") {
      return;
    }
    const keys = [
      "intake_name", "intake_age", "intake_sex", "intake_arrival_type", "intake_eta",
      "intake_hr", "intake_spo2", "intake_bp", "intake_rr", "intake_temp",
      "intake_scenario", "intake_selected", "intake_is_routine", "intake_saved_at"
    ];
    keys.forEach(key => localStorage.removeItem(key));
  };

  // Real-time Operational Triage Status
  const realtimeTriage = useMemo(() => {
    const heartRate = parseInt(hr, 10);
    const oxygen = parseFloat(spo2);
    const respRate = parseInt(rr, 10);
    const temperature = parseFloat(temp);
    
    const bpParts = bp.split("/");
    const systolic = bpParts[0] ? parseInt(bpParts[0], 10) : NaN;

    // High Risk / Immediate Attention triggers:
    const isImmediate =
      (!isNaN(oxygen) && oxygen < 90) ||
      (!isNaN(heartRate) && (heartRate > 150 || heartRate < 50)) ||
      (!isNaN(respRate) && (respRate > 25 || respRate < 10)) ||
      (!isNaN(temperature) && (temperature > 38.5 || temperature < 35.5)) ||
      (!isNaN(systolic) && (systolic >= 160 || systolic < 90)) ||
      selected.includes("Unconsciousness") ||
      selected.includes("Chest Pain") ||
      selected.includes("Neurological Symptoms");

    if (isImmediate) {
      return {
        label: "Immediate Attention",
        emoji: "🔴",
        color: "red",
        severity: "critical" as const,
      };
    }

    // Moderate Risk / Requires Review triggers:
    const isRequiresReview =
      (!isNaN(oxygen) && oxygen >= 90 && oxygen <= 94) ||
      (!isNaN(heartRate) && ((heartRate >= 101 && heartRate <= 150) || (heartRate >= 50 && heartRate <= 59))) ||
      (!isNaN(respRate) && ((respRate >= 21 && respRate <= 25) || (respRate >= 10 && respRate <= 11))) ||
      (!isNaN(temperature) && ((temperature >= 37.6 && temperature <= 38.5) || (temperature >= 35.5 && temperature <= 36.4))) ||
      (!isNaN(systolic) && ((systolic >= 140 && systolic <= 159) || (systolic >= 90 && systolic <= 99))) ||
      selected.length > 0;

    if (isRequiresReview) {
      return {
        label: "Requires Review",
        emoji: "🟡",
        color: "orange",
        severity: "moderate" as const,
      };
    }

    return {
      label: "Stable",
      emoji: "🟢",
      color: "green",
      severity: "low" as const,
    };
  }, [hr, spo2, rr, temp, bp, selected]);

  // Map operational triage colors to the four severity levels needed for the backend
  const severity = useMemo(() => {
    if (realtimeTriage.color === "red") {
      const lowSpo2 = Number(spo2) > 0 && Number(spo2) < 90;
      if (selected.includes("Unconsciousness") || lowSpo2) return "critical" as const;
      return "high" as const;
    }
    if (realtimeTriage.color === "orange") return "moderate" as const;
    return "low" as const;
  }, [realtimeTriage, selected, spo2]);

  // Operational Alert Shortcut
  const showCriticalAlert = useMemo(() => {
    const heartRate = parseInt(hr, 10);
    const oxygen = parseFloat(spo2);
    return (!isNaN(oxygen) && oxygen < 85) || (!isNaN(heartRate) && heartRate > 160);
  }, [hr, spo2]);

  // Validation checklists
  const missingFields = useMemo(() => {
    const list: string[] = [];
    if (!name.trim()) list.push("Full Name");
    if (!age.trim()) list.push("Age");
    else if (ageError) list.push(`Age (${ageError})`);
    if (!sex) list.push("Gender");
    if (!hr.trim()) list.push("Heart Rate");
    else if (hrError) list.push(`Heart Rate (${hrError})`);
    if (!bp.trim()) list.push("Blood Pressure");
    else if (bpError) list.push(`Blood Pressure (${bpError})`);
    if (!spo2.trim()) list.push("SpO₂");
    else if (spo2Error) list.push(`SpO₂ (${spo2Error})`);
    if (!rr.trim()) list.push("Respiratory Rate");
    else if (rrError) list.push(`Respiratory Rate (${rrError})`);
    if (!temp.trim()) list.push("Temperature");
    else if (tempError) list.push(`Temperature (${tempError})`);
    if (arrivalType === "ambulance" && !eta.trim()) list.push("ETA");
    return list;
  }, [name, age, sex, hr, bp, spo2, rr, temp, arrivalType, eta, ageError, hrError, bpError, spo2Error, rrError, tempError]);

  const hasAnyValidationError = !!(ageError || hrError || spo2Error || rrError || tempError || bpError);
  const isFormValid = useMemo(() => missingFields.length === 0 && !hasAnyValidationError, [missingFields, hasAnyValidationError]);

  // Patient Readiness Panel Completion Metrics
  // Invalid entries do NOT count toward readiness — only valid values contribute.
  const readinessPanel = useMemo(() => {
    const ageValid = age.trim() !== "" && !ageError;
    const hrValid = hr.trim() !== "" && !hrError;
    const bpValid = bp.trim() !== "" && !bpError;
    const spo2Valid = spo2.trim() !== "" && !spo2Error;
    const rrValid = rr.trim() !== "" && !rrError;
    const tempValid = temp.trim() !== "" && !tempError;

    const hasDemo = name.trim() !== "" && ageValid;
    const hasVitals = hrValid && bpValid && spo2Valid && rrValid && tempValid;
    const hasMode = isRoutine || selected.length > 0;

    let score = 0;
    if (name.trim()) score += 15;
    if (ageValid) score += 15;
    if (hrValid) score += 10;
    if (bpValid) score += 10;
    if (spo2Valid) score += 10;
    if (rrValid) score += 10;
    if (tempValid) score += 10;
    if (hasMode) score += 20;

    return {
      hasDemo,
      hasVitals,
      hasMode,
      score,
    };
  }, [name, age, hr, bp, spo2, rr, temp, isRoutine, selected, ageError, hrError, bpError, spo2Error, rrError, tempError]);

  const recommended = useMemo(() => {
    // If routine mode is active, hide emergency tests and show routine checklist
    if (isRoutine) {
      return ["Routine Blood Panel", "Chest X-ray (optional)", "ECG (optional)"];
    }
    const recs: string[] = [];
    if (selected.includes("Chest Pain")) recs.push("ECG", "Troponin");
    if (selected.includes("Breathlessness")) recs.push("Chest X-ray", "ABG");
    if (selected.includes("Trauma") || selected.includes("Bleeding")) recs.push("FAST scan", "CBC");
    if (selected.includes("Unconsciousness") || selected.includes("Neurological Symptoms"))
      recs.push("CT Brain");
    if (!recs.includes("CBC")) recs.push("CBC");
    return Array.from(new Set(recs));
  }, [selected, isRoutine]);

  const toggle = (s: string) => {
    setIsRoutine(false);
    setSelected((curr) => (curr.includes(s) ? curr.filter((x) => x !== s) : [...curr, s]));
  };

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
    const last_name = parts.slice(1).join(" ");
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
          temperature: parseFloat(temp) || null,
          respiratory_rate: parseInt(rr, 10) || null,
        },
        symptoms: symptomsPayload,
        ambulance_eta: arrivalType === "ambulance" ? parseInt(eta, 10) || null : null,
        emergency_description: scenario || null,
        chief_complaint: scenario ? scenario.split(".")[0] : null,
      });

      // Persist IDs for downstream pipeline steps
      localStorage.setItem("current_intake_id", response.data.intake_id);
      localStorage.setItem("current_patient_id", response.data.patient_id);

      // Force immediate reload of case store
      const caseStore = (window as any).__case_store_instance;
      if (caseStore && typeof caseStore.loadIntake === "function") {
        await caseStore.loadIntake(response.data.intake_id);
      } else {
        await loadIntake(response.data.intake_id);
      }

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

      clearAutosave();
      navigate({ to: "/nurse/dashboard" });
    } catch (error) {
      console.error("Intake submission failed:", error);
      toast.error("Submission failed", {
        description: axios.isAxiosError(error)
          ? apiErrorMessage(error)
          : "An unexpected error occurred. Please try again.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmitClick = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isFormValid) {
      toast.error("Please complete all mandatory triage observations before submitting.");
      return;
    }
    submit();
  };

  return (
    <div className="mx-auto max-w-7xl px-5 py-8 md:px-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <SectionHeader
          eyebrow="Stage 1 · Intake"
          title="Emergency Intake"
          description="Captured by the nurse on arrival or in-transit. On submit, the system generates the operational risk analysis and forwards the recommended investigations to the on-call doctor for approval."
        />
        {isRoutine && (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-100 px-3 py-1 text-xs font-semibold text-blue-800 dark:bg-blue-900/30 dark:text-blue-400 border border-blue-200">
            Routine Screening Mode
          </span>
        )}
      </div>

      <div className="mt-8">
        {/* Missing Observations Banner */}
        {missingFields.length > 0 && (
          <div className="mb-6 rounded-lg border border-amber-300 bg-amber-50 p-4 dark:border-amber-900/50 dark:bg-amber-950/20 animate-fade-in">
            <p className="text-xs font-bold text-amber-800 dark:text-amber-400 uppercase tracking-wider">
              Missing Observations
            </p>
            <ul className="mt-2 grid grid-cols-2 sm:grid-cols-4 gap-x-4 gap-y-1 text-xs text-amber-700 dark:text-amber-300 font-semibold list-inside list-disc">
              {missingFields.map((field) => (
                <li key={field}>{field}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
          <div className="space-y-6">
            <Card>
              <CardHeader><CardTitle className="text-base">Patient information</CardTitle></CardHeader>
              <CardContent className="grid gap-4 sm:grid-cols-2">
                <Field
                  label="Full name"
                  value={name}
                  onChange={setName}
                  required
                  showError
                  placeholder="e.g. John Doe"
                />
                <Field
                  label="Age"
                  value={age}
                  onChange={setAge}
                  required
                  showError
                  placeholder="e.g. 42"
                  helperText="Example: 42 years"
                  validationError={ageError}
                />
                
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <Label className="text-xs font-semibold">
                      Sex <span className="text-destructive font-bold">*</span>
                    </Label>
                  </div>
                  <div className="flex gap-2">
                    {(["M", "F"] as const).map((s) => (
                      <button
                        key={s}
                        type="button"
                        onClick={() => setSex(s)}
                        className={
                          "h-10 flex-1 rounded-md border text-sm font-semibold transition-colors " +
                          (sex === s ? "border-primary bg-primary/5 text-primary animate-fade-in" : "hover:bg-muted/50")
                        }
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="space-y-1.5 sm:col-span-2">
                  <Label className="text-xs font-semibold">Arrival Type</Label>
                  <div className="flex gap-2">
                    {(["walk_in", "ambulance", "referral"] as const).map((type) => (
                      <button
                        key={type}
                        type="button"
                        onClick={() => setArrivalType(type)}
                        className={cn(
                          "h-10 flex-1 rounded-md border text-sm font-semibold transition-colors capitalize",
                          arrivalType === type ? "border-primary bg-primary/5 text-primary" : "hover:bg-muted/50"
                        )}
                      >
                        {type.replace("_", " ")}
                      </button>
                    ))}
                  </div>
                </div>

                {arrivalType === "ambulance" && (
                  <div className="sm:col-span-2 animate-fade-in">
                    <Field
                      label="Ambulance / ETA (mins)"
                      value={eta}
                      onChange={setEta}
                      required
                      showError
                      placeholder="e.g. 10"
                      helperText="Example: 10 minutes"
                    />
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle className="text-base">Vitals</CardTitle></CardHeader>
              <CardContent className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                <Field
                  label="Heart Rate (bpm)"
                  value={hr}
                  onChange={setHr}
                  required
                  showError
                  placeholder="e.g. 72"
                  helperText="Normal: 60–100 bpm"
                  validationError={hrError}
                />
                <Field
                  label="SpO₂ (%)"
                  value={spo2}
                  onChange={setSpo2}
                  required
                  showError
                  placeholder="e.g. 98"
                  helperText="Normal: 95–100%"
                  validationError={spo2Error}
                />
                <Field
                  label="Blood Pressure"
                  value={bp}
                  onChange={setBp}
                  required
                  showError
                  placeholder="e.g. 120/80"
                  helperText="Example: 120/80 mmHg"
                  validationError={bpError}
                />
                <Field
                  label="Respiratory Rate"
                  value={rr}
                  onChange={setRr}
                  required
                  showError
                  placeholder="e.g. 16"
                  helperText="Normal: 12–20 breaths/min"
                  validationError={rrError}
                />
                <Field
                  label="Temperature (°C)"
                  value={temp}
                  onChange={setTemp}
                  required
                  showError
                  placeholder="e.g. 36.8"
                  helperText="Normal: 36.5–37.5 °C"
                  validationError={tempError}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-base">Symptoms</CardTitle>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setSelected([]);
                    setIsRoutine(false);
                  }}
                  className={cn(
                    "h-8 text-xs font-semibold gap-1.5 transition-all",
                    selected.length === 0 && !isRoutine
                      ? "border-emerald-500 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 hover:text-emerald-800 dark:border-emerald-600 dark:bg-emerald-950/30 dark:text-emerald-400"
                      : "text-muted-foreground"
                  )}
                >
                  <ShieldCheck className="h-3.5 w-3.5" />
                  No Symptoms
                </Button>
              </CardHeader>
              <CardContent>
                {/* Routine Screening Mode Selector */}
                <div className="mb-5">
                  <label
                    className={cn(
                      "flex cursor-pointer items-center gap-3 rounded-md border-2 p-3.5 text-sm font-semibold transition-all shadow-sm",
                      isRoutine
                        ? "border-blue-500 bg-blue-50/50 text-blue-800 dark:border-blue-600 dark:bg-blue-950/20 dark:text-blue-300"
                        : "border-slate-200 dark:border-slate-800 hover:bg-muted/50"
                    )}
                  >
                    <Checkbox
                      checked={isRoutine}
                      onCheckedChange={(checked) => {
                        setIsRoutine(!!checked);
                        if (checked) {
                          setSelected([]);
                        }
                      }}
                      className={isRoutine ? "border-blue-600 text-blue-600 focus-visible:ring-blue-600" : ""}
                    />
                    <div className="flex flex-col">
                      <span className="flex items-center gap-1.5 text-slate-800 dark:text-gray-200">
                        🩺 Routine Health Check-up
                      </span>
                      <span className="text-[11px] text-muted-foreground font-normal mt-0.5">
                        Check this box to switch intake into routine screening mode. This automatically clears emergency symptoms.
                      </span>
                    </div>
                  </label>
                </div>

                <div className="mb-2.5">
                  <p className="text-[11px] uppercase tracking-wider text-muted-foreground font-bold font-semibold">
                    Emergency Symptoms
                  </p>
                </div>

                <div className="grid gap-2 sm:grid-cols-2 md:grid-cols-3">
                  {SYMPTOMS.map((s) => {
                    const checked = selected.includes(s);
                    return (
                      <label
                        key={s}
                        className={
                          "flex cursor-pointer items-center gap-2 rounded-md border p-3 text-sm transition-colors " +
                          (checked ? "border-primary bg-primary/5 font-medium" : "hover:bg-muted/50")
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
          </div>

          <aside className="lg:sticky lg:top-20 lg:self-start space-y-4">
            {/* Patient Triage Readiness Panel */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs uppercase tracking-wider text-muted-foreground font-bold">
                  Patient Triage Readiness
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-1.5 text-xs">
                  <div className="flex items-center justify-between font-semibold">
                    <span>Demographics</span>
                    <span className={readinessPanel.hasDemo ? "text-emerald-600 font-bold" : "text-destructive font-bold"}>
                      {readinessPanel.hasDemo ? "✅ Complete" : "❌ Incomplete"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between font-semibold">
                    <span>Vitals</span>
                    <span className={readinessPanel.hasVitals ? "text-emerald-600 font-bold" : "text-amber-600 font-bold"}>
                      {readinessPanel.hasVitals ? "✅ Complete" : "⚠ Incomplete"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between font-semibold">
                    <span>Triage Mode / Symptoms</span>
                    <span className={readinessPanel.hasMode ? "text-emerald-600 font-bold" : "text-amber-600 font-bold"}>
                      {readinessPanel.hasMode ? "✅ Set" : "⚠ Missing"}
                    </span>
                  </div>
                </div>

                <div className="pt-2 border-t">
                  <div className="flex justify-between items-center text-xs font-bold mb-1">
                    <span>Overall Readiness</span>
                    <span className={cn(
                      readinessPanel.score === 100 ? "text-emerald-600" : "text-amber-600"
                    )}>{readinessPanel.score}%</span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className={cn(
                        "h-full transition-all duration-300 rounded-full",
                        readinessPanel.score === 100 ? "bg-emerald-500" : "bg-amber-500"
                      )}
                      style={{ width: `${readinessPanel.score}%` }}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* System Preview Card */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-sm">
                  <Ambulance className="h-4 w-4 text-primary" />
                  System preview
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Current Triage Status */}
                <div className="rounded-lg border bg-muted/30 p-4">
                  <p className="text-[11px] uppercase tracking-wider text-muted-foreground font-bold">
                    Current Triage Status
                  </p>
                  <div className="mt-2 flex items-center justify-between">
                    <span className={cn(
                      "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-bold shadow-sm border",
                      realtimeTriage.color === "green" && "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/20 dark:text-emerald-400 dark:border-emerald-900/50",
                      realtimeTriage.color === "orange" && "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/20 dark:text-amber-400 dark:border-amber-900/50",
                      realtimeTriage.color === "red" && "bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/20 dark:text-rose-400 dark:border-rose-900/50"
                    )}>
                      <span>{realtimeTriage.emoji}</span>
                      <span>{realtimeTriage.label}</span>
                    </span>
                  </div>
                </div>

                {/* Will be sent to doctor */}
                <div className="rounded-lg border p-4">
                  <p className="text-[11px] uppercase tracking-wider text-muted-foreground font-bold font-semibold">
                    Will be sent to doctor
                  </p>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {recommended.map((r) => (
                      <span key={r} className="rounded border bg-background px-2 py-0.5 text-xs font-medium">
                        {r}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Critical Patient Visual Alert */}
                {showCriticalAlert && (
                  <div className="rounded-lg border border-red-500 bg-red-50 p-3 text-red-800 dark:border-red-900/50 dark:bg-red-950/20 dark:text-red-400 animate-pulse">
                    <div className="flex gap-2">
                      <AlertCircle className="h-4 w-4 shrink-0 mt-0.5 text-red-600" />
                      <div>
                        <p className="text-xs font-bold uppercase tracking-wider">⚠️ Critical patient</p>
                        <p className="text-[10px] leading-normal font-semibold mt-0.5">
                          Consider immediate physician notification.
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                <Button
                  className={cn(
                    "w-full",
                    !isFormValid && "opacity-50 cursor-not-allowed hover:bg-primary"
                  )}
                  size="lg"
                  onClick={handleSubmitClick}
                  disabled={isSubmitting || !isFormValid}
                >
                  <Send className="mr-2 h-4 w-4" />
                  {isSubmitting ? "Submitting…" : "Submit intake"}
                </Button>

                <p className="text-[11px] leading-relaxed text-muted-foreground">
                  On submit, the system creates a doctor notification with vitals, symptoms, triage status,
                  and recommended investigations. No staff member forwards it manually.
                </p>
              </CardContent>
            </Card>
          </aside>
        </div>
      </div>
    </div>
  );
}

import { forwardRef } from "react";
import { apiErrorMessage } from "@/lib/api-error";

const Field = forwardRef<
  HTMLInputElement,
  {
    label: string;
    defaultValue?: string;
    value?: string;
    onChange?: (v: string) => void;
    placeholder?: string;
    helperText?: string;
    required?: boolean;
    showError?: boolean;
    errorText?: string;
    validationError?: string | null;
  }
>(function Field({ label, defaultValue, value, onChange, placeholder, helperText, required, showError, errorText, validationError }, ref) {
  const isMissing = required && !value?.trim();
  const hasError = (isMissing && showError) || !!validationError;
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <Label className="text-xs font-semibold">
          {label}
          {required && <span className="ml-1 text-destructive font-bold">*</span>}
        </Label>
        {validationError ? (
          <span className="text-[10px] text-destructive font-bold">
            {validationError}
          </span>
        ) : isMissing && showError ? (
          <span className="text-[10px] text-destructive font-bold animate-pulse">
            {errorText || "Required"}
          </span>
        ) : null}
      </div>
      {onChange ? (
        <Input ref={ref} value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} className={cn(hasError && "border-destructive focus-visible:ring-destructive")} />
      ) : (
        <Input ref={ref} defaultValue={defaultValue} placeholder={placeholder} className={cn(hasError && "border-destructive focus-visible:ring-destructive")} />
      )}
      {helperText && (
        <p className="text-[11px] text-muted-foreground font-semibold leading-normal mt-0.5">
          {helperText}
        </p>
      )}
    </div>
  );
});
