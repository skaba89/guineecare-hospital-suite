# Roadmap V3.0 — GuinéeCare Hospital Suite

**Date :** Juillet 2026
**Version document :** 1.0
**Périmètre :** Évolutions post-v2.9.3, horizon 12-18 mois
**Maître d'ouvrage :** Ministère de la Santé de la République de Guinée
**Maître d'œuvre :** Équipe technique GuinéeCare

---

## 1. Contexte

La version 2.9.3 finalise un cycle d'industrialisation et de mise en conformité. Le projet est **opérationnellement prêt** pour un déploiement national flagship, sous réserve des 3 décisions administratives P0 restantes (Render Starter, DPO nommé, pen test réalisé).

La roadmap V3.0 identifie les évolutions **stratégiques** à mener après le déploiement pilote, pour transformer GuinéeCare en plateforme de référence africaine. Elle se structure autour de 4 axes :

1. **Interopérabilité** — Branchement aux standards internationaux (OMS, HL7, SNIS)
2. **Télémédecine** — Étendre la couverture aux zones rurales mal connectées
3. **IA clinique** — Aide à la décision pour les praticiens isolés
4. **Durabilité** — Renforcer le modèle économique et opérationnel

---

## 2. Vue d'ensemble des lots V3.0

| Lot | Titre | Priorité | Estimation | Dépendance |
|-----|-------|----------|------------|------------|
| **V3.1** | Intégration ICD-11 API officielle OMS | P1 | 4 semaines | — |
| **V3.2** | FHIR R4 bidirectionnel avec DHIS2 | P1 | 6 semaines | V3.1 |
| **V3.3** | Module de télémédecine | P1 | 10 semaines | — |
| **V3.4** | Aide à la décision clinique (rules engine) | P2 | 8 semaines | V3.1 |
| **V3.5** | Module de signature électronique | P2 | 3 semaines | — |
| **V3.6** | Mode offline complet (mobile-first) | P2 | 6 semaines | — |
| **V3.7** | Observabilité avancée (Grafana, alerting) | P2 | 4 semaines | — |
| **V3.8** | Module formation continue e-learning | P3 | 8 semaines | — |
| **V3.9** | API publique pour chercheurs (anonymisée) | P3 | 6 semaines | V3.4 |
| **V3.10** | SaaS multi-pays (export régional) | P3 | 12 semaines | Toute la V3 |

**Total estimé :** ~67 semaines de développement (≈ 15 mois avec 1 équipe de 3 devs).

---

## 3. Détail des lots

### V3.1 — Intégration ICD-11 API officielle OMS (P1, 4 semaines)

#### Objectif

Remplacer le catalogue embarqué (~80 codes) par l'**API officielle OMS** (https://icd.who.int/icdapi) qui expose les 55 000+ codes ICD-11 dans toutes les langues de l'OMS.

#### Périmètre

- Connexion OAuth2 à l'API OMS (client_id/client_secret)
- Cache local Redis (TTL 24h) pour éviter les appels en rafale
- Recherche multilingue (FR, EN, arabe — utile pour la Guinée)
- Conservation du catalogue embarqué comme **fallback offline**
- Migration des diagnostics existants (champ `diagnosis_code` déjà libre — pas de migration DB)

#### Livrables

