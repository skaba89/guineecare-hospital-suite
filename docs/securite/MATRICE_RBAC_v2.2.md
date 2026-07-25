# Matrice RBAC — GuinéeCare Hospital Suite v2.2.0

**Date :** 2026-07-05
**Scope :** 8 rôles × 50+ permissions
**Référence :** `backend/app/modules/rbac/seed.py`

## Rôles

| Rôle | Code | Niveau | Périmètre |
|------|------|--------|-----------|
| Super Administrateur National | `SUPER_ADMIN` | National | Tous les établissements |
| Administrateur Établissement | `ADMIN` | Établissement | Son établissement |
| Médecin | `DOCTOR` | Clinical | Son établissement |
| Infirmier | `NURSE` | Clinical | Son établissement |
| Sage-femme | `MIDWIFE` | Clinical | Son établissement |
| Pharmacien | `PHARMACIST` | Pharmacy | Son établissement |
| Technicien Laboratoire | `LAB_TECH` | Lab | Son établissement |
| Caissier | `CASHIER` | Billing | Son établissement |

## Matrice des permissions par rôle

| Permission | SUPER_ADMIN | ADMIN | DOCTOR | NURSE | MIDWIFE | PHARMACIST | LAB_TECH | CASHIER |
|------------|:-----------:|:-----:|:------:|:-----:|:-------:|:----------:|:--------:|:-------:|
| **Patients** | | | | | | | | |
| `patient.read` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `patient.create` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `patient.update` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Admissions** | | | | | | | | |
| `admission.read` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `admission.write` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `admission.manage` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Urgences** | | | | | | | | |
| `emergency.read` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `emergency.write` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `emergency.manage` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Hospitalisation** | | | | | | | | |
| `hospitalization.read` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `hospitalization.write` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Maternité** | | | | | | | | |
| `maternity.read` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `maternity.write` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Clinical** | | | | | | | | |
| `clinical.read` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `clinical.write` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Pharmacie** | | | | | | | | |
| `pharmacy.read` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| `pharmacy.write` | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| `pharmacy.manage` | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Laboratoire** | | | | | | | | |
| `lab.read` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| `lab.write` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| **Imagerie** | | | | | | | | |
| `imaging.read` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `imaging.write` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Bloc opératoire** | | | | | | | | |
| `surgery.read` | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `surgery.write` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Facturation** | | | | | | | | |
| `billing.read` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| `billing.write` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| `billing.validate` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `billing.pay` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Personnel** | | | | | | | | |
| `personnel.read` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `personnel.manage` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `personnel.planning` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Qualité** | | | | | | | | |
| `quality.read` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `quality.manage` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Notifications** | | | | | | | | |
| `notification.manage` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **FHIR** | | | | | | | | |
| `fhir.read` | ✅ | ✅* | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `fhir.write` | ✅ | ✅* | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Reporting** | | | | | | | | |
| `metrics.read` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Audit** | | | | | | | | |
| `audit.read` | ✅ | ✅* | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Administration système** | | | | | | | | |
| `facility.manage` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `user.manage` | ✅ | ✅** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

`*` ADMIN obtient ces permissions via le bypass `require_permission` (voir `dependencies.py:35`)
`**` ADMIN peut gérer les utilisateurs de SON établissement uniquement

## Notes importantes

### Bypass ADMIN (v2.2.0 — à documenter)
La fonction `require_permission` (`backend/app/modules/rbac/dependencies.py:35`) court-circuite la vérification pour `SUPER_ADMIN` ET `ADMIN`. Cela signifie qu'un ADMIN a **toutes** les permissions, même celles non listées dans `ROLE_PERMISSION_MAP`. Ce comportement est intentionnel mais doit être documenté dans la politique de sécurité.

**Recommandation Phase 7 :** Supprimer le bypass ADMIN et définir explicitement ses permissions dans `ROLE_PERMISSION_MAP` pour réduire le risque de privilèges involontaires.

### Isolation multi-tenant
- `SUPER_ADMIN` voit tous les établissements (cross-tenant)
- Tous les autres rôles sont filtrés par `facility_id` via `tenant_query()`
- `enforce_facility_access()` lève 403 sur accès cross-tenant
- Valide sur : patients, admissions, clinical, billing, pharmacy, lab, imaging, surgery, FHIR (depuis v2.2.0)

### Permissions FHIR (depuis v2.0.0)
- `fhir.read` accordé à DOCTOR et NURSE (pas à MIDWIFE, PHARMACIST, LAB_TECH, CASHIER)
- `fhir.write` accordé à SUPER_ADMIN uniquement (pas à DOCTOR — création FHIR limitée)

## Voir aussi
- `docs/securite/auth-rbac.md` — Documentation RBAC complète
- `backend/app/modules/rbac/seed.py` — Code source des permissions
- `backend/tests/test_security_hardening.py` — Tests OWASP A01-A09
- `backend/tests/test_phase6_security.py` — Tests Phase 6 (FHIR tenant isolation + audit)
