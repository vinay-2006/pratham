"""
POST /nlp/extract — Clinical NLP extraction endpoint (stub)
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class NLPRequest(BaseModel):
    patient_id: uuid.UUID
    clinical_text: str = Field(..., min_length=1, max_length=5000)


class ExtractedEntity(BaseModel):
    entity_type: str  # e.g. "symptom", "diagnosis", "medication", "allergy"
    text: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    normalized_term: str | None = None


class NLPResponse(BaseModel):
    patient_id: uuid.UUID
    entities: list[ExtractedEntity]
    summary: str
    processing_time_ms: int


@router.post("/extract", response_model=NLPResponse)
async def extract_nlp(payload: NLPRequest) -> NLPResponse:
    """
    Extract structured clinical entities from free-text clinical notes.

    Stub response — NLP model integration (e.g. Groq/BioNLP) pending.
    """
    return NLPResponse(
        patient_id=payload.patient_id,
        entities=[
            ExtractedEntity(
                entity_type="symptom",
                text="chest pain",
                confidence=0.95,
                normalized_term="Chest pain (finding)",
            ),
            ExtractedEntity(
                entity_type="symptom",
                text="shortness of breath",
                confidence=0.91,
                normalized_term="Dyspnoea (finding)",
            ),
        ],
        summary="Stub: patient presents with chest pain and dyspnoea.",
        processing_time_ms=0,
    )