- `backend/app/modules/icd11/oms_client.py` — client OAuth2 + cache
- `backend/app/modules/icd11/routes.py` — endpoints `/icd11/search` rétro-compatibles
- Tests backend (mock de l'API OMS)
- Documentation mise à jour

#### Risques

- **Disponibilité API OMS** — Pas de SLA officiel. Mitigation : cache + fallback catalogue.
- **Quotas** — L'API OMS est limitée. Mitigation : cache Redis TTL 24h.
- **Coût** — L'API OMS est gratuite pour les États membres. Vérifier le statut de la Guinée.

---

### V3.2 — FHIR R4 bidirectionnel avec DHIS2 (P1, 6 semaines)

#### Objectif

Activer le **push effectif** des données agrégées mensuelles vers l'instance DHIS2 nationale (https://dhis2.sante.gov.gn), et permettre le **pull** des métadonnées DHIS2 (data elements, category options) pour aligner les indicateurs.

#### Périmètre

- Authentification DHIS2 (basic auth + token)
- Mapping FHIR R4 → DHIS2 dataValueSets (déjà partiellement implémenté en v2.9.1)
- Crontab mensuelle (déjà planifiée en v2.9.2 via Celery beat)
- Tableau de bord de suivi des pushs (succès/échec/retry)
- Réconciliation : en cas d'écart entre données GuinéeCare et DHIS2, alerte automatique
- Audit log détaillé des pushs (déjà implémenté en v2.9.2)

#### Livrables

- `backend/app/modules/reporting/dhis2_client.py` — client bidirectionnel
- `backend/app/modules/reporting/dhis2_mapping.py` — table de correspondance
- `frontend/src/pages/Dhis2SyncPage.tsx` — UI de suivi
- Tests backend (mock DHIS2)
- Documentation pour l'équipe SNIS nationale

#### Dépendances

- V3.1 (ICD-11) — les diagnostics doivent utiliser les codes OMS pour le mapping DHIS2
- Configuration DHIS2_URL/USERNAME/PASSWORD en production

#### Risques

- **Version DHIS2 nationale** — Vérifier la compatibilité (DHIS2 2.38+ recommandé)
- **Accès au serveur DHIS2** — Nécessite une autorisation de la DSI nationale
- **Mapping indicateurs** — Travail d'alignement avec l'équipe SNIS (non technique)

---

### V3.3 — Module de télémédecine (P1, 10 semaines)

#### Objectif

Permettre les **consultations à distance** entre un patient isolé (poste de santé rural) et un médecin spécialiste (CHU Donka / Ignace Deen). Trois cas d'usage :

1. **Téléconsultation synchrone** — Visio + chat + partage de documents cliniques
2. **Télé-expertise asynchrone** — Envoi de cas cliniques à un spécialiste pour avis
3. **Suivi post-opératoire** — Visites de contrôle à distance

#### Périmètre

- WebRTC (visio) — intégration LiveKit ou Jitsi
- Chat temps réel (déjà couvert par WebSocket `realtime` v1.3.0)
- Planification de rendez-vous (extension du module `admissions`)
- Partage de documents (imagerie, ECG, biologiques)
- Prescription électronique (extension du module `clinical`)
- Traçabilité complète (audit log)
- Support multi-langue (FR, EN, peul, malinké, soussou)

#### Livrables

- `backend/app/modules/telemedicine/` — module complet (models, routes, service)
- `frontend/src/pages/TelemedicinePage.tsx` — UI patient
- `frontend/src/pages/TelemedicinePractitionerPage.tsx` — UI médecin
- `mobile/` — intégration visio sur mobile
- Migration Alembic (3 nouvelles tables)
- Documentation utilisateur (guide téléconsultation)

#### Dépendances

- Connexion Internet stable côté CHU (déjà OK)
- Bande passante minimale côté poste rural (1 Mbps suffisant pour visio compressée)
- Compatible avec le mode offline mobile (V3.6)

#### Risques

- **Connectivité rurale** — Visio impossible en 3G. Mitigation : mode asynchrone (télé-expertise) en fallback.
- **Acceptation culturelle** — Prévoir formation patient + praticien
- **Cadre légal** — Vérifier la législation guinéenne sur la télémédecine (loi en cours d'adoption)

---

### V3.4 — Aide à la décision clinique (rules engine) (P2, 8 semaines)

#### Objectif

Implémenter un **moteur de règles cliniques** qui analyse les données patient en temps réel et propose des recommandations aux praticiens (alertes d'interactions médicamenteuses, dépistages recommandés, suivi des pathologies chroniques).

#### Périmètre

- Moteur de règles (Drools-like ou Python custom)
- Bibliothèque de règles initiales (50+ règles) :
  - Interactions médicamenteuses (théophylline + ciprofloxacine, etc.)
  - Dépistages par âge/sexe (cancer col utérin, hypertension)
  - Alertes grossesse à risque (prééclampsie, gélatine gélatinipare)
  - Suivi diabète (HbA1c tous les 3 mois, etc.)
  - Vaccinations manquantes
- UI d'alerte en temps réel dans le dossier patient
- Possibilité pour le praticien de marquer une alerte comme "non pertinente"
- Audit log de chaque alerte générée

#### Dépendances

- V3.1 (ICD-11) — pour les diagnostics structurés
- Module `clinical` existant (constantes, prescriptions)

#### Risques

- **Qualité des règles** — Doivent être validées par un collège de praticiens guinéens
- **Surcharge d'alertes** — Mitigation : paramétrage par utilisateur (alertes critiques vs info)

---

### V3.5 — Module de signature électronique (P2, 3 semaines)

#### Objectif

Permettre la **signature électronique** des ordonnances, certificats médicaux et comptes rendus opératoires, avec valeur légale en Guinée.

#### Périmètre

- Signature électronique basée sur certificat (PAdES pour PDF, XAdES pour XML)
- Intégration avec un prestataire de signature qualifié (eIDAS niveau qualifié)
- Traçabilité complète (hash du document signé, horodatage, identité signataire)
- Vérification de signature dans l'UI (badge "Signé électroniquement")
- Export PDF signé téléchargeable

#### Risques

- **Cadre légal guinéen** — La signature électronique n'a pas encore de valeur légale pleine en Guinée. Vérifier l'avancement de la loi.
- **Coût prestataire** — Signature qualifiée ≈ 0,50 € par document. Budget à prévoir.

---

### V3.6 — Mode offline complet (mobile-first) (P2, 6 semaines)

#### Objectif

Étendre le mode offline du mobile (déjà partiellement implémenté en v2.8.9) pour permettre une **utilisation complète en zones sans connexion** (postes de santé ruraux).

#### Périmètre

- Cache local SQLite (React Native) pour :
  - Dossiers patients récents (50 derniers consultés)
  - Catalogue médicaments
  - Catalogue ICD-11 (déjà embarqué en v2.9.2)
  - Plannings du praticien
- File d'attente des mutations (déjà implémenté en v2.8.9)
- Synchronisation au prochain login (déjà implémenté)
- Gestion des conflits (dernière écriture gagne, avec audit log)

#### Dépendances

- App mobile (React Native) — déjà déployée en v2.8.9

---

### V3.7 — Observabilité avancée (Grafana, alerting) (P2, 4 semaines)

#### Objectif

Mettre en place une stack d'observabilité complète pour la production : Grafana (dashboards), Loki (logs), Alertmanager (alerting), PagerDuty (escalade).

#### Périmètre

- Dashboards Grafana prêts à l'emploi :
  - Vue métier (KPIs hospitaliers en temps réel)
  - Vue technique (latence API, erreurs 5xx, saturation DB)
  - Vue sécurité (tentatives de login échouées, rate limit hits)
- Alertes critiques (email + SMS via module v1.4.0) :
  - Erreur 500 en rafale (> 5/min)
  - Latence p95 > 1s
  - DB disk > 80 %
  - Worker Celery inactif > 5 min
- Runbook opérateur (procédures de réponse à chaque alerte)

---

### V3.8 — Module formation continue e-learning (P3, 8 semaines)

#### Objectif

Intégrer un **LMS (Learning Management System)** dans GuinéeCare pour la formation continue des praticiens : modules e-learning, quiz, certificats, suivi DPC (Développement Professionnel Continu).

#### Périmètre

- Catalogue de modules (10 modules initiaux) :
  - Paludisme grave chez l'enfant
  - Prise en charge de la prééclampsie
  - Réanimation néonatale
  - Bon usage des antibiotiques
  - Prévention des infections associées aux soins
  - etc.
- Quiz interactifs (QCM, cas cliniques)
- Certificats de réussite (avec signature électronique V3.5)
- Suivi des validations par le Conseil National de l'Ordre des Médecins

---

### V3.9 — API publique pour chercheurs (anonymisée) (P3, 6 semaines)

#### Objectif

Exposer une **API publique anonymisée** pour permettre aux chercheurs (universités, OMS, banques de développement) d'effectuer des études épidémiologiques sur les données agrégées GuinéeCare.

#### Périmètre

- Endpoints `/api/v1/public/` :
  - `/public/stats/demographics` — pyramide âge/sexe par région
  - `/public/stats/epidemiology` — incidence mensuelle par pathologie
  - `/public/stats/quality` — indicateurs qualité OMS
- Anonymisation (k-anonymité ≥ 5) — suppression des groupes démographiques trop petits
- Quotas (1000 requêtes/jour par token)
- Documentation OpenAPI publique
- Comité scientifique de validation des accès

#### Dépendances

- V3.4 (rules engine) — pour valider la cohérence des données avant publication

---

### V3.10 — SaaS multi-pays (export régional) (P3, 12 semaines)

#### Objectif

Transformer GuinéeCare en **SaaS multi-pays** déployable dans d'autres pays africains (Liberia, Sierra Leone, Mali, Côte d'Ivoire) avec adaptation aux contextes nationaux.

#### Périmètre

- Multi-tenancy au niveau pays (extension du multi-tenant `facility_id` existant)
- Personnalisation :
  - Langues officielles
  - Système monétaire
  - Catalogue médicaments national
  - Codes diagnostiques spécifiques (endémies locales)
  - Réglementation RGPD/locale
- Module de facturation SaaS (par utilisateur actif)
- Marketplace d'extensions (plugins pays-spécifiques)

#### Risques

- **Complexité architecture** — Refactor profond du multi-tenant
- **Concurrence** — Dossier médical partagé (DMP) en Côte d'Ivoire, etc.
- **Stratégie commerciale** — À valider avec le Ministère (cession, licence, joint-venture)

---

## 4. Priorisation et planning

### 4.1 Planning indicatif (12-18 mois)

```
2026 H2                  2027 H1                   2027 H2
─────────────────────────────────────────────────────────────
T3 2026 (juil-sep)
├── V3.1 ICD-11 OMS API (4 sem)         ── Phase pilote ──┐
├── V3.5 Signature électronique (3 sem)                  │
└── V3.7 Observabilité avancée (4 sem)                   │
                                                          ▼
T4 2026 (oct-déc)
├── V3.2 FHIR/DHIS2 bidir (6 sem)       ── Déploiement national ──┐
├── V3.6 Mode offline complet (6 sem)                              │
└── V3.4 Aide à la décision (début, 4 sem)                         │
                                                                   ▼
T1 2027 (jan-mar)
├── V3.4 Aide à la décision (suite, 4 sem)  ── Premiersdashboards IA ─┐
├── V3.3 Télémédecine (début, 6 sem)                                  │
└── V3.9 API publique chercheurs (6 sem)                              │
                                                                      ▼
T2 2027 (avr-juin)
├── V3.3 Télémédecine (suite, 4 sem)            ── Télémédecine pilote ─┐
├── V3.8 E-learning (8 sem)                                            │
└── V3.10 SaaS multi-pays (début, 6 sem)                               │
                                                                       ▼
T3 2027 (juil-sep)
└── V3.10 SaaS multi-pays (suite, 6 sem)        ── Premier pays pilote ──┘
```

### 4.2 Priorisation justifiée

| Priorité | Lots | Justification |
|----------|------|---------------|
| **P1** | V3.1, V3.2, V3.3 | Critiques pour l'atteinte des objectifs nationaux (interopérabilité SNIS, couverture rurale) |
| **P2** | V3.4, V3.5, V3.6, V3.7 | Améliorent la qualité et la robustesse sans changer le périmètre |
| **P3** | V3.8, V3.9, V3.10 | Élargissement du scope, à valider après bilan pilote |

---

## 5. Ressources nécessaires

### 5.1 Équipe technique

| Rôle | Effectif | Coût mensuel indicatif |
|------|----------|------------------------|
| Lead developer | 1 | 8 000 € |
| Backend developers | 2 | 12 000 € |
| Frontend developers | 1 | 6 000 € |
| Mobile developer | 1 | 6 000 € |
| DevOps | 0,5 | 3 000 € |
| Product owner | 0,5 | 3 000 € |
| Designer UX | 0,25 | 1 500 € |
| **Total mensuel** | **5,25 ETP** | **39 500 €/mois** |

### 5.2 Budget annuel V3.0

| Poste | Montant |
|-------|---------|
| Équipe technique (12 mois) | 474 000 € |
| Infrastructure (Render + Redis + Neon + Grafana Cloud) | 6 000 € |
| Outils (GitHub, Figma, Sentry, etc.) | 4 000 € |
| Formation continue équipe | 10 000 € |
| Certification ISO 27001 (optionnelle) | 25 000 € |
| **Total année 1** | **≈ 519 000 €** |

### 5.3 Financement à sécuriser

- **Ministère de la Santé guinéen** : 30 % du budget (postes permanents)
- **Banque Mondiale / BAD** : 40 % (projet d'appui au système de santé)
- **OMS** : 15 % (volet interopérabilité SNIS/DHIS2)
- **GIZ / AFD** : 15 % (volet télémédecine rurale)

> 💡 L'engagement de financement doit être formalisé **avant le démarrage de V3.1** (septembre 2026 cible).

---

## 6. Risques transverses

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Financement non bouclé | Moyenne | Critique | Présenter V3.0 aux bailleurs en T3 2026 |
| Perte de ressources clés (lead dev) | Moyenne | Élevé | Documentation + pair programming |
| Conflit avec autres priorités Ministère | Élevée | Moyen | Comité de pilotage trimestriel |
| Instabilité politique | Faible | Critique | Hébergement Redundant (Render + VPS de secours) |
| Cybersécurité (attaque) | Moyenne | Critique | Pen test annuel + SOC managé |
| Cadre légal télémédecine non adopté | Élevée | Moyen | V3.3 conditionnée à adoption loi |

---

## 7. Gouvernance

### 7.1 Comité de pilotage V3.0

Présidé par le Directeur de Cabinet du Ministre, réuni trimestriellement :
- DSI Ministère
- DPO
- RSSI
- Directeur Médical (CHU Donka)
- Représentant OMS Guinée
- Représentant équipe technique GuinéeCare

### 7.2 Revue technique mensuelle

Présidée par le DSI, ouverte à l'équipe technique :
- Avancement des lots
- Blocages identifiés
- Décisions d'architecture

### 7.3 Rétrospective trimestrielle

Ouverte à toute l'équipe, format agile :
- Ce qui a bien fonctionné
- Ce qui peut être amélioré
- Actions concrètes pour le trimestre suivant

---

## 8. Indicateurs de succès V3.0

| Indicateur | Cible fin 2027 |
|------------|----------------|
| Établissements déployés | ≥ 50 |
| Patients dans la base | ≥ 500 000 |
| Téléconsultations réalisées (V3.3) | ≥ 5 000/an |
| Pushs DHIS2 réussis (V3.2) | ≥ 99 % |
| Praticiens formés via LMS (V3.8) | ≥ 1 000 |
| Disponibilité plateforme | ≥ 99,5 % |
| Latence API p95 | ≤ 500 ms |
| Pays pilotes SaaS (V3.10) | ≥ 1 |

---

## 9. Conclusion

La roadmap V3.0 propose **10 lots** s'étalant sur 12-18 mois, pour un budget d'environ **519 000 € la première année**. Elle vise à transformer GuinéeCare en plateforme de référence africaine, alignée sur les standards internationaux (OMS, HL7, DHIS2) et adaptée aux réalités guinéennes (zones rurales, langues locales, cadre légal en construction).

Les **3 lots prioritaires P1** (V3.1 ICD-11 OMS, V3.2 FHIR/DHIS2 bidir, V3.3 Télémédecine) doivent être engagés dès le T3 2026 pour respecter le calendrier national. Le financement doit être sécurisé dans les meilleurs délais auprès des bailleurs.

La mise en œuvre de cette roadmap fera l'objet d'un **comité de pilotage trimestriel** et d'une **réévaluation annuelle** des priorités en fonction des retours d'usage du terrain.

---

## 10. Validation

| Rôle | Nom | Date | Signature |
|------|-----|------|-----------|
| DSI Ministère | | | |
| Directeur de Cabinet | | | |
| Ministre de la Santé | | | |
| Représentant OMS Guinée | | | |
| Lead dev GuinéeCare | | | |
