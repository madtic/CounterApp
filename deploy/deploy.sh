#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT_DIR}"

# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
# CI sets CI_COMMIT_SHORT_SHA and CI_REGISTRY_IMAGE. Both can be overridden
# when running the script manually on the local machine.
TAG="${DEPLOY_IMAGE_TAG:-${CI_COMMIT_SHORT_SHA:-local}}"
REGISTRY_IMAGE="${CI_REGISTRY_IMAGE:-}"

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
VITE_API_BASE_URL="${VITE_API_BASE_URL:-http://localhost:${BACKEND_PORT}}"
CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:${FRONTEND_PORT},http://127.0.0.1:${FRONTEND_PORT}}"

if [ -n "${REGISTRY_IMAGE}" ]; then
  BACKEND_IMAGE="${REGISTRY_IMAGE}/backend:${TAG}"
  FRONTEND_IMAGE="${REGISTRY_IMAGE}/frontend:${TAG}"
else
  # Manual/local invocation without a registry.
  BACKEND_IMAGE="counter-app-local/backend:${TAG}"
  FRONTEND_IMAGE="counter-app-local/frontend:${TAG}"
fi

export BACKEND_IMAGE FRONTEND_IMAGE
export BACKEND_PORT FRONTEND_PORT CORS_ORIGINS

COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"
COMPOSE=(docker compose -f "${COMPOSE_FILE}")

# ---------------------------------------------------------------------------
# Sanity checks
# ---------------------------------------------------------------------------
command -v docker >/dev/null 2>&1 || {
  echo "ERROR: docker is not installed on this runner." >&2
  exit 1
}

docker info >/dev/null 2>&1 || {
  echo "ERROR: the current user cannot access the Docker daemon." >&2
  echo "Add the runner user to the docker group or fix the Docker socket permissions." >&2
  exit 1
}

docker compose version >/dev/null 2>&1 || {
  echo "ERROR: Docker Compose v2 is required (the 'docker compose' command)." >&2
  exit 1
}

# ---------------------------------------------------------------------------
# Reuse images pushed by the docker-build job, otherwise build locally.
# ---------------------------------------------------------------------------
images_available=false

if [ -n "${REGISTRY_IMAGE}" ]; then
  if [ -n "${CI_REGISTRY:-}" ] && [ -n "${CI_REGISTRY_USER:-}" ] && [ -n "${CI_REGISTRY_PASSWORD:-}" ]; then
    if ! echo "${CI_REGISTRY_PASSWORD}" | docker login \
      --username "${CI_REGISTRY_USER}" \
      --password-stdin "${CI_REGISTRY}"; then
      echo "WARNING: registry login failed; trying to pull the public images anyway."
    fi
  fi

  echo "Trying registry images for commit ${TAG}..."
  if docker pull "${BACKEND_IMAGE}" && docker pull "${FRONTEND_IMAGE}"; then
    images_available=true
  else
    echo "Registry images are not available; falling back to a local build."
  fi
fi

if [ "${images_available}" = true ]; then
  echo "Deploying images from the GitLab registry."
else
  echo "Building deployment images locally from the checked-out commit..."
  docker build \
    --file backend/Dockerfile \
    --tag "${BACKEND_IMAGE}" \
    backend

  docker build \
    --file frontend/Dockerfile \
    --build-arg "VITE_API_BASE_URL=${VITE_API_BASE_URL}" \
    --tag "${FRONTEND_IMAGE}" \
    frontend
fi

# ---------------------------------------------------------------------------
# Deploy. Compose recreates containers whose image tag or digest changed, so
# this also handles upgrades.
# ---------------------------------------------------------------------------
"${COMPOSE[@]}" up \
  --detach \
  --remove-orphans \
  --wait \
  --wait-timeout 180

"${COMPOSE[@]}" ps

echo
echo "Deployment complete: ${TAG}"
echo "  Frontend: http://localhost:${FRONTEND_PORT}"
echo "  Backend:  http://localhost:${BACKEND_PORT}"
echo "  API docs: http://localhost:${BACKEND_PORT}/docs"
