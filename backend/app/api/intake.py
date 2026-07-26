"""
POST /api/intake — Emergency patient intake endpoint
Writes patient, emergency_intake, vitals, and symptoms to Supabase.
"""

from __future__ import annotations

import logging
import uuid
from fastapi import APIRouter, HTTPException
from app.models.patient import EmergencyIntakeCreate, IntakeResponse
from app.db.supabase_client import supabase
from app.domains.ai.repository import nlp_repository, risk_scores_repository
from app.domains.triage.repository import (
    intake_repository,
    vitals_repository,
    symptoms_repository,
    patients_repository,
    preparation_alerts_repository,
)
from app.models.workflow import WorkflowStatus
from app.services.workflow_service import log_status_transition, update_workflow_status

logger = logging.getLogger(__name__)
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
                intake_repository.delete(intake_id)
            if patient_id:
                patients_repository.delete(patient_id)
        except Exception as cleanup_err:
            logger.warning("[PRATHAM] Rollback cleanup error (non-fatal): %s", cleanup_err)

    try:
        # Convert numeric age to valid DOB date string format YYYY-01-01 if needed
        from datetime import datetime
        dob = data.patient.date_of_birth
        if dob and dob.isdigit():
            age_int = int(dob)
            birth_year = datetime.now().year - age_int
            dob = f"{birth_year}-01-01"

        # 1. Insert patient
        patient_row = patients_repository.create({
            "first_name": data.patient.first_name,
            "last_name": data.patient.last_name,
            "date_of_birth": dob,
            "gender": data.patient.gender,
            "contact_number": data.patient.contact_number,
            "allergies": data.patient.allergies,
            "current_medications": data.patient.current_medications,
            "past_medical_history": data.patient.past_medical_history,
        })

        patient_id = patient_row["id"]

        # Determine initial status based on arrival type
        arr_type = data.arrival_type or "walk_in"
        if arr_type == "ambulance":
            initial_status = WorkflowStatus.EN_ROUTE.value
        elif arr_type == "referral":
            initial_status = WorkflowStatus.INTAKE_SUBMITTED.value
        else:
            initial_status = WorkflowStatus.ARRIVED.value

        # Generate a collision-safe Case ID (e.g. PRA-2026-6F24A1)
        uuid_hex = uuid.uuid4().hex[:6].upper()
        case_id = f"PRA-2026-{uuid_hex}"

        from app.services.workflow_service import to_db_status
        # 2. Insert emergency intake
        intake_row = intake_repository.create({
            "patient_id": patient_id,
            "case_id": case_id,
            "arrival_type": arr_type,
            "ambulance_eta": data.ambulance_eta,
            "emergency_description": data.emergency_description,
            "chief_complaint": data.chief_complaint,
            "status": to_db_status(initial_status),
        })

        intake_id = intake_row["id"]

        # Log initial status transition
        log_status_transition(
            intake_id=intake_id,
            old_status=None,
            new_status=initial_status,
            actor_type="Nurse",
            actor_name="Intake Nurse",
            reason="Patient registered at triage desk."
        )

        # For Walk-in, immediately transition Arrived -> Awaiting Doctor Approval
        if initial_status == WorkflowStatus.ARRIVED.value:
            update_workflow_status(
                intake_id=intake_id,
                new_status=WorkflowStatus.AWAITING_APPROVAL.value,
                actor_type="System",
                actor_name="Triage Pipeline",
                reason="Patient checked in for clinical triage."
            )

        # 3. Insert vitals
        try:
            vitals_row = vitals_repository.create({
                "patient_id": patient_id,
                "intake_id": intake_id,
                "heart_rate": data.vitals.heart_rate,
                "spo2": data.vitals.spo2,
                "bp_systolic": data.vitals.bp_systolic,
                "bp_diastolic": data.vitals.bp_diastolic,
                "temperature": data.vitals.temperature,
                "respiratory_rate": data.vitals.respiratory_rate,
            })
            vitals_saved = True
        except Exception as vitals_err:
            logger.error("[PRATHAM] Vitals insert failed - rolling back: %s", vitals_err)
            _rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Vitals save failed — entire intake rolled back. Error: {vitals_err}",
            )

        # 4. Insert symptoms
        try:
            symptoms_repository.create({
                "intake_id": intake_id,
                "chest_pain": data.symptoms.chest_pain,
                "breathlessness": data.symptoms.breathlessness,
                "trauma": data.symptoms.trauma,
                "bleeding": data.symptoms.bleeding,
                "unconsciousness": data.symptoms.unconsciousness,
                "neurological_symptoms": data.symptoms.neurological_symptoms,
            })
        except Exception as sym_err:
            logger.error("[PRATHAM] Symptoms insert failed - rolling back: %s", sym_err)
            # Also clean up vitals
            try:
                vitals_repository.delete_by_intake_id(intake_id)
            except Exception:
                pass
            _rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Symptoms save failed — entire intake rolled back. Error: {sym_err}",
            )

        # ── PIPELINE INITIALIZATION (mandatory — abort intake on failure) ────
        from app.services.pipeline_status_service import (
            initialize_pipeline,
            mark_running,
            mark_completed,
            mark_failed as pipeline_mark_failed,
        )

        try:
            initialize_pipeline(intake_id)
        except Exception as init_err:
            logger.error("[PRATHAM] Pipeline initialization failed - rolling back intake: %s", init_err)
            # Also clean up vitals + symptoms
            try:
                symptoms_repository.delete_by_intake_id(intake_id)
            except Exception:
                pass
            try:
                vitals_repository.delete_by_intake_id(intake_id)
            except Exception:
                pass
            _rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Pipeline initialization failed — intake aborted. Error: {init_err}",
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
        mark_running(intake_id, "nlp")
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

            nlp_repository.create(nlp_row)
            mark_completed(intake_id, "nlp")
        except Exception as nlp_err:
            logger.warning("[PRATHAM] NLP extraction failed (non-fatal): %s", nlp_err)
            # Record failure but do NOT re-raise — NLP uses graceful degradation
            try:
                supabase.table("pipeline_status").update({
                    "status": "failed",
                    "error_message": str(nlp_err),
                    "updated_at": __import__("datetime").datetime.now(
                        __import__("datetime").timezone.utc
                    ).isoformat(),
                }).eq("intake_id", intake_id).eq("stage", "nlp").execute()
            except Exception:
                pass
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
        mark_running(intake_id, "risk")
        try:
            risk_scores = calculate_risk_scores(vitals_dict, symptoms_dict, nlp_flags)

            risk_scores_repository.create({
                "intake_id": intake_id,
                **risk_scores,
            })

            # Update intake severity
            intake_repository.update_severity(intake_id, risk_scores["overall_severity"])

            mark_completed(intake_id, "risk")
        except Exception as risk_err:
            pipeline_mark_failed(intake_id, "risk", risk_err)

        # Step C: Preparation alerts
        alerts = generate_preparation_alerts(risk_scores)
        for alert_type in alerts:
            preparation_alerts_repository.create_alert(
                intake_id=intake_id,
                alert_type=alert_type,
                status="pending",
            )

        # Step D: Investigation recommendations (visit-type aware)
        from app.services.visit_classifier import classify_visit, get_routine_investigations
        
        visit_type = classify_visit(
            symptoms_dict, vitals_dict, risk_scores["overall_severity"], data.emergency_description, data.chief_complaint
        )
        
        if visit_type == "routine":
            investigations = get_routine_investigations()
        else:
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
        intake = intake_repository.get_by_id(intake_id)
        if not intake:
            raise HTTPException(status_code=404, detail="Intake not found")
        patient_id = intake.get("patient_id")

        # 2. Fetch patient
        patient = {}
        if patient_id:
            pat_row = patients_repository.get_by_id(patient_id)
            if pat_row:
                patient = pat_row

        # 3. Fetch vitals
        vitals = {}
        vitals_row = vitals_repository.get_by_intake_id(intake_id)
        if vitals_row:
            vitals = vitals_row

        # 4. Fetch symptoms
        symptoms = {}
        syms_row = symptoms_repository.get_by_intake_id(intake_id)
        if syms_row:
            symptoms = syms_row

        # 5. Fetch risk scores
        risk = {}
        risk_row = risk_scores_repository.get_by_intake_id(intake_id)
        if risk_row:
            risk = risk_row

        # 6. Fetch preparation alerts
        alerts_data = preparation_alerts_repository.get_by_intake_id(intake_id)

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
        try:
            bp_str = f"{int(bp_sys)}/{int(bp_dia)}" if bp_sys and bp_dia else "—"
        except (ValueError, TypeError):
            bp_str = "—"
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
            alert_type = a.get("alert_type") or "unknown"
            status = a.get("status") or ""
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
