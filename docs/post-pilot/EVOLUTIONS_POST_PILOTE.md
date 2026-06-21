# Évolutions post-pilote — Roadmap v1.3 et au-delà

> Public : équipe projet, direction médicale, Ministère de la Santé
> Dernière mise à jour : 2026-06-22 (v1.7.0)
> Statut : document **dynamique** — alimenté par les retours utilisateurs
> collectés via la boucle feedback de v1.1.0.

Ce document consolide les évolutions envisagées pour GuinéeCare
Hospital Suite après le pilote CHU Donka. Il ne s'agit pas d'un
engagement formel : chaque évolution sera priorisée en fonction des
retours terrain, des contraintes budgétaires et des arbitrages
stratégiques. Le backlog est organisé en trois temps : **court terme**
(v1.2-v1.3 — 6 mois), **moyen terme** (v1.4-v1.6 — 9 mois) et **long terme**
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

## v1.7 — Livré le 2026-06-22 (release v1.7.0)

La release v1.7.0 livre la **5ᵉ et dernière évolution moyen terme** :
l'**application mobile Android** (évolution 6). Avec cette release, les **5
évolutions moyen terme de la roadmap v1.4-v1.7 sont toutes livrées**.

### ✅ Évolution 6 — Application mobile Android (React Native) (LIVRÉ)

Module `mobile/` — application React Native 0.74 via Expo SDK 51, dédiée aux
médecins et infirmiers en garde. 8 écrans implémentés (Login, BiometricLock,
Dashboard, Patients, PatientDetail, QRScan, Notifications, Profile).

**Stack** : React Navigation 6, Axios + JWT avec refresh automatique,
expo-secure-store (tokens), expo-local-authentication (biométrie),
expo-barcode-scanner (QR code patient), expo-notifications (push),
@react-native-community/netinfo + AsyncStorage (offline sync), EAS Build
(builds Android APK/AAB).

**Authentification biométrique** : empreinte/Face ID au démarrage (optionnel,
désactivable). Bouton "Se déconnecter" en secours.

**Scan QR code patient** : scan du bracelet d'identification → navigation
directe vers le dossier patient. Gestion des erreurs (patient introuvable,
QR invalide, réseau).

**Mode hors-ligne** : file d'attente des mutations (POST/PATCH/DELETE) via
AsyncStorage. Replay FIFO automatique au retour du réseau. 4xx → abandon, 5xx
→ retry jusqu'à 5 fois.

