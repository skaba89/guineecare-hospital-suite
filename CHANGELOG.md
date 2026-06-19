# Changelog

## 0.4.0 — 2026-06-19

### Added — Pages admin (section SYSTÈME)
- **`/users`** — Gestion des utilisateurs (CRUD, activation/désactivation, filtre par rôle, recherche)
- **`/rbac`** — Matrice rôles × permissions avec toggle visuel, création de rôles et permissions
- **`/facilities`** — Établissements de santé en cartes (vue nationale pour SUPER_ADMIN, mono-établissement pour ADMIN)
- **`/departments`** — Départements avec filtre par établissement
- Section "SYSTÈME" ajoutée à la sidebar (visible uniquement SUPER_ADMIN/ADMIN)
- Routes frontend protégées par `ProtectedRoute roles={["SUPER_ADMIN","ADMIN"]}`
- Flags `canSeeUsers`, `canSeeRbac`, `canSeeFacilities`, `canSeeDepartments` dans `useNavVisibility()`

### Added — Tests E2E
- Script `scripts/verify_admin_pages.py` : 31 tests E2E automatisés
  - Authentification multi-rôles (5 comptes : SUPER_ADMIN, ADMIN, DOCTOR, NURSE, PHARMACIST)
  - RBAC strict sur `/users`, `/rbac/roles`, `/rbac/permissions` (DOCTOR/NURSE → 403)
  - Isolation multi-tenant (`/facilities` : ADMIN voit 1, SUPER_ADMIN voit 20)
  - Validation Pydantic v2 (email invalide → 422, champ manquant → 422)
  - Pages frontend servies par Vite (5 routes)

### Fixed — Backend
- **`POST /patients`** : auto-génération de `facility_id` (depuis JWT) et `patient_number` (format `PAT-YYYYMMDDHHMMSS`) si manquants — facilite l'usage API
- **`GET /hospitalization/bed-board`** : `facility_id` devient optionnel
  - SUPER_ADMIN sans `facility_id` → tous les lits
  - Autres rôles sans `facility_id` → fallback sur leur établissement
- **`UserCreate`** : durcissement de la validation
  - `email` → `EmailStr` (validation RFC 5322)
  - `password` → `Field(min_length=8)`
  - `first_name` / `last_name` → `Field(min_length=1, max_length=100)`
- **`UserUpdate`** : même durcissement
- Migration `class Config` → `model_config = ConfigDict(from_attributes=True)` sur `UserRead`, `PatientRead`

### Hygiene
- `.gitignore` backend : exclusion des `*.db` et `__pycache__/`
- Suppression du tracking git de `backend/test_guineecare.db`
- `start_dev.sh` : script de démarrage robuste avec seed complet

### Statistics
- 84/84 tests pytest backend
- 31/31 tests E2E pages admin
- 4 nouvelles pages frontend (350+ lignes chacune)
- Build Vite OK (1 MB gzippé)

---

## 0.3.0 — 2026-06-14

- Suite E2E complète (109/109 tests)
- RBAC permission improvements
- Bug fixes sur tests E2E

## 0.2.0 — 2026-06-10

- Multi-tenant RLS + RBAC robuste
- Gestion du personnel complète

## 0.1.0 — 2026-06-02

- Création de la base documentaire GuinéeCare Hospital Suite
- Ajout des 16 lots fonctionnels et techniques
- Documents de roadmap, budget, gouvernance, architecture, déploiement
