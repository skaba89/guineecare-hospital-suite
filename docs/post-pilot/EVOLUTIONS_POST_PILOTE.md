# Évolutions post-pilote — Roadmap v1.3 et au-delà

> Public : équipe projet, direction médicale, Ministère de la Santé
> Dernière mise à jour : 2026-06-21 (v1.3.0)
> Statut : document **dynamique** — alimenté par les retours utilisateurs
> collectés via la boucle feedback de v1.1.0.

Ce document consolide les évolutions envisagées pour GuinéeCare
Hospital Suite après le pilote CHU Donka. Il ne s'agit pas d'un
engagement formel : chaque évolution sera priorisée en fonction des
retours terrain, des contraintes budgétaires et des arbitrages
stratégiques. Le backlog est organisé en trois temps : **court terme**
(v1.2-v1.3 — 6 mois), **moyen terme** (v1.4 — 9 mois) et **long terme**
(v2.0 — 12+ mois).

---

## Méthodologie de priorisation

Chaque évolution candidate est évaluée sur cinq critères pondérés :

| Critère | Poids | Question |
|---------|-------|----------|
| Impact clinique | 30 % | Cette évolution améliore-t-elle directement la qualité des soins ou la sécurité patient ? |
| Adoption utilisateurs | 25 % | Combien d'utilisateurs en bénéficieront ? Freine-t-elle actuellement l'adoption ? |
| Effort de développement | 20 % | Complexité technique (jours-homme) et risque de régression. |
| Conformité réglementaire | 15 % | Cette évolution est-elle requise par une réglementation guinéenne ou OHADA ? |
| Extensibilité nationale | 10 % | Cette évolution facilite-t-elle le déploiement sur d'autres établissements ? |

Le score est calculé sur 100, et les évolutions sont classées par ordre
décroissant. Seules les évolutions à score ≥ 60 entrent dans la
roadmap suivante. Le comité de pilotage (équipe projet + direction
médicale + représentant Ministère) révise les priorités tous les
mois.

---

## v1.3 — Livré le 2026-06-21 (release v1.3.0)

La release v1.3.0 livre les **3 évolutions court terme restantes**
reportées de v1.2 : i18n EN/FR, dashboard temps réel, et mode hors-ligne
PWA. Avec cette release, les 5 évolutions court terme initialement
planifiées sont toutes livrées.

### ✅ Évolution 2 — Internationalisation EN/FR (LIVRÉE)

Module backend `i18n` avec catalogue FR (par défaut) + EN baked into
the source. Endpoint public `GET /api/v1/i18n/translations/{locale}`
retourne le catalogue complet pour le frontend. Service `translate()`
avec fallback sur FR puis sur la clé elle-même. 25 clés initiales
couvrant les messages d'erreur auth, RBAC, multi-tenant, common,
patients, documents, feedback, i18n.

Frontend : `I18nProvider` (sans i18next, 100 lignes suffisent),
`LanguageToggle` (dropdown compact avec drapeaux), `useI18n()` hook.
Détection initiale : localStorage > `navigator.language` > `fr`. 23
tests backend.

### ✅ Évolution 3 — Dashboard temps réel (LIVRÉ)

Module backend `realtime` avec broker pub/sub in-process (asyncio.Queue)
+ Redis optionnel pour multi-worker. WebSocket authentifié par JWT
(query param `?token=...`) à `WS /api/v1/realtime/ws`. Filtrage par
facility_id server-side (SUPER_ADMIN reçoit tout via canal `*`).
Heartbeat 25s. 3 mutations publient des KPI events : admissions
(+1), paiements (+amount), résultats labo validés (+1).

Frontend : `useRealtimeKPIs()` hook (auto-reconnect exponential
backoff), `RealtimeStatus` badge (🟢/🟡/🔴/⚪), DashboardPage
incrémente les compteurs live sans refetch. 14 tests backend.

### ✅ Évolution 5 — Mode hors-ligne PWA (LIVRÉ)

Manifest (`manifest.webmanifest`) avec 2 icônes 192/512 maskable,
3 raccourcis (admission, recherche patient, urgences), thème teal
#0f766e. Service worker (`sw.js`) avec stratégies :
- App shell : stale-while-revalidate.
- API GET : network-first, fallback cache si offline.
- API mutations : pass-through (503 si offline).
- WebSocket : exclu du SW.

