from enum import Enum

class WorkflowStatus(str, Enum):
    INTAKE_SUBMITTED = "intake_submitted"
    EN_ROUTE = "en_route"
    ARRIVED = "arrived"
    AWAITING_APPROVAL = "awaiting_doctor_approval"
    APPROVED = "investigations_approved"
    UPLOAD_PENDING = "evidence_upload_pending"
    ANALYSIS_RUNNING = "analysis_running"
    REPORT_READY = "clinical_report_ready"
    UNDER_REVIEW = "under_doctor_review"
    CLOSED = "case_closed"
    OFFLINE = "offline_care"


# Canonical mapping of workflow status → UI progress percentage.
# Defined here because it is a property of the WorkflowStatus state machine,
# not of any individual API handler.
# Previously duplicated inside get_patient_queue, get_doctor_review_patients,
# and get_doctor_reports_list (partial variant).
WORKFLOW_PROGRESS_MAP: dict[str, int] = {
    WorkflowStatus.INTAKE_SUBMITTED.value: 10,
    WorkflowStatus.EN_ROUTE.value:          10,
    WorkflowStatus.ARRIVED.value:           20,
    WorkflowStatus.AWAITING_APPROVAL.value: 40,
    WorkflowStatus.APPROVED.value:          60,
    WorkflowStatus.UPLOAD_PENDING.value:    60,
    WorkflowStatus.ANALYSIS_RUNNING.value:  75,
    WorkflowStatus.REPORT_READY.value:      90,
    WorkflowStatus.UNDER_REVIEW.value:      95,
    WorkflowStatus.CLOSED.value:           100,
    WorkflowStatus.OFFLINE.value:          100,
}
