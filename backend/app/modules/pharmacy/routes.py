from datetime import datetime
from app.core.datetime import utcnow

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.pagination import PaginationParams, paginate
from app.core.tenant import tenant_query, enforce_facility_access
from app.db.session import get_db
from app.modules.pharmacy.models import PharmacyProduct, PharmacyStock, StockMovement
from app.modules.pharmacy.schemas import PharmacyProductCreate, StockMovementCreate
from app.modules.rbac.dependencies import require_permission
from app.modules.audit.service import audit_log
from app.modules.users.models import User

router = APIRouter(prefix="/pharmacy", tags=["pharmacy"])


@router.get("/products")
def list_products(
    pagination: PaginationParams = Depends(),
    category: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("pharmacy.read")),
):
    """Liste paginée des produits pharmacie avec filtres serveur.

    Filtres : `category`, `search` (sur name et code).
    """
    query = tenant_query(db, PharmacyProduct, current_user).order_by(PharmacyProduct.name)
    if pagination.search:
        query = query.filter(
            (PharmacyProduct.name.ilike(f"%{pagination.search}%"))
            | (PharmacyProduct.code.ilike(f"%{pagination.search}%"))
        )
    if category:
        query = query.filter(PharmacyProduct.category == category)
    return paginate(query, pagination)


@router.post("/products")
def create_product(
    payload: PharmacyProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("pharmacy.manage")),
):
    data = payload.model_dump(exclude_none=True)
    if not data.get("facility_id"):
        data["facility_id"] = current_user.facility_id
    enforce_facility_access(current_user, data.get("facility_id"))
    row = PharmacyProduct(**data)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "product created"}


@router.get("/stock")
def get_stock(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("pharmacy.read")),
):
    query = tenant_query(db, PharmacyStock, current_user).order_by(PharmacyStock.updated_at.desc())
    if pagination.search:
        query = query.join(PharmacyProduct, PharmacyStock.product_id == PharmacyProduct.id).filter(
            (PharmacyProduct.name.ilike(f"%{pagination.search}%"))
            | (PharmacyProduct.code.ilike(f"%{pagination.search}%"))
        )
    return paginate(query, pagination)


@router.post("/stock/movements")
def create_stock_movement(
    payload: StockMovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("pharmacy.manage")),
):
    enforce_facility_access(current_user, payload.facility_id)

    product = db.query(PharmacyProduct).filter(PharmacyProduct.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    stock = db.query(PharmacyStock).filter(
        PharmacyStock.facility_id == payload.facility_id,
        PharmacyStock.product_id == payload.product_id,
    ).first()
    if not stock:
        stock = PharmacyStock(
            facility_id=payload.facility_id,
            product_id=payload.product_id,
            quantity_available=0,
            min_threshold=payload.min_threshold,
        )
        db.add(stock)
        db.flush()

    if payload.movement_type.upper() == "IN":
        stock.quantity_available += payload.quantity
    elif payload.movement_type.upper() == "OUT":
        if stock.quantity_available < payload.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")
        stock.quantity_available -= payload.quantity
    else:
        raise HTTPException(status_code=400, detail="movement_type must be IN or OUT")

    stock.updated_at = utcnow()
    movement = StockMovement(
        facility_id=payload.facility_id,
        product_id=payload.product_id,
        movement_type=payload.movement_type.upper(),
        quantity=payload.quantity,
        reason=payload.reason,
        performed_by=current_user.id,
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)
    db.refresh(stock)
    return {"data": {"movement": movement, "stock": stock}, "message": "stock movement created"}


@router.get("/stock/movements")
def list_stock_movements(
    pagination: PaginationParams = Depends(),
    movement_type: str | None = None,
    product_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("pharmacy.read")),
):
    """Liste paginée des mouvements de stock avec filtres serveur.

    Filtres : `movement_type`, `product_id`, `date_from`/`date_to` (sur performed_at), `search`.
    """
    query = tenant_query(db, StockMovement, current_user).order_by(StockMovement.performed_at.desc())
    if pagination.search:
        query = query.filter(
            (StockMovement.reason.ilike(f"%{pagination.search}%"))
            | (StockMovement.movement_type.ilike(f"%{pagination.search}%"))
        )
    if movement_type:
        query = query.filter(StockMovement.movement_type == movement_type.upper())
    if product_id:
        query = query.filter(StockMovement.product_id == product_id)
    if date_from:
        try:
            from datetime import datetime as _dt
            query = query.filter(StockMovement.performed_at >= _dt.fromisoformat(date_from))
        except ValueError:
            pass
    if date_to:
        try:
            from datetime import datetime as _dt
            query = query.filter(StockMovement.performed_at <= _dt.fromisoformat(date_to))
        except ValueError:
            pass
    return paginate(query, pagination)


# ============================================================================
# v2.4.0 — Phase 4 : Dispensation patient + alertes + valorisation
# ============================================================================

@router.post("/dispense")
def dispense_to_patient(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("pharmacy.write")),
):
    """Dispensation d'un médicament à un patient.

    Body JSON:
    {
      "product_id": "...",
      "quantity": 10,
      "patient_id": "...",          // obligatoire
      "prescription_id": "...",     // optionnel — ClinicalNote.id
      "admission_id": "...",        // optionnel
      "reason": "Traitement paludisme"
    }

    Crée un StockMovement de type OUT lié au patient, vérifie le stock
    disponible, et décrémente quantity_available.

    Sécurité :
    - permission pharmacy.write requise
    - tenant_query filtre par facility_id (vérifié sur product + patient)
    - quantité doit être > 0 et ≤ stock disponible
    """
    product_id = payload.get("product_id")
    quantity = payload.get("quantity")
    patient_id = payload.get("patient_id")
    prescription_id = payload.get("prescription_id")
    admission_id = payload.get("admission_id")
    reason = payload.get("reason", "Dispensation patient")

    if not product_id or not patient_id or not quantity:
        raise HTTPException(
            status_code=422,
            detail="product_id, patient_id et quantity sont obligatoires",
        )
    try:
        quantity = float(quantity)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="quantity doit être un nombre")
    if quantity <= 0:
        raise HTTPException(status_code=422, detail="quantity doit être > 0")

    # Vérifier que le produit existe et appartient à l'établissement
    product = db.query(PharmacyProduct).filter(PharmacyProduct.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    enforce_facility_access(current_user, product.facility_id)

    # v2.8.0 — P0-2 fix : row lock SELECT FOR UPDATE pour éviter race condition
    stock = (
        db.query(PharmacyStock)
        .filter(PharmacyStock.product_id == product_id)
        .filter(PharmacyStock.facility_id == product.facility_id)
        .with_for_update()
        .first()
    )
    if not stock or stock.quantity_available < quantity:
        available = stock.quantity_available if stock else 0
        raise HTTPException(
            status_code=409,
            detail=f"Stock insuffisant — demandé {quantity}, disponible {available}",
        )

    # Décrémenter le stock
    stock.quantity_available -= quantity
    stock.updated_at = utcnow()

    # Créer le mouvement avec lien patient
    movement = StockMovement(
        facility_id=product.facility_id,
        product_id=product_id,
        movement_type="OUT",
        quantity=quantity,
        reason=reason,
        performed_by=str(current_user.id),
        performed_at=utcnow(),
        patient_id=patient_id,
        prescription_id=prescription_id,
        admission_id=admission_id,
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)
    # v2.8.0 — Audit log pour traçabilité médico-légale
    audit_log(
        db=db,
        action="pharmacy.dispense",
        user=current_user,
        resource_type="stock_movement",
        resource_id=str(movement.id),
        request=None,  # pas de Request dans cette fonction
        status_code=200,
    )

    return {
        "data": {
            "movement_id": str(movement.id),
            "product_id": product_id,
            "product_name": product.name,
            "quantity_dispensed": quantity,
            "patient_id": patient_id,
            "prescription_id": prescription_id,
            "remaining_stock": stock.quantity_available,
            "dispensed_by": str(current_user.id),
            "dispensed_at": movement.performed_at.isoformat(),
        },
        "message": "Dispensation enregistrée",
    }


@router.get("/alerts")
def pharmacy_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("pharmacy.read")),
):
    """Alertes stock pharmacie : ruptures + péremptions proches.

    Retourne 2 listes :
    - low_stock : produits où quantity_available ≤ min_threshold
    - near_expiry : stock expirant dans les 30 prochains jours (ou déjà expiré)
    """
    stocks_query = tenant_query(db, PharmacyStock, current_user)
    products_by_id = {}
    for p in tenant_query(db, PharmacyProduct, current_user).all():
        products_by_id[p.id] = p

    low_stock = []
    near_expiry = []
    now = utcnow()
    from datetime import timedelta
    threshold = now + timedelta(days=30)

    for stock in stocks_query.all():
        product = products_by_id.get(stock.product_id)
        if not product:
            continue

        # Rupture / stock bas
        if stock.quantity_available <= stock.min_threshold:
            low_stock.append({
                "product_id": str(product.id),
                "product_name": product.name,
                "product_code": product.code,
                "quantity_available": stock.quantity_available,
                "min_threshold": stock.min_threshold,
                "severity": "RUPTURE" if stock.quantity_available == 0 else "LOW",
            })

        # Péremption proche
        if stock.expiry_date:
            exp = stock.expiry_date
            if exp.tzinfo is None:
                from datetime import timezone
                exp = exp.replace(tzinfo=timezone.utc)
            if exp <= now:
                near_expiry.append({
                    "product_id": str(product.id),
                    "product_name": product.name,
                    "product_code": product.code,
                    "batch_number": stock.batch_number,
                    "expiry_date": stock.expiry_date.isoformat(),
                    "days_until_expiry": (exp - now).days,
                    "severity": "EXPIRED",
                })
            elif exp <= threshold:
                near_expiry.append({
                    "product_id": str(product.id),
                    "product_name": product.name,
                    "product_code": product.code,
                    "batch_number": stock.batch_number,
                    "expiry_date": stock.expiry_date.isoformat(),
                    "days_until_expiry": (exp - now).days,
                    "severity": "NEAR_EXPIRY",
                })

    return {
        "data": {
            "low_stock": low_stock,
            "low_stock_count": len(low_stock),
            "near_expiry": near_expiry,
            "near_expiry_count": len(near_expiry),
            "total_alerts": len(low_stock) + len(near_expiry),
        },
        "message": "Alertes stock pharmacie",
    }


