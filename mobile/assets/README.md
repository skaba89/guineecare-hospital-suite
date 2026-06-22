# Assets

Placez ici les icônes de l'app mobile (référencées dans app.json) :

- `icon.png` (1024×1024) — icône app principale
- `splash.png` (1242×2436) — écran de démarrage
- `adaptive-icon.png` (1024×1024) — icône Android adaptative
- `favicon.png` (48×48) — favicon web
- `notification-icon.png` (96×96) — icône notifications Android

Vous pouvez générer ces assets avec [Expo Image Generator](https://docs.expo.dev/develop/user-interface/splash-screen-and-app-icon/) à partir d'un logo source PNG 1024×1024.

En attendant, Expo utilise un placeholder par défaut. Pour générer les icônes GuinéeCare :

```bash
# Installer expo-image-utils
npx expo install expo-image-manipulator

# Puis utiliser https://docs.expo.dev/develop/user-interface/splash-screen-and-app-icon/
# avec un logo source de 1024x1024 (teal #0f766e + monogramme "GC" blanc)
```
