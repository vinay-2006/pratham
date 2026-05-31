"""
NLP Service — Stub for clinical NLP extraction.

TODO: Integrate Groq LLM API or a BioNLP model for entity extraction.
"""

from __future__ import annotations


class NLPService:
    """Extracts structured clinical entities from free-text notes."""

    async def extract_entities(self, clinical_text: str) -> dict[str, list[str]]:
        """
        Stub: Extract symptoms, diagnoses, medications, and allergies.

        Args:
            clinical_text: Raw clinical note or patient-reported history.

        Returns:
            Dictionary keyed by entity type with lists of extracted terms.
        """
        # TODO: Call Groq API with a clinical NER prompt
        return {
            "symptoms": [],
            "diagnoses": [],
            "medications": [],
            "allergies": [],
        }
