
def main() -> int:
    # 1. Create patient
    step("1 · Create test patient")
    payload = {
        "patient": {
            "first_name": "Phase1",
            "last_name": "VerifyTest",
            "date_of_birth": "1975-03-10",
            "gender": "male",
            "contact_number": "+91-9000000001",
        },
        "vitals": {
            "heart_rate": 115,
            "spo2": 89,
            "bp_systolic": 155,
            "bp_diastolic": 98,
            "temperature": 38.8,
            "respiratory_rate": 28,
        },
        "symptoms": {
            "chest_pain": True,
            "breathlessness": True,
            "trauma": False,
            "bleeding": False,
            "unconsciousness": False,
            "neurological_symptoms": False,
        },
        "arrival_type": "ambulance",
        "ambulance_eta": 5,
        "emergency_description": "Phase1 evidence filtering verification",
        "chief_complaint": "Chest pain and breathlessness",
    }

    try:
        response = request_json("POST", "/api/intake", json=payload)
        response_data = response.json()
    except (requests.RequestException, RuntimeError, ValueError) as exc:
        fail(f"Could not create patient: {exc}")
        return 1

    intake_id = response_data.get("intake_id")
    if not intake_id:
        fail(f"Intake response did not include intake_id: {response_data}")
        return 1
    ok(f"Patient created; intake_id={intake_id}")

    # 2. Intake pipeline
    step("2 · Pipeline verification")
    ok("NLP, Risk, and Investigations are expected to run during intake registration.")

    # 3. Approve investigations
    step("3 · Doctor approves Chest X-ray, CBC, ABG")
    try:
        request_json(
            "POST",
            "/api/investigations/approve",
            json={
                "intake_id": intake_id,
                "approved_tests": ["Chest X-ray", "CBC", "ABG"],
                "doctor_notes": "Phase1 test",
                "doctor_name": "Dr.Phase1",
            },
        )
        ok("Approval request completed for Chest X-ray, CBC, and ABG")
    except (requests.RequestException, RuntimeError) as exc:
        fail(f"Investigation approval failed: {exc}")
        return 1

    # 4. Fetch investigation IDs
    step("4 · Fetch investigation IDs")
    try:
        response_data = request_json(
            "GET", f"/api/investigations/patient/{intake_id}"
        ).json()
    except (requests.RequestException, RuntimeError, ValueError) as exc:
        fail(f"Could not fetch investigations: {exc}")
        return 1

    investigations = response_data.get("investigations", [])
    inv_map = {
        inv.get("investigation_type"): inv.get("id")
        for inv in investigations
        if inv.get("status") == "approved" and inv.get("investigation_type") and inv.get("id")
    }
    for name, investigation_id in inv_map.items():
        ok(f"{name} -> {str(investigation_id)[:8]}...")

    required = ["Chest X-ray", "CBC", "ABG"]
    missing = [name for name in required if name not in inv_map]
    if missing:
        fail(f"Missing approved investigation(s): {', '.join(missing)}")
        return 1

    # 5. Upload distinct evidence for each investigation
    step("5 · Upload distinct evidence — one file per investigation")
    xray_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_xray.jpg")
    if not os.path.isfile(xray_path):
        fail(f"Required test image not found: {xray_path}")
        return 1

    def upload(
        investigation_type: str,
        evidence_type: str,
        filename: str,
        content: bytes,
    ) -> Optional[Dict[str, Any]]:
        investigation_id = inv_map.get(investigation_type)
        if not investigation_id:
            fail(f"No approved investigation for {investigation_type}")
            return None

        content_type = (
            "image/jpeg"
            if filename.lower().endswith((".jpg", ".jpeg"))
            else "text/plain"
        )
        fields = {
            "intake_id": intake_id,
            "evidence_type": evidence_type,
            "investigation_id": investigation_id,
        }
        files = {"file": (filename, io.BytesIO(content), content_type)}

        try:
            result = request_json(
                "POST", "/api/evidence/upload", data=fields, files=files
            ).json()
        except (requests.RequestException, RuntimeError, ValueError) as exc:
            fail(f"Upload failed for {filename}: {exc}")
            return None

        evidence_id = result.get("evidence_id")
        if not evidence_id:
            fail(f"Upload response for {filename} did not include evidence_id: {result}")
            return None
        ok(
            f"Uploaded '{filename}' -> {investigation_type} "
            f"({evidence_type}), evidence_id={str(evidence_id)[:8]}..."
        )
        return result

    try:
        with open(xray_path, "rb") as image_file:
            xray_bytes = image_file.read()
    except OSError as exc:
        fail(f"Could not read test X-ray image: {exc}")
        return 1

    xray_evidence = upload(
        "Chest X-ray", "xray", "chest_xray_phase1.jpg", xray_bytes
    )
    cbc_evidence = upload(
        "CBC",
        "lab_report",
        "cbc_report_phase1.txt",
        b"CBC Report\nWBC:12.5 RBC:4.2 Hgb:14.1 Plt:250",
    )
    abg_evidence = upload(
        "ABG",
        "lab_report",
        "abg_report_phase1.txt",
        b"ABG Report\npH:7.35 pCO2:45 pO2:80 HCO3:24",
    )

    if not all([xray_evidence, cbc_evidence, abg_evidence]):
        fail("One or more evidence uploads failed; stopping before dependent tests.")
        return 1

    # 6. Verify evidence isolation
    step("6 · Verify evidence filtering (no cross-contamination)")
    try:
        data = request_json(
            "GET", f"/api/investigations/patient/{intake_id}"
        ).json()
    except (requests.RequestException, RuntimeError, ValueError) as exc:
        fail(f"Could not verify evidence filtering: {exc}")
        return 1

    expected = {
        "Chest X-ray": ["chest_xray_phase1.jpg"],
        "CBC": ["cbc_report_phase1.txt"],
        "ABG": ["abg_report_phase1.txt"],
    }
    filtering_ok = True
    found_names = set()

    for investigation in data.get("investigations", []):
        if investigation.get("status") != "approved":
            continue
        investigation_type = investigation.get("investigation_type")
        if investigation_type not in expected: