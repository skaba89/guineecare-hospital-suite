# Cahier des Charges — Test d'Intrusion Externe (Pen Test)

**Projet :** GuinéeCare Hospital Suite
**Version :** 1.0
**Date :** Juillet 2026
**Classification :** Confidentiel — Diffusion restreinte
**Commanditaire :** Ministère de la Santé de la République de Guinée
**Référence :** Prérequis P0 — déploiement national flagship GuinéeCare

---

## 1. Contexte et objectifs

### 1.1 Contexte du projet

GuinéeCare Hospital Suite est la plateforme hospitalière nationale déployée par le Ministère de la Santé de la République de Guinée. La plateforme traite des **données de santé à grande échelle** (Article 9 RGPD), ce qui en fait une cible potentielle pour les attaques informatiques.

Avant un déploiement à l'échelle nationale (prévu après la phase pilote CHU Donka / CHU Ignace Deen), le Ministère de la Santé souhaite faire réaliser un **test d'intrusion externe indépendant** par un prestataire spécialisé.

### 1.2 Objectifs du test

Le test d'intrusion vise à :

1. **Identifier les vulnérabilités techniques** de l'application GuinéeCare Hospital Suite (backend API, frontend web, application mobile) avant le déploiement national.
2. **Valider les mesures de sécurité** déjà implémentées (RBAC, multi-tenant, JWT, 2FA, audit log, rate limiting).
3. **Tester la résistance** de l'architecture aux attaques OWASP Top 10 et aux menaces spécifiques aux données de santé.
4. **Fournir des recommandations** priorisées pour le durcissement de la plateforme.
5. **Constituer un livrable** opposable aux autorités de contrôle (ARPT, audit ministériel) et aux partenaires internationaux (OMS, banques de développement).

### 1.3 Périmètre fonctionnel

