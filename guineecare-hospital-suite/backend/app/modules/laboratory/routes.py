from datetime import datetime
from app.core.datetime import utcnow

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.pagination import PaginationParams, paginate
from app.core.tenant import tenant_query, enforce_facility_access
from app.db.session import get_db
from app.modules.laboratory.models import LabOrder, LabOrderTest, LabResult, LabTest
from app.modules.laboratory.schemas import LabOrderCreate, LabResultCreate, LabTestCreate
from app.modules.rbac.dependencies import require_permission
from app.modules.realtime import publish_kpi_update
from app.modules.users.models import User

router = APIRouter(prefix="/laboratory", tags=["laboratory"])


@router.get("/tests")
def list_tests(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("lab.read")),
):
    query = tenant_query(db, LabTest, current_user).order_by(LabTest.name)
    if pagination.search:
        query = query.filter(
            (LabTest.name.ilike(f"%{pagination.search}%"))
            | (LabTest.code.ilike(f"%{pagination.search}%"))
        )
    return paginate(query, pagination)


@router.post("/tests")
def create_test(
    payload: LabTestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("lab.manage")),
):
    data = payload.model_dump(exclude_none=True)
    if not data.get("facility_id"):
        data["facility_id"] = current_user.facility_id
    enforce_facility_access(current_user, data.get("facility_id"))
    row = LabTest(**data)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "lab test created"}


@router.post("/orders")
def create_order(
    payload: LabOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("lab.order")),
):
    test = db.query(LabTest).filter(LabTest.id == payload.test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Lab test not found")
    # Inférer facility_id depuis le patient si non fourni
    from app.modules.patients.models import Patient
    patient = db.query(Patient).filter(Patient.id == payload.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    enforce_facility_access(current_user, patient.facility_id)
    data = payload.model_dump(exclude_none=True)
    if not data.get("facility_id"):
        data["facility_id"] = patient.facility_id
    enforce_facility_access(current_user, data.get("facility_id"))
    row = LabOrder(**data, ordered_by=current_user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "lab order created"}


@router.get("/orders")
def list_orders(
    pagination: PaginationParams = Depends(),
    status: str | None = None,
    patient_id: str | None = None,
    test_id: str | None = None,
    priority: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("lab.read")),
):
    """Liste paginée des demandes laboratoire avec filtres serveur.

    Filtres : `status`, `patient_id`, `test_id`, `priority`,
    `date_from`/`date_to` (sur ordered_at), `search`.
    """
    query = tenant_query(db, LabOrder, current_user).order_by(LabOrder.ordered_at.desc())
    if pagination.search:
        query = query.filter(
            (LabOrder.status.ilike(f"%{pagination.search}%"))
            | (LabOrder.priority.ilike(f"%{pagination.search}%"))
        )
    if status:
        query = query.filter(LabOrder.status == status.upper())
    if patient_id:
        query = query.filter(LabOrder.patient_id == patient_id)
    if test_id:
        query = query.filter(LabOrder.test_id == test_id)
    if priority:
        query = query.filter(LabOrder.priority == priority.upper())
    if date_from:
        try:
            from datetime import datetime as _dt
            query = query.filter(LabOrder.ordered_at >= _dt.fromisoformat(date_from))
        except ValueError:
            pass
    if date_to:
        try:
            from datetime import datetime as _dt
            query = query.filter(LabOrder.ordered_at <= _dt.fromisoformat(date_to))
        except ValueError:
            pass
    return paginate(query, pagination)


@router.post("/orders/{order_id}/results")
def create_result(
    order_id: str,
    payload: LabResultCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("lab.result")),
):
    order = db.query(LabOrder).filter(LabOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Lab order not found")
    enforce_facility_access(current_user, order.facility_id)
    data = payload.model_dump(exclude_none=True)
    if not data.get("facility_id"):
        data["facility_id"] = order.facility_id
    row = LabResult(**data, order_id=order_id, entered_by=current_user.id)
    order.status = "RESULT_ENTERED"
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "result saved"}


