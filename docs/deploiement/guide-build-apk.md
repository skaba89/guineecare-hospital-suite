# Guide Build APK — GuinéeCare Mobile (React Native + Expo)

> Build d'un APK Android installable sur téléphone

## Prérequis

- Compte Expo (gratuit) : https://expo.dev
- Node.js 20+
- Un téléphone Android (USB debugging activé) ou émulateur

## Étape 1 — Installer EAS CLI

```bash
cd mobile
npm install -g eas-cli
eas login
# Connectez-vous avec votre compte Expo
```

## Étape 2 — Configurer EAS

```bash
eas build:configure
# Cela crée eas.json à la racine du projet
```

Vérifiez que `eas.json` contient :
```json
{
  "build": {
    "preview": {
      "android": {
        "buildType": "apk"
      }
    },
    "production": {
      "android": {
        "buildType": "app-bundle"
      }
    }
  }
}
```

## Étape 3 — Configurer l'URL backend

Dans `mobile/app.json`, vérifiez :
```json
{
  "expo": {
    "extra": {
      "eas": {
        "projectId": "guineecare-mobile"
      }
    }
  }
}
```

Pour que l'app mobile pointe vers le backend Render :
```bash
# Créer un fichier .env dans mobile/
echo 'EXPO_PUBLIC_API_URL=https://guineecare.onrender.com/api/v1' > mobile/.env
```

## Étape 4 — Build APK

```bash
cd mobile
eas build --platform android --profile preview
```

- Le build prend ~15 min sur les serveurs EAS (cloud)
- Vous recevez un email avec le lien de téléchargement
- L'APK est aussi disponible sur https://expo.dev/accounts/VOTRE_ACCOUNT/projects/guineecare-mobile/builds

## Étape 5 — Installer sur téléphone

### Option A : Téléchargement direct
1. Ouvrez le lien EAS sur votre téléphone Android
2. Téléchargez l'APK
3. Autorisez "Installation depuis sources inconnues"
4. Installez

### Option B : ADB (USB)
```bash
# Connecter le téléphone en USB (debugging activé)
adb install /path/to/guineecare-mobile.apk
```

## Étape 6 — Tester

1. Ouvrez GuinéeCare sur le téléphone
2. Login : `admin@guineecare.com` / `admin123`
3. Testez :
   - [ ] Dashboard affiche les KPIs
   - [ ] Liste des patients (recherche)
   - [ ] Création d'un patient (avec champs médicaux)
   - [ ] Scan QR code (si vous avez un QR patient)
   - [ ] Notifications
   - [ ] Toggle biométrie (Profile → Activer)
   - [ ] Mode offline (couper WiFi → saisir constante → rallumer → sync)

## Étape 7 — Build AAB (Play Store)

```bash
eas build --platform android --profile production
```

L'AAB est le format requis par le Google Play Store.

## Configuration de l'icône

Les icônes par défaut d'Expo sont utilisées. Pour personnaliser :

1. Créez un logo 1024×1024 PNG (fond teal #0f766e + monogramme "GC" blanc)
2. Placez-le dans `mobile/assets/icon.png`
3. Générez toutes les tailles :
   ```bash
   npx expo install expo-image-manipulator
   # Ou utilisez https://docs.expo.dev/develop/user-interface/splash-screen-and-app-icon/
   ```

## Dépannage

### "Unable to resolve module"
```bash
cd mobile
rm -rf node_modules
npm install
npx expo start --clear
```

### Build échoue sur EAS
- Vérifiez que `app.json` est valide
- Vérifiez que `package.json` n'a pas de dépendances manquantes
- Consultez les logs : https://expo.dev/accounts/VOTRE_ACCOUNT/projects/guineecare-mobile/builds

### L'app crash au démarrage
- Vérifiez que `EXPO_PUBLIC_API_URL` est défini
- L'URL doit être `https://guineecare.onrender.com/api/v1` (pas localhost)

### Push notifications ne marchent pas
- L'endpoint `/user-profile/devices` n'existe pas encore côté backend
- Les push sont désactivés en v1.9 — activés en v2.0

## Coûts EAS

| Plan | Builds/mois | Prix |
|---|---|---|
| Free | 15 builds | 0 € |
| Priority | Illimité | 1 $/build |

Le plan free suffit pour les tests pilote (15 builds/mois).
