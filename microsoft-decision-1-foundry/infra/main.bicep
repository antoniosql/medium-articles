// Microsoft Foundry resource + project + Microsoft-Decision-1 deployment
// Companion to "Your agents don't need to think so much: Microsoft-Decision-1 in Foundry"

targetScope = 'resourceGroup'

@description('Name of the Foundry (AI Services) resource. Also used as the custom subdomain.')
@minLength(2)
@maxLength(64)
param foundryName string = 'frasohome-${uniqueString(resourceGroup().id)}'

@description('Name of the Foundry project inside the resource.')
param projectName string = 'frasohome-decisions'

@description('Region for the resource. Pick one close to your users and where the model is offered.')
param location string = resourceGroup().location

@description('Deployment name. Requests send this value in the "model" field.')
param deploymentName string = 'frasohome-decision'

@description('DataZoneStandard keeps inference in the data zone (the only SKU offered in EU regions at launch). GlobalStandard = global capacity where offered.')
@allowed([
  'GlobalStandard'
  'DataZoneStandard'
])
param deploymentSku string = 'DataZoneStandard'

@description('Capacity units. 1 unit = 1 request and 1,000 tokens per minute. 500 is the Azure default.')
@minValue(1)
param deploymentCapacity int = 500

@description('Object ID of the user or service principal that will call the API. Empty = no role assignment.')
param callerPrincipalId string = ''

@description('Principal type of callerPrincipalId.')
@allowed([
  'User'
  'ServicePrincipal'
  'Group'
])
param callerPrincipalType string = 'User'

@description('Disable API keys and force Microsoft Entra ID. Recommended.')
param disableLocalAuth bool = true

// Built-in role: Cognitive Services User (data-plane inference)
var cognitiveServicesUserRoleId = 'a97b65f3-24c7-4388-baec-2e87135dc908'

resource foundry 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: foundryName
  location: location
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: foundryName
    allowProjectManagement: true
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: disableLocalAuth
  }
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' = {
  parent: foundry
  name: projectName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    displayName: projectName
    description: 'FraSoHome demos for Microsoft-Decision-1'
  }
}

resource decisionDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = {
  parent: foundry
  name: deploymentName
  sku: {
    name: deploymentSku
    capacity: deploymentCapacity
  }
  properties: {
    model: {
      format: 'Microsoft'
      name: 'Microsoft-Decision-1'
      version: '1'
    }
  }
  dependsOn: [
    project
  ]
}

resource callerCanInfer 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(callerPrincipalId)) {
  scope: foundry
  name: guid(foundry.id, callerPrincipalId, cognitiveServicesUserRoleId)
  properties: {
    principalId: callerPrincipalId
    principalType: callerPrincipalType
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      cognitiveServicesUserRoleId
    )
  }
}

@description('Base endpoint for the decision API: <endpoint>/providers/microsoft/v1/systemone')
output endpoint string = 'https://${foundryName}.services.ai.azure.com'

@description('Value to send in the "model" field of each request.')
output deploymentName string = decisionDeployment.name

output foundryName string = foundry.name
output projectName string = project.name
