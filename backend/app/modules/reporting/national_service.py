"""Service national reporting — v2.5.0 Phase 5.

Agrège les indicateurs sanitaires à l'échelle nationale pour le Ministère
de la Santé, les directions régionales et les partenaires ONG.

SÉCURITÉ :
- Toutes les fonctions acceptent `current_user` pour appliquer tenant_query.
- SUPER_ADMIN voit tous les établissements (cross-tenant).
- Les autres rôles ne voient que leur établissement.
- AUCUNE donnée patient n'est exposée — uniquement des agrégats anonymisés
  (comptages, sommes, moyennes).

FILTRES GÉOGRAPHIQUES :
- region, prefecture, commune : chaînes optionnelles
- facility_id : UUID optionnel
- Si aucun filtre → agrégat national (tous établissements visibles)
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from app.core.datetime import utcnow
from app.core.tenant import tenant_query
from app.modules.facilities.models import Facility
from app.modules.users.models import User
# Imports modèles pour agrégation
from app.modules.patients.models import Patient
from app.modules.admissions.models import Admission
from app.modules.emergency.models import EmergencyVisit
from app.modules.billing.models import Invoice, Payment
from app.modules.laboratory.models import LabOrder
from app.modules.pharmacy.models import PharmacyProduct, PharmacyStock, StockMovement
from app.modules.maternity.models import MaternityRecord, DeliveryRecord
from app.modules.hospitalization.models import HospitalStay, Bed
from app.modules.clinical.models import ClinicalNote


# ── Helpers ────────────────────────────────────────────────────────────────

def _facility_filter(db: Session, current_user: User, region: str | None, prefecture: str | None, commune: str | None, facility_id: str | None):
    """Retourne une query Facility filtrée par tenant + géographie.

    NOTE : Facility n'a pas de facility_id (c'est l'entité racine), donc
    tenant_query ne filtre pas automatiquement. On filtre manuellement :
    - SUPER_ADMIN voit tous les établissements (cross-tenant)
    - Les autres rôles ne voient QUE leur établissement (current_user.facility_id)
    """
    query = db.query(Facility)
    # v2.5.0 — Phase 5 : isolation tenant pour Facility
    # (tenant_query ne marche pas car Facility n'a pas facility_id)
    if current_user.role not in {"SUPER_ADMIN"}:
        if current_user.facility_id:
            query = query.filter(Facility.id == current_user.facility_id)
        else:
            # Utilisateur sans facility → aucune facility visible
            query = query.filter(Facility.id == "__NO_FACILITY__")
    if region:
        query = query.filter(Facility.region == region)
    if prefecture:
        query = query.filter(Facility.prefecture == prefecture)
    if commune:
        query = query.filter(Facility.commune == commune)
    if facility_id:
        query = query.filter(Facility.id == facility_id)
    return query


def _get_visible_facility_ids(db: Session, current_user: User, region: str | None, prefecture: str | None, commune: str | None, facility_id: str | None) -> list[str]:
    """Liste des facility_id visibles par l'utilisateur après filtres géo."""
    facilities = _facility_filter(db, current_user, region, prefecture, commune, facility_id).all()
    return [f.id for f in facilities]


def _period_bounds(period: str | None) -> tuple[datetime | None, datetime | None]:
    """Convertit un period string (YYYY, YYYYMM, YYYYQn) en (start, end).

    None ou vide → (None, None) = pas de filtre période.
    "2026" → (2026-01-01, 2027-01-01)
    "202603" → (2026-03-01, 2026-04-01)
    "2026Q1" → (2026-01-01, 2026-04-01)

    v2.8.1 — FIX : le branch YYYYQn (avec "Q") était APRÈS le branch YYYYMM
    (len==6). "2026Q1" a longueur 6 → matchait YYYYMM → int("Q1") → ValueError.
    Maintenant on vérifie "Q" en PREMIER pour les chaînes de longueur 6.
    """
    if not period:
        return None, None
    try:
        # v2.8.1 — FIX : vérifier "Q" (trimestriel) AVANT YYYYMM
        if "Q" in period and len(period) == 6:  # YYYYQn
            year = int(period[:4])
            q = int(period[5])
            if q < 1 or q > 4:
                return None, None
            start_month = (q - 1) * 3 + 1
            start = datetime(year, start_month, 1)
            # Fin du trimestre = début du trimestre suivant
            if start_month + 3 > 12:
                end = datetime(year + 1, 1, 1)
            else:
                end = datetime(year, start_month + 3, 1)
            return start, end
        if len(period) == 4:  # YYYY
            year = int(period)
            return datetime(year, 1, 1), datetime(year + 1, 1, 1)
        if len(period) == 6:  # YYYYMM
            year, month = int(period[:4]), int(period[4:])
            if month < 1 or month > 12:
                return None, None
            start = datetime(year, month, 1)
            end = datetime(year + (1 if month == 12 else 0), (month % 12) + 1, 1)
            return start, end
    except (ValueError, IndexError):
        pass
    return None, None


