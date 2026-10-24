using './main.bicep'

// Defaults are fine for the demo. The deploy scripts pass location and callerPrincipalId.
param projectName = 'frasohome-decisions'
param deploymentName = 'frasohome-decision'
param deploymentSku = 'DataZoneStandard'
param deploymentCapacity = 500
param disableLocalAuth = true
