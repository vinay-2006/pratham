// Mock clinical data for the PRATHAM prototype.
// Wording is intentionally cautious. Nothing here is a real prediction.

export type Severity = "critical" | "high" | "moderate" | "low";
export type AIConfidence = "Low" | "Moderate" | "High";
export type Completeness = "LOW" | "MODERATE" | "HIGH";
export type InvestigationStatus = "Pending" | "In progress" | "Confirmed";

// New: end-to-end workflow status for the investigation pipeline
export type WorkflowStatus =
  | "Pending Approval"
  | "Approved"
  | "In Progress"
  | "Results Available"
  | "Reviewed"
  | "Rejected";

// Patient-level lifecycle status visible to nurses
export type PatientStatus =
  | "Intake Pending"
  | "Awaiting Doctor Approval"
  | "Investigation Approved"
  | "Investigation Running"
  | "Results Available";

export interface RiskEstimate {
  label: string;
  value: number; // 0-100
  severity: Severity;
  note: string;
}

export interface Investigation {
  name: string;
  status: InvestigationStatus;
  rationale: string;
}

export interface DifferentialItem {
  condition: string;
  probability: number; // 0-100
  aiConfidence: AIConfidence;
  contributingEvidence: string[];
  uncertainty: string;
}

export interface EvidencePiece {
  id: string;
  label: string;
  finding: string;
  source: string; // provenance
  contribution: string;
  weight: Severity;
}

export interface PatientCase {
  id: string;
  patient: {
    name: string;
    age: number;
    sex: "M" | "F";
    arrival: string;
    eta: string;
  };
  vitals: {
    heartRate: number;
    spo2: number;
    bloodPressure: string;
    respiratoryRate: number;
    temperature: number;
  };
  symptoms: string[];
  freeText: string;

  evidenceCompleteness: Completeness;
  overallSeverity: Severity;
  priorityLabel: string;

  operationalRiskEstimates: RiskEstimate[];
  preparationAlerts: { label: string; active: boolean; note: string }[];

  recommendedInvestigations: Investigation[];

  evidence: {
    available: EvidencePiece[];
    missing: { name: string; reason: string }[];
  };

  assistiveDifferential: DifferentialItem[];

  imaging: {
    studyType: string;
    pneumoniaProbability: number;
    aiConfidence: AIConfidence;
    suppressed: boolean;
    heatmapHotspots: { x: number; y: number; r: number; intensity: number }[];
    interpretation: string;
  };
}

