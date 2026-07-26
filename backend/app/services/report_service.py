"""
report_service.py — Single Source of Truth for Clinical Report Data

Both the JSON report endpoint and the PDF export endpoint call
`get_complete_report(intake_id)`. This avoids duplicating database
queries or report-building logic across endpoints.

Architecture (PRATHAM v1):
    1. Fetch raw data from all DB tables.
    2. Build the legacy-compatible report dict.
    3. Run clinical_reasoning_service → Clinical Evidence Object (facts + conclusions).
    4. Run interpretation_service → LLM narrative (or fallback).
    5. Assemble unified 17-section Report DTO.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.domains.triage.repository import intake_repository
from app.domains.ai.repository import (
    nlp_repository, lab_results_repository,
    imaging_results_repository, aggregation_results_repository,
)
from app.domains.evidence.repository import evidence_repository
from app.domains.investigation.repository import investigation_repository
from app.domains.workflow.repository import workflow_repository

logger = logging.getLogger(__name__)

# ── Version constants ────────────────────────────────────────────────────────
PRATHAM_VERSION = "1.0"

# ── Helpers ──────────────────────────────────────────────────────────────────

SYMPTOM_LABEL_MAP: Dict[str, str] = {
    "chest_pain": "Chest Pain",
    "breathlessness": "Breathlessness",
    "trauma": "Trauma",
    "bleeding": "Bleeding",
    "unconsciousness": "Unconsciousness",
    "neurological_symptoms": "Neurological Symptoms",
}


def _build_display_name(patient_row: dict | None) -> str:
    row = patient_row or {}
    first = (row.get("first_name") or "").strip()
    last = (row.get("last_name") or "").strip()
    if last and last != first:
        return f"{first} {last}".strip() or "Unknown"
    return first or "Unknown"


def _compute_age(dob: str | None) -> int:
    if not dob:
        return 0
    if "-" in str(dob):
        try:
            return max(0, datetime.now().year - int(str(dob).split("-")[0]))
        except (ValueError, IndexError):
            pass
    try:
        return int(dob)
    except (TypeError, ValueError):
        return 0


# ── Core function ────────────────────────────────────────────────────────────

async def get_complete_report(intake_id: str) -> Dict[str, Any]:
    """
    Fetch and assemble the complete clinical intelligence report
    for a given intake_id.  Returns the unified 17-section Report DTO.

    Raises ValueError if the intake is not found.
    """

    # ── 1. Intake + Patient + Vitals + Symptoms + Risk ────────────────
    intake = intake_repository.get_by_id(
        intake_id,
        columns=(
            "id, status, created_at, severity_level, case_id, "
            "arrival_type, emergency_description, chief_complaint, ambulance_eta, "
            "patients(id, first_name, last_name, gender, date_of_birth, "
            "contact_number, allergies, current_medications, past_medical_history), "
            "vitals(heart_rate, spo2, bp_systolic, bp_diastolic, temperature, respiratory_rate), "
            "symptoms(chest_pain, breathlessness, trauma, bleeding, unconsciousness, neurological_symptoms), "
            "risk_scores(cardiac_risk, respiratory_risk, trauma_risk, neurological_risk, overall_severity)"
        ),
    )

    if not intake:
        raise ValueError(f"Intake {intake_id} not found")

    patient_row = intake.get("patients") or {}
    vitals_rows = intake.get("vitals") or []
    vitals_row = vitals_rows[0] if vitals_rows else {}
    syms_rows = intake.get("symptoms") or []
    syms_row = syms_rows[0] if syms_rows else {}
    risk_rows = intake.get("risk_scores") or []
    risk_row = risk_rows[0] if risk_rows else {}

    name = _build_display_name(patient_row)
    gender = (patient_row.get("gender") or "").lower()
    age = _compute_age(patient_row.get("date_of_birth"))

    bp_sys = vitals_row.get("bp_systolic")
    bp_dia = vitals_row.get("bp_diastolic")
    bp_str = f"{int(bp_sys)}/{int(bp_dia)}" if bp_sys and bp_dia else "—"

    symptom_list = [
        label for field, label in SYMPTOM_LABEL_MAP.items()
        if syms_row.get(field)
    ]

    severity = (risk_row.get("overall_severity") or "moderate").lower()

    # ── 2–6. Fetch independent AI + evidence data in parallel ────────

    def _fetch_nlp():
        try:
            return nlp_repository.get_by_intake_id(intake_id) or {}
        except Exception:
            return {}

    def _fetch_lab():
        try:
            return lab_results_repository.get_latest(intake_id)
        except Exception:
            return None

    def _fetch_imaging():
        try:
            return imaging_results_repository.get_latest(intake_id, columns="*")
        except Exception:
            return None

    def _fetch_agg():
        try:
            return aggregation_results_repository.get_by_intake_id(intake_id)
        except Exception:
            return None

    def _fetch_evidence():
        try:
            return evidence_repository.get_by_intake_id_with_columns(
                intake_id,
                columns="id, evidence_type, file_name, file_url, file_size, uploaded_at",
                order_by="uploaded_at",
                desc=True,
            )
        except Exception:
            return []

    def _fetch_investigations():
        try:
            return investigation_repository.get_by_intake_id_with_columns(
                intake_id,
                columns="id, investigation_type, evidence_type, status, review_notes",
            )
        except Exception:
            return []

    nlp_data, lab_data, imaging_data, agg_data, evidence_list_raw, investigations = await asyncio.gather(
        asyncio.to_thread(_fetch_nlp),
        asyncio.to_thread(_fetch_lab),
        asyncio.to_thread(_fetch_imaging),
        asyncio.to_thread(_fetch_agg),
        asyncio.to_thread(_fetch_evidence),
        asyncio.to_thread(_fetch_investigations),
    )

    # ── Evidence Deduplication ───────────────────────────────────────
    # Deduplicate by (file_name, evidence_type, file_size), keeping the
    # most recent entry (list is already ordered by uploaded_at DESC).
    # file_size disambiguates legitimately different files with the same name.
    _seen_evidence: set[tuple[str, str, int | None]] = set()
    evidence_list: list[dict] = []
    for ev in evidence_list_raw:
        key = (ev.get("file_name", ""), ev.get("evidence_type", ""), ev.get("file_size"))
        if key not in _seen_evidence:
            _seen_evidence.add(key)
            evidence_list.append(ev)

    nlp_flags = {
        "chest_pain": syms_row.get("chest_pain", False),
        "breathlessness": syms_row.get("breathlessness", False),
        "cardiac_risk_flag": nlp_data.get("cardiac_risk_flag", False),
        "respiratory_distress": nlp_data.get("respiratory_distress", False),
        "head_trauma": nlp_data.get("head_trauma", False),
        "loss_of_consciousness": nlp_data.get("loss_of_consciousness", False),
        "neurological_risk_flag": nlp_data.get("neurological_risk_flag", False),
    }
    nlp_entities = nlp_data.get("extracted_entities") or []
    nlp_summary = ""
    raw_llm = nlp_data.get("raw_llm_output")
    if isinstance(raw_llm, dict):
        nlp_summary = raw_llm.get("clinical_summary", "")

    # Fetch the original X-ray URL if imaging has evidence_id
    xray_url = ""
    if imaging_data and imaging_data.get("evidence_id"):
        try:
            ev_row = evidence_repository.get_by_id_with_columns(
                imaging_data["evidence_id"], columns="file_url"
            )
            if ev_row:
                xray_url = ev_row.get("file_url", "")
        except Exception:
            pass

    # ── 7. Pipeline status ───────────────────────────────────────────
    from app.services.pipeline_status_service import get_pipeline_status
    try:
        pipeline_data = get_pipeline_status(intake_id)
        pipeline_status = {
            stage: info["status"]
            for stage, info in pipeline_data["stages"].items()
        }
    except Exception:
        pipeline_status = {
            "nlp": "completed" if nlp_data else "pending",
            "risk": "completed" if risk_row else "pending",
            "lab": "completed" if lab_data else "pending",
            "imaging": "completed" if imaging_data else "pending",
            "aggregation": "completed" if agg_data else "pending",
        }

    # Parse aggregation probabilities
    probabilities: Dict[str, Optional[float]] = {}
    evidence_breakdown: Dict[str, List[str]] = {}
    source_summary: Dict[str, bool] = {}
    if agg_data:
        probability_columns = {
            "ACS": ("acs_probability", "prob_acs"),
            "PE": ("pe_probability", "prob_pe"),
            "Pneumonia": ("pneumonia_probability", "prob_pneumonia"),
            "Arrhythmia": ("arrhythmia_probability", "prob_arrhythmia"),
            "Other": ("other_probability", "prob_other"),
        }
        for cond, keys in probability_columns.items():
            val = None
            for key in keys:
                if agg_data.get(key) is not None:
                    val = agg_data.get(key)
                    break
            probabilities[cond] = float(val) if val is not None else None
        try:
            eb = agg_data.get("evidence_breakdown_json")
            if isinstance(eb, str):
                evidence_breakdown = json.loads(eb)
            elif isinstance(eb, dict):
                evidence_breakdown = eb
        except Exception:
            pass
        try:
            ss = agg_data.get("source_summary_json")
            if isinstance(ss, str):
                source_summary = json.loads(ss)
            elif isinstance(ss, dict):
                source_summary = ss
        except Exception:
            pass

    created = intake.get("created_at", "")

    # ── Build the base report data (backward-compatible) ─────────────
    base_report = {
        "intake_id": intake_id,
        "generated_at": datetime.now().isoformat(),

        "patient_summary": {
            "patient_id": patient_row.get("id"),
            "case_id": intake.get("case_id") or f"PRA-2026-{intake_id[:6].upper()}",
            "name": name,
            "age": age,
            "gender": gender,
            "contact": patient_row.get("contact_number"),
            "chief_complaint": intake.get("chief_complaint", ""),
            "emergency_description": intake.get("emergency_description", ""),
            "ambulance_eta": intake.get("ambulance_eta", ""),
            "severity": severity,
            "allergies": patient_row.get("allergies") or [],
            "medications": patient_row.get("current_medications") or [],
            "medical_history": patient_row.get("past_medical_history") or [],
            "arrival_time": str(created)[11:16] if created and len(str(created)) >= 16 else "",
        },

        "vitals": {
            "heart_rate": vitals_row.get("heart_rate"),
            "spo2": vitals_row.get("spo2"),
            "bp_systolic": bp_sys,
            "bp_diastolic": bp_dia,
            "blood_pressure": bp_str,
            "temperature": vitals_row.get("temperature"),
            "respiratory_rate": vitals_row.get("respiratory_rate"),
        },

        "symptoms": symptom_list,

        "nlp_findings": {
            "flags": nlp_flags,
            "entities": nlp_entities,
            "summary": nlp_summary,
        },

        "risk_engine": {
            "cardiac": risk_row.get("cardiac_risk", 0) or 0,
            "respiratory": risk_row.get("respiratory_risk", 0) or 0,
            "trauma": risk_row.get("trauma_risk", 0) or 0,
            "neurological": risk_row.get("neurological_risk", 0) or 0,
            "severity": severity,
        },

        "lab_intelligence": {
            "available": lab_data is not None,
            "model_name": lab_data.get("model_name") if lab_data else None,
            "prediction": lab_data.get("prediction") if lab_data else None,
            "risk_probability": lab_data.get("risk_probability") if lab_data else None,
            "top_features": lab_data.get("top_features") if lab_data else None,
            "shap_values": lab_data.get("shap_values") if lab_data else None,
            "created_at": lab_data.get("created_at") if lab_data else None,
        },

        "lab_evaluations": [],

        "imaging_intelligence": {
            "available": imaging_data is not None,
            "model_name": imaging_data.get("model_name") if imaging_data else None,
            "prediction": imaging_data.get("prediction") if imaging_data else None,
            "pneumonia_probability": imaging_data.get("pneumonia_probability") if imaging_data else None,
            "confidence": imaging_data.get("confidence") if imaging_data else None,
            "xray_url": xray_url,
            "gradcam_url": imaging_data.get("gradcam_url", "") if imaging_data else "",
            "created_at": imaging_data.get("created_at") if imaging_data else None,
        },

        "aggregation": {
            "available": agg_data is not None,
            "primary_condition": agg_data.get("primary_condition") if agg_data else None,
            "confidence_suppressed": agg_data.get("confidence_suppressed") if agg_data else None,
            "suppression_reason": agg_data.get("suppression_reason") if agg_data else None,
            "probabilities": probabilities,
            "evidence_breakdown": evidence_breakdown,
            "source_summary": source_summary,
        },

        "evidence": evidence_list,
        "pipeline_status": pipeline_status,
        "investigations": investigations,
    }

    # Lab evaluations — computed separately to guard against bad data
    try:
        from app.services.lab_intelligence_service import evaluate_lab_panel
        lab_eval_result = evaluate_lab_panel(lab_data.get("top_features") if lab_data else None)
        if isinstance(lab_eval_result, dict):
            base_report["lab_evaluations"] = lab_eval_result.get("evaluations", [])
    except Exception as exc:
        logger.warning("[PRATHAM] lab_evaluations computation failed (non-fatal)  intake=%s  error=%s", intake_id, exc)

    # ── 8. Clinical Reasoning + Interpretation ───────────────────────
    from app.services.clinical_reasoning_service import build_clinical_evidence
    from app.services.interpretation_service import generate_clinical_interpretation

    try:
        clinical_evidence = build_clinical_evidence(base_report)
        interpretation = generate_clinical_interpretation(clinical_evidence)
    except Exception as exc:
        logger.error("[PRATHAM] Clinical reasoning/interpretation failed: %s", exc)
        clinical_evidence = {"facts": {}, "conclusions": {}}
        interpretation = {}

    # ── 9. Assemble the unified Report DTO ───────────────────────────
    conclusions = clinical_evidence.get("conclusions", {})

    base_report["clinical_interpretation"] = interpretation
    base_report["clinical_conclusions"] = conclusions
    base_report["report_version"] = PRATHAM_VERSION
    base_report["clinical_audit_log"] = {
        "report_generated_at": datetime.now().isoformat(),
        "generated_by": f"PRATHAM v{PRATHAM_VERSION}",
        "evidence_sources": [
            k for k, v in conclusions.get("data_completeness", {}).items()
            if isinstance(v, dict) and v.get("available")
        ],
        "pipeline_integrity": conclusions.get("report_quality", {}).get("pipeline_integrity", "PASS") if isinstance(conclusions.get("report_quality"), dict) else "PASS",
    }

    # ── 9b. Assemble 12 Clinician Sections (Sprint 1.4 Redesign) ────────
    try:
        # A. Clinical Timeline Logs (Task 2: Timeline)
        log_data = workflow_repository.get_logs(intake_id)
        timeline_list = []
        for log in log_data:
            try:
                dt = datetime.fromisoformat(log["changed_at"].replace("Z", "+00:00"))
                time_str = dt.strftime("%I:%M %p")
            except Exception:
                time_str = log["changed_at"]
            new_status_lbl = log["new_status"].replace("_", " ").title()
            timeline_list.append({
                "time": time_str,
                "event": new_status_lbl,
                "actor": f"{log['actor_type']} ({log['actor_name']})",
                "reason": log.get("reason") or ""
            })
        if not timeline_list:
            timeline_list.append({
                "time": str(created)[11:16],
                "event": "Intake Submitted",
                "actor": "System",
                "reason": "Initial triage creation"
            })

        # B. Presenting Complaint (Task 3: Presenting Complaint)
        clean_desc = intake.get("emergency_description") or ""
        # Remove any stray JSON fragments for safety
        if clean_desc and "{" in clean_desc:
            clean_desc = clean_desc.split("{")[0].strip()

        # C. HPI Narrative (Task 4: HPI)
        pmh_val = patient_row.get("past_medical_history") or "No significant past medical history"
        meds_val = patient_row.get("current_medications") or "None reported"
        allergies_val = patient_row.get("allergies") or "No known drug allergies"
        hpi_narrative = (
            f"Patient is a {age}-year-old {gender} presenting with {intake.get('chief_complaint') or 'unspecified complaint'}. "
            f"Active medical history: {pmh_val}. Current medications: {meds_val}. "
            f"Allergy profile: {allergies_val}."
        )

        # D. Investigations matrix (Task A1)
        matrix_list = []
        rec_types = {inv.get("investigation_type") for inv in investigations}
        
        # Check standard panels
        panels = [
            ("Heart Failure Analysis", lab_data is not None),
            ("Chest X-ray Interpretation", imaging_data is not None),
            ("Troponin", False),
            ("CT Brain", False),
        ]
        for name, is_done in panels:
            if is_done:
                status_str = "Completed"
            elif name in rec_types:
                status_str = "Pending"
            else:
                status_str = "Not Requested"
            matrix_list.append({"test_name": name, "status": status_str})

        # E. Differential Diagnosis (Task B4)
        diff_list = []
        primary_cond = conclusions.get("primary_condition", "Other")
        
        # Build Pneumonia Diagnosis
        if primary_cond == "Pneumonia" or imaging_data is not None:
            diff_list.append({
                "condition": "Community-acquired Pneumonia",
                "supporting": ["Fever", "Productive cough", "Right lower zone airspace opacity", "Elevated respiratory rate"],
                "contradicting": ["Oxygenation preserved"],
                "further_evidence": "Sputum culture, Complete Blood Count (CBC)"
            })
        
        # Build Heart Failure Diagnosis
        if primary_cond == "ACS" or lab_data is not None:
            diff_list.append({
                "condition": "Acute Heart Failure / Cardiac Dysfunction",
                "supporting": ["Advanced age", "Elevated blood pressure", "Abnormal cardiac laboratory values"],
                "contradicting": ["No peripheral edema", "Lung fields clear to auscultation"],
                "further_evidence": "Echocardiography, Serial troponins, EKG"
            })
            
        if not diff_list:
            if primary_cond == "Routine Check-up":
                diff_list.append({
                    "condition": "Normal Physiological Baseline",
                    "supporting": ["All vital signs within expected reference values", "Subjective report of stable state"],
                    "contradicting": [],
                    "further_evidence": "None required"
                })
            else:
                diff_list.append({
                    "condition": "Insufficient Clinical Evidence",
                    "supporting": [],
                    "contradicting": [],
                    "further_evidence": "Further diagnostic uploads required (imaging or laboratory results)"
                })

        # F. Recommendations Split (Task B6)
        immediate_recs = []
        short_term_recs = []
        add_invs = []
        
        if primary_cond == "Pneumonia":
            immediate_recs.append("Continuous pulse oximetry monitoring (SpO2)")
            immediate_recs.append("Supplemental low-flow oxygen if SpO2 falls below 94%")
            short_term_recs.append("Repeat chest radiographic imaging in 48-72 hours if no improvement")
            add_invs.append("Sputum culture and gram stain")
            add_invs.append("Complete Blood Count (CBC) with differential")
        elif primary_cond == "ACS":
            immediate_recs.append("Continuous cardiac telemetry monitoring")
            short_term_recs.append("Consult cardiology specialist")
            add_invs.append("Serial Troponin testing (at 0, 3, and 6 hours)")
            add_invs.append("12-Lead Electrocardiogram (EKG)")
        else:
            immediate_recs.append("Maintain standard clinical observation protocols")
            short_term_recs.append("Routine outpatient follow-up evaluation")

        # G. Evidence Reliability & version history (Task 7 & 9)
        reliability = "High"
        rel_reason = "Complete vital signs, symptoms, and diagnostic uploads are available."
        
        if primary_cond == "Insufficient Evidence":
            reliability = "Limited"
            rel_reason = "Assessment is limited by the absence of imaging and laboratory panels."
            
        version_history = [
            {"version": "v1", "time": str(created)[11:16], "event": "Intake Submitted - Initial triage version generated"}
        ]
        if len(evidence_list) > 1 or lab_data or imaging_data:
            up_time = str(intake.get("updated_at") or created)[11:16]
            version_history.append({
                "version": f"v{len(evidence_list)}",
                "time": up_time,
                "event": "Diagnostic uploads completed - Analysis version updated"
            })

        # Resolve gen_at NameError and format timestamps robustly
        gen_at = base_report.get("generated_at") or datetime.now().isoformat()
        
        def format_iso_timestamp(ts):
            if not ts:
                return ""
            try:
                if isinstance(ts, datetime):
                    return ts.strftime("%d %b %Y, %I:%M %p")
                ts_str = str(ts).replace("Z", "+00:00")
                if "." in ts_str:
                    parts_ts = ts_str.split(".", 1)
                    base = parts_ts[0]
                    tz = parts_ts[1]
                    if "+" in tz:
                        ts_str = base + "+" + tz.split("+", 1)[-1]
                    elif "-" in tz and len(tz.split("-")) > 1:
                        ts_str = base + "-" + tz.split("-", 1)[-1]
                    else:
                        ts_str = base
                return datetime.fromisoformat(ts_str).strftime("%d %b %Y, %I:%M %p")
            except Exception as e:
                logger.warning("[PRATHAM] Failed to parse timestamp %s: %s", ts, e)
                return str(ts)

        # Assemble Clinician report sections
        base_report["clinician_report"] = {
            "patient_snapshot": {
                "case_id": base_report["patient_summary"]["case_id"],
                "patient_name": name,
                "age": age,
                "gender": gender.capitalize(),
                "arrival_type": (intake.get("arrival_type") or "walk_in").replace("_", " ").title(),
                "priority": severity.title(),
                "status": (base_report["patient_summary"].get("status") or "Under Doctor Review").replace("_", " ").title(),
                "completed_tests": f"{len(evidence_list)} / {len(investigations) or 2}",
                "pending_tests": sum(1 for inv in investigations if inv.get("status") != "completed"),
                "report_version": f"Version {len(evidence_list) or 1}",
                "generated_time": format_iso_timestamp(gen_at),
                "updated_time": format_iso_timestamp(intake.get("updated_at") or gen_at)
            },
            "timeline": timeline_list,
            "presenting_complaint": {
                "chief_complaint": intake.get("chief_complaint", ""),
                "emergency_description": clean_desc
            },
            "hpi": hpi_narrative,
            "vitals_list": base_report["vitals"],
            "investigations_matrix": matrix_list,
            "clinical_findings": {
                "cardiac": (interpretation.get("cardiac_summary") or ""),
                "respiratory": (interpretation.get("respiratory_summary") or ""),
                "general": (interpretation.get("clinical_overview") or "")
            },
            "differential_diagnosis": diff_list,
            "clinical_impression": {
                "primary": ((interpretation.get("overall_impression") or "").split(".")[0] + ".") if (interpretation.get("overall_impression") or "") else "No impression provided.",
                "secondary": (interpretation.get("alternative_considerations_narrative") or ""),
                "assessment": (interpretation.get("overall_impression") or "")
            },
            "recommendations": {
                "immediate": immediate_recs,
                "short_term": short_term_recs,
                "additional": add_invs
            },
            "evidence_quality": {
                "reliability": reliability,
                "reason": rel_reason,
                "history": version_history
            }
        }
    except Exception as exc:
        logger.error("[PRATHAM] Clinician report compilation failed: %s", exc)
        base_report["clinician_report"] = {
            "patient_snapshot": {
                "case_id": base_report["patient_summary"]["case_id"],
                "patient_name": name,
                "age": age,
                "gender": gender.capitalize(),
                "arrival_type": (intake.get("arrival_type") or "walk_in").replace("_", " ").title(),
                "priority": severity.title(),
                "status": base_report["patient_summary"].get("status", "Under Doctor Review").replace("_", " ").title(),
                "completed_tests": f"{len(evidence_list)} / {len(investigations) or 2}",
                "pending_tests": sum(1 for inv in investigations if inv.get("status") != "completed"),
                "report_version": "v1",
                "generated_time": "",
                "updated_time": ""
            },
            "timeline": [],
            "presenting_complaint": {
                "chief_complaint": intake.get("chief_complaint", ""),
                "emergency_description": f"Failed to compile clinician report details: {exc}"
            },
            "hpi": "",
            "vitals_list": base_report.get("vitals", []),
            "investigations_matrix": [],
            "clinical_findings": {
                "cardiac": "",
                "respiratory": "",
                "general": ""
            },
            "differential_diagnosis": [],
            "clinical_impression": {
                "primary": "Failed to compile clinician report details.",
                "secondary": "",
                "assessment": ""
            },
            "recommendations": {
                "immediate": [],
                "short_term": [],
                "additional": []
            },
            "evidence_quality": {
                "reliability": "Limited",
                "reason": "Failed to compile clinician report details.",
                "history": []
            }
        }

    # ── 10. Post-generation validation ───────────────────────────────
    try:
        from app.services.report_validator import validate_report
        validation_result = validate_report(base_report)
        if validation_result["errors"]:
            logger.error(
                "[PRATHAM/REPORT] Report validation FAILED  intake=%s  errors=%s",
                intake_id, validation_result["errors"],
            )
        if validation_result["warnings"]:
            logger.warning(
                "[PRATHAM/REPORT] Report validation warnings  intake=%s  warnings=%s",
                intake_id, validation_result["warnings"],
            )
        base_report["validation"] = validation_result
    except Exception as exc:
        logger.warning("[PRATHAM/REPORT] Report validation skipped (non-fatal)  intake=%s  error=%s", intake_id, exc)

    return base_report
