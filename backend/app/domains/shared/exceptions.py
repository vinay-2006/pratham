"""
PRATHAM Domain Exceptions — Typed, domain-specific error hierarchy.

Every domain raises exceptions from this module instead of generic Python
exceptions or FastAPI HTTPException. The API layer catches these and maps
them to appropriate HTTP status codes.

This separation ensures:
 - Services never depend on HTTP concepts
 - Error handling is consistent across all domains
 - New error types can be added without modifying existing code

Domain Ownership: shared (cross-cutting)
"""

from __future__ import annotations


# ── Base ─────────────────────────────────────────────────────────────────────

class PrathamError(Exception):
    """Base exception for all PRATHAM domain errors."""

    def __init__(self, message: str, *, code: str = "PRATHAM_ERROR", details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.details = details or {}


# ── Repository Layer ─────────────────────────────────────────────────────────

class RepositoryError(PrathamError):
    """Base exception for data access failures."""

    def __init__(self, message: str, *, table: str = "", operation: str = "", details: dict | None = None):
        super().__init__(message, code="REPOSITORY_ERROR", details=details)
        self.table = table
        self.operation = operation


class RecordNotFoundError(RepositoryError):
    """Raised when a requested record does not exist."""

    def __init__(self, entity: str, identifier: str, *, details: dict | None = None):
        super().__init__(
            f"{entity} not found: {identifier}",
            table=entity.lower(),
            operation="find",
            details=details,
        )
        self.code = "RECORD_NOT_FOUND"


class DuplicateRecordError(RepositoryError):
    """Raised when a unique constraint would be violated."""

    def __init__(self, entity: str, field: str, value: str, *, details: dict | None = None):
        super().__init__(
            f"Duplicate {entity}: {field}={value}",
            table=entity.lower(),
            operation="create",
            details=details,
        )
        self.code = "DUPLICATE_RECORD"


# ── Patient Domain ───────────────────────────────────────────────────────────

class PatientNotFoundError(RecordNotFoundError):
    """Raised when a patient record cannot be found."""

    def __init__(self, patient_id: str):
        super().__init__("Patient", patient_id)
        self.code = "PATIENT_NOT_FOUND"


# ── Triage / Intake Domain ──────────────────────────────────────────────────

class IntakeNotFoundError(RecordNotFoundError):
    """Raised when an intake record cannot be found."""

    def __init__(self, intake_id: str):
        super().__init__("Intake", intake_id)
        self.code = "INTAKE_NOT_FOUND"


class DuplicateCaseIDError(DuplicateRecordError):
    """Raised when a generated case ID already exists."""

    def __init__(self, case_id: str):
        super().__init__("Intake", "case_id", case_id)
        self.code = "DUPLICATE_CASE_ID"


# ── Workflow Domain ──────────────────────────────────────────────────────────

class WorkflowTransitionError(PrathamError):
    """Raised when a workflow state transition is invalid."""

    def __init__(
        self,
        intake_id: str,
        current_status: str,
        attempted_status: str,
        *,
        allowed: list[str] | None = None,
    ):
        allowed_str = ", ".join(allowed) if allowed else "none"
        super().__init__(
            f"Invalid transition for intake {intake_id}: "
            f"{current_status} -> {attempted_status} (allowed: {allowed_str})",
            code="INVALID_WORKFLOW_TRANSITION",
            details={
                "intake_id": intake_id,
                "current_status": current_status,
                "attempted_status": attempted_status,
                "allowed_transitions": allowed or [],
            },
        )


class WorkflowStatusNotFoundError(PrathamError):
    """Raised when no workflow status can be resolved for an intake."""

    def __init__(self, intake_id: str):
        super().__init__(
            f"No workflow status found for intake {intake_id}",
            code="WORKFLOW_STATUS_NOT_FOUND",
        )


# ── Investigation Domain ────────────────────────────────────────────────────

class InvestigationNotFoundError(RecordNotFoundError):
    """Raised when an investigation recommendation cannot be found."""

    def __init__(self, identifier: str):
        super().__init__("Investigation", identifier)
        self.code = "INVESTIGATION_NOT_FOUND"


class InvalidInvestigationError(PrathamError):
    """Raised when an investigation type is not recognized by the registry."""

    def __init__(self, investigation_type: str):
        super().__init__(
            f"Unknown investigation type: {investigation_type}",
            code="INVALID_INVESTIGATION_TYPE",
            details={"investigation_type": investigation_type},
        )


# ── Evidence Domain ──────────────────────────────────────────────────────────

class EvidenceNotFoundError(RecordNotFoundError):
    """Raised when an evidence record cannot be found."""

    def __init__(self, evidence_id: str):
        super().__init__("Evidence", evidence_id)
        self.code = "EVIDENCE_NOT_FOUND"


class EvidenceUploadError(PrathamError):
    """Raised when evidence file upload fails."""

    def __init__(self, message: str, *, intake_id: str = "", file_name: str = ""):
        super().__init__(
            message,
            code="EVIDENCE_UPLOAD_FAILED",
            details={"intake_id": intake_id, "file_name": file_name},
        )


class EvidenceValidationError(PrathamError):
    """Raised when an uploaded evidence file fails validation."""

    def __init__(self, message: str, *, file_name: str = "", reason: str = ""):
        super().__init__(
            message,
            code="EVIDENCE_VALIDATION_FAILED",
            details={"file_name": file_name, "reason": reason},
        )


# ── Pipeline Domain ──────────────────────────────────────────────────────────

class PipelineStageError(PrathamError):
    """Raised when a pipeline stage operation fails."""

    def __init__(self, intake_id: str, stage: str, message: str):
        super().__init__(
            f"Pipeline stage '{stage}' failed for intake {intake_id}: {message}",
            code="PIPELINE_STAGE_ERROR",
            details={"intake_id": intake_id, "stage": stage},
        )


class PipelineTimeoutError(PrathamError):
    """Raised when a pipeline stage exceeds its timeout."""

    def __init__(self, intake_id: str, stage: str, timeout_seconds: int):
        super().__init__(
            f"Pipeline stage '{stage}' timed out after {timeout_seconds}s for intake {intake_id}",
            code="PIPELINE_TIMEOUT",
            details={"intake_id": intake_id, "stage": stage, "timeout_seconds": timeout_seconds},
        )


# ── Report Domain ────────────────────────────────────────────────────────────

class ReportGenerationError(PrathamError):
    """Raised when clinical report generation fails."""

    def __init__(self, intake_id: str, message: str):
        super().__init__(
            f"Report generation failed for intake {intake_id}: {message}",
            code="REPORT_GENERATION_FAILED",
            details={"intake_id": intake_id},
        )


class InsufficientDataError(PrathamError):
    """Raised when there is not enough data to generate a meaningful report."""

    def __init__(self, intake_id: str, missing: list[str] | None = None):
        missing_str = ", ".join(missing) if missing else "unknown"
        super().__init__(
            f"Insufficient data for report on intake {intake_id}: missing {missing_str}",
            code="INSUFFICIENT_DATA",
            details={"intake_id": intake_id, "missing": missing or []},
        )


# ── AI / Analysis Domain ────────────────────────────────────────────────────

class ModelNotLoadedError(PrathamError):
    """Raised when an ML model is requested but has not been loaded."""

    def __init__(self, model_name: str):
        super().__init__(
            f"ML model '{model_name}' is not loaded or unavailable",
            code="MODEL_NOT_LOADED",
            details={"model_name": model_name},
        )


class AnalysisError(PrathamError):
    """Raised when AI analysis fails."""

    def __init__(self, analysis_type: str, intake_id: str, message: str):
        super().__init__(
            f"{analysis_type} analysis failed for intake {intake_id}: {message}",
            code="ANALYSIS_FAILED",
            details={"analysis_type": analysis_type, "intake_id": intake_id},
        )


# ── Configuration Domain ────────────────────────────────────────────────────

class ConfigurationError(PrathamError):
    """Raised when a required configuration value is missing or invalid."""

    def __init__(self, variable: str, message: str = ""):
        detail = f": {message}" if message else ""
        super().__init__(
            f"Configuration error for '{variable}'{detail}",
            code="CONFIGURATION_ERROR",
            details={"variable": variable},
        )