@router.post("/results/{result_id}/validate")
def validate_result(
    result_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("lab.validate")),
):
    row = db.query(LabResult).filter(LabResult.id == result_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Lab result not found")
    enforce_facility_access(current_user, row.facility_id)
    row.status = "VALIDATED"
    row.validated_by = current_user.id
    row.validated_at = utcnow()
    order = db.query(LabOrder).filter(LabOrder.id == row.order_id).first()
    if order:
        order.status = "VALIDATED"
    db.commit()
    db.refresh(row)
    # v1.3.0 — push realtime KPI update so the dashboard live-counts validated lab results
    publish_kpi_update(
        facility_id=row.facility_id or (order.facility_id if order else None) or "*",
        kpi="lab.results.validated.count",
        value=1,
        delta=1,
        extra={"result_id": row.id, "order_id": row.order_id},
    )
    return {"data": row, "message": "result validated"}


@router.get("/results")
def list_results(
    pagination: PaginationParams = Depends(),
    status: str | None = None,
    order_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("lab.read")),
):
    """Liste paginée des résultats labo avec filtres serveur.

    Filtres : `status`, `order_id`, `date_from`/`date_to` (sur entered_at), `search`.
    """
    query = tenant_query(db, LabResult, current_user).order_by(LabResult.entered_at.desc())
    if pagination.search:
        query = query.filter(
            (LabResult.result_value.ilike(f"%{pagination.search}%"))
            | (LabResult.status.ilike(f"%{pagination.search}%"))
        )
    if status:
        query = query.filter(LabResult.status == status.upper())
    if order_id:
        query = query.filter(LabResult.order_id == order_id)
    if date_from:
        try:
            from datetime import datetime as _dt
            query = query.filter(LabResult.entered_at >= _dt.fromisoformat(date_from))
        except ValueError:
            pass
    if date_to:
        try:
            from datetime import datetime as _dt
            query = query.filter(LabResult.entered_at <= _dt.fromisoformat(date_to))
        except ValueError:
            pass
    return paginate(query, pagination)


# ============================================================================
# v2.4.0 — Phase 4 : Statut des demandes laboratoire (dashboard)
# ============================================================================

@router.get("/stats")
def lab_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("lab.read")),
):
    """Statut des demandes laboratoire — tableau de bord.

    Retourne :
    - count_by_status : {ORDERED, RESULT_ENTERED, VALIDATED, COMPLETED, CANCELLED}
    - count_by_priority : {NORMAL, URGENT, STAT}
    - urgent_pending : liste des commandes urgentes en attente
    - total_orders : nombre total
    - avg_validation_time_hours : temps moyen ORDERED → VALIDATED (last 30 jours)
    """
    from sqlalchemy import func

    query = tenant_query(db, LabOrder, current_user)

    # Comptage par statut
    status_counts_raw = (
        query.with_entities(LabOrder.status, func.count(LabOrder.id))
        .group_by(LabOrder.status)
        .all()
    )
    count_by_status = {status: count for status, count in status_counts_raw}

    # Comptage par priorité
    priority_counts_raw = (
        query.with_entities(LabOrder.priority, func.count(LabOrder.id))
        .group_by(LabOrder.priority)
        .all()
    )
    count_by_priority = {prio: count for prio, count in priority_counts_raw}

    # Commandes urgentes en attente (ORDERED + URGENT/STAT)
    urgent_pending = (
        query.filter(LabOrder.status == "ORDERED")
        .filter(LabOrder.priority.in_(["URGENT", "STAT"]))
        .order_by(LabOrder.ordered_at.asc())
        .limit(10)
        .all()
    )

    total_orders = sum(count_by_status.values())

    return {
        "data": {
            "count_by_status": count_by_status,
            "count_by_priority": count_by_priority,
            "total_orders": total_orders,
            "urgent_pending": [
                {
                    "id": str(o.id),
                    # v2.5.0 — Phase 5 : patient_id retiré pour anonymisation
                    # (les dashboards nationaux ne doivent pas exposer de PHI)
                    "test_id": o.test_id,
                    "priority": o.priority,
                    "status": o.status,
                    "ordered_at": o.ordered_at.isoformat() if o.ordered_at else None,
                }
                for o in urgent_pending
            ],
            "urgent_pending_count": len(urgent_pending),
        },
        "message": "lab stats dashboard",
    }