| Composant | URL / accès | Périmètre |
|-----------|-------------|-----------|
| Backend API FastAPI | https://[backend-render].onrender.com/api/v1 | ✅ Inclus |
| Frontend React | https://[frontend-render].onrender.com | ✅ Inclus |
| Application mobile React Native | APK Android à fournir | ✅ Inclus |
| Base de données Neon | Inaccessible directement | ❌ Hors périmètre (test via l'app seulement) |
| Instance DHIS2 nationale | https://dhis2.sante.gov.gn | ❌ Hors périmètre (géré par la DSI nationale) |
| Infrastructure Render/Neon | N/A | ❌ Hors périmètre (test via app seulement) |

### 1.4 Types de tests demandés

Le prestataire réalisera les tests suivants :

1. **Test boîte noire (black box)** — sans accès au code source, comme un attaquant externe
2. **Test boîte grise (gray box)** — avec accès à un compte utilisateur standard (DOCTOR, NURSE, PHARMACIST)
3. **Test boîte blanche (white box)** — avec accès au code source (repo GitHub privé) pour optimiser la couverture

Les trois approches sont complémentaires et seront toutes réalisées.

---

## 2. Référentiels et méthodologie

### 2.1 Cadre méthodologique

Le test d'intrusion devra suivre la méthodologie **OWASP Web Security Testing Guide (WSTG)** v4.2 ou supérieure, et notamment les phases suivantes :

- **WSTG-INFO** — Information Gathering
- **WSTG-CONF** — Configuration and Deployment Management Testing
- **WSTG-IDNT** — Identity Management Testing
- **WSTG-ATHN** — Authentication Testing
- **WSTG-ATHZ** — Authorization Testing
- **WSTG-SESS** — Session Management Testing
- **WSTG-INPV** — Input Validation Testing
- **WSTG-ERRH** — Error Handling Testing
- **WSTG-CRYP** — Cryptography Testing
- **WSTG-BUSL** — Business Logic Testing
- **WSTG-CLNT** — Client-side Testing
- **WSTG-APIT** — API Testing

### 2.2 Référentiels complémentaires

- **OWASP Top 10 2021** — catégories de risques majeurs
- **OWASP API Security Top 10 2023** — spécifique aux API REST
- **OWASP Mobile Top 10 2024** — pour l'application mobile
- **PTES** (Penetration Testing Execution Standard) — méthodologie générale
- **NIST SP 800-115** — Technical Guide to Information Security Testing

### 2.3 Conformité sectorielle

Le test devra valider la conformité avec :
- **RGPD** (Article 32 — sécurité du traitement)
- **HDS** (Hébergeur de Données de Santé) — si applicable à l'infrastructure
- **ISO 27001** — annexe A.12 (Operations security)
- **Loi guinéenne L/2022/018/AN** sur la protection des données

---

## 3. Périmètre technique détaillé

### 3.1 Backend API FastAPI

#### Authentification et sessions
- Login / logout / refresh JWT
- Rate limiting sur `/auth/login` (5 tentatives/min)
- Lockout après 5 échecs
- 2FA TOTP (Google Authenticator)
- Refresh token rotation
- JTI blacklist (logout révoqué)

#### RBAC et multi-tenant
- 8 rôles (SUPER_ADMIN, ADMIN, DOCTOR, NURSE, MIDWIFE, PHARMACIST, LAB_TECH, CASHIER)
- Permissions granulaires (≥ 50 permissions)
- Isolation multi-tenant par `facility_id`
- `enforce_facility_access` sur toutes les routes métier
- Tentative de cross-tenant access (lecture/écriture d'un patient d'un autre établissement)

#### Endpoints sensibles à tester prioritairement
- `POST /api/v1/auth/login` — brute force, credential stuffing, SQL injection
- `POST /api/v1/auth/2fa/verify` — bypass 2FA, brute force TOTP
- `POST /api/v1/users/bootstrap` — bypass X-Bootstrap-Token
- `GET /api/v1/patients/{id}` — IDOR (Insecure Direct Object Reference)
- `POST /api/v1/billing/invoices` — falsification montant, injection
- `POST /api/v1/reporting/dhis2/{period}/push` — exfiltration de données nationales
- `GET /api/v1/audit/logs` — lecture du journal d'audit par un DOCTOR (devrait être 403)
- `POST /api/v1/tasks/trigger/{name}` — exécution de tâche système par un DOCTOR (devrait être 403)
- WebSocket `/api/v1/realtime` — injection de messages cross-tenant

#### Recherche de vulnérabilités spécifiques
- **Injection SQL** — toutes les routes avec paramètre `?search=`, `?patient_id=`, etc.
- **Injection de commandes** — `subprocess` dans `backup_database` ( Celery task )
- **SSRF** — `requests.post` dans `push_dhis2_dataset` (URL DHIS2 configurable)
- **Path traversal** — génération de documents PDF (`/documents`)
- **XXE** — parser XML si utilisé (FHIR R4)
- **Mass assignment** — payloads JSON avec champs non prévus (ex: `role`, `facility_id`)
- **Race conditions** — création en double de patients, paiements concurrents
- **Information disclosure** — messages d'erreur verbeux, stack traces, `/docs` en production

### 3.2 Frontend React

#### Tests spécifiques
- **XSS (Cross-Site Scripting)** — réflexion de données utilisateur dans le DOM
- **CSRF** — vérifier l'absence de token CSRF (JWT Bearer supposed immune, mais à valider)
- **CSP** — vérifier les directives Content-Security-Policy (déjà configurées)
- **Local storage** — token JWT stocké en clair (vérifier le risque de vol XSS)
- **Source maps** — vérifier que les `.map` ne sont pas exposés en production
- **Service worker** — vérifier que le SW ne cache pas des données sensibles
- **CORS** — vérifier la configuration `allow_origins`

### 3.3 Application mobile React Native

#### Tests spécifiques (OWASP Mobile Top 10)
- **M1: Improper Credential Usage** — biometric, code PIN local
- **M2: Insecure Data Storage** — données patient en cache local
- **M3: Insecure Communication** — TLS pinning, certificate validation
- **M4: Insecure Authentication** — offline sync, token JWT en local
- **M5: Insufficient Cryptography** — chiffrement des données offline
- **M6: Insecure Authorization** — bypass RBAC via l'app mobile
- **M7: Client Code Quality** — reverse engineering de l'APK
- **M8: Code Tampering** — re-packaging de l'APK
- **M9: Reverse Engineering** — obfuscation du code
- **M10: Extraneous Functionality** — debug endpoints en production

---

## 4. Méthodologie d'exécution

### 4.1 Planning prévisionnel

| Phase | Durée | Description |
|-------|-------|-------------|
| **Phase 1** — Cadrage | 1 semaine | Réunion de kickoff, validation du périmètre, accès aux environnements |
| **Phase 2** — Reconnaissance | 1 semaine | Information gathering, fingerprinting, scan de vulnérabilités automatisé |
| **Phase 3** — Tests manuels | 2 semaines | Exploitation, post-exploitation, tests métier spécifiques |
| **Phase 4** — Reporting | 1 semaine | Rédaction du rapport, présentation des résultats |
| **Phase 5** — Restitution | 0,5 semaine | Présentation orale, atelier de correction |
| **Total** | **5,5 semaines** | |

### 4.2 Environnement de test

Le test sera réalisé sur un **environnement de pré-production** séparé de la production pilote, mais avec une **base de données réaliste** (anonymisée ou synthétique).

- **URL** : https://preprod.guineecare.gn (à provisionner)
- **Données** : jeu de données synthétique (50 patients, 10 users, 5 établissements) — pas de données patient réelles
- **Comptes de test** : 1 SUPER_ADMIN, 1 ADMIN, 2 DOCTOR, 1 NURSE, 1 PHARMACIST, 1 LAB_TECH, 1 CASHIER
- **Code source** : accès au repo GitHub privé `skaba89/guineecare-hospital-suite`

### 4.3 Outils attendus

Le prestataire utilisera au minimum :
- **Burp Suite Professional** (ou équivalent) — proxy d'interception
- **OWASP ZAP** — scan automatisé
- **Nuclei** — templates de vulnérabilités
- **Nmap** — scan de ports et services
- **SQLMap** — détection et exploitation SQL injection
- **FFUF / Gobuster** — fuzzing et directory listing
- **MobSF** (Mobile Security Framework) — analyse mobile
- **Frida** — instrumentation dynamique (mobile)

### 4.4 Règles d'engagement

#### Autorisé
- Tests d'intrusion sur l'application GuinéeCare (backend, frontend, mobile)
- Utilisation de comptes de test fournis
- Exploitation de vulnérabilités avec preuve de concept (PoC) non destructrice
- Exfiltration de données de test (uniquement) à des fins de démonstration
- Scan automatisé limité à 100 requêtes/seconde (pour ne pas saturer l'environnement)

#### Strictement interdit
- **Attaques DoS/DDoS** (Déni de Service)
- **Tests sur l'infrastructure Render/Neon** (hors app GuinéeCare)
- **Tests sur l'instance DHIS2 nationale**
- **Exfiltration de données patient réelles** (utiliser uniquement le jeu de données synthétique)
- **Modifications destructives** (DROP TABLE, suppression de données)
- **Tests sur la production pilote** (CHU Donka) — uniquement pré-production
- **Ingénierie sociale** (phishing du personnel) hors accord explicite préalable

#### En cas d'incident
- Si le prestataire découvre une **vulnérabilité critique exploitable permettant l'accès aux données patient réelles**, il doit **interrompre immédiatement le test** et notifier le commanditaire sous **1 heure**.
- Si une vulnérabilité entraîne une **violation de données avérée**, le DPO doit être informé pour déclenchement de la procédure Article 33 RGPD (notification ARPT sous 72h).

---

## 5. Livrables attendus

### 5.1 Rapport technique détaillé

Le rapport technique contiendra :

1. **Synthèse exécutive** (2-3 pages) — destinée au Ministre de la Santé
   - Score global de sécurité (sur 10)
   - Nombre de vulnérabilités par sévérité (Critique / Élevée / Moyenne / Faible)
   - Top 5 des vulnérabilités à corriger en priorité
   - Recommandations stratégiques

2. **Méthodologie et périmètre** (5 pages)
   - Cadre méthodologique utilisé
   - Périmètre fonctionnel et technique
   - Outils utilisés
   - Planning effectif

3. **Détail des vulnérabilités** (par vulnérabilité, ~2-5 pages chacune)
   - Titre et sévérité (CVSS v3.1)
   - Description technique
   - Preuve de concept (PoC) — code ou capture d'écran
   - Impact métier (confidentialité, intégrité, disponibilité)
   - Recommandation de correction
   - Référence OWASP / CWE

4. **Annexes**
   - Logs complets des tests
   - Sorties des outils (Burp, Nmap, etc.)
   - Captures d'écran

### 5.2 Présentation orale

- Durée : 2 heures
- Audience : DSI, RSSI, DPO, équipe technique GuinéeCare, Directeur Médical
- Format : présentation des résultats + atelier Q&A
- Livrable : slides au format PDF

### 5.3 Support de correction

- Atelier de **2 heures** avec l'équipe technique pour détailler les corrections à apporter
- **Plan d'action priorisé** (P0/P1/P2) avec estimation de charge
- Disponibilité du prestataire pour **questions de clarification** pendant 30 jours après la restitution

### 5.4 Rapport de re-test (optionnel)

Après correction des vulnérabilités critiques et élevées, le prestataire réalisera un **re-test** (1 semaine) pour valider les corrections. Ce re-test donnera lieu à un rapport complémentaire.

---

## 6. Critères de sévérité

Le prestataire utilisera le référentiel **CVSS v3.1** pour évaluer la sévérité de chaque vulnérabilité, avec la correspondance suivante :

| CVSS Score | Sévérité | Couleur | Délai de correction |
|------------|----------|---------|---------------------|
| 9.0 – 10.0 | Critique | Rouge | ≤ 7 jours |
| 7.0 – 8.9 | Élevée | Orange | ≤ 30 jours |
| 4.0 – 6.9 | Moyenne | Jaune | ≤ 90 jours |
| 0.1 – 3.9 | Faible | Bleu | ≤ 180 jours |
| 0.0 | Information | Gris | Pas de correction requise |

Le **contexte spécifique des données de santé** sera pris en compte dans l'évaluation : une vulnérabilité permettant l'accès non autorisé à des données de santé sera automatiquement sur-évaluée d'au moins un niveau (ex: Moyenne → Élevée).

---

## 7. Profil du prestataire recherché

### 7.1 Certifications requises

Le prestataire devra disposer des certifications suivantes :
- **ANSSI** — visée de qualification (pour la France) ou équivalent européen
- **CREST** — Certified Tester
- **OSCP** (Offensive Security Certified Professional) pour les auditeurs intervenants
- Au minimum 3 ans d'expérience en tests d'intrusion d'applications web et mobiles

### 7.2 Expérience sectorielle

Le prestataire devra justifier d'une expérience préalable dans :
- Tests d'intrusion d'**applications de santé** (SIH, DMP, télémédecine)
- Connaissance du **RGPD** appliqué aux données de santé (Article 9)
- Connaissance des **normes HL7 FHIR** et **DHIS2** (recommandé)

### 7.3 Indépendance

Le prestataire devra signer un engagement d'indépendance et ne pas avoir de lien commercial avec :
- L'équipe de développement de GuinéeCare
- Les fournisseurs d'infrastructure (Render, Neon, AWS)
- Les fournisseurs de la stack technique (FastAPI, React, etc.)

### 7.4 Confidentialité

Le prestataire signera un **NDA (Non-Disclosure Agreement)** avec le Ministère de la Santé avant tout accès aux documents et environnements. Les données de test (synthétiques) ne pourront pas être conservées au-delà de la fin du test.

---

## 8. Critères de jugement des offres

Les offres seront évaluées sur les critères pondérés suivants :

| Critère | Poids |
|---------|-------|
| Méthodologie proposée (pertinence, exhaustivité) | 30% |
| Expérience sectorielle (santé, RGPD) | 25% |
| Qualifications de l'équipe intervenante | 20% |
| Prix (voir budget indicatif ci-dessous) | 15% |
| Références clients similaires | 10% |

### Budget indicatif

- **Fourchette estimée** : 25 000 € – 50 000 € HT (selon périmètre exact)
- **Financement** : à charge du Ministère de la Santé / partenaires internationaux (OMS, Banque Mondiale)
- **Modalités** : 40% à la commande, 40% à la restitution, 20% après re-test

---

## 9. Planning prévisionnel

| Étape | Date cible | Responsable |
|-------|------------|-------------|
| Publication du cahier des charges | S+0 | DSI Ministère |
| Réception des offres | S+3 | DSI Ministère |
| Sélection du prestataire | S+5 | DSI + DPO + RSSI |
| NDA + contrat signé | S+6 | DSI |
| Kickoff et accès aux environnements | S+7 | Prestataire + DSI |
| Phase de tests | S+8 à S+12 | Prestataire |
| Restitution et rapport | S+13 | Prestataire |
| Atelier de correction | S+14 | Prestataire + équipe technique |
| Correction des P0 | S+15 à S+17 | Équipe technique |
| Re-test | S+18 | Prestataire |
| Rapport final et go/no-go déploiement national | S+19 | DSI + DPO |

> ⚠️ Le déploiement national de GuinéeCare ne pourra pas être lancé tant que les vulnérabilités critiques (P0) identifiées lors du pen test ne seront pas corrigées et validées par le re-test.

---

## 10. Annexes

### Annexe A — Architecture technique cible

Voir `docs/architecture/` du dépôt GuinéeCare :
- `architecture-generale.md` — vue d'ensemble
- `architecture-deploiement.md` — Render + Neon
- `architecture-mobile.md` — React Native

### Annexe B — Code source et documentation technique

- **Repo GitHub privé** : `skaba89/guineecare-hospital-suite`
- **Documentation OpenAPI** : https://[backend-render].onrender.com/docs
- **Spécification FHIR R4** : endpoint `/api/v1/fhir/metadata`
- **Métriques Prometheus** : endpoint `/metrics` (token-gated)

### Annexe C — Documents RGPD existants

- `docs/securite/AIPD_v1.md` — Analyse d'Impact relative à la Protection des Données
- `docs/securite/REGISTRE_TRAITEMENTS.md` — Registre des traitements
- `docs/securite/NOTICE_PATIENT.md` — Notice d'information patient
- `docs/securite/DPO_DESIGNATION_v1.md` — Désignation du DPO

### Annexe D — Checklist de sécurité déjà implémentée

Le prestataire pourra s'appuyer sur cette checklist pour ne pas refaire les tests de base :

| Mesure | Statut | Référence code |
|--------|--------|----------------|
| Authentification JWT + refresh rotation | ✅ | `app/modules/auth/` |
| 2FA TOTP (Google Authenticator) | ✅ | `app/modules/auth/two_factor_*` |
| RBAC granulaire (8 rôles, 50+ permissions) | ✅ | `app/modules/rbac/` |
| Multi-tenant par `facility_id` | ✅ | `app/core/tenant.py` |
| Audit log append-only | ✅ | `app/modules/audit/` |
| Rate limiting (slowapi + Redis) | ✅ v2.9.2 | `app/core/limiter.py` |
| Security headers (CSP, HSTS, X-Frame-Options) | ✅ | `app/main.py` |
| Lockout après 5 échecs login | ✅ | `app/modules/auth/` |
| CORS restreint | ✅ | `app/main.py` |
| Prévention X-Forwarded-For spoofing | ✅ | `app/core/limiter.py` |
| Rotation des backups (30 jours) | ✅ v2.9.2 | `app/tasks/maintenance_tasks.py` |
| Pruning audit log (365 jours) | ✅ v2.9.2 | `app/tasks/maintenance_tasks.py` |
| Métriques Prometheus token-gated | ✅ | `app/modules/observability/` |
| Secret management (env vars, sync=false) | ✅ | `render.yaml` |

### Annexe E — Contacts

| Rôle | Nom | Email |
|------|-----|-------|
| Commanditaire | Ministre de la Santé | cabinet@sante.gov.gn |
| DSI Ministère | [À compléter] | dsi@sante.gov.gn |
| RSSI | [À compléter] | rssi@sante.gov.gn |
| DPO | [À compléter — voir DPO_DESIGNATION_v1.md] | dpo@sante.gov.gn |
| Lead dev GuinéeCare | [À compléter] | tech@guineecare.gn |

---

## 11. Validation du cahier des charges

| Rôle | Nom | Date | Signature |
|------|-----|------|-----------|
| DSI Ministère | | | |
| RSSI | | | |
| DPO | | | |
| Ministre de la Santé | | | |
