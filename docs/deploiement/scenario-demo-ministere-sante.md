# Scénario Démo — Ministère de la Santé Guinée

**Version :** v2.5.0 (Phase 5)
**Public :** Ministre de la Santé, Secrétariat Général, Direction des Systèmes d'Information Sanitaire (DSIS), Directeurs régionaux de la Santé, ONG partenaires (OMS, UNICEF, USAID)
**Durée :** 30-45 min
**Objectif :** Démontrer que GuinéeCare permet le pilotage national sanitaire sans exposer les données patients nominatives

## Contexte

La Guinée compte :
- **8 régions administratives** : Conakry, Boké, Kindia, Labé, Mamou, Faranah, Kankan, Nzérékoré
- **33 préfectures** + 5 communes de Conakry
- **~400 établissements de santé** (CHU, hôpitaux régionaux, préfectoraux, centres de santé, cliniques privées)
- **SNIS** (Système National d'Information Sanitaire) — reporting mensuel obligatoire
- **DHIS2** — plateforme nationale de collecte (en cours de déploiement)

## Prérequis démo

- ✅ Instance démo : `https://guineecare.onrender.com`
- ✅ Compte `admin@guineecare.com` / `admin123` (SUPER_ADMIN national)
- ✅ Données seed : 20 établissements répartis sur 8 régions, 50 patients
- ✅ Vidéoprojecteur + écran 16:9
- ✅ Connexion Internet stable (ou captures d'écran de backup)

## Scénario : Revue trimestrielle d'activité sanitaire Q1 2026

### Étape 1 — Accueil et vue nationale (5 min)

1. **Login** en tant que `admin@guineecare.com` (SUPER_ADMIN national)
2. Menu **Pilotage national** → page principale

**À montrer :**
- Vue d'ensemble nationale : 20 établissements suivis
- KPIs agrégés nationaux :
  - Total patients enregistrés
  - Total admissions (période en cours)
  - Total urgences
  - Occupation moyenne des lits
  - Recettes nationales (GNF)
- **Insister :** toutes ces données sont **anonymisées** — aucun nom de patient n'apparaît

### Étape 2 — Indicateurs multi-établissements (5 min)

Menu **Pilotage national** → **Tableau de bord national** (endpoint `GET /reporting/national`)

**Indicateurs affichés (tous agrégés) :**

| Catégorie | Indicateur | Valeur démo |
|-----------|------------|-------------|
| **Patients** | Total patients | 50 |
| **Admissions** | Total admissions | 23 |
| | Admissions actives | 8 |
| **Consultations** | Total consultations | 45 |
| **Urgences** | Total urgences | 12 |
| | Temps d'attente moyen (min) | 18.5 |
| **Hospitalisation** | Hospitalisations actives | 5 |
| | Total lits | 120 |
| | Lits occupés | 85 |
| | Taux d'occupation (%) | 70.8 |
| **Maternité** | Grossesses suivies | 8 |
| | Accouchements | 3 |
| **Pharmacie** | Produits pharmacie | 25 |
| | Valeur stock (GNF) | 5 250 000 |
| | Ruptures de stock | 4 |
| **Laboratoire** | Demandes laboratoire | 18 |
| | Résultats validés | 12 |
| | Résultats en attente | 6 |
| **Facturation** | Total factures | 30 |
| | Factures payées | 22 |
| | Factures impayées | 8 |
| | Recettes (GNF) | 4 500 000 |
| | Créances (GNF) | 1 200 000 |

**Point clé :** "Chaque indicateur est calculé en temps réel depuis les données opérationnelles des établissements. Aucune donnée patient n'est exposée ici."

### Étape 3 — Filtres géographiques (5 min)

**Filtre par région :**
1. Sélectionner **"Conakry"** dans le filtre région
2. Les KPIs se mettent à jour — n'affichent que les établissements de Conakry
3. Comparer avec **"Kankan"** — activité moindre

**Filtre par préfecture :**
1. Région = "Conakry" → Préfecture = "Conakry" (5 communes)
2. Région = "Kindia" → Préfecture = "Kindia"

**Filtre par commune :**
1. Région = "Conakry" → Commune = "Kaloum" (CHU Donka)
2. Région = "Conakry" → Commune = "Dixinn" (CHU Ignace Deen)

**Filtre par établissement :**
1. Sélectionner "CHU Donka" → vue détaillée d'un seul établissement

**Point clé :** "Le Ministère peut filtrer jusqu'au niveau commune pour cibler les interventions."

### Étape 4 — Répartition géographique (3 min)

Menu **Pilotage national** → **Répartition géographique**

**Vue par région :**
| Région | Établissements | Patients |
|--------|----------------|----------|
| Conakry | 8 | 25 |
| Kankan | 3 | 8 |
| Kindia | 2 | 5 |
| Nzérékoré | 2 | 4 |
| Labé | 2 | 3 |
| Boké | 1 | 2 |
| Mamou | 1 | 2 |
| Faranah | 1 | 1 |

**Vue par préfecture** + **vue par commune** disponibles.

### Étape 5 — Activité par établissement (5 min)

Menu **Pilotage national** → **Par établissement** (endpoint `GET /reporting/facility-breakdown`)

**Tableau détaillé :**

| Établissement | Région | Patients | Admissions | Urgences | Labos | Recettes GNF | Créances GNF |
|---------------|--------|----------|------------|----------|-------|--------------|--------------|
| CHU Donka | Conakry | 15 | 8 | 5 | 8 | 2 500 000 | 600 000 |
| CHU Ignace Deen | Conakry | 10 | 5 | 3 | 4 | 1 200 000 | 300 000 |
| Hôpital Régional Kankan | Kankan | 8 | 3 | 2 | 2 | 500 000 | 150 000 |
| ... | ... | ... | ... | ... | ... | ... | ... |

**Tri :** par activité décroissante (somme des compteurs)
**Insister :** "Aucune donnée patient nominative — uniquement des agrégats par établissement."

### Étape 6 — Export Excel (3 min)

1. Bouton **"Exporter Excel"** (endpoint `GET /reporting/export/xlsx`)
2. Le fichier `guineecare_national_all_YYYYMMDD_HHMMSS.xlsx` se télécharge
3. **Ouvrir dans Excel/LibreOffice** — 2 feuilles :
   - **Feuille 1 "Tableau de bord"** : tous les indicateurs agrégés + répartition par région
   - **Feuille 2 "Par établissement"** : tableau détaillé avec colonnes géographiques

**Point clé :** "L'export est **journalisé** dans l'audit log (action=`reporting.export.xlsx`) — traçabilité totale pour la conformité."

### Étape 7 — Export DHIS2 / SNIS (5 min)

Menu **Pilotage national** → **Export DHIS2/SNIS**

1. Sélectionner période : **"202603"** (Mars 2026)
2. Bouton **"Générer dataset DHIS2"** (endpoint `GET /reporting/dhis2/202603`)

**Réponse JSON (format DHIS2 dataValueSets) :**
```json
{
  "dataSet": "SNIS_MENSUEL",
  "period": "202603",
  "orgUnits": ["CHU-DONKA", "CHU-IGNACE-DEEN", "HR-KANKAN", ...],
  "dataValues": [
    {"dataElement": "TOTAL_ADMISSIONS", "orgUnit": "CHU-DONKA", "period": "202603", "value": "8"},
    {"dataElement": "TOTAL_EMERGENCIES", "orgUnit": "CHU-DONKA", "period": "202603", "value": "5"},
    {"dataElement": "TOTAL_DELIVERIES", "orgUnit": "CHU-DONKA", "period": "202603", "value": "2"},
    {"dataElement": "TOTAL_LAB_ORDERS", "orgUnit": "CHU-DONKA", "period": "202603", "value": "8"},
    {"dataElement": "TOTAL_REVENUE_GNF", "orgUnit": "CHU-DONKA", "period": "202603", "value": "2500000"},
    ...
  ],
  "total_values": 100
}
```

**Point clé :** "Cette structure est **compatible DHIS2** — prête à être poussée vers l'instance nationale DHIS2 via `POST /api/dataValueSets`. Le SNIS mensuel peut être généré automatiquement."

### Étape 8 — Alertes sanitaires (3 min)

Menu **Reporting** → onglet **Alertes épidémiques**

1. **Liste des alertes actives** :
   - Rougeole — Kankan — 12 cas — Niveau HIGH
   - Paludisme — Nzérékoré — 45 cas — Niveau CRITICAL
   - Choléra — Conakry (Kaloum) — 3 cas — Niveau MEDIUM

2. **Créer une nouvelle alerte** :
   - Maladie : "Fièvre hémorragique"
   - Région : "Conakry"
   - Nombre de cas : 2
   - Niveau : CRITICAL
   - Description : "2 cas suspects à Ratoma"
   - Mesures prises : "Isolement + investigation équipe DSIS"

3. **Clôturer une alerte** (clic sur une alerte → "Clôturer")

### Étape 9 — Rapports nationaux (3 min)

Menu **Reporting** → onglet **Rapports nationaux**

1. **Liste des rapports** (par établissement, par période)
2. **Créer un rapport mensuel SNIS** :
   - Établissement : CHU Donka
   - Période : 2026-03 (Mars 2026)
   - Type : SNIS_MENSUEL
   - Total admissions : 8
   - Total décès : 1
   - Total accouchements : 2
   - Taux d'occupation lits : 75%
   - Distribution maladies : {"Paludisme": 12, "IRAS": 3, "Rougeole": 0}

3. **Workflow de validation** :
   - DRAFT → SUBMITTED (par l'établissement)
   - SUBMITTED → VALIDATED (par le DSIS national)
   - SUBMITTED → REJECTED (avec motif)

### Étape 10 — Sécurité et conformité (3 min)

1. Menu **Audit** :
   - L'export Excel est tracé (action `reporting.export.xlsx`)
   - Chaque accès au tableau de bord national est journalisé
   - IP + User-Agent + timestamp pour chaque action

2. **Anonymisation vérifiée** :
   - Aucun nom de patient dans les dashboards nationaux
   - Aucun patient_id dans les exports
   - Uniquement des comptages, sommes, moyennes

3. **Isolation multi-tenant** :
   - Un ADMIN d'établissement ne voit QUE son établissement
   - Seul le SUPER_ADMIN (Ministère) voit tous les établissements
   - `tenant_query` filtre automatiquement par `facility_id`

## Récapitulatif — ce qui a été démontré

| # | Étape | Fonctionnalité | Endpoint |
|---|-------|----------------|----------|
| 1 | Vue nationale | KPIs agrégés multi-établissements | `GET /reporting/national` |
| 2 | Indicateurs | 25+ indicateurs sanitaires | (inclut dans /national) |
| 3 | Filtres géo | Region / Préfecture / Commune / Facility | (query params) |
| 4 | Répartition | Distribution géographique | `GET /reporting/geo-distribution` |
| 5 | Par établissement | Tableau détaillé activité | `GET /reporting/facility-breakdown` |
| 6 | Export Excel | Fichier .xlsx 2 feuilles | `GET /reporting/export/xlsx` |
| 7 | DHIS2/SNIS | Dataset compatible DHIS2 | `GET /reporting/dhis2/{period}` |
| 8 | Alertes | Épidémies temps réel | `GET/POST /reporting/epidemic-alerts` |
| 9 | Rapports | Workflow SNIS mensuel | `GET/POST /reporting/national-reports` |
| 10 | Sécurité | Audit + anonymisation + multi-tenant | `GET /audit` |

## Points clés à insister

### Pour le Ministre de la Santé
- ✅ **Pilotage national temps réel** — plus besoin d'attendre les rapports papier mensuels
- ✅ **Données anonymisées** — respect de la confidentialité médicale
- ✅ **Compatibilité DHIS2/SNIS** — intégration avec le système national existant
- ✅ **Alertes sanitaires temps réel** — détection épidémies précoce
- ✅ **Export Excel** — pour les analyses hors-ligne et archives

### Pour la DSIS (Direction Système d'Information Sanitaire)
- ✅ **API REST standard** — intégration avec le SI national
- ✅ **Multi-tenant** — chaque établissement gère ses données, le Ministère agrège
- ✅ **Audit trail complet** — traçabilité pour conformité
- ✅ **Workflow de validation** — DRAFT → SUBMITTED → VALIDATED

### Pour les Directeurs Régionaux
- ✅ **Filtre par région** — vue limitée à votre région
- ✅ **Comparaison inter-établissements** — benchmarking
- ✅ **Alertes régionales** — surveillance épidémiologique

### Pour les ONG partenaires (OMS, UNICEF, USAID)
- ✅ **Indicateurs OMS/HAS** — module qualité intégré
- ✅ **Export DHIS2** — reporting aux bailleurs
- ✅ **Données anonymisées** — conforme RGPD-like

## Anticipation questions

| Question | Réponse |
|----------|---------|
| "Combien d'établissements peuvent être connectés ?" | Illimité — architecture multi-tenant SaaS |
| "Comment intégrer DHIS2 existant ?" | Export JSON DHIS2-compatible → POST vers instance nationale |
| "Les données patients sont-elles exposées ?" | NON — uniquement des agrégats anonymisés |
| "Qui voit quoi ?" | SUPER_ADMIN = national ; ADMIN = son établissement ; autres = limité par permissions |
| "Peut-on filtrer par région ?" | Oui — région, préfecture, commune, établissement |
| "Fréquence de mise à jour ?" | Temps réel (les KPIs se calculent à chaque requête) |
| "Historique disponible ?" | Période filtrable : YYYY, YYYYMM, YYYYQn |
| "Coût pour le Ministère ?" | SaaS 30-50 USD/mois/établissement ; licence nationale négociable |
| "Formation ?" | 1-2 jours par établissement ; DSIS 3 jours pour le pilotage national |
| "Hébergement ?" | Cloud privé Guinée (recommandé) ou on-premise Ministère |
| "Sécurité ?" | 2FA, RBAC, audit trail, TLS, HSTS, CSP — conforme données de santé |
| "Plan de déploiement national ?" | Phase 1 pilote CHU Donka → Phase 2 CHU Conakry → Phase 3 régionaux → Phase 4 préfectoraux |

## En cas de problème pendant la démo

- **Instance lente** (Render free tier sleep) : attendre 30s
- **Erreur 429** (rate limit) : 1 login/min en prod
- **Page blanche** : F5 ou Ctrl+Shift+R
- **Backup plan** : captures d'écran préparées + vidéo pré-enregistrée du parcours

## Voir aussi

- `docs/deploiement/scenario-demo-bout-en-bout.md` — Scénario patient complet
- `docs/deploiement/CHECKLIST_DEMO.md` — Checklist démo détaillée
- `docs/securite/MATRICE_RBAC_v2.2.md` — Matrice RBAC
- `docs/securite/CHECKLIST_CONFORMITE_GUINEE_v2.2.md` — Conformité données médicales
