# Analyse d'Impact relative à la Protection des Données (AIPD)
# GuinéeCare Hospital Suite — Article 35 RGPD

**Version :** 1.0
**Date :** Juillet 2026
**Responsable :** [À compléter — DPO désigné]
**Référence :** Règlement UE 2016/66 (RGPD), Article 35
**Loi nationale :** Loi guinéenne sur la protection des données (à venir)

---

## 1. Description du traitement

### 1.1 Identité du responsable du traitement
- **Nom :** Ministère de la Santé de la République de Guinée / Établissement de santé exploitant
- **Contact DPO :** [À compléter]
- **Représentant :** [À compléter]

### 1.2 Finalités du traitement
GuinéeCare Hospital Suite traite des données de santé à des fins de :
1. **Gestion du dossier patient informatisé** (DPI) — démographie, antécédents, allergies, groupe sanguin
2. **Suivi clinique** — consultations, prescriptions, constantes vitales, diagnostics
3. **Gestion hospitalière** — admissions, urgences, hospitalisation, maternité, bloc opératoire
4. **Laboratoire et imagerie** — demandes, résultats, validation biologique
5. **Pharmacie** — stock, dispensation, alertes ruptures/péremptions
6. **Facturation** — factures, paiements, reçus
7. **Pilotage sanitaire national** — indicateurs agrégés anonymisés, reporting SNIS/DHIS2
8. **Audit et traçabilité** — journal d'audit des accès aux données de santé

