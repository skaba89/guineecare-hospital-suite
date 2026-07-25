# Guide Mobile — GuinéeCare Hospital Suite

**Version :** v2.7.0 (Phase 7)
**Plateforme :** React Native + Expo SDK 51
**Public :** Médecins, infirmiers, sages-femmes, agents d'accueil, agents terrain
**Objectif :** Utiliser GuinéeCare sur mobile en environnement hospitalier guinéen avec connexion instable

## 1. Installation

### Prérequis

- **Node.js** 18+ et npm
- **Expo CLI** : `npm install -g expo-cli`
- **Android Studio** (pour émulateur) ou un appareil Android physique
- **Backend GuinéeCare** accessible (local ou Render)

### Démarrage

```bash
cd mobile
npm install

# Configuration de l'API
cp .env.example .env
# Éditer .env :
#   EXPO_PUBLIC_API_URL=http://10.0.2.2:8000/api/v1  (émulateur Android)
#   EXPO_PUBLIC_API_URL=http://localhost:8000/api/v1  (iOS sim)
#   EXPO_PUBLIC_API_URL=https://guineecare.onrender.com/api/v1  (prod)
#
#   # Credentials démo (DEV uniquement — invisible en prod)
#   EXPO_PUBLIC_DEV_EMAIL=admin@guineecare.com
#   EXPO_PUBLIC_DEV_PASSWORD=admin123

# Lancer en mode dev
npm start
# Scanner le QR code avec Expo Go (Android) ou Camera (iOS)
```

### Build APK Android

```bash
# Installer EAS CLI
npm install -g eas-cli

# Login Expo
eas login

# Build APK preview
eas build -p android --profile preview

# Build production (APK signé)
eas build -p android --profile production
```

## 2. Écrans disponibles

| Écran | Rôle | Description |
|-------|------|-------------|
| **Login** | Tous | Authentification email/password + bouton démo (DEV) |
| **BiometricLock** | Tous | Déverrouillage biométrique (empreinte/Face ID) si activé |
| **Dashboard** | Tous | KPIs principaux + FAB "Note rapide" |
| **PatientsList** | Tous | Liste patients + recherche server-side + pagination |
| **PatientDetail** | Médecin, Infirmier | Dossier patient + constantes vitales + notes |
| **PatientForm** | Médecin, Infirmier | Création patient (marche offline) |
| **QuickConsultation** | Médecin, Infirmier | Saisie rapide note au lit du patient (offline-ready) |
| **QRScan** | Tous | Scan QR code patient → ouverture fiche |
| **Notifications** | Tous | Alertes + notifications push |
| **Profile** | Tous | Profil utilisateur + biométrie + logout |

## 3. Fonctionnalités offline (v2.7.0)

### Indicateur de connectivité

Une **bannière colorée** s'affiche en haut de l'app :
- 🔴 **Rouge** "Hors ligne — X en attente" : pas de connexion
- 🟠 **Orange** "X modification(s) en attente" : online mais mutations en file
- 🔵 **Bleu** "Synchronisation en cours…" : replay de la file
- 🟢 (rien) : tout va bien

### File d'attente offline

Quand l'app est offline, les mutations suivantes sont mises en file :
- Création patient (`POST /patients`)
- Note rapide (`POST /clinical/patients/{id}/notes`)
- Création constante vitale (`POST /clinical/measurements`)

La file est stockée dans AsyncStorage et replayée automatiquement au retour du réseau (FIFO).

### Conflits 409

Si une mutation en file entre en conflit avec l'état serveur (HTTP 409), elle est **déplacée vers une queue de conflits** (au lieu d'être silencieusement drop). L'utilisateur peut la résoudre manuellement via Profile → "Conflits à résoudre".

### Retry avec backoff exponentiel

Les mutations en échec (5xx ou réseau) sont retryées avec un délai exponentiel : 2s → 4s → 8s → 16s → 30s (max). Après 5 retries, la mutation est abandonnée.

## 4. Sécurité mobile

| Mesure | Implémentation |
|--------|----------------|
| **Tokens JWT** | Stockés dans SecureStore (Keychain iOS / Keystore Android) |
| **Biométrie** | Empreinte/Face ID via expo-local-authentication |
| **Re-verrouillage** | L'app se re-verrouille au retour depuis le background (si biométrie activée) |
| **Session expiry** | Vérification JWT `exp` au démarrage → re-login si expiré |
| **Logout serveur** | `POST /auth/logout` révoque le refresh token côté serveur |
| **Pas de credentials hardcodés** | Bouton démo via env vars (`EXPO_PUBLIC_DEV_*`) — invisible en prod |
| **Pas de PHI en clair** | La file offline contient des données médicales mais AsyncStorage est sandboxé par l'OS |

### Risques résiduels

- ⚠️ La file offline n'est **pas chiffrée** (AsyncStorage plain text). Sur un appareil rooté/jailbreaké, les données sont accessibles. Mitigation future : chiffrement AES via `expo-crypto`.
- ⚠️ Pas de **remote wipe** en cas de vol d'appareil. Mitigation : l'admin peut désactiver l'utilisateur (`is_active=False`) → les tokens sont invalidés.

## 5. Configuration des variables d'environnement

Créer un fichier `.env` dans `mobile/` :