// PRIMARY CASE — coherent ACS-leaning presentation with moderate evidence
const primaryCase: PatientCase = {
  id: "case-primary",
  patient: { name: "Patient A. Sharma", age: 58, sex: "M", arrival: "20:14", eta: "6 min" },
  vitals: { heartRate: 118, spo2: 91, bloodPressure: "148/96", respiratoryRate: 24, temperature: 37.4 },
  symptoms: ["Chest Pain", "Breathlessness"],
  freeText:
    "58 y/o male, sudden onset substernal chest pain radiating to left arm during exertion, associated breathlessness and diaphoresis. No prior cardiac history reported.",
  evidenceCompleteness: "MODERATE",
  overallSeverity: "high",
  priorityLabel: "High Priority",
  operationalRiskEstimates: [
    { label: "Cardiac Risk", value: 78, severity: "high", note: "Vitals + symptom pattern suggest cardiac workup priority." },
    { label: "Respiratory Risk", value: 62, severity: "moderate", note: "SpO2 91% with elevated respiratory rate." },
    { label: "Trauma Risk", value: 8, severity: "low", note: "No reported mechanism of injury." },
    { label: "Neurological Risk", value: 22, severity: "low", note: "Patient alert, no focal deficits reported." },
  ],
  preparationAlerts: [
    { label: "ICU bed standby", active: true, note: "Cardiac ICU notified" },
    { label: "Oxygen prep", active: true, note: "Set for 4 L/min nasal" },
    { label: "Trauma team", active: false, note: "Not indicated" },
    { label: "CT readiness", active: true, note: "Suite reserved 20:30" },
    { label: "Cath lab on-call", active: true, note: "Standby notified" },
  ],
  recommendedInvestigations: [
    { name: "ECG", status: "In progress", rationale: "Rule out STEMI / arrhythmia" },
    { name: "Troponin", status: "Pending", rationale: "Myocardial injury marker" },
    { name: "Chest X-ray", status: "Confirmed", rationale: "Rule out pulmonary cause" },
    { name: "CBC", status: "Pending", rationale: "Baseline hematology" },
    { name: "CT Brain", status: "Pending", rationale: "Optional if neuro signs emerge" },
  ],
  evidence: {
    available: [
      { id: "ev-1", label: "Heart rate 118 bpm", finding: "Tachycardia at rest", source: "Ambulance monitor · 20:08", contribution: "Raises cardiac risk estimate; consistent with stress response or arrhythmia.", weight: "high" },
      { id: "ev-2", label: "SpO2 91%", finding: "Mild hypoxemia", source: "Pulse oximeter · 20:09", contribution: "Supports respiratory compromise component.", weight: "moderate" },
      { id: "ev-3", label: "Chest X-ray opacity", finding: "Lower-zone opacity, right lung", source: "Imaging viewer · 20:12", contribution: "Imaging model highlighted region; assistive only.", weight: "moderate" },
      { id: "ev-4", label: "Symptom pattern", finding: "Substernal pain radiating to left arm + diaphoresis", source: "Intake free-text · 20:05", contribution: "Pattern weighted toward acute coronary syndrome.", weight: "high" },
    ],
    missing: [
      { name: "Troponin", reason: "Not yet drawn — required for ACS confirmation." },
      { name: "12-lead ECG result", reason: "Acquisition in progress." },
      { name: "Prior cardiac history", reason: "Patient unable to provide; family contacted." },
    ],
  },
  assistiveDifferential: [
    { condition: "Acute Coronary Syndrome", probability: 71, aiConfidence: "Moderate", contributingEvidence: ["Symptom pattern", "Heart rate 118 bpm", "Age + sex risk profile"], uncertainty: "Troponin and ECG not yet available — estimate may shift substantially." },
    { condition: "Pulmonary Embolism", probability: 14, aiConfidence: "Low", contributingEvidence: ["SpO2 91%", "Tachycardia", "Acute breathlessness"], uncertainty: "No D-dimer or CTPA available; cannot rule out." },
    { condition: "Severe Arrhythmia", probability: 7, aiConfidence: "Low", contributingEvidence: ["Tachycardia"], uncertainty: "Requires ECG for any meaningful assessment." },
    { condition: "Pneumonia (lower-zone)", probability: 5, aiConfidence: "Low", contributingEvidence: ["X-ray opacity", "Temperature 37.4°C"], uncertainty: "Imaging finding non-specific; clinical correlation needed." },
  ],
  imaging: {
    studyType: "Chest X-ray (PA)",
    pneumoniaProbability: 0.36,
    aiConfidence: "Low",
    suppressed: false,
    heatmapHotspots: [
      { x: 62, y: 68, r: 22, intensity: 0.85 },
      { x: 54, y: 60, r: 14, intensity: 0.5 },
    ],
    interpretation: "Model attention concentrated in the right lower lung zone. Finding is non-specific; treat as supportive only.",
  },
};