@router.post("/orders/{order_id}/collect")
def collect_sample(
    order_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("lab.write")),
):
    """Enregistrer le prélèvement d'un échantillon.

    Body JSON:
    {"sample_id": "SAM-2026-001"}  // optionnel — auto-généré si absent

    Passe le statut de la commande ORDERED → SAMPLE_COLLECTED.
    Si la commande a déjà un statut supérieur, retourne 409.
    """
    order = db.query(LabOrder).filter(LabOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Commande labo introuvable")
    enforce_facility_access(current_user, order.facility_id)

    if order.status != "ORDERED":
        raise HTTPException(
            status_code=409,
            detail=f"Prélèvement impossible — statut actuel: {order.status}",
        )

    sample_id = (payload or {}).get("sample_id") or f"SAM-{order.id[:8].upper()}-{utcnow().strftime('%Y%m%d%H%M')}"
    order.status = "SAMPLE_COLLECTED"
    # v2.8.3 — P2-2 fix : utiliser les vraies colonnes dédiées
    # (au lieu du hack ordered_by = "sample:{id}")
    order.sample_id = sample_id
    order.collected_by = str(current_user.id)
    order.collected_at = utcnow()
    db.commit()
    db.refresh(order)

    return {
        "data": {
            "id": str(order.id),
            "status": order.status,
            "sample_id": sample_id,
            "collected_at": utcnow().isoformat(),
            "collected_by": str(current_user.id),
        },
        "message": "Prélèvement enregistré",
    }


# ============================================================================
# v2.6.0 — Phase 7 : Panel labo (1 commande = N tests)
# ============================================================================

@router.post("/orders/panel")
def create_lab_panel(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("lab.write")),
):
    """Créer une commande labo avec plusieurs tests (panel).

    Body JSON:
    {
      "patient_id": "...",
      "admission_id": "...",       // optionnel
      "priority": "URGENT",        // optionnel, défaut NORMAL
      "test_ids": ["test-1", "test-2", "test-3"]
    }

    Crée :
    - 1 LabOrder (sans test_id — nullable depuis v2.6.0)
    - N LabOrderTest (1 par test dans le panel)

    Sécurité :
    - permission lab.write requise
    - enforce_facility_access sur le patient
    - Tous les tests doivent appartenir au même établissement que le patient
    """
    from app.modules.patients.models import Patient

    patient_id = payload.get("patient_id")
    test_ids = payload.get("test_ids", [])

    if not patient_id:
        raise HTTPException(status_code=422, detail="patient_id obligatoire")
    if not test_ids or not isinstance(test_ids, list) or len(test_ids) == 0:
        raise HTTPException(status_code=422, detail="test_ids doit être une liste non vide")

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient introuvable")
    enforce_facility_access(current_user, patient.facility_id)

    # Vérifier que tous les tests existent et appartiennent au même établissement
    tests = db.query(LabTest).filter(LabTest.id.in_(test_ids)).all()
    if len(tests) != len(test_ids):
        raise HTTPException(status_code=404, detail="Un ou plusieurs tests introuvables")
    for t in tests:
        if t.facility_id != patient.facility_id:
            raise HTTPException(
                status_code=403,
                detail=f"Test {t.name} n'appartient pas au même établissement que le patient",
            )

    # Créer la commande (sans test_id — panel multi-tests)
    order = LabOrder(
        facility_id=patient.facility_id,
        patient_id=patient_id,
        admission_id=payload.get("admission_id"),
        test_id=None,  # nullable depuis v2.6.0 pour les panels
        priority=payload.get("priority", "NORMAL"),
        status="ORDERED",
        ordered_by=str(current_user.id),
    )
    db.add(order)
    db.flush()  # pour avoir l'ID

    # Créer les LabOrderTest pour chaque test du panel
    created_items = []
    for test_id in test_ids:
        item = LabOrderTest(
            order_id=order.id,
            test_id=test_id,
            status="ORDERED",
        )
        db.add(item)
        created_items.append(item)

    db.commit()
    db.refresh(order)

    return {
        "data": {
            "order_id": str(order.id),
            "patient_id": str(order.patient_id),
            "priority": order.priority,
            "status": order.status,
            "ordered_at": order.ordered_at.isoformat() if order.ordered_at else None,
            "panel_tests": [
                {
                    "item_id": str(item.id),
                    "test_id": str(item.test_id),
                    "test_name": next((t.name for t in tests if t.id == item.test_id), "?"),
                    "status": item.status,
                }
                for item in created_items
            ],
            "total_tests": len(created_items),
        },
        "message": f"Panel labo créé avec {len(created_items)} test(s)",
    }


