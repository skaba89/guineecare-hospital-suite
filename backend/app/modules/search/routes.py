"""HTTP routes for the global search module (v1.2.0).

Single endpoint:

- `GET /api/v1/search?q=...` — global search across patients, lab orders,
  imaging orders, invoices, and clinical notes.

The endpoint returns categorized results, capped at 10 per category and
50 total by default. Pagination is not supported (the client is expected
to refine the query if too many results are returned).

Permission: any authenticated user can search. Results are automatically
filtered by facility (tenant_query) so a NURSE in facility A will never
see results from facility B.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.search.service import global_search
from app.modules.users.models import User

router = APIRouter(prefix="/search", tags=["search"])


@router.get(
    "",
    summary="Recherche globale multi-ressources",
    description=(
        "Recherche full-text-like sur 5 catégories de ressources : "
        "patients, factures, demandes laboratoire, demandes imagerie, notes "
        "cliniques. Les résultats sont groupés par catégorie, avec un maximum "
        "de 10 résultats par catégorie et 50 résultats au total. "
        "\n\n"
        "**Recherche par préfixe** : si la requête commence par `PAT-`, `INV-`, "
        "`LAB-` ou `IMG-`, la recherche se limite à la catégorie correspondante "
        "et le préfixe est retiré du motif de recherche. Exemple : "
        "`?q=PAT-1234` ne cherche que dans les patients avec le motif `1234`."
        "\n\n"
        "**Filtrage multi-tenant** : les résultats sont automatiquement "
        "restreints à l'établissement de l'utilisateur courant (sauf SUPER_ADMIN "
        "qui voit tous les établissements)."
        "\n\n"
        "**Performance** : la recherche s'appuie sur les indexes déjà en place "
        "(`patient_number`, `invoice_number`, etc.). Pour les volumétries "
        ">100k lignes par table, une migration vers PostgreSQL tsvector + GIN "
        "ou Meilisearch est prévue en v1.3."
    ),
)
def search(
    q: str = Query(..., min_length=2, max_length=200, description="Terme de recherche (min 2 caractères)"),
    limit: int = Query(10, ge=1, le=50, description="Nombre maximum de résultats par catégorie"),
    max_total: int = Query(50, ge=1, le=200, description="Nombre total maximum de résultats"),
    categories: str | None = Query(
        None,
        description=(
            "Liste de catégories à rechercher, séparées par virgule. "
            "Valeurs possibles : patient, invoice, lab_order, imaging_order, clinical_note. "
            "Défaut : toutes les catégories."
        ),
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code=422, detail="La requête doit contenir au moins 2 caractères")
    cat_list = None
    if categories:
        valid = {"patient", "invoice", "lab_order", "imaging_order", "clinical_note"}
        cat_list = [c.strip() for c in categories.split(",") if c.strip()]
        invalid = [c for c in cat_list if c not in valid]
        if invalid:
            raise HTTPException(
                status_code=422,
                detail=f"Catégorie(s) invalide(s) : {', '.join(invalid)}. "
                       f"Valeurs valides : {', '.join(sorted(valid))}",
            )

    results = global_search(
        db=db,
        current_user=current_user,
        query=q,
        limit_per_category=limit,
        max_total=max_total,
        categories=cat_list,
    )
    return {
        "data": results,
        "message": f"search results for '{q}'",
    }
