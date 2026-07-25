# Guide SMS Réel — Orange Guinée SMS Pro

> Configuration de l'envoi de SMS réels via Orange Guinée

## Étape 1 — Obtenir un compte Orange SMS Pro

1. Allez sur https://smspro.orange.com
2. Créez un compte entreprise avec :
   - Raison sociale : Ministère de la Santé / CHU Donka
   - Contact technique : votre email
   - Numéro de téléphone : votre numéro
3. Orange vous fournit :
   - `client_id` (clé API)
   - `client_secret` (secret API)
   - Sender ID (ex: "GUINEECARE" ou "CHU DONKA")
4. Achetez un pack SMS (ex: 10 000 SMS pour ~250 000 GNF)

## Étape 2 — Configurer dans GuinéeCare

### Via l'interface web
1. Connectez-vous en tant qu'ADMIN ou SUPER_ADMIN
2. Allez dans **SMS Admin** (sidebar → SYSTÈME)
3. Onglet **Providers** → **+ Nouveau provider**
4. Remplissez :
   - Code : `orange`
   - Nom : `Orange Guinée SMS Pro`
   - URL API : `https://api.orange.com/smsmessaging/v1/outbound/tel%3A%2B{sender}/requests`
   - Clé API : votre `client_id`
   - Secret API : votre `client_secret`
   - Sender ID : `GUINEECARE`
   - Coût/SMS : `25` (GNF)
5. Cliquez **Créer**
6. Cliquez **🧪 Tester** — envoyez un SMS de test à votre numéro

### Via l'API
```bash
TOKEN=$(curl -s -X POST https://guineecare.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@guineecare.com","password":"admin123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -X POST https://guineecare.onrender.com/api/v1/notifications/sms/providers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "orange",
    "name": "Orange Guinée SMS Pro",
    "api_url": "https://api.orange.com/smsmessaging/v1/outbound/tel%3A%2B{sender}/requests",
    "api_key": "VOTRE_CLIENT_ID",
    "api_secret": "VOTRE_CLIENT_SECRET",
    "sender_id": "GUINEECARE",
    "cost_per_sms_gnf": 25
  }'
```

## Étape 3 — Tester l'envoi

```bash
# Obtenir l'ID du provider Orange
PROVIDER_ID=$(curl -s -H "Authorization: Bearer $TOKEN" \
  https://guineecare.onrender.com/api/v1/notifications/sms/providers \
  | python3 -c "import sys,json; [print(p['id']) for p in json.load(sys.stdin)['data'] if p['code']=='orange']")

# Envoyer un SMS de test
curl -X POST https://guineecare.onrender.com/api/v1/notifications/sms/providers/$PROVIDER_ID/test \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"to": "+224622000000", "body": "Test GuinéeCare v1.9 — SMS Orange"}'
```

## Étape 4 — Configurer le chiffrement (production)

```bash
# Générer une clé Fernet
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Définir sur Render (Environment Variables)
SMS_FERNET_KEY=votre_cle_fernet_generee
```

## Coûts estimés

| Volume | Coût (GNF) | Usage |
|---|---|---|
| 100 SMS/mois | 2 500 | Tests pilote |
| 1 000 SMS/mois | 25 000 | CHU Donka (résultats labo critiques) |
| 10 000 SMS/mois | 250 000 | Déploiement national |

## Sécurité

- Les credentials sont **chiffrés** en DB (Fernet optionnel)
- L'endpoint `/notifications/sms/providers` ne retourne **jamais** les credentials en clair
- Seuls `ADMIN` et `SUPER_ADMIN` peuvent gérer les providers
- Audit log de chaque envoi SMS

## Alternative : MTN / Moov

Le code supporte aussi MTN et Moov. Configurez de la même façon :
- Code : `mtn` ou `moov`
- URL API : selon la documentation opérateur
- Credentials : selon l'opérateur
