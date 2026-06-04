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
    ]
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_rbac(db)
    finally:
        db.close()
    return models