Icônes générées par `scripts/generate_pwa_icons.py` (PIL, carré arrondi
teal + monogramme "GC" blanc). SW enregistré uniquement en production
(`import.meta.env.PROD`) pour éviter de cacher les fichiers HMR en dev.

### ⏭️ Évolutions court terme — Terminées

Avec v1.3.0, toutes les évolutions court terme (v1.2-v1.3) sont livrées :

- ✅ Évolution 1 — Impression PDF des documents cliniques (v1.2.0)
- ✅ Évolution 2 — Internationalisation EN/FR (v1.3.0)
- ✅ Évolution 3 — Dashboard temps réel (v1.3.0)
- ✅ Évolution 4 — Recherche globale Ctrl+K (v1.2.0)
- ✅ Évolution 5 — Mode hors-ligne PWA (v1.3.0)

---

## v1.2 — Livré le 2026-06-21 (release v1.2.0)

La release v1.2.0 a livré **2 des 5 évolutions court terme** planifiées :
l'export PDF des documents cliniques (évolution 1) et la recherche
globale Ctrl+K (évolution 4). Les 3 évolutions restantes (i18n,
dashboard temps réel, mode hors-ligne PWA) ont été reportées en v1.3
et sont désormais livrées (voir ci-dessus).

### ✅ Évolution 1 — Impression PDF des documents cliniques (LIVRÉE)

