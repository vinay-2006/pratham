"""
PRATHAM Centralized Enums — Single source of truth for all string constants.

Every status, stage, type, and label used across the system is defined here.
No hardcoded strings should exist elsewhere in the codebase.
These enums are backward-compatible with all existing string values in the database
and API responses.

Domain Ownership: shared (cross-cutting)
"""

from __future__ import annotations

from enum import Enum


# ── Workflow Status ──────────────────────────────────────────────────────────
# Matches the 11-state workflow defined in the Phase 0B State Machine.
# Compatible with app.models.workflow.WorkflowStatus values.

class WorkflowStatus(str, Enum):
    """Patient case lifecycle states — the canonical 11-state machine."""
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

    @classmethod
    def terminal_states(cls) -> set[WorkflowStatus]:
        """Return the set of states from which no further transitions are allowed."""
        return {cls.CLOSED, cls.OFFLINE}

    @classmethod
    def active_states(cls) -> set[WorkflowStatus]:
        """Return all non-terminal states (cases still in progress)."""
        return set(cls) - cls.terminal_states()

    @property
    def label(self) -> str:
        """Human-readable display label for this status."""
        return _WORKFLOW_LABELS[self]


_WORKFLOW_LABELS: dict[WorkflowStatus, str] = {
    WorkflowStatus.INTAKE_SUBMITTED: "Intake Submitted",
    WorkflowStatus.EN_ROUTE: "En Route",
    WorkflowStatus.ARRIVED: "Arrived",
    WorkflowStatus.AWAITING_APPROVAL: "Awaiting Doctor Approval",
    WorkflowStatus.APPROVED: "Investigations Approved",
    WorkflowStatus.UPLOAD_PENDING: "Evidence Upload Pending",
    WorkflowStatus.ANALYSIS_RUNNING: "Analysis Running",
    WorkflowStatus.REPORT_READY: "Clinical Report Ready",
    WorkflowStatus.UNDER_REVIEW: "Under Doctor Review",
    WorkflowStatus.CLOSED: "Case Closed",
    WorkflowStatus.OFFLINE: "Offline Care",
}


# ── Pipeline Stage ───────────────────────────────────────────────────────────
# The 5 AI pipeline stages — must match pipeline_status.stage CHECK constraint.

class PipelineStage(str, Enum):
    """AI pipeline analysis stages."""
    NLP = "nlp"
    RISK = "risk"
    LAB = "lab"
    IMAGING = "imaging"
    AGGREGATION = "aggregation"

    @classmethod
    def all_stages(cls) -> tuple[PipelineStage, ...]:
        """Return all stages in execution order."""
        return (cls.NLP, cls.RISK, cls.LAB, cls.IMAGING, cls.AGGREGATION)


# ── Pipeline Stage Status ────────────────────────────────────────────────────

class PipelineStageStatus(str, Enum):
    """Execution state of an individual pipeline stage."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ── Investigation Status ─────────────────────────────────────────────────────

class InvestigationStatus(str, Enum):
    """Lifecycle state of an investigation recommendation."""
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_INFO = "needs_info"


# ── Severity ─────────────────────────────────────────────────────────────────
# Used across risk scoring, evidence assessment, and report generation.

class Severity(str, Enum):
    """Clinical severity levels — used by risk engine and report."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


# ── Arrival Type ─────────────────────────────────────────────────────────────

class ArrivalType(str, Enum):
    """How the patient arrived at the emergency department."""
    WALK_IN = "walk_in"
    AMBULANCE = "ambulance"
    REFERRAL = "referral"


# ── Actor Type ───────────────────────────────────────────────────────────────

class ActorType(str, Enum):
    """Who triggered a workflow action — for audit logging."""
    SYSTEM = "System"
    NURSE = "Nurse"
    DOCTOR = "Doctor"


# ── Evidence Type ────────────────────────────────────────────────────────────

class EvidenceType(str, Enum):
    """Type of clinical evidence uploaded by nurse."""
    XRAY = "xray"
    LAB_REPORT = "lab_report"
    ECG = "ecg"
    CLINICAL_NOTES = "clinical_notes"
    CT_SCAN = "ct_scan"
    MRI = "mri"
    BLOOD_WORK = "blood_work"
    ULTRASOUND = "ultrasound"


# ── Analysis Type ────────────────────────────────────────────────────────────

class AnalysisType(str, Enum):
    """Type of AI analysis that can be run on evidence."""
    LAB = "lab"
    IMAGING = "imaging"


# ── Visit Type ───────────────────────────────────────────────────────────────

class VisitType(str, Enum):
    """Classification of the emergency department visit."""
    EMERGENCY = "emergency"
    ROUTINE = "routine"


# ── Provenance ───────────────────────────────────────────────────────────────
# ADR-008: Clinical Safety Provenance — track how results were produced.

class Provenance(str, Enum):
    """Source/method that produced a clinical result."""
    LLM = "llm"
    RULE_BASED = "rule-based"
    FALLBACK = "fallback"
    MOCK = "mock"
    ML_MODEL = "ml-model"


# ── Risk Category ────────────────────────────────────────────────────────────

class RiskCategory(str, Enum):
    """Clinical risk categories assessed by the risk engine."""
    CARDIAC = "cardiac_risk"
    RESPIRATORY = "respiratory_risk"
    TRAUMA = "trauma_risk"
    NEUROLOGICAL = "neurological_risk"


# ── Preparation Alert Type ───────────────────────────────────────────────────

class PreparationAlertType(str, Enum):
    """Hospital preparation alerts triggered by risk assessment."""
    ICU_STANDBY = "icu_standby"
    OXYGEN_PREP = "oxygen_prep"
    TRAUMA_TEAM = "trauma_team"
    CT_SCANNER = "ct_scanner"
    EMERGENCY_BED = "emergency_bed"
    BLOOD_BANK = "blood_bank"
