"""
PRATHAM 100-Patient Stress Test and Workflow Simulation
============================================================
Simulates 100 patient cases through the entire intake and approval lifecycle.
Ensures zero exceptions, zero relational integrity issues, and zero crashes.
"""
import sys
import time
import requests
from dotenv import load_dotenv

# Load env variables
load_dotenv()

API = "http://127.0.0.1:8000"

def run_stress_test():
    print("=" * 72)
    print("  PRATHAM 100-Patient Stress Test and Lifecycle Simulation")
    print("=" * 72)
    
    start_time = time.time()
    successful_cases = 0
    failed_cases = 0
    
    for i in range(1, 101):
        try:
            # Step 1: Create intake case
            intake_payload = {
                "patient": {
                    "first_name": f"StressTest{i}",
                    "last_name": "Patient",
                    "date_of_birth": "1980-05-15",
                    "gender": "male" if i % 2 == 0 else "female",
                    "contact_number": f"+91-990000{i:04d}"
                },
                "vitals": {
                    "heart_rate": 80 + (i % 20),
                    "spo2": 95 + (i % 6),
                    "bp_systolic": 120 + (i % 30),
                    "bp_diastolic": 80 + (i % 15),
                    "temperature": 36.5 + (i % 10) * 0.1,
                    "respiratory_rate": 16 + (i % 5)
                },
                "symptoms": {
                    "chest_pain": i % 3 == 0,
                    "breathlessness": i % 3 == 0,
                    "trauma": i % 4 == 0,
                    "bleeding": False,
                    "unconsciousness": False,
                    "neurological_symptoms": False
                },
                "arrival_type": "ambulance" if i % 2 == 0 else "walk_in",
                "ambulance_eta": 10,
                "emergency_description": f"Stress testing simulation patient sequence {i}",
                "chief_complaint": "Chest pain and breathlessness" if i % 3 == 0 else "Routine checkup"
            }
            
            # Post intake
            r = requests.post(f"{API}/api/intake", json=intake_payload, timeout=10)
            if r.status_code != 201:
                print(f"  [Case {i}] Intake registration failed: Status {r.status_code}")
                failed_cases += 1
                continue
                
            intake_data = r.json()
            intake_id = intake_data.get("intake_id")
            recommended = intake_data.get("investigations_recommended", [])
            
            # Step 2: Confirm arrival if en_route
            if i % 2 == 0:
                r_arr = requests.post(f"{API}/api/intake/arrival/confirm", json={
                    "intake_id": intake_id,
                    "actor_name": "StressTest Robot"
                }, timeout=10)
                if r_arr.status_code != 200:
                    print(f"  [Case {i}] Arrival confirmation failed: Status {r_arr.status_code}")
                    failed_cases += 1
                    continue

            # Step 3: Approve recommended investigations (transitions status and rejects rest)
            # If no recommendations, approve default ones
            to_approve = recommended if recommended else ["Troponin", "CBC"]
            r_app = requests.post(f"{API}/api/investigations/approve", json={
                "intake_id": intake_id,
                "approved_tests": to_approve,
                "doctor_name": "Dr. StressTestBot",
                "doctor_notes": f"Stress test case {i} approval reason."
            }, timeout=10)
            
            if r_app.status_code != 200:
                print(f"  [Case {i}] Investigation approval failed: Status {r_app.status_code}")
                failed_cases += 1
                continue
            
            # Step 4: Verify patient details loading endpoint
            r_det = requests.get(f"{API}/api/investigations/patient/{intake_id}", timeout=10)
            if r_det.status_code != 200:
                print(f"  [Case {i}] Patient details loading failed: Status {r_det.status_code}")
                failed_cases += 1
                continue
                
            # Step 5: Verify clinical report compiles successfully
            r_rep = requests.get(f"{API}/api/report/{intake_id}", timeout=10)
            if r_rep.status_code != 200:
                print(f"  [Case {i}] Clinical report fetch failed: Status {r_rep.status_code}")
                failed_cases += 1
                continue
            
            successful_cases += 1
            if i % 10 == 0:
                print(f"  [Progress] Simulated {i} / 100 cases successfully...")
                
        except Exception as e:
            print(f"  [Case {i}] Exception raised during simulation: {e}")
            failed_cases += 1
            
    duration = time.time() - start_time
    print("\n" + "=" * 72)
    print("  SIMULATION RESULTS")
    print("=" * 72)
    print(f"  Total Simulated Patients : 100")
    print(f"  Successful Passes        : {successful_cases}")
    print(f"  Failed Lifecycle Flows   : {failed_cases}")
    print(f"  Total Simulation Time    : {duration:.2f} seconds")
    print("=" * 72)
    
    if failed_cases > 0:
        print("  [FAIL] Stress test simulation completed with failures.")
        sys.exit(1)
        
    print("  [PASS] All 100 simulations passed. Starting database integrity verification...")
    # Import integrity verification
    import subprocess
    rc = subprocess.call(["python", "verify_db_integrity.py"])
    if rc == 0:
        print("  [PASS] Database integrity verification completed successfully.")
        sys.exit(0)
    else:
        print("  [FAIL] Database integrity check failed after stress test.")
        sys.exit(1)

if __name__ == "__main__":
    run_stress_test()
