# =============================================================================
# GuinéeCare Hospital Suite — Frontend Dockerfile (v2.3.0 — Phase 8)
# =============================================================================
# Multi-stage build : Node builder → nginx alpine (non-root).
# - Base images pincées (patch versions)
# - HEALTHCHECK sur / (endpoint nginx)
# - USER nginx (non-root) — nginx alpine fournit l'utilisateur nginx UID 101
# - LABEL org.opencontainers.image.* pour traçabilité
# - Config nginx versionnée (frontend/nginx.conf) au lieu de inline echo
# =============================================================================

# Stage 1: Build Vite
FROM node:20.18-alpine3.20 AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --no-audit --no-fund
COPY . .
ARG VITE_API_BASE_URL=http://localhost/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# Stage 2: Production nginx
FROM nginx:1.27-alpine3.20

# Métadonnées OCI (v2.3.0)
LABEL org.opencontainers.image.title="GuinéeCare Hospital Suite — Frontend" \
      org.opencontainers.image.description="Frontend React/Vite servé par nginx" \
      org.opencontainers.image.source="https://github.com/skaba89/guineecare-hospital-suite" \
      org.opencontainers.image.licenses="MIT"

# Copier la config nginx versionnée (au lieu de inline echo — fragile)
COPY --from=builder /app/frontend-nginx.conf /etc/nginx/conf.d/default.conf
# Copier le build Vite
COPY --from=builder /app/dist /usr/share/nginx/html

# v2.3.0 — Phase 8 : santé + non-root
# nginx alpine expose déjà /usr/share/nginx/html en lecture pour l'user nginx.
# Les fichiers copiés appartiennent à root; nginx a besoin de lire → OK par défaut.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -q --spider http://localhost:80/ || exit 1

# nginx alpine a l'utilisateur nginx (UID 101) — on l'utilise
# Note : nginx doit pouvoir écrire dans /var/cache/nginx et /var/run.
# L'image officielle alpine gère ça via /var/cache/nginx créée en 755 root.
USER nginx

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
