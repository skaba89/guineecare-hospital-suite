# GuinéeCare Load Tests

Tests de charge avec [Locust](https://locust.io/) pour mesurer les performances
de l'API GuinéeCare sous charge simulée.

## Scénarios

1. **GuineeCareUser** (défaut) — chaque utilisateur simulé :
   - Se connecte une fois au démarrage (`POST /auth/login`)
   - Browsse la liste des patients avec pagination
   - Fetch un détail patient aléatoire
   - Hit le dashboard (agrégations lourdes)
   - List ses notifications + compteur non-lus
   - Hit `/auth/me`, `/users`, `/audit/logs`
   - Se déconnecte à la fin (`POST /auth/logout` avec révocation jti)
   - Think time : 1.0-3.5 s

2. **GuineeCareLoginStorm** (`--tags login_storm`) — chaque itération fait un
   login fresh. Teste le rate-limiter (5/min/IP en prod) et le pool DB.
   Désactivé par défaut (`weight=0`).

## Prérequis

- Backend démarré en mode dev avec seed :

```bash
cd backend
DATABASE_URL="sqlite:///./dev_guineecare.db" \
AUTH_SECRET="dev-secret-key-2025" \
ENVIRONMENT=local \
SEED_DEMO_DATA=true \
CORS_ORIGINS='["*"]' \
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- Locust installé :

```bash
pip install locust
```

## Exécution

### Web UI interactive (recommandé pour explorer)

```bash
locust -f load_tests/locustfile.py --host http://localhost:8000
# Ouvrir http://localhost:8089
# Régler le nombre d'utilisateurs (50, 100, 200) et le spawn rate (5/s)
```

### Headless (pour CI / scripts)

```bash
# 50 users, 5/s spawn, 60s duration
locust -f load_tests/locustfile.py --host http://localhost:8000 \
    --headless -u 50 -r 5 -t 60s \
    --csv load_tests/results/locust_report

# 200 users, 10/s spawn, 5 min — tester la capacité maximale
locust -f load_tests/locustfile.py --host http://localhost:8000 \
    --headless -u 200 -r 10 -t 300s \
    --csv load_tests/results/locust_report_200u
```

### Scénario login storm uniquement

```bash
locust -f load_tests/locustfile.py --host http://localhost:8000 \
    --headless -u 100 -r 10 -t 30s \
    --tags login_storm \
    --csv load_tests/results/login_storm
```

## Métriques attendues

Sur une instance SQLite locale (dev), les seuils cibles sont :

| Endpoint                       | P50   | P95   | P99   |
|--------------------------------|-------|-------|-------|
| `GET /health/ready`            | < 10 ms | < 30 ms | < 80 ms |
| `GET /auth/me`                 | < 20 ms | < 80 ms | < 200 ms |
| `GET /patients?page=1` (20)    | < 50 ms | < 200 ms | < 500 ms |
| `GET /patients/dashboard/stats`| < 200 ms | < 1 s | < 2 s |
| `POST /auth/login`             | < 100 ms | < 400 ms | < 1 s |

En production (PostgreSQL, 2 vCPU, 4 GB RAM), ces seuils doivent être
divisés par ~3 grâce au pool de connexions et au cache OS.

## Interprétation des résultats

- **RPS** (requests per second) — débit global.
- **P95/P99** — latence en queue. Si P99 > 2×P95, il y a un goulot
  (probablement le pool DB).
- **Échecs** — distinguer 401 (tokens expirés en cours de test — normal
  si > 60 min) de 5xx (vrai problème).
- **429** — rate-limit atteint. Normal sur `POST /auth/login` en prod
  si > 5 tentatives/min/IP.

## CI

Le workflow `.github/workflows/load-test.yml` tourne nightly à 03:00 UTC
et lance 30s de test à 20 users. Les résultats sont uploadés en artifact
GitHub pour analyse.
