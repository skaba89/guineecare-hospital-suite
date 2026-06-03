from app.db.base import Base
from app.db.session import engine
from app.modules.facilities.models import Facility
from app.modules.departments.models import Department
from app.modules.patients.models import Patient
from app.modules.admissions.models import Admission
from app.modules.users.models import User
from app.modules.rbac.models import Role, Permission, RolePermission


def init_db():
    models = [Facility, Department, Patient, Admission, User, Role, Permission, RolePermission]
    Base.metadata.create_all(bind=engine)
    return models
