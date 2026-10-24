<#
.SYNOPSIS
  Adds a Microsoft-Decision-1 deployment to an EXISTING Foundry resource
  (the Azure CLI path shown in the article) and writes .env in the project root.

.EXAMPLE
  ./infra/scripts/add-deployment.ps1 -AccountName my-foundry -ResourceGroup my-rg
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)] [string]$AccountName,
    [Parameter(Mandatory)] [string]$ResourceGroup,
    [string]$DeploymentName = "frasohome-decision",
    [ValidateSet("GlobalStandard", "DataZoneStandard")]
    [string]$DeploymentSku = "GlobalStandard",
    [int]$Capacity = 1
)

$ErrorActionPreference = "Stop"
$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path

az cognitiveservices account deployment create `
    --name $AccountName `
    --resource-group $ResourceGroup `
    --deployment-name $DeploymentName `
    --model-name "Microsoft-Decision-1" `
    --model-format Microsoft `
    --model-version "1" `
    --sku-name $DeploymentSku `
    --sku-capacity $Capacity `
    --output none
if ($LASTEXITCODE -ne 0) { throw "Deployment creation failed." }

az cognitiveservices account deployment list `
    --name $AccountName `
    --resource-group $ResourceGroup `
    --output table

$subdomain = az cognitiveservices account show `
    --name $AccountName `
    --resource-group $ResourceGroup `
    --query properties.customSubDomainName -o tsv
$endpoint = "https://$subdomain.services.ai.azure.com"

$envContent = @"
# Written by infra/scripts/add-deployment.ps1 on $((Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ"))
AZURE_ENDPOINT=$endpoint
DEPLOYMENT_NAME=$DeploymentName
AZURE_API_KEY=
"@
Set-Content -Path (Join-Path $RootDir ".env") -Value $envContent -Encoding utf8

Write-Host ""
Write-Host "Deployment $DeploymentName ready on $AccountName. .env written."
Write-Host "Your identity needs the 'Cognitive Services User' role on the resource to call it with Entra ID."
