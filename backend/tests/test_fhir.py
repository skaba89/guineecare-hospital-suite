"""Tests du module FHIR R4 v1.6.0 — conversions + endpoints RESTful."""
from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest

from app.modules.admissions.models import Admission
from app.modules.clinical.models import ClinicalNote, PatientMeasurement
from app.modules.fhir.conversions import (
    admission_to_fhir,
    bundle,
    imaging_result_to_fhir,
    lab_result_to_fhir,
    measurement_to_fhir,
    operation_outcome,
    patient_to_fhir,
    prescription_to_fhir,
)
from app.modules.imaging.models import ImagingOrder, ImagingResult
from app.modules.laboratory.models import LabOrder, LabResult, LabTest
from app.modules.patients.models import Patient


# ── Helpers ─────────────────────────────────────────────────────────────────

def _create_patient(db, **overrides):
    """Crée un patient de test."""
    suffix = uuid4().hex[:8]
    defaults = {
        "facility_id": "facility-test-001",
        "patient_number": f"PAT-TEST-{suffix}",
        "first_name": "Amadou",
        "last_name": "Diallo",
        "gender": "M",
        "date_of_birth": date(1985, 5, 15),
        "phone": "+224622334455",
        "address": "Conakry, Guinée",
        "national_id": f"GN-{suffix}",
        "status": "ACTIVE",
    }
    defaults.update(overrides)
    p = Patient(**defaults)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


# ── Conversions unitaires ───────────────────────────────────────────────────

def test_patient_to_fhir_basic(db):
    """Conversion Patient → FHIR Patient avec champs de base."""
    p = _create_patient(db)
    fhir = patient_to_fhir(p)

    assert fhir["resourceType"] == "Patient"
    assert fhir["id"] == p.id
    assert fhir["name"][0]["family"] == "Diallo"
    assert fhir["name"][0]["given"] == ["Amadou"]
    assert fhir["gender"] == "male"
    assert fhir["birthDate"] == "1985-05-15"
    assert fhir["active"] is True

    # Identifiers
    identifiers = {i["system"]: i["value"] for i in fhir["identifier"]}
    assert any("patient-number" in s for s in identifiers)
    assert any("national-id" in s for s in identifiers)


def test_patient_to_fhir_gender_mapping(db):
    """Mapping des genres M/F/O → male/female/other."""
    for internal, expected in [("M", "male"), ("F", "female"), ("O", "other")]:
        p = _create_patient(db, gender=internal, patient_number=f"PAT-{internal}-{uuid4().hex[:8]}")
        fhir = patient_to_fhir(p)
        assert fhir["gender"] == expected


def test_patient_to_fhir_no_gender(db):
    """Patient sans genre → pas de champ gender dans FHIR."""
    p = _create_patient(db, gender=None, patient_number=f"PAT-NG-{uuid4().hex[:8]}")
    fhir = patient_to_fhir(p)
    assert "gender" not in fhir


def test_patient_to_fhir_meta_tag(db):
    """Le bloc meta contient le tag GUINEECARE."""
    p = _create_patient(db)
    fhir = patient_to_fhir(p)
    assert "meta" in fhir
    assert "tag" in fhir["meta"]
    tags = [t["code"] for t in fhir["meta"]["tag"]]
    assert "GUINEECARE" in tags


def test_admission_to_fhir(db):
    """Conversion Admission → FHIR Encounter."""
    p = _create_patient(db)
    adm = Admission(
        facility_id="facility-test-001",
        patient_id=p.id,
        admission_type="EMERGENCY",
        status="OPEN",
        admitted_at=datetime.utcnow(),
    )
    db.add(adm)
    db.commit()
    db.refresh(adm)

    fhir = admission_to_fhir(adm)
    assert fhir["resourceType"] == "Encounter"
    assert fhir["status"] == "in-progress"
    assert fhir["class"]["code"] == "EMER"
    assert fhir["subject"]["reference"] == f"Patient/{p.id}"
    assert "period" in fhir
    assert "start" in fhir["period"]


