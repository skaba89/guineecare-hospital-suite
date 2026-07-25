# Scénario Démo Bout-en-Bout — GuinéeCare Hospital Suite

**Version :** v2.4.0 (Phase 4)
**Objectif :** Démonstration réaliste du parcours patient complet, de l'arrivée à la sortie avec documents PDF
**Durée :** 30-45 min
**Public :** Ministère, directeurs d'hôpital, partenaires ONG, clients potentiels

## Prérequis

- ✅ Instance démo accessible : `https://guineecare.onrender.com`
- ✅ Compte démo : `admin@guineecare.com` / `admin123` (SUPER_ADMIN)
- ✅ Données seed chargées (50 patients, 20 établissements)
- ✅ Navigateur Chrome/Edge récent
- ✅ Connexion Internet stable

## Scénario : Mme Aminata Diallo, 28 ans, fièvre + douleurs abdominales

### Étape 1 — Accueil et tableau de bord (2 min)

1. Login en tant que `admin@guineecare.com` / `admin123`
2. **Montrer le tableau de bord :**
   - 8 KPIs : patients, admissions, urgences, hospitalisés, lits dispo, examens en attente, alertes, rapports
   - Graphique admissions 7 derniers jours
   - Pie chart occupation des lits
   - Timeline flux patients temps réel
   - Alertes prioritaires
3. **Pointer :** le caractère temps réel (les KPIs se mettent à jour via WebSocket)

### Étape 2 — Création du patient Mme Diallo (3 min)

1. Menu **Patients** → bouton **Nouveau**
2. Remplir :
   - Prénom : Aminata
   - Nom : Diallo
   - Sexe : F
   - Date naissance : 15/03/1997 (28 ans)
   - Téléphone : +224 622 33 44 55
   - Adresse : Hamdallaye, Conakry
   - Groupe sanguin : O+
   - Allergies : Pénicilline
3. Valider — **patient_number auto-généré** affiché (ex: PAT-202607051230-abc123)

### Étape 3 — Admission aux urgences (5 min)

1. Menu **Urgences** → **File d'attente**
2. **Cliquer "Nouveau patient urgence"**
3. Sélectionner Mme Diallo + motif : "Fièvre 38.5°C + douleurs abdominales"
4. Valider — la visite apparaît dans la file d'attente avec statut **WAITING**

5. **Triage** (onglet Triage) :
   - Niveau de priorité : **P3** (Urgent — atteinte modérée)
   - Constantes vitales : TA 120/80, FC 95, T° 38.5, FR 18, SpO2 98%
   - Valider → statut passe à **TRIAGED**

6. **Prise en charge** (clic sur la visite) :
   - Médecin : Dr Diallo
   - Notes : "Examen abdominal — défense à la palpation de la FID"
   - Traitement : "Antispasmodique + antipyrétique"
   - Valider → statut **IN_CARE**

### Étape 4 — Consultation et prescription (5 min)

1. Menu **Patients** → rechercher "Diallo Aminata" → clic
2. Onglet **Clinical** → **Nouvelle consultation**
3. Type : CONSULTATION
4. Contenu : "Suspicione appendicite aiguë. À réévaluer après bilan biologique."
5. Valider

6. **Prescription** (depuis le dossier patient) :
   - Type : PRESCRIPTION
   - Contenu : "Paracétamol 1g x3/jour, Bilan NFS + CRP + Amylase"
   - Valider

### Étape 5 — Demande laboratoire (5 min)

1. Menu **Laboratoire** → **Nouvelle commande**
2. Patient : Mme Diallo
3. Test : NFS (Numération Formule Sanguine)
4. Priorité : **URGENT**
5. Valider

6. Répéter avec CRP et Amylase (3 commandes séparées)
7. **Statut des demandes** : menu **Labo** → onglet **Stats**
   - Montrer : count_by_status (3 ORDERED), urgent_pending_count (3)

8. **Prélèvement** (rôle labo) :
   - Se déconnecter, reconnecter en `lab.sow@chu-donka.gn` / `lab123`
   - Onglet **Commandes** → clic sur une commande → **Prélever**
   - Sample ID auto-généré : SAM-XXXX
   - Statut : SAMPLE_COLLECTED