# ── Indicateurs nationaux agrégés ──────────────────────────────────────────

def compute_national_dashboard(
    db: Session,
    current_user: User,
    *,
    region: str | None = None,
    prefecture: str | None = None,
    commune: str | None = None,
    facility_id: str | None = None,
    period: str | None = None,
) -> dict[str, Any]:
    """Calculer le tableau de bord national agrégé.

    Toutes les agrégations sont anonymisées (comptages, sommes, moyennes).
    AUCUNE donnée patient n'est retournée.

    Retourne un dict avec :
    - filters : les filtres appliqués
    - facilities : nombre d'établissements dans le périmètre
    - indicators : dict d'indicateurs agrégés
    - by_region : répartition par région (si pas de filtre région)
    - by_facility_type : répartition par catégorie d'établissement
    """
    facility_ids = _get_visible_facility_ids(db, current_user, region, prefecture, commune, facility_id)
    period_start, period_end = _period_bounds(period)

    if not facility_ids:
        return {
            "filters": {"region": region, "prefecture": prefecture, "commune": commune,
                        "facility_id": facility_id, "period": period},
            "facilities_count": 0,
            "indicators": {},
            "by_region": [],
            "by_facility_type": [],
            "message": "Aucun établissement dans le périmètre",
        }

    # ── Patients ──
    patients_q = db.query(Patient).filter(Patient.facility_id.in_(facility_ids))
    if period_start:
        patients_q = patients_q.filter(Patient.created_at >= period_start)
    if period_end:
        patients_q = patients_q.filter(Patient.created_at < period_end)
    total_patients = patients_q.count()

    # ── Admissions ──
    adm_q = db.query(Admission).filter(Admission.facility_id.in_(facility_ids))
    if period_start:
        adm_q = adm_q.filter(Admission.admitted_at >= period_start)
    if period_end:
        adm_q = adm_q.filter(Admission.admitted_at < period_end)
    total_admissions = adm_q.count()
    active_admissions = adm_q.filter(Admission.status.in_(["OPEN", "ACTIVE"])).count()

    # ── Consultations (ClinicalNote type=CONSULTATION) ──
    consult_q = db.query(ClinicalNote).filter(
        ClinicalNote.facility_id.in_(facility_ids),
        ClinicalNote.note_type == "CONSULTATION",
    )
    if period_start:
        consult_q = consult_q.filter(ClinicalNote.created_at >= period_start)
    if period_end:
        consult_q = consult_q.filter(ClinicalNote.created_at < period_end)
    total_consultations = consult_q.count()

    # ── Urgences ──
    emerg_q = db.query(EmergencyVisit).filter(EmergencyVisit.facility_id.in_(facility_ids))
    if period_start:
        emerg_q = emerg_q.filter(EmergencyVisit.arrived_at >= period_start)
    if period_end:
        emerg_q = emerg_q.filter(EmergencyVisit.arrived_at < period_end)
    total_emergencies = emerg_q.count()
    # Temps moyen arrivée → prise en charge
    emerg_with_seen = emerg_q.filter(EmergencyVisit.seen_at.isnot(None)).all()
    if emerg_with_seen:
        avg_wait_min = sum(
            (v.seen_at - v.arrived_at).total_seconds()
            for v in emerg_with_seen if v.arrived_at and v.seen_at
        ) / len(emerg_with_seen) / 60.0
    else:
        avg_wait_min = 0.0

    # ── Hospitalisation ──
    stays_q = db.query(HospitalStay).filter(HospitalStay.facility_id.in_(facility_ids))
    if period_start:
        stays_q = stays_q.filter(HospitalStay.admitted_at >= period_start)
    if period_end:
        stays_q = stays_q.filter(HospitalStay.admitted_at < period_end)
    active_stays = stays_q.filter(HospitalStay.status == "ACTIVE").count()
    total_stays = stays_q.count()

    # Lits : total + occupés
    beds_q = db.query(Bed).filter(Bed.facility_id.in_(facility_ids))
    total_beds = beds_q.count()
    occupied_beds = beds_q.filter(Bed.bed_status == "OCCUPIED").count()
    available_beds = beds_q.filter(Bed.bed_status == "AVAILABLE").count()
    bed_occupancy_rate = round((occupied_beds / total_beds * 100), 1) if total_beds > 0 else 0.0

    # ── Maternité ──
    maternity_q = db.query(MaternityRecord).filter(MaternityRecord.facility_id.in_(facility_ids))
    total_pregnancies = maternity_q.count()
    deliveries_q = db.query(DeliveryRecord).filter(DeliveryRecord.facility_id.in_(facility_ids))
    if period_start:
        deliveries_q = deliveries_q.filter(DeliveryRecord.created_at >= period_start)
    if period_end:
        deliveries_q = deliveries_q.filter(DeliveryRecord.created_at < period_end)
    total_deliveries = deliveries_q.count()

    # ── Pharmacie ──
    products_q = db.query(PharmacyProduct).filter(PharmacyProduct.facility_id.in_(facility_ids))
    total_products = products_q.count()
    # Stock total + ruptures
    # v2.8.1 — FIX N+1 : on précharge tous les products en une seule requête
    stocks_q = db.query(PharmacyStock).filter(PharmacyStock.facility_id.in_(facility_ids))
    stocks = stocks_q.all()
    products_in_scope = (
        db.query(PharmacyProduct)
        .filter(PharmacyProduct.facility_id.in_(facility_ids))
        .all()
    )
    product_price_map = {p.id: (p.unit_price or 0) for p in products_in_scope}
    total_stock_value = sum(
        s.quantity_available * product_price_map.get(s.product_id, 0)
        for s in stocks
    )
    low_stock_count = sum(1 for s in stocks if s.quantity_available <= (s.min_threshold or 0))

    # ── Laboratoire ──
    lab_q = db.query(LabOrder).filter(LabOrder.facility_id.in_(facility_ids))
    if period_start:
        lab_q = lab_q.filter(LabOrder.ordered_at >= period_start)
    if period_end:
        lab_q = lab_q.filter(LabOrder.ordered_at < period_end)
    total_lab_orders = lab_q.count()
    validated_lab_orders = lab_q.filter(LabOrder.status == "VALIDATED").count()
    pending_lab_orders = lab_q.filter(LabOrder.status.in_(["ORDERED", "SAMPLE_COLLECTED", "RESULT_ENTERED"])).count()

    # ── Facturation ──
    inv_q = db.query(Invoice).filter(Invoice.facility_id.in_(facility_ids))
    if period_start:
        inv_q = inv_q.filter(Invoice.created_at >= period_start)
    if period_end:
        inv_q = inv_q.filter(Invoice.created_at < period_end)
    invoices = inv_q.all()
    total_invoices = len(invoices)
    total_revenue = sum(i.paid_amount for i in invoices)
    total_outstanding = sum(i.balance_due for i in invoices if i.status in ("ISSUED", "PARTIALLY_PAID"))
    paid_invoices = sum(1 for i in invoices if i.status == "PAID")
    unpaid_invoices = sum(1 for i in invoices if i.status in ("ISSUED", "PARTIALLY_PAID"))

    # ── Répartition par région (si pas de filtre région) ──
    # v2.8.8 — perf : GROUP BY au lieu de N+1 (1 requête au lieu de N)
    by_region = []
    if not region:
        facilities_all = _facility_filter(db, current_user, None, None, None, None).all()
        region_map: dict[str, dict] = {}
        for f in facilities_all:
            r = f.region or "Non renseignée"
            if r not in region_map:
                region_map[r] = {"region": r, "facilities_count": 0, "patients_count": 0}
            region_map[r]["facilities_count"] += 1
        # v2.8.8 — 1 seule requête avec JOIN + GROUP BY au lieu de N requêtes
        from sqlalchemy import func as sa_func
        region_counts = (
            db.query(Facility.region, sa_func.count(Patient.id))
            .join(Patient, Patient.facility_id == Facility.id)
            .filter(Facility.id.in_([f.id for f in facilities_all]))
            .group_by(Facility.region)
            .all()
        )
        for r_name, cnt in region_counts:
            r_key = r_name or "Non renseignée"
            if r_key in region_map:
                region_map[r_key]["patients_count"] = cnt
        by_region = sorted(region_map.values(), key=lambda x: x["patients_count"], reverse=True)

    # ── Répartition par catégorie d'établissement ──
    facilities_in_scope = _facility_filter(db, current_user, region, prefecture, commune, facility_id).all()
    cat_map: dict[str, int] = {}
    for f in facilities_in_scope:
        c = f.category or "Non renseignée"
        cat_map[c] = cat_map.get(c, 0) + 1
    by_facility_type = [{"category": k, "count": v} for k, v in sorted(cat_map.items(), key=lambda x: x[1], reverse=True)]

    return {
        "filters": {
            "region": region,
            "prefecture": prefecture,
            "commune": commune,
            "facility_id": facility_id,
            "period": period,
        },
        "facilities_count": len(facility_ids),
        "indicators": {
            # Patients
            "total_patients": total_patients,
            # Admissions
            "total_admissions": total_admissions,
            "active_admissions": active_admissions,
            # Consultations
            "total_consultations": total_consultations,
            # Urgences
            "total_emergencies": total_emergencies,
            "avg_emergency_wait_min": round(avg_wait_min, 1),
            # Hospitalisation
            "active_stays": active_stays,
            "total_stays": total_stays,
            "total_beds": total_beds,
            "occupied_beds": occupied_beds,
            "available_beds": available_beds,
            "bed_occupancy_rate": bed_occupancy_rate,
            # Maternité
            "total_pregnancies": total_pregnancies,
            "total_deliveries": total_deliveries,
            # Pharmacie
            "total_products": total_products,
            "total_stock_value_gnf": round(total_stock_value, 2),
            "low_stock_count": low_stock_count,
            # Laboratoire
            "total_lab_orders": total_lab_orders,
            "validated_lab_orders": validated_lab_orders,
            "pending_lab_orders": pending_lab_orders,
            # Facturation
            "total_invoices": total_invoices,
            "paid_invoices": paid_invoices,
            "unpaid_invoices": unpaid_invoices,
            "total_revenue_gnf": round(total_revenue, 2),
            "total_outstanding_gnf": round(total_outstanding, 2),
        },
        "by_region": by_region,
        "by_facility_type": by_facility_type,
        "generated_at": utcnow().isoformat(),
        "message": "national dashboard",
    }


