from app.core.security import hash_password
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.modules.billing.models import TariffItem
from app.modules.departments.models import Department
from app.modules.facilities.models import Facility
from app.modules.laboratory.models import LabTest
from app.modules.patients.models import Patient
from app.modules.pharmacy.models import PharmacyProduct, PharmacyStock
from app.modules.users.models import User


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

        admin = db.query(User).filter(User.email == "admin@guineecare.com").first()
        if not admin:
            db.add(User(
                facility_id=facility.id,
                email="admin@guineecare.com",
                password_hash=hash_password("admin123"),
                first_name="Admin",
                last_name="GuineeCare",
                role="SUPER_ADMIN",
            ))

        doctor = db.query(User).filter(User.email == "doctor@guineecare.com").first()
        if not doctor:
            db.add(User(
                facility_id=facility.id,
                email="doctor@guineecare.com",
                password_hash=hash_password("doctor123"),
                first_name="Amadou",
                last_name="Diallo",
                role="DOCTOR",
            ))

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

        for code, name, category, form, dosage, quantity, min_threshold in [
            ("PARA-500", "Paracetamol 500 mg", "ANTALGIC", "tablet", "500 mg", 1000, 100),
            ("AMOX-500", "Amoxicilline 500 mg", "ANTIBIOTIC", "capsule", "500 mg", 500, 50),
        ]:
            product = db.query(PharmacyProduct).filter(
                PharmacyProduct.facility_id == facility.id,
                PharmacyProduct.code == code,
            ).first()
            if not product:
                product = PharmacyProduct(
                    facility_id=facility.id,
                    code=code,
                    name=name,
                    category=category,
                    form=form,
                    dosage=dosage,
                )
                db.add(product)
                db.flush()
            stock = db.query(PharmacyStock).filter(
                PharmacyStock.facility_id == facility.id,
                PharmacyStock.product_id == product.id,
            ).first()
            if not stock:
                db.add(PharmacyStock(
                    facility_id=facility.id,
                    product_id=product.id,
                    quantity_available=quantity,
                    min_threshold=min_threshold,
                ))

        for code, name, category, sample_type in [
            ("NFS", "Numeration formule sanguine", "HEMATOLOGY", "blood"),
            ("GLY", "Glycemie", "BIOCHEMISTRY", "blood"),
            ("GE", "Goutte epaisse", "PARASITOLOGY", "blood"),
        ]:
            exists = db.query(LabTest).filter(
                LabTest.facility_id == facility.id,
                LabTest.code == code,
            ).first()
            if not exists:
                db.add(LabTest(
                    facility_id=facility.id,
                    code=code,
                    name=name,
                    category=category,
                    sample_type=sample_type,
                ))

        for code, name, category, unit_price in [
            ("CONS-GEN", "Consultation medecine generale", "CONSULTATION", 50000),
            ("URG-CONS", "Consultation urgence", "URGENCE", 75000),
            ("LAB-NFS", "NFS", "LABORATOIRE", 35000),
            ("LAB-GLY", "Glycemie", "LABORATOIRE", 20000),
        ]:
            exists = db.query(TariffItem).filter(
                TariffItem.facility_id == facility.id,
                TariffItem.code == code,
            ).first()
            if not exists:
                db.add(TariffItem(
                    facility_id=facility.id,
                    code=code,
                    name=name,
                    category=category,
                    unit_price=unit_price,
                ))

        db.commit()
        print("Seed completed successfully")
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
