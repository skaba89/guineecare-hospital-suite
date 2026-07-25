# Security Policy

GuinéeCare manipule des données de santé sensibles. La sécurité doit être appliquée dès la conception.

## Principes

- HTTPS obligatoire.
- Authentification forte.
- RBAC et permissions fines.
- Audit des accès aux dossiers patients.
- Chiffrement des sauvegardes.
- Cloisonnement multi-hôpital.
- Contrôle des exports PDF, Excel, CSV.

## Signalement

Tout incident de sécurité doit être remonté à l’équipe projet et traité comme prioritaire.

## Bonnes pratiques minimales

- Ne jamais commiter de secrets.
- Utiliser un fichier `.env.example` sans valeurs sensibles.
- Rotation régulière des clés.
- Tests d’accès par rôle et habilitations.
- Tester les sauvegardes et restaurations.
