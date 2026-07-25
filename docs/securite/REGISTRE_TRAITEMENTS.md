# Registre des Traitements — GuinéeCare Hospital Suite

**Conformément au RGPD (Article 30)**

---

## 1. Identité du responsable du traitement

| Champ | Valeur |
|-------|--------|
| **Nom** | [Établissement de santé] |
| **Représentant** | [Directeur] |
| **DPO** | [À nommer] |
| **Contact** | [email / téléphone] |

---

## 2. Traitements enregistrés

### Traitement T-001 : Gestion du dossier patient informatisé

| Champ | Valeur |
|-------|--------|
| **Finalité** | Gestion du dossier médical patient |
| **Base légale** | Art. 9(2)(h) RGPD — soins de santé |
| **Données** | Identité, contact, données de santé, données financières |
| **Durée conservation** | 20 ans après dernier contact |
| **Destinataires** | Personnel soignant, administrateurs |
| **Transferts hors UE** | Render (USA/EU), Neon (AWS) — à évaluer |
| **Mesures sécurité** | TLS, JWT+2FA, RBAC, multi-tenant, audit log |

### Traitement T-002 : Gestion des admissions et urgences

| Champ | Valeur |
|-------|--------|
| **Finalité** | Admission, triage, orientation, sortie |
| **Base légale** | Art. 9(2)(h) RGPD |
| **Données** | Identité, motif d'admission, triage, soins |
| **Durée conservation** | 20 ans |
| **Destinataires** | Personnel soignant |
| **Mesures sécurité** | RBAC, multi-tenant, audit log |

### Traitement T-003 : Laboratoire et imagerie

| Champ | Valeur |
|-------|--------|
| **Finalité** | Demandes d'examens, résultats, validation |
| **Base légale** | Art. 9(2)(h) RGPD |
| **Données** | Résultats biologiques, comptes rendus radiologiques |
| **Durée conservation** | 20 ans |
| **Destinataires** | Laborantins, médecins |
| **Mesures sécurité** | RBAC, multi-tenant, audit log |

### Traitement T-004 : Pharmacie et dispensation

| Champ | Valeur |
|-------|--------|
| **Finalité** | Gestion stock, dispensation médicamenteuse |
| **Base légale** | Art. 9(2)(h) RGPD |
| **Données** | Prescriptions, dispensations, stock |
| **Durée conservation** | 10 ans (pharmacovigilance) |
| **Destinataires** | Pharmaciens |
| **Mesures sécurité** | Row locks, audit log, masquage champs médicaux |

### Traitement T-005 : Facturation et paiements

| Champ | Valeur |
|-------|--------|
| **Finalité** | Facturation, encaissement, reçus |
| **Base légale** | Obligation légale (OHADA) |
| **Données** | Factures, paiements, solde |
| **Durée conservation** | 10 ans (OHADA) |
| **Destinataires** | Caissiers, administrateurs |
| **Mesures sécurité** | Row locks, audit log |

### Traitement T-006 : Pilotage sanitaire national

| Champ | Valeur |
|-------|--------|
| **Finalité** | Indicateurs agrégés, reporting SNIS/DHIS2 |
| **Base légale** | Obligation légale (SNIS) |
| **Données** | **Agrégats anonymisés uniquement** (pas de PHI) |
| **Durée conservation** | Indéfinie (statistiques) |
| **Destinataires** | Ministère de la Santé, DSIS, ONG |
| **Mesures sécurité** | Anonymisation, pas de données nominatives |

### Traitement T-007 : Audit et traçabilité

| Champ | Valeur |
|-------|--------|
| **Finalité** | Journal d'audit médico-légal |
| **Base légale** | Obligation légale |
| **Données** | IP, user-agent, actions, timestamps, user_id |
| **Durée conservation** | 5 ans |
| **Destinataires** | DPO, auditeurs |
| **Mesures sécurité** | Append-only, pas de modification/suppression |

### Traitement T-008 : Authentification et gestion des accès

| Champ | Valeur |
|-------|--------|
| **Finalité** | Login, 2FA, refresh token, logout |
| **Base légale** | Intérêt légitime (sécurité) |
| **Données** | Email, mot de passe (haché), 2FA secret, refresh tokens |
| **Durée conservation** | Durée de l'emploi + 30 jours (tokens) |
| **Destinataires** | Système (pas d'accès humain) |
| **Mesures sécurité** | bcrypt, TOTP, jti blacklist, rate limiting |

---

## 3. Sous-traitants

| Sous-traitant | Traitement | Pays | Garanties |
|---------------|------------|------|-----------|
| **Render** | Hébergement application | USA/EU | CGU, chiffrement TLS |
| **Neon** | Base de données PostgreSQL | AWS (multi-région) | TLS, chiffrement disque |
| **Cloudflare** | CDN / proxy | Global | Conforme RGPD |

---

## 4. Transferts hors UE

| Destination | Données | Mesure de protection |
|-------------|---------|---------------------|
| Render (USA/EU) | Toutes données | Chiffrement TLS en transit |
| Neon/AWS (multi-région) | Base de données | TLS + chiffrement disque |
| **Évaluation** | À évaluer pour hébergement local Guinée ou pays adéquat |

---

*Document à tenir à jour en cas de modification des traitements.*
