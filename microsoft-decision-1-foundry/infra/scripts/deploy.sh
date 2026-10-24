#!/usr/bin/env bash
# Deploys a Foundry resource, a project and a Microsoft-Decision-1 deployment,
# grants the signed-in user inference rights, and writes ../../.env.
#
# Usage (from the project root):
#   bash infra/scripts/deploy.sh
#   RESOURCE_GROUP=rg-demo LOCATION=eastus2 DEPLOYMENT_SKU=DataZoneStandard bash infra/scripts/deploy.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

RESOURCE_GROUP="${RESOURCE_GROUP:-rg-frasohome-decision}"
LOCATION="${LOCATION:-swedencentral}"          # check model region availability first
DEPLOYMENT_NAME="${DEPLOYMENT_NAME:-frasohome-decision}"
DEPLOYMENT_SKU="${DEPLOYMENT_SKU:-GlobalStandard}"
FOUNDRY_NAME="${FOUNDRY_NAME:-}"                # empty = generated from the resource group id
CALLER_PRINCIPAL_ID="${CALLER_PRINCIPAL_ID:-}"  # empty = the signed-in user
CALLER_PRINCIPAL_TYPE="${CALLER_PRINCIPAL_TYPE:-User}"

command -v az >/dev/null || { echo "Azure CLI (az) not found. Install it first." >&2; exit 1; }
az account show >/dev/null 2>&1 || { echo "Not signed in. Run: az login" >&2; exit 1; }

echo "Subscription: $(az account show --query name -o tsv)"

if [[ -z "${CALLER_PRINCIPAL_ID}" ]]; then
  CALLER_PRINCIPAL_ID="$(az ad signed-in-user show --query id -o tsv 2>/dev/null || true)"
  if [[ -z "${CALLER_PRINCIPAL_ID}" ]]; then
    echo "Could not resolve the signed-in user. Set CALLER_PRINCIPAL_ID (and CALLER_PRINCIPAL_TYPE=ServicePrincipal for an app)." >&2
    exit 1
  fi
fi

echo "Creating resource group ${RESOURCE_GROUP} in ${LOCATION}..."
az group create --name "${RESOURCE_GROUP}" --location "${LOCATION}" --output none

PARAMS=(
  --parameters location="${LOCATION}"
  --parameters deploymentName="${DEPLOYMENT_NAME}"
  --parameters deploymentSku="${DEPLOYMENT_SKU}"
  --parameters callerPrincipalId="${CALLER_PRINCIPAL_ID}"
  --parameters callerPrincipalType="${CALLER_PRINCIPAL_TYPE}"
)
if [[ -n "${FOUNDRY_NAME}" ]]; then
  PARAMS+=(--parameters foundryName="${FOUNDRY_NAME}")
fi

echo "Deploying Foundry resource, project and Microsoft-Decision-1 (${DEPLOYMENT_SKU})..."
OUTPUTS="$(az deployment group create \
  --resource-group "${RESOURCE_GROUP}" \
  --name "decision-1-$(date +%Y%m%d%H%M%S)" \
  --template-file "${ROOT_DIR}/infra/main.bicep" \
  "${PARAMS[@]}" \
  --query "[properties.outputs.endpoint.value, properties.outputs.deploymentName.value, properties.outputs.foundryName.value]" \
  --output tsv)"

ENDPOINT="$(sed -n 1p <<< "${OUTPUTS}" | tr -d '\r')"
DEPLOYED_NAME="$(sed -n 2p <<< "${OUTPUTS}" | tr -d '\r')"
ACCOUNT="$(sed -n 3p <<< "${OUTPUTS}" | tr -d '\r')"

cat > "${ROOT_DIR}/.env" <<EOF
# Written by infra/scripts/deploy.sh on $(date -u +%Y-%m-%dT%H:%M:%SZ)
AZURE_ENDPOINT=${ENDPOINT}
DEPLOYMENT_NAME=${DEPLOYED_NAME}
AZURE_API_KEY=
# Resource: ${ACCOUNT} in ${RESOURCE_GROUP}
EOF

echo
echo "Done."
echo "  Foundry resource : ${ACCOUNT}"
echo "  Endpoint         : ${ENDPOINT}/providers/microsoft/v1/systemone"
echo "  Deployment       : ${DEPLOYED_NAME}"
echo "  .env written to  : ${ROOT_DIR}/.env"
echo
echo "Role assignments can take a few minutes to propagate. Then run:"
echo "  decision-demo send examples/02-choice.json"