```bash
# API backend
EXPO_PUBLIC_API_URL=https://guineecare.onrender.com/api/v1

# Credentials démo (DEV uniquement — ne pas définir en prod)
EXPO_PUBLIC_DEV_EMAIL=admin@guineecare.com
EXPO_PUBLIC_DEV_PASSWORD=admin123
```

> ⚠️ Les variables `EXPO_PUBLIC_*` sont injectées au build time. Ne jamais y mettre de secrets sensibles. Les credentials démo ne sont visibles que si les deux vars sont définies.

## 6. Tests recommandés

### Tests manuels (avant chaque release)

| # | Scénario | Attendu |
|---|----------|---------|
| 1 | Login avec credentials valides | Dashboard s'affiche |
| 2 | Login avec credentials invalides | Message "Identifiants invalides." |
| 3 | Login sans connexion | Message "Connexion impossible. Vérifiez votre réseau." |
| 4 | Login + mise en background 5min + retour | Re-verrouillage biométrique (si activé) |
| 5 | Recherche patient "Diallo" | Liste filtrée |
| 6 | Scan QR code patient | Fiche patient s'ouvre |
| 7 | Création patient online | Succès immédiat |
| 8 | Création patient offline (mode avion) | "Sauvegardé hors-ligne" |
| 9 | Retour réseau après création offline | Sync automatique + bannière bleue |
| 10 | Note rapide offline | Enqueue + bannière "1 en attente" |
| 11 | Token expiré (attendre 60min) | Auto-refresh + requête réussit |
| 12 | Token expiré + refresh token révoqué | Retour écran login "Session expirée" |
| 13 | Erreur 500 serveur (GET) | Retry automatique 3× (1s/2s/4s) |
| 14 | Logout | Retour login + POST /auth/logout serveur |
| 15 | Notifications push reçues | Affichées dans NotificationsScreen |

### Tests automatisés (futur)

- Jest + React Native Testing Library pour composants
- Detox pour E2E (login → scan QR → note rapide → logout)
- Maestro CLI pour tests d'intégration rapides

## 7. Scénario de démo mobile (10 min)

### Contexte
Une sage-femme au CHU Donka doit faire une consultation prénatale au lit de la patiente Mme Diallo, mais la connexion Wi-Fi de l'hôpital est instable.

### Déroulé

| Étape | Durée | Action | Attendu |
|-------|-------|--------|---------|
| 1 | 30s | Login `sf.bah@chu-donka.gn` / `midwife123` | Dashboard s'affiche |
| 2 | 30s | Activer le mode avion sur le téléphone | Bannière rouge "Hors ligne" |
| 3 | 1min | Appuyer sur le FAB "+" → QuickConsultation | Écran de saisie s'ouvre |
| 4 | 1min | Taper "Diallo" dans la recherche | "Recherche impossible hors-ligne — utilisez le scan QR." |
| 5 | 30s | Appuyer sur l'onglet "Scanner" | Caméra s'ouvre |
| 6 | 30s | Scanner le QR code bracelet de Mme Diallo | Fiche patient s'ouvre (cache local) |
| 7 | 1min | Retour + FAB "+" → QuickConsultation | Sélectionner "Diallo Aminata" (déjà en cache) |
| 8 | 1min | Type = "Observation", contenu = "PA 120/80, œdèmes légers, bon état général" | |
| 9 | 30s | Appuyer "Enregistrer hors-ligne" | "Sauvegardé hors-ligne — sera synchronisé" + bannière orange "1 en attente" |
| 10 | 30s | Désactiver le mode avion | Bannière bleue "Synchronisation…" → bannière disparaît |
| 11 | 30s | Vérifier dans le backend que la note est créée | Note visible dans /clinical/patients/{id}/notes |

**Points clés démontrés :**
- ✅ Saisie médicale possible sans connexion
- ✅ Scan QR pour identification patient offline
- ✅ Indicateur de connectivité visible
- ✅ Synchronisation automatique au retour réseau
- ✅ Aucune donnée perdue

## 8. Ce qui reste pour la Phase 8

| Élément | Priorité | Effort |
|---------|----------|--------|
| Chiffrement file offline (AES via expo-crypto) | P1 | 1 jour |
| Cache local patients (AsyncStorage read-through) | P1 | 1 jour |
| Idempotency keys sur POST (UUID client) | P1 | 4h |
| Push token unregistration on logout | P1 | 2h |
| Push deep-linking (tap → navigate) | P1 | 1 jour |
| Infinite scroll patients | P2 | 4h |
| DateTimePicker pour dates | P2 | 2h |
| Torch toggle QR scan | P2 | 1h |
| Migrer expo-barcode-scanner → expo-camera | P2 | 1 jour |
| Tests E2E Detox/Maestro | P2 | 2 jours |
| Mode sombre (DarkTheme déjà importé) | P3 | 1 jour |

## Voir aussi

- `docs/deploiement/guide-build-apk.md` — Guide build APK détaillé
- `docs/deploiement/guide-utilisateur-rapide.md` — Guide utilisateurs web (transposable mobile)
- `docs/deploiement/scenario-demo-bout-en-bout.md` — Scénario démo complet
- `mobile/src/hooks/useOfflineSync.ts` — Code offline sync
- `mobile/src/services/api.ts` — Client HTTP avec retry + refresh