const lowEvidenceCase: PatientCase = {
  id: "case-low-evidence",
  patient: { name: "Patient B. Iyer", age: 41, sex: "F", arrival: "20:42", eta: "incoming" },
  vitals: { heartRate: 104, spo2: 95, bloodPressure: "—", respiratoryRate: 20, temperature: 0 },
  symptoms: ["Breathlessness"],
  freeText: "Brief radio report: female, ~40s, breathing difficulty. No further details yet.",
  evidenceCompleteness: "LOW",
  overallSeverity: "moderate",
  priorityLabel: "Awaiting Triage",
  operationalRiskEstimates: [
    { label: "Cardiac Risk", value: 34, severity: "moderate", note: "Sparse data — estimate unstable." },
    { label: "Respiratory Risk", value: 48, severity: "moderate", note: "Single symptom report only." },
    { label: "Trauma Risk", value: 5, severity: "low", note: "No mechanism reported." },
    { label: "Neurological Risk", value: 12, severity: "low", note: "No information." },
  ],
  preparationAlerts: [
    { label: "ICU bed standby", active: false, note: "Insufficient data to commit" },
    { label: "Oxygen prep", active: true, note: "Precautionary" },
    { label: "Trauma team", active: false, note: "Not indicated" },
    { label: "CT readiness", active: false, note: "Hold pending intake" },
    { label: "Cath lab on-call", active: false, note: "Not indicated" },
  ],
  recommendedInvestigations: [
    { name: "ECG", status: "Pending", rationale: "Baseline cardiac assessment" },
    { name: "Troponin", status: "Pending", rationale: "Rule out cardiac component" },
    { name: "Chest X-ray", status: "Pending", rationale: "Evaluate respiratory cause" },
    { name: "CBC", status: "Pending", rationale: "Baseline hematology" },
  ],
  evidence: {
    available: [
      { id: "ev-l1", label: "Breathlessness reported", finding: "Subjective respiratory distress", source: "Ambulance radio · 20:38", contribution: "Single qualitative data point; insufficient for differential.", weight: "moderate" },
      { id: "ev-l2", label: "SpO2 95%", finding: "Within acceptable range", source: "Pulse oximeter · 20:40", contribution: "Does not strongly support or rule out hypoxic causes.", weight: "low" },
    ],
    missing: [
      { name: "Blood pressure", reason: "Cuff not yet applied." },
      { name: "ECG", reason: "Not acquired." },
      { name: "Troponin", reason: "Not drawn." },
      { name: "Chest imaging", reason: "Not acquired." },
      { name: "Patient history", reason: "Unavailable on arrival." },
    ],
  },
  assistiveDifferential: [
    { condition: "Acute respiratory distress (cause undetermined)", probability: 32, aiConfidence: "Low", contributingEvidence: ["Breathlessness reported"], uncertainty: "Estimate based on a single symptom — not reliable." },
    { condition: "Anxiety / hyperventilation", probability: 22, aiConfidence: "Low", contributingEvidence: ["Normal SpO2"], uncertainty: "Cannot differentiate without clinical exam." },
    { condition: "Cardiac-origin dyspnea", probability: 18, aiConfidence: "Low", contributingEvidence: [], uncertainty: "No cardiac data available." },
  ],
  imaging: {
    studyType: "Chest X-ray (not acquired)",
    pneumoniaProbability: 0,
    aiConfidence: "Low",
    suppressed: true,
    heatmapHotspots: [],
    interpretation: "No imaging available — interpretation suppressed.",
  },
};

export const cases: Record<string, PatientCase> = { primary: primaryCase, low: lowEvidenceCase };
export const defaultCaseKey = "primary";

// ===== Notification queue (system-generated for doctor) =====
export interface DoctorNotification {
  id: string;
  intake_id: string; // maps to emergency_intake.id in Supabase
  patientName: string;
  age: number;
  sex: "M" | "F";
  severity: Severity;
  symptoms: string[];
  vitalsSummary: string;
  recommendedInvestigations: string[];
  timestamp: string; // HH:MM
  urgency: "Routine" | "Urgent" | "Critical";
  status: "Pending Approval" | "Approved" | "Rejected" | "Needs Info";
  caseKey?: keyof typeof cases;
  vitals?: {
    heartRate: number | null;
    spo2: number | null;
    bloodPressure: string | null;
    respiratoryRate: number | null;
    temperature: number | null;
  };
  emergencyDescription?: string;
  audit?: {
    reviewedBy?: string;
    reviewedAt?: string;
    reviewNotes?: string;
  };
}

