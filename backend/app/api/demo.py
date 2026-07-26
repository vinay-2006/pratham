"""
PRATHAM Demo Management Router
Handles database resetting, demo data loading, and case registry safely under ENABLE_DEMO_MODE guard.
"""

import os
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List

from app.db.supabase_client import supabase
from app.api.demo_patients import DEMO_CASES

router = APIRouter()


def check_demo_mode():
    """Security guard verifying ENABLE_DEMO_MODE=true environment configuration."""
    if os.getenv("ENABLE_DEMO_MODE") != "true":
        raise HTTPException(
            status_code=403,
            detail="Demo mode disabled. Set ENABLE_DEMO_MODE=true in your environment to enable."
        )


@router.get("/cases", dependencies=[Depends(check_demo_mode)])
async def get_demo_cases() -> Dict[str, Any]:
    """Retrieve metadata of the 10 portfolio demo cases."""
    return {
        "cases": [
            {
                "id": key,
                "name": case["name"],
                "age": case["age"],
                "sex": case["sex"],
                "chief_complaint": case["chief_complaint"]
            }
            for key, case in DEMO_CASES.items()
        ]
    }


@router.post("/reset", dependencies=[Depends(check_demo_mode)])
async def reset_demo_database() -> Dict[str, Any]:
    """Relational SQL purge of all demo intake data, maintaining DB schema integrity."""
    try:
        # Purge tables in correct dependency order to prevent FK violations
        tables_to_purge = [
            "pipeline_status",
            "investigation_recommendations",
            "risk_scores",
            "preparation_alerts",
            "nlp_extractions",
            "symptoms",
            "vitals",
            "evidence",
            "lab_results",
            "imaging_results",
            "aggregation_results",
            "emergency_intake",
            "patients"
        ]

        purged_counts = {}
        for table in tables_to_purge:
            # Execute delete on all records
            res = supabase.table(table).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            purged_counts[table] = len(res.data) if res.data else 0

        return {
            "status": "success",
            "message": "Demo tables purged successfully.",
            "purged_records": purged_counts
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Database purge failed: {exc}"
        )


@router.post("/load/{case_id}", dependencies=[Depends(check_demo_mode)])
async def load_demo_case(case_id: str) -> Dict[str, Any]:
    """Insert complete telemetry records for selected demo case directly into Supabase."""
    if case_id not in DEMO_CASES:
        raise HTTPException(status_code=404, detail=f"Demo case {case_id} not found.")

    case = DEMO_CASES[case_id]

    try:
        # 1. Create Patient
        p_res = supabase.table("patients").insert({
            "first_name": case["name"].split(" ")[0],
            "last_name": case["name"].split(" ")[-1],
            "gender": case["sex"],
            "date_of_birth": "1980-01-01",
        }).execute()
        if not p_res.data:
            raise HTTPException(status_code=500, detail="Failed to create demo patient — insert returned no data")
        patient_id = p_res.data[0]["id"]

        # 2. Create Intake
        i_res = supabase.table("emergency_intake").insert({
            "patient_id": patient_id,
            "chief_complaint": case["chief_complaint"],
            "emergency_description": f"Demo presentation loading case: {case['name']}",
            "status": "intake_completed",
            "severity_level": case["vitals"].get("spo2", 98) < 90 and "CRITICAL" or "MODERATE"
        }).execute()
        if not i_res.data:
            raise HTTPException(status_code=500, detail="Failed to create demo intake — insert returned no data")
        intake_id = i_res.data[0]["id"]

        # 3. Create Vitals
        v_data = case["vitals"]
        supabase.table("vitals").insert({
            "patient_id": patient_id,
            "intake_id": intake_id,
            "heart_rate": v_data["hr"],
            "bp_systolic": int(v_data["bp"].split("/")[0]),
            "bp_diastolic": int(v_data["bp"].split("/")[1]),
            "spo2": v_data["spo2"],
            "respiratory_rate": v_data["rr"],
            "temperature": v_data["temp"],
        }).execute()

        # 4. Create Symptoms
        s_data = case["symptoms"]
        supabase.table("symptoms").insert({
            "intake_id": intake_id,
            "chest_pain": s_data.get("chest_pain", False),
            "breathlessness": s_data.get("breathlessness", False),
            "trauma": s_data.get("trauma", False),
            "bleeding": s_data.get("bleeding", False),
            "unconsciousness": s_data.get("unconsciousness", False),
            "neurological_symptoms": s_data.get("neurological", False),
        }).execute()

        # 5. Create pipeline stages
        stages = ["nlp", "risk", "lab", "imaging", "aggregation"]
        for stage in stages:
            supabase.table("pipeline_status").insert({
                "intake_id": intake_id,
                "stage": stage,
                "status": "completed",
                "attempt_count": 1,
                "duration_ms": 500
            }).execute()

        return {
            "status": "success",
            "intake_id": intake_id,
            "patient_id": patient_id,
            "message": f"Successfully loaded demo case: {case['name']}"
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load demo case {case_id}: {exc}"
        )
