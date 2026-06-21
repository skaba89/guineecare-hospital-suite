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
    ("MIDWIFE", "Sage-femme"),
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
    ("clinical.read", "Voir les donnees cliniques", "clinical"),
    ("clinical.write", "Saisir des donnees cliniques", "clinical"),
    ("hospitalization.read", "Voir l'hospitalisation", "hospitalization"),
    ("hospitalization.manage", "Gerer l'hospitalisation", "hospitalization"),
    ("personnel.read", "Voir le personnel", "personnel"),
    ("personnel.manage", "Gerer le personnel", "personnel"),
    ("maternity.read", "Voir la maternite", "maternity"),
    ("maternity.write", "Saisir des donnees maternite", "maternity"),
    ("emergency.care", "Soins aux urgences", "emergency"),
    ("emergency.discharge", "Sortie des urgences", "emergency"),
    ("imaging.read", "Voir l'imagerie", "imaging"),
    ("imaging.manage", "Gerer l'imagerie", "imaging"),
    ("surgery.read", "Voir le bloc operatoire", "surgery"),
    ("surgery.manage", "Gerer le bloc operatoire", "surgery"),
    ("quality.read", "Voir la qualite", "quality"),
    ("quality.manage", "Gerer la qualite", "quality"),
    ("reporting.read", "Voir le reporting", "reporting"),
    ("reporting.manage", "Gerer le reporting", "reporting"),
    ("audit.read", "Consulter le journal d'audit", "audit"),
    ("notification.send", "Envoyer une notification", "notifications"),
    # v1.1.0 — change-management feedback loop
    ("feedback.read", "Consulter les retours utilisateurs", "feedback"),
    ("feedback.resolve", "Trier et resoudre les retours utilisateurs", "feedback"),
    # v1.4.0 — SMS + quality dashboard advanced
    ("notification.manage", "Configurer providers SMS et regles de routage", "notifications"),
    ("quality.dashboard", "Consulter le dashboard qualite avance", "quality"),
    # v1.5.0 — RH v2 (plannings/gardes/congés/astreintes/remplacements)
    ("personnel.planning", "Consulter et gerer le planning hebdo", "personnel"),
    ("personnel.leave_approve", "Approuver les demandes de conge", "personnel"),
]

ROLE_PERMISSION_MAP = {
    "DOCTOR": [
        "facility.read",
        "department.read",
        "patient.read",
        "admission.read",
        "admission.create",
        "emergency.read",
        "emergency.create",
        "emergency.triage",
        "emergency.orient",
        "emergency.care",
        "emergency.discharge",
        "lab.read",
        "lab.order",
        "lab.result",
        "clinical.read",
        "clinical.write",
        "hospitalization.read",
        "hospitalization.manage",
        "personnel.read",
        "maternity.read",
        "maternity.write",
        "imaging.read",
        "imaging.manage",
        "surgery.read",
        "surgery.manage",
        "quality.read",
        "quality.dashboard",
        "reporting.read",
        "personnel.planning",
    ],
    "NURSE": [
        "facility.read",
        "department.read",
        "patient.read",
        "admission.read",
        "emergency.read",
        "emergency.triage",
        "emergency.care",
        "clinical.read",
        "clinical.write",
        "hospitalization.read",
        "personnel.read",
        "personnel.planning",
        "maternity.read",
        "imaging.read",
        "quality.read",
        "quality.dashboard",
    ],
    "PHARMACIST": [
        "facility.read",
        "patient.read",
        "pharmacy.read",
        "pharmacy.manage",
    ],
    "LAB_TECH": [
        "facility.read",
        "patient.read",
        "lab.read",
        "lab.result",
        "lab.validate",
    ],
    "CASHIER": [
        "facility.read",
        "patient.read",
        "billing.read",
        "billing.manage",
        "billing.pay",
    ],
    "MIDWIFE": [
        "facility.read",
        "department.read",
        "patient.read",
        "maternity.read",
        "maternity.write",
        "emergency.care",
        "clinical.read",
        "clinical.write",
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
