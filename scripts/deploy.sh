#!/usr/bin/env bash
# =============================================================================
# GuinéeCare Hospital Suite — Production deployment script (CHU Donka pilot)
# =============================================================================
#
# Usage:
#   bash scripts/deploy.sh                       # full deploy
#   bash scripts/deploy.sh --no-build            # use existing images
#   bash scripts/deploy.sh --check-only          # dry-run, validate only
#
# Pre-requisites:
#   - .env.production exists (see .env.production.template)
#   - tls/fullchain.pem + tls/privkey.pem exist
#   - Docker 24+ and Docker Compose v2 installed
#   - At least 4 GB RAM, 20 GB free disk on the host
#
# =============================================================================

set -euo pipefail

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log()  { echo -e "${GREEN}[$(date +%H:%M:%S)]${NC} $*"; }
warn() { echo -e "${YELLOW}[$(date +%H:%M:%S)] WARN:${NC} $*"; }
err()  { echo -e "${RED}[$(date +%H:%M:%S)] ERROR:${NC} $*" >&2; }
step() { echo -e "\n${BLUE}=== $* ===${NC}"; }

# --- Working dir ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"
CHECK_ONLY=false
NO_BUILD=false

for arg in "$@"; do
    case "$arg" in
        --check-only) CHECK_ONLY=true ;;
        --no-build)   NO_BUILD=true ;;
        *) err "Unknown arg: $arg"; exit 2 ;;
    esac
done

# =============================================================================
# Pre-flight checks
# =============================================================================
step "Pre-flight checks"

if [[ ! -f "$ENV_FILE" ]]; then
    err "Missing $ENV_FILE. Create it from .env.production.template."
    err "  cp .env.production.template $ENV_FILE"
    err "  # then edit and fill in real secrets"
    exit 1
fi

# Source env file to check required vars
# shellcheck disable=SC1090
set -a; source "$ENV_FILE"; set +a

# Required vars
REQUIRED_VARS=(
    ENVIRONMENT AUTH_SECRET DB_PASSWORD
    CORS_ORIGINS REDIS_PASSWORD
    METRICS_TOKEN BOOTSTRAP_TOKEN
)
MISSING=()
for v in "${REQUIRED_VARS[@]}"; do
    if [[ -z "${!v:-}" ]]; then
        MISSING+=("$v")
    fi
