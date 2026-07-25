# Guide utilisateur — Nouveautés v2.9.2

**À destination de :** SUPER_ADMIN, ADMIN, DSI, DPO
**Version :** 1.0 — Juillet 2026
**Durée de lecture :** 10 minutes

Ce guide présente les nouvelles fonctionnalités introduites dans la version 2.9.2 de GuinéeCare Hospital Suite, et comment les utiliser au quotidien.

---

## 1. Mode sombre 🌙

### 1.1 Activer le mode sombre

Le bouton de bascule du mode sombre se trouve dans la **barre supérieure** (topbar), à côté de l'indicateur de connexion temps réel et du sélecteur de langue.

```
┌─────────────────────────────────────────────────────────────┐
│ ☰  Tableau de bord         ● Temps réel  🌙  🌐 FR  │
└─────────────────────────────────────────────────────────────┘
```

- Cliquez sur **🌙** pour passer en mode sombre
- Cliquez sur **☀️** pour revenir en mode clair
- La préférence est **mémorisée** entre les sessions (localStorage)
- Au premier chargement, le thème suit votre préférence système (`prefers-color-scheme`)

### 1.2 Avantages du mode sombre

- **Confort oculaire** dans les environnements peu éclairés (gardes de nuit, salles de radiologie)
- **Économie d'énergie** sur les écrans OLED/AMOLED
- **Lisibilité préservée** : tous les contrastes ont été vérifiés (WCAG AA)

### 1.3 Comportement attendu

