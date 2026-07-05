import axios from "axios";

const API_BASE = "http://localhost:8000/api";

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
  intake_status: string;
  chief_complaint: string;
  created_at: string;
  workflow_status: string;
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