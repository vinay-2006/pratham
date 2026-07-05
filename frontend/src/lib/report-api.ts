/**
 * report-api.ts — API client for the Clinical Intelligence Report
 *
 * Single function to fetch the consolidated report from
 * GET /api/report/{intake_id}
 *
 * Also provides fetchPipelineStatus for the dedicated pipeline polling endpoint.
 *
 * PRATHAM v1: Updated to include clinical reasoning conclusions,
 * LLM interpretations, and the unified 17-section Report DTO types.
 */

import axios from "axios";

const API_BASE = "http://localhost:8000/api";

// ── Type definitions ─────────────────────────────────────────────────────

export interface PatientSummary {
  patient_id: string;
  name: string;
  age: number;
  gender: string;
  contact: string | null;
  chief_complaint: string;
  emergency_description: string;
  severity: string;
  allergies: string[];
  medications: string[];
  medical_history: string[];
  arrival_time: string;
}

export interface Vitals {
  heart_rate: number | null;
  spo2: number | null;
  bp_systolic: number | null;
  bp_diastolic: number | null;
  blood_pressure: string;
  temperature: number | null;
  respiratory_rate: number | null;
}

export interface NlpFindings {
  flags: Record<string, boolean>;
  entities: string[];
  summary: string;
}

export interface RiskEngine {
  cardiac: number;
  respiratory: number;
  trauma: number;
  neurological: number;
  severity: string;
}

export interface LabIntelligence {
  available: boolean;
  model_name: string | null;
  prediction: string | null;
  risk_probability: number | null;
  top_features: Record<string, number> | null;
  shap_values: Record<string, number> | null;
  created_at: string | null;
}

export interface ImagingIntelligence {
  available: boolean;
  model_name: string | null;
  prediction: string | null;
  pneumonia_probability: number | null;
  confidence: number | null;
  xray_url: string;
  gradcam_url: string;
  created_at: string | null;
}

export interface Aggregation {
  available: boolean;
  primary_condition: string | null;
  confidence_suppressed: boolean | null;
  suppression_reason: string | null;
  probabilities: Record<string, number>;
  evidence_breakdown: Record<string, string[]>;
  source_summary: Record<string, boolean>;
}

export interface EvidenceItem {
  id: string;
  evidence_type: string;
  file_name: string;
  file_url: string;
  uploaded_at: string;
}

// ── Clinical Interpretation (LLM narratives) ─────────────────────────────

export interface ClinicalInterpretation {
  clinical_overview: string;
  overall_impression: string;
  cardiac_summary: string;
  respiratory_summary: string;
  laboratory_summary: string;
  imaging_summary: string;
  monitoring_narrative: string;
  precautions_narrative: string;
  alternative_considerations_narrative: string;
  limitations_narrative: string;
}

// ── Clinical Conclusions (deterministic reasoning) ───────────────────────

export interface VitalAnalysis {
  parameter: string;
  value: number;
  unit: string;
  reference_low: number;
  reference_high: number;
  status: "normal" | "low" | "high";
}

export interface AlternativeCondition {
  condition: string;
  condition_key: string;
  probability: number;
}

export interface MonitoringPriority {
  parameter: string;
  reason: string;
}

export interface ClinicalPrecaution {
  action: string;
  reason: string;
}

export interface InvestigationStatus {
  investigation_type: string;
  status: string;
  ai_supported: boolean;
  analysis_type: string | null;
  ai_status: string;
}

export interface ClinicalLimitation {
  source: string;
  available: boolean;
  note?: string;
}

export interface ReportQuality {
  evidence_completeness_pct: number;
  subsystem_agreement: string;
  pipeline_integrity: string;
  missing_critical_inputs: string[];
}

export interface RankingJustification {
  primary_reasons: string[];
  vs_alternatives: { condition: string; reasons: string[] }[];
}

export interface DataCompleteness {
  [key: string]: {
    label: string;
    available: boolean;
    critical: boolean;
  };
}

export interface ClinicalConclusions {
  primary_condition: string | null;
  primary_condition_key: string | null;
  probabilities: Record<string, number | null>;
  alternative_conditions: AlternativeCondition[];
  supporting_evidence: string[];
  conflicting_evidence: string[];
  clinical_confidence: string;
  confidence_factors: string[];
  uncertainty_reasons: string[];
  ranking_justification: RankingJustification;
  monitoring_priorities: MonitoringPriority[];
  clinical_precautions: ClinicalPrecaution[];
  investigation_status: InvestigationStatus[];
  data_completeness: DataCompleteness;
  clinical_limitations: ClinicalLimitation[];
  report_quality: ReportQuality;
}

// ── Pipeline Status types ────────────────────────────────────────────────

export interface StageStatus {
  status: "pending" | "running" | "completed" | "failed";
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
  error_message: string | null;
  attempt_count: number;
  updated_at: string | null;
}

export interface PipelineStatusResponse {
  intake_id: string;
  stages: {
    nlp: StageStatus;
    risk: StageStatus;
    lab: StageStatus;
    imaging: StageStatus;
    aggregation: StageStatus;
  };
}

/** Legacy simple status map used by the report endpoint */
export interface PipelineStatus {
  nlp: string;
  risk: string;
  lab: string;
  imaging: string;
  aggregation: string;
}

// ── Unified Report DTO ──────────────────────────────────────────────────

export interface ClinicalReport {
  intake_id: string;
  generated_at: string;
  report_version: string;
  patient_summary: PatientSummary;
  vitals: Vitals;
  symptoms: string[];
  nlp_findings: NlpFindings;
  risk_engine: RiskEngine;
  lab_intelligence: LabIntelligence;
  imaging_intelligence: ImagingIntelligence;
  aggregation: Aggregation;
  evidence: EvidenceItem[];
  pipeline_status: PipelineStatus;
  investigations: { id: string; investigation_type: string; status: string; review_notes?: string }[];
  clinical_interpretation: ClinicalInterpretation;
  clinical_conclusions: ClinicalConclusions;
}

// ── Fetch functions ─────────────────────────────────────────────────────

export async function fetchClinicalReport(intakeId: string): Promise<ClinicalReport> {
  const { data } = await axios.get<ClinicalReport>(`${API_BASE}/report/${intakeId}`);
  return data;
}

export async function fetchPipelineStatus(intakeId: string): Promise<PipelineStatusResponse> {
  const { data } = await axios.get<PipelineStatusResponse>(
    `${API_BASE}/pipeline/status/${intakeId}`
  );
  return data;
}

/**
 * Check if any stage is still in progress (pending or running).
 * Used to determine whether polling should continue.
 */
export function isPipelineActive(stages: PipelineStatusResponse["stages"]): boolean {
  return Object.values(stages).some(
    (s) => s.status === "pending" || s.status === "running"
  );
}