### 1.3 Base légale
- **Article 9(2)(h) RGPD** : traitement nécessaire aux fins de la médecine préventive, du diagnostic médical, de la fourniture de soins de santé ou de traitement
- **Consentement** du patient pour le traitement de ses données de santé (recueilli à l'admission)
- **Obligation légale** pour le reporting SNIS (Système National d'Information Sanitaire)

---

## 2. Données traitées

### 2.1 Catégories de données
| Catégorie | Données | Sensibilité |
|-----------|---------|-------------|
| **Identité** | Nom, prénom, date de naissance, sexe | Personnelles |
| **Contact** | Téléphone, adresse | Personnelles |
| **Identifiants** | Numéro patient, numéro d'identité nationale, numéro d'assurance | Personnelles |
| **Données de santé** | Groupe sanguin, allergies, antécédents médicaux, médicaments, maladies chroniques | **Catégorie spéciale (Article 9)** |
| **Cliniques** | Consultations, prescriptions, diagnostics (CIM-10), constantes vitales | **Catégorie spéciale** |
| **Laboratoire** | Résultats d'analyses biologiques | **Catégorie spéciale** |
| **Imagerie** | Comptes rendus radiologiques | **Catégorie spéciale** |
| **Maternité** | Suivi grossesse, accouchements, nouveau-nés | **Catégorie spéciale** |
| **Financières** | Factures, paiements, solde dû | Personnelles |
| **Authentification** | Email, mot de passe (haché), 2FA | Personnelles |
| **Audit** | Journal d'audit (IP, user-agent, actions, timestamps) | Personnelles |

### 2.2 Destinataires
| Destinataire | Données | Finalité |
|---------------|---------|----------|
| Personnel soignant (médecins, infirmiers, sages-femmes) | Dossier patient complet | Soins |
| Pharmaciens | Données démographiques + prescriptions | Dispensation |
| Laborantins | Données démographiques + demandes labo | Analyses |
| Caissiers | Données démographiques + factures | Encaissement |
| Administrateurs établissement | Toutes données (sauf champs médicaux masqués pour non-cliniques) | Gestion |
| Super-admin national | Données agrégées anonymisées | Pilotage |
| Ministère de la Santé / DSIS | Indicateurs agrégés SNIS | Reporting national |
| Hébergeur (Render/Neon) | Toutes données chiffrées en transit | Infrastructure |

---

## 3. Évaluation des risques

### 3.1 Risques identifiés

| # | Risque | Probabilité | Gravité | Mesures existantes | Risque résiduel |
|---|--------|-------------|---------|---------------------|-----------------|
| 1 | Accès non autorisé aux données de santé | Moyenne | Élevée | RBAC + multi-tenant + audit log | Faible |
| 2 | Fuite de données (intrusion) | Faible | Élevée | TLS + headers sécurité + 2FA | Faible |
| 3 | Accès cross-tenant (établissement A voit établissement B) | Faible | Élevée | tenant_query + enforce_facility_access + tests | Très faible |
| 4 | Perte de données (panne DB) | Faible | Élevée | Backup quotidien + vérification | Très faible |
| 5 | Divulgation par employé malveillant | Moyenne | Élevée | Audit log + masquage champs médicaux | Faible |
| 6 | Réidentification à partir d'agrégats nationaux | Faible | Moyenne | Agrégats seulement (pas de PHI) | Très faible |
| 7 | Vol de session (token JWT) | Faible | Élevée | 2FA + jti blacklist + last_disabled_at | Faible |
| 8 | Brute-force mot de passe | Moyenne | Moyenne | Lockout 5 échecs + rate limit + politique 12 chars | Très faible |
| 9 | Attaque par déni de service | Moyenne | Moyenne | Rate limiting + nginx | Faible |
| 10 | Faille injection SQL | Faible | Élevée | SQLAlchemy ORM (pas de SQL raw) | Très faible |

### 3.2 Risque lié à l'hébergement
- **Render (USA/EU)** + **Neon PostgreSQL (AWS)** : données hébergées hors de Guinée
- **Mesure** : évaluer la possibilité d'un hébergement local ou dans un pays à niveau de protection adéquat
- **Mitigation** : chiffrement TLS en transit, AUTH_SECRET pour JWT, backups chiffrés

---

## 4. Mesures de sécurité

### 4.1 Mesures techniques
| Mesure | Implémentation | Statut |
|--------|----------------|--------|
| Chiffrement en transit | TLS 1.2/1.3 (nginx + Neon) | ✅ |
| Authentification forte | JWT + 2FA TOTP + refresh rotation | ✅ |
| Contrôle d'accès | RBAC 8 rôles + 59 permissions | ✅ |
| Isolation multi-tenant | tenant_query + enforce_facility_access | ✅ |
| Journal d'audit | audit_logs sur tous les actes médicaux | ✅ |
| Masquage données sensibles | Champs médicaux masqués pour non-cliniques | ✅ |
| Rate limiting | login 5/min, 2FA 5/user/5min, refresh 30/min | ✅ |
| Headers sécurité | HSTS, CSP, X-Frame-Options, Permissions-Policy | ✅ |
| Politique mot de passe | 12+ chars, majuscule, minuscule, chiffre, spécial | ✅ |
| Lockout compte | 5 échecs → verrouillage 15 min | ✅ |
| Row locks | SELECT FOR UPDATE (pharmacie, facturation) | ✅ |
| Anonymisation reporting | Agrégats seulement (pas de PHI) | ✅ |
| Droits patients | Rectification, effacement, portabilité | ✅ |
| Registre violations | Table data_breaches + notification 72h | ✅ |

### 4.2 Mesures organisationnelles
| Mesure | Statut |
|--------|--------|
| DPO désigné | ⚠️ À nommer |
| Registre des traitements | ⚠️ À compléter |
| Notice d'information patient | ⚠️ À diffuser |
| Formation du personnel | ⚠️ À planifier |
| Procédure notification violation 72h | ✅ Endpoint /audit/breaches |
| Tests de pénétration | ⚠️ À programmer |
| Audit interne annuel | ⚠️ À planifier |

---

## 5. Charte des droits des patients

| Droit | Implémentation | Endpoint |
|-------|----------------|----------|
| Droit d'accès (Art. 15) | GET /patients/{id} + GET /patients/{id}/export | ✅ |
| Droit de rectification (Art. 16) | PUT /patients/{id} | ✅ |
| Droit à l'effacement (Art. 17) | DELETE /patients/{id} (soft-delete + anonymisation) | ✅ |
| Droit à la portabilité (Art. 20) | GET /patients/{id}/export (JSON) | ✅ |
| Droit d'opposition (Art. 21) | ⚠️ Procédure manuelle via DPO | — |
| Droit à la limitation (Art. 18) | ⚠️ À implémenter (gel de dossier) | — |

---

## 6. Conclusion

Le traitement de données de santé par GuinéeCare Hospital Suite présente un **risque résiduel faible** grâce aux mesures techniques implémentées. Les mesures organisationnelles restantes (DPO, formation, pen test) doivent être mises en place avant le déploiement national.

**Recommandation :** Autoriser le traitement sous réserve de la désignation d'un DPO, de la réalisation d'un pen test externe, et de la diffusion de la notice d'information patient.

---

*Document à valider par le DPO et le responsable du traitement.*