9. **Saisie résultat** :
   - Cliquer **Saisir résultat**
   - Valeur : "Leucocytes 12.5 G/L"
   - Valider → statut RESULT_ENTERED

10. **Validation biologique** :
    - Cliquer **Valider** → statut VALIDATED
    - Le résultat est désormais officiel et imprimable

### Étape 6 — Dispensation pharmacie (3 min)

1. Se déconnecter, reconnecter en `ph.cisse@chu-donka.gn` / `pharma123`
2. Menu **Pharmacie** → **Dispenser**
3. Sélectionner :
   - Patient : Mme Diallo
   - Produit : Paracétamol 500mg
   - Quantité : 10
   - Reason : "Selon prescription Dr Diallo"
4. Valider → **remaining_stock** affiché (ex: 90)
5. **Vérifier l'historique** : menu **Pharmacie** → **Dispensations**
   - La dispensation apparaît avec patient_id lié

6. **Alertes pharmacie** : menu **Pharmacie** → **Alertes**
   - Montrer low_stock_count (produits en rupture)
   - Montrer near_expiry_count (péremptions proches)

7. **Valorisation stock** : menu **Pharmacie** → **Valorisation**
   - total_stock_value_gnf affiché (ex: 5 250 000 GNF)

### Étape 7 — Facturation et paiement (5 min)

1. Se déconnecter, reconnecter en `ca.diallo@chu-donka.gn` / `cashier123`
2. Menu **Facturation** → **Nouvelle facture**
3. Patient : Mme Diallo
4. Description : "Consultation urgences + bilan biologique + médicaments"
5. Montant net : 150 000 GNF
6. Valider → **invoice_number** auto-généré

7. **Tableau de bord caisse** : menu **Facturation** → **Dashboard**
   - revenue_today affiché
   - outstanding_total affiché
   - count_by_status (1 ISSUED)

8. **Paiement partiel** :
   - Cliquer sur la facture → **Paiement**
   - Montant : 80 000 GNF
   - Mode : CASH
   - Valider → statut PARTIALLY_PAID, balance_due = 70 000 GNF

9. **Reçu PDF** :
   - Cliquer **Reçu PDF** sur le paiement
   - Le PDF s'ouvre : n° reçu, facture, montant payé, solde restant
   - Mention "Document généré électroniquement par GuinéeCare"

### Étape 8 — Clôture du passage urgence (2 min)

1. Reconnecter en `admin@guineecare.com`
2. Menu **Urgences** → trouver Mme Diallo (statut IN_CARE)
3. Cliquer **Sortie**
4. Destination : **HOME** (retour à domicile)
5. Compte rendu : "Patient vu, bilan en cours, traitement antalgique. Reconsultation si aggravation."
6. Valider → statut **DISCHARGED**

### Étape 9 — Historique patient (3 min)

1. Menu **Patients** → Mme Diallo → onglet **Historique**
2. **Timeline agrégée** affichée :
   - Admission urgence
   - Note consultation
   - Prescription
   - 3 demandes laboratoire
   - Facture
   - Paiement partiel
   - Sortie urgence
3. Chaque événement est cliquable et détaillé

### Étape 10 — Documents PDF (5 min)

1. **Prescription PDF** : clic sur la prescription → **PDF**
2. **Résultat laboratoire PDF** : clic sur un résultat validé → **PDF**
3. **Facture PDF** : clic sur la facture → **PDF**
4. **Reçu de paiement PDF** : déjà fait en étape 7

Tous les PDFs ont :
- En-tête avec nom établissement
- Numéro de document unique
- Date émission
- Mentions légales OHADA
- Pied de page "Document généré par GuinéeCare"

### Étape 11 — Vue nationale (2 min)

1. Menu **Pilotage national** (réservé SUPER_ADMIN)
2. **Vue multi-établissements** :
   - Carte/répartition des établissements
   - Indicateurs agrégés
   - Alertes sanitaires
3. Menu **Reporting** :
   - Rapports nationaux (soumission, validation)
   - Statistiques de santé
   - Alertes épidémiologiques

### Étape 12 — Sécurité et conformité (3 min)

