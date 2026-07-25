# Checklist Conformité Données Personnelles — Guinée

**Date :** 2026-07-05
**Référence :** Loi guinéenne sur la protection des données (à venir), recommandations OHADA, RGPD comme référence internationale
**Périmètre :** GuinéeCare Hospital Suite — traitement de données de santé (catégorie spéciale)

## 1. Base légale et finalités

| # | Exigence | Statut | Preuve |
|---|----------|--------|--------|
| 1.1 | Identifier la base légale du traitement | ⚠️ À documenter | Consentement patient (à formaliser) |
| 1.2 | Définir les finalités du traitement | ✅ | `README.md` — gestion hospitalière |
| 1.3 | Limiter la collecte aux données nécessaires | ✅ | Schémas Pydantic — pas de collecte excessive |
| 1.4 | Durée de conservation définie | ⚠️ À définir | Politique de rétention à rédiger |

## 2. Information des patients

| # | Exigence | Statut | Preuve |
|---|----------|--------|--------|
| 2.1 | Notice d'information patient | ❌ À créer | Modèle à inclure dans le dossier patient |
| 2.2 | Mention du DPO / contact | ❌ À créer | À ajouter dans la notice |
| 2.3 | Droit d'accès, rectification, effacement | ⚠️ Partiel | Endpoint `GET /patients/{id}` existe ; pas d'endpoint d'effacement auto |
| 2.4 | Droit d'opposition | ❌ À implémenter | Process manuel à définir |

## 3. Sécurité des données (technique)

| # | Exigence | Statut | Preuve |
|---|----------|--------|--------|
| 3.1 | Chiffrement en transit (HTTPS/TLS) | ✅ | nginx.prod.conf + HSTS header (v2.2.0) |
| 3.2 | Chiffrement au repos | ⚠️ Partiel | Neon PostgreSQL : TLS activé ; chiffrement disque à vérifier |
| 3.3 | Authentification forte | ✅ | JWT + 2FA TOTP + lockout compte |
| 3.4 | Contrôle d'accès basé sur les rôles (RBAC) | ✅ | 8 rôles × 50+ permissions |
| 3.5 | Isolation multi-tenant | ✅ | `tenant_query()` + `enforce_facility_access()` |
| 3.6 | Journalisation des accès (audit trail) | ✅ | `audit_logs` — toutes mutations + accès PHI (v2.2.0) |
| 3.7 | Sauvegarde chiffrée | ✅ | `scripts/backup.sh` — pg_dump format custom |
| 3.8 | Politique de mot de passe | ✅ | 12+ chars + complexité + lockout 5 échecs |
| 3.9 | Rate limiting | ✅ | login 5/min, refresh 30/min, 2FA 10/min |
| 3.10 | Headers de sécurité | ✅ | HSTS + CSP + Permissions-Policy (v2.2.0) |

## 4. Minimisation et masquage des données

| # | Exigence | Statut | Preuve |
|---|----------|--------|--------|
| 4.1 | `password_hash` jamais exposé | ✅ | `User.to_read_dict()` — test `test_security_hardening.py` |
| 4.2 | `totp_secret` / `backup_codes` jamais exposés | ✅ | `UserTwoFactor.to_dict()` |
| 4.3 | Données médicales (blood_type, allergies, etc.) | ⚠️ Partiel | `PatientRead` expose tout à `patient.read` ; à restreindre par rôle en Phase 7 |
| 4.4 | Audit log payload redacted (password) | ✅ | `[REDACTED]` placeholder |
| 4.5 | PII dans audit log (email, patient_number) | ⚠️ Partiel | Visible à ADMIN du même établissement ; à anonymiser si audit.read accordé à d'autres rôles |

## 5. Droits des patients

| # | Exigence | Statut | Preuve |
|---|----------|--------|--------|
| 5.1 | Droit d'accès (art. 15 RGPD-like) | ⚠️ Manuel | Patient doit contacter l'ADMIN pour export de ses données |
| 5.2 | Droit de rectification (art. 16) | ⚠️ Manuel | Via `PUT /patients/{id}` par un soignant autorisé |
| 5.3 | Droit à l'effacement (art. 17) | ⚠️ Partiel | Soft-delete `status=DELETED` — pas d'effacement physique |
| 5.4 | Droit à la limitation (art. 18) | ❌ À implémenter | Process de gel de dossier à définir |
| 5.5 | Portabilité (art. 20) | ⚠️ Partiel | Export PDF existe ; export JSON/CSV à ajouter |
| 5.6 | Droit d'opposition (art. 21) | ❌ À implémenter | Process manuel |