done
if [[ ${#MISSING[@]} -gt 0 ]]; then
    err "Missing required env vars in $ENV_FILE: ${MISSING[*]}"
    exit 1
fi

# Refuse placeholder values
if [[ "$AUTH_SECRET" == CHANGE_ME* ]]; then
    err "AUTH_SECRET still has placeholder value. Generate a real secret:"
    err "  openssl rand -hex 48"
    exit 1
fi
if [[ "$DB_PASSWORD" == CHANGE_ME* ]]; then
    err "DB_PASSWORD still has placeholder value. Generate:"
    err "  openssl rand -hex 32"
    exit 1
fi
if [[ "$ENVIRONMENT" != "production" ]]; then
    err "ENVIRONMENT must be 'production' in $ENV_FILE (got: $ENVIRONMENT)"
    exit 1
fi
if [[ "${SEED_DEMO_DATA:-false}" == "true" ]]; then
    err "SEED_DEMO_DATA=true is FORBIDDEN in production. Fix $ENV_FILE."
    exit 1
fi
log "✓ Env file OK"

# Check TLS certs
if [[ ! -f tls/fullchain.pem ]] || [[ ! -f tls/privkey.pem ]]; then
    err "Missing TLS certificates. Place them at:"
    err "  tls/fullchain.pem"
    err "  tls/privkey.pem"
    err ""
    err "For Let's Encrypt, use certbot:"
    err "  sudo certbot certonly --standalone -d chu-donka.guineecare.gn"
    err "  sudo cp /etc/letsencrypt/live/chu-donka.guineecare.gn/fullchain.pem tls/"
    err "  sudo cp /etc/letsencrypt/live/chu-donka.guineecare.gn/privkey.pem   tls/"
    err "  sudo chown -R \$USER:\$USER tls/"
    exit 1
fi
log "✓ TLS certs present"

# Check docker
if ! command -v docker >/dev/null 2>&1; then
    err "Docker is not installed. Install: https://docs.docker.com/engine/install/"
    exit 1
fi
if ! docker compose version >/dev/null 2>&1; then
    err "Docker Compose v2 is not installed."
    exit 1
fi
log "✓ Docker + Compose OK"

# Check disk space (need ≥ 5 GB free)
FREE_GB=$(df -BG . | awk 'NR==2 {gsub("G","",$4); print $4}')
if [[ "$FREE_GB" -lt 5 ]]; then
    err "Only ${FREE_GB} GB free on / — need at least 5 GB."
    exit 1
fi
log "✓ Disk space OK (${FREE_GB} GB free)"

# Check memory (need ≥ 3 GB free)
FREE_MB=$(free -m | awk '/^Mem:/ {print $7}')
if [[ "$FREE_MB" -lt 2048 ]]; then
    warn "Only ${FREE_MB} MB RAM available — recommend ≥ 3 GB for production."
fi

if [[ "$CHECK_ONLY" == true ]]; then
    log "✓ Check-only mode — pre-flight checks passed. Exiting."
    exit 0
fi

# =============================================================================
# Build images
# =============================================================================
if [[ "$NO_BUILD" == false ]]; then
    step "Building Docker images"
    docker compose $COMPOSE_FILES --env-file "$ENV_FILE" build --pull
    log "✓ Build complete"
fi

# =============================================================================
# Pull latest postgres + redis images
# =============================================================================
step "Pulling base images"
docker compose $COMPOSE_FILES --env-file "$ENV_FILE" pull postgres redis nginx
log "✓ Base images up-to-date"

# =============================================================================
# Start database first (with health check)
# =============================================================================
step "Starting PostgreSQL"
docker compose $COMPOSE_FILES --env-file "$ENV_FILE" up -d postgres
log "Waiting for PostgreSQL to be healthy…"
for i in {1..30}; do
    if docker compose $COMPOSE_FILES --env-file "$ENV_FILE" ps postgres | grep -q "healthy"; then
        log "✓ PostgreSQL healthy"
        break
    fi
    sleep 2
    if [[ $i -eq 30 ]]; then
        err "PostgreSQL did not become healthy within 60s."
        docker compose $COMPOSE_FILES --env-file "$ENV_FILE" logs --tail=50 postgres
        exit 1
    fi
done

# =============================================================================
# Run Alembic migrations
# =============================================================================
step "Running Alembic migrations"
docker compose $COMPOSE_FILES --env-file "$ENV_FILE" run --rm \
    --no-deps backend \
    alembic upgrade head
log "✓ Migrations applied"

# =============================================================================
# Start remaining services
# =============================================================================
step "Starting backend + frontend + nginx + redis"
docker compose $COMPOSE_FILES --env-file "$ENV_FILE" up -d
log "Waiting for backend health…"
for i in {1..40}; do
    if docker compose $COMPOSE_FILES --env-file "$ENV_FILE" ps backend | grep -q "healthy"; then
        log "✓ Backend healthy"
        break
    fi
    sleep 3
    if [[ $i -eq 40 ]]; then
        err "Backend did not become healthy within 120s."
        docker compose $COMPOSE_FILES --env-file "$ENV_FILE" logs --tail=100 backend
        exit 1
    fi
done

# =============================================================================
# Bootstrap super-admin (first deploy only)
# =============================================================================
step "Bootstrap check"
# Check if any SUPER_ADMIN exists already
ADMIN_COUNT=$(docker compose $COMPOSE_FILES --env-file "$ENV_FILE" exec -T postgres \
    psql -U guineecare -d guineecare -tAc \
    "SELECT COUNT(*) FROM users WHERE role = 'SUPER_ADMIN'" 2>/dev/null || echo "0")
if [[ "$ADMIN_COUNT" == "0" ]]; then
    warn "No SUPER_ADMIN found. Run bootstrap:"
    echo "  docker compose $COMPOSE_FILES --env-file $ENV_FILE exec backend \\"
    echo "    python -m app.cli create-superuser \\"
    echo "      --email admin@guineecare.gn \\"
    echo "      --password '<strong-password>' \\"
    echo "      --first-name Admin --last-name Donka"
    echo ""
    echo "  OR via HTTP bootstrap (requires BOOTSTRAP_TOKEN):"
    echo "    curl -X POST https://chu-donka.guineecare.gn/api/v1/users/bootstrap \\"
    echo "      -H 'X-Bootstrap-Token: \$BOOTSTRAP_TOKEN' \\"
    echo "      -H 'Content-Type: application/json' \\"
    echo "      -d '{\"email\":\"admin@guineecare.gn\",...}'"
else
    log "✓ $ADMIN_COUNT SUPER_ADMIN(s) already exist — skipping bootstrap"
fi

# =============================================================================
# Verify deployment
# =============================================================================
step "Smoke tests"
PUBLIC_URL="${PUBLIC_URL:-https://chu-donka.guineecare.gn}"

# Health check via HTTPS
if curl -fsS --max-time 10 "${PUBLIC_URL}/health" >/dev/null 2>&1; then
    log "✓ HTTPS /health OK"
else
    warn "HTTPS /health failed (DNS or TLS not ready yet). Try locally:"
    echo "  curl -k https://localhost/health"
fi

# Container status
step "Container status"
docker compose $COMPOSE_FILES --env-file "$ENV_FILE" ps

log ""
log "==================================================================="
log "  GuinéeCare v1.0 deployed."
log "  Public URL: $PUBLIC_URL"
log "  API docs:   $PUBLIC_URL/docs (IP-allowlisted — see nginx.prod.conf)"
log ""
log "  Next steps:"
log "    1. Bootstrap super-admin (see instructions above)"
log "    2. Verify login via browser"
log "    3. Schedule nightly backup verification:"
log "       bash scripts/backup.sh --verify"
log "==================================================================="
