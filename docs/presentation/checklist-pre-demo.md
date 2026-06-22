# Checklist pré-démonstration — Ministre de la Santé

> À cocher dans l'ordre. Ne rien sauter.

## J-7 : Préparation technique

- [ ] **Déployer sur VPS** (DigitalOcean/Hetzner ~20$/mois)
  - [ ] `docker-compose.prod.yml` configuré (PostgreSQL + backend + frontend + nginx)
  - [ ] HTTPS activé (Let's Encrypt / Certbot)
  - [ ] Nom de domaine pointé (ex: `demo.guineecare.gn`)
  - [ ] Tester l'accès depuis un navigateur externe
- [ ] **Sauvegarde DB** testée (`scripts/backup.sh`)
- [ ] **Variables d'environnement production** :
  - [ ] `AUTH_SECRET` généré (64 chars aléatoires, PAS "dev-secret-key")
  - [ ] `ENVIRONMENT=production`
  - [ ] `SEED_DEMO_DATA=false` (ou `true` pour la démo)
  - [ ] `CORS_ORIGINS` limité au domaine de démo

## J-5 : Données de démo

- [ ] **Supprimer et recréer la DB** avec `SEED_DEMO_DATA=true`
- [ ] **Vérifier que le seed passe sans erreur** (tous les ✅ Sections)
- [ ] **Tester le scénario complet** :
  - [ ] Login admin → Dashboard s'affiche avec KPIs
  - [ ] Créer un patient → s'affiche dans la liste
  - [ ] Créer une admission → s'affiche dans les urgences
  - [ ] Trier le patient → niveau de triage correct
  - [ ] Créer une demande labo → s'affiche dans le laboratoire
  - [ ] Saisir un résultat critique → alerte qualité déclenchée
  - [ ] Créer une facture → PDF généré
  - [ ] Encaisser un paiement → statut facture mis à jour
  - [ ] Toggle FR/EN → interface traduite
- [ ] **Captures d'écran** professionnelles (minimum 8) :
  - [ ] Dashboard avec KPIs
  - [ ] Liste patients
  - [ ] Dossier patient détail
  - [ ] Urgences avec triage
  - [ ] Laboratoire avec résultat critique
  - [ ] Dashboard qualité avec alertes
  - [ ] Facture PDF
  - [ ] Toggle FR/EN

## J-3 : SMS (optionnel mais idéal)

- [ ] **Contacter Orange Guinée** (smspro.orange.com) pour compte de test
  - [ ] Obtenir `client_id` + `client_secret`
  - [ ] Configurer dans l'UI : SMS Admin → Providers → Orange
  - [ ] Tester l'envoi d'un SMS de test
- [ ] **Si Orange indisponible** : utiliser le provider Mock et expliquer que l'intégration est "prête, en attente des credentials opérateur"

## J-2 : App mobile (NE PAS montrer si non testée)

- [ ] **Si APK testé sur device réel** :
  - [ ] `cd mobile && npm install`
  - [ ] `eas build --platform android --profile preview`
  - [ ] Installer l'APK sur un téléphone Android
  - [ ] Tester : login → scan QR → saisie constante → offline
  - [ ] Apporter le téléphone à la démo
- [ ] **Si APK NON testé** : NE PAS mentionner l'app mobile au ministre

## J-1 : Répétition

- [ ] **Répéter le scénario complet** (docs/presentation/scenario-demo-ministere.md)
  - [ ] Chronométrer — doit tenir en 10 minutes
  - [ ] Identifier les bugs et les contourner
  - [ ] Préparer des phrases de transition entre chaque étape
- [ ] **Préparer le matériel** :
  - [ ] Ordinateur portable avec backend + frontend démarrés
  - [ ] Câble HDMI pour projecteur/écran
  - [ ] Dossier de présentation imprimé (dossier-ministere-sante.md → PDF)
  - [ ] Scénario imprimé (antisèche)
  - [ ] Cartes de visite / flyers (optionnel)

## J-0 : Jour J (30 min avant)

- [ ] **Démarrer backend + frontend** sur l'ordinateur de démo
- [ ] **Vérifier** : login admin → Dashboard → KPIs visibles
- [ ] **Navigateur** : plein écran (F11), zoom 110%
- [ ] **Onglets préparés** : Dashboard | Patients | Urgences | Laboratoire | Qualité | Facturation
- [ ] **WiFi** : vérifier la connexion (ou utiliser localhost si pas de réseau)
- [ ] **Fermer notifications** (Slack, email, etc.)
- [ ] **Boire de l'eau** — on est prêt

## Pendant la démo

- [ ] Suivre le scénario à la lettre (scenario-demo-ministere.md)
- [ ] Parler lentement, laisser le temps de voir chaque écran
- [ ] Si bug : F5, ne pas paniquer, dire "rafraîchissement"
- [ ] Ne JAMAIS montrer le code
- [ ] Ne JAMAIS montrer les logs backend
- [ ] Ne JAMAIS dire "prototype" ou "première version" — dire "plateforme"

## Après la démo

- [ ] Remettre le dossier de présentation
- [ ] Demander une lettre d'engagement pour le pilote CHU Donka
- [ ] Prendre note des demandes spécifiques du Ministre
- [ ] Envoyer un email de remerciement avec les captures d'écran