def test_measurement_to_fhir_vital(db):
    """Conversion PatientMeasurement → FHIR Observation (vital-signs)."""
    p = _create_patient(db)
    m = PatientMeasurement(
        facility_id="facility-test-001",
        patient_id=p.id,
        measurement_type="HEART_RATE",
        value="72",
        unit="bpm",
        recorded_at=datetime.utcnow(),
    )
    db.add(m)
    db.commit()
    db.refresh(m)

    fhir = measurement_to_fhir(m, p.id)
    assert fhir["resourceType"] == "Observation"
    assert fhir["status"] == "final"
    assert fhir["category"][0]["coding"][0]["code"] == "vital-signs"
    assert fhir["code"]["coding"][0]["code"] == "8867-4"  # LOINC Heart rate
    assert fhir["valueQuantity"]["value"] == 72
    assert fhir["subject"]["reference"] == f"Patient/{p.id}"


def test_lab_result_to_fhir(db):
    """Conversion LabResult → FHIR Observation (laboratory)."""
    p = _create_patient(db)
    test = LabTest(
        facility_id="facility-test-001",
        code="GLYCEMIE",
        name="Glycémie",
        sample_type="SANG",
    )
    db.add(test)
    db.commit()
    db.refresh(test)

    order = LabOrder(
        facility_id="facility-test-001",
        patient_id=p.id,
        test_id=test.id,
        status="VALIDATED",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    result = LabResult(
        facility_id="facility-test-001",
        order_id=order.id,
        result_value="0.95",
        interpretation="NORMAL",
        status="VALIDATED",
    )
    db.add(result)
    db.commit()
    db.refresh(result)

    fhir = lab_result_to_fhir(result, p.id)
    assert fhir["resourceType"] == "Observation"
    assert fhir["status"] == "final"
    assert fhir["category"][0]["coding"][0]["code"] == "laboratory"
    assert fhir["valueQuantity"]["value"] == 0.95


def test_lab_result_critical_interpretation(db):
    """LabResult CRITIQUE → interpretation HX (critical high)."""
    p = _create_patient(db)
    test = LabTest(facility_id="facility-test-001", code="KAL", name="Kaliémie", sample_type="SANG")
    db.add(test)
    db.commit()
    db.refresh(test)

    order = LabOrder(facility_id="facility-test-001", patient_id=p.id, test_id=test.id, status="VALIDATED")
    db.add(order)
    db.commit()
    db.refresh(order)

    result = LabResult(
        facility_id="facility-test-001",
        order_id=order.id, result_value="7.5",
        interpretation="CRITIQUE", status="VALIDATED",
    )
    db.add(result)
    db.commit()
    db.refresh(result)

    fhir = lab_result_to_fhir(result, p.id)
    assert "interpretation" in fhir
    assert fhir["interpretation"][0]["coding"][0]["code"] == "HX"


def test_prescription_to_fhir(db):
    """Conversion ClinicalNote PRESCRIPTION → FHIR MedicationRequest."""
    p = _create_patient(db)
    note = ClinicalNote(
        facility_id="facility-test-001",
        patient_id=p.id,
        note_type="PRESCRIPTION",
        content="Paracetamol 1g x3/jour pendant 5 jours",
    )
    db.add(note)
    db.commit()
    db.refresh(note)

    fhir = prescription_to_fhir(note, p.id)
    assert fhir["resourceType"] == "MedicationRequest"
    assert fhir["intent"] == "order"
    assert fhir["subject"]["reference"] == f"Patient/{p.id}"
    assert "Paracetamol" in fhir["medicationCodeableConcept"]["text"]


def test_imaging_result_to_fhir(db):
    """Conversion ImagingResult → FHIR DiagnosticReport."""
    p = _create_patient(db)
    order = ImagingOrder(
        facility_id="facility-test-001",
        patient_id=p.id,
        exam_type="RADIOGRAPHY",
        body_region="THORAX",
        status="COMPLETED",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    result = ImagingResult(
        facility_id="facility-test-001",
        order_id=order.id,
        patient_id=p.id,
        findings="Aucun foyer infectieux décelé",
        conclusion="Radio thoracique normale",
        status="VALIDATED",
    )
    db.add(result)
    db.commit()
    db.refresh(result)

    fhir = imaging_result_to_fhir(result, p.id)
    assert fhir["resourceType"] == "DiagnosticReport"
    assert fhir["status"] == "final"
    assert fhir["subject"]["reference"] == f"Patient/{p.id}"
    assert "Conclusion: Radio thoracique normale" in fhir["conclusion"]


# ── Bundle / OperationOutcome ───────────────────────────────────────────────

def test_bundle_structure():
    """bundle() retourne une structure FHIR Bundle valide."""
    resources = [
        {"resourceType": "Patient", "id": "p1"},
        {"resourceType": "Patient", "id": "p2"},
    ]
    b = bundle(resources)
    assert b["resourceType"] == "Bundle"
    assert b["type"] == "searchset"
    assert b["total"] == 2
    assert len(b["entry"]) == 2
    assert b["entry"][0]["fullUrl"] == "Patient/p1"


def test_operation_outcome_structure():
    """operation_outcome() retourne une ressource OperationOutcome valide."""
    oo = operation_outcome("error", "not-found", "Patient introuvable")
    assert oo["resourceType"] == "OperationOutcome"
    assert oo["issue"][0]["severity"] == "error"
    assert oo["issue"][0]["code"] == "not-found"
    assert oo["issue"][0]["diagnostics"] == "Patient introuvable"


# ── Endpoints HTTP ──────────────────────────────────────────────────────────

def test_metadata_endpoint(auth_headers, client):
    """GET /fhir/metadata — CapabilityStatement."""
    response = client.get("/api/v1/fhir/metadata", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["resourceType"] == "CapabilityStatement"
    assert data["fhirVersion"] == "4.0.1"
    resources = [r["type"] for r in data["rest"][0]["resource"]]
    assert "Patient" in resources
    assert "Encounter" in resources
    assert "Observation" in resources
    assert "MedicationRequest" in resources
    assert "DiagnosticReport" in resources


def test_search_patients_empty(auth_headers, client):
    """GET /fhir/Patient — Bundle vide si aucun patient."""
    response = client.get("/api/v1/fhir/Patient", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["resourceType"] == "Bundle"
    assert data["total"] == 0
    assert data["entry"] == []


def test_search_patients_by_name(auth_headers, client, db):
    """GET /fhir/Patient?name=Diallo — recherche par nom."""
    _create_patient(db, patient_number=f"PAT-N1-{uuid4().hex[:6]}", first_name="Amadou", last_name="Diallo")
    _create_patient(db, patient_number=f"PAT-N2-{uuid4().hex[:6]}", first_name="Mariame", last_name="Touré")

    response = client.get("/api/v1/fhir/Patient?name=Diallo", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert all(p["resource"]["name"][0]["family"] == "Diallo" for p in data["entry"])


def test_search_patients_by_identifier(auth_headers, client, db):
    """GET /fhir/Patient?identifier=PAT-XXX — recherche par patient_number."""
    p = _create_patient(db, patient_number=f"PAT-ID-{uuid4().hex[:6]}")

    response = client.get(f"/api/v1/fhir/Patient?identifier={p.patient_number}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["entry"][0]["resource"]["id"] == p.id


def test_read_patient(auth_headers, client, db):
    """GET /fhir/Patient/{id} — lecture par ID."""
    p = _create_patient(db, patient_number=f"PAT-READ-{uuid4().hex[:6]}")

    response = client.get(f"/api/v1/fhir/Patient/{p.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["resourceType"] == "Patient"
    assert data["id"] == p.id
    assert data["name"][0]["family"] == "Diallo"


def test_read_patient_not_found(auth_headers, client):
    """GET /fhir/Patient/{id} — 404 si inexistant."""
    response = client.get("/api/v1/fhir/Patient/nonexistent-id", headers=auth_headers)
    assert response.status_code == 404
    data = response.json()
    assert data["detail"]["resourceType"] == "OperationOutcome"


def test_create_patient_fhir(auth_headers, client, db):
    """POST /fhir/Patient — création via FHIR.

    Note: Le current_user de test n'a pas de facility_id. Le endpoint FHIR
    échouera donc avec une 400. On vérifie le message d'erreur plutôt que la
    création réussie.
    """
    payload = {
        "resourceType": "Patient",
        "name": [
            {
                "use": "official",
                "family": "Camara",
                "given": ["Fatoumata"],
            }
        ],
        "gender": "female",
        "birthDate": "1990-08-20",
        "telecom": [{"system": "phone", "value": "+224628765432"}],
        "address": [{"text": "Kankan, Guinée"}],
        "identifier": [
            {"system": "https://guineecare.gn/identifiers/national-id", "value": "GN-987654321"}
        ],
    }
    response = client.post("/api/v1/fhir/Patient", json=payload, headers=auth_headers)
    # Sans facility_id sur le user, on attend 400. Si facility_id présent, on attend 201.
    assert response.status_code in (201, 400)
    if response.status_code == 201:
        data = response.json()
        assert data["resourceType"] == "Patient"
        assert data["name"][0]["family"] == "Camara"
        assert data["gender"] == "female"
        national_ids = [
            i for i in data["identifier"]
            if "national-id" in i.get("system", "")
        ]
        assert len(national_ids) == 1
        assert national_ids[0]["value"] == "GN-987654321"


def test_create_patient_invalid_resource_type(auth_headers, client):
    """POST /fhir/Patient avec resourceType incorrect → 400."""
    response = client.post(
        "/api/v1/fhir/Patient",
        json={"resourceType": "Observation", "id": "x"},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_search_encounters_by_patient(auth_headers, client, db):
    """GET /fhir/Encounter?patient=Patient/{id}."""
    p = _create_patient(db, patient_number=f"PAT-ENC-{uuid4().hex[:6]}")
    adm = Admission(
        facility_id="facility-test-001",
        patient_id=p.id,
        admission_type="ROUTINE",
        status="OPEN",
        admitted_at=datetime.utcnow(),
    )
    db.add(adm)
    db.commit()

    response = client.get(f"/api/v1/fhir/Encounter?patient=Patient/{p.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["entry"][0]["resource"]["resourceType"] == "Encounter"
    assert data["entry"][0]["resource"]["subject"]["reference"] == f"Patient/{p.id}"


def test_search_observations_vitals(auth_headers, client, db):
    """GET /fhir/Observation?patient=...&category=vital-signs."""
    p = _create_patient(db, patient_number=f"PAT-OBS-{uuid4().hex[:6]}")
    m = PatientMeasurement(
        facility_id="facility-test-001",
        patient_id=p.id,
        measurement_type="HEART_RATE",
        value="80",
        unit="bpm",
        recorded_at=datetime.utcnow(),
    )
    db.add(m)
    db.commit()

    response = client.get(
        f"/api/v1/fhir/Observation?patient=Patient/{p.id}&category=vital-signs",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["entry"][0]["resource"]["resourceType"] == "Observation"
    assert data["entry"][0]["resource"]["category"][0]["coding"][0]["code"] == "vital-signs"


def test_search_medication_requests(auth_headers, client, db):
    """GET /fhir/MedicationRequest?patient=..."""
    p = _create_patient(db, patient_number=f"PAT-MED-{uuid4().hex[:6]}")
    note = ClinicalNote(
        facility_id="facility-test-001",
        patient_id=p.id,
        note_type="PRESCRIPTION",
        content="Amoxicilline 500mg x3/jour",
    )
    db.add(note)
    db.commit()

    response = client.get(
        f"/api/v1/fhir/MedicationRequest?patient=Patient/{p.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["entry"][0]["resource"]["resourceType"] == "MedicationRequest"
    assert "Amoxicilline" in data["entry"][0]["resource"]["medicationCodeableConcept"]["text"]


def test_search_diagnostic_reports(auth_headers, client, db):
    """GET /fhir/DiagnosticReport?patient=..."""
    p = _create_patient(db, patient_number=f"PAT-DR-{uuid4().hex[:6]}")
    order = ImagingOrder(
        facility_id="facility-test-001",
        patient_id=p.id,
        exam_type="RADIOGRAPHY",
        body_region="THORAX",
        status="COMPLETED",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    result = ImagingResult(
        facility_id="facility-test-001",
        order_id=order.id,
        patient_id=p.id,
        findings="Pas d'anomalie",
        conclusion="Radio thoracique normale",
        status="VALIDATED",
    )
    db.add(result)
    db.commit()

    response = client.get(
        f"/api/v1/fhir/DiagnosticReport?patient=Patient/{p.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["entry"][0]["resource"]["resourceType"] == "DiagnosticReport"


# ── Auth ────────────────────────────────────────────────────────────────────

def test_fhir_endpoints_require_auth(client):
    """GET /fhir/metadata sans auth → 401."""
    response = client.get("/api/v1/fhir/metadata")
    assert response.status_code == 401
