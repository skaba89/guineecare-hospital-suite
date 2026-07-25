# DPO — Désignation, charte et fiche de poste

**Projet :** GuinéeCare Hospital Suite
**Version :** 1.0
**Date :** Juillet 2026
**Référence :** RGPD (Règlement UE 2016/679), Articles 37, 38, 39
**Loi nationale :** Loi guinéenne sur la protection des données à caractère personnel (Loi L/2022/018/AN, à compléter par le décret d'application)

---

## 1. Désignation du DPO

### 1.1 Obligation légale

Conformément à l'**Article 37 du RGPD**, la désignation d'un Délégué à la Protection des Données (DPO) est **obligatoire** pour GuinéeCare Hospital Suite, car l'activité principale du responsable du traitement consiste en un **traitement à grande échelle de données de santé** (Article 9 — données sensibles).

Cette obligation est confirmée par la loi guinéenne L/2022/018/AN qui transpose le RGPD dans le droit national et exige un correspondant à la protection des données pour les traitements publics de données sensibles.

### 1.2 Identité du DPO désigné

> ⚠️ À compléter formellement par arrêté du Ministre de la Santé.

| Champ | Valeur |
|-------|--------|
| **Nom et prénom** | [À compléter] |
| **Fonction administrative** | [À compléter — ex: Directeur des Systèmes d'Information du Ministère de la Santé] |
| **Email professionnel** | dpo@sante.gov.gn |
| **Téléphone** | +224 [à compléter] |
| **Adresse postale** | Ministère de la Santé, BP 585, Conakry, République de Guinée |
| **Date de prise de fonction** | [JJ/MM/AAAA] |
| **Date de fin de mandat** | [JJ/MM/AAAA — mandat de 5 ans renouvelable] |
| **Référence de l'arrêté** | [Numéro et date de l'arrêté ministériel] |

### 1.3 Critères de désignation (Article 37.5 RGPD)

Le DPO désigné respecte les critères suivants :
- **Expertise professionnelle** en matière de protection des données et de pratiques de sécurité informatique (formation RGPD certifiante ou équivalent).
- **Indépendance** — le DPO n'a pas de conflit d'intérêts avec ses autres fonctions et ne reçoit d'instructions hiérarchiques concernant l'exercice de ses missions (Article 38.3 RGPD).
- **Absence de conflit d'intérêts** — le DPO ne peut pas occuper simultanément une fonction qui le placerait en situation de déterminer les finalités et les moyens du traitement (ex: DSI, Directeur Médical).
- **Ressources suffisantes** — le Ministère s'engage à fournir au DPO les ressources nécessaires (formation continue, accès aux locaux et systèmes, temps de travail dédié).

### 1.4 Modalités de signalement à l'autorité de contrôle

Le DPO est **officiellement notifié** à l'autorité guinéenne de protection des données (Autorité de Régulation des Télécommunications — ARPT, division protection des données) dans un délai de **30 jours** après sa désignation, conformément à l'article 37.7 du RGPD.

Les coordonnées du DPO sont également publiées sur le site public du Ministère de la Santé et accessibles depuis l'application GuinéeCare (page "Mentions légales" → "Protection des données").

---

## 2. Charte du DPO

### 2.1 Missions (Article 39 RGPD)

Le DPO a pour missions principales :

1. **Information et conseil** — informer et conseiller le responsable du traitement (Ministère de la Santé) et les sous-traitants (équipe technique GuinéeCare) de leurs obligations RGPD.
2. **Veille et audit interne** — surveiller l'application du RGPD, des politiques de protection des données et de la loi guinéenne L/2022/018/AN.
3. **Conseil sur l'AIPD** — conseiller le responsable du traitement et mener l'Analyse d'Impact relative à la Protection des Données (Article 35 RGPD), en cohérence avec le document `AIPD_v1.md` déjà produit.
4. **Coopération avec l'autorité de contrôle** — servir de point de contact privilégié pour l'ARPT et faciliter ses interventions.
5. **Gestion des violations** — assurer le signalement des violations de données à l'ARPT dans les **72 heures** suivant leur découverte (Article 33 RGPD), en coordination avec le responsable sécurité.
6. **Information des personnes** — servir de point de contact pour les patients et le personnel concernant leurs droits RGPD (accès, rectification, effacement, portabilité, opposition).

### 2.2 Indépendance et hiérarchie

Le DPO **rapporte directement** au Ministre de la Santé et n'est soumis à aucune hiérarchie intermédiaire dans l'exercice de ses missions (Article 38.3 RGPD). Il ne peut pas être **sanctionné, rétrogradé ou licencié** en raison de l'exercice de ses missions (Article 38.3 RGPD).

Le DPO peut saisir directement l'autorité de contrôle s'il constate une violation grave du RGPD non corrigée par le responsable du traitement.

### 2.3 Confidentialité et secret professionnel

Le DPO est soumis au **secret professionnel** pour toutes les informations dont il a connaissance dans l'exercice de ses missions, y compris après la fin de son mandat. Cette obligation est inscrite dans son acte de nomination.

### 2.4 Ressources et moyens

Le Ministère de la Santé met à la disposition du DPO :
- **Temps dédié** — minimum 50% de son temps de travail consacré aux missions DPO (Article 38.2 RGPD).
- **Budget formation** — formation continue RGPD et cybersécurité, minimum 5 jours par an.
- **Accès aux systèmes** — accès en lecture au registre des traitements, au journal d'audit (via le module `/audit/logs`), aux AIPD, aux procédures de sécurité.
- **Équipe** — possibilité de désigner des correspondants RGPD dans chaque établissement pilote (CHU Donka, CHU Ignace Deen, etc.).

### 2.5 Liaison avec l'équipe technique GuinéeCare

Le DPO travaille en étroite collaboration avec :
- Le **RSSI** (Responsable de la Sécurité des Systèmes d'Information) pour les aspects techniques (tests d'intrusion, journalisation, sauvegardes).
- Le **DSI** du Ministère pour les choix d'architecture et de sous-traitance (Render, Neon, etc.).
- Le **référent métier** (Directeur Médical) pour la compréhension des flux cliniques.
- L'**équipe dev** GuinéeCare pour l'implémentation des mesures techniques (RBAC, 2FA, audit log, anonymisation).

---

## 3. Fiche de poste

### 3.1 Intitulé

**Délégué à la Protection des Données (DPO) — GuinéeCare Hospital Suite**

### 3.2 Rattachement hiérarchique

- **Supervision directe** : Ministre de la Santé
- **Liaison fonctionnelle** : DSI du Ministère, RSSI, Directeur Médical
- **Liaison externe** : ARPT (autorité de contrôle), CNIL (en cas de transferts hors UE)

### 3.3 Missions détaillées

#### Mission 1 — Conformité RGPD et loi nationale (30% du temps)

- Maintenir à jour le **registre des traitements** (document `REGISTRE_TRAITEMENTS.md`).
- Mettre à jour les **AIPD** pour chaque nouveau traitement ou modification substantielle (`AIPD_v1.md`).
- Valider les **notices d'information patient** (`NOTICE_PATIENT.md`) et s'assurer de leur accessibilité.
- Vérifier la conformité des **transferts internationaux** (Render/USA, Neon/AWS, sous-traitants cloud).
- Préparer les **dossiers d'autorisation** préalable auprès de l'ARPT pour les traitements sensibles (données de santé à grande échelle).

#### Mission 2 — Gestion des droits des patients (20% du temps)

- Traiter les demandes d'**exercice de droits** (accès, rectification, effacement, portabilité, opposition) dans les délais légaux (1 mois).
- Coordonner avec les équipes métier pour la mise en œuvre technique des droits (export patient via API FHIR, anonymisation, suppression).
- Maintenir un **registre des demandes** de droits et leur traitement.

#### Mission 3 — Gestion des violations de données (15% du temps)

- Définir et maintenir le **plan de gestion des incidents** (détection, qualification, notification).
- En cas de violation avérée, notifier l'ARPT dans les **72 heures** (Article 33 RGPD).
- Notifier les personnes concernées si la violation présente un **risque élevé** pour leurs droits et libertés (Article 34 RGPD).
- Tenir un **registre des violations** (table `data_breaches` déjà implémentée dans le backend GuinéeCare).

#### Mission 4 — Sensibilisation et formation (15% du temps)

- Élaborer et animer des **sessions de formation** à destination du personnel soignant et administratif.
- Maintenir des **supports de sensibilisation** affichés dans les établissements.
- Intégrer un **module RGPD** dans le parcours d'onboarding des nouveaux utilisateurs GuinéeCare.

#### Mission 5 — Audit interne et veille (10% du temps)

- Réaliser des **audits internes annuels** sur l'application du RGPD.
- Assurer une **veille réglementaire** (évolution du RGPD, lois guinéennes, recommandations ARPT).
- Participer aux **revues de code** sensibles (authentification, journalisation, anonymisation).

#### Mission 6 — Liaison avec l'autorité de contrôle (10% du temps)

- Servir de **point de contact** à l'ARPT pour toute question ou contrôle.
- Préparer les **réponses aux demandes** de l'autorité de contrôle.
- Faciliter les **visites de contrôle** sur site.

### 3.4 Compétences requises

#### Compétences juridiques
- Maîtrise du **RGPD** et de la **loi guinéenne L/2022/018/AN**.
- Connaissance du **secret médical** et des règles spécifiques aux données de santé (Article 9 RGPD).
- Connaissance des **conventions internationales** (Convention 108+ du Conseil de l'Europe).

#### Compétences techniques
- Compréhension des **architectures cloud** (IaaS, PaaS, SaaS) et des enjeux de sous-traitance.
- Connaissance des **mesures de sécurité** technique (chiffrement, RBAC, journalisation, MFA).
- Lecture de **spécifications API** et de **schémas de bases de données**.

#### Compétences relationnelles
- **Pédagogie** pour expliquer les enjeux RGPD aux équipes métier et techniques.
- **Diplomatie** pour faire respecter les obligations sans bloquer les projets.
- **Éthique** et **indépendance** (Article 38.3 RGPD).

### 3.5 Indicateurs d'activité (KPI)

Le DPO rapporte annuellement au Ministre de la Santé et à l'ARPT les indicateurs suivants :

| Indicateur | Cible 2026 |
|------------|------------|
| Demandes d'exercice de droits traitées < 30 jours | 100% |
| Violations notifiées à l'ARPT < 72h | 100% |
| Sessions de formation dispensées | ≥ 4 par an |
| Audits internes réalisés | ≥ 1 par an |
| AIPD mises à jour | ≥ 1 par an |
| Personnel formé RGPD | ≥ 80% du personnel soignant |
| Revues de code sensibles participation | 100% |

---

## 4. Lettre de nomination (modèle)

```
RÉPUBLIQUE DE GUINÉE
Travail — Justice — Solidarité

MINISTÈRE DE LA SANTÉ
Cabinet du Ministre

N° _______/MS/CAB/2026

ARRÊTÉ PORTANT DÉSIGNATION DU DÉLÉGUÉ À LA PROTECTION
DES DONNÉES DU PROJET GUINÉECARE HOSPITAL SUITE

LE MINISTRE DE LA SANTÉ,

Vu le Règlement UE 2016/679 dit "RGPD", notamment ses articles 37 à 39 ;
Vu la loi L/2022/018/AN du [date] sur la protection des données à caractère
personnel en République de Guinée, notamment son article [X] ;
Vu le décret [n°] portant organisation du Ministère de la Santé ;
Vu l'arrêté [n°] portant création du projet GuinéeCare Hospital Suite ;

ARRÊTE

Article 1er : Est désigné Délégué à la Protection des Données (DPO) du
projet GuINÉECARE HOSPITAL SUITE, Monsieur/Madame [NOM PRÉNOM],
[grade/fonction], en poste au Ministère de la Santé.

Article 2 : Le DPO exerce les missions prévues par l'article 39 du RGPD
et par la charte annexée au présent arrêté. Il rapporte directement au
Ministre de la Santé et bénéficie de l'indépendance prévue par l'article
38.3 du RGPD.

Article 3 : Le DPO est désigné pour une durée de CINQ (5) ans, renouvelable,
à compter de la date de notification du présent arrêté.

Article 4 : Le DPO est notifié à l'Autorité de Régulation des
Télécommunications (ARPT) dans un délai de 30 jours conformément à
l'article 37.7 du RGPD.

Article 5 : Le présent arrêté est publié au Journal Officiel de la
République de Guinée.

Conakry, le [JJ/MM/AAAA]

[Signature]
Le Ministre de la Santé
```

---

## 5. Plan de mise en œuvre

### Étape 1 — Désignation (semaine 1-2)
- [ ] Identifier le candidat (interne Ministère ou recrutement externe)
- [ ] Vérifier l'absence de conflit d'intérêts
- [ ] Rédiger l'arrêté ministériel de désignation
- [ ] Faire valider par le Secrétariat Général du Gouvernement

### Étape 2 — Notification (semaine 3)
- [ ] Notifier l'ARPT dans les 30 jours
- [ ] Publier les coordonnées du DPO sur le site du Ministère
- [ ] Afficher les coordonnées dans les établissements pilotes

### Étape 3 — Prise de fonction (mois 1-3)
- [ ] Formation RGPD certifiante (5 jours minimum)
- [ ] Prise de connaissance des documents existants : AIPD, registre des traitements, notice patient
- [ ] Audit initial de l'application GuinéeCare (modules, RBAC, journalisation)
- [ ] Première session de sensibilisation du personnel

### Étape 4 — Période de rodage (mois 3-6)
- [ ] Mise en place du registre des demandes de droits
- [ ] Premiers retours d'expérience et ajustement des procédures
- [ ] Premier rapport d'activité au Ministre

### Étape 5 — Régime de croisière (à partir du mois 6)
- [ ] Audits internes annuels
- [ ] Sessions de formation trimestrielles
- [ ] Revue annuelle de l'AIPD

---

## 6. Références

- **RGPD** : Règlement (UE) 2016/679 du Parlement européen et du Conseil du 27 avril 2016
- **Loi guinéenne L/2022/018/AN** : Loi relative à la protection des données à caractère personnel en République de Guinée
- **Convention 108+** : Convention du Conseil de l'Europe pour la protection des personnes à l'égard du traitement automatisé des données à caractère personnel (modernisée)
- **Lignes directrices du CEPD** : sur les DPO (WP243 rev.01)
- **Documents internes** :
  - `AIPD_v1.md` — Analyse d'Impact relative à la Protection des Données
  - `REGISTRE_TRAITEMENTS.md` — Registre des traitements
  - `NOTICE_PATIENT.md` — Notice d'information patient
  - `CHECKLIST_CONFORMITE_GUINEE_v2.2.md` — Checklist conformité

---

## 7. Validation

| Rôle | Nom | Date | Signature |
|------|-----|------|-----------|
| DPO désigné | [À compléter] | JJ/MM/AAAA | |
| DSI Ministère | [À compléter] | JJ/MM/AAAA | |
| Ministre de la Santé | [À compléter] | JJ/MM/AAAA | |
| Représentant ARPT (accusé de réception) | [À compléter] | JJ/MM/AAAA | |
