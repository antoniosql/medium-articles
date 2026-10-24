#!/usr/bin/env bash
# Deletes the demo resource group. Foundry (Cognitive Services) resources are
# soft-deleted; set PURGE=1 to purge it too so the name can be reused.
#
# Usage (from the project root):
#   bash infra/scripts/teardown.sh
#   PURGE=1 bash infra/scripts/teardown.sh
set -euo pipefail

RESOURCE_GROUP="${RESOURCE_GROUP:-rg-frasohome-decision}"
PURGE="${PURGE:-0}"

LOCATION="$(az group show --name "${RESOURCE_GROUP}" --query location -o tsv)"
ACCOUNTS="$(az cognitiveservices account list --resource-group "${RESOURCE_GROUP}" --query "[].name" -o tsv)"

echo "Deleting resource group ${RESOURCE_GROUP}..."
az group delete --name "${RESOURCE_GROUP}" --yes

if [[ "${PURGE}" == "1" ]]; then
  for account in ${ACCOUNTS}; do
    echo "Purging soft-deleted resource ${account}..."
    az cognitiveservices account purge \
      --name "${account}" --resource-group "${RESOURCE_GROUP}" --location "${LOCATION}"
  done
fi

echo "Done."
