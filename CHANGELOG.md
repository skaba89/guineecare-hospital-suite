# Changelog

## [1.4.0] — 2026-06-21

### Added — Notifications SMS réelles (Orange/MTN/Moov) + tableau de bord qualité avancé

Cette release livre les **2 premières évolutions moyen terme** identifiées
dans `docs/post-pilot/EVOLUTIONS_POST_PILOTE.md` : le **(10) système de
notifications SMS réelles via opérateurs locaux** et le **(9) tableau de
bord qualité avancé** avec seuils d'alerte automatiques. Les 3 évolutions
moyen terme restantes (app mobile React Native, HL7 FHIR R4, module RH v2)
sont reportées à v1.5.

#### Module backend `notifications/sms` — providers multicanal + routing

3 nouvelles tables (migration Alembic `0017_sms_v14`) :

- **`sms_providers`** — configuration des opérateurs (code, credentials
  chiffrés via Fernet optionnel, sender ID, coût/SMS en GNF, quotas).
- **`sms_messages`** — journal complet de chaque SMS envoyé (statut
  PENDING/SENT/DELIVERED/FAILED/REJECTED, operator_message_id, coût,
  tentatives, timestamps).
- **`sms_routing_rules`** — règles de routage par catégorie de
  notification (ex: `lab_critical` → `in_app,sms` avec `min_priority=urgent`).

**Provider abstraction** (`backend/app/modules/notifications/sms_provider.py`) :

- `SmsProviderBase` — interface commune, validation E.164, timeout 10s.
- `MockSmsProvider` — toujours succès, log JSONL optionnel (`SMS_MOCK_LOG`).
- `OrangeSmsProvider` — OAuth2 client_credentials → POST
  `/smsmessaging/v1/outbound/{sender}/requests` (doc Orange API).
- `MtnSmsProvider` — POST HTTP simple avec Bearer token.
- `MoovSmsProvider` — POST HTTP avec clé API dans le body + signature.
- `normalize_phone_gn()` — normalise les numéros guinéens (622334455 → +224622334455).
- `encrypt_credential()` / `decrypt_credential()` — chiffrement Fernet
  optionnel (fallback clair en dev/test).

**Service** (`backend/app/modules/notifications/sms_service.py`) :

- `send_sms()` — orchestration complète : normalisation → sélection
  provider (règle de routage → provider préféré → provider par défaut →
  mock implicite) → envoi → journalisation `SmsMessage`. Ne lève jamais
  d'exception.
- `get_routing_rule()` — résolution avec priorité facility-spécifique
  surclasse la règle globale.
- `should_send_sms_for_rule()` — vérifie que la priorité atteint le seuil.
- `retry_failed_sms()` — retry avec max 3 tentatives cumulées.
- `get_sms_stats()` — agrégats par provider / catégorie sur une période.
- `seed_default_providers()` — crée un provider mock au premier accès
  (dev convenience).
- `seed_default_routing_rules()` — 8 règles par défaut (`lab_critical`,
  `incident_critical`, `appointment_reminder`, `medication_dispensed`,
  `admission_created`, `invoice_ready`, `quality_alert`, `system`).

**Routes** (`/api/v1/notifications/sms/*` — tag OpenAPI `notifications-sms`) :

- `GET /providers` — liste (credentials masqués, flags `has_api_key`/`has_api_secret`).
- `GET /providers/supported` — catalogue statique (mock/orange/mtn/moov).
- `POST /providers` — création (credentials chiffrés avant stockage).
- `PATCH /providers/{id}` — mise à jour partielle.
- `DELETE /providers/{id}` — suppression (mock protégé).
- `POST /providers/{id}/test` — envoi d'un SMS de test (coût réel).
- `GET /rules` — liste des règles de routage (multi-tenant).
- `POST /rules` — création (409 si catégorie déjà enabled).
- `PATCH /rules/{id}` — mise à jour.
- `DELETE /rules/{id}` — suppression.
- `POST /send` — envoi manuel (admin only, `notification.send`).
- `POST /messages/{id}/retry` — retry d'un SMS échoué.
- `GET /messages` — historique paginé (filtres `status`, `provider_code`,
  `category`, `recipient_phone`).
- `GET /stats?days=30` — statistiques agrégées.

**Permissions RBAC** (2 nouvelles) :

- `notification.manage` — CRUD providers + règles (SUPER_ADMIN/ADMIN bypass).
- `notification.send` — envoi manuel + retry (déjà existant, étendu au SMS).

Tests (`backend/tests/test_sms.py`) — **27 tests** : CRUD providers, règles
de routage, envoi mock, normalisation téléphone, retry, stats, permissions
RBAC, helpers unitaires.

#### Module backend `quality/dashboard` — tableau de bord qualité avancé

2 nouvelles tables (migration Alembic `0018_quality_dashboard`) :

- **`quality_thresholds`** — seuils d'alerte par indicateur (comparateur
  LT/LE/GT/GE/EQ, valeur, sévérité LOW/MEDIUM/HIGH/CRITICAL, cooldown,
  notify_roles, channels).
- **`quality_alerts`** — alertes concrètes levées quand une mesure franchit
  un seuil. Cycle : OPEN → ACKNOWLEDGED → RESOLVED → CLOSED.

**Catalogue d'indicateurs prédéfinis** (10 indicateurs OMS/HAS) :

- `INOSO_RATE` — taux d'infections nosocomiales (cible OMS : < 5%).
- `READMIT_30D` — taux de réadmissions à 30 jours (cible HAS : < 10%).
- `SAT_PATIENT` — satisfaction patient (cible : > 80%).
- `ED_WAIT_4H` — délai moyen prise en charge urgences (cible : < 4h).
- `MORTALITY_24H` — mortalité 24h post-admission (cible : < 2%).
- `MED_ERROR_RATE` — erreurs médicamenteuses (cible : < 1/1000).
- `SURG_SITE_INFECTION` — infections site opératoire (cible OMS : < 3%).
- `BED_OCCUPANCY` — taux d'occupation des lits (cible : ≤ 85%).
- `FALL_RATE` — taux de chutes patient (cible HAS : < 3/1000).
- `VAGINAL_DELIVERY_RATE` — taux d'accouchements voie basse (cible OMS : > 80%).

**Seuils par défaut** (10 thresholds liés aux indicateurs ci-dessus) :
seedés via `POST /quality/seed-defaults?facility_id=...` (idempotent).

**Service** (`backend/app/modules/quality/dashboard_service.py`) :

- `compute_dashboard()` — agrège KPIs (dernière valeur par indicateur),
  incidents (par type/sévérité/statut, délai moyen résolution), alertes
  (open/acknowledged/resolved + 10 récentes), tendances (5 premiers
  indicateurs, séries temporelles).
- `check_thresholds()` — évalue toutes les mesures récentes contre les
  thresholds actifs. Lève une `QualityAlert` si franchissement + cooldown
  respecté. Notifie via `notify()` du module notifications (multi-canal,
  la catégorie `quality_alert` déclenche SMS via la règle de routage).
- `evaluate_threshold()` — comparaison numérique ou string (EQ sur
  catégories qualitatives).
- `acknowledge_alert()` / `resolve_alert()` / `close_alert()` — cycle de
  vie humain.

**Routes** (`/api/v1/quality/*` — tag OpenAPI `quality-dashboard`) :

- `GET /dashboard?days=30` — dashboard agrégé (multi-tenant).
- `GET /indicators/catalog` — catalogue statique OMS/HAS (documentation).
- `POST /seed-defaults?facility_id=...` — insertion indicateurs + seuils.
- `GET /thresholds` — liste paginée.
- `POST /thresholds` — création.
- `PATCH /thresholds/{id}` — mise à jour.
- `DELETE /thresholds/{id}` — suppression.
- `GET /alerts?status=...` — liste paginée.
- `POST /alerts/check` — déclenche l'évaluation manuelle des seuils.
- `POST /alerts/{id}/acknowledge` — prise en charge.
- `POST /alerts/{id}/resolve` — résolution avec note.
- `POST /alerts/{id}/close` — clôture.

**Permission RBAC** (1 nouvelle) :

- `quality.dashboard` — consultation dashboard avancé (étendue à DOCTOR
  et NURSE en plus de ADMIN/SUPER_ADMIN).

Tests (`backend/tests/test_quality_dashboard.py`) — **22 tests** : CRUD
thresholds, dashboard agrégé, seed defaults, check_thresholds (lève une
alerte si franchissement, respecte le cooldown), lifecycle complet des
alertes (open → ack → resolve → close), comparateurs (LT/LE/GT/GE/EQ),
valeurs avec `%`, comparaison non numérique (EQ only).

#### Frontend — nouvelles pages et onglets

- **`SmsAdminPage.tsx`** (nouvelle page, route `/sms-admin`) — 4 onglets :
  - **Providers** : liste + formulaire de création (code/name/credentials/
    coût/SMS), toggle enable/disable, test provider (modal), suppression
    (mock protégé).
  - **Règles de routage** : liste des règles par catégorie, badges canaux
    (sms/email/in_app), toggle enable/disable.
  - **Historique** : tableau paginé des SMS envoyés, filtre par statut,
    envoi manuel (formulaire), retry des échecs.
  - **Statistiques** : 5 KPI cards (total, succès, échecs, taux, coût GNF)
    + tables agrégées par provider et par catégorie.
- **`QualityDashboardTab.tsx`** (nouvel onglet dans `QualityPage`) —
  Dashboard agrégé : 5 stat cards, tableau KPIs (dernière valeur vs cible
  avec statut coloré), agrégats incidents (par type/sévérité/statut),
  tendances SVG (5 indicateurs principaux avec ligne de cible), boutons
  "Seed OMS/HAS" et "Check seuils".
- **`QualityAlertsTab.tsx`** (nouvel onglet dans `QualityPage`) — 2
  sous-onglets : Alertes (liste avec filtre statut, actions ack/resolve/
  close, modal de résolution avec note) + Seuils (CRUD complet avec
  formulaire de création).
- **Sidebar** — nouvelle entrée "SMS Admin" sous la section SYSTÈME
  (icône `MessageSquare`, visible ADMIN/SUPER_ADMIN uniquement).
- **`useLookupData`** — fetch également `/quality/indicators` pour le
  dropdown de sélection d'indicateur dans le formulaire de seuil.
- **`ProtectedRoute.useNavVisibility`** — nouveau flag `canSeeSmsAdmin`.

#### Configuration et dépendances

- **`backend/requirements.txt`** — ajout de `requests==2.32.3` (appels
  HTTP aux opérateurs SMS Orange/MTN/Moov).
- **`backend/app/main.py`** — version bump 1.3.0 → 1.4.0, nouveaux routers
  `sms_router` et `quality_dashboard_router`, nouveaux tags OpenAPI
  `notifications-sms` et `quality-dashboard`.
- **`backend/tests/conftest.py`** — import des nouveaux modèles
  (`SmsProvider`, `SmsMessage`, `SmsRoutingRule`, `QualityThreshold`,
  `QualityAlert`) pour que `Base.metadata.create_all` les crée en SQLite.
- **`backend/app/modules/rbac/seed.py`** — 2 nouvelles permissions
  (`notification.manage`, `quality.dashboard`) + `quality.dashboard`
  ajoutée à DOCTOR et NURSE.

#### Variables d'environnement

