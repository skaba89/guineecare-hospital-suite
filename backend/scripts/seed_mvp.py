from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.modules.facilities.models import Facility
from app.modules.departments.models import Department
from app.modules.patients.models import Patient


def run():
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
                prefecture="Conakry"
            )
            db.add(facility)
            db.commit()
            db.refresh(facility)

        department = db.query(Department).filter(Department.code == "URG").first()
        if not department:
            department = Department(
                facility_id=facility.id,
                code="URG",
                name="Urgences",
                category="clinical"
            )
            db.add(department)

        patient = db.query(Patient).filter(Patient.patient_number == "GC-PAT-000001").first()
        if not patient:
            patient = Patient(
                facility_id=facility.id,
                patient_number="GC-PAT-000001",
                first_name="Mamadou",
                last_name="Camara"
            )
            db.add(patient)

        db.commit()
        print("MVP seed completed")
    finally:
        db.close()


if __name__ == "__main__":
    run()
