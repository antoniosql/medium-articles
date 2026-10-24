using './main.bicep'

// Defaults are fine for the demo. The deploy scripts pass location and callerPrincipalId.
param projectName = 'frasohome-decisions'
param deploymentName = 'frasohome-decision'
param deploymentSku = 'GlobalStandard'
param deploymentCapacity = 1
param disableLocalAuth = true
