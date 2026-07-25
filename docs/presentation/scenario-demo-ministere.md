# Scénario de démonstration — Ministère de la Santé de Guinée

> Durée : 10 minutes
> Public : Ministre de la Santé + conseillers techniques
> Objectif : Démontrer la valeur opérationnelle de GuinéeCare sur un parcours patient complet

---

## Préparation (avant l'arrivée du Ministre)

### Setup technique
- [ ] Backend démarré sur http://localhost:8000 avec SEED_DEMO_DATA=true
- [ ] Frontend démarré sur http://localhost:5173
- [ ] Navigateur en plein écran (F11) — masquer la barre d'URL
- [ ] Zoom à 110% pour meilleure lisibilité sur projecteur
- [ ] Onglets préparés : Dashboard | Patients | Urgences | Laboratoire | Qualité | Facturation
- [ ] Compte admin connecté : `admin@guineecare.com` / `admin123`
- [ ] Vérifier que le toggle FR/EN fonctionne
- [ ] Imprimer ce scénario en guise de antisèche

### Données de démo pré-chargées
Le seed crée automatiquement :
- 20 établissements (CHU Donka, CHU Ignace Deen, HGR régionaux, CSI Conakry)
- 38 utilisateurs (médecins, infirmiers, sages-femmes, pharmaciens, lab techs, caissiers)
- 50 patients avec dossiers complets
- Admissions, résultats labo, imagerie, factures, paiements

---

## Scénario scripté (10 minutes)

### Étape 1 — Accueil & Vue d'ensemble (1 min 30)

