from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.modules.departments.models import Department
from app.modules.facilities.models import Facility
from app.modules.patients.models import Patient


def run_seed():
    init_db()
    db = SessionLocal()
    try:
        facility = db.query(Facility).filter(Facility.code == "CHU-DONKA").first()
        if not facility:
            facility = Facility(
                code="CHU-DONKA",
                name="CHU Donka",
                category="CHU",
                region="Conakry",
                prefecture="Conakry",
            )
            db.add(facility)
            db.commit()
            db.refresh(facility)

        for code, name, category in [
            ("URG", "Urgences", "CLINICAL"),
            ("MAT", "Maternité", "CLINICAL"),
            ("MED", "Médecine générale", "CLINICAL"),
            ("LAB", "Laboratoire", "TECHNICAL"),
            ("PHA", "Pharmacie", "SUPPORT"),
            ("CAI", "Caisse", "ADMIN"),
        ]:
            exists = db.query(Department).filter(
                Department.facility_id == facility.id,
                Department.code == code,
            ).first()
            if not exists:
                db.add(Department(
                    facility_id=facility.id,
                    code=code,
                    name=name,
                    category=category,
                ))

        patient = db.query(Patient).filter(Patient.patient_number == "GC-PAT-000001").first()
        if not patient:
            db.add(Patient(
                facility_id=facility.id,
                patient_number="GC-PAT-000001",
                first_name="Mamadou",
                last_name="Camara",
            ))

        db.commit()
        print("Seed completed successfully")
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