| Élément | Mode clair | Mode sombre |
|---------|------------|-------------|
| Fond principal | Gris clair (#f8fafc) | Bleu nuit (#0f172a) |
| Cartes | Blanc | Bleu foncé (#1e293b) |
| Texte principal | Noir (#1e293b) | Blanc cassé (#f1f5f9) |
| Bouton primaire | Vert Guinée (#0f6b3e) | Vert clair (#4ade80) |
| Liens | Bleu (#2563eb) | Bleu clair (#60a5fa) |

### 1.4 Que faire si le mode sombre ne s'applique pas ?

1. **Videz le cache** : Ctrl+Shift+R (ou Cmd+Shift+R sur Mac)
2. **Videz le localStorage** : ouvrir DevTools (F12) → Console → `localStorage.clear()` → recharger
3. **Vérifiez votre navigateur** : Chrome/Edge/Firefox récents supportent les variables CSS
4. **Contactez le support** si le problème persiste : tech@guineecare.gn

---

## 2. Tâches planifiées ⚙️

### 2.1 Accéder à la page

La page **Tâches planifiées** est accessible depuis la sidebar, section **SYSTÈME** :

```
┌──────────────────────┐
│ SYSTÈME              │
│ ├ Utilisateurs       │
│ ├ Rôles & Permissions│
│ ├ Établissements     │
│ ├ Départements       │
│ ├ Audit              │
│ ├ SMS Admin          │
│ └ Tâches planifiées  │ ← nouvelle entrée v2.9.2
└──────────────────────┘
```

> ⚠️ Réservé aux rôles **SUPER_ADMIN** et **ADMIN**. Les autres rôles ne voient pas cette entrée.

### 2.2 Comprendre le tableau de bord

La page affiche 3 indicateurs en haut :

| Indicateur | Signification |
|------------|---------------|
| **Worker Celery** | Actif = le worker Celery tourne (recommandé). Synchrone (fallback) = les tâches s'exécutent dans le processus API (mode dégradé). |
| **Broker Redis** | Configuré = `REDIS_URL` est présente. Non configuré = Redis absent (les tâches tournent quand même en mode synchrone). |
| **Tâches disponibles** | Nombre de tâches planifiées (5 en standard). |

### 2.3 Les 5 tâches disponibles

| Tâche | Description | Planification | Risque |
|-------|-------------|---------------|--------|
| 🗑️ **Purge audit log** | Supprime les entrées audit_logs > 365 jours (RGPD) | Quotidien 03h UTC | ⚠️ Destructive |
| 💾 **Backup database** | Dump PostgreSQL + rotation 30 jours | Quotidien 04h UTC | Sécuritaire |
| 📤 **Retry SMS pending** | Re-tente l'envoi des SMS en échec (24h max) | 5 minutes | Sécuritaire |
| 📊 **Push DHIS2 mensuel** | Pousse le dataset DHIS2 du mois précédent | 5 du mois 06h UTC | Sécuritaire |
| 🚨 **Digest qualité** | Envoie un digest des alertes qualité aux admins | Quotidien 06h30 UTC | Sécuritaire |

### 2.4 Déclencher une tâche manuellement

1. Cliquez sur le bouton **▶ Exécuter maintenant** de la tâche choisie
2. Une **boîte de confirmation** s'affiche (surtout pour les tâches destructives)
3. Pour certaines tâches, un **prompt** demande un paramètre :
   - `prune_audit_logs` : rétention en jours (défaut 365)
   - `push_dhis2_monthly` : période YYYYMM (défaut = mois précédent)
4. Cliquez sur **OK** pour confirmer
5. Le résultat s'affiche dans la carte (en vert si succès)

### 2.5 Consulter l'historique

Le tableau en bas de page affiche les **20 dernières exécutions** (issues du journal d'audit) :

| Colonne | Description |
|---------|-------------|
| Date | Horodatage de l'exécution |
| Tâche | Nom convivial de la tâche |
| Statut | ✓ 200 (succès) ou ✗ 4xx/5xx (échec) |
| Détails | Paramètres passés (JSON tronqué) |

### 2.6 Bonnes pratiques

- **Prune audit log** : à déclencher **hors heures ouvrées** (la nuit) car la purge peut prendre plusieurs minutes sur un gros volume
- **Backup database** : peut être déclenché à tout moment — non bloquant pour l'application
- **Push DHIS2 mensuel** : vérifier que les credentials DHIS2 sont configurés avant (sinon mode dry-run)
- **Retry SMS pending** : à déclencher après une panne réseau ou un incident SMS provider

### 2.7 Mode dégradé (sans Celery)

Si le worker Celery n'est pas disponible (warning orange en haut de page), les tâches s'exécutent **dans le processus de l'API** en mode synchrone. Cela signifie :

- ✅ La tâche s'exécute immédiatement
- ⚠️ La requête HTTP est bloquée pendant l'exécution (peut durer plusieurs secondes)
- ⚠️ Pas de retry automatique en cas d'échec
- ⚠️ Pas de planification cron (il faut déclencher manuellement)

Pour activer le mode asynchrone, contactez la DSI pour configurer Redis + Celery worker.

---

## 3. Recherche ICD-11 🔍

### 3.1 Quand l'utiliser ?

La recherche ICD-11 est disponible dans le **formulaire de diagnostic** d'un patient (page Patient → onglet Diagnostics → Nouveau diagnostic).

Elle permet de trouver rapidement le **code OMS officiel** d'un diagnostic plutôt que de saisir un libellé libre.

### 3.2 Comment rechercher

1. Tapez dans le champ **Diagnostic (recherche ICD-11)** :
   - Un **libellé** : « paludisme », « hypertension », « diabète »
   - Un **code** : « 1F03 », « BA00 »
   - En **français ou anglais** : « malaria », « asthma »
2. Après 300ms (debounce), la liste déroulante affiche les **10 premiers résultats**
3. Naviguez avec les **flèches du clavier** (↑/↓) ou la souris
4. **Enter** ou **clic** pour sélectionner
5. Le code ICD-11 s'affiche en badge bleu sous le champ

### 3.3 Catalogue disponible

Le catalogue embarqué contient **~80 codes** prioritaires pour la pratique guinéenne :

| Catégorie | Exemples de codes |
|-----------|-------------------|
| Maladies transmissibles | Paludisme (1F03, 1F2Z), TB (1B11), VIH (1H0Z), Ebola (1E74), Lassa (1E73) |
| Appareil respiratoire | Pneumonie (CA40), Asthme (CA03), BPCO (CB6Z) |
| Cardiovasculaire | Hypertension (BA00), Insuffisance cardiaque (BB71) |
| Digestif | Appendicite (DA40), Gastro-entérite (DA96), Hépatite B (DC40) |
| Endocrinien | Diabète type 1 (5A11), type 2 (5A1A), Malnutrition (5A90) |
| Grossesse | Prééclampsie (JB02), Hémorragie post-partum (JC24), GEU (JA60) |
| Périnatal | Prématurité (KA8Z), Infection néonatale (KA2Z) |
| Neurologique | AVC ischémique (8B40), Épilepsie (8A20), Migraine (8A00) |
| Santé mentale | Dépression (6A70), Anxiété (6A60), Trouble bipolaire (6A80) |
| Lésions | Fracture crâne (NA0Z), Brûlure (ND1Z), Polytraumatisme (PA60) |

### 3.4 Et si le code n'existe pas ?

Si votre recherche ne retourne aucun résultat :

- Vérifiez l'**orthographe** (le moteur est insensible à la casse mais pas aux fautes)
- Essayez en **anglais** (« malaria » au lieu de « paludisme »)
- Essayez un **terme plus large** (« diabète » au lieu de « diabète type 2 insulinodépendant »)
- Si le code n'est vraiment pas dans le catalogue, vous pouvez **saisir un libellé libre** : tapez simplement le texte sans sélectionner de suggestion. Le champ « Code CIM-10 » restera vide (ce qui est acceptable).

> 📝 Pour une liste exhaustive des 55 000+ codes ICD-11, consultez https://icd.who.int/browse11 — une intégration API officielle est prévue en v3.0.

---

## 4. Vue scroll infini (patients) ♾️

### 4.1 Activer la vue scroll infini

Sur la page **Patients**, un bouton **Vue paginée / Vue scroll infini** permet de basculer entre les deux modes :

```
┌─────────────────────────────────────────────────────────────┐
│ 👥 Patients — Vue scroll infini          [🔍 Recherche]     │
│ 50 patient(s) — 50 chargé(s) · scroll pour en charger plus  │
│                                                  [List Vue] │
└─────────────────────────────────────────────────────────────┘
```

La préférence est **mémorisée** entre les sessions.

### 4.2 Différences avec la vue paginée

| Aspect | Vue paginée | Vue scroll infini |
|--------|-------------|-------------------|
| Navigation | Boutons Précédent/Suivant | Scroll naturel |
| Recherche | Champ + bouton | Champ avec debounce |
| Chargement | Manuel (clic page suivante) | Automatique (200px avant le bas) |
| Saut direct | Possible (numéro de page) | Non (scroll seul) |
| Performance | Constante (20 items/page) | Peut charger beaucoup d'items |
| Idéale pour | Administration, recherche précise | Consultation rapide, parcours |

### 4.3 Quand utiliser quoi ?

- **Vue paginée** : si vous cherchez un patient précis et que vous connaissez sa position approximative dans la liste alphabétique
- **Vue scroll infini** : si vous parcourez les patients pour une revue globale (gardes, audits, statistiques)

### 4.4 Indicateurs visuels

- **Loading…** : chargement de la page suivante en cours (spinner en bas de liste)
- **✓ Tous les patients chargés (50/50)** : vous avez atteint la fin de la liste
- **Clic sur un patient** : ouvre une modale avec le résumé (initiales, âge, téléphone)

---

## 5. Foire aux questions

### Q1. Le mode sombre ne s'applique pas à mon téléphone mobile

**R :** Le mode sombre est disponible uniquement sur l'application **web** (frontend React). L'application mobile (React Native) garde son thème par défaut pour l'instant. Une évolution v3.0 est prévue.

### Q2. Puis-je déclencher plusieurs tâches en parallèle ?

**R :** Oui, en mode Celery async. En mode synchrone (sans worker), les tâches s'exécutent séquentiellement — attendez la fin de l'une avant de déclencher l'autre.

### Q3. La tâche « Push DHIS2 » reste en dry-run

**R :** Le mode dry-run signifie que `DHIS2_URL` n'est pas configurée. Contactez la DSI pour configurer les variables d'environnement `DHIS2_URL`, `DHIS2_USERNAME`, `DHIS2_PASSWORD`. Une fois configurées, le push deviendra effectif.

### Q4. Le catalogue ICD-11 ne contient pas mon diagnostic

**R :** Le catalogue embarqué est volontairement limité aux ~80 codes les plus pertinents pour la Guinée. Pour un diagnostic rare, saisissez un libellé libre. Pour une intégration complète (55 000+ codes), une évolution v3.0 est prévue via l'API officielle OMS.

### Q5. La vue scroll infini charge très lentement

**R :** Le chargement dépend de la latence réseau et du volume de données. Sur une connexion 3G, comptez 1-2 secondes par page de 20 patients. Si c'est trop lent, basculez en vue paginée (qui ne charge qu'une page à la fois).

### Q6. Mes collègues ne voient pas l'entrée « Tâches planifiées »

**R :** Cette entrée est visible uniquement pour les rôles **SUPER_ADMIN** et **ADMIN**. Les DOCTOR, NURSE, PHARMACIST, LAB_TECH et CASHIER ne la voient pas (et ne peuvent pas y accéder même en connaissant l'URL).

---

## 6. Contact et support

- **Bug technique** : tech@guineecare.gn
- **Question fonctionnelle** : DSI du Ministère — dsi@sante.gov.gn
- **Question RGPD** (relatives aux tâches de purge/backup) : dpo@sante.gov.gn
- **Documentation complète** : voir `docs/` dans le dépôt GitHub

---

## 7. Récapitulatif des nouveautés

| Fonctionnalité | Où | Pour qui |
|----------------|-----|----------|
| Mode sombre 🌙 | Topbar (toutes pages) | Tous utilisateurs |
| Tâches planifiées ⚙️ | Sidebar → Système | SUPER_ADMIN, ADMIN |
| Recherche ICD-11 🔍 | Page Patient → Diagnostics | DOCTOR, NURSE, MIDWIFE (rôles cliniques) |
| Vue scroll infini ♾️ | Page Patients | Tous utilisateurs (opt-in) |

Bon usage ! 🚀
