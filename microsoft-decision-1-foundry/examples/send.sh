#!/usr/bin/env bash
# Sends one example request with curl and Microsoft Entra ID. No Python needed.
#
# Usage (from the project root, after deploy):
#   bash examples/send.sh examples/02-choice.json
set -euo pipefail

FILE="${1:?Usage: bash examples/send.sh examples/<file>.json}"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi
: "${AZURE_ENDPOINT:?Set AZURE_ENDPOINT or run infra/scripts/deploy.sh}"
: "${DEPLOYMENT_NAME:?Set DEPLOYMENT_NAME or run infra/scripts/deploy.sh}"

if [[ -n "${AZURE_API_KEY:-}" ]]; then
  AUTH_HEADER="api-key: ${AZURE_API_KEY}"
else
  TOKEN="$(az account get-access-token --resource https://cognitiveservices.azure.com \
    --query accessToken --output tsv)"
  AUTH_HEADER="Authorization: Bearer ${TOKEN}"
fi

# The example files carry "<deployment-name>"; swap in the real deployment name.
BODY="$(sed "s/<deployment-name>/${DEPLOYMENT_NAME}/" "${FILE}")"

curl --silent --show-error --fail-with-body \
  "${AZURE_ENDPOINT%/}/providers/microsoft/v1/systemone" \
  -H "Content-Type: application/json" \
  -H "${AUTH_HEADER}" \
  --data-binary "${BODY}"
echo
