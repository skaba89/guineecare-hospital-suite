"""Routes ICD-11 — v2.9.2

Endpoints de recherche et consultation des codes ICD-11 (classification OMS).

Endpoints :
- GET /icd11/search?q=...&limit=20  → recherche fuzzy
- GET /icd11/{code}                  → détail d'un code
- GET /icd11/categories              → liste des catégories du catalogue

Aucune authentification requise (catalogue de référence public OMS) — mais
on garde le JWT pour tracer l'usage. Pas de permission RBAC spécifique :
la recherche ICD-11 est utile à tous les rôles cliniques.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.modules.auth.dependencies import get_current_user
from app.modules.icd11.catalog import (
    get_icd11_by_code,
    list_icd11_categories,
    search_icd11,
)

router = APIRouter(prefix="/icd11", tags=["icd11"])


@router.get("/search")
def search(
    q: str = Query(..., min_length=1, max_length=100, description="Texte recherché (code ou label)"),
    limit: int = Query(20, ge=1, le=100, description="Nombre max de résultats"),
    current_user=Depends(get_current_user),
):
    """Recherche fuzzy dans le catalogue ICD-11.

    Exemples :
    - GET /icd11/search?q=palu → paludisme (1F03, 1F2Z)
    - GET /icd11/search?q=1F → tous les codes commençant par 1F
    - GET /icd11/search?q=hypertension

    Recherche sur code, label FR et label EN. Insensible à la casse.
    """
    results = search_icd11(q, limit=limit)
    return {
        "data": results,
        "total": len(results),
        "query": q,
    }


@router.get("/categories")
def categories(current_user=Depends(get_current_user)):
    """Liste les catégories disponibles dans le catalogue ICD-11 embarqué."""
    return {
        "data": list_icd11_categories(),
    }


@router.get("/{code}")
def get_by_code(
    code: str,
    current_user=Depends(get_current_user),
):
    """Récupère le détail d'un code ICD-11.

    Exemple : GET /icd11/1F03 → {code: "1F03", label_fr: "Paludisme à P. falciparum", ...}
    """
    result = get_icd11_by_code(code)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Code ICD-11 non trouvé: {code}. Utilisez /icd11/search?q={code} pour une recherche.",
        )
    return {"data": result}