export const initialNotifications: DoctorNotification[] = [
  {
    id: "ntf-001",
    intake_id: "00000000-0000-0000-0000-000000000001",
    patientName: "A. Sharma",
    age: 58,
    sex: "M",
    severity: "high",
    symptoms: ["Chest Pain", "Breathlessness"],
    vitalsSummary: "HR 118 · SpO₂ 91% · BP 148/96",
    recommendedInvestigations: ["ECG", "Troponin", "Chest X-ray", "CBC"],
    timestamp: "20:11",
    urgency: "Urgent",
    status: "Pending Approval",
    caseKey: "primary",
  },
  {
    id: "ntf-002",
    intake_id: "00000000-0000-0000-0000-000000000002",
    patientName: "R. Verma",
    age: 34,
    sex: "M",
    severity: "critical",
    symptoms: ["Chest Pain", "Breathlessness", "Diaphoresis"],
    vitalsSummary: "HR 138 · SpO₂ 82% · BP 92/60",
    recommendedInvestigations: ["ECG", "Troponin", "ABG", "CBC"],
    timestamp: "20:18",
    urgency: "Critical",
    status: "Pending Approval",
  },
  {
    id: "ntf-003",
    intake_id: "00000000-0000-0000-0000-000000000003",
    patientName: "B. Iyer",
    age: 41,
    sex: "F",
    severity: "moderate",
    symptoms: ["Breathlessness"],
    vitalsSummary: "HR 104 · SpO₂ 95% · BP —",
    recommendedInvestigations: ["ECG", "Chest X-ray", "CBC"],
    timestamp: "20:40",
    urgency: "Routine",
    status: "Pending Approval",
    caseKey: "low",
  },
];

// ===== Patient queue (for nurse dashboard) =====
export interface QueuePatient {
  id: string;
  name: string;
  age: number;
  sex: "M" | "F";
  severity: Severity;
  status: PatientStatus;
  bed: string;
  eta: string;
  symptoms: string[];
  caseKey?: keyof typeof cases;
}

export const patientQueue: QueuePatient[] = [
  {
    id: "pq-001",
    name: "A. Sharma",
    age: 58,
    sex: "M",
    severity: "high",
    status: "Investigation Running",
    bed: "ER-04",
    eta: "On site",
    symptoms: ["Chest Pain", "Breathlessness"],
    caseKey: "primary",
  },
  {
    id: "pq-002",
    name: "R. Verma",
    age: 34,
    sex: "M",
    severity: "critical",
    status: "Awaiting Doctor Approval",
    bed: "ER-01",
    eta: "On site",
    symptoms: ["Chest Pain", "Breathlessness"],
  },
  {
    id: "pq-003",
    name: "B. Iyer",
    age: 41,
    sex: "F",
    severity: "moderate",
    status: "Intake Pending",
    bed: "Triage",
    eta: "2 min",
    symptoms: ["Breathlessness"],
    caseKey: "low",
  },
  {
    id: "pq-004",
    name: "S. Khan",
    age: 27,
    sex: "F",
    severity: "low",
    status: "Results Available",
    bed: "ER-07",
    eta: "On site",
    symptoms: ["Abdominal Pain"],
  },
  {
    id: "pq-005",
    name: "M. Pillai",
    age: 66,
    sex: "M",
    severity: "moderate",
    status: "Investigation Approved",
    bed: "ER-02",
    eta: "On site",
    symptoms: ["Dizziness", "Headache"],
  },
];

export const workflowOrder: WorkflowStatus[] = [
  "Pending Approval",
  "Approved",
  "In Progress",
  "Results Available",
  "Reviewed",
];
