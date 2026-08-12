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
    # v1.6.0 — FHIR R4 + observability
    ("fhir.read", "Consulter les ressources FHIR", "fhir"),
    ("fhir.write", "Créer des ressources FHIR", "fhir"),
    ("metrics.read", "Consulter les métriques Prometheus", "observability"),
    # v2.8.0 — Permissions additionnelles pour ADMIN (bypass retiré)
    ("activity.read", "Consulter le flux d'activité", "activity"),
    ("billing.validate", "Valider/annuler des factures", "billing"),
    ("billing.write", "Créer/modifier des factures", "billing"),
    ("pharmacy.write", "Dispenser et gérer les stocks pharmacie", "pharmacy"),
    ("hospitalization.write", "Gérer les séjours et lits hospitalisation", "hospitalization"),
    ("imaging.write", "Créer des demandes et résultats imagerie", "imaging"),
    ("surgery.write", "Créer des programmations chirurgicales", "surgery"),
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
        "fhir.read",
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
    # v2.8.0 — ADMIN a désormais des permissions explicites (bypass retiré)
    "ADMIN": [
        "facility.read",
        "department.read",
        "department.manage",
        "patient.read",
        "patient.create",
        "admission.read",
        "admission.create",
        "emergency.read",
        "emergency.create",
        "emergency.triage",
        "emergency.orient",
        "emergency.care",
        "emergency.discharge",
        "hospitalization.read",
        "hospitalization.write",
        "maternity.read",
        "clinical.read",
        "clinical.write",
        "pharmacy.read",
        "pharmacy.write",
        "lab.read",
        "lab.order",
        "lab.result",
        "lab.validate",
        "imaging.read",
        "imaging.write",
        "surgery.read",
        "billing.read",
        "billing.write",
        "billing.validate",
        "billing.pay",
        "personnel.read",
        "personnel.manage",
        "personnel.planning",
        "quality.read",
        "quality.manage",
        "quality.dashboard",
        "reporting.read",
        "notification.manage",
        "activity.read",
        "feedback.read",
        "feedback.resolve",
        "audit.read",
        "fhir.read",
    ],
}


def seed_rbac(db: Session):
    """Seed RBAC roles, permissions, and role-permission mappings.

    v2.8.5 — OPTIMISÉ : utilise des requêtes en lot (bulk) au lieu de
    requêtes individuelles. Avant : ~250 requêtes individuelles → 14 min
    sur Neon PostgreSQL. Maintenant : 5 requêtes en lot → < 5 secondes.

    - Ajoute les rôles manquants (1 requête pour vérifier, 1 pour insérer)
    - Ajoute les permissions manquantes (1 requête pour vérifier, 1 pour insérer)
    - Supprime les role_permissions orphelins (1 requête DELETE)
    - Ajoute les role_permissions manquants (1 requête pour vérifier, 1 pour insérer)
    """
    from sqlalchemy import text

    # 1. Rôles — requête en lot
    existing_roles = {r.code for r in db.query(Role).all()}
    new_roles = [(code, name) for code, name in DEFAULT_ROLES if code not in existing_roles]
    if new_roles:
        db.execute(Role.__table__.insert(), [
            {"code": code, "name": name} for code, name in new_roles
        ])
    db.commit()

    # 2. Permissions — requête en lot
    existing_perms = {p.code for p in db.query(Permission).all()}
    new_perms = [(code, name, module) for code, name, module in DEFAULT_PERMISSIONS if code not in existing_perms]
    if new_perms:
        db.execute(Permission.__table__.insert(), [
            {"code": code, "name": name, "module": module} for code, name, module in new_perms
        ])
    db.commit()

    # 3. Nettoyer les role_permissions orphelins — 1 requête DELETE
    valid_perm_codes = [code for code, _, _ in DEFAULT_PERMISSIONS]
    if existing_perms:  # seulement si la table n'était pas vide
        db.execute(
            text("DELETE FROM role_permissions WHERE permission_code NOT IN :valid_codes"),
            {"valid_codes": tuple(valid_perm_codes)}
        )
    db.commit()

    # 4. Role-Permission mappings — requête en lot
    # Récupérer tous les mappings existants en 1 requête
    existing_rps = {
        (rp.role_code, rp.permission_code)
        for rp in db.query(RolePermission).all()
    }

    # Calculer les nouveaux mappings manquants
    new_rps = []
    for role_code, permissions in ROLE_PERMISSION_MAP.items():
        for permission_code in permissions:
            if (role_code, permission_code) not in existing_rps:
                new_rps.append({"role_code": role_code, "permission_code": permission_code})

    if new_rps:
        db.execute(RolePermission.__table__.insert(), new_rps)
    db.commit()