Quatre types de documents PDF générés à la volée via ReportLab 4.2.5
(bibliothèque pure Python, aucune dépendance système — WeasyPrint
était initialement prévu mais nécessite cairo/pango partagés,
incompatible avec l'environnement Docker léger du pilote) :

- **Ordonnance patient** — à partir d'une `ClinicalNote`
  (`note_type=PRESCRIPTION`).
- **Compte rendu d'imagerie** — à partir d'une `ImagingOrder` et de
  son `ImagingResult`.
- **Résultat de laboratoire** — bandeau d'alerte rouge si
  l'interprétation contient « CRITIQUE ».
- **Facture patient** — détail des montants + paiements.

Endpoints : `GET /api/v1/documents/{prescriptions|imaging-reports|lab-results|invoices}/{id}/pdf`.
Audit trail : table `documents_generated` (SHA-256 du PDF, qui / quand /
pour quel patient). 19 tests backend.

### ✅ Évolution 4 — Recherche globale Ctrl+K (LIVRÉE)

Endpoint `GET /api/v1/search?q=...` qui recherche en parallèle sur 5
catégories : patients, factures, demandes laboratoire, demandes
imagerie, notes cliniques. Recherche par préfixe (PAT-, INV-, LAB-,
IMG-). Filtrage multi-tenant automatique. Frontend : Command Palette
accessible via Ctrl+K avec navigation clavier. 21 tests backend.

### ⏭️ Évolutions 2, 3 et 5 — Livrées en v1.3.0

Les évolutions suivantes étaient planifiées pour v1.2 mais ont été
reportées puis livrées en v1.3.0 (voir section v1.3 ci-dessus pour les
détails d'implémentation) :

- **Évolution 2 — Internationalisation EN/FR** ✅ LIVRÉ v1.3.0
- **Évolution 3 — Dashboard temps réel** ✅ LIVRÉ v1.3.0
- **Évolution 5 — Mode hors-ligne PWA** ✅ LIVRÉ v1.3.0

---

## v1.2 — Évolutions confirmées (historique de planification)

### Évolutions confirmées

#### 1. Impression PDF des documents cliniques ✅ LIVRÉ v1.2.0

**Problème** : v1.0.0 ne génère pas de PDF natifs. Les utilisateurs
doivent recourir à Ctrl+P du navigateur, ce qui donne une mise en page
médiocre pour les ordonnances, comptes rendus et résultats de labo.

**Solution** : module d'export PDF backend utilisant WeasyPrint
(templates HTML/CSS → PDF). Quatre types de documents prioritaires :

- Ordonnance patient (avec en-tête établissement, signature médecin).
- Compte rendu d'imagerie (avec logo, conclusion, recommandations).
- Résultat de laboratoire (avec valeurs de référence, interprétation).
- Facture patient (avec détail des actes, total, mode de paiement).

**Impact clinique** : élevé (les ordonnances imprimées sont exigées
par les pharmaciens d'officine pour la délivrance).

**Effort** : 8 jours-homme.

#### 2. Internationalisation complète (i18n EN/FR) ✅ LIVRÉ v1.3.0

**Problème** : le backend et le frontend sont uniquement en français.
Une partie du personnel soignant du CHU Donka est anglophone
(formation au Libéria, Sierra Leone, Ghana). Les comptes rendus de
recherche clinique doivent pouvoir être en anglais.

**Solution** :

- Catalogue de clés i18n (`fr.json`, `en.json`) couvrant toute l'UI.
- Détection automatique de la langue navigateur à la première visite.
- Stockage de la préférence utilisateur (déjà disponible via
  `/api/v1/me/preferences` en v1.1.0 — `locale` field).
- Toggle de langue dans le menu utilisateur.
- Les données médicales (libellés CIM-10, DCI) restent en français
  par convention OHADA.

**Impact clinique** : moyen.

**Effort** : 10 jours-homme (essentiellement traduction + tests).

#### 3. Dashboard de pilotage temps réel ✅ LIVRÉ v1.3.0

**Problème** : la direction du CHU Donka et le Ministère ont besoin
d'une vue agrégée temps réel. Les pages de reporting existantes sont
statiques (génération à la demande, pas de push).

**Solution** : dashboard temps réel multi-niveaux :

- **Niveau établissement** — KPI CHU Donka (fréquentation, lits,
  finances, qualité).
- **Niveau service** — KPI par service (urgences, maternité, labo).
- **Niveau national** — agrégation multi-établissements (Super Admin).

Technologie : WebSocket (FastAPI + Redis pub/sub) pour le push, Recharts
côté frontend. Refresh automatique configurable (déjà disponible via
`dashboard_refresh_seconds` en v1.1.0).

**Impact pilotage** : élevé.

**Effort** : 12 jours-homme.

#### 4. Recherche globale (search bar) ✅ LIVRÉ v1.2.0

**Problème** : actuellement, il faut savoir dans quel module chercher
(patients, labo, imagerie, etc.) pour trouver une ressource. Les
utilisateurs veulent une barre de recherche globale comme sur un
moteur de recherche.

**Solution** : barre de recherche en haut de page (Ctrl+K) qui
interroge en parallèle plusieurs modules et affiche les résultats
catégorisés. Implémentation :

- Recherche full-text PostgreSQL (`tsvector` + GIN index) sur les
  tables patients, lab_orders, imaging_orders, invoices.
- Recherche par numéro de dossier (préfixe `PAT-`, `LAB-`, `IMG-`,
  `INV-`).
- Recherche par nom/prénom (avec normalisation des accents).
- Limitation à 10 résultats par catégorie, 50 au total.

**Impact adoption** : élevé (frustration fréquemment remontée).

**Effort** : 6 jours-homme.

#### 5. Mode hors-ligne partiel (PWA) ✅ LIVRÉ v1.3.0

**Problème** : en cas de coupure réseau ou de panne serveur, plus
aucune saisie n'est possible. La continuité de service est
critique, particulièrement dans le contexte guinéen (coupures
électriques fréquentes, bande passante instable).

**Solution** : transformer le frontend en PWA (Progressive Web App)
avec service worker. Modules critiques fonctionnant hors-ligne :

- **Admissions** — création de patient, admission urgente.
- **Constantes** — saisie de constantes vitales.
- **Ordonnances** — prescription en attente de synchronisation.

Les données sont stockées dans IndexedDB, synchronisées au retour du
réseau avec résolution des conflits (last-write-wins pour les
constantes, merge manuel pour les admissions en double).

**Impact clinique** : élevé (continuité de service).

**Effort** : 20 jours-homme (complexité élevée — gestion des
conflits à prévoir).

---

## v1.3 — Moyen terme (6 mois)

#### 6. Application mobile (Android natif)

**Problème** : les médecins en garde se déplacent entre services
avec leur téléphone. Avoir une app mobile dédiée (vs navigateur)
améliore l'expérience : notifications push, scan de QR code patient,
prise de photo pour imagerie.

**Solution** : application Android native (React Native) avec :

- Authentification biométrique (empreinte).
- Scan de QR code patient au pied du lit.
- Notifications push (résultats labo critiques, alertes).
- Mode hors-ligne synchronisé (cf. évolution 5).
- Fonctionnalités limitées (pas de saisie clinique complète —
  réservée à l'interface desktop).

**Impact clinique** : moyen (confort).

**Effort** : 30 jours-homme.

#### 7. Interopérabilité HL7 FHIR

**Problème** : GuinéeCare est une solution isolée. Aucune
interopérabilité avec d'autres SIH (si un patient vient d'un autre
hôpital, son dossier n'est pas accessible). Les laboratoires
d'analyse externes ne peuvent pas envoyer leurs résultats
électroniquement.

**Solution** : implémenter un endpoint FHIR R4 (REST + JSON) pour les
ressources principales :

- `Patient` — export du DPI patient.
- `Observation` — constantes, résultats labo.
- `MedicationRequest` — prescriptions.
- `DiagnosticReport` — comptes rendus d'imagerie.
- `Encounter` — admissions.

Authentification par OAuth2 + SMART on FHIR. Périmètre limité aux
partenaires identifiés (cliniques privées agréées, laboratoires
d'analyse médicale).

**Impact clinique** : élevé (continuité du parcours patient).

**Effort** : 25 jours-homme.

#### 8. Module de planification des ressources (RH v2)

**Problème** : le module RH actuel est basique (effectifs, contrats).
Les chef de service réclament un véritable module de planification :
planning de garde, congés, astreintes, remplacements.

**Solution** :

- Planning hebdomadaire / mensuel glissant par service.
- Gestion des gardes (nuit, week-end, jour férié).
- Gestion des congés (demande, validation, solde).
- Gestion des astreintes (téléphonique, physique).
- Système de remplacement automatique en cas d'absence.
- Notifications aux intéressés (R/Push).

**Impact organisationnel** : élevé.

**Effort** : 18 jours-homme.

#### 9. Tableau de bord qualité avancé

**Problème** : le module qualité actuel collecte les incidents mais
ne fournit pas d'analyse poussée. La direction qualité veut des
indicateurs agrégés (taux d'incidents par service, gravité, délai de
traitement).

**Solution** :

- Indicateurs qualité prédéfinis (OMS, HAS) : taux d'infections
  nosocomiales, réadmissions à 30 j, satisfaction patient.
- Tableaux de bord par service, par période, comparaison inter-établissements.
- Alertes automatiques en cas de dépassement de seuil.
- Export vers le rapport qualité annuel du Ministère.

**Impact conformité** : élevé (exigence Ministère).

**Effort** : 15 jours-homme.

#### 10. Système de notifications multicanal étendu

**Problème** : les notifications actuelles sont en app + email + SMS
(théorique). En pratique, l'email n'est pas consulté et le SMS n'est
pas implémenté. Les soignants ratent des notifications critiques.

**Solution** :

- Intégration SMS réelle via un opérateur local (Orange, MTN, Moov).
- Notifications push via l'app mobile (cf. évolution 6).
- Règles de routage : urgences → SMS, informations → app, etc.
- Préférences utilisateur par catégorie de notification.

**Impact clinique** : élevé (résultats labo critiques).

**Effort** : 12 jours-homme (intégration opérateur + tests).

---

## v2.0 — Long terme (12+ mois)

#### 11. Data warehouse santé national

**Problème** : le reporting national actuel est limité à des agrégats
pré-calculés. Pour les études épidémiologiques et la planification
sanitaire, le Ministère a besoin d'un véritable data warehouse
permettant des requêtes ad hoc.

**Solution** :

- ETL nightly : PostgreSQL (applicatif) → PostgreSQL/ClickHouse (DWH).
- Schéma en étoile : tables de faits (visites, actes, prescriptions) +
  dimensions (patient, établissement, période, diagnostic CIM-10).
- Cube OLAP pour requêtes multi-dimensionnelles.
- Outil de requêtage (Metabase ou Apache Superset) accessible aux
  analystes du Ministère.
- Anonymisation des données patient (k-anonymat ≥ 5).

**Impact stratégique** : très élevé (pilotage national).

**Effort** : 40 jours-homme.

#### 12. Module de télédecine

**Problème** : les zones rurales guinéennes ont peu de spécialistes.
Les centres de santé ruraux envoient leurs patients vers le CHU Donka
sans préavis, ce qui engorge les urgences.

**Solution** :

- Plateforme de téléconsultation (audio + vidéo) intégrée à GuinéeCare.
- File d'attente de téléconsultation par spécialité.
- Partage d'écran pour visualiser les résultats labo/imagerie pendant
  la consultation.
- e-Prescription (envoi direct à la pharmacie rurale).
- Traçabilité de la téléconsultation dans le DPI patient.

**Impact clinique** : très élevé (désenclavement).

**Effort** : 50 jours-homme.

#### 13. Intelligence artificielle — aide au diagnostic

**Problème** : pénurie de spécialistes, en particulier en radiologie
et en anatomopathologie. Les comptes rendus d'imagerie sont en retard.

**Solution** (expérimental) :

- Intégration de modèles de deep learning pré-entraînés pour :
  - Détection de tuberculose sur radio thoracique (modèles OMS OpenAI).
  - Détection de fractures sur radiographies osseuses.
  - Comptage cellulaire sur frottis sanguin.
- Affichage des prédictions comme **aide au diagnostic** (jamais
  comme décision autonome — validé par le médecin).
- Boucle d'apprentissage : les corrections des médecins améliorent
  le modèle.

**Impact clinique** : très élevé (potentiel).

**Effort** : 60 jours-homme (recherche + intégration + validation).

#### 14. Module de gestion du stock multi-entrepôts

**Problème** : la pharmacie centrale du CHU Donka gère plusieurs
entrepôts (pharmacie centrale, pharmacie urgences, dépôts de service).
Le module pharmacie actuel gère un seul stock.

**Solution** :

- Multi-entrepôts avec transferts inter-sites.
- Gestion des péremptions (FIFO, alertes).
- Codification GS1 (codes-barres 2D).
- Inventaire tournant automatisé.
- Réapprovisionnement automatique des dépôts de service.

**Impact opérationnel** : élevé.

**Effort** : 22 jours-homme.

#### 15. Migration Kubernetes

**Problème** : Docker Compose est suffisant pour un seul établissement
mais limite la scalabilité horizontale (multi-établissements,
haute disponibilité, blue-green deploys).

**Solution** :

- Migration de la stack Docker Compose vers Kubernetes (K3s pour
  commencer, EKS/GKE à terme).
- Helm charts pour le déploiement reproductible.
- Autoscaling horizontal (HPA) sur le backend.
- Blue-green deployments via Argo CD.
- Observabilité centralisée (Prometheus + Grafana + Loki).

**Impact opérationnel** : élevé (nationalisation).

**Effort** : 35 jours-homme.

---

## Backlog additionnel (idées en attente de priorisation)

Les évolutions suivantes ont été collectées via la boucle feedback
mais ne sont pas encore priorisées. Elles pourront entrer dans une
future roadmap :

- **Mode sombre complet** (partiellement disponible via `theme=dark`
  en v1.1.0, mais tous les composants ne sont pas encore stylés).
- **Export CSV universel** sur toutes les listes paginées.
- **Recherche phonétique** pour les noms (dialectes locaux).
- **Support du calendrier hégirien** (affichage optionnel).
- **Signature électronique** des ordonnances (carte à puce).
- **Module de gestion du sang** (banque de sang).
- **Module de stérilisation** (traçabilité des cycles).
- **Module de gestion des déchets médicaux**.
- **Intégration DMP** (Dossier Médical Partagé) si un DMP national
  voit le jour en Guinée.

---

## Suivi et gouvernance

Ce document est révisé mensuellement par le comité de pilotage. Les
évolutions confirmées entrent dans le backlog GitHub et sont suivies
via le board de projet. À chaque release, le CHANGELOG documente ce
qui a été livré et le README met à jour la roadmap publique.

Pour soumettre une nouvelle idée d'évolution, deux canaux :

1. **Boucle feedback in-app** (icône 💬) — pour tous les
   utilisateurs. Les feedbacks `suggestion` alimentent ce backlog.
2. **Réunion mensuelle du comité** — pour les chefs de service et la
   direction. Les demandes sont documentées en réunion puis intégrées
   au présent document.

La prochaine révision est prévue en **juillet 2026**, après 6 semaines
de pilote. À cette occasion, le présent document sera mis à jour avec
les évolutions effectivement retenues pour v1.2.
