# Release Notes — GuinéeCare Hospital Suite v2.9.3

**Date :** 14 juillet 2026
**Version :** 2.9.3 (depuis 2.9.2)
**Statut :** ✅ Prête pour déploiement national flagship

---

## 🎯 Objectif de la v2.9.3

La v2.9.2 a livré les **infrastructures** (Redis, Celery, ICD-11 module, mode sombre CSS, hook infinite scroll). La v2.9.3 finalise l'**UI** en rendant ces fonctionnalités directement utilisables par les administrateurs et les cliniciens dans l'application web.

---

## ✨ Nouveautés v2.9.3

### 1. Page Admin Tasks ⚙️ (frontend)

Nouvelle page `/tasks-admin` réservée aux SUPER_ADMIN et ADMIN :
- **Tableau de bord** : statut Worker Celery, Broker Redis, nombre de tâches
- **5 cartes tâches** : purge audit, backup DB, retry SMS, push DHIS2, digest qualité
- **Bouton "Exécuter maintenant"** sur chaque tâche (avec confirmation pour tâches destructives)
- **Historique** : 20 dernières exécutions issues du journal d'audit
- **RBAC strict** : SUPER_ADMIN + ADMIN uniquement

**Fichiers :**
- `frontend/src/pages/TasksAdminPage.tsx` (~440 lignes)
- Entrée sidebar "Tâches planifiées" + icône Settings
- i18n FR + EN

### 2. Composant ICD11Search 🔍 (frontend)

Nouveau composant d'autocomplétion ICD-11 :
- Recherche fuzzy (code, label FR, label EN) — insensible à la casse
- Debounce 300ms (pas de requête en rafale)
- Navigation clavier (↑/↓/Enter/Esc)
- Dropdown avec code coloré par catégorie + libellé FR/EN
- Badge bleu affichant le code sélectionné
- Bouton ✕ pour effacer

**Intégré** dans `PatientDetailPage.tsx` — formulaire "Nouveau diagnostic" :
- Remplace les 2 champs texte (Libellé + Code CIM-10)
- Permet de saisir un libellé libre si code non trouvé dans le catalogue

**Fichiers :**
- `frontend/src/components/ICD11Search.tsx` (~280 lignes)
- `frontend/src/pages/PatientDetailPage.tsx` (formulaire diagnostic mis à jour)

### 3. Vue scroll infini sur PatientsPage ♾️ (frontend)

Bouton toggle dans `/patients` pour basculer entre :
- **Vue paginée** (défaut, ResourcePage avec navigation page par page)
- **Vue scroll infini** (nouveau, opt-in, hook `useInfiniteScroll`)

La préférence est persistée dans `localStorage` (clé `guineecare_patients_view`).

La vue scroll infini charge automatiquement la page suivante quand l'utilisateur scroll à 200px du bas de la liste (IntersectionObserver). Affiche :
- Avatar avec initiales
- Nom, n° patient, sexe, âge, téléphone
- Spinner pendant le chargement
- "✓ Tous les patients chargés (N/total)" en fin de liste
- Modale au clic sur un patient (résumé)

**Fichiers :**
- `frontend/src/pages/InfinitePatientsList.tsx` (~270 lignes)
- `frontend/src/pages/PatientsPage.tsx` (toggle avec persistance)

### 4. Tests backend étendus (+18 tests)

`backend/tests/test_v292_tasks_routes_extended.py` :
- **Audit log** : vérifie que chaque trigger génère une entrée `system.task_trigger`
- **RBAC strict** : DOCTOR, NURSE, PHARMACIST, LAB_TECH, CASHIER → 403
- **Cohérence liste** : 5 tâches attendues, paths valides, champs `async_enabled`/`celery_available`/`broker_url_configured`
- **Gestion erreurs** : tâche inconnue 404, paramètres invalides (retention_days string, period invalide), body vide
- **ADMIN role** : ADMIN peut lister les tâches (pas seulement SUPER_ADMIN)

**Correction backend** : `app/tasks/routes.py` valide désormais le type des paramètres (`int()` avec try/except) pour éviter les 500 sur paramètres invalides.

### 5. Guide utilisateur complet 📚

`docs/formation/GUIDE_UTILISATEUR_v2.9.2.md` (~250 lignes) :
- **Mode sombre** : activation, avantages, comportement attendu, troubleshooting
- **Tâches planifiées** : accès, tableau de bord, 5 tâches détaillées, déclenchement manuel, historique, bonnes pratiques, mode dégradé
- **Recherche ICD-11** : utilisation, catalogue par catégorie, fallback libellé libre
- **Vue scroll infini** : activation, différences avec pagination, cas d'usage
- **FAQ** : 6 questions fréquentes (mobile, parallélisme, dry-run DHIS2, codes manquants, lenteur, RBAC)

---

## 📊 Métriques v2.9.3

| Métrique | v2.9.2 | v2.9.3 | Δ |
|----------|--------|--------|---|
| Version | 2.9.2 | **2.9.3** | +0.0.1 |
| Tests backend | 280+ | **298+** (+18) | +18 |
| Pages frontend | 32 | **34** (+2) | +2 (TasksAdmin, InfinitePatientsList) |
| Composants frontend | ~30 | **~31** (+1) | +1 (ICD11Search) |
| Parcours E2E | 24 | 24 | 0 |
| Documents | 98 | **99** (+1) | +1 (guide utilisateur) |
| Lignes frontend | — | **+990** | nouveau |

---

## ✅ Validation

- ✅ TypeScript compile sans erreur (`tsc --noEmit`)
- ✅ Vite build OK (741ms, dist/ généré)
- ✅ 82 tests backend passent (38 v2.9.2 + 18 v2.9.3 + 26 non-régression)
- ✅ OpenAPI régénéré (1 113 204 bytes)
- ✅ Postman collection mise à jour

---

## 🚀 Installation

### Depuis l'archive

```bash
unzip v2.9.3.zip
cd v2.9.3/guineecare-hospital-suite

# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
npm run dev
```

### Mise à jour depuis v2.9.2

Aucune migration DB nécessaire (pas de nouveau schéma). Voir `docs/deploiement/RUNBOOK_MISE_A_JOUR_v2.9.2.md` (la procédure s'applique aussi à v2.9.3).

---

## 📞 Support

- **Bug technique** : tech@guineecare.gn
- **Question fonctionnelle** : dsi@sante.gov.gn
- **Documentation** : voir `docs/` dans l'archive
- **Guide utilisateur** : `docs/formation/GUIDE_UTILISATEUR_v2.9.2.md`
