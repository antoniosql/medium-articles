<#
.SYNOPSIS
  Deploys a Foundry resource, a project and a Microsoft-Decision-1 deployment,
  grants the signed-in user inference rights, and writes .env in the project root.

.EXAMPLE
  ./infra/scripts/deploy.ps1
  ./infra/scripts/deploy.ps1 -ResourceGroup rg-demo -Location spaincentral -Capacity 100
#>
[CmdletBinding()]
param(
    [string]$ResourceGroup = "rg-frasohome-decision",
    [string]$Location = "swedencentral",           # check model region availability first
    [string]$DeploymentName = "frasohome-decision",
    [ValidateSet("GlobalStandard", "DataZoneStandard")]
    [string]$DeploymentSku = "DataZoneStandard",   # only SKU offered in EU regions at launch
    [int]$Capacity = 500,                          # 1 unit = 1 request + 1,000 tokens per minute
    [string]$FoundryName = "",                     # empty = generated from the resource group id
    [string]$CallerPrincipalId = "",               # empty = the signed-in user
    [ValidateSet("User", "ServicePrincipal", "Group")]
    [string]$CallerPrincipalType = "User"
)

$ErrorActionPreference = "Stop"
$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path

if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    throw "Azure CLI (az) not found. Install it first."
}
az account show --output none 2>$null
if ($LASTEXITCODE -ne 0) { throw "Not signed in. Run: az login" }

Write-Host "Subscription: $(az account show --query name -o tsv)"

if (-not $CallerPrincipalId) {
    $CallerPrincipalId = az ad signed-in-user show --query id -o tsv 2>$null
    if (-not $CallerPrincipalId) {
        throw "Could not resolve the signed-in user. Pass -CallerPrincipalId (and -CallerPrincipalType ServicePrincipal for an app)."
    }
}

Write-Host "Creating resource group $ResourceGroup in $Location..."
az group create --name $ResourceGroup --location $Location --output none
if ($LASTEXITCODE -ne 0) { throw "Resource group creation failed." }

$params = @(
    "--parameters", "location=$Location",
    "--parameters", "deploymentName=$DeploymentName",
    "--parameters", "deploymentSku=$DeploymentSku",
    "--parameters", "deploymentCapacity=$Capacity",
    "--parameters", "callerPrincipalId=$CallerPrincipalId",
    "--parameters", "callerPrincipalType=$CallerPrincipalType"
)
if ($FoundryName) { $params += @("--parameters", "foundryName=$FoundryName") }

Write-Host "Deploying Foundry resource, project and Microsoft-Decision-1 ($DeploymentSku)..."
$outputsJson = az deployment group create `
    --resource-group $ResourceGroup `
    --name ("decision-1-" + (Get-Date -Format "yyyyMMddHHmmss")) `
    --template-file (Join-Path $RootDir "infra/main.bicep") `
    @params `
    --query properties.outputs `
    --output json
if ($LASTEXITCODE -ne 0) { throw "Deployment failed." }

$outputs = $outputsJson | ConvertFrom-Json
$endpoint = $outputs.endpoint.value
$deployedName = $outputs.deploymentName.value
$account = $outputs.foundryName.value

$envContent = @"
# Written by infra/scripts/deploy.ps1 on $((Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ"))
AZURE_ENDPOINT=$endpoint
DEPLOYMENT_NAME=$deployedName
AZURE_API_KEY=
# Resource: $account in $ResourceGroup
"@
Set-Content -Path (Join-Path $RootDir ".env") -Value $envContent -Encoding utf8

Write-Host ""
Write-Host "Done."
Write-Host "  Foundry resource : $account"
Write-Host "  Endpoint         : $endpoint/providers/microsoft/v1/systemone"
Write-Host "  Deployment       : $deployedName"
Write-Host "  .env written to  : $(Join-Path $RootDir '.env')"
Write-Host ""
Write-Host "Role assignments can take a few minutes to propagate. Then run:"
Write-Host "  decision-demo send examples/02-choice.json"
