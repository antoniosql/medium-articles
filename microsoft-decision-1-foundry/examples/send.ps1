<#
.SYNOPSIS
  Sends one example request with Invoke-RestMethod and Microsoft Entra ID. No Python needed.

.EXAMPLE
  ./examples/send.ps1 examples/02-choice.json
#>
[CmdletBinding()]
param([Parameter(Mandatory)] [string]$File)

$ErrorActionPreference = "Stop"

if (Test-Path ".env") {
    foreach ($line in Get-Content ".env") {
        if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$') {
            if (-not [Environment]::GetEnvironmentVariable($Matches[1])) {
                [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2])
            }
        }
    }
}
if (-not $env:AZURE_ENDPOINT -or -not $env:DEPLOYMENT_NAME) {
    throw "Set AZURE_ENDPOINT and DEPLOYMENT_NAME, or run infra/scripts/deploy.ps1"
}

if ($env:AZURE_API_KEY) {
    $headers = @{ "api-key" = $env:AZURE_API_KEY }
} else {
    $token = az account get-access-token --resource https://cognitiveservices.azure.com --query accessToken --output tsv
    $headers = @{ Authorization = "Bearer $token" }
}

# The example files carry "<deployment-name>"; swap in the real deployment name.
$body = (Get-Content -Raw -Encoding utf8 $File).Replace("<deployment-name>", $env:DEPLOYMENT_NAME)
$uri = $env:AZURE_ENDPOINT.TrimEnd("/") + "/providers/microsoft/v1/systemone"

$response = Invoke-RestMethod -Method Post -Uri $uri -Headers $headers `
    -ContentType "application/json; charset=utf-8" `
    -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
$response | ConvertTo-Json -Depth 10
