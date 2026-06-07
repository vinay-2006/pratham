"""
POST /api/intake — Emergency patient intake endpoint
Writes patient, emergency_intake, vitals, and symptoms to Supabase.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.models.patient import EmergencyIntakeCreate, IntakeResponse
from app.db.supabase_client import supabase

router = APIRouter()


@router.post("/api/intake", response_model=IntakeResponse, status_code=201, tags=["Intake"])
async def create_intake(data: EmergencyIntakeCreate) -> IntakeResponse:
    """
    Accept a full emergency intake payload and persist to Supabase.

    Inserts records into: patients → emergency_intake → vitals → symptoms.
    Returns the generated patient_id and intake_id for downstream pipeline steps.
    """
    try:
        # 1. Insert patient
        patient_result = supabase.table("patients").insert({
            "first_name": data.patient.first_name,
            "last_name": data.patient.last_name,
            "date_of_birth": data.patient.date_of_birth,
            "gender": data.patient.gender,
            "contact_number": data.patient.contact_number,
            "allergies": data.patient.allergies,
            "current_medications": data.patient.current_medications,
            "past_medical_history": data.patient.past_medical_history,
        }).execute()

        if not patient_result.data:
            raise HTTPException(status_code=500, detail="Failed to insert patient record")

        patient_id: str = patient_result.data[0]["id"]

        # 2. Insert emergency intake
        intake_result = supabase.table("emergency_intake").insert({
            "patient_id": patient_id,
            "ambulance_eta": data.ambulance_eta,
            "emergency_description": data.emergency_description,
            "chief_complaint": data.chief_complaint,
            "status": "intake_pending",
        }).execute()

        if not intake_result.data:
            raise HTTPException(status_code=500, detail="Failed to insert emergency intake record")

        intake_id: str = intake_result.data[0]["id"]

        # 3. Insert vitals
        supabase.table("vitals").insert({
            "patient_id": patient_id,
            "intake_id": intake_id,
            "heart_rate": data.vitals.heart_rate,
            "spo2": data.vitals.spo2,
            "bp_systolic": data.vitals.bp_systolic,
            "bp_diastolic": data.vitals.bp_diastolic,
            "temperature": data.vitals.temperature,
            "respiratory_rate": data.vitals.respiratory_rate,
        }).execute()

        # 4. Insert symptoms
        supabase.table("symptoms").insert({
            "intake_id": intake_id,
            "chest_pain": data.symptoms.chest_pain,
            "breathlessness": data.symptoms.breathlessness,
            "trauma": data.symptoms.trauma,
            "bleeding": data.symptoms.bleeding,
            "unconsciousness": data.symptoms.unconsciousness,
            "neurological_symptoms": data.symptoms.neurological_symptoms,
        }).execute()

        # ── AUTOMATED CLINICAL PIPELINE ──────────────────────────────────────
        from app.services.nlp_service import extract_clinical_signals
        from app.services.risk_service import (
            calculate_risk_scores,
            generate_preparation_alerts,
        )
        from app.services.investigation_service import recommend_investigations

        symptoms_dict = data.symptoms.model_dump()
        vitals_dict = data.vitals.model_dump()

        # Step A: NLP extraction via Groq
        nlp_flags = extract_clinical_signals(
            emergency_description=data.emergency_description or "",
            symptoms=symptoms_dict,
            vitals=vitals_dict,
        )

        # Save NLP results
        nlp_row = {
            "intake_id": intake_id,
            "extracted_entities": nlp_flags.get("extracted_keywords", []),
            "raw_llm_output": nlp_flags,
        }
        for flag_key in (
            "head_trauma",
            "loss_of_consciousness",
            "neurological_risk_flag",
            "respiratory_distress",
            "cardiac_risk_flag",
        ):
            if flag_key in nlp_flags:
                nlp_row[flag_key] = nlp_flags[flag_key]

        supabase.table("nlp_extractions").insert(nlp_row).execute()

        # Step B: Risk scoring
        risk_scores = calculate_risk_scores(vitals_dict, symptoms_dict, nlp_flags)

        supabase.table("risk_scores").insert({
            "intake_id": intake_id,
            **risk_scores,
        }).execute()

        # Update intake severity
        supabase.table("emergency_intake").update({
            "severity_level": risk_scores["overall_severity"],
        }).eq("id", intake_id).execute()

        # Step C: Preparation alerts
        alerts = generate_preparation_alerts(risk_scores)
        for alert_type in alerts:
            supabase.table("preparation_alerts").insert({
                "intake_id": intake_id,
                "alert_type": alert_type,
                "status": "pending",
            }).execute()

        # Step D: Investigation recommendations
        investigations = recommend_investigations(
            symptoms_dict, vitals_dict, nlp_flags, risk_scores
        )
        for inv in investigations:
            supabase.table("investigation_recommendations").insert({
                "intake_id": intake_id,
                "investigation_type": inv,
                "status": "pending_approval",
            }).execute()

        # Return enriched response
        return IntakeResponse(
            patient_id=patient_id,
            intake_id=intake_id,
            status="intake_registered",
            severity=risk_scores["overall_severity"],
            risk_scores=risk_scores,
            investigations_recommended=investigations,
            preparation_alerts=alerts,
            nlp_summary=nlp_flags.get("clinical_summary", ""),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
