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
    If any insert fails, previously created records are cleaned up (compensating rollback).
    """
    patient_id: str | None = None
    intake_id: str | None = None

    def _rollback():
        """Delete any records that were partially created."""
        try:
            if intake_id:
                supabase.table("emergency_intake").delete().eq("id", intake_id).execute()
            if patient_id:
                supabase.table("patients").delete().eq("id", patient_id).execute()
        except Exception as cleanup_err:
            print(f"[PRATHAM] Rollback cleanup error (non-fatal): {cleanup_err}")

    try:
        # Convert numeric age to valid DOB date string format YYYY-01-01 if needed
        from datetime import datetime
        dob = data.patient.date_of_birth
        if dob and dob.isdigit():
            age_int = int(dob)
            birth_year = datetime.now().year - age_int
            dob = f"{birth_year}-01-01"

        # 1. Insert patient
        patient_result = supabase.table("patients").insert({
            "first_name": data.patient.first_name,
            "last_name": data.patient.last_name,
            "date_of_birth": dob,
            "gender": data.patient.gender,
            "contact_number": data.patient.contact_number,
            "allergies": data.patient.allergies,
            "current_medications": data.patient.current_medications,
            "past_medical_history": data.patient.past_medical_history,
        }).execute()

        if not patient_result.data:
            raise HTTPException(status_code=500, detail="Failed to insert patient record")

        patient_id = patient_result.data[0]["id"]

        # 2. Insert emergency intake
        intake_result = supabase.table("emergency_intake").insert({
            "patient_id": patient_id,
            "ambulance_eta": data.ambulance_eta,
            "emergency_description": data.emergency_description,
            "chief_complaint": data.chief_complaint,
            "status": "intake_pending",
        }).execute()

        if not intake_result.data:
            _rollback()
            raise HTTPException(status_code=500, detail="Failed to insert emergency intake record")

        intake_id = intake_result.data[0]["id"]

        # 3. Insert vitals
        try:
            vitals_result = supabase.table("vitals").insert({
                "patient_id": patient_id,
                "intake_id": intake_id,
                "heart_rate": data.vitals.heart_rate,
                "spo2": data.vitals.spo2,
                "bp_systolic": data.vitals.bp_systolic,
                "bp_diastolic": data.vitals.bp_diastolic,
                "temperature": data.vitals.temperature,
                "respiratory_rate": data.vitals.respiratory_rate,
            }).execute()
            if not vitals_result.data:
                raise Exception("Vitals insert returned empty data")
            vitals_saved = True
        except Exception as vitals_err:
            print(f"[PRATHAM] Vitals insert failed — rolling back: {vitals_err}")
            _rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Vitals save failed — entire intake rolled back. Error: {vitals_err}",
            )

        # 4. Insert symptoms
        try:
            supabase.table("symptoms").insert({
                "intake_id": intake_id,
                "chest_pain": data.symptoms.chest_pain,
                "breathlessness": data.symptoms.breathlessness,
                "trauma": data.symptoms.trauma,
                "bleeding": data.symptoms.bleeding,
                "unconsciousness": data.symptoms.unconsciousness,
                "neurological_symptoms": data.symptoms.neurological_symptoms,
            }).execute()
        except Exception as sym_err:
            print(f"[PRATHAM] Symptoms insert failed — rolling back: {sym_err}")
            # Also clean up vitals
            try:
                supabase.table("vitals").delete().eq("intake_id", intake_id).execute()
            except Exception:
                pass
            _rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Symptoms save failed — entire intake rolled back. Error: {sym_err}",
            )

        # ── AUTOMATED CLINICAL PIPELINE ──────────────────────────────────────
        from app.services.risk_service import (
            calculate_risk_scores,
            generate_preparation_alerts,
        )
        from app.services.investigation_service import recommend_investigations

        symptoms_dict = data.symptoms.model_dump()
        vitals_dict = data.vitals.model_dump()

        # Step A: NLP extraction via Groq (graceful degradation if unavailable)
        nlp_flags: dict = {}
        nlp_summary = ""
        try:
            from app.services.nlp_service import extract_clinical_signals
            nlp_flags = extract_clinical_signals(
                emergency_description=data.emergency_description or "",
                symptoms=symptoms_dict,
                vitals=vitals_dict,
            )
            nlp_summary = nlp_flags.get("clinical_summary", "")

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
        except Exception as nlp_err:
            print(f"[PRATHAM] NLP extraction failed (non-fatal): {nlp_err}")
            # Fallback: derive flags directly from symptom booleans
            nlp_flags = {
                "head_trauma": False,
                "loss_of_consciousness": symptoms_dict.get("unconsciousness", False),
                "neurological_risk_flag": symptoms_dict.get("neurological_symptoms", False),
                "respiratory_distress": symptoms_dict.get("breathlessness", False),
                "cardiac_risk_flag": symptoms_dict.get("chest_pain", False),
                "trauma_present": symptoms_dict.get("trauma", False),
                "hemorrhage_risk": symptoms_dict.get("bleeding", False),
                "extracted_keywords": [],
                "clinical_summary": "NLP extraction unavailable — fallback flags used.",
            }
            nlp_summary = nlp_flags["clinical_summary"]

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

        # Step D: Investigation recommendations (only if vitals exist)
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
            nlp_summary=nlp_summary,
        )

    except HTTPException:
        raise
    except Exception as e:
        _rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/intake/{intake_id}", tags=["Intake"])
async def get_intake(intake_id: str):
    """
    Retrieve full details for an emergency intake by ID, mapped to the PatientCase structure
    expected by the frontend workstation.
    """
    try:
        # 1. Fetch intake
        intake_res = supabase.table("emergency_intake").select("*").eq("id", intake_id).execute()
        if not intake_res.data:
            raise HTTPException(status_code=404, detail="Intake not found")
        intake = intake_res.data[0]
        patient_id = intake.get("patient_id")

        # 2. Fetch patient
        patient = {}
        if patient_id:
            pat_res = supabase.table("patients").select("*").eq("id", patient_id).execute()
            if pat_res.data:
                patient = pat_res.data[0]

        # 3. Fetch vitals
        vitals = {}
        vitals_res = supabase.table("vitals").select("*").eq("intake_id", intake_id).execute()
        if vitals_res.data:
            vitals = vitals_res.data[0]

        # 4. Fetch symptoms
        symptoms = {}
        syms_res = supabase.table("symptoms").select("*").eq("intake_id", intake_id).execute()
        if syms_res.data:
            symptoms = syms_res.data[0]

        # 5. Fetch risk scores
        risk = {}
        risk_res = supabase.table("risk_scores").select("*").eq("intake_id", intake_id).execute()
        if risk_res.data:
            risk = risk_res.data[0]

        # 6. Fetch preparation alerts
        alerts_res = supabase.table("preparation_alerts").select("*").eq("intake_id", intake_id).execute()
        alerts_data = alerts_res.data or []

        # 7. Fetch investigation recommendations
        inv_res = supabase.table("investigation_recommendations").select("*").eq("intake_id", intake_id).execute()
        inv_data = inv_res.data or []

        # Map to PatientCase structure
        first = patient.get("first_name", "")
        last = patient.get("last_name", "")
        name = f"Patient {first} {last}".strip() or "Unknown Patient"

        # Parse age from date_of_birth
        from datetime import datetime
        dob = patient.get("date_of_birth")
        age = 0
        if dob:
            if "-" in dob:
                try:
                    birth_year = int(dob.split("-")[0])
                    age = datetime.now().year - birth_year
                except Exception:
                    pass
            else:
                try:
                    age = int(dob)
                except ValueError:
                    pass

        gender = (patient.get("gender") or "").lower()
        sex = "M" if gender == "male" else "F"

        # Vitals formatting
        hr = vitals.get("heart_rate")
        spo2 = vitals.get("spo2")
        bp_sys = vitals.get("bp_systolic")
        bp_dia = vitals.get("bp_diastolic")
        bp_str = f"{int(bp_sys)}/{int(bp_dia)}" if bp_sys and bp_dia else "—"
        rr = vitals.get("respiratory_rate")
        temp = vitals.get("temperature")

        # Active symptoms
        SYMPTOM_LABEL_MAP = {
            "chest_pain": "Chest Pain",
            "breathlessness": "Breathlessness",
            "trauma": "Trauma",
            "bleeding": "Bleeding",
            "unconsciousness": "Unconsciousness",
            "neurological_symptoms": "Neurological Symptoms",
        }
        symptom_labels = []
        for field, label in SYMPTOM_LABEL_MAP.items():
            if symptoms.get(field):
                symptom_labels.append(label)

        # Alerts mapping
        prep_alerts = []
        for a in alerts_data:
            alert_type = a.get("alert_type")
            status = a.get("status")
            prep_alerts.append({
                "label": alert_type.replace("_", " ").title(),
                "active": status == "pending" or status == "active",
                "note": f"Alert automatically triggered. Status: {status}."
            })

        # If no alerts found but severity is high/critical, add some sensible defaults
        if not prep_alerts:
            severity = (risk.get("overall_severity") or "").lower()
            if severity in ("critical", "high"):
                prep_alerts = [
                    {"label": "ICU bed standby", "active": True, "note": "Priority alert triggered"},
                    {"label": "Oxygen prep", "active": True, "note": "Prepare clinical O2 line"},
                ]

        # Recommended investigations mapping
        investigations = []
        for inv in inv_data:
            inv_status = "Pending"
            status_lower = (inv.get("status") or "").lower()
            if status_lower == "approved":
                inv_status = "Confirmed"
            elif status_lower in ("running", "in_progress"):
                inv_status = "In progress"

            investigations.append({
                "name": inv.get("investigation_type"),
                "status": inv_status,
                "rationale": "Recommended based on triage profile."
            })

        # Risk Estimates mapping
        cardiac = risk.get("cardiac_risk", 0) or 0
        resp = risk.get("respiratory_risk", 0) or 0
        trauma = risk.get("trauma_risk", 0) or 0
        neuro = risk.get("neurological_risk", 0) or 0

        severity = (risk.get("overall_severity") or "moderate").lower()

        risk_estimates = [
            {"label": "Cardiac Risk", "value": cardiac, "severity": "high" if cardiac >= 50 else ("moderate" if cardiac >= 20 else "low"), "note": "Derived cardiac score."},
            {"label": "Respiratory Risk", "value": resp, "severity": "high" if resp >= 50 else ("moderate" if resp >= 20 else "low"), "note": "Derived respiratory score."},
            {"label": "Trauma Risk", "value": trauma, "severity": "high" if trauma >= 50 else ("moderate" if trauma >= 20 else "low"), "note": "Derived trauma score."},
            {"label": "Neurological Risk", "value": neuro, "severity": "high" if neuro >= 50 else ("moderate" if neuro >= 20 else "low"), "note": "Derived neurological score."},
        ]

        # ETA & arrival
        eta = intake.get("ambulance_eta")
        eta_str = f"{eta} min" if eta else "—"
        created = intake.get("created_at", "")
        arrival_str = ""
        if created and len(created) >= 16:
            arrival_str = created[11:16]

        # Evidence completeness — count available data signals
        _evidence_signals = 0
        if hr: _evidence_signals += 1
        if spo2: _evidence_signals += 1
        if bp_sys and bp_dia: _evidence_signals += 1
        if rr: _evidence_signals += 1
        if temp: _evidence_signals += 1
        if symptom_labels: _evidence_signals += 1
        if risk: _evidence_signals += 1
        if intake.get("emergency_description"): _evidence_signals += 1
        if any(inv.get("status", "").lower() in ("approved", "running", "in_progress", "confirmed") for inv in inv_data): _evidence_signals += 1

        if _evidence_signals >= 7:
            evidence_completeness = "HIGH"
        elif _evidence_signals >= 4:
            evidence_completeness = "MODERATE"
        else:
            evidence_completeness = "LOW"

        # Return full PatientCase equivalent
        return {
            "id": intake_id,
            "patient": {
                "name": name,
                "age": age,
                "sex": sex,
                "arrival": arrival_str,
                "eta": eta_str
            },
            "vitals": {
                "heartRate": hr or 0,
                "spo2": spo2 or 0,
                "bloodPressure": bp_str,
                "respiratoryRate": rr or 0,
                "temperature": temp or 0
            },
            "symptoms": symptom_labels,
            "freeText": intake.get("emergency_description") or "",
            "evidenceCompleteness": evidence_completeness,
            "overallSeverity": severity,
            "priorityLabel": f"{severity.title()} Priority" if severity else "Moderate Triage",
            "operationalRiskEstimates": risk_estimates,
            "preparationAlerts": prep_alerts,
            "recommendedInvestigations": investigations,
            "evidence": {
                "available": [
                    {"id": "ev-1", "label": "Clinical Vitals", "finding": f"HR {hr}, SpO2 {spo2}", "source": "Nurse Intake", "contribution": "Primary baseline", "weight": severity}
                ],
                "missing": []
            },
            "assistiveDifferential": [
                {"condition": "Acute presenting condition", "probability": 40, "aiConfidence": "Moderate", "contributingEvidence": symptom_labels, "uncertainty": "Requires further investigations."}
            ],
            "imaging": {
                "studyType": "Chest X-ray",
                "pneumoniaProbability": 0,
                "aiConfidence": "Low",
                "suppressed": True,
                "heatmapHotspots": [],
                "interpretation": "No imaging performed."
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
