from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.modules.facilities.models import Facility
from app.modules.departments.models import Department
from app.modules.patients.models import Patient
from app.modules.admissions.models import Admission
from app.modules.users.models import User
from app.modules.rbac.models import Role, Permission, RolePermission
from app.modules.rbac.seed import seed_rbac
from app.modules.activity.models import ActivityEntry
from app.modules.emergency.models import EmergencyVisit
from app.modules.pharmacy.models import PharmacyProduct, PharmacyStock, StockMovement
from app.modules.laboratory.models import LabTest, LabOrder, LabResult
from app.modules.billing.models import TariffItem, Invoice, Payment
from app.modules.clinical.models import ClinicalNote, PatientMeasurement, Diagnosis
from app.modules.hospitalization.models import Room, Bed, HospitalStay
from app.modules.maternity.models import MaternityRecord, MaternityConsultation, DeliveryRecord
from app.modules.personnel.models import StaffMember, OnCallSchedule, LeaveRequest, Contract
from app.modules.imaging.models import ImagingOrder, ImagingResult
from app.modules.surgery.models import OperatingRoom, SurgerySchedule, SurgeryTeamMember, SurgeryReport
from app.modules.quality.models import QualityIndicator, QualityMeasurement, IncidentReport
from app.modules.reporting.models import NationalReport, EpidemicAlert, HealthStatistic


def init_db():
    models = [
        Facility,
        Department,
        Patient,
        Admission,
        User,
        Role,
        Permission,
        RolePermission,
        ActivityEntry,
        EmergencyVisit,
        PharmacyProduct,
        PharmacyStock,
        StockMovement,
        LabTest,
        LabOrder,
        LabResult,
        TariffItem,
        Invoice,
        Payment,
        ClinicalNote,
        PatientMeasurement,
        Diagnosis,
        Room,
        Bed,
        HospitalStay,
        MaternityRecord,
        MaternityConsultation,
        DeliveryRecord,
        StaffMember,
        OnCallSchedule,
        LeaveRequest,
        Contract,
        ImagingOrder,
        ImagingResult,
        OperatingRoom,
        SurgerySchedule,
        SurgeryTeamMember,
        SurgeryReport,
        QualityIndicator,
        QualityMeasurement,
        IncidentReport,
        NationalReport,
        EpidemicAlert,
        HealthStatistic,
    ]
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_rbac(db)
    finally:
        db.close()
    return models
