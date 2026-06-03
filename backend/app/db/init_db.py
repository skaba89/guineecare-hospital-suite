from app.db.base import Base
from app.db.session import engine
from app.modules.facilities.models import Facility
from app.modules.departments.models import Department
from app.modules.patients.models import Patient
from app.modules.admissions.models import Admission
from app.modules.users.models import User


def init_db():
    models = [Facility, Department, Patient, Admission, User]
    Base.metadata.create_all(bind=engine)
    return models