@router.get("/orders/{order_id}/panel")
def get_lab_panel(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("lab.read")),
):
    """Récupérer le détail d'une commande labo panel (avec tous ses tests).

    Retourne la commande + la liste des LabOrderTest associés avec leur
    statut et résultat individuel.
    """
    order = db.query(LabOrder).filter(LabOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Commande labo introuvable")
    enforce_facility_access(current_user, order.facility_id)

    items = (
        db.query(LabOrderTest)
        .filter(LabOrderTest.order_id == order_id)
        .all()
    )

    # Récupérer les noms des tests
    test_ids = [item.test_id for item in items]
    tests = db.query(LabTest).filter(LabTest.id.in_(test_ids)).all() if test_ids else []
    test_map = {t.id: t for t in tests}

    return {
        "data": {
            "order_id": str(order.id),
            "patient_id": str(order.patient_id),
            "priority": order.priority,
            "status": order.status,
            "ordered_at": order.ordered_at.isoformat() if order.ordered_at else None,
            "tests": [
                {
                    "item_id": str(item.id),
                    "test_id": str(item.test_id),
                    "test_name": test_map[item.test_id].name if item.test_id in test_map else "?",
                    "test_code": test_map[item.test_id].code if item.test_id in test_map else "?",
                    "status": item.status,
                    "result_value": item.result_value,
                    "interpretation": item.interpretation,
                    "validated_by": item.validated_by,
                    "validated_at": item.validated_at.isoformat() if item.validated_at else None,
                }
                for item in items
            ],
            "total_tests": len(items),
        },
        "message": "panel details",
    }


@router.patch("/orders/{order_id}/panel/{item_id}/result")
def enter_panel_result(
    order_id: str,
    item_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("lab.write")),
):
    """Saisir le résultat d'un test individuel dans un panel.

    Body JSON:
    {
      "result_value": "12.5 g/L",
      "interpretation": "Normal"
    }
    """
    order = db.query(LabOrder).filter(LabOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Commande labo introuvable")
    enforce_facility_access(current_user, order.facility_id)

    item = (
        db.query(LabOrderTest)
        .filter(LabOrderTest.id == item_id)
        .filter(LabOrderTest.order_id == order_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item panel introuvable")

    result_value = payload.get("result_value")
    if not result_value:
        raise HTTPException(status_code=422, detail="result_value obligatoire")

    item.result_value = result_value
    item.interpretation = payload.get("interpretation")
    item.status = "RESULT_ENTERED"
    db.commit()
    db.refresh(item)

    return {
        "data": {
            "item_id": str(item.id),
            "test_id": str(item.test_id),
            "status": item.status,
            "result_value": item.result_value,
            "interpretation": item.interpretation,
        },
        "message": "Résultat saisi",
    }