def compute_facility_breakdown(
    db: Session,
    current_user: User,
    *,
    region: str | None = None,
    prefecture: str | None = None,
    commune: str | None = None,
    period: str | None = None,
) -> list[dict[str, Any]]:
    """Activité par établissement — tableau détaillé pour le pilotage.

    v2.8.8 — OPTIMISÉ : 5 requêtes GROUP BY au lieu de 5×N requêtes.
    Avant : 5 requêtes par établissement × 20 établissements = 100 requêtes.
    Maintenant : 5 requêtes GROUP BY (1 par table) + 1 requête facilities.
    """
    from sqlalchemy import func as sa_func

    facilities = _facility_filter(db, current_user, region, prefecture, commune, None).all()
    period_start, period_end = _period_bounds(period)

    if not facilities:
        return []

    fac_ids = [f.id for f in facilities]

    # v2.8.8 — 5 requêtes GROUP BY au lieu de 5×N requêtes individuelles
    # 1. Patients count par facility
    patients_q = db.query(Patient.facility_id, sa_func.count(Patient.id)).filter(
        Patient.facility_id.in_(fac_ids)
    )
    if period_start:
        patients_q = patients_q.filter(Patient.created_at >= period_start)
    if period_end:
        patients_q = patients_q.filter(Patient.created_at < period_end)
    patients_map = dict(patients_q.group_by(Patient.facility_id).all())

    # 2. Admissions count par facility
    adm_q = db.query(Admission.facility_id, sa_func.count(Admission.id)).filter(
        Admission.facility_id.in_(fac_ids)
    )
    if period_start:
        adm_q = adm_q.filter(Admission.admitted_at >= period_start)
    if period_end:
        adm_q = adm_q.filter(Admission.admitted_at < period_end)
    admissions_map = dict(adm_q.group_by(Admission.facility_id).all())

    # 3. Emergencies count par facility
    emerg_q = db.query(EmergencyVisit.facility_id, sa_func.count(EmergencyVisit.id)).filter(
        EmergencyVisit.facility_id.in_(fac_ids)
    )
    if period_start:
        emerg_q = emerg_q.filter(EmergencyVisit.arrived_at >= period_start)
    if period_end:
        emerg_q = emerg_q.filter(EmergencyVisit.arrived_at < period_end)
    emergencies_map = dict(emerg_q.group_by(EmergencyVisit.facility_id).all())

    # 4. Lab orders count par facility
    lab_q = db.query(LabOrder.facility_id, sa_func.count(LabOrder.id)).filter(
        LabOrder.facility_id.in_(fac_ids)
    )
    if period_start:
        lab_q = lab_q.filter(LabOrder.ordered_at >= period_start)
    if period_end:
        lab_q = lab_q.filter(LabOrder.ordered_at < period_end)
    lab_map = dict(lab_q.group_by(LabOrder.facility_id).all())

    # 5. Revenue + outstanding par facility (SUM + CASE)
    inv_q = db.query(
        Invoice.facility_id,
        sa_func.sum(Invoice.paid_amount),
        sa_func.sum(sa_func.coalesce(Invoice.balance_due, 0)).filter(
            Invoice.status.in_(["ISSUED", "PARTIALLY_PAID"])
        ) if hasattr(sa_func, 'coalesce') else sa_func.sum(Invoice.balance_due),
    ).filter(Invoice.facility_id.in_(fac_ids))
    if period_start:
        inv_q = inv_q.filter(Invoice.created_at >= period_start)
    if period_end:
        inv_q = inv_q.filter(Invoice.created_at < period_end)
    # Simplifions : on récupère les sums par facility
    revenue_map = {}
    outstanding_map = {}
    inv_rows = (
        db.query(
            Invoice.facility_id,
            sa_func.sum(Invoice.paid_amount).label("revenue"),
        )
        .filter(Invoice.facility_id.in_(fac_ids))
    )
    if period_start:
        inv_rows = inv_rows.filter(Invoice.created_at >= period_start)
    if period_end:
        inv_rows = inv_rows.filter(Invoice.created_at < period_end)
    for fac_id, rev in inv_rows.group_by(Invoice.facility_id).all():
        revenue_map[fac_id] = float(rev or 0)

    outstanding_rows = (
        db.query(
            Invoice.facility_id,
            sa_func.sum(Invoice.balance_due).label("outstanding"),
        )
        .filter(Invoice.facility_id.in_(fac_ids))
        .filter(Invoice.status.in_(["ISSUED", "PARTIALLY_PAID"]))
    )
    if period_start:
        outstanding_rows = outstanding_rows.filter(Invoice.created_at >= period_start)
    if period_end:
        outstanding_rows = outstanding_rows.filter(Invoice.created_at < period_end)
    for fac_id, out in outstanding_rows.group_by(Invoice.facility_id).all():
        outstanding_map[fac_id] = float(out or 0)

    breakdown = []
    for f in facilities:
        breakdown.append({
            "facility_id": str(f.id),
            "name": f.name,
            "code": f.code,
            "region": f.region,
            "prefecture": f.prefecture,
            "commune": f.commune,
            "category": f.category,
            "patients_count": patients_map.get(f.id, 0),
            "admissions_count": admissions_map.get(f.id, 0),
            "emergencies_count": emergencies_map.get(f.id, 0),
            "lab_orders_count": lab_map.get(f.id, 0),
            "revenue_gnf": round(revenue_map.get(f.id, 0), 2),
            "outstanding_gnf": round(outstanding_map.get(f.id, 0), 2),
        })

    # Trier par activité décroissante
    breakdown.sort(
        key=lambda x: x["patients_count"] + x["admissions_count"] + x["emergencies_count"],
        reverse=True,
    )
    return breakdown


