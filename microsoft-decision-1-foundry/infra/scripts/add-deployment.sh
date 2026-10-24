#!/usr/bin/env bash
# Adds a Microsoft-Decision-1 deployment to an EXISTING Foundry resource
# (the Azure CLI path shown in the article) and writes ../../.env.
#
# Usage (from the project root):
#   ACCOUNT_NAME=my-foundry RESOURCE_GROUP=my-rg bash infra/scripts/add-deployment.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

: "${ACCOUNT_NAME:?Set ACCOUNT_NAME to your Foundry resource name}"
: "${RESOURCE_GROUP:?Set RESOURCE_GROUP to the resource group of that resource}"
DEPLOYMENT_NAME="${DEPLOYMENT_NAME:-frasohome-decision}"
DEPLOYMENT_SKU="${DEPLOYMENT_SKU:-GlobalStandard}"   # or DataZoneStandard where available
CAPACITY="${CAPACITY:-1}"

az cognitiveservices account deployment create \
  --name "${ACCOUNT_NAME}" \
  --resource-group "${RESOURCE_GROUP}" \
  --deployment-name "${DEPLOYMENT_NAME}" \
  --model-name "Microsoft-Decision-1" \
  --model-format Microsoft \
  --model-version "1" \
  --sku-name "${DEPLOYMENT_SKU}" \
  --sku-capacity "${CAPACITY}" \
  --output none

az cognitiveservices account deployment list \
  --name "${ACCOUNT_NAME}" \
  --resource-group "${RESOURCE_GROUP}" \
  --output table

SUBDOMAIN="$(az cognitiveservices account show \
  --name "${ACCOUNT_NAME}" \
  --resource-group "${RESOURCE_GROUP}" \
  --query properties.customSubDomainName -o tsv)"
ENDPOINT="https://${SUBDOMAIN}.services.ai.azure.com"

cat > "${ROOT_DIR}/.env" <<EOF
# Written by infra/scripts/add-deployment.sh on $(date -u +%Y-%m-%dT%H:%M:%SZ)
AZURE_ENDPOINT=${ENDPOINT}
DEPLOYMENT_NAME=${DEPLOYMENT_NAME}
AZURE_API_KEY=
EOF

echo
echo "Deployment ${DEPLOYMENT_NAME} ready on ${ACCOUNT_NAME}. .env written."
echo "Your identity needs the 'Cognitive Services User' role on the resource to call it with Entra ID."
