# Procédure d'appel d'offres — Test d'intrusion externe

**Projet :** GuinéeCare Hospital Suite
**Version :** 1.0 — Modèle à compléter
**Référence :** Cahier des charges `CAHIER_DES_CHARGES_PEN_TEST_v1.md`
**Maître d'ouvrage :** Ministère de la Santé de la République de Guinée
**Maître d'œuvre :** Prestataire à sélectionner

---

## 1. Objet de l'appel d'offres

Le Ministère de la Santé de la République de Guinée lance un appel d'offres en vue de la sélection d'un prestataire spécialisé pour réaliser un **test d'intrusion externe indépendant** de la plateforme hospitalière nationale GuinéeCare Hospital Suite.

Ce test d'intrusion constitue un prérequis P0 au déploiement national flagship de la plateforme, conformément aux recommandations de l'audit expert réalisé en juin 2026.

---

## 2. Calendrier prévisionnel

| Étape | Date cible | Description |
|-------|------------|-------------|
| Publication de l'appel d'offres | S+0 | Publication sur le portail des marchés publics |
| Visite de site / réunion d'information | S+1 | Optionnelle — pour les candidats intéressés |
| Date limite de soumission des offres | S+3 | 17h00 GMT, Conakry |
| Ouverture des plis | S+3 (J+1) | Séance publique |
| Évaluation technique et financière | S+4 à S+5 | Commission d'évaluation |
| Notification d'attribution | S+6 | Au prestataire retenu |
| Signature du contrat + NDA | S+7 | Avec le prestataire retenu |
| Kickoff du test d'intrusion | S+8 | Réunion de démarrage |
| Phase de tests | S+8 à S+12 | 5 semaines de tests |
| Restitution et rapport | S+13 | Présentation des résultats |
| Atelier de correction | S+14 | Avec l'équipe technique GuinéeCare |
| Correction des P0 | S+15 à S+17 | Par l'équipe technique |
| Re-test | S+18 | Par le prestataire |
| Rapport final et go/no-go national | S+19 | Décision Ministre |

---

## 3. Conditions de participation

### 3.1 Éligibilité du prestataire

Pour être admis à soumissionner, le prestataire doit :

1. **Être enregistré légalement** en Guinée, dans un État membre de la CEDEAO, ou dans un État membre de l'UE.
2. **Disposer des certifications** suivantes :
   - ANSSI (visée de qualification) ou équivalent européen (CREST, OSCP)
   - Au moins 3 ans d'expérience en tests d'intrusion d'applications web et mobiles
3. **Justifier d'une expérience sectorielle** : au moins 2 références en tests d'intrusion d'applications de santé (SIH, DMP, télémédecine) ou de plateformes traitant des données sensibles (RGPD Article 9).
4. **Ne pas avoir de conflit d'intérêts** avec :
   - L'équipe de développement de GuinéeCare
   - Les fournisseurs d'infrastructure (Render, Neon, AWS)
   - Les fournisseurs de la stack technique (FastAPI, React, etc.)
5. **Accepter de signer un NDA** (Non-Disclosure Agreement) avant tout accès aux documents et environnements.

### 3.2 Capacités techniques requises

Le prestataire devra mettre à disposition une équipe de **2 à 3 auditeurs** avec les compétences suivantes :

- **Lead auditor** : 5+ ans d'expérience, certification OSCP ou équivalent
- **Auditeur senior** : 3+ ans d'expérience, familiarité avec OWASP WSTG
- **Auditeur mobile** (optionnel) : expérience React Native / Android / iOS

L'équipe devra être francophone (les livrables doivent être rédigés en français).

### 3.3 Capacités matérielles

Le prestataire devra disposer de :
- Outils professionnels (Burp Suite Pro, OWASP ZAP, Nuclei, Nmap, SQLMap, MobSF, Frida)
- Environnement de test isolé (pas de tests depuis des adresses IP personnelles)
- Capacité à générer des rapports PDF professionnels

---

## 4. Contenu de l'offre

L'offre doit comprendre les éléments suivants, dans l'ordre indiqué :

### 4.1 Lettre de soumission

- Identification du prestataire (raison sociale, adresse, contacts)
- Identification du signataire autorisé
- Référence de l'appel d'offres
- Date de soumission

### 4.2 Références