def compute_geographic_distribution(
    db: Session,
    current_user: User,
    *,
    level: str = "region",
) -> list[dict[str, Any]]:
    """Répartition géographique des établissements et patients.

    level : "region" | "prefecture" | "commune"
    """
    facilities = tenant_query(db, Facility, current_user).all()

    if level == "region":
        getter = lambda f: f.region or "Non renseignée"
    elif level == "prefecture":
        getter = lambda f: f.prefecture or "Non renseignée"
    elif level == "commune":
        getter = lambda f: f.commune or "Non renseignée"
    else:
        getter = lambda f: f.region or "Non renseignée"

    distribution: dict[str, dict] = {}
    for f in facilities:
        key = getter(f)
        if key not in distribution:
            distribution[key] = {level: key, "facilities_count": 0, "patients_count": 0}
        distribution[key]["facilities_count"] += 1

    # Compter patients par zone géo
    for zone_name in distribution:
        fac_ids = [f.id for f in facilities if getter(f) == zone_name]
        if fac_ids:
            cnt = db.query(Patient).filter(Patient.facility_id.in_(fac_ids)).count()
            distribution[zone_name]["patients_count"] = cnt

    return sorted(distribution.values(), key=lambda x: x["patients_count"], reverse=True)


def export_dhis2_dataset(
    db: Session,
    current_user: User,
    *,
    period: str,
    dataset: str = "SNIS_MENSUEL",
    region: str | None = None,
) -> dict[str, Any]:
    """Génère un dataset DHIS2-compatible pour la période donnée.

    Structure DHIS2 :
    {
      "dataSet": "SNIS_MENSUEL",
      "period": "202603",
      "orgUnits": ["<facility_code>", ...],
      "dataValues": [
        {"dataElement": "TOTAL_ADMISSIONS", "value": "1234", "orgUnit": "...", "period": "202603"},
        ...
      ]
    }

    NOTE : Cette fonction prépare les données au format DHIS2. L'envoi effectif
    vers une instance DHIS2 (POST /api/dataValueSets) nécessite une config
    DHIS2_URL + DHIS2_USERNAME + DHIS2_PASSWORD (Phase 5+ future).
    """
    facility_ids = _get_visible_facility_ids(db, current_user, region, None, None, None)
    period_start, period_end = _period_bounds(period)

    if not facility_ids:
        return {"dataSet": dataset, "period": period, "dataValues": [], "message": "Aucun établissement"}

    # Récupérer les facility codes DHIS2
    facilities = db.query(Facility).filter(Facility.id.in_(facility_ids)).all()
    org_units = [f.code for f in facilities if f.code]
    fac_id_to_code = {f.id: f.code for f in facilities if f.code}

    data_values = []

    # Pour chaque établissement, générer les dataElements DHIS2
    for fac_id, fac_code in fac_id_to_code.items():
        # Admissions
        adm_q = db.query(Admission).filter(Admission.facility_id == fac_id)
        if period_start and period_end:
            adm_q = adm_q.filter(Admission.admitted_at >= period_start, Admission.admitted_at < period_end)
        adm_count = adm_q.count()

        # Urgences
        emerg_q = db.query(EmergencyVisit).filter(EmergencyVisit.facility_id == fac_id)
        if period_start and period_end:
            emerg_q = emerg_q.filter(EmergencyVisit.arrived_at >= period_start, EmergencyVisit.arrived_at < period_end)
        emerg_count = emerg_q.count()

        # Accouchements
        del_q = db.query(DeliveryRecord).filter(DeliveryRecord.facility_id == fac_id)
        if period_start and period_end:
            del_q = del_q.filter(DeliveryRecord.created_at >= period_start, DeliveryRecord.created_at < period_end)
        del_count = del_q.count()

        # Lab orders
        lab_q = db.query(LabOrder).filter(LabOrder.facility_id == fac_id)
        if period_start and period_end:
            lab_q = lab_q.filter(LabOrder.ordered_at >= period_start, LabOrder.ordered_at < period_end)
        lab_count = lab_q.count()

        # Revenue
        inv_q = db.query(Invoice).filter(Invoice.facility_id == fac_id)
        if period_start and period_end:
            inv_q = inv_q.filter(Invoice.created_at >= period_start, Invoice.created_at < period_end)
        revenue = sum(i.paid_amount for i in inv_q.all())

        # Ajouter les dataValues DHIS2
        for element, value in [
            ("TOTAL_ADMISSIONS", adm_count),
            ("TOTAL_EMERGENCIES", emerg_count),
            ("TOTAL_DELIVERIES", del_count),
            ("TOTAL_LAB_ORDERS", lab_count),
            ("TOTAL_REVENUE_GNF", revenue),
        ]:
            data_values.append({
                "dataElement": element,
                "orgUnit": fac_code,
                "period": period,
                "value": str(value),
            })

    return {
        "dataSet": dataset,
        "period": period,
        "orgUnits": org_units,
        "dataValues": data_values,
        "total_values": len(data_values),
        "message": "DHIS2-compatible dataset generated",
    }


