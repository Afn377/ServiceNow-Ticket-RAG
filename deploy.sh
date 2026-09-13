#!/usr/bin/env bash
#
# Deploy the ServiceNow ticket-RAG backend on an EC2 instance.
#
# Run this ON the EC2 instance, from inside a git clone of this repo after
# `git pull` (NOT from a local dev machine). It builds the Docker image and
# (re)starts the backend container, pulling secrets from AWS SSM Parameter
# Store and passing EXTENSION_ORIGIN through from the caller's environment.
#
# Usage:
#   EXTENSION_ORIGIN="chrome-extension://abc123" ./deploy.sh
#
# EXTENSION_ORIGIN is optional (not a secret); if unset it is passed through
# as an empty value so the script is runnable before the extension ID is known.
set -euo pipefail

IMAGE_NAME="servicenow-backend"
CONTAINER_NAME="servicenow-backend"

# EXTENSION_ORIGIN is supplied by the caller (e.g. from the CI/deploy shell)
# and is not a secret, so it is not read from SSM. Default it to empty so
# `set -u` doesn't abort when the extension ID isn't known yet.
EXTENSION_ORIGIN="${EXTENSION_ORIGIN:-}"

echo "==> Building ${IMAGE_NAME} image"
docker build -t "${IMAGE_NAME}" .

echo "==> Fetching secrets from AWS SSM Parameter Store"
BACKEND_API_KEY="$(aws ssm get-parameter \
  --name /servicenow-ticket-rag/backend_api_key \
  --with-decryption \
  --query 'Parameter.Value' \
  --output text)"

DEEPSEEK_API_KEY="$(aws ssm get-parameter \
  --name /servicenow-ticket-rag/deepseek_api_key \
  --with-decryption \
  --query 'Parameter.Value' \
  --output text)"

echo "==> Stopping and removing any existing container"
docker stop "${CONTAINER_NAME}" 2>/dev/null || true
docker rm "${CONTAINER_NAME}" 2>/dev/null || true

echo "==> Starting new container"
docker run -d \
  --name "${CONTAINER_NAME}" \
  --restart=always \
  -p 127.0.0.1:8420:8420 \
  -e BACKEND_API_KEY="$BACKEND_API_KEY" \
  -e DEEPSEEK_API_KEY="$DEEPSEEK_API_KEY" \
  -e EXTENSION_ORIGIN="$EXTENSION_ORIGIN" \
  "${IMAGE_NAME}"

echo "==> Deployed. Container status:"
docker ps --filter "name=${CONTAINER_NAME}"
