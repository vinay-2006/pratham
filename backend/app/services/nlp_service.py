

"""
NLP Service — Groq-powered clinical signal extraction.

Calls Groq API with Mistral to extract structured clinical risk flags
from emergency intake free text, symptoms, and vitals.
"""

from __future__ import annotations

import json
import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def extract_clinical_signals(
    emergency_description: str, symptoms: dict, vitals: dict
) -> dict:
    """
    Call Groq API with Mistral to extract clinical risk flags
    from the emergency description + symptoms + vitals.
    Returns structured JSON with clinical flags.
    """
    prompt = (
        "You are a clinical NLP assistant for an emergency department system.\n\n"
        "Analyze this emergency intake and extract clinical risk flags.\n"
        "Return ONLY a valid JSON object. No explanation. No markdown. Just JSON.\n\n"
        f"Emergency Description: {emergency_description}\n\n"
        f"Symptoms present: {json.dumps(symptoms)}\n\n"
        f"Vitals: {json.dumps(vitals)}\n\n"
        "Return this exact JSON structure:\n"
        "{\n"
        '  "head_trauma": true/false,\n'
        '  "loss_of_consciousness": true/false,\n'
        '  "neurological_risk_flag": true/false,\n'
        '  "respiratory_distress": true/false,\n'
        '  "cardiac_risk_flag": true/false,\n'
        '  "trauma_present": true/false,\n'
        '  "hemorrhage_risk": true/false,\n'
        '  "extracted_keywords": ["keyword1", "keyword2"],\n'
        '  "clinical_summary": "one sentence summary of the emergency"\n'
        "}"
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=500,
    )

    raw = response.choices[0].message.content.strip()

    # Strip <think>...</think> reasoning tags (qwen3 models)
    import re
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

    # Strip markdown fences if present
    if "```" in raw:
        parts = raw.split("```")
        for part in parts:
            cleaned = part.strip()
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()
            if cleaned.startswith("{"):
                raw = cleaned
                break

    # Try to extract first JSON object with regex as final fallback
    if not raw.startswith("{"):
        match = re.search(r"\{[\s\S]*\}", raw)
        if match:
            raw = match.group(0)

    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails — derive from raw symptom data
        return {
            "head_trauma": False,
            "loss_of_consciousness": symptoms.get("unconsciousness", False),
            "neurological_risk_flag": symptoms.get("neurological_symptoms", False),
            "respiratory_distress": symptoms.get("breathlessness", False),
            "cardiac_risk_flag": symptoms.get("chest_pain", False),
            "trauma_present": symptoms.get("trauma", False),
            "hemorrhage_risk": symptoms.get("bleeding", False),
            "extracted_keywords": [],
            "clinical_summary": "Automated extraction failed — manual review required",
        }