1. Menu **Audit** :
   - Toutes les actions sont tracées (login, patient.read, prescription.create, etc.)
   - IP + User-Agent + timestamp pour chaque action
   - Filtre par utilisateur, action, date
2. Menu **Rôles & Permissions** :
   - 8 rôles, 50+ permissions
   - Matrice RBAC complète
3. Menu **Utilisateurs** :
   - 2FA activable par utilisateur
   - Désactivation = invalidation immédiate des tokens

## Récapitulatif — ce qui a été démontré

| # | Étape | Endpoint(s) utilisés | Document généré |
|---|-------|---------------------|-----------------|
| 1 | Tableau de bord | GET /dashboard (via pages) | — |
| 2 | Création patient | POST /patients | — |
| 3 | Admission urgence | POST /emergency/visits + triage + care | — |
| 4 | Consultation + prescription | POST /clinical/patients/{id}/notes | — |
| 5 | Demande labo + prélèvement + validation | POST /laboratory/orders + /collect + /results + /validate | PDF résultat labo |
| 6 | Dispensation pharmacie | POST /pharmacy/dispense | — |
| 7 | Facturation + paiement | POST /billing/invoices + /payments | PDF facture + PDF reçu |
| 8 | Clôture urgence | POST /emergency/visits/{id}/discharge | — |
| 9 | Historique patient | GET /patients/{id}/history | — |
| 10 | Documents PDF | GET /documents/* | 4 PDFs |
| 11 | Vue nationale | GET /national + /reporting | — |
| 12 | Sécurité/audit | GET /audit + /rbac + /users | — |

## Points clés à insister

- ✅ **Workflow complet bout-en-bout** : patient arrive, est admis, consulté, reçoit prescription, passe labo + pharmacie, paie, sort avec PDFs
- ✅ **Traçabilité totale** : chaque action est auditée (PHI access log)
- ✅ **Multi-rôles** : 4 rôles différents ont été utilisés (admin, doctor, lab_tech, pharmacist, cashier)
- ✅ **Isolation multi-tenant** : chaque établissement ne voit que ses données
- ✅ **Documents PDF professionnels** : prescription, résultat labo, facture, reçu
- ✅ **Tableaux de bord métier** : caisse, labo stats, urgences indicateurs, pharmacy alerts
- ✅ **Alertes intelligentes** : stock pharmacie (ruptures + péremptions), urgences (temps d'attente)
- ✅ **Conformité OHADA** : mentions légales, numérotation factures

## Anticipation questions

| Question | Réponse |
|----------|---------|
| "Combien de temps pour former le personnel ?" | 1-2 jours par établissement (fiches par rôle) |
| "Fonctionne hors-ligne ?" | Oui (app mobile React Native + offline sync) |
| "Intégration DHIS2 ?" | Phase 5 — prévu (export SNIS) |
| "SMS pour rappels RDV ?" | Oui (Orange/MTN/Moov Guinée) |
| "Multilingue ?" | FR + EN |
| "Hébergement ?" | SaaS Render/Neon, VPS, ou on-premise hôpital |
| "Sécurité données médicales ?" | 2FA, RBAC, audit trail, isolation tenant, TLS, HSTS, CSP |
| "Coût ?" | SaaS 30-50 USD/mois, on-premise 500-1500 USD investissement |
| "Maintenance ?" | Documentation complète + runbook + formation |

## En cas de problème pendant la démo

- **Instance lente** (Render free tier sleep) : attendre 30s ou rafraîchir
- **Erreur 429** (rate limit) : attendre 1 min (5 logins/min)
- **Page blanche** : F5, sinon Ctrl+Shift+R
- **Backup plan** : captures d'écran préparées (voir `docs/deploiement/CHECKLIST_DEMO.md`)

## Voir aussi

- `docs/deploiement/CHECKLIST_DEMO.md` — Checklist démo détaillée
- `docs/presentation/scenario-demo-ministere.md` — Scénario Ministère
- `docs/deploiement/guide-utilisateur-rapide.md` — Guide utilisateurs
- `docs/securite/MATRICE_RBAC_v2.2.md` — Matrice RBAC
