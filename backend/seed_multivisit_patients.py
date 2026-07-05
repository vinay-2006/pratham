"""
seed_multivisit_patients.py — Multi-Visit Patient Trajectory Seed Script

Populates Supabase with multi-visit longitudinal patient profiles (Visit 1 vs Visit 2 vs Visit 3)
to fuel Phase 3 longitudinal trend analysis and comparative delta reporting.
"""

from __future__ import annotations
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))
from app.db.supabase_client import supabase


def seed_multivisit_trajectories():
    print("=" * 60)
    print("  Seeding Multi-Visit Patient Trajectories into Supabase...")
    print("=" * 60)

    # 1. Create Patient
    patient_data = {
        "first_name": "Robert",
        "last_name": "Vance",
        "date_of_birth": "1954-05-12",
        "gender": "male",
        "contact_number": "+1-555-0192",
        "allergies": ["Penicillin"],
        "current_medications": ["Aspirin 81mg", "Lisinopril 10mg"],
        "past_medical_history": ["Hypertension", "Type 2 Diabetes"],
    }

    try:
        p_res = supabase.table("patients").insert(patient_data).execute()
        if not p_res.data:
            print("Failed to create patient")
            return
        patient_id = p_res.data[0]["id"]
        print(f"Created Patient: Robert Vance (ID: {patient_id})")
    except Exception as exc:
        print(f"Error creating patient: {exc}")
        return

    # 2. Visit 1: Initial Presentation (Severe Pneumonia) - 5 days ago
    now = datetime.now()
    t1 = now - timedelta(days=5)
    t2 = now - timedelta(days=2)
    t3 = now

    visits_spec = [
        {
            "tag": "Visit 1 (Acute Admission)",
            "created_at": t1.isoformat(),
            "cc": "severe dyspnea, high fever, productive cough",
            "desc": "Patient presented to ER via ambulance with acute respiratory distress",
            "severity": "critical",
            "vitals": {"heart_rate": 118, "spo2": 88, "bp_systolic": 142, "bp_diastolic": 88, "temperature": 39.2, "respiratory_rate": 28},
            "symptoms": {"breathlessness": True, "chest_pain": False},
            "risk": {"cardiac_risk": 20, "respiratory_risk": 85, "trauma_risk": 0, "neurological_risk": 10, "overall_severity": "critical"},
        },
        {
            "tag": "Visit 2 (48-Hour Re-assessment)",
            "created_at": t2.isoformat(),
            "cc": "improving dyspnea on IV antibiotics",
            "desc": "48-hour ward assessment following oxygen therapy and ceftriaxone",
            "severity": "moderate",
            "vitals": {"heart_rate": 92, "spo2": 94, "bp_systolic": 130, "bp_diastolic": 82, "temperature": 37.8, "respiratory_rate": 20},
            "symptoms": {"breathlessness": True, "chest_pain": False},
            "risk": {"cardiac_risk": 10, "respiratory_risk": 45, "trauma_risk": 0, "neurological_risk": 0, "overall_severity": "moderate"},
        },
        {
            "tag": "Visit 3 (Day 5 Discharge Evaluation)",
            "created_at": t3.isoformat(),
            "cc": "routine pre-discharge evaluation",
            "desc": "Patient clinically stable, ready for transition to oral antibiotics",
            "severity": "low",
            "vitals": {"heart_rate": 74, "spo2": 98, "bp_systolic": 122, "bp_diastolic": 78, "temperature": 36.7, "respiratory_rate": 15},
            "symptoms": {"breathlessness": False, "chest_pain": False},
            "risk": {"cardiac_risk": 5, "respiratory_risk": 10, "trauma_risk": 0, "neurological_risk": 0, "overall_severity": "low"},
        },
    ]

    for vspec in visits_spec:
        intake_res = supabase.table("emergency_intake").insert({
            "patient_id": patient_id,
            "chief_complaint": vspec["cc"],
            "emergency_description": vspec["desc"],
            "severity_level": vspec["severity"],
            "status": "completed",
            "created_at": vspec["created_at"],
        }).execute()

        intake_id = intake_res.data[0]["id"]

        # Vitals
        v = vspec["vitals"]
        v["patient_id"] = patient_id
        v["intake_id"] = intake_id
        v["created_at"] = vspec["created_at"]
        supabase.table("vitals").insert(v).execute()

        # Symptoms
        s = vspec["symptoms"]
        s["intake_id"] = intake_id
        s["created_at"] = vspec["created_at"]
        supabase.table("symptoms").insert(s).execute()

        # Risk
        r = vspec["risk"]
        r["intake_id"] = intake_id
        r["created_at"] = vspec["created_at"]
        supabase.table("risk_scores").insert(r).execute()

        print(f"  ✓ Seeded {vspec['tag']} (Intake ID: {intake_id[:8]}...)")

    print("=" * 60)
    print("  Multi-Visit Patient Trajectory Seeding Complete!")
    print("=" * 60)


if __name__ == "__main__":
    seed_multivisit_trajectories()
