#!/usr/bin/env bash
# =============================================================================
# GuinéeCare — Alias vers verify-demo.sh (v2.3.0 — Phase 8)
# =============================================================================
# Ce script était un doublon de verify-demo.sh. Il est conservé pour
# rétro-compatibilité avec la documentation et les habitudes existantes.
# Usage : ./scripts/test-login.sh [API_URL]
# =============================================================================
set -euo pipefail

if [[ $# -gt 0 ]]; then
  API_URL="$1" exec "$(dirname "$0")/verify-demo.sh"
else
  exec "$(dirname "$0")/verify-demo.sh"
fi
