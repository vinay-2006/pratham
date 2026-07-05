"""
PRATHAM Structured Logging Service
Standardizes system observability with unified log context (request ID, patient, stage, latency).
"""

import json
import logging
import sys
import time
import uuid
from typing import Optional

# Setup standard logger
logger = logging.getLogger("pratham")
logger.setLevel(logging.INFO)

# Create a clean handler writing JSON format to stdout for easy production ingestion
class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        # Inject standard telemetry attributes if present
        for field in ["request_id", "patient_id", "pipeline_stage", "duration_ms"]:
            if hasattr(record, field):
                log_data[field] = getattr(record, field)
        return json.dumps(log_data)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(StructuredFormatter())
logger.addHandler(handler)

def log_event(
    message: str,
    level: int = logging.INFO,
    request_id: Optional[str] = None,
    patient_id: Optional[str] = None,
    pipeline_stage: Optional[str] = None,
    duration_ms: Optional[float] = None,
):
    """Log a structured clinical or system event."""
    extra = {
        "request_id": request_id or str(uuid.uuid4()),
        "patient_id": patient_id or "N/A",
        "pipeline_stage": pipeline_stage or "SYSTEM",
        "duration_ms": int(duration_ms) if duration_ms is not None else None,
    }
    logger.log(level, message, extra=extra)
