#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT_DIR}"

COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"

# The compose file requires image variables during interpolation, even for
# `down`. Deployment images are identified by the running containers, so these
# placeholders are never pulled or started.
export BACKEND_IMAGE="${BACKEND_IMAGE:-counter-app-local/backend:undeploy}"
export FRONTEND_IMAGE="${FRONTEND_IMAGE:-counter-app-local/frontend:undeploy}"

command -v docker >/dev/null 2>&1 || {
  echo "ERROR: docker is not installed on this runner." >&2
  exit 1
}

docker compose version >/dev/null 2>&1 || {
  echo "ERROR: Docker Compose v2 is required (the 'docker compose' command)." >&2
  exit 1
}

# --volumes also removes the named PostgreSQL volume. Remove it if the next
# deployment should start with a fresh counter.
docker compose -f "${COMPOSE_FILE}" down --remove-orphans --volumes

echo "Local deployment removed."
