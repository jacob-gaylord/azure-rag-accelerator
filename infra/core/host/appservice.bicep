metadata description = 'Creates an Azure App Service in an existing Azure App Service plan.'
param name string
param location string = resourceGroup().location
param tags object = {}

// Reference Properties
param applicationInsightsName string = ''
param appServicePlanId string
param keyVaultName string = ''
param managedIdentity bool = !empty(keyVaultName)
param virtualNetworkSubnetId string = ''

// Runtime Properties
@allowed([
  'dotnet', 'dotnetcore', 'dotnet-isolated', 'node', 'python', 'java', 'powershell', 'custom'
])
param runtimeName string
param runtimeNameAndVersion string = '${runtimeName}|${runtimeVersion}'
param runtimeVersion string

// Microsoft.Web/sites Properties
param kind string = 'app,linux'

// Microsoft.Web/sites/config
param allowedOrigins array = []
param additionalScopes array = []
param additionalAllowedAudiences array = []
param allowedApplications array = []
param alwaysOn bool = true
param appCommandLine string = ''
@secure()
param appSettings object = {}
param clientAffinityEnabled bool = false
param enableOryxBuild bool = contains(kind, 'linux')
param functionAppScaleLimit int = -1
param linuxFxVersion string = runtimeNameAndVersion
param minimumElasticInstanceCount int = -1
param numberOfWorkers int = -1
param scmDoBuildDuringDeployment bool = false
param use32BitWorkerProcess bool = false
param ftpsState string = 'FtpsOnly'
param healthCheckPath string = ''
param clientAppId string = ''
param serverAppId string = ''
@secure()
param clientSecretSettingName string = ''
param authenticationIssuerUri string = ''
@allowed([ 'Enabled', 'Disabled' ])
param publicNetworkAccess string = 'Enabled'
param enableUnauthenticatedAccess bool = false
param disableAppServicesAuthentication bool = false

// .default must be the 1st scope for On-Behalf-Of-Flow combined consent to work properly
// Please see https://learn.microsoft.com/entra/identity-platform/v2-oauth2-on-behalf-of-flow#default-and-combined-consent
var requiredScopes = [ 'api://${serverAppId}/.default', 'openid', 'profile', 'email', 'offline_access' ]
var requiredAudiences = [ 'api://${serverAppId}' ]

var coreConfig = {
  linuxFxVersion: linuxFxVersion
  alwaysOn: alwaysOn
  ftpsState: ftpsState
  appCommandLine: appCommandLine
  numberOfWorkers: numberOfWorkers != -1 ? numberOfWorkers : null
  minimumElasticInstanceCount: minimumElasticInstanceCount != -1 ? minimumElasticInstanceCount : null
  minTlsVersion: '1.2'
  use32BitWorkerProcess: use32BitWorkerProcess
  functionAppScaleLimit: functionAppScaleLimit != -1 ? functionAppScaleLimit : null
  healthCheckPath: healthCheckPath
  cors: {
    allowedOrigins: allowedOrigins
  }
}

var appServiceProperties = {
  serverFarmId: appServicePlanId
  siteConfig: coreConfig
  clientAffinityEnabled: clientAffinityEnabled
  httpsOnly: true
  // Always route traffic through the vnet
  // See https://learn.microsoft.com/azure/app-service/configure-vnet-integration-routing#configure-application-routing
  vnetRouteAllEnabled: !empty(virtualNetworkSubnetId)
  virtualNetworkSubnetId: !empty(virtualNetworkSubnetId) ? virtualNetworkSubnetId : null
  publicNetworkAccess: publicNetworkAccess
}

// add flag to indicate the App Service already exists and should not be re-created
@description('If true the module will reference an existing App Service instead of creating a new one.')
param exists bool = false

// Reference existing site when `exists` is true
resource appServiceExisting 'Microsoft.Web/sites@2022-03-01' existing = if (exists) {
  name: name
}

// Create or update site only when it doesn't already exist
resource appService 'Microsoft.Web/sites@2022-03-01' = if (!exists) {
  name: name
  location: location
  tags: tags
  kind: kind
  properties: appServiceProperties
  identity: { type: managedIdentity ? 'SystemAssigned' : 'None' }

  resource configAppSettings 'config' = if (!exists) {
    name: 'appsettings'
    properties: union(appSettings,
      {
        SCM_DO_BUILD_DURING_DEPLOYMENT: string(scmDoBuildDuringDeployment)
        ENABLE_ORYX_BUILD: string(enableOryxBuild)
      },
      runtimeName == 'python' ? { PYTHON_ENABLE_GUNICORN_MULTIWORKERS: 'true' } : {},
      !empty(applicationInsightsName) ? { APPLICATIONINSIGHTS_CONNECTION_STRING: applicationInsights.properties.ConnectionString } : {},
      !empty(keyVaultName) ? { AZURE_KEY_VAULT_ENDPOINT: keyVault.properties.vaultUri } : {})
  }

  resource configLogs 'config' = if (!exists) {
    name: 'logs'
    properties: {
      applicationLogs: { fileSystem: { level: 'Verbose' } }
      detailedErrorMessages: { enabled: true }
      failedRequestsTracing: { enabled: true }
      httpLogs: { fileSystem: { enabled: true, retentionInDays: 1, retentionInMb: 35 } }
    }
    dependsOn: [
      configAppSettings
    ]
  }

  resource basicPublishingCredentialsPoliciesFtp 'basicPublishingCredentialsPolicies' = if (!exists) {
    name: 'ftp'
    properties: {
      allow: false
    }
  }

  resource basicPublishingCredentialsPoliciesScm 'basicPublishingCredentialsPolicies' = if (!exists) {
    name: 'scm'
    properties: {
      allow: false
    }
  }

  resource configAuth 'config' = if (!exists && !(empty(clientAppId)) && !disableAppServicesAuthentication) {
    name: 'authsettingsV2'
    properties: {
      globalValidation: {
        requireAuthentication: true
        unauthenticatedClientAction: enableUnauthenticatedAccess ? 'AllowAnonymous' : 'RedirectToLoginPage'
        redirectToProvider: 'azureactivedirectory'
      }
      identityProviders: {
        azureActiveDirectory: {
          enabled: true
          registration: {
            clientId: clientAppId
            clientSecretSettingName: clientSecretSettingName
            openIdIssuer: authenticationIssuerUri
          }
          login: {
            loginParameters: [ 'scope=${join(union(requiredScopes, additionalScopes), ' ')}' ]
          }
          validation: {
            allowedAudiences: union(requiredAudiences, additionalAllowedAudiences)
            defaultAuthorizationPolicy: {
              allowedApplications: allowedApplications
            }
          }
        }
      }
      login: {
        tokenStore: {
          enabled: true
        }
      }
    }
  }
}

resource keyVault 'Microsoft.KeyVault/vaults@2022-07-01' existing = if (!(empty(keyVaultName))) {
  name: keyVaultName
}

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' existing = if (!empty(applicationInsightsName)) {
  name: applicationInsightsName
}

// Choose correct reference for outputs
var appRef = exists ? appServiceExisting : appService

output id string = resourceId('Microsoft.Web/sites', name)
output identityPrincipalId string = managedIdentity ? appRef.identity.principalId : ''
output name string = name
output uri string = 'https://${appRef.properties.defaultHostName}'
