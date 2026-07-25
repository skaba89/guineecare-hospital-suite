# Checklist Démo — GuinéeCare Hospital Suite

**Version :** v2.3.0 (Phase 8)
**Usage :** À valider AVANT chaque démo (Ministère, partenaire, client, formation)

## T-24h : Préparation

### Données de démonstration
- [ ] Instance démo accessible : `https://guineecare.onrender.com` (ou votre instance)
- [ ] Données seed chargées (50 patients, 20 établissements, etc.)
- [ ] Comptes démo fonctionnels (tester chaque compte) :
  - [ ] `admin@guineecare.com` / `admin123` (SUPER_ADMIN)
  - [ ] `dr.diallo@chu-donka.gn` / `doctor123` (DOCTOR)
  - [ ] `inf.konde@chu-donka.gn` / `nurse123` (NURSE)
  - [ ] `sf.bah@chu-donka.gn` / `midwife123` (MIDWIFE)
  - [ ] `ph.cisse@chu-donka.gn` / `pharma123` (PHARMACIST)
  - [ ] `lab.sow@chu-donka.gn` / `lab123` (LAB_TECH)
  - [ ] `ca.diallo@chu-donka.gn` / `cashier123` (CASHIER)
  - [ ] `admin.facility@chu-donka.gn` / `admin123` (ADMIN)
- [ ] Patients de démo réalistes (noms guinéens, données cohérentes)

### Scénario de démo
- [ ] Scénario écrit et imprimé (`docs/presentation/scenario-demo-ministere.md`)
- [ ] Durée estimée : 30-45 min (pas plus)
- [ ] Points clés à montrer :
  - [ ] Login + tableau de bord (impression visuelle)
  - [ ] Création patient + admission (parcours complet)
  - [ ] Consultation + prescription (rôle médecin)
  - [ ] Dispensation pharmacie (rôle pharmacien)
  - [ ] Saisie résultat labo (rôle labo)
  - [ ] Encaissement paiement (rôle caissier)
  - [ ] Impression PDF (prescription, facture, résultat)
  - [ ] Tableau de bord national (rôle SUPER_ADMIN)
  - [ ] Audit log (conformité)
  - [ ] Multi-établissement (isolation tenant)

## T-1h : Vérifications techniques

### Connectivité
- [ ] Instance démo accessible depuis le réseau de la démo
- [ ] WiFi / 4G de secours testé
- [ ] Vidéoprojecteur / écran testé
- [ ] Navigateur à jour (Chrome / Edge recommandé)

### Performance
- [ ] Page de login charge en < 3s
- [ ] Tableau de bord charge en < 5s
- [ ] Création patient en < 3s
- [ ] Pas d'erreur 500 dans les logs

### Sécurité
- [ ] ⚠️ **Ne PAS montrer les comptes démo à l'audience** (sauf si démo technique)
- [ ] Préparer un compte avec données fictives pour la démo live
- [ ] Désactiver l'autocomplétion mot de passe navigateur

## T-5min : Pré-finalisation

- [ ] Onglets ouverts et prêts :
  - Tab 1 : Login page
  - Tab 2 : Tableau de bord (login admin déjà fait)
  - Tab 3 : Liste patients
  - Tab 4 : Dossier patient (pré-ouvert)
  - Tab 5 : Reporting national
- [ ] Captures d'écran de backup (en cas de panne réseau pendant la démo)
- [ ] Présentation PowerPoint prête (`docs/presentation/`)
- [ ] Documents à distribuer imprimés :
  - [ ] Brochure GuinéeCare (1 page A4)
  - [ ] Guide utilisateur rapide (2 pages)
  - [ ] Carte de visite / contact

## Pendant la démo

### Déroulé recommandé (30 min)

| Temps | Section | Action |
|-------|---------|--------|
| 0-2 min | Introduction | Présentation GuinéeCare, contexte Guinée |
| 2-5 min | Architecture | Stack technique, modes de déploiement (SaaS/on-premise) |
| 5-10 min | Tableau de bord | KPIs, alertes, flux temps réel |
| 10-15 min | Parcours patient | Création → admission → consultation → prescription |
| 15-20 min | Pharmacie + Labo | Dispensation + saisie résultat + validation |
| 20-25 min | Facturation | Facture → paiement → reçu PDF |
| 25-28 min | Reporting national | Vue multi-établissements, alertes sanitaires |
| 28-30 min | Sécurité + conformité | RBAC, audit, 2FA, isolation tenant |

### Points à insister

- ✅ **Sécurité :** 2FA, RBAC, audit trail, isolation multi-tenant
- ✅ **Simplicité :** Interface en français, adaptée au contexte guinéen
- ✅ **Faible connectivité :** Fonctionne avec 3G, offline-ready (mobile)
- ✅ **Conformité :** Audit log, masquage données sensibles (Phase 7)
- ✅ **Coût :** Mode SaaS dès 30 USD/mois, mode on-premise dès 500 USD investissement
- ✅ **Autonomie :** Documentation en français, formation 1-2 jours

### Anticiper les questions

| Question type | Réponse préparée |
|---------------|------------------|
| "Combien ça coûte ?" | Voir `docs/presentation/dossier-ministere-sante.md` — offres par client |
| "Hébergement où ?" | SaaS Render/Neon, cloud privé VPS, ou on-premise hôpital |
| "Sécurité données ?" | 2FA, RBAC, audit, isolation tenant, TLS, backup chiffré |
| "Formation ?" | 1-2 jours par établissement, fiches par rôle, supports en français |
| "Intégration DHIS2 ?" | Phase 5 — prévu, export SNIS |
| "SMS ?" | Orange/MTN/Moov Guinée, routing par catégorie |
| "Mobile ?" | App React Native (Android APK), offline sync |
| "Multilingue ?" | FR (par défaut) + EN |

## T+5min : Post-démo

- [ ] Collecter les retours (formulaire papier ou Google Form)
- [ ] Distribuer la documentation :
  - Brochure
  - Guide utilisateur rapide
  - Carte de visite
- [ ] Programmer un envoi de compte-rendu sous 24h
- [ ] Noter les engagements (pilote, date, périmètre)
- [ ] Mettre à jour le CRM / fichier prospects

## Cas de panne réseau pendant la démo

1. **Garder son calme** — basculer sur captures d'écran
2. Présentation PowerPoint avec captures haute résolution
3. Vidéo pré-enregistrée du parcours (si disponible)
4. Si retour réseau : reprendre en live

## Voir aussi
- `docs/presentation/scenario-demo-ministere.md` — Scénario détaillé
- `docs/presentation/dossier-ministere-sante.md` — Dossier commercial
- `docs/presentation/checklist-demo-rdv.md` — Checklist rendez-vous
- `docs/deploiement/guide-utilisateur-rapide.md` — À distribuer
