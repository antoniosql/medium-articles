<#
.SYNOPSIS
  Deletes the demo resource group. Foundry (Cognitive Services) resources are
  soft-deleted; pass -Purge to purge it too so the name can be reused.

.EXAMPLE
  ./infra/scripts/teardown.ps1
  ./infra/scripts/teardown.ps1 -Purge
#>
[CmdletBinding()]
param(
    [string]$ResourceGroup = "rg-frasohome-decision",
    [switch]$Purge
)

$ErrorActionPreference = "Stop"

$location = az group show --name $ResourceGroup --query location -o tsv
$accounts = az cognitiveservices account list --resource-group $ResourceGroup --query "[].name" -o tsv

Write-Host "Deleting resource group $ResourceGroup..."
az group delete --name $ResourceGroup --yes
if ($LASTEXITCODE -ne 0) { throw "Resource group deletion failed." }

if ($Purge) {
    foreach ($account in ($accounts -split "`n" | Where-Object { $_ })) {
        Write-Host "Purging soft-deleted resource $account..."
        az cognitiveservices account purge --name $account --resource-group $ResourceGroup --location $location
    }
}

Write-Host "Done."