**2 hooks réutilisables** : `useOfflineSync` (file d'attente + replay) et
`usePushNotifications` (Expo Push Token + channels Android + listeners).

Documentation complète : `mobile/README.md`. Points d'attention documentés
(endpoint push token à implémenter côté backend en v1.8, pas de WebSocket
temps réel sur mobile, saisie clinique limitée aux constantes vitales, pas
de cache patient offline).

### ⏭️ Évolutions moyen terme — Terminées ✅

Avec v1.7.0, **toutes les évolutions moyen terme sont livrées** :

- ✅ Évolution 6 — Application mobile Android (React Native) (v1.7.0)
- ✅ Évolution 7 — Interopérabilité HL7 FHIR R4 (v1.6.0)
- ✅ Évolution 8 — Module RH v2 (v1.5.0)
- ✅ Évolution 9 — Tableau de bord qualité avancé (v1.4.0)
- ✅ Évolution 10 — Notifications SMS réelles (v1.4.0)

La suite de la roadmap se concentre maintenant sur les **évolutions long
terme (v2.0+)** : data warehouse santé national, télémédecine, IA d'aide au
diagnostic, gestion multi-entrepôts, migration Kubernetes. Voir section
`v2.0 — Long terme (12+ mois)` ci-dessous.

---

## v1.5 — Livré le 2026-06-21 (release v1.5.0)

La release v1.5.0 livre la **3ᵉ évolution moyen terme** : le **module de
planification des ressources (RH v2)** (évolution 8). Les 2 évolutions moyen
terme restantes (app mobile React Native, HL7 FHIR R4) sont reportées à v1.6.

### ✅ Évolution 8 — Module de planification des ressources (RH v2) (LIVRÉ)

Module backend `personnel/rh_v2` avec 5 nouvelles tables (migration Alembic
`0019_rh_v2`) :

- **`shifts`** : templates récurrents (DAY/NIGHT/FULL_DAY/ON_CALL) avec
  récurrence DAILY/WEEKDAYS/WEEKEND/CUSTOM.
- **`shift_assignments`** : affectations concrètes d'un staff à un shift à
  une date. Statut SCHEDULED → CONFIRMED → COMPLETED (ou ABSENT/CANCELLED).
- **`leave_balances`** : soldes de congés par staff × année (accumulated,
  used, carried_over, pending — remaining calculé à la volée).
- **`on_call_duties`** : astreintes (TELEPHONIC/PHYSICAL/MIXED) avec
  compensation en jours de récupération.
- **`shift_swaps`** : demandes de remplacement entre staffs (workflow
  REQUESTED → ACCEPTED → APPROVED → COMPLETED | REJECTED | CANCELLED).

**Service** : `generate_assignments()` génère des affectations en masse
(selon récurrence + skip options). `_find_eligible_staff()` sélectionne
automatiquement un staff (même facility + department + profession,
status=ACTIVE, pas en conflit ni en congé). `check_conflicts()` détecte
les chevauchements. `recompute_leave_balance()` recalcule used/pending à
partir des LeaveRequest. Workflow complet des swaps (accept/approve/reject/
cancel) avec transfert automatique de l'affectation au remplaçant à
l'approbation. `get_planning()` construit la vue planning (rows × cells).

**Routes** (27 endpoints sous `/api/v1/personnel/*`) : planning hebdo
(max 90 jours), CRUD shifts, génération en masse d'affectations, CRUD
affectations + conflicts, CRUD soldes (avec auto-création), CRUD astreintes,
workflow complet des swaps.

**Frontend** : 2 nouvelles pages — `PersonnelPlanningPage` (5 onglets :
planning hebdo calendrier avec navigation + filtre département, templates
de shifts, affectations, astreintes, remplacements) et `LeaveManagementPage`
(2 onglets : demandes de congé avec approbation, soldes avec barre de
progression). 2 nouvelles entrées dans la sidebar. 30 tests backend.

### ⏭️ Évolutions moyen terme — Statut

Avec v1.5.0, 3 des 5 évolutions moyen terme sont livrées :

- ✅ Évolution 8 — Module RH v2 (v1.5.0)
- ✅ Évolution 9 — Tableau de bord qualité avancé (v1.4.0)
- ✅ Évolution 10 — Notifications SMS réelles (v1.4.0)
- ⏭️ Évolution 6 — Application mobile Android (React Native) — reportée v1.6
- ⏭️ Évolution 7 — Interopérabilité HL7 FHIR R4 — reportée v1.6

---

## v1.4 — Livré le 2026-06-21 (release v1.4.0)

La release v1.4.0 livre les **2 premières évolutions moyen terme** :
le système de notifications SMS réelles via opérateurs locaux
(évolution 10) et le tableau de bord qualité avancé avec seuils
d'alerte automatiques (évolution 9). Les 3 évolutions moyen terme
restantes (app mobile React Native, HL7 FHIR R4, module RH v2) sont
reportées à v1.5.

### ✅ Évolution 10 — Système de notifications SMS multicanal étendu (LIVRÉ)

Module backend `notifications/sms` avec 3 nouvelles tables (migration
Alembic `0017_sms_v14`) : `sms_providers` (configuration des opérateurs
avec credentials chiffrés via Fernet optionnel), `sms_messages`
(journal de chaque SMS envoyé : statut, coût GNF, opérateur,
tentatives), `sms_routing_rules` (règles de routage par catégorie de
notification).

**Provider abstraction** : 4 implémentations — `MockSmsProvider`
(dev/test, toujours succès), `OrangeSmsProvider` (OAuth2
client_credentials → Orange SMS Pro API), `MtnSmsProvider` (Bearer
token), `MoovSmsProvider` (clé API dans le body + signature).
Normalisation automatique des numéros guinéens (`622334455` →
`+224622334455`). Aucune exception ne remonte à l'appelant — tous les
échecs sont journalisés dans `SmsMessage`.

**Service** : `send_sms()` orchestre normalisation → sélection
provider (règle de routage → provider préféré → provider par défaut →
mock implicite) → envoi → journalisation. `retry_failed_sms()` avec
max 3 tentatives. `get_sms_stats()` agrège par provider/catégorie sur
une période.

**Routes** (14 endpoints sous `/api/v1/notifications/sms/*`) : CRUD
providers, CRUD règles de routage, envoi manuel, retry, historique
paginé (filtres `status`/`provider_code`/`category`/`recipient_phone`),
statistiques agrégées (coût total GNF, taux de succès par provider et
par catégorie).

**8 règles de routage par défaut** seedées automatiquement :
`lab_critical` (urgent → SMS+in_app), `incident_critical` (urgent →
SMS+email+in_app), `appointment_reminder` (normal → SMS+in_app),
`medication_dispensed` (in_app only), `admission_created` (in_app),
`invoice_ready` (normal → SMS+in_app), `quality_alert` (high →
SMS+email+in_app), `system` (in_app only).

**Frontend** : nouvelle page `/sms-admin` (4 onglets : Providers,
Règles de routage, Historique, Statistiques) accessible aux
ADMIN/SUPER_ADMIN. 27 tests backend.

### ✅ Évolution 9 — Tableau de bord qualité avancé (LIVRÉ)

Module backend `quality/dashboard` avec 2 nouvelles tables (migration
Alembic `0018_quality_dashboard`) : `quality_thresholds` (seuils
d'alerte par indicateur avec comparateur LT/LE/GT/GE/EQ, sévérité
LOW/MEDIUM/HIGH/CRITICAL, cooldown anti-spam, notify_roles,
channels), `quality_alerts` (alertes concrètes avec lifecycle OPEN →
ACKNOWLEDGED → RESOLVED → CLOSED).

**Catalogue d'indicateurs prédéfinis OMS/HAS** (10 indicateurs) :
`INOSO_RATE` (infections nosocomiales, cible < 5%), `READMIT_30D`
(réadmissions 30j, < 10%), `SAT_PATIENT` (satisfaction, > 80%),
`ED_WAIT_4H` (délai urgences, < 4h), `MORTALITY_24H` (mortalité 24h,
< 2%), `MED_ERROR_RATE` (erreurs médicamenteuses, < 1/1000),
`SURG_SITE_INFECTION` (infections site opératoire, < 3%),
`BED_OCCUPANCY` (occupation lits, ≤ 85%), `FALL_RATE` (chutes, <
3/1000), `VAGINAL_DELIVERY_RATE` (accouchements voie basse, > 80%).

**Service** : `compute_dashboard()` agrège KPIs + incidents +
alertes + tendances. `check_thresholds()` évalue les mesures récentes
contre les seuils, lève des `QualityAlert` si franchissement (avec
cooldown), notifie via `notify()` du module notifications (multi-canal
— la catégorie `quality_alert` déclenche SMS via la règle de routage).
`evaluate_threshold()` gère comparaisons numériques et qualitatives
(EQ only).

**Routes** (11 endpoints sous `/api/v1/quality/*`) : dashboard agrégé,
catalogue statique, seed-defaults (idempotent), CRUD thresholds,
liste alertes, check manuel, ack/resolve/close.

**Frontend** : 2 nouveaux onglets dans `QualityPage` — Dashboard
(5 stat cards, tableau KPIs avec statut coloré, agrégats incidents,
tendances SVG avec ligne de cible) et Alertes (liste avec filtre
statut, actions ack/resolve/close, modal de résolution, CRUD seuils).
22 tests backend.

### ⏭️ Évolutions moyen terme — Statut

Avec v1.4.0, 2 des 5 évolutions moyen terme sont livrées :

- ✅ Évolution 9 — Tableau de bord qualité avancé (v1.4.0)
- ✅ Évolution 10 — Notifications SMS réelles (v1.4.0)
- ⏭️ Évolution 6 — Application mobile Android (React Native) — reportée v1.5
- ⏭️ Évolution 7 — Interopérabilité HL7 FHIR R4 — reportée v1.5
- ⏭️ Évolution 8 — Module RH v2 (plannings/gardes) — reportée v1.5

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
