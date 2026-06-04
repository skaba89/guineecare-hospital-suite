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
    ("emergency.read", "Voir la file urgence", "emergency"),
    ("emergency.create", "Creer un passage urgence", "emergency"),
    ("emergency.triage", "Realiser le triage", "emergency"),
    ("emergency.orient", "Orienter un passage urgence", "emergency"),
    ("pharmacy.read", "Voir la pharmacie", "pharmacy"),
    ("pharmacy.manage", "Gerer la pharmacie", "pharmacy"),
    ("lab.read", "Voir le laboratoire", "laboratory"),
    ("lab.manage", "Gerer le catalogue laboratoire", "laboratory"),
    ("lab.order", "Creer une demande laboratoire", "laboratory"),
    ("lab.result", "Saisir un resultat laboratoire", "laboratory"),
    ("lab.validate", "Valider un resultat laboratoire", "laboratory"),
    ("billing.read", "Voir la facturation", "billing"),
    ("billing.manage", "Gerer la facturation", "billing"),
    ("billing.pay", "Encaisser un paiement", "billing"),
]

ROLE_PERMISSION_MAP = {
    "DOCTOR": [
        "patient.read",
        "admission.read",
        "admission.create",
        "emergency.read",
        "emergency.create",
        "emergency.triage",
        "emergency.orient",
        "lab.read",
        "lab.order",
    ],
    "NURSE": [
        "patient.read",
        "admission.read",
        "emergency.read",
        "emergency.triage",
    ],
    "PHARMACIST": [
        "patient.read",
        "pharmacy.read",
        "pharmacy.manage",
    ],
    "LAB_TECH": [
        "patient.read",
        "lab.read",
        "lab.result",
        "lab.validate",
    ],
    "CASHIER": [
        "patient.read",
        "billing.read",
        "billing.manage",
        "billing.pay",
    ],
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
