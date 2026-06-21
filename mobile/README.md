# GuinéeCare Mobile — v1.7.0

Application mobile Android (React Native + Expo) pour la suite hospitalière GuinéeCare.

## Objectif

Offrir aux médecins et infirmiers en garde un accès mobile aux dossiers patients, avec :

- **Authentification biométrique** (empreinte/Face ID) au démarrage
- **Scan QR code patient** au pied du lit (bracelet d'identification)
- **Notifications push** (résultats labo critiques, alertes qualité, etc.)
- **Mode hors-ligne** avec file d'attente des mutations (constantes vitales, notes)
- **Fonctionnalités limitées** au contexte mobile (pas de saisie clinique complète — réservée à l'interface desktop)

## Stack technique

- **React Native** 0.74 via **Expo SDK 51** (managed workflow)
- **TypeScript** strict
- **React Navigation** 6 (Stack + Bottom Tabs)
- **Axios** + JWT (avec refresh automatique)
- **expo-secure-store** pour le stockage sécurisé des tokens (Keychain/Keystore)
- **expo-local-authentication** pour la biométrie
- **expo-barcode-scanner** pour le scan QR
- **expo-notifications** pour les push
- **@react-native-community/netinfo** + **AsyncStorage** pour l'offline sync
- **EAS Build** pour les builds Android (APK/AAB)

## Structure du projet

```
mobile/
├── app.json                  # Configuration Expo
├── package.json              # Dépendances npm
├── tsconfig.json             # Config TypeScript
├── babel.config.js           # Babel (alias @/ → ./src/)
└── src/
    ├── App.tsx               # Point d'entrée — wrap providers + navigator
    ├── types/
    │   └── index.ts          # Types TypeScript partagés (User, Patient, etc.)
    ├── services/
    │   └── api.ts            # Client HTTP axios + JWT + refresh
    ├── context/
    │   └── AuthContext.tsx   # État auth global + biométrie
    ├── navigation/
    │   └── AppNavigator.tsx  # Stack + Bottom Tabs + ProtectedRoute
    ├── hooks/
    │   ├── useOfflineSync.ts # File d'attente mutations offline
    │   └── usePushNotifications.ts # Expo push token + listeners
    ├── components/
    │   └── Icons.tsx         # Wrapper @expo/vector-icons
    └── screens/
        ├── LoginScreen.tsx
        ├── BiometricLockScreen.tsx
        ├── DashboardScreen.tsx
        ├── PatientsListScreen.tsx
        ├── PatientDetailScreen.tsx
        ├── QRScanScreen.tsx
        ├── NotificationsScreen.tsx
        └── ProfileScreen.tsx
```

## Démarrage rapide (développement)

### Prérequis

- Node.js 20+
- npm ou bun
- Expo CLI (`npm install -g expo-cli`)
- Backend GuinéeCare démarré sur `http://localhost:8000`

### Installation

```bash
cd mobile
npm install
```

### Lancer l'app

```bash
# Démarrer le serveur Expo
npm start

# Ou directement sur émulateur Android
npm run android
```

L'app ouvre sur http://localhost:8081 (Expo DevTools). Scannez le QR code avec l'app **Expo Go** (Android Play Store) pour tester sur device physique.

### Configuration du backend

L'app mobile communique avec le backend via `EXPO_PUBLIC_API_URL`. Par défaut :

- **Émulateur Android** : `http://10.0.2.2:8000/api/v1` (10.0.2.2 = host loopback)
- **Device physique** : `http://<IP-LOCALE>:8000/api/v1` (ex: `http://192.168.1.42:8000/api/v1`)

Pour surcharger :
```bash
EXPO_PUBLIC_API_URL="http://192.168.1.42:8000/api/v1" npm start
```

### Comptes de test

| Email | Mot de passe | Rôle |
|---|---|---|
| `admin@guineecare.com` | `admin123` | SUPER_ADMIN |
| `dr.diallo@chu-donka.gn` | `doctor123` | DOCTOR |
| `inf.konde@chu-donka.gn` | `nurse123` | NURSE |

## Fonctionnalités par écran

### 🔐 Login
- Email + password
- Validation basique
- Lien "Mode démo" qui pré-remplit admin
- Persistance session via SecureStore

### 🔒 BiometricLock
- S'affiche au démarrage si l'utilisateur a activé le déverrouillage biométrique
- Authentification empreinte/Face ID via `expo-local-authentication`
- Bouton "Se déconnecter" en secours

### 🏠 Dashboard
- KPIs du jour (patients actifs, admissions, lits, urgences)
- Tâches en attente (labo, imagerie)
- Cartes finances (recette du jour, créances impayées)
- Pull-to-refresh

### 👥 PatientsList
- Recherche server-side debouncée 300ms
- Pagination offset (20/page)
- Pull-to-refresh
- Tap → PatientDetail

### 👤 PatientDetail
- Identité + âge + contact
- 5 dernières constantes vitales (avec icônes par type)
- 5 dernières demandes labo (avec badge statut)
- 3 dernières ordonnances
- Modal "Saisir constante" (formulaire avec picker de type + valeur numérique)
- Pull-to-refresh

### 📷 QRScan
- Scan QR code patient via `expo-barcode-scanner`
- Gestion permission caméra
- Cadre de visée animé
- Recherche automatique du patient scanné → navigation PatientDetail
- Gestion erreur (QR inconnu, réseau)

### 🔔 Notifications
- Liste paginée des notifications (50/page)
- Badge priorité (urgent/high/normal/low)
- Tap → marquer comme lu
- Bouton "Tout marquer comme lu"
- Pull-to-refresh

### 👨‍⚕️ Profile
- Carte profil (nom, email, rôle)
- Toggle déverrouillage biométrique
- Affichage URL backend (debug)
- Bouton déconnexion

## Mode hors-ligne (offline sync)

L'app gère la connectivité intermittente (fréquente en Guinée) via :

1. **Détection réseau** via `@react-native-community/netinfo`
2. **File d'attente** : quand offline, les mutations (POST/PATCH/DELETE) sont stockées dans `AsyncStorage` au lieu d'être envoyées
3. **Replay automatique** : dès que la connexion revient, la queue est replayée dans l'ordre (FIFO)
4. **Gestion d'erreurs** :
   - 4xx (erreur client) → abandon de la mutation
   - 5xx (erreur serveur) → retry jusqu'à 5 fois
   - Sinon → garde dans la queue

Usage typique dans un écran :
```typescript
const { isOnline, enqueue } = useOfflineSync();

async function handleSaveVital() {
  if (!isOnline) {
    await enqueue('POST', '/clinical/measurements', { patient_id, ... });
    Alert.alert('Sauvegardé hors-ligne', 'Sera synchronisé au retour du réseau.');
  } else {
    await createMeasurement(payload);
  }
}
```

## Notifications push

Inscription automatique au démarrage :
1. Demande de permission (iOS + Android 13+)
2. Configuration des channels Android (`default` + `urgent` pour alertes critiques)
3. Récupération de l'Expo Push Token
4. Enregistrement auprès du backend via `POST /user-profile/devices` (endpoint à implémenter côté backend en v1.8)

Listeners en foreground :
- Notifications affichées en bannière système (non intrusives)
- Tap sur notification → TODO navigation vers l'écran pertinent (v1.8)

## Build de production

### Prérequis EAS

```bash
npm install -g eas-cli
eas login
eas build:configure
```

### Build APK preview (installable sur device)

```bash
npm run build:android
```

### Build AAB production (Play Store)

```bash
npm run build:production
```

Le build s'exécute sur les serveurs EAS Build (cloud Expo). Compter ~15 min pour un APK Android.

### Mise à jour OTA (EAS Update)

Les mises à jour de code JS (sans rebuild natif) sont publiées via :
```bash
eas update --branch production --message "Fix: crash QR scan sur Android 14"
```

Les devices téléchargent automatiquement la mise à jour au prochain démarrage de l'app.

## Permissions Android

Déclarées dans `app.json` :
- `CAMERA` — scan QR code patient
- `USE_BIOMETRIC`, `USE_FINGERPRINT` — déverrouillage biométrique
- `VIBRATE` — notifications
- `INTERNET`, `ACCESS_NETWORK_STATE` — API + détection offline

## Points d'attention v1.7

1. **Endpoint push token** : `POST /user-profile/devices` est appelé mais n'existe pas encore côté backend. À implémenter en v1.8 pour activer les push réels.

2. **Pas de temps réel WebSocket** : le dashboard ne se met pas à jour en live (pull-to-refresh uniquement). L'intégration WebSocket (déjà présente côté web via `useRealtimeKPIs`) est prévue en v1.8.

3. **Saisie clinique limitée** : seules les constantes vitales peuvent être saisies depuis le mobile. Les prescriptions, ordonnances labo/imagerie, admissions etc. restent sur l'interface desktop (plus ergonomique).

4. **Pas de cache patient offline** : la liste des patients et le détail patient ne sont pas mis en cache AsyncStorage. En offline, seules les mutations sont queueées — pas de consultation des données déjà chargées. À améliorer en v1.8 avec un cache local SQLite (expo-sqlite).

5. **Auth biométrique optionnelle** : activée par défaut sur device compatible, mais désactivable depuis ProfileScreen. En cas de problème, l'utilisateur peut toujours se déconnecter et se reconnecter avec email/password.

6. **Multi-tenant** : l'app envoie automatiquement `X-Facility-ID` pour les rôles non-SUPER_ADMIN (comme le frontend web). Le user conserve son facility_id au login.

## Roadmap v1.8

- Cache local SQLite pour consultation offline des dossiers patients
- WebSocket temps réel sur le dashboard (KPIs live)
- Push notifications avec navigation contextuelle (tap → PatientDetail)
- Saisie de notes cliniques courtes (observation, évolution)
- Mode portrait/paysage optimisé pour tablettes
- Authentification par code PIN (alternative à la biométrie)
- Internationalisation EN/FR (cohérent avec le web)
