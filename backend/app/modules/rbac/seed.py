from sqlalchemy.orm import Session

from app.modules.rbac.models import Permission, Role, RolePermission

DEFAULT_ROLES = [
    ("SUPER_ADMIN", "Super administrateur"),
    ("ADMIN", "Administrateur hopital"),
    ("DOCTOR", "Medecin"),
    ("NURSE", "Infirmier"),
    ("PHARMACIST", "Pharmacien"),
    ("LAB_TECH", "Laboratoire"),
    ("CASHIER", "Caissier"),
]

DEFAULT_PERMISSIONS = [
    ("facility.read", "Voir les etablissements", "facilities"),
    ("facility.manage", "Gerer les etablissements", "facilities"),
    ("department.read", "Voir les services", "departments"),
    ("department.manage", "Gerer les services", "departments"),
    ("patient.read", "Voir les patients", "patients"),
    ("patient.create", "Creer les patients", "patients"),
    ("admission.read", "Voir les admissions", "admissions"),
    ("admission.create", "Creer les admissions", "admissions"),
    ("admission.close", "Cloturer les admissions", "admissions"),
    ("pharmacy.read", "Voir la pharmacie", "pharmacy"),
    ("lab.read", "Voir le laboratoire", "laboratory"),
    ("billing.read", "Voir la facturation", "billing"),
]

ROLE_PERMISSION_MAP = {
    "DOCTOR": ["patient.read", "admission.read", "lab.read"],
    "NURSE": ["patient.read", "admission.read"],
    "PHARMACIST": ["patient.read", "pharmacy.read"],
    "LAB_TECH": ["patient.read", "lab.read"],
    "CASHIER": ["patient.read", "billing.read"],
}


def seed_rbac(db: Session):
    for code, name in DEFAULT_ROLES:
        if not db.query(Role).filter(Role.code == code).first():
            db.add(Role(code=code, name=name))

    for code, name, module in DEFAULT_PERMISSIONS:
        if not db.query(Permission).filter(Permission.code == code).first():
            db.add(Permission(code=code, name=name, module=module))

    db.commit()

    for role_code, permissions in ROLE_PERMISSION_MAP.items():
        for permission_code in permissions:
            existing = (
                db.query(RolePermission)
                .filter(RolePermission.role_code == role_code)
                .filter(RolePermission.permission_code == permission_code)
                .first()
            )
            if not existing:
                db.add(RolePermission(role_code=role_code, permission_code=permission_code))

    db.commit()