**Action** : Ouvrir le Dashboard (page d'accueil après login)

**Narration** :
> "Monsieur le Ministre, voici GuinéeCare — la plateforme hospitalière nationale pour la Guinée. Cet écran est le tableau de bord temps réel. On y voit en un coup d'œil : le nombre de patients actifs, les admissions en cours, les lits occupés, et les urgences en traitement."

**Points clés à souligner** :
- Les chiffres s'actualisent en direct (WebSocket) — montrer le badge "🟢 Connecté" en haut
- KPIs : patients, admissions, lits, urgences
- Tâches en attente : résultats labo à valider, imagerie en attente
- Recettes du jour et créances impayées

**Si on demande "est-ce que c'est en temps réel ?"** :
> "Oui, la connexion WebSocket en haut à droite montre 🟢. Quand un médecin valide un résultat labo, ce compteur se met à jour automatiquement sans rafraîchir la page."

---

### Étape 2 — Création d'un nouveau patient (1 min 30)

**Action** : Cliquer sur "Patients" dans la sidebar → bouton "Nouveau patient"

**Narration** :
> "Un patient se présente pour la première fois au CHU Donka. Le personnel d'accueil crée son dossier en moins de 30 secondes."

**Saisir** :
- Prénom : **Mariame**
- Nom : **Sow**
- Date de naissance : **1990-03-15**
- Genre : ♀ Féminin
- Téléphone : **+224 622 33 44 55**
- Groupe sanguin : **O+**
- Allergies : **Pénicilline**
- Autres champs : laisser "Non renseigné"

**Cliquer "Créer"**

**Points clés** :
- Le numéro patient est généré automatiquement (PAT-AAAAMMJJHHMMSS)
- Les champs médicaux ont des valeurs par défaut "Non renseigné" — le soignant complète plus tard
- Le dossier est immédiatement accessible

---

### Étape 3 — Admission aux urgences + triage (2 min)

**Action** : Aller dans "Urgences" → créer un passage aux urgences pour Mariame Sow

**Narration** :
> "La patiente se présente aux urgences du CHU Donka avec des douleurs abdominales. Le personnel crée un passage aux urgences et procède au triage."

**Saisir** :
- Patient : **Mariame Sow** (rechercher dans le dropdown)
- Motif : **Douleurs abdominales aiguës**
- Niveau de triage : **Niveau 3 — Urgent** (orange)

**Points clés** :
- Le triage couleur (niveaux 1-5) suit les standards internationaux
- Le patient apparaît automatiquement dans la file d'attente des urgences
- Le médecin de garde reçoit une notification

---

### Étape 4 — Demande de laboratoire + résultat critique (2 min)

**Action** : Aller dans "Laboratoire" → créer une demande → saisir un résultat critique

**Narration** :
> "Le médecin suspecte une appendicite. Il demande une prise de sang. Le laborantin reçoit la demande, analyse, et saisit le résultat."

**Créer la demande** :
- Patient : Mariame Sow
- Test : **Hémogramme / NFS**
- Priorité : **URGENT**

**Saisir le résultat** :
- Valeur : **18.5** (globules blancs élevés — signe d'infection)
- Interprétation : **CRITIQUE** (leucocytose élevée)

**Points clés** :
- Le résultat est marqué "CRITIQUE" → déclenche automatiquement :
  1. Une notification au médecin prescripteur
  2. Un SMS si configuré (expliquer que l'intégration Orange/MTN/Moov est prête)
  3. Une alerte dans le dashboard qualité

---

### Étape 5 — Tableau de bord qualité + alerte (1 min 30)

**Action** : Aller dans "Qualité" → onglet "Dashboard"

**Narration** :
> "GuinéeCare ne se contente pas de gérer les patients — il pilote la qualité des soins. Voici le dashboard qualité avec 10 indicateurs OMS et HAS pré-configurés."

**Cliquer "🔔 Check seuils"**

**Points clés** :
- Les indicateurs OMS (infections nosocomiales, taux de mortalité, satisfaction patient) sont pré-chargés
- Le système détecte automatiquement les dépassements de seuils
- Chaque alerte a un cycle de vie : Ouverte → Prise en charge → Résolue → Clos
- Le Ministère peut suivre la qualité des soins dans tous les établissements en temps réel

---

### Étape 6 — Facturation + reçu PDF (1 min 30)

**Action** : Aller dans "Facturation" → créer une facture pour Mariame Sow

**Narration** :
> "Après consultation et examens, la patiente passe à la caisse. Le système génère la facture avec le détail des actes."

**Créer la facture** :
- Patient : Mariame Sow
- Lignes :
  - Consultation urgences : 50 000 GNF
  - Prise de sang (NFS) : 25 000 GNF
- Total : 75 000 GNF

**Encaisser le paiement** :
- Montant : 75 000 GNF
- Mode : Espèces

**Cliquer "PDF"** sur la facture → le PDF s'ouvre dans un nouvel onglet

**Points clés** :
- Facture détaillée avec en-tête de l'établissement
- Reçu PDF imprimable (utile pour les pharmaciens d'officine)
- Traçabilité complète : qui a facturé, qui a encaissé, quand
- Audit log de chaque transaction

---

### Étape 7 — Bilinguisme FR/EN (30 secondes)

**Action** : Cliquer sur le toggle 🇫🇷/🇬🇧 en haut à droite

**Narration** :
> "La plateforme est entièrement bilingue français/anglais, pour accueillir le personnel soignant anglophone formé au Libéria, Sierra Leone ou Ghana, et pour les rapportages internationaux."

**Basculer en EN** → montrer que la sidebar, le dashboard, les titres changent

**Revenir en FR**

---

## Anticiper les questions du Ministre

### "Combien ça coûte ?"
> "Le développement est réalisé. Les coûts restants sont : hébergement cloud (~200 000 GNF/mois), formation des agents (~5 millions GNF pour 200 agents), et l'intégration SMS opérateur (~25 GNF/SMS). Soit un TCO annuel d'environ 30 millions GNF pour un établissement — contre 0 aujourd'hui avec le papier."

### "Est-ce que ça fonctionne sans internet ?"
> "Oui. Le mode hors-ligne PWA permet de continuer à saisir les admissions et constantes vitales même en cas de coupure. Les données sont synchronisées au retour du réseau. L'app mobile Android a également un mode offline avec file d'attente."

### "Combien de temps pour déployer dans tous les CHU ?"
> "Le pilote au CHU Donka prend 2 mois (formation + déploiement + ajustements). Ensuite, le déploiement régional (8 HGR + 20 CSI) prend 6 mois, à raison de 2 établissements par mois. Soit 8 mois au total pour la couverture nationale des structures publiques."

### "Et la sécurité des données médicales ?"
> "Authentification JWT avec RBAC (8 rôles), isolation multi-tenant par établissement, audit log de chaque action, chiffrement des credentials SMS. Un audit OWASP Top 10 est prévu avant le pilote."

### "Qui maintient le code ?"
> "Le code est documenté et versionné sur GitHub. Une équipe de 2 développeurs peut maintenir et faire évoluer la plateforme. Les coûts de maintenance sont minimes comparés à un SIH commercial (qui coûte 50-100 millions GNF/an en licences)."

---

## Ce qu'il NE FAUT PAS faire pendant la démo

1. ❌ **Ne pas montrer le code** — le Ministre veut voir le produit, pas la technique
2. ❌ **Ne pas montrer l'app mobile** — sauf si APK testé sur device réel avant
3. ❌ **Ne pas parler de "première version" ou "prototype"** — dire "plateforme" ou "solution"
4. ❌ **Ne pas montrer les logs backend** — même si un conseiller technique le demande
5. ❌ **Ne pas basculer entre les onglets trop vite** — laisser le temps de voir chaque écran
6. ❌ **Ne pas improviser** — suivre ce script à la lettre

## En cas de bug pendant la démo

1. **Ne pas paniquer** — dire "laissez-moi rafraîchir" (F5)
2. **Si le backend plante** — dire "le serveur redémarre automatiquement, 10 secondes"
3. **Si une page blanche** — Ctrl+Shift+R (hard refresh)
4. **Si login expiré** — se reconnecter rapidement sans commenter

## Après la démo

- Remettre le dossier de présentation (document séparé `dossier-ministere-sante.md`)
- Mentionner les prochaines étapes : pilote CHU Donka, formation, déploiement régional
- Demander une lettre d'engagement pour le pilote
