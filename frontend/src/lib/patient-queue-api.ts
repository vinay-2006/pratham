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

export async function fetchPatientQueue(): Promise<PatientQueueItem[]> {
  const { data } = await axios.get<PatientQueueItem[]>(`${API_BASE}/investigations/queue`);
  return data;
}