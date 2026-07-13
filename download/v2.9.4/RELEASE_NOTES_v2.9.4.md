# Release Notes — GuinéeCare Hospital Suite v2.9.4

**Date :** 14 juillet 2026
**Version :** 2.9.4 (depuis 2.9.3)
**Statut :** ✅ Prête pour déploiement national flagship

---

## 🎯 Objectif de la v2.9.4

La v2.9.4 complète la v2.9.3 en :
1. **Validant** le script `validate_v292.sh` en local (15 PASS / 0 FAIL / 4 WARN)
2. **Étendant** la couverture E2E Playwright (+40 tests sur 3 nouvelles pages)
3. **Créant les templates administratifs** pour finaliser les 3 P0 juridiques (lettre ARPT, appel d'offres pen test)
4. **Formalisant la roadmap V3.0** (10 lots sur 12-18 mois, budget 519 k€)
5. **Éditant des fiches rapides** utilisateurs imprimables (4 fiches 1-page)

---

## ✨ Nouveautés v2.9.4

### 1. Script de validation corrigé et testé

- `scripts/validate_v292.sh` exécuté en local : **15 PASS / 0 FAIL / 4 WARN** (warnings attendus en dev : Redis/Celery/DHIS2/metrics non configurés)
- Corrections :
  - Accepte `"ok"` ET `"healthy"` comme statut `/health`
  - Accepte toute version `2.9.x` (rétro-compatible v2.9.0 à v2.9.4+)

### 2. 40 nouveaux tests E2E Playwright

| Fichier | Tests | Couverture |
|---------|-------|------------|
| `v293-tasks-admin.spec.ts` | 18 | Accès RBAC, tableau de bord, 5 cartes tâches, trigger manuel, historique, refresh |
| `v293-icd11-search.spec.ts` | 12 | Accès formulaire, recherche par libellé/code, sélection badge, aucun résultat |
| `v293-infinite-patients.spec.ts` | 10 | Toggle vue, persistance localStorage, contenu, recherche |

**Total E2E : 64 parcours** (24 v2.9.2 + 40 v2.9.4)

### 3. Templates administratifs (P0 juridiques)

#### Lettre de notification ARPT pour DPO

`docs/securite/LETTRE_NOTIFICATION_ARPT_DPO_v1.md` (~200 lignes)
- Lettre officielle prête à imprimer
- 6 sections (identité DPO, prise de fonction, cadre traitement, contacts, référence arrêté, annexes)
- Checklist des pièces jointes (4 documents)
- Délai d'envoi (30 jours après désignation)
- Tableau de suivi (6 étapes)
- Références juridiques (RGPD Art. 37.7 + loi guinéenne)

#### Procédure appel d'offres pen test

`docs/securite/PROCEDURE_APPEL_OFFRES_PEN_TEST_v1.md` (~300 lignes)
- 12 sections complètes
- Calendrier prévisionnel (19 semaines)
- Conditions de participation (éligibilité, certifications CREST/OSCP, capacités)
- Contenu de l'offre (lettre, références, méthodologie, équipe, planning, financier, éthique)
- Critères d'évaluation pondérés (5 critères)
- Modalités de soumission (format, langue, adresse, date limite)
- Clause de confidentialité
- Attribution et contrat
- Garanties et pénalités
- 7 annexes référencées
- Contact et validation

### 4. Roadmap V3.0

`docs/roadmap/ROADMAP_V3.0.md` (~350 lignes)
- 10 lots détaillés sur 12-18 mois :
  - **V3.1** ICD-11 API officielle OMS (4 sem, P1)
  - **V3.2** FHIR R4 bidirectionnel avec DHIS2 (6 sem, P1)
  - **V3.3** Module télémédecine (10 sem, P1)
  - **V3.4** Aide à la décision clinique (8 sem, P2)
  - **V3.5** Signature électronique (3 sem, P2)
  - **V3.6** Mode offline complet mobile (6 sem, P2)
  - **V3.7** Observabilité avancée Grafana (4 sem, P2)
  - **V3.8** E-learning formation continue (8 sem, P3)
  - **V3.9** API publique chercheurs (6 sem, P3)
  - **V3.10** SaaS multi-pays (12 sem, P3)
- Planning indicatif visuel (T3 2026 → T3 2027)
- Ressources nécessaires (5,25 ETP, 519 k€ an 1)
- Financement à sécuriser (Ministère 30 % + bailleurs 70 %)
- Risques transverses (6 risques, mitigations)
- Gouvernance (comité pilotage trimestriel + revue technique mensuelle)
- Indicateurs de succès (8 KPI fin 2027)

### 5. Fiches rapides utilisateurs (4 fiches 1-page)

Dans `docs/formation/fiches-rapides/` :

| Fiche | Public | Contenu |
|-------|--------|---------|
| `fiche-mode-sombre.md` | Tous | Activation, comportement, problèmes fréquents |
| `fiche-taches-planifiees.md` | SUPER_ADMIN, ADMIN | Accès, 5 tâches, déclenchement, historique, statut infrastructure |
| `fiche-icd11-recherche.md` | Cliniciens | Recherche, 20 codes utiles Guinée, fallback libellé libre |
| `fiche-scroll-infini.md` | Tous | Activation, différences avec pagination, indicateurs visuels |

Format : 1 page recto-verso, imprimable, à garder à portée de main.

---

## 📊 Métriques v2.9.4

| Métrique | v2.9.3 | v2.9.4 | Δ |
|----------|--------|--------|---|
| Version | 2.9.3 | **2.9.4** | +0.0.1 |
| Tests E2E | 24 | **64** | +40 |
| Tests backend | 298+ | 298+ | 0 (pas de nouveau backend) |
| Documents | 99 | **104** (+5) | +5 |
| Fiches rapides | 11 | **15** | +4 |

---

## ✅ Validation

- ✅ Script `validate_v292.sh` testé en local : 15 PASS / 0 FAIL / 4 WARN
- ✅ OpenAPI régénéré (1 113 204 bytes)
- ✅ 40 nouveaux tests E2E Playwright créés
- ✅ 2 templates administratifs prêts à imprimer
- ✅ Roadmap V3.0 formalisée
- ✅ 4 fiches rapides utilisateurs

---

## 🚀 Prochaines étapes concrètes

### Pour le déploiement national flagship

1. **Désignation DPO** — Signer l'arrêté ministériel (modèle dans `DPO_DESIGNATION_v1.md`)
2. **Notification ARPT** — Envoyer la lettre (`LETTRE_NOTIFICATION_ARPT_DPO_v1.md`) dans les 30 jours
3. **Appel d'offres pen test** — Publier la procédure (`PROCEDURE_APPEL_OFFRES_PEN_TEST_v1.md`)
4. **Render Starter** — Upgrader le plan Render à Starter ($7/mois)
5. **Déploiement** — Suivre `RUNBOOK_MISE_A_JOUR_v2.9.2.md`
6. **Validation** — Exécuter `./scripts/validate_v292.sh https://votre-url admin@guineecare.com admin123`
7. **Formation** — Distribuer les 4 fiches rapides + le guide utilisateur

### Pour la V3.0

1. **Sécuriser le financement** (519 k€ an 1) auprès des bailleurs
2. **Présenter la roadmap** au comité de pilotage
3. **Démarrer V3.1** (ICD-11 API OMS) dès T3 2026
4. **V3.2** (FHIR/DHIS2 bidir) en parallèle dès T4 2026

---

## 📦 Contenu de l'archive

**`v2.9.4.zip`** (≈ 31 MB)

- Code source complet (sans node_modules / .venv)
- 104 documents (docs/securite, docs/formation, docs/roadmap, docs/deploiement, etc.)
- 64 tests E2E Playwright
- 298+ tests backend
- 4 fiches rapides imprimables
- 2 templates administratifs prêts à imprimer
- 1 roadmap V3.0 formalisée
- 1 script de validation post-déploiement testé

---

## 📞 Contact

- **Bug technique** : tech@guineecare.gn
- **Question fonctionnelle** : dsi@sante.gov.gn
- **Question juridique (DPO/ARPT)** : dpo@sante.gov.gn
- **Question V3.0 (roadmap)** : dsi@sante.gov.gn
- **Documentation** : voir `docs/` dans l'archive