- `SMS_FERNET_KEY` (optionnel) — clé Fernet pour chiffrer les credentials
  SMS. En dev/test sans cette clé, les credentials sont stockés en clair.
- `SMS_MOCK_LOG` (optionnel) — chemin d'un fichier JSONL où le provider
  mock journalise chaque SMS (utile pour audit local en démo).

---

## [1.3.0] — 2026-06-21

### Added — Internationalisation EN/FR + dashboard temps réel (WebSocket) + mode hors-ligne PWA

Cette release livre les **3 évolutions court terme restantes** identifiées
dans le document post-pilote (EVOLUTIONS_POST_PILOTE.md) :
**(2) l'internationalisation complète EN/FR**, **(3) le dashboard temps
réel via WebSocket**, et **(5) le mode hors-ligne PWA**. Avec cette
release, les 5 évolutions court terme (v1.2) sont toutes livrées.

#### Module backend `i18n` — internationalisation EN/FR

Deux nouveaux endpoints publics (pas d'auth requise — le frontend en a
besoin pour afficher la page de login dans la langue du navigateur) :

- **`GET /api/v1/i18n/translations/{locale}`** — retourne le catalogue
  de traductions pour la langue demandée (`fr` ou `en`). Le frontend
  hydrate son provider i18n avec ce catalogue au démarrage.
- **`GET /api/v1/i18n/supported`** — liste des langues supportées +
  langue par défaut (`fr`).

**Service de traduction** (`backend/app/modules/i18n/service.py`) :

- Catalogues FR (par défaut) et EN baked into the source code (dicts
  Python, pas de fichiers JSON externes — bénéficie du type checking).
- Clés dotted (`auth.login.invalid_credentials`, `rbac.permission_denied`,
  `tenant.access_denied`, `common.not_found`, etc.).
- `translate(key, locale, **vars)` — résout la clé dans la catalogue
  de la locale, fallback sur FR, fallback sur la clé elle-même si
  manquante (avec log WARNING).
- `negotiate_locale(accept_language)` — parse le header
  `Accept-Language` et retourne la meilleure locale supportée
  (tri par qualité décroissante, fallback sur `fr`).
- Interpolation des variables via `str.format_map` avec un dict safe
  (les variables manquantes rendent en chaîne vide, pas de KeyError).

**Catalogue initial** : 25 clés couvrant les messages d'erreur auth,
RBAC, multi-tenant, common, patients, documents, feedback, i18n. Le
catalogue est extensible sans casser la rétro-compatibilité (les clés
manquantes retournent la clé elle-même).

Tests (`backend/tests/test_i18n.py`) — 23 tests en 3 classes :

- `TestTranslate` (6) — FR default, EN, missing key fallback,
  variable interpolation, missing variable, unsupported locale.
- `TestNegotiateLocale` (12) — paramétré sur 11 cas
  (`None`, `""`, `fr`, `fr-FR`, `fr-FR,fr;q=0.9,en;q=0.8`, `en`,
  `en-US`, `en-US,en;q=0.9`, `de-DE,de;q=0.9,en;q=0.8`,
  `de-DE,de;q=0.9,fr;q=0.8`, `zh-CN`) + test de tri par qualité.
- `TestI18nRoutes` (5) — supported locales, translations FR,
  translations EN, unsupported locale (404), pas d'auth requise.

#### Module backend `realtime` — WebSocket temps réel

Un endpoint WebSocket authentifié par JWT (passé en query param
`?token=...`, convention navigateur car les WS ne supportent pas le
header `Authorization`) :

- **`WS /api/v1/realtime/ws?token=<JWT>`** — ouvre une connexion
  persistante qui stream les events temps réel au client connecté.
  - Authentification : décode le JWT, extrait `facility_id` et `role`.
  - SUPER_ADMIN subscribe au canal broadcast `*` (reçoit tous les
    events de tous les établissements).
  - Autres rôles subscribe au canal de leur `facility_id` (reçoivent
    uniquement les events de leur établissement).
  - Heartbeat : le serveur envoie `{type: "ping"}` toutes les 25s
    pour maintenir la connexion à travers les proxies nginx
    (timeout par défaut 60s).
  - À la connexion, le serveur envoie `{type: "connected", payload:
    {facility_id, role, channel}}` pour confirmer l'authentification.

