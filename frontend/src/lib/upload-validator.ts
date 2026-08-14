export const MAX_FILE_SIZE_MB = 10;
export const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

export interface ValidationResult {
  valid: boolean;
  error?: string;
}

export enum InvestigationId {
  CHEST_XRAY = "chest_xray",
  HEART_FAILURE = "heart_failure",
  ECG = "ecg",
  TROPONIN = "troponin",
  CBC = "cbc",
  CT_BRAIN = "ct_brain",
  UNKNOWN = "unknown"
}

export const MAP_INVESTIGATION_TYPE_TO_ID: Record<string, InvestigationId> = {
  "Chest X-ray": InvestigationId.CHEST_XRAY,
  "Chest X Ray": InvestigationId.CHEST_XRAY,
  "Chest Xray": InvestigationId.CHEST_XRAY,
  "Heart Failure": InvestigationId.HEART_FAILURE,
  "Heart Failure Analysis": InvestigationId.HEART_FAILURE,
  "ECG": InvestigationId.ECG,
  "EKG": InvestigationId.ECG,
  "Electrocardiogram": InvestigationId.ECG,
  "Troponin": InvestigationId.TROPONIN,
  "CBC": InvestigationId.CBC,
  "CT Brain": InvestigationId.CT_BRAIN,
};

export function getInvestigationId(type: string): InvestigationId {
  if (!type) return InvestigationId.UNKNOWN;
  if (MAP_INVESTIGATION_TYPE_TO_ID[type]) {
    return MAP_INVESTIGATION_TYPE_TO_ID[type];
  }
  const normalized = type.toLowerCase().trim().replace(/[-_\s]+/g, "");
  if (normalized.includes("chestxray")) return InvestigationId.CHEST_XRAY;
  if (normalized.includes("heartfailure")) return InvestigationId.HEART_FAILURE;
  if (normalized.includes("ecg") || normalized.includes("ekg")) return InvestigationId.ECG;
  if (normalized.includes("troponin")) return InvestigationId.TROPONIN;
  if (normalized.includes("cbc")) return InvestigationId.CBC;
  if (normalized.includes("ctbrain")) return InvestigationId.CT_BRAIN;
  
  return InvestigationId.UNKNOWN;
}

export const EVIDENCE_FORMATS: Record<
  string,
  { supported: string[]; unsupported: string[]; extensions: string[]; mimeTypes: string[] }
> = {
  clinical_notes: {
    supported: ["PDF", "DOCX", "TXT"],
    unsupported: ["PNG", "JPEG", "JPG"],
    extensions: [".pdf", ".docx", ".txt"],
    mimeTypes: ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"],
  },
  xray: {
    supported: ["PNG", "JPEG", "JPG", "DICOM (.dcm)"],
    unsupported: ["TXT", "PDF", "DOCX"],
    extensions: [".png", ".jpg", ".jpeg", ".dcm"],
    mimeTypes: ["image/png", "image/jpeg", "application/dicom"],
  },
  ecg: {
    supported: ["PNG", "JPEG", "JPG", "PDF"],
    unsupported: ["TXT", "DOCX"],
    extensions: [".png", ".jpg", ".jpeg", ".pdf"],
    mimeTypes: ["image/png", "image/jpeg", "application/pdf"],
  },
  lab_report: {
    supported: ["PDF", "TXT", "PNG", "JPEG", "JPG"],
    unsupported: ["DOCX"],
    extensions: [".pdf", ".txt", ".png", ".jpg", ".jpeg"],
    mimeTypes: ["application/pdf", "text/plain", "image/png", "image/jpeg"],
  },
};

export function validateFile(file: File, evidenceType: string): ValidationResult {
  if (file.size > MAX_FILE_SIZE_BYTES) {
    return {
      valid: false,
      error: `File size exceeds the maximum limit of ${MAX_FILE_SIZE_MB} MB.`,
    };
  }

  const spec = EVIDENCE_FORMATS[evidenceType];
  if (!spec) {
    return { valid: true };
  }

  const mimeValid = file.type === "" || spec.mimeTypes.includes(file.type);
  const name = file.name.toLowerCase();
  const extValid = spec.extensions.some((ext) => name.endsWith(ext));

  if (!mimeValid || !extValid) {
    return {
      valid: false,
      error: "This investigation accepts only supported file formats.",
    };
  }

  return { valid: true };
}
