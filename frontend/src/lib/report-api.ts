/**
 * report-api.ts — API client for the Clinical Intelligence Report
 *
 * Single function to fetch the consolidated report from
 * GET /api/report/{intake_id}
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

export interface PipelineStatus {
  nlp: string;
  risk: string;
  lab: string;
  imaging: string;
  aggregation: string;
}

export interface ClinicalReport {
  intake_id: string;
  generated_at: string;
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
}

// ── Fetch function ───────────────────────────────────────────────────────

export async function fetchClinicalReport(intakeId: string): Promise<ClinicalReport> {
  const { data } = await axios.get<ClinicalReport>(`${API_BASE}/report/${intakeId}`);
  return data;
}