Au moins **3 références** de tests d'intrusion similaires réalisés dans les 5 dernières années, avec pour chacune :
- Client (secteur santé recommandé)
- Nature du test (web, mobile, API, infrastructure)
- Périmètre fonctionnel
- Durée
- Montant du marché (facultatif mais recommandé)
- Contact de référence (nom, email, téléphone) — avec autorisation préalable

### 4.3 Méthodologie détaillée

Le prestataire devra proposer une **note méthodologique** (10 à 20 pages) décrivant :
- Approche retenue (boîte noire, grise, blanche — les 3 sont attendues)
- Outils qui seront utilisés
- Phases du test (reconnaissance, scan, exploitation, post-exploitation, reporting)
- Traçabilité des actions (journal d'audit des tests)
- Mesures de sécurité prises pendant le test (pas d'exfiltration de données réelles, pas de DoS, etc.)
- Gestion des incidents (procédure si vulnérabilité critique découverte)
- Format du rapport final

### 4.4 Équipe proposée

CV détaillé de chaque auditeur :
- Formation et certifications
- Expérience (années, types de missions)
- Références personnelles
- Rôle dans la mission

### 4.5 Planning détaillé

Calendrier précis des 5 semaines de tests, avec :
- Répartition des phases (reconnaissance, tests manuels, etc.)
- Points de synchronisation avec l'équipe GuinéeCare
- Date de livraison du rapport préliminaire
- Date de la restitution orale

### 4.6 Offre financière

Tableau détaillé des coûts :
- Forfait tests (5 semaines) : ______ € HT
- Forfait restitution et atelier : ______ € HT
- Forfait re-test (1 semaine, post-correction) : ______ € HT
- Frais de déplacement (si tests sur site) : ______ € HT
- **Total HT** : ______ € HT
- TVA applicable (si applicable) : ______ €
- **Total TTC** : ______ € TTC

Budget indicatif du Ministère : **25 000 € à 50 000 € HT**. Les offres hors budget seront éliminées.

### 4.7 Conformité et éthique

- Engagement de confidentialité (NDA pré-rempli en annexe)
- Engagement d'indépendance
- Engagement à ne pas réutiliser les données de test au-delà de la fin du contrat
- Engagement à signaler toute vulnérabilité critique dans un délai < 1 heure

---

## 5. Critères d'évaluation des offres

Les offres seront évaluées selon les critères pondérés suivants :

| Critère | Poids | Détail |
|---------|-------|--------|
| **Méthodologie proposée** | 30 % | Pertinence, exhaustivité, adaptation au contexte santé |
| **Expérience sectorielle** | 25 % | Références en santé + RGPD Article 9 |
| **Qualifications de l'équipe** | 20 % | Certifications (CREST, OSCP) + expérience |
| **Prix** | 15 % | Offre financière dans le budget indicatif |
| **Références clients** | 10 % | Qualité et pertinence des références fournies |

Note minimale d'éligibilité : **60/100** sur l'ensemble des critères.

---

## 6. Modalités de soumission

### 6.1 Format

Les offres doivent être soumises **en 3 exemplaires papier** + **1 version électronique** (clé USB), sous enveloppe cachetée portant la mention :

```
APPEL D'OFFRES — TEST D'INTRUSION GUINÉECARE
Ne pas ouvrir avant la séance d'ouverture des plis
N° [_______] /MS/CAB/DSI/2026
```

### 6.2 Langue

Les offres doivent être rédigées en **français**. Toute offre en langue étrangère sera éliminée.

### 6.3 Adresse de soumission

```
Ministère de la Santé
Direction des Systèmes d'Information
Cellule des Marchés Publics
BP 585, Conakry, République de Guinée
```

### 6.4 Date et heure limites

**Date limite :** [JJ/MM/AAAA] à **17h00 GMT** (Conakry)
Aucune offre reçue après cette date ne sera examinée.

---

## 7. Communication avec les candidats

### 7.1 Questions des candidats

Les candidats peuvent adresser leurs questions par email à :
**marches-publics@sante.gov.gn**
Objet : « Question — Appel d'offres Pen Test GuinéeCare — Réf [_______] »

Les questions seront recevables jusqu'à **J-7 de la date limite de soumission**. Les réponses seront communiquées à tous les candidats simultanément (anonymat respecté).

### 7.2 Visite d'information (optionnelle)

Une réunion d'information sera organisée à Conakry le **[JJ/MM/AAAA]** à 10h00 GMT, dans les locaux du Ministère de la Santé. La présence est recommandée mais non obligatoire. L'inscription se fait par email.

### 7.3 Modifications de l'appel d'offres

Le Ministère se réserve le droit de modifier l'appel d'offres à tout moment avant la date limite de soumission. Les modifications seront notifiées à tous les candidats ayant manifesté leur intérêt.

---

## 8. Clause de confidentialité

Toutes les informations contenues dans le cahier des charges `CAHIER_DES_CHARGES_PEN_TEST_v1.md` et dans les échanges avec les candidats sont **confidentielles**. Les candidats s'engagent à :

- Ne pas diffuser les informations à des tiers
- Ne pas les utiliser à d'autres fins que la préparation de leur offre
- Les détruire à l'issue de la procédure (sauf si attributaire)

Le non-respect de cette clause entraîne l'élimination immédiate du candidat.

---

## 9. Attribution et signature du contrat

### 9.1 Notification d'attribution

Le candidat retenu sera notifié par courrier officiel dans un délai de **15 jours** après l'évaluation des offres. La notification précisera :
- Le montant du marché attribué
- Les conditions de démarrage
- Les délais d'exécution
- Les modalités de paiement

### 9.2 Contrat

Le contrat sera signé dans les **30 jours** suivant la notification. Il comprendra :

1. Le cahier des charges `CAHIER_DES_CHARGES_PEN_TEST_v1.md` (annexe 1)
2. L'offre technique et financière du prestataire (annexe 2)
3. Le NDA (annexe 3)
4. Les conditions générales d'exécution (annexe 4)

### 9.3 Modalités de paiement

- **40 %** à la commande (signature du contrat)
- **40 %** à la restitution du rapport préliminaire
- **20 %** après re-test et validation finale

Paiement par virement bancaire sur présentation de facture.

---

## 10. Garanties et pénalités

### 10.1 Garantie de bonne exécution

Le prestataire retenu devra fournir une **garantie bancaire** équivalente à 5 % du montant du marché, valable pendant toute la durée d'exécution + 6 mois.

### 10.2 Pénalités de retard

En cas de retard dans la livraison des livrables, des pénalités de **1 % du montant du marché par semaine de retard** seront appliquées, plafonnées à 10 % du montant total.

### 10.3 Résiliation

Le Ministère se réserve le droit de résilier le contrat en cas de :
- Non-respect des délais (au-delà de 4 semaines de retard)
- Non-respect des engagements de confidentialité
- Manquements graves à la méthodologie proposée
- Force majeure

En cas de résiliation, le prestataire est payé pour les prestations effectivement réalisées, déduction faite des pénalités éventuelles.

---

## 11. Annexes

Les annexes suivantes font partie intégrante de l'appel d'offres :

| Annexe | Document | Référence |
|--------|----------|-----------|
| 1 | Cahier des charges pen test | `docs/securite/CAHIER_DES_CHARGES_PEN_TEST_v1.md` |
| 2 | Modèle de NDA | `docs/securite/NDA_PEN_TEST_modele.md` (à préparer) |
| 3 | Architecture technique | `docs/architecture/architecture-generale.md` |
| 4 | Checklist sécurité existante | `docs/securite/CHECKLIST_CONFORMITE_GUINEE_v2.2.md` |
| 5 | AIPD | `docs/securite/AIPD_v1.md` |
| 6 | Registre des traitements | `docs/securite/REGISTRE_TRAITEMENTS.md` |
| 7 | Matrice RBAC | `docs/securite/MATRICE_RBAC_v2.2.md` |

---

## 12. Contact

Pour toute question relative à cet appel d'offres :

| Rôle | Email | Téléphone |
|------|-------|-----------|
| Maître d'ouvrage | cabinet@sante.gov.gn | +224 [à compléter] |
| Cellule marchés publics | marches-publics@sante.gov.gn | +224 [à compléter] |
| DSI Ministère | dsi@sante.gov.gn | +224 [à compléter] |
| RSSI | rssi@sante.gov.gn | +224 [à compléter] |
| DPO | dpo@sante.gov.gn | +224 [à compléter] |

---

## Validation de la procédure

| Rôle | Nom | Date | Signature |
|------|-----|------|-----------|
| DSI Ministère | | | |
| Cellule marchés publics | | | |
| RSSI | | | |
| DPO | | | |
| Ministre de la Santé | | | |

---

> ⚠️ **Note** : Cette procédure est un **modèle** à adapter à la réglementation des marchés publics guinéens (Code des marchés publics de la République de Guinée, décret n° [à compléter]). Faire valider par la Direction Juridique du Ministère avant publication.