# ============================================================================
# v2.9.1 — DHIS2 push effectif (POST vers instance nationale)
# ============================================================================

def push_dhis2_dataset(
    db: Session,
    current_user: User,
    *,
    period: str,
    dhis2_url: str | None = None,
    dhis2_username: str | None = None,
    dhis2_password: str | None = None,
    dataset: str = "SNIS_MENSUEL",
    region: str | None = None,
) -> dict[str, Any]:
    """Génère un dataset DHIS2 et le pousse vers une instance DHIS2 nationale.

    v2.9.1 — Implémente le push effectif via POST /api/dataValueSets.

    Si dhis2_url/dhis2_username/dhis2_password ne sont pas fournis,
    on utilise les variables d'environnement :
    - DHIS2_URL
    - DHIS2_USERNAME
    - DHIS2_PASSWORD

    Si aucune URL n'est configurée, retourne le dataset généré sans push
    (mode "dry run" — utile pour tester avant la mise en production DHIS2).
    """
    import os
    import logging
    import requests

    logger = logging.getLogger("guineecare.dhis2")

    # 1. Générer le dataset
    dhis2_data = export_dhis2_dataset(
        db, current_user,
        period=period, dataset=dataset, region=region,
    )

    # 2. Récupérer la configuration DHIS2
    dhis2_url = dhis2_url or os.environ.get("DHIS2_URL", "")
    dhis2_username = dhis2_username or os.environ.get("DHIS2_USERNAME", "")
    dhis2_password = dhis2_password or os.environ.get("DHIS2_PASSWORD", "")

    if not dhis2_url:
        logger.info("DHIS2_URL not configured — returning dataset without push (dry run)")
        return {
            **dhis2_data,
            "push_status": "dry_run",
            "push_message": "DHIS2_URL non configuré — dataset généré sans push",
        }

    # 3. Push vers DHIS2
    push_url = f"{dhis2_url.rstrip('/')}/api/dataValueSets"
    headers = {"Content-Type": "application/json"}
    auth = (dhis2_username, dhis2_password) if dhis2_username else None

    # Format DHIS2 dataValueSets
    payload = {
        "dataSet": dhis2_data["dataSet"],
        "completeDate": utcnow().strftime("%Y-%m-%d"),
        "period": dhis2_data["period"],
        "orgUnit": dhis2_data["orgUnits"][0] if dhis2_data["orgUnits"] else "",
        "dataValues": dhis2_data["dataValues"],
    }

    try:
        response = requests.post(
            push_url,
            json=payload,
            headers=headers,
            auth=auth,
            timeout=30,
        )

        if response.status_code in (200, 201):
            result = response.json() if response.text else {}
            logger.info("DHIS2 push successful: %s dataValues", dhis2_data["total_values"])
            return {
                **dhis2_data,
                "push_status": "success",
                "push_response": result,
                "push_url": push_url,
            }
        else:
            logger.error("DHIS2 push failed: HTTP %s — %s", response.status_code, response.text[:500])
            return {
                **dhis2_data,
                "push_status": "failed",
                "push_error": f"HTTP {response.status_code}: {response.text[:500]}",
                "push_url": push_url,
            }
    except requests.exceptions.RequestException as e:
        logger.error("DHIS2 push error: %s", e)
        return {
            **dhis2_data,
            "push_status": "error",
            "push_error": str(e),
            "push_url": push_url,
        }
