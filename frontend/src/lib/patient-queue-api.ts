import axios from "axios";
import { WorkflowStatus } from "./mock-data";
import { API_BASE } from "./api-config";

export interface PipelineStatusMap {
  nlp: string;
  risk: string;
  lab: string;
  imaging: string;
  aggregation: string;
}

export interface PatientQueueItem {
  intake_id: string;
  patient_name: string;
  age: number;
  sex: "M" | "F";
  severity: string;
  arrival_time: string;
  intake_status: WorkflowStatus;
  chief_complaint: string;
  created_at: string;
  workflow_status: WorkflowStatus;
  case_id?: string;
  arrival_type: string;
  ambulance_eta?: number | null;
  progress: number;
  investigation_counts: {
    approved: number;
    pending: number;
    rejected: number;
    needs_info: number;
    total: number;
  };
  evidence_completeness: {
    uploaded: number;
    required: number;
  };
  pipeline_status: PipelineStatusMap;
}

export interface QueueStats {
  total_patients: number;
  pending_approval_patients: number;
}

export interface TimelineEvent {
  event: string;
  timestamp: string;
  icon: string;
  type: string;
  detail: string | null;
}

export interface WorkflowLog {
  id: string;
  intake_id: string;
  old_status: string | null;
  new_status: string;
  actor_type: "System" | "Nurse" | "Doctor";
  actor_name: string;
  reason: string | null;
  changed_at: string;
}

export interface RegistryItem {
  intake_id: string;
  case_id: string;
  patient_name: string;
  created_at: string;
  updated_at?: string;
  arrival_type: string;
  status: WorkflowStatus;
  report_available: boolean;
  closed_by?: string | null;
}

// ── New Doctor Workspace Interfaces ──────────────────────────────────────────

export interface DoctorDashboardStats {
  total_patients: number;
  total_patients_trend: number;
  cases_closed: number;
  cases_closed_trend: number;
  pending_approvals: number;
  pending_approvals_trend: number;
  clinical_reviews_remaining: number;
  clinical_reviews_remaining_trend: number;
}

export interface DoctorReviewPatient {
  intake_id: string;
  case_id: string;
  patient_name: string;
  age: number;
  sex: "M" | "F";
  arrival_type: string;
  status: WorkflowStatus;
  workflow_status: WorkflowStatus;
  created_at: string;
  chief_complaint: string;
  severity: string;
  investigations: {
    id: string;
    status: string;
    investigation_type: string;
    approved_at?: string;
    approved_by?: string;
    rejected_at?: string;
    rejected_by?: string;
    review_notes?: string;
  }[];
  progress: number;
}

export interface DoctorReportItem {
  intake_id: string;
  case_id: string;
  patient_name: string;
  age: number;
  sex: "M" | "F";
  arrival_type: string;
  status: WorkflowStatus;
  workflow_status: WorkflowStatus;
  created_at: string;
  updated_at?: string;
  chief_complaint: string;
  severity: string;
  pipeline_status: PipelineStatusMap;
  investigations: {
    investigation_type: string;
    status: string;
  }[];
  progress: number;
}

// ── API Functions ────────────────────────────────────────────────────────────

export async function fetchPatientQueue(): Promise<PatientQueueItem[]> {
  const { data } = await axios.get<PatientQueueItem[]>(`${API_BASE}/investigations/queue`);
  return data;
}

export async function fetchQueueStats(): Promise<QueueStats> {
  const { data } = await axios.get<QueueStats>(`${API_BASE}/investigations/queue/stats`);
  return data;
}

export async function fetchPatientTimeline(intakeId: string): Promise<TimelineEvent[]> {
  const { data } = await axios.get<TimelineEvent[]>(
    `${API_BASE}/investigations/patient/${intakeId}/timeline`
  );
  return data;
}

export async function fetchWorkflowLogs(intakeId: string): Promise<WorkflowLog[]> {
  const { data } = await axios.get<WorkflowLog[]>(
    `${API_BASE}/intake/${intakeId}/workflow-logs`
  );
  return data;
}

export async function confirmArrival(
  intakeId: string,
  actorName: string
): Promise<{ status: string; new_status: string }> {
  const { data } = await axios.post(`${API_BASE}/intake/arrival/confirm`, {
    intake_id: intakeId,
    actor_name: actorName,
  });
  return data;
}

export async function closeCase(
  intakeId: string,
  actorName: string,
  reason?: string
): Promise<{ status: string }> {
  const { data } = await axios.post(`${API_BASE}/intake/${intakeId}/close`, {
    actor_name: actorName,
    reason: reason || "Doctor marked case as closed.",
  });
  return data;
}

export async function fetchRegistry(): Promise<RegistryItem[]> {
  const { data } = await axios.get<RegistryItem[]>(`${API_BASE}/intake/registry`);
  return data;
}

// ── New Doctor Workspace API Functions ────────────────────────────────────────

export async function fetchDoctorDashboardStats(): Promise<DoctorDashboardStats> {
  const { data } = await axios.get<DoctorDashboardStats>(`${API_BASE}/doctor/dashboard/stats`);
  return data;
}

export async function fetchDoctorReviewPatients(): Promise<DoctorReviewPatient[]> {
  const { data } = await axios.get<DoctorReviewPatient[]>(`${API_BASE}/doctor/review/patients`);
  return data;
}

export async function fetchDoctorReportsList(): Promise<DoctorReportItem[]> {
  const { data } = await axios.get<DoctorReportItem[]>(`${API_BASE}/doctor/reports/list`);
  return data;
}

export async function approveInvestigations(
  intakeId: string,
  approvedTests: string[],
  customTests: string[],
  doctorName: string,
  doctorNotes: string
): Promise<{ success: boolean; approved_count: number; status: string }> {
  const { data } = await axios.post(`${API_BASE}/investigations/approve`, {
    intake_id: intakeId,
    approved_tests: approvedTests,
    custom_tests: customTests,
    doctor_name: doctorName,
    doctor_notes: doctorNotes,
  });
  return data;
}

export async function rejectInvestigations(
  intakeId: string,
  doctorName: string,
  doctorNotes: string
): Promise<{ intake_id: string; status: string }> {
  const { data } = await axios.post(`${API_BASE}/investigations/reject`, {
    intake_id: intakeId,
    doctor_name: doctorName,
    doctor_notes: doctorNotes,
  });
  return data;
}

export async function returnToNurse(
  intakeId: string,
  actorName: string,
  reason: string
): Promise<{ status: string }> {
  const { data } = await axios.post(`${API_BASE}/investigations/return-to-nurse`, {
    intake_id: intakeId,
    actor_name: actorName,
    reason: reason,
  });
  return data;
}

export async function recommendInvestigation(
  intakeId: string,
  testName: string,
  doctorName: string
): Promise<{ status: string; id: string }> {
  const { data } = await axios.post(`${API_BASE}/investigations/recommend`, {
    intake_id: intakeId,
    investigation_type: testName,
    doctor_name: doctorName,
  });
  return data;
}