## 6. Violation de données

| # | Exigence | Statut | Preuve |
|---|----------|--------|--------|
| 6.1 | Procédure de notification de violation | ❌ À rédiger | Runbook à compléter |
| 6.2 | Délai de notification (72h) | ❌ À définir | Process interne à établir |
| 6.3 | Registre des violations | ❌ À créer | Table `data_breaches` à ajouter |

## 7. Transferts internationaux

| # | Exigence | Statut | Preuve |
|---|----------|--------|--------|
| 7.1 | Hébergement en Guinée ou pays adéquat | ⚠️ À vérifier | Render (USA/EU) + Neon (AWS) — à évaluer |
| 7.2 | Garanties appropriées | ⚠️ À documenter | CGU Render + Neon à conserver |
| 7.3 | Informations aux patients | ❌ À ajouter | Notice d'information à compléter |

## 8. Étude d'impact (AIPD)

| # | Exigence | Statut | Preuve |
|---|----------|--------|--------|
| 8.1 | AIPD requise (données de santé) | ✅ Requise | À rédiger |
| 8.2 | AIPD réalisée | ❌ À faire | Modèle CNIL/RGPD à adapter |
| 8.3 | Mesures de réduction des risques | ⚠️ Partiel | Voir sections 3 et 4 ci-dessus |

## 9. Gouvernance

| # | Exigence | Statut | Preuve |
|---|----------|--------|--------|
| 9.1 | Désignation d'un DPO | ❌ À faire | À nommer formellement |
| 9.2 | Registre des activités de traitement | ⚠️ Partiel | `audit_logs` couvre les accès ; registre RT documentaire à faire |
| 9.3 | Formation du personnel | ❌ À planifier | Module de formation à créer |
| 9.4 | Audit interne annuel | ❌ À planifier | Première audit à programmer |

## Synthèse

| Catégorie | ✅ Conforme | ⚠️ Partiel | ❌ Manquant |
|-----------|:-----------:|:----------:|:----------:|
| 1. Base légale | 2 | 2 | 0 |
| 2. Information patients | 0 | 1 | 3 |
| 3. Sécurité technique | 8 | 1 | 0 |
| 4. Minimisation | 2 | 2 | 0 |
| 5. Droits patients | 0 | 3 | 3 |
| 6. Violations | 0 | 0 | 3 |
| 7. Transferts | 0 | 2 | 1 |
| 8. AIPD | 1 | 0 | 2 |
| 9. Gouvernance | 0 | 1 | 3 |
| **Total** | **13** | **12** | **15** |

**Score global : 33% conforme**

## Priorités Phase 7

1. **P0 :** AIPD (étude d'impact) + notice d'information patient
2. **P0 :** Procédure de notification de violation (72h)
3. **P1 :** Endpoints droits patients (accès, rectification, effacement, portabilité)
4. **P1 :** Restriction `PatientRead` par rôle (medical fields réservés DOCTOR/NURSE/MIDWIFE)
5. **P1 :** Désignation DPO + registre des traitements
6. **P2 :** Évaluation hébergement Guinée vs international
7. **P2 :** Module de formation personnel

## Références

- **Loi guinéenne :** À venir (projet de loi sur la protection des données)
- **OHADA :** Acte uniforme sur la protection des données (en cours d'adoption)
- **RGPD :** Règlement UE 2016/679 (référence internationale)
- **CNIL France :** Guide données de santé (https://www.cnil.fr/fr/health-data)
- **ISO 27001 :** Système de management de la sécurité de l'information
- **ISO 27799 :** Sécurité de l'information dans la santé

## Voir aussi
- `docs/securite/MATRICE_RBAC_v2.2.md` — Matrice des rôles et permissions
- `docs/securite/auth-rbac.md` — Documentation authentification
- `docs/security/AUDIT_V0.8.0.md` — Audit sécurité v0.8.0
- `backend/tests/test_phase6_security.py` — Tests de régression sécurité Phase 6
