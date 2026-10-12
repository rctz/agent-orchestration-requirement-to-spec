#!/usr/bin/env bash
# Deploy req3 to the deploy/test host (.183) and (re)start the compose stack.
# Written in M0, first USED in M4 (plan §3). Never run against v2 hosts/paths.
#
# Usage: scripts/deploy.sh [--no-up]
#   --no-up  sync files only, skip `docker compose up -d --build`
#
# Env overrides: REQ3_DEPLOY_HOST (default pi@172.28.50.183),
#                REQ3_DEPLOY_DIR (default req3, relative to $HOME on host).
set -euo pipefail

HOST="${REQ3_DEPLOY_HOST:-pi@172.28.50.183}"
REMOTE_DIR="${REQ3_DEPLOY_DIR:-req3}"
SRC="$(cd "$(dirname "$0")/.." && pwd)"

[ -f "$SRC/.env" ] || { echo "error: $SRC/.env not found (copy from .env.example / req3-lab)" >&2; exit 1; }
[ -f "$SRC/docker-compose.yml" ] || echo "warning: docker-compose.yml missing; --no-up implied" >&2

echo "==> rsync code -> $HOST:$REMOTE_DIR"
rsync -az --delete \
  --exclude .git/ --exclude data/ --exclude .venv/ \
  --exclude __pycache__/ --exclude .pytest_cache/ --exclude .ruff_cache/ \
  --exclude '*.pyc' --exclude .env \
  "$SRC"/ "$HOST":"$REMOTE_DIR"/

echo "==> copy .env (mode 600, values never printed)"
rsync -az --chmod=F600 "$SRC/.env" "$HOST:$REMOTE_DIR/.env"
ssh "$HOST" "chmod 600 '$REMOTE_DIR/.env'"

if [ "${1:-}" != "--no-up" ]; then
  echo "==> docker compose up -d --build on $HOST"
  ssh "$HOST" "cd '$REMOTE_DIR' && docker compose up -d --build"
fi
echo "==> deploy done"