- **`GET /api/v1/realtime/stats`** — statistiques du broker
  (nombre d'abonnés par canal, nombre total de connexions, état Redis).
  Nécessite `ADMIN+` ou `SUPER_ADMIN`.

- **`POST /api/v1/realtime/test-broadcast`** — publie un event
  `test.broadcast` sur le canal de l'établissement courant. Utile
  pour vérifier qu'un client WS connecté reçoit bien les messages.
  Nécessite `ADMIN+`.

**Broker pub/sub** (`backend/app/modules/realtime/broker.py`) :

- `InProcessBroker` — broker asyncio basé sur `asyncio.Queue`. Chaque
  subscriber enregistre une queue pour un `facility_id` (ou `*` pour
  le broadcast). `publish_event` pousse l'event dans toutes les queues
  correspondantes + le canal broadcast.
- Thread-safe via `loop.call_soon_threadsafe` — `publish_event` est
  sync et peut être appelé depuis des handlers sync sans bloquer.
- Queue size limitée à 100 — en cas de queue full, le plus ancien
  event est drop (jamais le publisher ne bloque).
- **Redis optionnel** : si `REDIS_URL` est set, le broker publie
  également sur un channel Redis `guineecare:realtime:{facility_id}`
  et subscribe au pattern `guineecare:realtime:*` pour fan-out
  multi-worker. Redis est créé lazy et sa défaillance est non-fatale
  (fallback in-process only, log WARNING).

**Publication KPI sur mutations clés** — trois modules publient
désormais des events temps réel quand une mutation affecte le
dashboard :

- **Admissions** (`POST /api/v1/admissions`) → `kpi.admissions.today.count`
  avec `delta=+1`. Le dashboard live-counte les admissions.
- **Billing** (`POST /api/v1/billing/invoices/{id}/payments`) →
  `kpi.billing.payments.today.amount` avec `delta=+amount`. Le
  dashboard finance live-totalise les encaissements.
- **Laboratoire** (`POST /api/v1/laboratory/results/{id}/validate`) →
  `kpi.lab.results.validated.count` avec `delta=+1`. Le dashboard
  live-counte les résultats validés.

Tests (`backend/tests/test_realtime.py`) — 14 tests en 4 classes :

- `TestBrokerInProcess` (4) — publish single subscriber, multi-facility
  isolation, broadcast channel `*` (SUPER_ADMIN), stats.
- `TestRealtimeStatsRoute` (4) — requires auth, requires admin role,
  admin success, test-broadcast.
- `TestWebSocketAuth` (3) — missing token (close 4401), invalid token,
  valid token receives `connected` event.
- `TestWebSocketEventDelivery` (3) — same-facility delivery, SUPER_ADMIN
  broadcast from any facility, cross-facility isolation (DOCTOR on
  fac-A does not receive fac-B events).

#### Frontend — i18n Provider + Language Toggle + Realtime Status

**Provider i18n** (`frontend/src/i18n/index.tsx`) :

- Implémentation lightweight (sans i18next) — 100 lignes suffisent
  pour notre use case (lookup key→value + interpolation).
- Fetch le catalogue depuis `/api/v1/i18n/translations/{locale}` au
  démarrage. Fallback sur FR si le fetch échoue.
- Locale persistée dans `localStorage` (`guineecare_locale`).
- Détection initiale : localStorage > `navigator.language` > `fr`.
- `useI18n()` hook expose `{ locale, setLocale, t, loading, supportedLocales }`.
- `t(key, vars)` interpole `{vars}` via regex replacement (missing
  vars → empty string).

**LanguageToggle** (`frontend/src/components/LanguageToggle.tsx`) :

- Dropdown compact avec drapeau + code locale (🇫🇷 FR / 🇬🇧 EN).
- Menu déroulant avec les langues supportées, checkmark sur la
  langue active.
- Ferme le menu au clic en dehors ou sur une option.
- Accessible : `aria-haspopup`, `aria-expanded`, `role="menu"`,
  `role="menuitemradio"`, `aria-checked`.

**RealtimeStatus** (`frontend/src/components/RealtimeStatus.tsx`) :

- Badge dans le header de l'app montrant l'état de la connexion WS :
  - 🟢 `Live` (connected)
  - 🟡 `…` (connecting, animation pulse)
  - 🔴 `Hors ligne` (disconnected, retrying)
  - ⚪ `—` (idle / non connecté)
- Tooltip affiche le dernier event reçu.
- Auto-reconnect avec exponential backoff (1s → 2s → 4s → 8s → max 30s).

**Hook useRealtimeKPIs** (`frontend/src/hooks/useRealtimeKPIs.ts`) :

- Hook React qui gère la connexion WebSocket et expose `{ status,
  lastEvent, events, disconnect, reconnect }`.
- Filtre optionnel par `typePrefix` (ex: `kpi.admissions` pour ne
  recevoir que les events KPI d'admissions).
- Sliding window des 50 derniers events (pour debug / affichage
  timeline).
- Auto-reconnect avec exponential backoff. Skip les pings.

**DashboardPage live** — le dashboard consomme désormais les events
temps réel via `useRealtimeKPIs({ typePrefix: "kpi." })` :

- `kpi.admissions.today.count` → incrémente `stats.admissions` live.
- `kpi.lab.results.validated.count` → décrémente
  `stats.pendingLabOrders` live.
- Pas de refetch global — les compteurs sont ajustés localement et
  reconciliés au prochain refresh manuel ou `refresh-resource`.

#### Frontend — PWA (manifest + service worker + icônes)

**Manifest** (`frontend/public/manifest.webmanifest`) :

- `name`, `short_name`, `description`, `start_url=/`, `display=standalone`.
- `theme_color=#0f766e` (teal, couleur de marque), `background_color=#ffffff`.
- 2 icônes PNG (192×192 et 512×512) avec `purpose: "any maskable"`.
- 3 raccourcis (Nouvelle admission, Recherche patient, Urgences) —
  accessibles via le menu contextuel de l'icône sur Android.
- Catégories : `medical`, `health`, `productivity`.

**Service worker** (`frontend/public/sw.js`) :

- **App shell** (HTML, JS, CSS, icons) — stratégie stale-while-revalidate :
  sert depuis le cache immédiatement, rafraîchit en arrière-plan.
- **API GET** — stratégie network-first : tente le réseau, fallback
  sur le cache si offline. Réponses 200 seulement sont cachées.
- **API mutations** (POST/PUT/DELETE) — pass-through (non cachées).
  Si offline, retourne un 503 avec `{detail: "Offline — request
  queued for sync"}`. L'UI affiche un toast d'erreur.
- **WebSocket** — exclu du SW (les WS ne sont pas cachables).
- Versionnage du cache via `CACHE_VERSION = "guineecare-v1.3.0"` —
  bump à chaque release pour invalider les caches obsolètes au
  prochain `activate`.

**Icônes** — générées par `scripts/generate_pwa_icons.py` (PIL) :

- 192×192 et 512×512 (PNG) + favicon 32×32.
- Design : carré arrondi teal (#0f766e) avec monogramme "GC" blanc
  centré. Aucun asset externe requis — régénérable en une commande.

**Enregistrement du SW** (`frontend/src/main.tsx`) :

- Le SW n'est enregistré qu'en production (`import.meta.env.PROD`).
  En dev (vite dev server), le SW est désactivé pour éviter de cacher
  les fichiers source qui changent à chaque HMR.
- Logs informatifs sur le scope du SW.

**HTML head** (`frontend/index.html`) :

- `<meta name="theme-color">`, `<meta name="description">`.
- `<link rel="manifest">`, `<link rel="icon">`, `<link rel="apple-touch-icon">`.
- HTML `lang="fr"` (langue par défaut, ajustée dynamiquement par
  l'i18n provider au runtime).

### Changed

- `APP_VERSION` bumped de `1.2.0` à `1.3.0`.
- Tags OpenAPI enrichis : `i18n` et `realtime` ajoutés à la liste
  des tags documentés.
- Route racine `/api/v1` — `i18n` et `realtime` ajoutés à la liste
  des modules disponibles.
- `docs/api/openapi.json` régénéré (619kB → inclut les 3 nouveaux
  endpoints i18n + 3 nouveaux endpoints realtime).
- `docs/api/guineecare.postman_collection.json` régénéré (inclut
  les nouveaux endpoints).
- `EVOLUTIONS_POST_PILOTE.md` — évolutions 2, 3, 5 marquées
  ✅ LIVRÉ v1.3.0 avec détails d'implémentation.

### Tests

- **Backend** : 353 tests passent (316 + 37 nouveaux pour i18n + realtime).
- **Frontend** : build production OK (Vite 8.0.16, 263kB gzippé pour
  le bundle principal).
- **E2E Playwright** : 16 tests (inchangés — les nouveautés i18n/realtime
  n'ajoutent pas de parcours E2E critique, les composants sont testés
  via les tests backend + le build frontend).

### Migration

Aucune migration de base de données requise — le module i18n est
stateless (catalogues en code), et le module realtime utilise un
broker in-process (pas de persistance). La compatibilité ascendante
est totale : un frontend v1.2.0 fonctionne contre un backend v1.3.0
et vice-versa (les nouveaux endpoints sont additifs).

---

## [1.2.0] — 2026-06-21

### Added — Export PDF des documents cliniques + recherche globale (Ctrl+K)

Cette release livre les deux premières évolutions prioritaires
identifiées dans le document post-pilote (EVOLUTIONS_POST_PILOTE.md) :
**(1) l'impression PDF des documents cliniques** (ordonnances, comptes
rendus d'imagerie, résultats de laboratoire, factures) et **(4) la
recherche globale multi-ressources** accessible via Ctrl+K. Ces deux
fonctionnalités répondent aux deux remontées les plus fréquentes de la
phase pilote : l'impossibilité d'imprimer proprement les documents
médicaux (les pharmaciens d'officine exigent une ordonnance papier
signée), et la frustration de devoir savoir dans quel module chercher
pour retrouver un dossier.

#### Module backend `documents` (PDF generation via ReportLab)

Quatre nouveaux endpoints, un par type de document, qui génèrent un PDF
à la volée et le renvoient en flux (`application/pdf`) :

- **`GET /api/v1/documents/prescriptions/{clinical_note_id}/pdf`** —
  génère une ordonnance PDF à partir d'une `ClinicalNote` dont le
  `note_type` est `PRESCRIPTION`. Inclut l'en-tête établissement, le
  bloc d'identification patient, le contenu de la prescription, le bloc
  signature du médecin prescripteur.
- **`GET /api/v1/documents/imaging-reports/{imaging_order_id}/pdf`** —
  génère un compte rendu d'imagerie PDF à partir d'une `ImagingOrder`
  et de son `ImagingResult` associé. Si aucun résultat n'existe encore,
  le PDF est généré avec les informations de la demande seule.
- **`GET /api/v1/documents/lab-results/{lab_order_id}/pdf`** — génère
  un résultat de laboratoire PDF à partir d'une `LabOrder` et de son
  `LabResult` associé. Si l'interprétation contient le mot `CRITIQUE`,
  un bandeau rouge de alerte est ajouté au PDF pour attirer l'attention
  du médecin prescripteur.
- **`GET /api/v1/documents/invoices/{invoice_id}/pdf`** — génère une
  facture patient PDF à partir d'une `Invoice` et de ses `Payment`
  associés. Inclut le détail des montants (net, payé, reste à charge
  en rouge si > 0) et la liste des paiements encaissés.
- **`GET /api/v1/documents/audit`** — liste paginée des PDF générés
  (audit trail). Filtrable par `document_type`, `patient_id`. SUPER_ADMIN
  voit tous les établissements ; ADMIN et les autres rôles ne voient
  que leur établissement.

Tous les endpoints acceptent le paramètre `?download=1` pour forcer le
téléchargement (Content-Disposition: attachment) au lieu de l'affichage
inline (par défaut).

**Bibliothèque PDF** : ReportLab 4.2.5 (pure Python, aucune dépendance
système). Le cahier des charges initial mentionnait WeasyPrint, mais
WeasyPrint nécessite cairo/pango partagés — incompatible avec
l'environnement Docker léger du pilote CHU Donka. ReportLab produit des
PDF équivalents en qualité avec un footprint minimal.

**Audit trail** : chaque génération de PDF est journalisée dans la
nouvelle table `documents_generated` (migration Alembic 0016) avec le
SHA-256 du PDF produit, permettant de détecter les régénérations
identiques sans stocker les octets du PDF (question de rétention PII).
Une entrée d'audit log (`document.<type>_generated`) est également
écrite via `audit_log()`, plus une entrée d'activité
(`document.<type>_generated`).

Modèles (`backend/app/modules/documents/models.py`) :

- **`DocumentGenerated`** — `facility_id`, `document_type` (PRESCRIPTION,
  IMAGING_REPORT, LAB_RESULT, INVOICE), `source_id` (ID de la ressource
  source), `patient_id`, `generated_by`, `generated_at`,
  `file_size_bytes`, `checksum_sha256`, `note`. Index sur `facility_id`,
  `document_type`, `source_id`, `patient_id`, `generated_at`.

Tests (`backend/tests/test_documents.py`) — 19 tests en 5 classes :

- `TestPrescriptionPDF` (6) — success, download flag, wrong note_type
  (400), not found (404), cross-tenant (403), audit row written.
- `TestImagingReportPDF` (3) — with result, without result (demande
  seule), not found.
- `TestLabResultPDF` (3) — with result, without result, critical value
  highlighted.
- `TestInvoicePDF` (3) — without payments, with payments, not found.
- `TestDocumentsAudit` (4) — empty list, after generation, filter by
  document_type, filter by patient_id.

#### Module backend `search` (recherche globale multi-ressources)

Un nouvel endpoint qui recherche en parallèle sur 5 catégories de
ressources et renvoie les résultats groupés :

- **`GET /api/v1/search?q=...&limit=10&max_total=50&categories=patient,invoice`**

Catégories recherchées (par défaut toutes) :

- **Patients** — `first_name`, `last_name`, `patient_number`, `phone`,
  `national_id`.
- **Factures** — `invoice_number`, `description`.
- **Demandes laboratoire** — `id`, `LabTest.name`, `LabTest.code` (join).
- **Demandes imagerie** — `id`, `exam_type`, `body_region`,
  `clinical_info`.
- **Notes cliniques** — `content` (recherche par mot-clé dans les
  observations et consultations).

**Recherche par préfixe** : si la requête commence par `PAT-`, `INV-`,
`LAB-` ou `IMG-`, la recherche se limite à la catégorie correspondante
et le préfixe est retiré du motif. Exemple : `?q=PAT-1234` ne cherche
que dans les patients avec le motif `1234`.

**Filtrage multi-tenant** : les résultats sont automatiquement
restreints à l'établissement de l'utilisateur courant via `tenant_query`
(sauf SUPER_ADMIN qui voit tous les établissements).

**Performance** : la recherche s'appuie sur les indexes déjà en place
(`patient_number`, `invoice_number`, etc.). Pour les volumétries >100k
lignes par table, une migration vers PostgreSQL tsvector + GIN ou
Meilisearch est prévue en v1.3.

Tests (`backend/tests/test_search.py`) — 21 tests en 6 classes :

- `TestSearchBasics` (3) — too short query (422), no results,
  unauthenticated (401).
- `TestPatientSearch` (4) — by last name, first name, patient_number,
  phone.
- `TestInvoiceSearch` (2) — by invoice_number, by description.
- `TestResourceSearch` (4) — lab by test name, lab by test code, imaging
  by body_region, clinical note by content.
- `TestPrefixSearch` (2) — PAT- restricts to patients, INV- restricts
  to invoices.
- `TestTenantIsolation` (2) — doctor in facility A cannot see facility B
  patients, SUPER_ADMIN sees all facilities.
- `TestCategoriesAndCapping` (4) — categories filter restricts search,
  invalid category (422), limit_per_category caps results, max_total
  caps all results.

#### Frontend — Command Palette Ctrl+K + bouton PDF

Nouveau composant `CommandPalette` (`frontend/src/components/CommandPalette.tsx`)
qui s'ouvre avec **Ctrl+K** (ou **Cmd+K** sur macOS) et permet de
lancer une recherche globale depuis n'importe quelle page. Résultats
groupés par catégorie (Patients, Factures, Laboratoire, Imagerie, Notes
cliniques), navigation clavier (↑↓ Enter Esc), debounce 250ms. Un
bouton « Rechercher… » est ajouté en haut de la sidebar pour les
utilisateurs qui ne connaissent pas le raccourci clavier.

Nouveau composant `PdfButton` (`frontend/src/components/PdfButton.tsx`)
réutilisable : appelle l'endpoint `/api/v1/documents/*/{id}/pdf` avec
le JWT, récupère le blob, l'ouvre dans un nouvel onglet (preview
navigateur PDF). Trois variantes (ghost, primary, outline), deux
tailles (sm, md), état de chargement avec spinner.

Intégration du bouton PDF sur trois pages :

- **`FinancePage`** — colonne PDF sur la liste des factures.
- **`LabPage`** — bouton PDF sur chaque ligne de la liste des demandes
  laboratoire.
- **`ImagingPage`** — bouton PDF sur chaque ligne de la liste des
  demandes d'imagerie.

#### Migration Alembic 0016

`backend/alembic/versions/0016_documents.py` — crée la table
`documents_generated` avec 5 indexes (facility_id, document_type,
source_id, patient_id, generated_at).

#### Dépendances

- Ajout de `reportlab==4.2.5` à `backend/requirements.txt`.

#### OpenAPI 3.1 — 29 tags (vs 27 en v1.1.0)

Deux nouveaux tags documentés : `documents` et `search`. La spec
régénérée (`docs/api/openapi.json`, 608 KB) couvre désormais 152
endpoints (vs 146 en v1.1.0). Collection Postman régénérée (194 KB, 29
dossiers).

#### Tests — 316 backend tests (vs 276 en v1.1.0)

40 nouveaux tests (19 documents + 21 search). Toutes les suites
existentes restent vertes (aucune régression).

---

## [1.1.0] — 2026-06-21

### Added — Conduite du changement + formation + évolutions post-pilote

Cette release ouvre la phase d'exploitation post-déploiement en
ajoutant (1) un socle d'endpoints orientés "expérience utilisateur" —
préférences UI, items récents, boucle de feedback — et (2) un corpus
documentaire complet de conduite du changement et de formation par
rôle, destiné à être utilisé immédiatement par l'équipe de déploiement
terrain au CHU Donka.

#### Nouveau module backend `user_profile` (préférences, feedback, items récents)

Trois nouvelles tables, une migration Alembic 0015, et 8 nouveaux
endpoints :

- **`GET /api/v1/me/preferences`** — retourne les préférences UI de
  l'utilisateur courant (locale, theme, default_page_size,
  dashboard_refresh_seconds, extra JSON). Retourne des valeurs par
  défaut si l'utilisateur n'a jamais personnalisé son espace.
- **`PUT /api/v1/me/preferences`** — mise à jour partielle des
  préférences. Toutes les modifications sont journalisées dans
  l'audit log (`user.preferences.update`).
- **`POST /api/v1/feedback`** — soumet un retour utilisateur (bug,
  suggestion, question, praise). L'`user_agent` et la date sont
  capturés automatiquement. Journalisation audit
  (`feedback.create`).
- **`GET /api/v1/feedback`** — liste paginée des feedbacks.
  Filtrable par `category`, `status`, `facility_id`. Le paramètre
  `mine=true` restreint aux feedbacks de l'utilisateur courant.
  Les non-admins ne voient que leurs propres feedbacks ; les ADMIN
  voient ceux de leur établissement ; SUPER_ADMIN voit tout.
- **`PATCH /api/v1/feedback/{id}`** — triage / résolution
  (ADMIN+ uniquement). Trace la résolution avec `admin_response`,
  `resolved_at`, `resolved_by`. Audit log (`feedback.resolve`).
- **`GET /api/v1/me/recent`** — liste les derniers items
  consultés par l'utilisateur (patients, demandes labo, imagerie,
  etc.). Filtrable par `resource_type`, limit configurable (max 50).
- **`POST /api/v1/me/recent`** — enregistre une consultation
  (upsert : re-visite d'un item le fait remonter en tête). Pruning
  automatique à 50 items par utilisateur (sliding window).
- **`DELETE /api/v1/me/recent`** — vide l'historique.

Modèles (`backend/app/modules/user_profile/models.py`) :

- **`UserPreference`** (1:1 avec `users`) — `locale` (fr|en),
  `theme` (light|dark|auto), `default_page_size` (5-200),
  `dashboard_refresh_seconds` (0-600), `extra` (JSON libre).
- **`UserFeedback`** — append-only. Catégorie (bug/suggestion/
  question/praise), priorité (low/normal/high/urgent), statut
  (open/triaged/resolved/wontfix), `admin_response`, `resolved_at`,
  `resolved_by`. Index sur `created_at`, `user_id`, `facility_id`,
  `category`, `status`.
- **`UserRecentItem`** — contrainte unique sur
  `(user_id, resource_type, resource_id)` pour l'upsert.

Migration Alembic `0015_user_profile` (3 tables, 8 index, 1 contrainte
unique). RBAC : 2 nouvelles permissions seedées
(`feedback.read`, `feedback.resolve`) — SUPER_ADMIN et ADMIN bypass.

Pydantic v2 : `ConfigDict(from_attributes=True)`, `Literal` pour les
enums strictes (Locale, Theme, FeedbackCategory, FeedbackPriority,
FeedbackStatus, ResourceType).

Tests (`backend/tests/test_user_profile.py`) — 36 nouveaux tests en
3 classes :

- `TestPreferences` (10) — defaults, partial update, validation
  (locale, theme, page_size, refresh bounds), audit log trail.
- `TestFeedback` (13) — submit, minimal, invalid category,
  message too long, audit log, list mine / admin / super-admin,
  filter by category, resolve flow, cross-facility forbidden,
  non-admin forbidden, not found, audit log.
- `TestRecentItems` (13) — record, bubble-to-top, order, filter,
  limit, prune at MAX_RECENT_ITEMS, clear, isolation per user,
  invalid resource type, auth required.

Configuration tests (`backend/tests/conftest.py`) :
`TestingSessionLocal` passe à `expire_on_commit=False` pour éviter
les `DetachedInstanceError` quand les tests accèdent à `user.id`
après une requête.

#### OpenAPI 3.1 — 27 tags (vs 25 en v1.0.0)

Deux nouveaux tags documentés : `user-profile` (préférences + items
récents) et `feedback`. La spec régénérée (`docs/api/openapi.json`,
584 KB) couvre désormais 146 endpoints (vs 138 en v1.0.0). Collection
Postman régénérée (183 KB, 27 dossiers).

#### Documentation conduite du changement (étendue de 33 → 280 lignes)

`docs/formation/conduite-du-changement.md` — réécriture complète
structurée en 10 sections : objectifs (5 cibles chiffrées), publics
(10 profils avec durée formation), dispositif (5 formats : salle,
cas pratiques, fiches rapides, assistance, support continu),
calendrier 4 phases sur 12 semaines, gestion de la résistance
(culturelle / organisationnelle / technique), boucle feedback v1.1,
métriques d'adoption (5 KPI hebdo avec cibles S4 et S12), rôles et
responsabilités, risques et mitigation, suite logique.

#### Documentation formation (4 nouveaux documents)

- **`docs/formation/quickstart-utilisateur.md`** — Guide de prise en
  main en 10 minutes, structuré en 10 sections : pré-requis,
  connexion, navigation, première action par rôle (4 cas : admission,
  médecin, infirmier, pharmacien), personnalisation, items récents,
  feedback, problèmes courants, règles d'or, aller plus loin.

- **`docs/formation/faq-utilisateurs.md`** — 27 Q/R organisées en 7
  thèmes : connexion et compte, patients et DPI, saisie et données,
  permissions et RBAC, performance et disponibilité, sécurité et
  confidentialité, boucle feedback v1.1.

- **`docs/formation/parcours-recette-par-role.md`** — Check-list de
  validation des compétences par rôle. 10 parcours (un par rôle),
  13-21 actions chacun, avec critère de réussite et temps estimé.
  Total : ~170 actions à valider. Inclut un template de fiche de
  signature formateur + utilisateur.

- **`docs/formation/fiches-rapides/`** — 10 fiches A4 (107-139 lignes
  chacune, 1146 lignes total), une par rôle :
  `fiche-admission.md`, `fiche-medecin.md`, `fiche-infirmier.md`,
  `fiche-sage-femme.md`, `fiche-pharmacien.md`, `fiche-laboratoire.md`,
  `fiche-radiologie.md`, `fiche-caissier.md`, `fiche-direction.md`,
  `fiche-administrateur.md`. Structure uniforme : connexion, 10
  actions essentielles, raccourcis clavier, problèmes/solutions,
  contacts utiles. Noms guinéens réalistes (Diallo, Camara,
  Bangoura, Cissé, Touré, Sylla, Condé) et terminologie médicale
  contextualisée (paracétamol, arteméther, CPoN, APGAR, NFS,
  sérologie VIH).

#### Documentation post-pilote (1 nouveau document)

- **`docs/post-pilot/EVOLUTIONS_POST_PILOTE.md`** — Roadmap dynamique
  v1.2+ alimentée par la boucle feedback. Méthodologie de
  priorisation (5 critères pondérés). 15 évolutions candidates
  organisées en 3 temps :
  - **v1.2** (3 mois) : impression PDF, i18n EN/FR, dashboard
    temps réel, recherche globale, mode hors-ligne PWA.
  - **v1.3** (6 mois) : app mobile Android, interopérabilité FHIR,
    planning RH v2, dashboard qualité avancé, notifications
    multicanal étendues.
  - **v2.0** (12+ mois) : data warehouse national, télémédecine,
    IA aide au diagnostic, stock multi-entrepôts, migration
    Kubernetes.
  - Backlog additionnel : 9 idées en attente (mode sombre complet,
    export CSV universel, recherche phonétique, calendrier hégirien,
    signature électronique, banque de sang, stérilisation, déchets
    médicaux, intégration DMP).

### Changed

- **`APP_VERSION`** : `1.0.0` → `1.1.0` dans `backend/app/main.py`.
- **OpenAPI tags** : 25 → 27 (ajout `user-profile`, `feedback`).
- **`backend/tests/test_openapi.py`** : `test_app_version_matches_v1_1`,
  `test_app_has_all_27_tags`.
- **`backend/tests/conftest.py`** : `expire_on_commit=False` sur
  `TestingSessionLocal` pour éviter les `DetachedInstanceError` dans
  les tests qui accèdent à un attribut après une requête.
- **`backend/app/modules/rbac/seed.py`** : 2 nouvelles permissions
  (`feedback.read`, `feedback.resolve`), module `feedback`.
- **README.md** : badge version v1.0.0 → v1.1.0, roadmap ✅ v1.1,
  🔜 v1.2, nouvelle section "Conduite du changement et formation".
- **`docs/api/openapi.json`** régénéré (545 KB → 584 KB).
- **`docs/api/guineecare.postman_collection.json`** régénéré
  (173 KB → 183 KB, 25 → 27 dossiers).

### Stats

- 276/276 tests backend pytest passent (240 + 36 nouveaux, 78s).
- 0 régression (tous les tests v1.0.0 toujours verts).
- Frontend build inchangé (253 KB initial bundle).
- OpenAPI spec : 146 endpoints, 102 paths, 27 tags, 145 routes
  protégées avec auto-injection 401/403/429/500 + HTTPBearer.
- Documentation : 16 nouveaux fichiers Markdown dans
  `docs/formation/` et `docs/post-pilot/` (~2300 lignes au total).

### Migration

Aucun breaking change. La migration Alembic `0015_user_profile` crée
3 nouvelles tables — exécutable sans interruption de service via :

```bash
cd backend
alembic upgrade head
```

Les anciens endpoints sont inchangés. Les nouvelles permissions
(`feedback.read`, `feedback.resolve`) sont seedées automatiquement
au prochain démarrage de l'application.

---

## [1.0.0] — 2026-06-21

### Added — Déploiement pilote CHU Donka

Cette release marque la mise en production de GuinéeCare Hospital Suite au CHU Donka (Conakry, Guinée). Elle ajoute tout le socle opérationnel nécessaire à un déploiement pilote robuste : fichier docker-compose production durci, configuration nginx TLS + headers de sécurité, scripts de déploiement/backup/restore, runbook complet, et pipeline CI de release automatique.

#### Stack Docker production durcie

- **`docker-compose.prod.yml`** — Override de la stack dev avec hardening :
  - **Utilisateur non-root** : backend tourne en `user: 1001:1001` (appuser, créé dans le Dockerfile).
  - **Read-only filesystem** : `read_only: true` sur backend / frontend / nginx, avec tmpfs pour `/tmp` et les caches nginx.
  - **Capabilities dropped** : `cap_drop: ALL` sur tous les services, avec `cap_add` minimal (CHOWN/SETUID/SETGID/NET_BIND_SERVICE pour nginx/frontend).
  - **No-new-privileges** : `security_opt: no-new-privileges:true` sur tous les services.
  - **Resource limits** : memory + cpus limités par service (backend 1G/2CPU, postgres 1G/1CPU, frontend 128M, nginx 256M, redis 96M).
  - **ENVIRONMENT=production** + **SEED_DEMO_DATA=false** (refusé au démarrage si true).
  - **Restart always** au lieu de `unless-stopped`.
  - **TRUSTED_PROXIES** pré-configuré pour les ranges Docker (10.x, 172.16.x, 192.168.x).
  - **Redis password-protected** avec `--maxmemory 64mb` et politique `allkeys-lru`.
  - **Backup quotidien** : boucle interne au conteneur `db-backup` à 02:00 UTC, rétention 14 jours, format `pg_dump -Fc`.

- **`backend/Dockerfile`** durci :
  - Python 3.12-slim (au lieu de 3.11).
  - Création de l'utilisateur `appuser` (UID 1001).
  - `COPY --chown=appuser:appuser` pour tous les fichiers applicatifs.
  - `USER appuser` avant `CMD`.
  - `HEALTHCHECK` intégré au Dockerfile (en plus de celui du compose).
  - `uvicorn --workers 2 --proxy-headers` (utilise 2 CPUs et truste X-Forwarded-* de nginx).
  - Variables d'env `PYTHONUNBUFFERED=1` + `PYTHONDONTWRITEBYTECODE=1`.

#### Configuration nginx production (TLS + headers)

- **`nginx.prod.conf`** — Configuration nginx reverse proxy production :
  - **TLS 1.2/1.3 uniquement** (Mozilla intermediate, May 2024) — TLS 1.0/1.1 interdits.
  - **Redirect HTTP → HTTPS** (301 permanent) sur `:80`.
  - **HSTS** 1 an `includeSubDomains` (preload-ready après soumission manuelle).
  - **CSP strict** : `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'`.
  - **Permissions-Policy** : camera/microphone/geolocation/interest-cohort désactivés.
  - **COOP/CORP** `same-origin` (isolation cross-origin).
  - **Headers Owasp** : X-Content-Type-Options nosniff, X-Frame-Options DENY, X-XSS-Protection, Referrer-Policy strict-origin-when-cross-origin.
  - **Rate limiting** : `auth_limit` (5 req/min sur /auth/login), `login_burst` (burst 2), `api_limit` (120 req/min sur /api/).
  - **`client_max_body_size 10m`** (cap upload).
  - **IP allowlist** sur `/metrics` (private ranges uniquement), `/docs`, `/redoc`, `/api/v1/openapi.json` (admin office).
  - **Gzip** + `tcp_nopush` + `tcp_nodelay` + `keepalive 65s`.
  - **Logging format** custom avec timing (rt, uct, uht, urt).
  - **Page d'erreur 502/503/504** custom HTML (ne leak pas d'info interne).
  - **`server_tokens off`** (cache la version nginx).

#### Templates d'environnement

- **`.env.production.template`** — Template complet pour la production :
  - Toutes les variables requises (ENVIRONMENT, AUTH_SECRET, DB_PASSWORD, CORS_ORIGINS, TRUSTED_PROXIES, METRICS_TOKEN, BOOTSTRAP_TOKEN, REDIS_PASSWORD, PUBLIC_URL, BACKUP_RETENTION_DAYS).
  - Secrets avec placeholders `CHANGE_ME_openssl_rand_hex_*` (visuellement reconnaissables).
  - `SEED_DEMO_DATA=false` (hardcoded).
  - `CORS_ORIGINS=["https://chu-donka.guineecare.gn"]` (strict allowlist).
  - `TRUSTED_PROXIES=10.0.0.0/8,172.16.0.0/12,192.168.0.0/16` (Docker bridge).
  - Instructions inline pour générer chaque secret avec `openssl rand`.

- **`.env.example`** — Template pour dev/local (SQLite, AUTH_SECRET warning, CORS permissif, SEED_DEMO_DATA=true).

#### Scripts opérationnels

- **`scripts/deploy.sh`** — Déploiement production complet :
  - Pre-flight checks : présence `.env.production`, toutes les vars requises, aucune valeur `CHANGE_ME_*` restante, ENVIRONMENT=production, SEED_DEMO_DATA=false, certificats TLS présents, Docker installé, espace disque ≥ 5 GB, RAM disponible.
  - Mode `--check-only` : dry-run validation seulement.
  - Mode `--no-build` : réutilisation des images existantes.
  - Build des images, pull postgres/redis/nginx, start postgres + wait healthy, run Alembic migrations, start remaining services + wait backend healthy.
  - Bootstrap check : détecte si un SUPER_ADMIN existe déjà, affiche les instructions CLI/HTTP sinon.
  - Smoke tests HTTPS `/health`.
  - Affichage du status final + next steps.

- **`scripts/backup.sh`** — Wrapper backup manuel :
  - `--list` : liste les backups existants.
  - `--verify` : valide le dernier backup avec `pg_restore --list` + check taille ≥ 1 KB.
  - mode par défaut : backup immédiat vers `backups/guineecare_<ts>.dump`.

- **`scripts/restore.sh`** — Restauration disaster recovery :
  - `--latest` : restore le dernier backup du conteneur `db-backup`.
  - `--host <file>` : restore depuis un fichier sur l'hôte (via stdin).
  - Confirmation interactive (`CONFIRM`) avant DROP.
  - `pg_restore --clean --if-exists --no-owner --no-privileges` + Alembic upgrade head + restart backend.

- **`scripts/seed-pilot.sh`** — Création du premier super-admin CHU Donka :
  - Génère un mot de passe fort aléatoire (16 chars, `openssl rand`).
  - Idempotent (skip si l'email existe déjà).
  - Affiche les credentials dans un encadré pour distribution sécurisée.

#### Documentation

- **`docs/deploiement/RUNBOOK_CHU_DONKA.md`** — Runbook opérationnel complet (~600 lignes) :
  - **Architecture cible** : diagramme ASCII, specs serveur minimales (CPU/RAM/disk/OS).
  - **Préparation du serveur** : installation Docker + UFW + clone dépôt + DNS + certificats Let's Encrypt (avec cron de renouvellement).
  - **Configuration des secrets** : génération `openssl rand`, validation `--check-only`.
  - **Déploiement initial** : `deploy.sh`, bootstrap super-admin (CLI + HTTP), vérification post-déploiement (table de 7 checks).
  - **Opérations courantes** : status, logs (JSON structured), restart, mise à jour, backup manuel, restore, rotation des secrets (AUTH_SECRET, METRICS_TOKEN).
  - **Monitoring** : health checks, métriques clés (P95, 5xx, DB conns, disk), config Prometheus scrape, requêtes Loki.
  - **Procédures d'incident** : P0 site down, P1 dégradation lente, P1 fuite de secret, P2 perte de données.
  - **Maintenance planifiée** : fenêtres quotidienne/hebdo/mensuelle + communication.
  - **Contacts** : rôles à renseigner.
  - **Checklist go-live** : 18 items (DNS, TLS, secrets, deploy, backup test, monitoring, formation, rollback).
  - **Rollback** : procédure git checkout + redeploy + restore backup.

#### CI/CD — 1 nouveau workflow

- **`.github/workflows/deploy-release.yml`** — Pipeline de release :
  - Déclenché sur tag `v*` ou `workflow_dispatch`.
  - Matrix build : `guineecare-backend` + `guineecare-frontend`.
  - Push vers GHCR (`ghcr.io/skaba89/guineecare-backend:v1.0.0`, `:latest`).
  - Buildx avec cache GHA (accélération des builds ultérieurs).
  - Build args `VITE_API_BASE_URL=https://chu-donka.guineecare.gn/api/v1`.
  - Job `release-notes` : extrait l'entrée CHANGELOG correspondante au tag et crée une GitHub Release (avec `softprops/action-gh-release`), pré-release si tag contient `-rc` ou `-beta`.

#### Tests — 25 nouveaux

- `backend/tests/test_deployment_artifacts.py` :
  - `test_docker_compose_yml_valid`, `test_docker_compose_prod_yml_valid`, `test_docker_compose_prod_resources_enforced`, `test_docker_compose_prod_nginx_uses_tls_volume` (4 tests compose).
  - `test_nginx_prod_conf_has_tls`, `test_nginx_prod_conf_has_security_headers`, `test_nginx_prod_conf_http_redirects_to_https`, `test_nginx_prod_conf_metrics_ip_restricted`, `test_nginx_prod_conf_auth_rate_limited`, `test_nginx_prod_conf_client_max_body_size` (6 tests nginx).
  - `test_env_production_template_has_all_required_vars`, `test_env_production_template_has_placeholders`, `test_env_production_template_forbids_seed_demo_data`, `test_env_example_has_all_required_vars` (4 tests env).
  - `test_gitignore_excludes_secrets` (1 test gitignore).
  - `test_scripts_exist_and_are_executable`, `test_deploy_script_has_check_only_mode`, `test_deploy_script_validates_required_env_vars`, `test_backup_script_has_verify_mode`, `test_restore_script_has_confirm_prompt` (5 tests scripts).
  - `test_runbook_exists`, `test_runbook_has_required_sections`, `test_runbook_has_go_live_checklist` (3 tests runbook).
  - `test_deploy_release_workflow_exists`, `test_deploy_release_workflow_pushes_to_ghcr` (2 tests CI).

### Changed

- `backend/app/main.py` — `APP_VERSION` 0.10.0 → 1.0.0.
- `backend/tests/test_openapi.py` — `test_app_version_matches_v0_10` attend désormais `1.0.0`.
- `docs/api/openapi.json` + `docs/api/guineecare.postman_collection.json` — régénérés avec version 1.0.0.
- `README.md` — Badge version v1.0.0, roadmap v1.0 ✅ + v1.1 🔜, nouvelle section "Déploiement production (v1.0.0+)" avec commande de déploiement, table hardening dev vs prod (14 lignes), table scripts opérationnels (8 lignes), description CI release, lien runbook.
- `backend/Dockerfile` — Refonte complète (Python 3.12, appuser non-root, HEALTHCHECK, workers=2, proxy-headers).
- `.gitignore` — Ajout de `.env`, `.env.local`, `.env.production`, `.env.*.local`, `*.pem`, `*.key`, `tls/`, `certs/`, `*.dump`, `*.sql.gz`, `backups/`, `newman-*.html`, `newman-*.xml`.

### Stats

- **240/240** tests backend pytest passent (215 + 25 nouveaux, 65s).
- **0** régression sur les tests existants.
- **1** nouveau fichier docker-compose production (`docker-compose.prod.yml`).
- **1** nouvelle configuration nginx production (`nginx.prod.conf`).
- **2** templates d'environnement (`.env.example`, `.env.production.template`).
- **4** scripts opérationnels (`deploy.sh`, `backup.sh`, `restore.sh`, `seed-pilot.sh`).
- **1** runbook complet (~600 lignes, 11 sections).
- **1** nouveau workflow CI (`deploy-release.yml`).
- **1** Dockerfile backend durci (non-root, healthcheck, workers).
- Bundle frontend inchangé (253 KB initial).

### Migration

Pour préparer le déploiement CHU Donka :

1. **Préparer le serveur** selon la section 2 du runbook (Ubuntu 22.04+, Docker, UFW, DNS).
2. **Générer les secrets** : `openssl rand -hex 48` pour AUTH_SECRET, `openssl rand -hex 32` pour les autres.
3. **Obtenir les certificats TLS** : `certbot certonly --standalone -d chu-donka.guineecare.gn`.
4. **Créer `.env.production`** à partir de `.env.production.template`.
5. **Valider** : `bash scripts/deploy.sh --check-only`.
6. **Déployer** : `bash scripts/deploy.sh`.
7. **Bootstrap super-admin** : via CLI `python -m app.cli create-superuser` ou HTTP `POST /users/bootstrap`.
8. **Vérifier** : suivre la checklist go-live (section 10 du runbook).

---

## [0.10.0] — 2026-06-21

### Added — Documentation OpenAPI complète + collection Postman

Cette release fait passer la documentation API de GuinéeCare au niveau d'une API publique prête pour l'intégration partenaires (Ministère Santé, éditeurs tiers, intégrateurs régionaux). L'ensemble de la surface API (138 opérations sur 98 chemins, 25 tags thématiques) est désormais documenté avec exemples, codes d'erreur standardisés, schéma de sécurité JWT Bearer, et export Postman + OpenAPI 3.1 statiques.

#### Enrichissement OpenAPI 3.1

- **Métadonnées API** : `title`, `summary`, `description` (2084 caractères, format Markdown avec conventions, codes d'erreur, liens doc), `contact`, `license_info`, `servers` (3 environnements : courant, localhost, production CHU Donka).
- **25 tags** déclarés avec description (auth, users, rbac, facilities, departments, patients, admissions, emergency, hospitalization, clinical, maternity, pharmacy, laboratory, imaging, surgery, billing, personnel, quality, reporting, audit, activity, notifications, health, metrics, system).
- **Enrichissement automatique** via `custom_openapi()` dans `main.py` :
  - Injection des réponses standard `401`, `403`, `429`, `500` sur les 137 routes protégées (exclut 6 routes publiques : `/api/v1`, `/auth/login`, `/auth/refresh`, `/health`, `/health/live`, `/health/ready`, `/metrics`).
  - Injection de la réponse `422` sur les routes avec `requestBody`.
  - Attachment automatique du security scheme `HTTPBearer` sur les routes protégées (bouton 🔓 Authorize de Swagger UI fonctionnel).
  - Schémas `HTTPValidationError` + `ValidationError` garantis présents dans `components.schemas`.
  - Cache de la spec enrichie pour éviter la régénération à chaque appel.
- **Routes racine** : `GET /api/v1` désormais taguée `system` avec `summary` explicite.
- **Endpoints docs** : `openapi_url=/api/v1/openapi.json`, `docs_url=/docs` (Swagger), `redoc_url=/redoc` (ReDoc) déclarés explicitement.

#### Artifacts générés et versionnés

- `docs/api/openapi.json` (545 KB) — Spécification OpenAPI 3.1 statique, machine-lisible, committée dans Git pour audit hors-ligne.
- `docs/api/guineecare.postman_collection.json` (173 KB) — Collection Postman v2.1 avec 138 endpoints organisés en 25 dossiers, headers `Content-Type` et `Authorization: Bearer {{access_token}}` pré-déclarés, query params et body examples extraits de l'OpenAPI, script de test Postman qui capture automatiquement `access_token` et `refresh_token` après `/auth/login` ou `/auth/refresh`.
- `docs/api/guineecare-local.postman_environment.json` (1 KB) — Environnement Postman pour dev local : `host`, `base_url`, variables `access_token` / `refresh_token` (auto-remplies), et credentials de test (admin/doctor).

#### Script de génération

- `scripts/generate_openapi_artifacts.py` — Régénère les 3 artifacts en une commande. À exécuter après toute modification de routes. Override explicite de `DATABASE_URL`, `AUTH_SECRET`, `ENVIRONMENT` (résistance aux env vars shell polluantes).

#### Documentation

- `docs/api/OPENAPI_GUIDE.md` — Guide complet : vue d'ensemble, endpoints exposés, métadonnées, enrichissement automatique, génération statique, workflow de mise à jour, CI drift detection, validation tests, consultation interactive (Swagger/ReDoc/Postman/Insomnia), bonnes pratiques.
- `docs/api/POSTMAN_GUIDE.md` — Guide Postman : import, variables d'environnement, authentification automatique (script de test intégré), scénarios de démarrage rapide (login SUPER_ADMIN, cross-tenant refusé), structure de la collection (25 dossiers), Runner Postman, Newman CLI, régénération, astuces.

#### Tests — 19 nouveaux

- `backend/tests/test_openapi.py` :
  - `test_openapi_version_is_3_1`, `test_app_version_matches_v0_10`, `test_app_has_description`, `test_app_has_contact_and_license`, `test_app_has_servers`, `test_app_has_security_scheme`, `test_app_has_all_25_tags` (7 tests structure).
  - `test_every_operation_has_tag`, `test_every_operation_has_summary` (2 tests couverture).
  - `test_protected_operations_have_401_response`, `test_protected_operations_have_403_response`, `test_protected_operations_have_429_response`, `test_protected_operations_have_500_response`, `test_protected_operations_have_bearer_security` (5 tests enrichissement).
  - `test_body_operations_have_422_response` (1 test body).
  - `test_api_root_is_tagged_system`, `test_public_operations_have_no_security` (2 tests edge cases).
  - `test_committed_openapi_json_in_sync` — drift detection runtime vs `docs/api/openapi.json` committé.
  - `test_committed_postman_collection_exists` — sanity check collection.

#### CI/CD — 1 nouveau workflow

- `.github/workflows/openapi-check.yml` — Déclenché sur push/PR touchant `backend/app/**`, `docs/api/**`, ou le script de génération.
  - Job `drift-check` : régénère les artifacts, compare avec `git diff --exit-code` sur `openapi.json` et `guineecare.postman_collection.json`. Échoue si drift, avec message d'erreur explicite rappelant la commande à exécuter.
  - Étape finale : exécute `pytest tests/test_openapi.py` pour valider la structure (tags, summaries, security, responses).

### Changed

- `backend/app/main.py` — Refonte complète du bloc `FastAPI(...)` :
  - `title` → `GuinéeCare Hospital Suite API` (avec accent).
  - Ajout `summary`, `description`, `openapi_tags`, `contact`, `license_info`, `servers`, `openapi_url`, `docs_url`, `redoc_url`.
  - `version` 0.9.0 → 0.10.0 (constante `APP_VERSION`).
  - `set_app_info(version=APP_VERSION)` au lieu de littéral `"0.9.0"`.
  - `GET /api/v1` décoré avec `tags=["system"]` et `summary`.
  - Ajout du bloc enrichment OpenAPI (~150 lignes) + override `app.openapi = custom_openapi`.
- `README.md` — Badge version v0.9.0 → v0.10.0, roadmap `🔜 v0.10` → `✅ v0.10`, nouvelle section "Documentation API" avec badges/links vers `/docs`, `/redoc`, `openapi.json`, et les guides.

### Stats

- **215/215** tests backend pytest passent (196 + 19 nouveaux, 64s).
- **0** régression sur les tests existants.
- **138** opérations OpenAPI documentées (98 paths).
- **25** tags thématiques.
- **137** routes protégées avec 401/403/429/500 + Bearer security.
- **6** routes publiques exemptées d'enrichissement.
- **3** artifacts générés et versionnés (`openapi.json` 545 KB + Postman 173 KB + env 1 KB).
- **2** nouveaux guides Markdown (~400 lignes au total).
- **1** nouveau workflow CI (`openapi-check.yml`).
- Bundle frontend inchangé (253 KB initial).

### Migration

Aucune action requise pour les développeurs existants. Les nouveaux artifacts sont dans `docs/api/` et les guides associés dans le même dossier. Pour régénérer après une modification de routes :

```bash
python scripts/generate_openapi_artifacts.py
git add docs/api/
git commit -m "docs(api): regenerate openapi + postman"
```

Le CI `openapi-check.yml` détectera automatiquement tout drift oublié.

---

## [0.9.0] — 2026-06-21

### Added — Hardening LOW restant + tests de charge Locust

Cette release clôt le périmètre OWASP Top 10 (tous les findings LOW acceptés en v0.8 sont désormais corrigés) et ajoute une infrastructure complète de tests de charge.

#### Hardening sécurité (5 findings LOW → 0)

- **A05-001 — `TRUSTED_PROXIES`** (`backend/app/core/config.py`, `core/limiter.py`, `audit/service.py`, `auth/routes.py`) :
  - Nouvelle fonction `is_ip_trusted(remote_addr, trusted_proxies)` qui valide qu'une IP est dans un CIDR allowlisté avant de trust `X-Forwarded-For`.
  - `get_client_ip()` n'honore plus `X-Forwarded-For` que si le peer direct est dans `TRUSTED_PROXIES`. En l'absence de proxy configuré, on utilise le raw `remote_addr` — empêche le spoofing IP quand le backend est exposé directement.
  - Même logique appliquée à `_extract_request_meta()` dans `auth/routes.py` et `audit/service.py` pour cohérence.
  - Variable d'environnement : `TRUSTED_PROXIES=10.0.0.0/8,172.16.0.0/12`.

- **A05-005 — `METRICS_TOKEN`** (`backend/app/modules/observability/routes.py`) :
  - `/metrics` requiert désormais `Authorization: Bearer <METRICS_TOKEN>` quand la variable d'env est set. Si vide (défaut), `/metrics` reste ouvert pour le dev/local.
  - Comparaison constant-time via `hmac.compare_digest`.
  - Codes : 401 si header manquant, 403 si token invalide, 200 si OK.

- **A05-004 — CLI bootstrap + `BOOTSTRAP_TOKEN`** (`backend/app/cli.py`, `modules/users/routes.py`) :
  - Nouveau CLI `python -m app.cli create-superuser --email <e> --first-name <f> --last-name <l> [--password <p>] [--facility-id <uuid>] [--force]`. Password prompt interactif si omis. Validation de la politique de mot de passe (12+ chars, complexité). Refuse la création si la table users est non-vide sans `--force`.
  - Endpoint HTTP `POST /users/bootstrap` désormais gated par `X-Bootstrap-Token` en non-local. Si `BOOTSTRAP_TOKEN` est vide en non-local, l'endpoint est désactivé (403) — les opérateurs DOIVENT utiliser le CLI.
  - En local, l'endpoint reste ouvert pour le dev (chicken-and-egg).

- **A05-002 — Refus `SEED_DEMO_DATA` en prod** (`backend/app/main.py`) :
  - Si `ENVIRONMENT ∉ {local, test, dev}` et `SEED_DEMO_DATA=true`, le seed est skipé et un message ERROR est loggé. Empêche la création accidentelle de comptes `admin123` en production.

- **A07 — jti blacklist pour JWT** (`backend/app/core/security.py`, `modules/auth/models.py`, `modules/auth/jti.py`, `modules/auth/dependencies.py`, `modules/auth/routes.py`, `modules/auth/schemas.py`, migration `0014_jti_blacklist`) :
  - Chaque access_token JWT inclut désormais un `jti` (UUID unique) en plus de `sub`, `exp`, `iat`.
  - Nouvelle table `revoked_jtis` (jti PK, user_id, reason, revoked_at, expires_at). Index sur `expires_at` pour le prune.
  - Service `app.modules.auth.jti` : `revoke_jti()`, `is_jti_revoked()`, `revoke_user_jtis()` (stub), `prune_expired()`.
  - `get_current_user()` vérifie la blacklist : si le jti est présent → 401 "Jeton révoqué".
  - `POST /auth/logout` accepte désormais un `access_token` optionnel dans le body. Si fourni, le jti est révoqué immédiatement (invalidation avant l'expiry naturel de 60 min). Sans `access_token`, comportement inchangé (seul le refresh token est révoqué).
  - Fail-open en cas d'erreur DB sur la blacklist check (pour éviter de locker tous les users si la DB est down) — le token reste valide jusqu'à expiry naturel.

- **A06 — pip-audit + npm-audit fail-mode** (`.github/workflows/security-scan.yml`) :
  - Les jobs `pip-audit` et `npm-audit` passent de warn-only à fail. Les vulnérabilities HIGH/CRITICAL cassent désormais le build. Les maintainers doivent mettre à jour les packages affectés.

#### Tests de charge Locust

- **Nouveau dossier `load_tests/`** avec :
  - `locustfile.py` — 2 scénarios : `GuineeCareUser` (browse authentifié, default) et `GuineeCareLoginStorm` (login fresh à chaque itération, `weight=0`).
  - `README.md` — guide complet : prérequis, scénarios, exemples headless, métriques attendues, interprétation.
  - Scénario `GuineeCareUser` : login → browse patients (paginated) → détail patient → reporting dashboard → notifications → unread-count → users → audit logs → /auth/me → /health/ready → logout (avec révocation jti). Think time 1.0-3.5s.
- **Workflow CI `load-test.yml`** (nightly 03:00 UTC + workflow_dispatch) :
  - Démarre un backend SQLite seeded sur runner GitHub Actions.
  - Lance Locust headless : 20 users, 5/s spawn, 30s.
  - Upload le rapport HTML + CSV en artifact (rétention 14 jours).
  - Publie les stats dans le job summary GitHub.

### Added — Tests
- **`backend/tests/test_security_v09.py`** : 35 nouveaux tests couvrant tous les hardening ci-dessus.
  - `TestTrustedProxiesParsing` (4) — parsing de TRUSTED_PROXIES
  - `TestIsIpTrusted` (5) — validation IP/CIDR
  - `TestLimiterHonorsTrustedProxies` (3) — get_client_ip behavior
  - `TestMetricsToken` (5) — /metrics auth
  - `TestBootstrapToken` (5) — /users/bootstrap gate
  - `TestCliCreateSuperuser` (3) — CLI create-superuser
  - `TestSeedDemoDataGuard` (1) — SEED_DEMO_DATA refused in prod
  - `TestJtiBlacklist` (6) — service revoke_jti/is_jti_revoked/prune_expired
  - `TestJtiBlacklistIntegration` (3) — end-to-end: revoked jti rejects request, logout revokes jti, logout without access_token keeps jti valid
- **Total** : 196 tests backend (161 + 35) + 16 tests Playwright (inchangés).

### Added — Migration
- **Alembic 0014** : table `revoked_jtis` (jti PK, user_id FK, reason, revoked_at, expires_at) avec index sur `expires_at`.

### Added — CLI
- **`backend/app/cli.py`** : nouveau module CLI avec `create-superuser` command. Utilisable via `python -m app.cli create-superuser`. Documenté dans README.

### Added — Configuration
- Nouvelles variables d'environnement :
  - `TRUSTED_PROXIES` — comma-separated list of IPs/CIDRs (default: empty)
  - `METRICS_TOKEN` — bearer token for /metrics (default: empty = open)
  - `BOOTSTRAP_TOKEN` — bootstrap token for /users/bootstrap in non-local (default: empty = disabled)

### Updated — Documentation
- **`README.md`** : roadmap v0.9 marquée ✅, ajout section "Hardening v0.9" avec tableau récapitulatif des variables d'env.
- **`docs/security/AUDIT_V0.8.0.md`** : note de mise à jour en tête — tous les findings LOW sont désormais corrigés en v0.9.0.

### Statistics
- 196/196 tests backend pytest (63.5 s)
- 16/16 tests Playwright (inchangés)
- 0/0 findings Bandit HIGH+ sur `backend/app/` (inchangé)
- 21/21 findings OWASP Top 10 corrigés (13 en v0.8 + 5 en v0.9 + 3 acceptés en LOW désormais couverts)
- 2 nouveaux workflows CI : `security-scan.yml` (mis à jour fail-mode), `load-test.yml` (nightly Locust)
- 1 nouvelle migration Alembic (0014)
- 1 nouveau module backend : `auth.jti` (service), `app.cli` (CLI)
- 1 nouveau dossier `load_tests/` avec locustfile + README
- Bundle frontend : 253 KB initial (inchangé)

---

## [0.8.0] — 2026-06-20

### Added — Audit sécurité OWASP Top 10 + hardening
- **Rapport d'audit complet** : `docs/security/AUDIT_V0.8.0.md` — 21 findings OWASP Top 10 (2 CRITICAL, 2 HIGH, 9 MEDIUM, 8 LOW), 13 corrigés en v0.8.0, 5 acceptés avec plan de mitigation.
- **SAST Bandit** intégré au venv (0 findings sur `backend/app/`).
- **Workflow CI security-scan.yml** (3 jobs) :
  - `bandit-sast` — SAST Python, fail sur HIGH severity
  - `pip-audit` — scan dépendances backend contre OSV (warn-only en v0.8, fail en v0.9)
  - `npm-audit` — scan dépendances frontend (warn-only en v0.8, fail en v0.9)

### Fixed — CRITICAL (2 findings)

#### A02-001 — Fuite de `password_hash` via /users endpoints
- **Avant** : `GET /users`, `POST /users`, `PUT /users/{id}`, `POST /users/bootstrap` retournaient l'objet User ORM brut, exposant `password_hash` (bcrypt). Un ADMIN pouvait moissonner tous les hashes de sa facility.
- **Après** : Ajout de `User.to_read_dict()` qui exclut `password_hash`. Tous les endpoints /users retournent ce dict sécurisé.
- **Tests** : `TestPasswordHashNotExposed` (4 tests).

#### A01-001 — ADMIN facility-scoped pouvait muter le RBAC global
- **Avant** : `POST /rbac/roles`, `POST /rbac/permissions`, `POST /rbac/role-permissions` étaient accessibles à ADMIN (facility-scoped). Un ADMIN de facility A pouvait créer des rôles/permissions globaux affectant toutes les facilities.
- **Après** : Restriction à `require_role("SUPER_ADMIN")` uniquement pour les 3 endpoints de mutation. Les endpoints GET restent accessibles à ADMIN.
- **Tests** : `TestRBACSuperAdminOnly` (4 tests).

### Fixed — HIGH (2 findings)

#### A01-002 — /activity leakait l'activité cross-facility à ADMIN
- **Avant** : `GET /activity` était accessible à ADMIN mais `ActivityEntry` n'a pas de `facility_id` — la table est globale.
- **Après** : Restriction à `require_role("SUPER_ADMIN")` uniquement.

#### A09-001/002/003 — Mutations users/facilities/departments/RBAC non auditées
- **Avant** : Un ADMIN pouvait changer le mot de passe de n'importe quel utilisateur de sa facility sans laisser de trace forensic.
- **Après** : `audit_log()` appelé sur toutes les mutations :
  - `user.create`, `user.update`, `user.bootstrap`
  - `facility.create`, `facility.update`
  - `department.create`
  - `rbac.role.create`, `rbac.permission.create`, `rbac.role_permission.assign`
  - Pour les changements de mot de passe : payload `{"password": "[REDACTED]"}` — jamais le plaintext.
- **Tests** : `TestAuditLogOnMutations` (6 tests).

### Fixed — MEDIUM (9 findings)

#### A01-003 — /notifications/send sans contrôle tenant sur le destinataire
- **Avant** : ADMIN facility-scoped pouvait envoyer une notification (in_app + email si SMTP configuré) à n'importe quel utilisateur cross-facility → phishing.
- **Après** : `enforce_facility_access(current_user, recipient.facility_id)` après fetch du destinataire.

#### A04-001 — Account lockout après échecs de login
- **Avant** : Aucun verrouillage par compte — brute force possible en changeant d'IP.
- **Après** : Migration 0013 — colonnes `users.failed_login_count` + `users.locked_until`. Après 5 échecs, verrouillage 15 min. Réponse 423 Locked. Compteur reset sur login réussi.
- **Tests** : `TestAccountLockout` (2 tests).

#### A04-002 — Politique de mot de passe trop faible
- **Avant** : `min_length=8` seulement. Seeds avec `admin123`, `doctor123`.
- **Après** : Validation Pydantic exigeant ≥12 chars, ≥1 majuscule, ≥1 minuscule, ≥1 chiffre, ≥1 caractère spécial.
- **Tests** : `TestPasswordPolicy` (5 tests).

#### A04-003 — /auth/refresh non rate-limité
- **Avant** : Seul `/auth/login` était rate-limité. `/auth/refresh` ouvert → DoS + audit-log flooding.
- **Après** : `@_REFRESH_LIMIT = limiter.limit("30/minute")` en prod/staging. Audit log ajouté sur tous les échecs de refresh (unknown_token, revoked, expired, user_inactive).

#### A05-003 — `AUTH_SECRET` vide accepté en non-local
- **Avant** : `validate_settings()` levait `RuntimeError` mais `main.py` catchait et continuait → JWTs signés avec secret vide en prod.
- **Après** : `validate_settings()` appelle `sys.exit(1)` en non-local si `AUTH_SECRET` est vide. Hard-fail, pas de continuité.
- **Tests** : `TestAuthSecretValidation` (3 tests).

### Risques acceptés (LOW — reportés en v0.9)
- **A05-001** — `X-Forwarded-For` trusted sans validation → plan : `TRUSTED_PROXIES` en v0.9
- **A05-002** — Seeds avec mots de passe faibles → plan : refuser seed en prod en v0.9
- **A05-004** — `POST /users/bootstrap` non authentifié → plan : script CLI en v0.9
- **A05-005** — `/metrics` non authentifié → plan : `METRICS_TOKEN` en v0.9
- **A01-004/005** — Pattern fetch-then-check (404 vs 403 oracle) → plan : `tenant_query` uniforme en v0.9

### Added — Tests
- **`backend/tests/test_security_hardening.py`** : 26 nouveaux tests couvrant tous les fixes ci-dessus.
- **Total** : 161 tests backend (135 + 26) + 16 tests Playwright (inchangés).

### Added — Migration
- **Alembic 0013** : `users.failed_login_count` (int, default 0) + `users.locked_until` (datetime, nullable).

### Statistics
- 161/161 tests backend pytest (59.1 s)
- 16/16 tests Playwright (inchangés)
- 0/0 findings Bandit HIGH+ sur `backend/app/`
- 13/21 findings OWASP corrigés (2 CRITICAL + 2 HIGH + 9 MEDIUM)
- 5/21 findings OWASP acceptés en LOW (plan de mitigation documenté)
- 1 nouveau workflow CI : `security-scan.yml` (3 jobs : Bandit SAST + pip-audit + npm-audit)
- 1 nouvelle migration Alembic (0013)
- 1 nouveau rapport d'audit : `docs/security/AUDIT_V0.8.0.md`

---

## [0.7.0] — 2026-06-20

### Added — Module notifications (multicanal)
- **Migration Alembic 0012** : table `notifications` (recipient_id, sender_id, facility_id, category, priority, title, body, action_url, channels CSV, in_app/email/sms delivered flags, read_at, dismissed_at, resource_type, resource_id).
- **Service `notify()`** (`app/modules/notifications/service.py`) : helper à appeler depuis n'importe quelle route. Jamais bloquant — les échecs d'envoi sont enregistrés sur la ligne mais ne lèvent jamais d'exception.
- **3 canaux pluggables** : `ConsoleChannel` (toujours actif pour in_app), `EmailChannel` (SMTP — activé quand `SMTP_HOST` est set), `SmsChannel` (Twilio — activé quand `TWILIO_ACCOUNT_SID` est set). Aucune dépendance externe supplémentaire (smtplib + lazy import de twilio).
- **Routes** :
  - `GET /notifications` — liste paginée des notifications de l'utilisateur courant (filtres category, unread_only).
  - `GET /notifications/unread-count` — compteur pour badge d'en-tête.
  - `PATCH /notifications/{id}/read` — marquer comme lu.
  - `POST /notifications/mark-all-read` — tout marquer comme lu.
  - `DELETE /notifications/{id}` — supprimer (soft-delete via `dismissed_at`).
  - `POST /notifications/send` — admin-only (permission `notification.send`) pour envoyer à un utilisateur spécifique. Audit log automatique.
- **Permission RBAC** : `notification.send` ajoutée au seed (réservée SUPER_ADMIN/ADMIN via bypass).
- **Page frontend `/notifications`** : liste paginée avec filtres (catégorie, non lues seulement), badges de priorité colorés, icônes par catégorie, boutons marquer-comme-lu/supprimer, "tout marquer comme lu", infobulles sur l'état de livraison email/SMS.
- **Sidebar** : entrée "Notifications" ajoutée en haut de la section SOINS (visible pour tous les utilisateurs authentifiés — c'est leur boîte de réception personnelle).

### Added — Observabilité (Prometheus + health checks + logging structuré)
- **`GET /health/live`** : liveness probe — retourne 200 immédiatement si le process est vivant. Pour Kubernetes livenessProbe.
- **`GET /health/ready`** : readiness probe — ping DB (`SELECT 1`), retourne 200 si OK ou 503 si DB down. Pour Kubernetes readinessProbe.
- **`GET /metrics`** : exposition Prometheus text format (v0.0.4). Métriques :
  - `http_requests_total{method, path, status}` — counter
  - `http_request_duration_seconds{method, path, status}` — histogram (11 buckets de 5ms à 10s)
  - `http_requests_in_flight` — gauge
  - `app_info{version, environment}` — gauge constante
- **Middleware `MetricsMiddleware`** : instrumente chaque requête HTTP. Utilise le path template (ex. `/patients/{id}`) plutôt que le path brut pour éviter l'explosion de cardinalité des labels.
- **Logging structuré** : `JsonFormatter` (prod/staging) ou `PrettyFormatter` (dev/test) configuré au démarrage via `configure_logging(environment=...)`. Aucune dépendance externe (pas de structlog ni python-json-logger) — utilise la stdlib `logging` uniquement.
- **Endpoints sans auth** : `/health`, `/health/live`, `/health/ready`, `/metrics` ne nécessitent pas de JWT — par convention Kubernetes/Prometheus. En production, restreindre `/metrics` au niveau ingress (IP Prometheus uniquement).

### Added — Tests
- **`backend/tests/test_notifications.py`** : 24 tests (service notify + mark_read + dismiss + mark_all_read + HTTP list/filter/unread-count/mark-read/dismiss + admin send + RBAC + audit).
- **`backend/tests/test_observability.py`** : 12 tests (health live/ready, 503 on DB failure, metrics format/content/in-flight gauge, no-auth).
- **`frontend/tests/e2e/guineecare.spec.ts`** : 2 nouveaux tests Playwright (page /notifications accessible SUPER_ADMIN + DOCTOR).
- **Total** : 135 tests backend (99 + 36) + 16 tests Playwright (14 + 2).

### Fixed
- **`run_playwright.sh`** : `SEED_DEMO_DATA=false` → `true` (sinon le compte admin@guineecare.com n'existe pas et le check de login échoue).
- **`main.py`** : version FastAPI app mise à jour 0.1.0 → 0.7.0 (cohérence avec le tag git).

### Statistics
- 135/135 tests backend pytest (45.9 s)
- 16/16 tests Playwright UI (60 s, 1 flaky sur retry)
- 31/31 tests E2E API admin pages (inchangés)
- Bundle initial : 253 KB (gzip 80 KB) — inchangé (NotificationsPage chunké à 9.78 KB)
- 3 nouveaux modules backend : `notifications` (models + service + routes + schemas), `observability` (metrics + logging + middleware + routes)
- 1 nouvelle migration Alembic (0012)
- 1 nouvelle page frontend (NotificationsPage) + 1 nouvelle permission RBAC (notification.send)

---

## [0.6.0] — 2026-06-20

### Added — Refresh token + révocation JWT (sécurité)
- **`POST /auth/refresh`** : échange un refresh token valide contre un nouveau pair (access + refresh). Rotation automatique : l'ancien refresh token est révoqué immédiatement après usage.
- **`POST /auth/logout`** : révoque explicitement un refresh token (le `access_token` reste valide jusqu'à expiration, ~60 min).
- **Migration Alembic 0011** : table `refresh_tokens` (id, user_id, token_hash SHA-256, expires_at, revoked_at, replaced_by_id, created_ip, created_user_agent).
- **Sécurité** : le refresh token est stocké haché (SHA-256) en base — jamais en clair. Durée de vie : 30 jours.
- **Frontend** : `api.ts` gère automatiquement le refresh sur 401 (retry une fois avec un nouveau access token). Déduplication des refresh parallèles via `refreshPromise` partagé.
- **Frontend** : `authService.logout()` devient asynchrone et appelle `/auth/logout` pour révoquer côté serveur.

### Added — Module audit log (compliance)
- **Migration Alembic 0011** : table `audit_logs` (append-only) avec colonnes : user_id, facility_id, action, resource_type, resource_id, http_method, http_path, status_code, ip_address, user_agent, payload JSON.
- **Service `audit_log()`** (`app/modules/audit/service.py`) : helper à appeler depuis n'importe quelle route. Jamais bloquant (catch all errors, log + rollback).
- **Route `GET /audit/logs`** : liste paginée + filtres (action, resource_type, resource_id, user_id, start_date, end_date). SUPER_ADMIN voit tout, ADMIN voit sa facility.
- **Route `GET /audit/logs/{id}`** : détail d'une entrée.
- **Permission `audit.read`** : ajoutée au seed RBAC (réservée SUPER_ADMIN/ADMIN via bypass).
- **Audit automatique sur** : `auth.login`, `auth.login_failed`, `auth.login_inactive`, `auth.logout`.
- **Page frontend `/audit`** : tableau paginé avec filtres, codes couleur par action, modal de détail avec payload JSON formaté. Visible uniquement SUPER_ADMIN/ADMIN.
- **Sidebar** : section SYSTÈME enrichie avec "Journal d'audit".

### Added — Code splitting frontend (performance)
- **`React.lazy()` + `Suspense`** sur les 24 pages authentifiées.
- **Bundle initial** : 1014 KB → 252 KB (−75 %). Gzippé : 257 KB → 80 KB.
- Chunks par page : `AuditPage.js` 9.9 KB, `RbacPage.js` 9.5 KB, `DashboardPage.js` 15.9 KB, etc.
- Chunks Recharts isolés : `CategoricalChart.js` 296 KB (chargé uniquement sur pages avec graphiques), `BarChart.js` 47 KB, `PieChart.js` 17 KB.
- Plus d'avertissement "chunks > 500 kB" au build.

### Added — Tests
- **`backend/tests/test_refresh_audit.py`** : 15 nouveaux tests couvrant refresh token (issue, rotate, revoke, hash storage), audit log (login success/fail/logout enregistré, endpoint require auth, filtres, pagination).
- **`frontend/tests/e2e/guineecare.spec.ts`** : 2 nouveaux tests Playwright (page /audit accessible SUPER_ADMIN + DOCTOR redirigé).
- **Total** : 99 tests backend (84 + 15) + 14 tests Playwright (12 + 2).

### Fixed — Frontend
- **LoginPage** : ajout des `htmlFor` + `id` sur les labels/inputs pour sélecteurs Playwright stables (`#login-email`, `#login-password`).
- **Tests Playwright** : fonction `login()` réécrite — clear localStorage avant chaque login, IDs stables, `networkidle` wait. Tous les tests auparavant flaky sont désormais 100 % verts.
- **`playwright.config.ts`** : `reuseExistingServer: true` pour permettre le lancement d'un Vite externe + réutilisation par Playwright.
- **`vite-env.d.ts`** : recréé (perdu lors d'un reset) pour résoudre l'erreur TS2882 sur l'import side-effect CSS.

### Statistics
- 99/99 tests backend pytest (37 s)
- 14/14 tests Playwright UI (41 s)
- 31/31 tests E2E API admin pages (inchangés)
- Bundle initial : 252 KB (gzip 80 KB) — 4× plus léger
- 4 workflows GitHub Actions opérationnels
- 2 nouveaux modules backend : `auth.models` (RefreshToken, AuditLog), `audit` (service + routes)

---

## 0.5.0 — 2026-06-20

### Added — Tests Playwright E2E
- **12 parcours UI** avec Playwright 1.61 + Chromium
  - Authentification (login succès/échec, logout, multi-rôles)
  - Navigation pages admin (/users, /rbac, /facilities, /departments)
  - RBAC (DOCTOR/NURSE redirigés des pages admin)
  - Parcours patients
  - Dashboard (KPI visibles)
- `frontend/playwright.config.ts` — config avec webServer auto-start, traces, screenshots, vidéo
- `frontend/tests/e2e/guineecare.spec.ts` — 12 tests couvrant les parcours critiques
- Scripts npm : `npm run test:e2e`, `npm run test:e2e:ui`, `npm run test:e2e:report`

### Added — Vite proxy
- `frontend/vite.config.ts` — proxy `/api/*` → `http://127.0.0.1:8000`
- Plus besoin de `VITE_API_BASE_URL` en développement local
- Variable `VITE_API_PROXY_TARGET` configurable pour pointer vers un backend distant

### Added — CI/CD GitHub Actions (4 workflows)
- **`backend-tests.yml`** — pytest (84 tests) + cache pip + upload XML results
- **`frontend-build.yml`** — TypeCheck + build Vite + upload artifact `dist/`
- **`e2e-admin-pages.yml`** — 31 tests API E2E (déjà existant, inchangé)
- **`e2e-playwright.yml`** — Nouveau : démarre backend + seed, installe Chromium, lance les 12 tests Playwright, upload rapport HTML + traces
- Tous les workflows : `on: push: branches: [main]` + `pull_request`
- Badges README pour les 4 workflows

### Fixed — Backend
- **Rate limiter** `@limiter.limit("5/minute")` sur `/auth/login` :
  - Désactivé en `ENVIRONMENT=local|test|dev` (facilite tests E2E et Playwright)
  - Activé en production/staging (sécurité brute-force)
- Correction syntaxe YAML dans `backend-tests.yml` et `frontend-build.yml` (`branches: ain]` → `branches: [main]`)

### Updated — Documentation
- README enrichi : badges CI, table des 4 workflows, section Proxy Vite, section Contribution, conventions de commit Angular, roadmap v0.6-v1.0
- Référence aux scripts Playwright (`npm run test:e2e*`)
- Exemples de code multi-tenant RLS et ProtectedRoute

### Statistics
- 84/84 tests pytest backend
- 31/31 tests E2E API pages admin
- 12 tests Playwright UI (parcours critiques)
- 4 workflows GitHub Actions opérationnels
- ~3 min de pipeline CI total

---

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