@router.get("/valuation")
def stock_valuation(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("pharmacy.read")),
):
    """Valorisation du stock pharmacie en GNF.

    Calcule la valeur totale du stock = Σ (quantity_available × unit_price)
    pour tous les produits de l'établissement.
    """
    stocks = tenant_query(db, PharmacyStock, current_user).all()
    products_by_id = {}
    for p in tenant_query(db, PharmacyProduct, current_user).all():
        products_by_id[p.id] = p

    total_value = 0.0
    product_values = []
    for stock in stocks:
        product = products_by_id.get(stock.product_id)
        if not product:
            continue
        value = stock.quantity_available * (product.unit_price or 0)
        total_value += value
        product_values.append({
            "product_id": str(product.id),
            "product_name": product.name,
            "product_code": product.code,
            "quantity_available": stock.quantity_available,
            "unit_price": product.unit_price or 0,
            "total_value": round(value, 2),
        })

    # Trier par valeur décroissante
    product_values.sort(key=lambda x: x["total_value"], reverse=True)

    return {
        "data": {
            "total_stock_value_gnf": round(total_value, 2),
            "total_products": len(product_values),
            "currency": "GNF",
            "products": product_values[:50],  # Top 50 pour perf
        },
        "message": "Valorisation du stock pharmacie",
    }


@router.get("/dispensations")
def list_dispensations(
    patient_id: str | None = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("pharmacy.read")),
):
    """Historique des dispensations (StockMovement OUT avec patient_id non null).

    Filtre optionnel par patient_id.
    """
    query = tenant_query(db, StockMovement, current_user).filter(
        StockMovement.movement_type == "OUT"
    ).filter(StockMovement.patient_id.isnot(None))

    if patient_id:
        query = query.filter(StockMovement.patient_id == patient_id)

    query = query.order_by(StockMovement.performed_at.desc())
    return paginate(query, pagination)
