"""i18n translation service — v1.3.0.

Design choices:
- Catalogs are Python dicts (not JSON files) so they ship with the source
  and benefit from type checking. Adding a locale = adding a dict.
- Keys are dotted strings (`auth.login.invalid_credentials`). Nested dicts
  in the catalog are flattened on load.
- Missing keys fall back to French, then to the key itself. This avoids
  `KeyError` explosions in production but the missing-key event is logged
  at WARNING level so the i18n gap is visible.
- Variable interpolation uses `str.format_map` with a `defaultdict(str)`
  wrapper so missing variables render as empty strings rather than raising.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("guineecare.i18n")

DEFAULT_LOCALE = "fr"
SUPPORTED_LOCALES = ("fr", "en")


# --- French catalog (default) ---
_CATALOG_FR: dict[str, str] = {
    # Auth
    "auth.login.invalid_credentials": "Identifiants invalides.",
    "auth.login.account_locked": "Compte verrouillé après {attempts} échecs. Réessayez dans {minutes} minutes.",
    "auth.login.success": "Connexion réussie.",
    "auth.logout.success": "Déconnexion réussie.",
    "auth.refresh.invalid": "Token de rafraîchissement invalide ou expiré.",
    "auth.token.expired": "Token expiré.",
    "auth.token.invalid": "Token invalide.",
    "auth.token.revoked": "Token révoqué (jti blacklisté).",
    "auth.not_authenticated": "Non authentifié.",
    # RBAC
    "rbac.permission_denied": "Permission insuffisante : {permission} requis.",
    "rbac.role_required": "Rôle insuffisant : {role} requis.",
    # Multi-tenant
    "tenant.access_denied": "Accès à l'établissement {facility_id} refusé.",
    # Common
    "common.not_found": "Ressource introuvable.",
    "common.conflict": "Conflit — la ressource existe déjà ou est dans un état invalide.",
    "common.validation_error": "Erreur de validation.",
    "common.internal_error": "Erreur serveur interne.",
    "common.rate_limited": "Trop de requêtes. Réessayez dans {seconds}s.",
    # Patients
    "patient.duplicate_number": "Numéro patient déjà utilisé : {patient_number}.",
    "patient.not_found": "Patient introuvable (id={patient_id}).",
    # Documents
    "documents.invalid_note_type": "Type de note invalide — PRESCRIPTION requis, reçu : {actual}.",
    "documents.not_found": "Document source introuvable.",
    # Feedback
    "feedback.not_found": "Feedback introuvable.",
    # i18n
    "i18n.unsupported_locale": "Langue non supportée : {locale}. Langues supportées : {supported}.",

    # ─── UI essentials (v1.7.1) — used by frontend useT() ───

    # App / navigation
    "app.name": "GuinéeCare",
    "app.tagline": "Suite Hospitalière",
    "nav.section.care": "SOINS",
    "nav.section.emergency": "URGENCES",
    "nav.section.services": "SERVICES",
    "nav.section.admin": "ADMIN",
    "nav.section.system": "SYSTÈME",
    "nav.section.national": "NATIONAL",
    "nav.dashboard": "Tableau de bord",
    "nav.patients": "Patients",
    "nav.admissions": "Admissions",
    "nav.emergency": "Urgences",
    "nav.emergency.queue": "File d'attente",
    "nav.emergency.triage": "Triage",
    "nav.emergency.orientation": "Orientation",
    "nav.hospitalization": "Hospitalisation",
    "nav.maternity": "Maternité",
    "nav.pharmacy": "Pharmacie",
    "nav.laboratory": "Laboratoire",
    "nav.imaging": "Imagerie",
    "nav.surgery": "Bloc opératoire",
    "nav.billing": "Facturation",
    "nav.personnel": "Personnel",
    "nav.planning": "Planning & Gardes",
    "nav.leaves": "Congés",
    "nav.quality": "Qualité",
    "nav.reporting": "Reporting",
    "nav.notifications": "Notifications",
    "nav.activity": "Activité",
    "nav.users": "Utilisateurs",
    "nav.rbac": "Rôles & Permissions",
    "nav.facilities": "Établissements",
    "nav.departments": "Départements",
    "nav.audit": "Journal d'audit",
    "nav.sms_admin": "SMS Admin",
    "nav.national": "Pilotage national",
    "nav.profile": "Profil",
    "nav.logout": "Déconnexion",
    "nav.search": "Rechercher…",
    "nav.facility_connected": "Établissement connecté",
    "nav.national_view": "Vue nationale",

    # Common actions
    "action.save": "Enregistrer",
    "action.cancel": "Annuler",
    "action.delete": "Supprimer",
    "action.edit": "Modifier",
    "action.create": "Créer",
    "action.search": "Rechercher",
    "action.filter": "Filtrer",
    "action.refresh": "Rafraîchir",
    "action.export": "Exporter",
    "action.print": "Imprimer",
    "action.back": "Retour",
    "action.next": "Suivant",
    "action.previous": "Précédent",
    "action.confirm": "Confirmer",
    "action.close": "Fermer",
    "action.new": "Nouveau",
    "action.add": "Ajouter",

    # Common labels
    "label.loading": "Chargement…",
    "label.error": "Erreur",
    "label.success": "Succès",
    "label.no_data": "Aucune donnée",
    "label.retry": "Réessayer",
    "label.close": "Fermer",
    "label.view_all": "Voir tout",
    "label.refresh": "Actualiser",
    "label.no_results": "Aucun résultat",
    "label.searching": "Recherche…",
    "label.offline": "Hors ligne",
    "label.online": "En ligne",
    "label.total": "Total",
    "label.status": "Statut",
    "label.date": "Date",
    "label.name": "Nom",
    "label.first_name": "Prénom",
    "label.last_name": "Nom",
    "label.email": "Email",
    "label.phone": "Téléphone",
    "label.address": "Adresse",
    "label.description": "Description",
    "label.notes": "Notes",
    "label.actions": "Actions",
    "label.page": "Page",
    "label.of": "sur",
    "label.results": "résultat(s)",

    # Generic status labels — used by AdmissionsPage, SmsAdminPage, ReportingPage, etc.
    # Avoids hardcoded "Active"/"Inactive" English strings in French UI.
    "status.active": "En cours",
    "status.inactive": "Inactif",
    "status.open": "Ouvert",
    "status.closed": "Fermé",
    "status.discharged": "Sorti",
    "status.pending": "En attente",
    "status.completed": "Terminé",
    "status.in_progress": "En cours",
    "status.cancelled": "Annulé",
    "status.validated": "Validé",
    "status.rejected": "Rejeté",
    "status.enabled": "Activé",
    "status.disabled": "Désactivé",

    # Login page
    "login.title": "GuinéeCare",
    "login.subtitle": "Suite Hospitalière",
    "login.email": "Email",
    "login.password": "Mot de passe",
    "login.submit": "Se connecter",
    "login.connecting": "Connexion…",
    "login.error": "Identifiants invalides",
    "login.demo_link": "Utiliser les identifiants démo",

    # Dashboard
    "dashboard.title": "Tableau de bord",
    "dashboard.welcome": "Bonjour",
    "dashboard.active_patients": "Patients actifs",
    "dashboard.active_admissions": "Admissions en cours",
    "dashboard.occupied_beds": "Lits occupés",
    "dashboard.emergencies": "Urgences en cours",
    "dashboard.pending_lab": "Résultats labo en attente",
    "dashboard.pending_imaging": "Imagerie en attente",
    "dashboard.revenue_today": "Recette du jour",
    "dashboard.outstanding": "Créances impayées",

    # Patients
    "patients.title": "Patients",
    "patients.search_placeholder": "Rechercher par nom, numéro, ID…",
    "patients.new": "Nouveau patient",
    "patients.patient_number": "N° patient",
    "patients.age": "Âge",
    "patients.gender": "Genre",
    "patients.male": "Masculin",
    "patients.female": "Féminin",
    "patients.active": "Actif",

    # Patient detail
    "patient.detail.title": "Dossier patient",
    "patient.vitals": "Constantes vitales",
    "patient.lab_results": "Résultats laboratoire",
    "patient.prescriptions": "Ordonnances",
    "patient.blood_type": "Groupe sanguin",
    "patient.allergies": "Allergies",
    "patient.medical_history": "Antécédents médicaux",
    "patient.current_medication": "Traitement en cours",
    "patient.chronic_conditions": "Maladies chroniques",
    "patient.not_specified": "Non renseigné",
    "patient.add_vital": "Saisir une constante",

    # Quality
    "quality.title": "Qualité / Pilotage",
    "quality.dashboard": "Dashboard",
    "quality.alerts": "Alertes",
    "quality.indicators": "Indicateurs",
    "quality.measurements": "Mesures",
    "quality.incidents": "Événements indésirables",
    "quality.thresholds": "Seuils",
    "quality.check_thresholds": "Vérifier les seuils",
    "quality.seed_defaults": "Insérer les indicateurs OMS/HAS",
    "quality.description": "Gestion des indicateurs qualité, mesures, événements indésirables et alertes automatiques.",
    "quality.no_indicators": "Aucun indicateur trouvé.",
    "quality.no_measurements": "Aucune mesure trouvée.",
    "quality.no_incidents": "Aucun événement indésirable trouvé.",

    # SMS admin
    "sms.title": "Notifications SMS — Administration",
    "sms.providers": "Providers",
    "sms.routing_rules": "Règles de routage",
    "sms.history": "Historique",
    "sms.stats": "Statistiques",

    # Notifications page
    "notif.title": "Notifications",
    "notif.unread_count": "{count} notification(s) non lue(s) sur {total}",
    "notif.all_read": "{total} notification(s) — tout est lu",
    "notif.mark_all_read": "Tout marquer comme lu",
    "notif.category": "Catégorie",
    "notif.all_categories": "Toutes",
    "notif.unread_only": "Non lues seulement",
    "notif.refresh": "Actualiser",
    "notif.loading": "Chargement…",
    "notif.empty_title": "Aucune notification",
    "notif.empty_desc": "Les nouvelles notifications apparaîtront ici.",
    "notif.new_badge": "NEW",
    "notif.sent": "envoyé",
    "notif.failed": "échec",
    "notif.delivery_error": "⚠ Erreur de livraison",
    "notif.view": "Voir →",
    "notif.mark_read": "Marquer comme lu",
    "notif.delete": "Supprimer",
    "notif.previous": "Précédent",
    "notif.next": "Suivant",
    "notif.page_of": "Page {page} / {total}",
    "notif.deleted_toast": "Notification supprimée",
    "notif.marked_read_toast": "Toutes les notifications marquées comme lues",
    "notif.error_toast": "Erreur: {message}",
    "notif.admin_hint": "Astuce admin : pour envoyer une notification à un utilisateur spécifique, utilisez l'endpoint POST /api/v1/notifications/send avec la permission notification.send.",
    "notif.cat.system": "Système",
    "notif.cat.lab_result": "Résultat labo",
    "notif.cat.appointment": "Rendez-vous",
    "notif.cat.pharmacy": "Pharmacie",
    "notif.cat.billing": "Facturation",
    "notif.cat.emergency": "Urgence",
    "notif.time.now": "à l'instant",
    "notif.time.min_ago": "il y a {count} min",
    "notif.time.h_ago": "il y a {count} h",
    "notif.time.d_ago": "il y a {count} j",

    # ─── Common action additions (v1.9.0) ───
    "action.actualiser": "Actualiser",
    "action.reset": "Réinitialiser",
    "action.start": "Démarrer",
    "action.complete": "Terminer",
    "action.validate": "Valider",
    "action.approve": "Approuver",
    "action.reject": "Refuser",
    "action.activate": "Activer",
    "action.deactivate": "Désactiver",
    "action.view": "Voir",
    "action.detail": "Détail",
    "action.add_line": "Ajouter ligne",
    "action.schedule": "Planifier",

    # Common labels additions
    "label.department": "Service",
    "label.type": "Type",
    "label.reason": "Motif",
    "label.category": "Catégorie",
    "label.form": "Forme",
    "label.dosage": "Dosage",
    "label.code": "Code",
    "label.amount": "Montant",
    "label.method": "Mode",
    "label.reference": "Référence",
    "label.patient": "Patient",
    "label.doctor": "Médecin",
    "label.facility": "Établissement",
    "label.priority": "Priorité",
    "label.urgency": "Urgence",
    "label.quantity": "Quantité",
    "label.product": "Produit",
    "label.unit_price": "Prix unitaire",
    "label.active_only": "Actif",
    "label.inactive_only": "Inactif",
    "label.all_statuses": "Tous statuts",
    "label.all_types": "Tous types",
    "label.all_roles": "Tous les rôles",
    "label.all_departments": "Tous les services",
    "label.date_from": "Date début",
    "label.date_to": "Date fin",
    "label.choose": "— Choisir —",
    "label.empty.choice": "-- Choisir --",

    # ─── Admissions page (v1.9.0) ───
    "admissions.description": "Gestion des admissions, hospitalisations et sorties des patients.",
    "admissions.tab.dashboard": "Tableau",
    "admissions.tab.new": "Nouvelle admission",
    "admissions.tab.history": "Historique",
    "admissions.new.title": "Nouvelle admission",
    "admissions.new.subtitle": "Enregistrer une nouvelle admission de patient",
    "admissions.kpi.active": "Admissions actives",
    "admissions.kpi.today": "Prévues aujourd'hui",
    "admissions.kpi.hospitalized": "En hospitalisation",
    "admissions.kpi.discharges": "Sorties prévues",
    "admissions.button.dossier": "Dossier",
    "admissions.button.discharge": "Sortie",
    "admissions.submit.create": "Enregistrer l'admission",
    "admissions.submit.creating": "Enregistrement...",
    "admissions.discharge.confirm": "Confirmer la sortie de ce patient ?",
    "admissions.empty": "Aucune admission trouvée.",
    "admissions.empty_discharged": "Aucun patient sorti trouvé.",

    # ─── Lab page (v1.9.0) ───
    "lab.description": "Gestion des analyses, demandes et résultats de laboratoire.",
    "lab.tab.dashboard": "Tableau de bord",
    "lab.tab.orders": "Demandes",
    "lab.tab.results": "Résultats",
    "lab.tab.catalog": "Catalogue",
    "lab.orders.title": "Demandes d'analyses",
    "lab.orders.new": "Nouvelle demande",
    "lab.orders.empty": "Aucune demande trouvée.",
    "lab.results.title": "Résultats d'analyses",
    "lab.results.new": "Nouveau résultat",
    "lab.results.empty": "Aucun résultat enregistré.",
    "lab.catalog.title": "Catalogue des analyses",
    "lab.catalog.new": "Nouveau test",
    "lab.catalog.empty": "Aucun test enregistré.",

    # ─── Pharmacy page (v1.9.0) ───
    "pharmacy.description": "Gestion des stocks, dispensation et mouvements pharmaceutiques.",
    "pharmacy.tab.stock": "Stock",
    "pharmacy.tab.dispensation": "Dispensation",
    "pharmacy.tab.products": "Produits",
    "pharmacy.tab.movements": "Mouvements",
    "pharmacy.dispensation.new": "Nouvelle dispensation",
    "pharmacy.products.title": "Catalogue produits",
    "pharmacy.products.new": "Nouveau produit",
    "pharmacy.products.empty": "Aucun produit enregistré.",
    "pharmacy.movements.title": "Mouvements de stock",
    "pharmacy.movements.new": "Nouvelle entrée",
    "pharmacy.movements.empty": "Aucun mouvement enregistré.",

    # ─── Finance page (v1.9.0) ───
    "finance.description": "Gestion de la facturation, des paiements et des tarifs.",
    "finance.tab.dashboard": "Tableau de bord",
    "finance.tab.invoices": "Facturation",
    "finance.tab.payments": "Paiements",
    "finance.tab.tariffs": "Tarifs",
    "finance.invoices.title": "Facturation",
    "finance.invoices.new": "Nouvelle facture",
    "finance.invoices.empty": "Aucune facture trouvée.",
    "finance.payments.title": "Paiements",
    "finance.payments.new": "Enregistrer un paiement",
    "finance.payments.empty": "Aucun paiement enregistré.",
    "finance.tariffs.title": "Catalogue des tarifs",
    "finance.tariffs.new": "Nouveau tarif",
    "finance.tariffs.empty": "Aucun tarif enregistré.",

    # ─── Emergency page (v1.9.0) ───
    "emergency.stat.total": "Total patients",
    "emergency.stat.waiting": "En attente",
    "emergency.stat.triaged": "Triés",
    "emergency.stat.in_care": "En soins",
    "emergency.stat.oriented": "Orientés/Sortis",
    "emergency.stat.critical": "Critiques",
    "emergency.tab.dashboard": "Tableau",
    "emergency.tab.triage": "Triage",
    "emergency.tab.orientation": "Orientation",

    # ─── Surgery page (v1.9.0) ───
    "surgery.description": "Gestion des salles, programmations et comptes rendus chirurgicaux.",
    "surgery.tab.rooms": "Salles",
    "surgery.tab.schedules": "Programmation",
    "surgery.tab.reports": "Comptes rendus",
    "surgery.rooms.new": "Nouvelle salle",
    "surgery.rooms.empty": "Aucune salle opératoire configurée.",
    "surgery.schedules.title": "Programmation chirurgicale",
    "surgery.schedules.new": "Nouvelle programmation",
    "surgery.schedules.empty": "Aucune programmation trouvée.",
    "surgery.reports.title": "Comptes rendus opératoires",
    "surgery.reports.new": "Nouveau compte rendu",
    "surgery.reports.empty": "Aucun compte rendu trouvé.",

    # ─── Maternity page (v1.9.0) ───
    "maternity.description": "Suivi des grossesses, consultations prénatales et accouchements.",
    "maternity.tab.records": "Dossiers maternité",
    "maternity.tab.new_record": "Nouveau dossier",
    "maternity.tab.consultations": "Consultations",
    "maternity.tab.deliveries": "Accouchements",
    "maternity.records.new": "Nouveau dossier maternité",
    "maternity.records.empty": "Aucun dossier maternité enregistré.",
    "maternity.consultations.title": "Consultations prénatales",
    "maternity.consultations.new": "Nouvelle consultation",
    "maternity.deliveries.title": "Accouchements",
    "maternity.deliveries.new": "Nouvel accouchement",

    # ─── Personnel page (v1.9.0) ───
    "personnel.description": "Gestion du personnel, planning de garde, congés et contrats.",
    "personnel.tab.staff": "Personnel",
    "personnel.tab.oncall": "Gardes",
    "personnel.tab.leaves": "Congés",
    "personnel.tab.contracts": "Contrats",
    "personnel.tab.stats": "Statistiques",
    "personnel.staff.new": "Nouveau membre du personnel",
    "personnel.staff.empty": "Aucun membre du personnel trouvé.",
    "personnel.oncall.title": "Planning de garde",
    "personnel.oncall.new": "Planifier une garde",
    "personnel.oncall.empty": "Aucune garde planifiée.",
    "personnel.leaves.title": "Congés",
    "personnel.leaves.new": "Nouveau congé",
    "personnel.leaves.empty": "Aucun congé trouvé.",
    "personnel.contracts.title": "Contrats",
    "personnel.contracts.new": "Nouveau contrat",
    "personnel.contracts.empty": "Aucun contrat trouvé.",

    # ─── Users page (v1.9.0) ───
    "users.title": "Gestion des Utilisateurs",
    "users.description": "Création et gestion des comptes utilisateurs",
    "users.new": "Nouvel utilisateur",
    "users.empty": "Aucun utilisateur",
    "users.modal.title": "Nouvel utilisateur",
    "users.submit.create": "Créer l'utilisateur",

    # ─── Audit page (v1.9.0) ───
    "audit.description": "Traçabilité complète des actions sensibles — {total} entrée(s) au total",
    "audit.access_denied": "Accès refusé",
    "audit.access_denied_desc": "Seuls les administrateurs peuvent consulter le journal d'audit.",
    "audit.detail.title": "Détail de l'entrée d'audit",
    "audit.empty": "Aucune entrée d'audit trouvée.",
    "audit.button.refresh": "Actualiser",
}


# --- English catalog ---
_CATALOG_EN: dict[str, str] = {
    # Auth
    "auth.login.invalid_credentials": "Invalid credentials.",
    "auth.login.account_locked": "Account locked after {attempts} failed attempts. Try again in {minutes} minutes.",
    "auth.login.success": "Login successful.",
    "auth.logout.success": "Logout successful.",
    "auth.refresh.invalid": "Invalid or expired refresh token.",
    "auth.token.expired": "Token expired.",
    "auth.token.invalid": "Invalid token.",
    "auth.token.revoked": "Token revoked (jti blacklisted).",
    "auth.not_authenticated": "Not authenticated.",
    # RBAC
    "rbac.permission_denied": "Insufficient permission: {permission} required.",
    "rbac.role_required": "Insufficient role: {role} required.",
    # Multi-tenant
    "tenant.access_denied": "Access to facility {facility_id} denied.",
    # Common
    "common.not_found": "Resource not found.",
    "common.conflict": "Conflict — resource already exists or is in an invalid state.",
    "common.validation_error": "Validation error.",
    "common.internal_error": "Internal server error.",
    "common.rate_limited": "Too many requests. Try again in {seconds}s.",
    # Patients
    "patient.duplicate_number": "Patient number already in use: {patient_number}.",
    "patient.not_found": "Patient not found (id={patient_id}).",
    # Documents
    "documents.invalid_note_type": "Invalid note type — PRESCRIPTION required, got: {actual}.",
    "documents.not_found": "Source document not found.",
    # Feedback
    "feedback.not_found": "Feedback not found.",
    # i18n
    "i18n.unsupported_locale": "Unsupported locale: {locale}. Supported: {supported}.",

    # ─── UI essentials (v1.7.1) — used by frontend useT() ───

    # App / navigation
    "app.name": "GuinéeCare",
    "app.tagline": "Hospital Suite",
    "nav.section.care": "CARE",
    "nav.section.emergency": "EMERGENCY",
    "nav.section.services": "SERVICES",
    "nav.section.admin": "ADMIN",
    "nav.section.system": "SYSTEM",
    "nav.section.national": "NATIONAL",
    "nav.dashboard": "Dashboard",
    "nav.patients": "Patients",
    "nav.admissions": "Admissions",
    "nav.emergency": "Emergency",
    "nav.emergency.queue": "Queue",
    "nav.emergency.triage": "Triage",
    "nav.emergency.orientation": "Orientation",
    "nav.hospitalization": "Hospitalization",
    "nav.maternity": "Maternity",
    "nav.pharmacy": "Pharmacy",
    "nav.laboratory": "Laboratory",
    "nav.imaging": "Imaging",
    "nav.surgery": "Operating Room",
    "nav.billing": "Billing",
    "nav.personnel": "Staff",
    "nav.planning": "Planning & Shifts",
    "nav.leaves": "Leaves",
    "nav.quality": "Quality",
    "nav.reporting": "Reporting",
    "nav.notifications": "Notifications",
    "nav.activity": "Activity",
    "nav.users": "Users",
    "nav.rbac": "Roles & Permissions",
    "nav.facilities": "Facilities",
    "nav.departments": "Departments",
    "nav.audit": "Audit Log",
    "nav.sms_admin": "SMS Admin",
    "nav.national": "National Dashboard",
    "nav.profile": "Profile",
    "nav.logout": "Logout",
    "nav.search": "Search…",
    "nav.facility_connected": "Connected facility",
    "nav.national_view": "National view",

    # Common actions
    "action.save": "Save",
    "action.cancel": "Cancel",
    "action.delete": "Delete",
    "action.edit": "Edit",
    "action.create": "Create",
    "action.search": "Search",
    "action.filter": "Filter",
    "action.refresh": "Refresh",
    "action.export": "Export",
    "action.print": "Print",
    "action.back": "Back",
    "action.next": "Next",
    "action.previous": "Previous",
    "action.confirm": "Confirm",
    "action.close": "Close",
    "action.new": "New",
    "action.add": "Add",

    # Common labels
    "label.loading": "Loading…",
    "label.error": "Error",
    "label.success": "Success",
    "label.no_data": "No data",
    "label.retry": "Retry",
    "label.close": "Close",
    "label.view_all": "View all",
    "label.refresh": "Refresh",
    "label.no_results": "No results",
    "label.searching": "Searching…",
    "label.offline": "Offline",
    "label.online": "Online",
    "label.total": "Total",
    "label.status": "Status",
    "label.date": "Date",
    "label.name": "Name",
    "label.first_name": "First name",
    "label.last_name": "Last name",
    "label.email": "Email",
    "label.phone": "Phone",
    "label.address": "Address",
    "label.description": "Description",
    "label.notes": "Notes",
    "label.actions": "Actions",
    "label.page": "Page",
    "label.of": "of",
    "label.results": "result(s)",

    # Generic status labels — mirrors French catalog (status.*).
    "status.active": "Active",
    "status.inactive": "Inactive",
    "status.open": "Open",
    "status.closed": "Closed",
    "status.discharged": "Discharged",
    "status.pending": "Pending",
    "status.completed": "Completed",
    "status.in_progress": "In progress",
    "status.cancelled": "Cancelled",
    "status.validated": "Validated",
    "status.rejected": "Rejected",
    "status.enabled": "Enabled",
    "status.disabled": "Disabled",

    # Login page
    "login.title": "GuinéeCare",
    "login.subtitle": "Hospital Suite",
    "login.email": "Email",
    "login.password": "Password",
    "login.submit": "Sign in",
    "login.connecting": "Signing in…",
    "login.error": "Invalid credentials",
    "login.demo_link": "Use demo credentials",

    # Dashboard
    "dashboard.title": "Dashboard",
    "dashboard.welcome": "Hello",
    "dashboard.active_patients": "Active patients",
    "dashboard.active_admissions": "Active admissions",
    "dashboard.occupied_beds": "Occupied beds",
    "dashboard.emergencies": "Active emergencies",
    "dashboard.pending_lab": "Pending lab results",
    "dashboard.pending_imaging": "Pending imaging",
    "dashboard.revenue_today": "Today's revenue",
    "dashboard.outstanding": "Outstanding balance",

    # Patients
    "patients.title": "Patients",
    "patients.search_placeholder": "Search by name, number, ID…",
    "patients.new": "New patient",
    "patients.patient_number": "Patient #",
    "patients.age": "Age",
    "patients.gender": "Gender",
    "patients.male": "Male",
    "patients.female": "Female",
    "patients.active": "Active",

    # Patient detail
    "patient.detail.title": "Patient record",
    "patient.vitals": "Vital signs",
    "patient.lab_results": "Lab results",
    "patient.prescriptions": "Prescriptions",
    "patient.blood_type": "Blood type",
    "patient.allergies": "Allergies",
    "patient.medical_history": "Medical history",
    "patient.current_medication": "Current medication",
    "patient.chronic_conditions": "Chronic conditions",
    "patient.not_specified": "Not specified",
    "patient.add_vital": "Add vital sign",

    # Quality
    "quality.title": "Quality / Steering",
    "quality.dashboard": "Dashboard",
    "quality.alerts": "Alerts",
    "quality.indicators": "Indicators",
    "quality.measurements": "Measurements",
    "quality.incidents": "Adverse events",
    "quality.thresholds": "Thresholds",
    "quality.check_thresholds": "Check thresholds",
    "quality.seed_defaults": "Insert WHO/HAS indicators",
    "quality.description": "Management of quality indicators, measurements, adverse events and automatic alerts.",
    "quality.no_indicators": "No indicators found.",
    "quality.no_measurements": "No measurements found.",
    "quality.no_incidents": "No adverse events found.",

    # SMS admin
    "sms.title": "SMS Notifications — Administration",
    "sms.providers": "Providers",
    "sms.routing_rules": "Routing rules",
    "sms.history": "History",
    "sms.stats": "Statistics",

    # Notifications page
    "notif.title": "Notifications",
    "notif.unread_count": "{count} unread notification(s) of {total}",
    "notif.all_read": "{total} notification(s) — all read",
    "notif.mark_all_read": "Mark all as read",
    "notif.category": "Category",
    "notif.all_categories": "All",
    "notif.unread_only": "Unread only",
    "notif.refresh": "Refresh",
    "notif.loading": "Loading…",
    "notif.empty_title": "No notifications",
    "notif.empty_desc": "New notifications will appear here.",
    "notif.new_badge": "NEW",
    "notif.sent": "sent",
    "notif.failed": "failed",
    "notif.delivery_error": "⚠ Delivery error",
    "notif.view": "View →",
    "notif.mark_read": "Mark as read",
    "notif.delete": "Delete",
    "notif.previous": "Previous",
    "notif.next": "Next",
    "notif.page_of": "Page {page} of {total}",
    "notif.deleted_toast": "Notification deleted",
    "notif.marked_read_toast": "All notifications marked as read",
    "notif.error_toast": "Error: {message}",
    "notif.admin_hint": "Admin tip: to send a notification to a specific user, use the endpoint POST /api/v1/notifications/send with the permission notification.send.",
    "notif.cat.system": "System",
    "notif.cat.lab_result": "Lab result",
    "notif.cat.appointment": "Appointment",
    "notif.cat.pharmacy": "Pharmacy",
    "notif.cat.billing": "Billing",
    "notif.cat.emergency": "Emergency",
    "notif.time.now": "just now",
    "notif.time.min_ago": "{count} min ago",
    "notif.time.h_ago": "{count} h ago",
    "notif.time.d_ago": "{count} d ago",

    # ─── Common action additions (v1.9.0) ───
    "action.actualiser": "Refresh",
    "action.reset": "Reset",
    "action.start": "Start",
    "action.complete": "Complete",
    "action.validate": "Validate",
    "action.approve": "Approve",
    "action.reject": "Reject",
    "action.activate": "Activate",
    "action.deactivate": "Deactivate",
    "action.view": "View",
    "action.detail": "Detail",
    "action.add_line": "Add line",
    "action.schedule": "Schedule",

    # Common labels additions
    "label.department": "Department",
    "label.type": "Type",
    "label.reason": "Reason",
    "label.category": "Category",
    "label.form": "Form",
    "label.dosage": "Dosage",
    "label.code": "Code",
    "label.amount": "Amount",
    "label.method": "Method",
    "label.reference": "Reference",
    "label.patient": "Patient",
    "label.doctor": "Doctor",
    "label.facility": "Facility",
    "label.priority": "Priority",
    "label.urgency": "Urgency",
    "label.quantity": "Quantity",
    "label.product": "Product",
    "label.unit_price": "Unit price",
    "label.active_only": "Active",
    "label.inactive_only": "Inactive",
    "label.all_statuses": "All statuses",
    "label.all_types": "All types",
    "label.all_roles": "All roles",
    "label.all_departments": "All departments",
    "label.date_from": "From date",
    "label.date_to": "To date",
    "label.choose": "— Choose —",
    "label.empty.choice": "-- Choose --",

    # ─── Admissions page (v1.9.0) ───
    "admissions.description": "Management of patient admissions, hospitalizations and discharges.",
    "admissions.tab.dashboard": "Dashboard",
    "admissions.tab.new": "New admission",
    "admissions.tab.history": "History",
    "admissions.new.title": "New admission",
    "admissions.new.subtitle": "Register a new patient admission",
    "admissions.kpi.active": "Active admissions",
    "admissions.kpi.today": "Scheduled today",
    "admissions.kpi.hospitalized": "Hospitalized",
    "admissions.kpi.discharges": "Planned discharges",
    "admissions.button.dossier": "Record",
    "admissions.button.discharge": "Discharge",
    "admissions.submit.create": "Save admission",
    "admissions.submit.creating": "Saving...",
    "admissions.discharge.confirm": "Confirm the discharge of this patient?",
    "admissions.empty": "No admission found.",
    "admissions.empty_discharged": "No discharged patient found.",

    # ─── Lab page (v1.9.0) ───
    "lab.description": "Management of laboratory tests, orders and results.",
    "lab.tab.dashboard": "Dashboard",
    "lab.tab.orders": "Orders",
    "lab.tab.results": "Results",
    "lab.tab.catalog": "Catalog",
    "lab.orders.title": "Lab orders",
    "lab.orders.new": "New order",
    "lab.orders.empty": "No order found.",
    "lab.results.title": "Lab results",
    "lab.results.new": "New result",
    "lab.results.empty": "No result recorded.",
    "lab.catalog.title": "Test catalog",
    "lab.catalog.new": "New test",
    "lab.catalog.empty": "No test recorded.",

    # ─── Pharmacy page (v1.9.0) ───
    "pharmacy.description": "Management of stock, dispensation and pharmaceutical movements.",
    "pharmacy.tab.stock": "Stock",
    "pharmacy.tab.dispensation": "Dispensation",
    "pharmacy.tab.products": "Products",
    "pharmacy.tab.movements": "Movements",
    "pharmacy.dispensation.new": "New dispensation",
    "pharmacy.products.title": "Product catalog",
    "pharmacy.products.new": "New product",
    "pharmacy.products.empty": "No product recorded.",
    "pharmacy.movements.title": "Stock movements",
    "pharmacy.movements.new": "New entry",
    "pharmacy.movements.empty": "No movement recorded.",

    # ─── Finance page (v1.9.0) ───
    "finance.description": "Management of billing, payments and tariffs.",
    "finance.tab.dashboard": "Dashboard",
    "finance.tab.invoices": "Invoices",
    "finance.tab.payments": "Payments",
    "finance.tab.tariffs": "Tariffs",
    "finance.invoices.title": "Invoices",
    "finance.invoices.new": "New invoice",
    "finance.invoices.empty": "No invoice found.",
    "finance.payments.title": "Payments",
    "finance.payments.new": "Record a payment",
    "finance.payments.empty": "No payment recorded.",
    "finance.tariffs.title": "Tariff catalog",
    "finance.tariffs.new": "New tariff",
    "finance.tariffs.empty": "No tariff recorded.",

    # ─── Emergency page (v1.9.0) ───
    "emergency.stat.total": "Total patients",
    "emergency.stat.waiting": "Waiting",
    "emergency.stat.triaged": "Triaged",
    "emergency.stat.in_care": "In care",
    "emergency.stat.oriented": "Oriented/Discharged",
    "emergency.stat.critical": "Critical",
    "emergency.tab.dashboard": "Dashboard",
    "emergency.tab.triage": "Triage",
    "emergency.tab.orientation": "Orientation",

    # ─── Surgery page (v1.9.0) ───
    "surgery.description": "Management of operating rooms, schedules and surgical reports.",
    "surgery.tab.rooms": "Rooms",
    "surgery.tab.schedules": "Scheduling",
    "surgery.tab.reports": "Reports",
    "surgery.rooms.new": "New room",
    "surgery.rooms.empty": "No operating room configured.",
    "surgery.schedules.title": "Surgical scheduling",
    "surgery.schedules.new": "New schedule",
    "surgery.schedules.empty": "No schedule found.",
    "surgery.reports.title": "Operative reports",
    "surgery.reports.new": "New report",
    "surgery.reports.empty": "No report found.",

    # ─── Maternity page (v1.9.0) ───
    "maternity.description": "Monitoring of pregnancies, prenatal consultations and deliveries.",
    "maternity.tab.records": "Maternity records",
    "maternity.tab.new_record": "New record",
    "maternity.tab.consultations": "Consultations",
    "maternity.tab.deliveries": "Deliveries",
    "maternity.records.new": "New maternity record",
    "maternity.records.empty": "No maternity record registered.",
    "maternity.consultations.title": "Prenatal consultations",
    "maternity.consultations.new": "New consultation",
    "maternity.deliveries.title": "Deliveries",
    "maternity.deliveries.new": "New delivery",

    # ─── Personnel page (v1.9.0) ───
    "personnel.description": "Staff management, on-call planning, leaves and contracts.",
    "personnel.tab.staff": "Staff",
    "personnel.tab.oncall": "On-call",
    "personnel.tab.leaves": "Leaves",
    "personnel.tab.contracts": "Contracts",
    "personnel.tab.stats": "Statistics",
    "personnel.staff.new": "New staff member",
    "personnel.staff.empty": "No staff member found.",
    "personnel.oncall.title": "On-call planning",
    "personnel.oncall.new": "Schedule on-call",
    "personnel.oncall.empty": "No on-call scheduled.",
    "personnel.leaves.title": "Leaves",
    "personnel.leaves.new": "New leave",
    "personnel.leaves.empty": "No leave found.",
    "personnel.contracts.title": "Contracts",
    "personnel.contracts.new": "New contract",
    "personnel.contracts.empty": "No contract found.",

    # ─── Users page (v1.9.0) ───
    "users.title": "User Management",
    "users.description": "Creation and management of user accounts",
    "users.new": "New user",
    "users.empty": "No user",
    "users.modal.title": "New user",
    "users.submit.create": "Create user",

    # ─── Audit page (v1.9.0) ───
    "audit.description": "Full traceability of sensitive actions — {total} entry(ies) total",
    "audit.access_denied": "Access denied",
    "audit.access_denied_desc": "Only administrators can view the audit log.",
    "audit.detail.title": "Audit entry detail",
    "audit.empty": "No audit entry found.",
    "audit.button.refresh": "Refresh",
}


_CATALOGS: dict[str, dict[str, str]] = {
    "fr": _CATALOG_FR,
    "en": _CATALOG_EN,
}


class _SafeDict(dict):
    """dict subclass that returns '' for missing keys (for str.format_map)."""

    def __missing__(self, key: str) -> str:
        return ""


def negotiate_locale(accept_language: str | None) -> str:
    """Map an `Accept-Language` header value to a supported locale.

    Examples:
    - `"fr-FR,fr;q=0.9,en;q=0.8"` → `"fr"`
    - `"en-US,en;q=0.9"` → `"en"`
    - `None` / `""` / `"de-DE"` → `DEFAULT_LOCALE`

    Algorithm: parse the header, sort by quality, return the first
    language whose primary subtag matches a supported locale. Falls
    back to DEFAULT_LOCALE.
    """
    if not accept_language:
        return DEFAULT_LOCALE

    # Parse "fr-FR,fr;q=0.9,en;q=0.8" → [("fr-FR", 1.0), ("fr", 0.9), ("en", 0.8)]
    entries: list[tuple[str, float]] = []
    for part in accept_language.split(","):
        part = part.strip()
        if not part:
            continue
        if ";" in part:
            lang, params = part.split(";", 1)
            q = 1.0
            for p in params.split(";"):
                p = p.strip()
                if p.startswith("q="):
                    try:
                        q = float(p[2:])
                    except ValueError:
                        q = 1.0
            entries.append((lang.strip().lower(), q))
        else:
            entries.append((part.lower(), 1.0))

    # Sort by descending quality
    entries.sort(key=lambda e: e[1], reverse=True)

    for lang, _ in entries:
        # Take the primary subtag ("fr-fr" → "fr")
        primary = lang.split("-")[0]
        if primary in SUPPORTED_LOCALES:
            return primary

    return DEFAULT_LOCALE


def translate(key: str, locale: str | None = None, **variables: Any) -> str:
    """Translate a dotted key into the negotiated locale.

    Resolution order:
    1. Look up `key` in the catalog for `locale`.
    2. If missing, fall back to the DEFAULT_LOCALE catalog.
    3. If still missing, return the key itself and log a warning.

    Variables are interpolated via `str.format_map` with a safe dict
    (missing variables render as empty strings, no KeyError).
    """
    loc = locale if locale in SUPPORTED_LOCALES else DEFAULT_LOCALE
    catalog = _CATALOGS.get(loc, _CATALOG_FR)

    value = catalog.get(key)
    if value is None:
        # Fallback to default locale
        if loc != DEFAULT_LOCALE:
            value = _CATALOG_FR.get(key)
        if value is None:
            logger.warning("i18n.missing_key key=%s locale=%s", key, loc)
            return key

    if variables:
        try:
            return value.format_map(_SafeDict(variables))
        except (IndexError, ValueError):
            logger.warning("i18n.format_error key=%s locale=%s vars=%s", key, loc, variables)
            return value
    return value


def get_catalog(locale: str) -> dict[str, str]:
    """Return the full catalog for a locale (or the default if unsupported)."""
    if locale not in SUPPORTED_LOCALES:
        raise ValueError(f"Unsupported locale: {locale}")
    return dict(_CATALOGS[locale])
