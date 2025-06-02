targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the the environment which is used to generate a short unique hash used in all resources.')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

param appServicePlanName string = '' // Set in main.parameters.json
param backendServiceName string = '' // Set in main.parameters.json
param resourceGroupName string = '' // Set in main.parameters.json

param applicationInsightsDashboardName string = '' // Set in main.parameters.json
param applicationInsightsName string = '' // Set in main.parameters.json
param logAnalyticsName string = '' // Set in main.parameters.json

param searchServiceName string = '' // Set in main.parameters.json
param searchServiceResourceGroupName string = '' // Set in main.parameters.json
param searchServiceLocation string = '' // Set in main.parameters.json
// The free tier does not support managed identity (required) or semantic search (optional)
@description('The SKU name for the Azure AI Search service. Standard tier is recommended for production workloads.')
@allowed(['free', 'basic', 'standard', 'standard2', 'standard3', 'storage_optimized_l1', 'storage_optimized_l2'])
param searchServiceSkuName string // Set in main.parameters.json
param searchIndexName string // Set in main.parameters.json
param searchAgentName string = useAgenticRetrieval ? '${searchIndexName}-agent' : ''
param searchQueryLanguage string // Set in main.parameters.json
param searchQuerySpeller string // Set in main.parameters.json
param searchServiceSemanticRankerLevel string // Set in main.parameters.json
param searchFieldNameEmbedding string // Set in main.parameters.json
var actualSearchServiceSemanticRankerLevel = (searchServiceSkuName == 'free')
  ? 'disabled'
  : searchServiceSemanticRankerLevel
param searchServiceQueryRewriting string // Set in main.parameters.json
param storageAccountName string = '' // Set in main.parameters.json
param storageResourceGroupName string = '' // Set in main.parameters.json
param storageResourceGroupLocation string = location
param storageContainerName string = 'content'
param storageSkuName string // Set in main.parameters.json

param defaultReasoningEffort string // Set in main.parameters.json
param useAgenticRetrieval bool // Set in main.parameters.json

param userStorageAccountName string = ''
param userStorageContainerName string = 'user-content'

param tokenStorageContainerName string = 'tokens'

param appServiceSkuName string // Set in main.parameters.json

// Enhanced App Service Configuration Parameters
@description('App Service Plan tier (e.g., Basic, Standard, Premium, PremiumV2, PremiumV3)')
@allowed(['Free', 'Shared', 'Basic', 'Standard', 'Premium', 'PremiumV2', 'PremiumV3', 'Isolated', 'IsolatedV2'])
param appServicePlanTier string = 'Basic'

@description('App Service Plan size (e.g., B1, S1, P1V2)')
param appServicePlanSize string = 'B1'

@description('App Service Plan capacity (number of instances)')
param appServicePlanCapacity int = 1

@description('Enable auto-scaling for App Service Plan')
param appServiceEnableAutoscale bool = false

@description('Minimum number of instances for auto-scaling')
param appServiceAutoscaleMinInstances int = 1

@description('Maximum number of instances for auto-scaling')
param appServiceAutoscaleMaxInstances int = 10

@description('CPU percentage threshold to scale out')
param appServiceScaleOutCpuThreshold int = 70

@description('CPU percentage threshold to scale in')
param appServiceScaleInCpuThreshold int = 30

@description('Memory percentage threshold to scale out')
param appServiceScaleOutMemoryThreshold int = 80

@description('Memory percentage threshold to scale in')
param appServiceScaleInMemoryThreshold int = 40

@description('Health check path for App Service')
param appServiceHealthCheckPath string = ''

@description('Enable always-on for App Service (overrides SKU-based default)')
param appServiceAlwaysOn bool = true

@description('Use 32-bit worker process (overrides SKU-based default)')
param appServiceUse32BitWorkerProcess bool = false

@description('Number of worker processes')
param appServiceNumberOfWorkers int = 1

@description('Minimum elastic instance count for consumption plans')
param appServiceMinimumElasticInstanceCount int = 0

@description('Enable deployment slots for App Service')
param appServiceEnableDeploymentSlots bool = false

@description('Number of deployment slots to create')
param appServiceDeploymentSlotsCount int = 1

@description('Names of deployment slots (comma-separated)')
param appServiceDeploymentSlotNames string = 'staging'

@allowed(['azure', 'openai', 'azure_custom'])
param openAiHost string // Set in main.parameters.json
param isAzureOpenAiHost bool = startsWith(openAiHost, 'azure')
param deployAzureOpenAi bool = openAiHost == 'azure'
param azureOpenAiCustomUrl string = ''
param azureOpenAiApiVersion string = ''
@secure()
param azureOpenAiApiKey string = ''
param azureOpenAiDisableKeys bool = true
param openAiServiceName string = ''
param openAiResourceGroupName string = ''

param speechServiceResourceGroupName string = ''
param speechServiceLocation string = ''
param speechServiceName string = ''
param speechServiceSkuName string // Set in main.parameters.json
param speechServiceVoice string = ''
param useGPT4V bool = false
param useEval bool = false

@description('Base URL for citation links. If empty, uses the default backend content endpoint.')
param citationBaseUrl string = ''

@allowed(['free', 'provisioned', 'serverless'])
param cosmosDbSkuName string // Set in main.parameters.json
param cosmodDbResourceGroupName string = ''
param cosmosDbLocation string = ''
param cosmosDbAccountName string = ''
param cosmosDbThroughput int = 400
param chatHistoryDatabaseName string = 'chat-database'
param chatHistoryContainerName string = 'chat-history-v2'
@description('Name of the Cosmos DB container for storing user feedback')
param userFeedbackContainerName string = 'UserFeedback'
param chatHistoryVersion string = 'cosmosdb-v2'

// Enhanced Cosmos DB Configuration Parameters
@description('Consistency level for Cosmos DB')
@allowed(['Strong', 'BoundedStaleness', 'Session', 'Eventual', 'ConsistentPrefix'])
param cosmosDbConsistencyLevel string = 'Session'

@description('Max staleness prefix for BoundedStaleness consistency')
param cosmosDbMaxStalenessPrefix int = 100000

@description('Max interval in seconds for BoundedStaleness consistency')
param cosmosDbMaxIntervalInSeconds int = 5

@description('Backup policy type for Cosmos DB')
@allowed(['Periodic', 'Continuous'])
param cosmosDbBackupPolicyType string = 'Periodic'

@description('Backup interval in minutes for periodic backup (60-1440)')
param cosmosDbBackupIntervalInMinutes int = 240

@description('Backup retention in hours for periodic backup (8-720)')
param cosmosDbBackupRetentionInHours int = 8

@description('Enable geo-redundant backup for periodic backup')
param cosmosDbGeoRedundantBackup bool = false

@description('Enable multiple write locations for Cosmos DB')
param cosmosDbEnableMultipleWriteLocations bool = false

@description('Additional regions for Cosmos DB deployment (JSON array of objects with locationName and failoverPriority)')
param cosmosDbAdditionalRegions array = []

@description('Enable autoscale for Cosmos DB throughput')
param cosmosDbEnableAutoscale bool = false

@description('Maximum throughput for autoscale (4000-1000000, must be divisible by 1000)')
param cosmosDbAutoscaleMaxThroughput int = 4000

@description('Enable analytical storage for Cosmos DB')
param cosmosDbEnableAnalyticalStorage bool = false

@description('Time to live for analytical store in seconds (-1 for infinite)')
param cosmosDbAnalyticalStoreTtl int = -1

@description('Enable zone redundancy for Cosmos DB primary region')
param cosmosDbEnableZoneRedundancy bool = false

@description('Network ACL bypass for Cosmos DB')
@allowed(['None', 'AzureServices'])
param cosmosDbNetworkAclBypass string = 'AzureServices'

// Enhanced Networking Configuration Parameters
@description('Enable custom VNet configuration (overrides default settings)')
param vnetEnableCustomConfiguration bool = false

@description('Custom VNet address prefix (CIDR notation)')
param vnetAddressPrefix string = '10.0.0.0/16'

@description('App Service integration subnet address prefix')
param appSubnetAddressPrefix string = '10.0.3.0/24'

@description('Backend services subnet address prefix')
param backendSubnetAddressPrefix string = '10.0.1.0/24'

@description('Private endpoints subnet address prefix')
param privateEndpointSubnetAddressPrefix string = '10.0.2.0/24'

@description('Virtual machine subnet address prefix')
param vmSubnetAddressPrefix string = '10.0.4.0/24'

@description('Azure Bastion subnet address prefix')
param bastionSubnetAddressPrefix string = '10.0.5.0/24'

@description('Enable granular private endpoint controls (overrides usePrivateEndpoint for individual services)')
param enableGranularPrivateEndpoints bool = false

@description('Enable private endpoint for Cosmos DB')
param enableCosmosDbPrivateEndpoint bool = false

@description('Enable private endpoint for Storage Account')
param enableStoragePrivateEndpoint bool = false

@description('Enable private endpoint for App Service')
param enableAppServicePrivateEndpoint bool = false

@description('Enable private endpoint for Azure Search')
param enableSearchPrivateEndpoint bool = false

@description('Enable private endpoint for OpenAI service')
param enableOpenAiPrivateEndpoint bool = false

@description('Enable private endpoint for Computer Vision service')
param enableComputerVisionPrivateEndpoint bool = false

@description('Enable private endpoint for Document Intelligence service')
param enableDocumentIntelligencePrivateEndpoint bool = false

@description('Enable private endpoint for Speech service')
param enableSpeechPrivateEndpoint bool = false

@description('Enable custom Network Security Group rules')
param enableCustomNsgRules bool = false

@description('Allowed inbound ports for NSG rules (array of port strings)')
param allowedInboundPorts array = ['80', '443']

@description('Allowed outbound ports for NSG rules (array of port strings)')
param allowedOutboundPorts array = ['80', '443', '53']

@description('Allowed source address prefixes for inbound NSG rules')
param allowedSourceAddressPrefixes array = ['*']

@description('Allowed destination address prefixes for outbound NSG rules')
param allowedDestinationAddressPrefixes array = ['*']

@description('NSG rule priority starting number (rules will increment from this value)')
param nsgRulePriorityStart int = 1000

@description('Enable service endpoints for subnets')
param enableServiceEndpoints bool = false

@description('Service endpoints to enable (e.g., Microsoft.Storage, Microsoft.KeyVault)')
param serviceEndpoints array = ['Microsoft.Storage', 'Microsoft.KeyVault', 'Microsoft.AzureCosmosDB']

@description('Enable VNet peering configuration')
param enableVnetPeering bool = false

@description('Remote VNet resource ID for peering')
param remoteVnetResourceId string = ''

@description('Allow forwarded traffic in VNet peering')
param allowForwardedTraffic bool = false

@description('Allow gateway transit in VNet peering')
param allowGatewayTransit bool = false

@description('Use remote gateways in VNet peering')
param useRemoteGateways bool = false

@description('Enable DDoS protection standard')
param enableDdosProtection bool = false

@description('DDoS protection plan resource ID')
param ddosProtectionPlanId string = ''

@description('Custom DNS servers for VNet (array of IP addresses)')
param customDnsServers array = []

@description('Enable private DNS zone auto-registration')
param enablePrivateDnsAutoRegistration bool = true

@description('Custom private DNS zone names (array of DNS zone names)')
param customPrivateDnsZones array = []

// https://learn.microsoft.com/azure/ai-services/openai/concepts/models?tabs=global-standard%2Cstandard-chat-completions#models-by-deployment-type
@description('Location for the OpenAI resource group')
@allowed([
  'australiaeast'
  'brazilsouth'
  'canadaeast'
  'eastus'
  'eastus2'
  'francecentral'
  'germanywestcentral'
  'japaneast'
  'koreacentral'
  'northcentralus'
  'norwayeast'
  'polandcentral'
  'southafricanorth'
  'southcentralus'
  'southindia'
  'spaincentral'
  'swedencentral'
  'switzerlandnorth'
  'uaenorth'
  'uksouth'
  'westeurope'
  'westus'
  'westus3'
])
@metadata({
  azd: {
    type: 'location'
  }
})
param openAiLocation string

param openAiSkuName string = 'S0'

@secure()
param openAiApiKey string = ''
param openAiApiOrganization string = ''

param documentIntelligenceServiceName string = '' // Set in main.parameters.json
param documentIntelligenceResourceGroupName string = '' // Set in main.parameters.json

// Limited regions for new version:
// https://learn.microsoft.com/azure/ai-services/document-intelligence/concept-layout
@description('Location for the Document Intelligence resource group')
@allowed(['eastus', 'westus2', 'westeurope'])
@metadata({
  azd: {
    type: 'location'
  }
})
param documentIntelligenceResourceGroupLocation string

param documentIntelligenceSkuName string // Set in main.parameters.json

param computerVisionServiceName string = '' // Set in main.parameters.json
param computerVisionResourceGroupName string = '' // Set in main.parameters.json
param computerVisionResourceGroupLocation string = '' // Set in main.parameters.json
param computerVisionSkuName string // Set in main.parameters.json

param contentUnderstandingServiceName string = '' // Set in main.parameters.json
param contentUnderstandingResourceGroupName string = '' // Set in main.parameters.json

@description('The name of the chat GPT model to deploy (e.g., gpt-4o-mini, gpt-35-turbo)')
param chatGptModelName string = ''
@description('The deployment name for the chat GPT model')
param chatGptDeploymentName string = ''
@description('The version of the chat GPT model to deploy')
param chatGptDeploymentVersion string = ''
@description('The SKU name for the chat GPT deployment (e.g., GlobalStandard, Standard)')
param chatGptDeploymentSkuName string = ''
@description('The capacity (TPM) for the chat GPT deployment')
param chatGptDeploymentCapacity int = 0

var chatGpt = {
  modelName: !empty(chatGptModelName) ? chatGptModelName : 'gpt-4o-mini'
  deploymentName: !empty(chatGptDeploymentName) ? chatGptDeploymentName : 'chat'
  deploymentVersion: !empty(chatGptDeploymentVersion) ? chatGptDeploymentVersion : '2024-07-18'
  deploymentSkuName: !empty(chatGptDeploymentSkuName) ? chatGptDeploymentSkuName : 'GlobalStandard' // Not backward-compatible
  deploymentCapacity: chatGptDeploymentCapacity != 0 ? chatGptDeploymentCapacity : 30
}

@description('The name of the embedding model to deploy (e.g., text-embedding-3-large, text-embedding-ada-002)')
param embeddingModelName string = ''
@description('The deployment name for the embedding model')
param embeddingDeploymentName string = ''
@description('The version of the embedding model to deploy')
param embeddingDeploymentVersion string = ''
@description('The SKU name for the embedding deployment (e.g., GlobalStandard, Standard)')
param embeddingDeploymentSkuName string = ''
@description('The capacity (TPM) for the embedding deployment')
param embeddingDeploymentCapacity int = 0
@description('The number of dimensions for the embedding model (e.g., 3072 for text-embedding-3-large)')
param embeddingDimensions int = 0
var embedding = {
  modelName: !empty(embeddingModelName) ? embeddingModelName : 'text-embedding-3-large'
  deploymentName: !empty(embeddingDeploymentName) ? embeddingDeploymentName : 'text-embedding-3-large'
  deploymentVersion: !empty(embeddingDeploymentVersion) ? embeddingDeploymentVersion : (embeddingModelName == 'text-embedding-ada-002' ? '2' : '1')
  deploymentSkuName: !empty(embeddingDeploymentSkuName) ? embeddingDeploymentSkuName : (embeddingModelName == 'text-embedding-ada-002' ? 'Standard' : 'GlobalStandard')
  deploymentCapacity: embeddingDeploymentCapacity != 0 ? embeddingDeploymentCapacity : 30
  dimensions: embeddingDimensions != 0 ? embeddingDimensions : 3072
}

param gpt4vModelName string = ''
param gpt4vDeploymentName string = ''
param gpt4vModelVersion string = ''
param gpt4vDeploymentSkuName string = ''
param gpt4vDeploymentCapacity int = 0
var gpt4v = {
  modelName: !empty(gpt4vModelName) ? gpt4vModelName : 'gpt-4o'
  deploymentName: !empty(gpt4vDeploymentName) ? gpt4vDeploymentName : 'vision'
  deploymentVersion: !empty(gpt4vModelVersion) ? gpt4vModelVersion : '2024-08-06'
  deploymentSkuName: !empty(gpt4vDeploymentSkuName) ? gpt4vDeploymentSkuName : 'GlobalStandard' // Not-backward compatible
  deploymentCapacity: gpt4vDeploymentCapacity != 0 ? gpt4vDeploymentCapacity : 10
}

param evalModelName string = ''
param evalDeploymentName string = ''
param evalModelVersion string = ''
param evalDeploymentSkuName string = ''
param evalDeploymentCapacity int = 0
var eval = {
  modelName: !empty(evalModelName) ? evalModelName : 'gpt-4o'
  deploymentName: !empty(evalDeploymentName) ? evalDeploymentName : 'eval'
  deploymentVersion: !empty(evalModelVersion) ? evalModelVersion : '2024-08-06'
  deploymentSkuName: !empty(evalDeploymentSkuName) ? evalDeploymentSkuName : 'GlobalStandard' // Not backward-compatible
  deploymentCapacity: evalDeploymentCapacity != 0 ? evalDeploymentCapacity : 30
}

param searchAgentModelName string = ''
param searchAgentDeploymentName string = ''
param searchAgentModelVersion string = ''
param searchAgentDeploymentSkuName string = ''
param searchAgentDeploymentCapacity int = 0
var searchAgent = {
  modelName: !empty(searchAgentModelName) ? searchAgentModelName : 'gpt-4o'
  deploymentName: !empty(searchAgentDeploymentName) ? searchAgentDeploymentName : 'searchagent'
  deploymentVersion: !empty(searchAgentModelVersion) ? searchAgentModelVersion : '2024-08-06'
  deploymentSkuName: !empty(searchAgentDeploymentSkuName) ? searchAgentDeploymentSkuName : 'GlobalStandard'
  deploymentCapacity: searchAgentDeploymentCapacity != 0 ? searchAgentDeploymentCapacity : 30
}


param tenantId string = tenant().tenantId
param authTenantId string = ''

// Used for the optional login and document level access control system
param useAuthentication bool = false
param enforceAccessControl bool = false
// Force using MSAL app authentication instead of built-in App Service authentication
// https://learn.microsoft.com/azure/app-service/overview-authentication-authorization
param disableAppServicesAuthentication bool = false
param enableGlobalDocuments bool = false
param enableUnauthenticatedAccess bool = false
param serverAppId string = ''
@secure()
param serverAppSecret string = ''
param clientAppId string = ''
@secure()
param clientAppSecret string = ''

// Used for optional CORS support for alternate frontends
param allowedOrigin string = '' // should start with https://, shouldn't end with a /

@allowed(['None', 'AzureServices'])
@description('If allowedIp is set, whether azure services are allowed to bypass the storage and AI services firewall.')
param bypass string = 'AzureServices'

@description('Public network access value for all deployed resources')
@allowed(['Enabled', 'Disabled'])
param publicNetworkAccess string = 'Enabled'

@description('Add a private endpoints for network connectivity')
param usePrivateEndpoint bool = false

@description('Id of the user or app to assign application roles')
param principalId string = ''

@description('Use Application Insights for monitoring and performance tracing')
param useApplicationInsights bool = false

@description('Enable language picker')
param enableLanguagePicker bool = false
@description('Use speech recognition feature in browser')
param useSpeechInputBrowser bool = false
@description('Use speech synthesis in browser')
param useSpeechOutputBrowser bool = false
@description('Use Azure speech service for reading out text')
param useSpeechOutputAzure bool = false
@description('Use chat history feature in browser')
param useChatHistoryBrowser bool = false
@description('Use chat history feature in CosmosDB')
param useChatHistoryCosmos bool = false
@description('Show options to use vector embeddings for searching in the app UI')
param useVectors bool = false
@description('Use Built-in integrated Vectorization feature of AI Search to vectorize and ingest documents')
param useIntegratedVectorization bool = false

@description('Use media description feature with Azure Content Understanding during ingestion')
param useMediaDescriberAzureCU bool = true

@description('Enable user document upload feature')
param useUserUpload bool = false
param useLocalPdfParser bool = false
param useLocalHtmlParser bool = false

@description('Use AI project')
param useAiProject bool = false

// Conditional Resource Deployment Parameters
@description('Deploy Azure AI Search Service')
param deploySearchService bool = true

@description('Deploy Azure Document Intelligence Service')
param deployDocumentIntelligence bool = true

@description('Deploy main Azure Storage Account')
param deployStorageAccount bool = true

@description('Deploy Azure Cosmos DB')
param deployCosmosDB bool = true

@description('Deploy Azure OpenAI Service')
param deployOpenAI bool = true

@description('Deploy Azure Computer Vision Service')
param deployComputerVision bool = true

@description('Deploy Azure Speech Service')
param deploySpeechService bool = true

@description('Deploy Azure Content Understanding Service')
param deployContentUnderstanding bool = true

@description('Deploy Azure Application Insights and Monitoring')
param deployMonitoring bool = true

@description('Deploy User Storage Account')
param deployUserStorage bool = true

@description('Deploy Azure Redis Cache (when implemented)')
param deployRedisCache bool = false

// Add observability parameters after existing parameters
param observabilityAlertsEnabled bool = true
param alertEmailAddress string = ''
param observabilityDashboardEnabled bool = true

var abbrs = loadJsonContent('abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var tags = { 'azd-env-name': environmentName }

var tenantIdForAuth = !empty(authTenantId) ? authTenantId : tenantId
var authenticationIssuerUri = '${environment().authentication.loginEndpoint}${tenantIdForAuth}/v2.0'

@description('Whether the deployment is running on GitHub Actions')
param runningOnGh string = ''

@description('Whether the deployment is running on Azure DevOps Pipeline')
param runningOnAdo string = ''

@description('Used by azd for containerapps deployment')
param webAppExists bool

@allowed(['Consumption', 'D4', 'D8', 'D16', 'D32', 'E4', 'E8', 'E16', 'E32', 'NC24-A100', 'NC48-A100', 'NC96-A100'])
param azureContainerAppsWorkloadProfile string

@allowed(['appservice', 'containerapps'])
param deploymentTarget string = 'appservice'
param acaIdentityName string = deploymentTarget == 'containerapps' ? '${environmentName}-aca-identity' : ''
param acaManagedEnvironmentName string = deploymentTarget == 'containerapps' ? '${environmentName}-aca-env' : ''
param containerRegistryName string = deploymentTarget == 'containerapps'
  ? '${replace(toLower(environmentName), '-', '')}acr'
  : ''

// Configure CORS for allowing different web apps to use the backend
// For more information please see https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS
var msftAllowedOrigins = [ 'https://portal.azure.com', 'https://ms.portal.azure.com' ]
var loginEndpoint = environment().authentication.loginEndpoint
var loginEndpointFixed = lastIndexOf(loginEndpoint, '/') == length(loginEndpoint) - 1 ? substring(loginEndpoint, 0, length(loginEndpoint) - 1) : loginEndpoint
var allMsftAllowedOrigins = !(empty(clientAppId)) ? union(msftAllowedOrigins, [ loginEndpointFixed ]) : msftAllowedOrigins
// Combine custom origins with Microsoft origins, remove any empty origin strings and remove any duplicate origins
var allowedOrigins = reduce(filter(union(split(allowedOrigin, ';'), allMsftAllowedOrigins), o => length(trim(o)) > 0), [], (cur, next) => union(cur, [next]))

// Organize resources in a resource group
resource resourceGroup 'Microsoft.Resources/resourceGroups@2024-11-01' = {
  name: !empty(resourceGroupName) ? resourceGroupName : '${abbrs.resourcesResourceGroups}${environmentName}'
  location: location
  tags: tags
}

resource openAiResourceGroup 'Microsoft.Resources/resourceGroups@2024-11-01' existing = if (!empty(openAiResourceGroupName)) {
  name: !empty(openAiResourceGroupName) ? openAiResourceGroupName : resourceGroup.name
}

resource documentIntelligenceResourceGroup 'Microsoft.Resources/resourceGroups@2024-11-01' existing = if (!empty(documentIntelligenceResourceGroupName)) {
  name: !empty(documentIntelligenceResourceGroupName) ? documentIntelligenceResourceGroupName : resourceGroup.name
}

resource computerVisionResourceGroup 'Microsoft.Resources/resourceGroups@2024-11-01' existing = if (!empty(computerVisionResourceGroupName)) {
  name: !empty(computerVisionResourceGroupName) ? computerVisionResourceGroupName : resourceGroup.name
}

resource contentUnderstandingResourceGroup 'Microsoft.Resources/resourceGroups@2024-11-01' existing = if (!empty(contentUnderstandingResourceGroupName)) {
  name: !empty(contentUnderstandingResourceGroupName) ? contentUnderstandingResourceGroupName : resourceGroup.name
}

resource searchServiceResourceGroup 'Microsoft.Resources/resourceGroups@2024-11-01' existing = if (!empty(searchServiceResourceGroupName)) {
  name: !empty(searchServiceResourceGroupName) ? searchServiceResourceGroupName : resourceGroup.name
}

resource storageResourceGroup 'Microsoft.Resources/resourceGroups@2024-11-01' existing = if (!empty(storageResourceGroupName)) {
  name: !empty(storageResourceGroupName) ? storageResourceGroupName : resourceGroup.name
}

resource speechResourceGroup 'Microsoft.Resources/resourceGroups@2024-11-01' existing = if (!empty(speechServiceResourceGroupName)) {
  name: !empty(speechServiceResourceGroupName) ? speechServiceResourceGroupName : resourceGroup.name
}

resource cosmosDbResourceGroup 'Microsoft.Resources/resourceGroups@2024-11-01' existing = if (!empty(cosmodDbResourceGroupName)) {
  name: !empty(cosmodDbResourceGroupName) ? cosmodDbResourceGroupName : resourceGroup.name
}

// Monitor application with Azure Monitor
module monitoring 'core/monitor/monitoring.bicep' = if (deployMonitoring && useApplicationInsights) {
  name: 'monitoring'
  scope: resourceGroup
  params: {
    location: location
    tags: tags
    applicationInsightsName: !empty(applicationInsightsName)
      ? applicationInsightsName
      : '${abbrs.insightsComponents}${resourceToken}'
    logAnalyticsName: !empty(logAnalyticsName)
      ? logAnalyticsName
      : '${abbrs.operationalInsightsWorkspaces}${resourceToken}'
    publicNetworkAccess: publicNetworkAccess
  }
}

module applicationInsightsDashboard 'backend-dashboard.bicep' = if (deployMonitoring && useApplicationInsights) {
  name: 'application-insights-dashboard'
  scope: resourceGroup
  params: {
    name: !empty(applicationInsightsDashboardName)
      ? applicationInsightsDashboardName
      : '${abbrs.portalDashboards}${resourceToken}'
    location: location
    applicationInsightsName: useApplicationInsights ? monitoring.outputs.applicationInsightsName : ''
  }
}

// Create an App Service Plan to group applications under the same payment plan and SKU
module appServicePlan 'core/host/appserviceplan.bicep' = if (deploymentTarget == 'appservice') {
  name: 'appserviceplan'
  scope: resourceGroup
  params: {
    name: !empty(appServicePlanName) ? appServicePlanName : '${abbrs.webServerFarms}${resourceToken}'
    location: location
    tags: tags
    sku: {
      name: !empty(appServiceSkuName) ? appServiceSkuName : '${appServicePlanTier}_${appServicePlanSize}'
      tier: appServicePlanTier
      size: appServicePlanSize
      capacity: appServicePlanCapacity
    }
    kind: 'linux'
  }
}

var appEnvVariables = {
  AZURE_STORAGE_ACCOUNT: deployStorageAccount ? storage.outputs.name : ''
  AZURE_STORAGE_CONTAINER: storageContainerName
  AZURE_SEARCH_INDEX: searchIndexName
  AZURE_SEARCH_AGENT: searchAgentName
  AZURE_SEARCH_SERVICE: deploySearchService ? searchService.outputs.name : ''
  AZURE_SEARCH_SEMANTIC_RANKER: actualSearchServiceSemanticRankerLevel
  AZURE_SEARCH_QUERY_REWRITING: searchServiceQueryRewriting
  AZURE_VISION_ENDPOINT: (deployComputerVision && useGPT4V) ? computerVision.outputs.endpoint : ''
  AZURE_SEARCH_QUERY_LANGUAGE: searchQueryLanguage
  AZURE_SEARCH_QUERY_SPELLER: searchQuerySpeller
  AZURE_SEARCH_FIELD_NAME_EMBEDDING: searchFieldNameEmbedding
  APPLICATIONINSIGHTS_CONNECTION_STRING: (deployMonitoring && useApplicationInsights)
    ? monitoring.outputs.applicationInsightsConnectionString
    : ''
  AZURE_SPEECH_SERVICE_ID: (deploySpeechService && useSpeechOutputAzure) ? speech.outputs.resourceId : ''
  AZURE_SPEECH_SERVICE_LOCATION: (deploySpeechService && useSpeechOutputAzure) ? speech.outputs.location : ''
  AZURE_SPEECH_SERVICE_VOICE: (deploySpeechService && useSpeechOutputAzure) ? speechServiceVoice : ''
  ENABLE_LANGUAGE_PICKER: enableLanguagePicker
  USE_SPEECH_INPUT_BROWSER: useSpeechInputBrowser
  USE_SPEECH_OUTPUT_BROWSER: useSpeechOutputBrowser
  USE_SPEECH_OUTPUT_AZURE: useSpeechOutputAzure
  USE_AGENTIC_RETRIEVAL: useAgenticRetrieval
  // Chat history settings
  USE_CHAT_HISTORY_BROWSER: useChatHistoryBrowser
  USE_CHAT_HISTORY_COSMOS: useChatHistoryCosmos
  AZURE_COSMOSDB_ACCOUNT: (deployCosmosDB && useAuthentication && useChatHistoryCosmos) ? cosmosDb.outputs.name : ''
  AZURE_CHAT_HISTORY_DATABASE: chatHistoryDatabaseName
  AZURE_CHAT_HISTORY_CONTAINER: chatHistoryContainerName
  AZURE_USER_FEEDBACK_CONTAINER: userFeedbackContainerName
  AZURE_CHAT_HISTORY_VERSION: chatHistoryVersion
  // Shared by all OpenAI deployments
  OPENAI_HOST: openAiHost
  AZURE_OPENAI_EMB_MODEL_NAME: embedding.modelName
  AZURE_OPENAI_EMB_DIMENSIONS: embedding.dimensions
  AZURE_OPENAI_CHATGPT_MODEL: chatGpt.modelName
  AZURE_OPENAI_GPT4V_MODEL: gpt4v.modelName
  AZURE_OPENAI_REASONING_EFFORT: defaultReasoningEffort
  // Specific to Azure OpenAI
  AZURE_OPENAI_SERVICE: (deployOpenAI && isAzureOpenAiHost && deployAzureOpenAi) ? openAi.outputs.name : ''
  AZURE_OPENAI_CHATGPT_DEPLOYMENT: chatGpt.deploymentName
  AZURE_OPENAI_EMB_DEPLOYMENT: embedding.deploymentName
  AZURE_OPENAI_GPT4V_DEPLOYMENT: useGPT4V ? gpt4v.deploymentName : ''
  AZURE_OPENAI_SEARCHAGENT_MODEL: searchAgent.modelName
  AZURE_OPENAI_SEARCHAGENT_DEPLOYMENT: searchAgent.deploymentName
  AZURE_OPENAI_API_VERSION: azureOpenAiApiVersion
  AZURE_OPENAI_API_KEY_OVERRIDE: azureOpenAiApiKey
  AZURE_OPENAI_CUSTOM_URL: azureOpenAiCustomUrl
  // Used only with non-Azure OpenAI deployments
  OPENAI_API_KEY: openAiApiKey
  OPENAI_ORGANIZATION: openAiApiOrganization
  // Optional login and document level access control system
  AZURE_USE_AUTHENTICATION: useAuthentication
  AZURE_ENFORCE_ACCESS_CONTROL: enforceAccessControl
  AZURE_ENABLE_GLOBAL_DOCUMENT_ACCESS: enableGlobalDocuments
  AZURE_ENABLE_UNAUTHENTICATED_ACCESS: enableUnauthenticatedAccess
  AZURE_SERVER_APP_ID: serverAppId
  AZURE_CLIENT_APP_ID: clientAppId
  AZURE_TENANT_ID: tenantId
  AZURE_AUTH_TENANT_ID: tenantIdForAuth
  AZURE_AUTHENTICATION_ISSUER_URI: authenticationIssuerUri
  // CORS support, for frontends on other hosts
  ALLOWED_ORIGIN: join(allowedOrigins, ';')
  USE_VECTORS: useVectors
  USE_GPT4V: useGPT4V
  USE_USER_UPLOAD: useUserUpload
  AZURE_USERSTORAGE_ACCOUNT: (deployUserStorage && useUserUpload) ? userStorage.outputs.name : ''
  AZURE_USERSTORAGE_CONTAINER: (deployUserStorage && useUserUpload) ? userStorageContainerName : ''
  AZURE_DOCUMENTINTELLIGENCE_SERVICE: deployDocumentIntelligence ? documentIntelligence.outputs.name : ''
  USE_LOCAL_PDF_PARSER: useLocalPdfParser
  USE_LOCAL_HTML_PARSER: useLocalHtmlParser
  USE_MEDIA_DESCRIBER_AZURE_CU: useMediaDescriberAzureCU
  AZURE_CONTENTUNDERSTANDING_ENDPOINT: (deployContentUnderstanding && useMediaDescriberAzureCU) ? contentUnderstanding.outputs.endpoint : ''
  RUNNING_IN_PRODUCTION: 'true'
  // Citation base URL configuration
  CITATION_BASE_URL: citationBaseUrl
}

// App Service for the web application (Python Quart app with JS frontend)
module backend 'core/host/appservice.bicep' = if (deploymentTarget == 'appservice') {
  name: 'web'
  scope: resourceGroup
  params: {
    name: !empty(backendServiceName) ? backendServiceName : '${abbrs.webSitesAppService}backend-${resourceToken}'
    location: location
    tags: union(tags, { 'azd-service-name': 'backend' })
    // Need to check deploymentTarget again due to https://github.com/Azure/bicep/issues/3990
    appServicePlanId: deploymentTarget == 'appservice' ? appServicePlan.outputs.id : ''
    runtimeName: 'python'
    runtimeVersion: '3.11'
    appCommandLine: 'python3 -m gunicorn main:app'
    scmDoBuildDuringDeployment: true
    managedIdentity: true
    virtualNetworkSubnetId: isolation.outputs.appSubnetId
    publicNetworkAccess: publicNetworkAccess
    allowedOrigins: allowedOrigins
    clientAppId: clientAppId
    serverAppId: serverAppId
    enableUnauthenticatedAccess: enableUnauthenticatedAccess
    disableAppServicesAuthentication: disableAppServicesAuthentication
    clientSecretSettingName: !empty(clientAppSecret) ? 'AZURE_CLIENT_APP_SECRET' : ''
    authenticationIssuerUri: authenticationIssuerUri
    // Enhanced App Service configuration using new parameters
    use32BitWorkerProcess: appServiceUse32BitWorkerProcess
    alwaysOn: appServiceAlwaysOn
    numberOfWorkers: appServiceNumberOfWorkers
    minimumElasticInstanceCount: appServiceMinimumElasticInstanceCount
    healthCheckPath: appServiceHealthCheckPath
    appSettings: union(appEnvVariables, {
      AZURE_SERVER_APP_SECRET: serverAppSecret
      AZURE_CLIENT_APP_SECRET: clientAppSecret
    })
  }
}

// Azure container apps resources (Only deployed if deploymentTarget is 'containerapps')

// User-assigned identity for pulling images from ACR
module acaIdentity 'core/security/aca-identity.bicep' = if (deploymentTarget == 'containerapps') {
  name: 'aca-identity'
  scope: resourceGroup
  params: {
    identityName: acaIdentityName
    location: location
  }
}

module containerApps 'core/host/container-apps.bicep' = if (deploymentTarget == 'containerapps') {
  name: 'container-apps'
  scope: resourceGroup
  params: {
    name: 'app'
    tags: tags
    location: location
    workloadProfile: azureContainerAppsWorkloadProfile
    containerAppsEnvironmentName: acaManagedEnvironmentName
    containerRegistryName: '${containerRegistryName}${resourceToken}'
    logAnalyticsWorkspaceResourceId: useApplicationInsights ? monitoring.outputs.logAnalyticsWorkspaceId : ''
  }
}

// Container Apps for the web application (Python Quart app with JS frontend)
module acaBackend 'core/host/container-app-upsert.bicep' = if (deploymentTarget == 'containerapps') {
  name: 'aca-web'
  scope: resourceGroup
  dependsOn: [
    containerApps
    acaIdentity
  ]
  params: {
    name: !empty(backendServiceName) ? backendServiceName : '${abbrs.webSitesContainerApps}backend-${resourceToken}'
    location: location
    identityName: (deploymentTarget == 'containerapps') ? acaIdentityName : ''
    exists: webAppExists
    workloadProfile: azureContainerAppsWorkloadProfile
    containerRegistryName: (deploymentTarget == 'containerapps') ? containerApps.outputs.registryName : ''
    containerAppsEnvironmentName: (deploymentTarget == 'containerapps') ? containerApps.outputs.environmentName : ''
    identityType: 'UserAssigned'
    tags: union(tags, { 'azd-service-name': 'backend' })
    targetPort: 8000
    containerCpuCoreCount: '1.0'
    containerMemory: '2Gi'
    containerMinReplicas: 0
    allowedOrigins: allowedOrigins
    env: union(appEnvVariables, {
      // For using managed identity to access Azure resources. See https://github.com/microsoft/azure-container-apps/issues/442
      AZURE_CLIENT_ID: (deploymentTarget == 'containerapps') ? acaIdentity.outputs.clientId : ''
    })
    secrets: useAuthentication ? {
      azureclientappsecret: clientAppSecret
      azureserverappsecret: serverAppSecret
    } : {}
    envSecrets: useAuthentication ? [
      {
        name: 'AZURE_CLIENT_APP_SECRET'
        secretRef: 'azureclientappsecret'
      }
      {
        name: 'AZURE_SERVER_APP_SECRET'
        secretRef: 'azureserverappsecret'
      }
    ] : []
  }
}

module acaAuth 'core/host/container-apps-auth.bicep' = if (deploymentTarget == 'containerapps' && !empty(clientAppId)) {
  name: 'aca-auth'
  scope: resourceGroup
  params: {
    name: acaBackend.outputs.name
    clientAppId: clientAppId
    serverAppId: serverAppId
    clientSecretSettingName: !empty(clientAppSecret) ? 'azureclientappsecret' : ''
    authenticationIssuerUri: authenticationIssuerUri
    enableUnauthenticatedAccess: enableUnauthenticatedAccess
    blobContainerUri: 'https://${storageAccountName}.blob.${environment().suffixes.storage}/${tokenStorageContainerName}'
    appIdentityResourceId: (deploymentTarget == 'appservice') ? '' : acaBackend.outputs.identityResourceId
  }
}

var defaultOpenAiDeployments = [
  {
    name: chatGpt.deploymentName
    model: {
      format: 'OpenAI'
      name: chatGpt.modelName
      version: chatGpt.deploymentVersion
    }
    sku: {
      name: chatGpt.deploymentSkuName
      capacity: chatGpt.deploymentCapacity
    }
  }
  {
    name: embedding.deploymentName
    model: {
      format: 'OpenAI'
      name: embedding.modelName
      version: embedding.deploymentVersion
    }
    sku: {
      name: embedding.deploymentSkuName
      capacity: embedding.deploymentCapacity
    }
  }
]

var openAiDeployments = concat(
  defaultOpenAiDeployments,
  useEval
    ? [
      {
        name: eval.deploymentName
        model: {
          format: 'OpenAI'
          name: eval.modelName
          version: eval.deploymentVersion
        }
        sku: {
          name: eval.deploymentSkuName
          capacity: eval.deploymentCapacity
        }
      }
    ] : [],
  useGPT4V
    ? [
        {
          name: gpt4v.deploymentName
          model: {
            format: 'OpenAI'
            name: gpt4v.modelName
            version: gpt4v.deploymentVersion
          }
          sku: {
            name: gpt4v.deploymentSkuName
            capacity: gpt4v.deploymentCapacity
          }
        }
      ]
    : [],
  useAgenticRetrieval
    ? [
        {
          name: searchAgent.deploymentName
          model: {
            format: 'OpenAI'
            name: searchAgent.modelName
            version: searchAgent.deploymentVersion
          }
          sku: {
            name: searchAgent.deploymentSkuName
            capacity: searchAgent.deploymentCapacity
          }
        }
      ]
    : []
)

module openAi 'br/public:avm/res/cognitive-services/account:0.7.2' = if (deployOpenAI && isAzureOpenAiHost && deployAzureOpenAi) {
  name: 'openai'
  scope: openAiResourceGroup
  params: {
    name: !empty(openAiServiceName) ? openAiServiceName : '${abbrs.cognitiveServicesAccounts}${resourceToken}'
    location: openAiLocation
    tags: tags
    kind: 'OpenAI'
    customSubDomainName: !empty(openAiServiceName)
      ? openAiServiceName
      : '${abbrs.cognitiveServicesAccounts}${resourceToken}'
    publicNetworkAccess: publicNetworkAccess
    networkAcls: {
      defaultAction: 'Allow'
      bypass: bypass
    }
    sku: openAiSkuName
    deployments: openAiDeployments
    disableLocalAuth: azureOpenAiDisableKeys
  }
}

// Formerly known as Form Recognizer
// Does not support bypass
module documentIntelligence 'br/public:avm/res/cognitive-services/account:0.7.2' = if (deployDocumentIntelligence) {
  name: 'documentintelligence'
  scope: documentIntelligenceResourceGroup
  params: {
    name: !empty(documentIntelligenceServiceName)
      ? documentIntelligenceServiceName
      : '${abbrs.cognitiveServicesDocumentIntelligence}${resourceToken}'
    kind: 'FormRecognizer'
    customSubDomainName: !empty(documentIntelligenceServiceName)
      ? documentIntelligenceServiceName
      : '${abbrs.cognitiveServicesDocumentIntelligence}${resourceToken}'
    publicNetworkAccess: publicNetworkAccess
    networkAcls: {
      defaultAction: 'Allow'
    }
    location: documentIntelligenceResourceGroupLocation
    disableLocalAuth: true
    tags: tags
    sku: documentIntelligenceSkuName
  }
}

module computerVision 'br/public:avm/res/cognitive-services/account:0.7.2' = if (deployComputerVision && useGPT4V) {
  name: 'computerVision'
  scope: computerVisionResourceGroup
  params: {
    name: !empty(computerVisionServiceName)
      ? computerVisionServiceName
      : '${abbrs.cognitiveServicesComputerVision}${resourceToken}'
    kind: 'ComputerVision'
    networkAcls: {
      defaultAction: 'Allow'
    }
    customSubDomainName: !empty(computerVisionServiceName)
      ? computerVisionServiceName
      : '${abbrs.cognitiveServicesComputerVision}${resourceToken}'
    location: computerVisionResourceGroupLocation
    tags: tags
    sku: computerVisionSkuName
  }
}


module contentUnderstanding 'br/public:avm/res/cognitive-services/account:0.7.2' = if (deployContentUnderstanding && useMediaDescriberAzureCU) {
  name: 'content-understanding'
  scope: contentUnderstandingResourceGroup
  params: {
    name: !empty(contentUnderstandingServiceName)
      ? contentUnderstandingServiceName
      : '${abbrs.cognitiveServicesContentUnderstanding}${resourceToken}'
    kind: 'AIServices'
    networkAcls: {
      defaultAction: 'Allow'
    }
    customSubDomainName: !empty(contentUnderstandingServiceName)
      ? contentUnderstandingServiceName
      : '${abbrs.cognitiveServicesContentUnderstanding}${resourceToken}'
    // Hard-coding to westus for now, due to limited availability and no overlap with Document Intelligence
    location: 'westus'
    tags: tags
    sku: 'S0'
  }
}

module speech 'br/public:avm/res/cognitive-services/account:0.7.2' = if (deploySpeechService && useSpeechOutputAzure) {
  name: 'speech-service'
  scope: speechResourceGroup
  params: {
    name: !empty(speechServiceName) ? speechServiceName : '${abbrs.cognitiveServicesSpeech}${resourceToken}'
    kind: 'SpeechServices'
    networkAcls: {
      defaultAction: 'Allow'
    }
    customSubDomainName: !empty(speechServiceName)
      ? speechServiceName
      : '${abbrs.cognitiveServicesSpeech}${resourceToken}'
    location: !empty(speechServiceLocation) ? speechServiceLocation : location
    tags: tags
    sku: speechServiceSkuName
  }
}
module searchService 'core/search/search-services.bicep' = if (deploySearchService) {
  name: 'search-service'
  scope: searchServiceResourceGroup
  params: {
    name: !empty(searchServiceName) ? searchServiceName : 'gptkb-${resourceToken}'
    location: !empty(searchServiceLocation) ? searchServiceLocation : location
    tags: tags
    disableLocalAuth: true
    sku: {
      name: searchServiceSkuName
    }
    semanticSearch: actualSearchServiceSemanticRankerLevel
    publicNetworkAccess: publicNetworkAccess == 'Enabled'
      ? 'enabled'
      : (publicNetworkAccess == 'Disabled' ? 'disabled' : null)
    sharedPrivateLinkStorageAccounts: usePrivateEndpoint && deployStorageAccount ? [storage.outputs.id] : []
  }
}

module searchDiagnostics 'core/search/search-diagnostics.bicep' = if (deploySearchService && deployMonitoring && useApplicationInsights) {
  name: 'search-diagnostics'
  scope: searchServiceResourceGroup
  params: {
    searchServiceName: searchService.outputs.name
    workspaceId: useApplicationInsights ? monitoring.outputs.logAnalyticsWorkspaceId : ''
  }
}

module storage 'core/storage/storage-account.bicep' = if (deployStorageAccount) {
  name: 'storage'
  scope: storageResourceGroup
  params: {
    name: !empty(storageAccountName) ? storageAccountName : '${abbrs.storageStorageAccounts}${resourceToken}'
    location: storageResourceGroupLocation
    tags: tags
    publicNetworkAccess: publicNetworkAccess
    bypass: bypass
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    sku: {
      name: storageSkuName
    }
    deleteRetentionPolicy: {
      enabled: true
      days: 2
    }
    containers: [
      {
        name: storageContainerName
        publicAccess: 'None'
      }
      {
        name: tokenStorageContainerName
        publicAccess: 'None'
      }
    ]
  }
}

module userStorage 'core/storage/storage-account.bicep' = if (deployUserStorage && useUserUpload) {
  name: 'user-storage'
  scope: storageResourceGroup
  params: {
    name: !empty(userStorageAccountName)
      ? userStorageAccountName
      : 'user${abbrs.storageStorageAccounts}${resourceToken}'
    location: storageResourceGroupLocation
    tags: tags
    publicNetworkAccess: publicNetworkAccess
    bypass: bypass
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    isHnsEnabled: true
    sku: {
      name: storageSkuName
    }
    containers: [
      {
        name: userStorageContainerName
        publicAccess: 'None'
      }
    ]
  }
}

module cosmosDb 'br/public:avm/res/document-db/database-account:0.6.1' = if (deployCosmosDB && useAuthentication && useChatHistoryCosmos) {
  name: 'cosmosdb'
  scope: cosmosDbResourceGroup
  params: {
    name: !empty(cosmosDbAccountName) ? cosmosDbAccountName : '${abbrs.documentDBDatabaseAccounts}${resourceToken}'
    location: !empty(cosmosDbLocation) ? cosmosDbLocation : location
    
    // Enhanced region configuration with support for additional regions
    locations: concat([
      {
        locationName: !empty(cosmosDbLocation) ? cosmosDbLocation : location
        failoverPriority: 0
        isZoneRedundant: cosmosDbEnableZoneRedundancy
      }
    ], cosmosDbAdditionalRegions)
    
    // Enhanced consistency configuration using individual parameters
    defaultConsistencyLevel: cosmosDbConsistencyLevel
    maxStalenessPrefix: cosmosDbConsistencyLevel == 'BoundedStaleness' ? cosmosDbMaxStalenessPrefix : null
    maxIntervalInSeconds: cosmosDbConsistencyLevel == 'BoundedStaleness' ? cosmosDbMaxIntervalInSeconds : null
    
    // Enhanced backup configuration using individual parameters
    backupPolicyType: cosmosDbBackupPolicyType
    backupIntervalInMinutes: cosmosDbBackupPolicyType == 'Periodic' ? cosmosDbBackupIntervalInMinutes : null
    backupRetentionIntervalInHours: cosmosDbBackupPolicyType == 'Periodic' ? cosmosDbBackupRetentionInHours : null
    backupStorageRedundancy: cosmosDbBackupPolicyType == 'Periodic' && cosmosDbGeoRedundantBackup ? 'Geo' : 'Local'
    
    enableFreeTier: cosmosDbSkuName == 'free'
    capabilitiesToAdd: concat(
      cosmosDbSkuName == 'serverless' ? ['EnableServerless'] : [],
      cosmosDbEnableAnalyticalStorage ? ['EnableAnalyticalStorage'] : []
    )
    
    // Enhanced networking configuration
    networkRestrictions: {
      ipRules: []
      networkAclBypass: cosmosDbNetworkAclBypass
      publicNetworkAccess: publicNetworkAccess
      virtualNetworkRules: []
    }
    
    // Multi-write locations configuration
    enableMultipleWriteLocations: cosmosDbEnableMultipleWriteLocations
    
    // Analytical storage configuration
    enableAnalyticalStorage: cosmosDbEnableAnalyticalStorage
    
    sqlDatabases: [
      {
        name: chatHistoryDatabaseName
        // Enhanced throughput configuration with autoscale support
        throughput: cosmosDbSkuName == 'serverless' ? null : (cosmosDbEnableAutoscale ? null : cosmosDbThroughput)
        autoscaleSettingsMaxThroughput: cosmosDbSkuName == 'serverless' ? null : (cosmosDbEnableAutoscale ? cosmosDbAutoscaleMaxThroughput : null)
        containers: [
          {
            name: chatHistoryContainerName
            kind: 'MultiHash'
            paths: [
              '/entra_oid'
              '/session_id'
            ]
            // Enhanced analytical storage configuration
            analyticalStorageTtl: cosmosDbEnableAnalyticalStorage ? cosmosDbAnalyticalStoreTtl : null
            indexingPolicy: {
              indexingMode: 'consistent'
              automatic: true
              includedPaths: [
                {
                  path: '/entra_oid/?'
                }
                {
                  path: '/session_id/?'
                }
                {
                  path: '/messageId/?'
                }
                {
                  path: '/timestamp/?'
                }
                {
                  path: '/type/?'
                }
              ]
              excludedPaths: [
                {
                  path: '/*'
                }
              ]
            }
          }
          {
            name: userFeedbackContainerName
            kind: 'MultiHash'
            paths: [
              '/userId'
              '/sessionId'
            ]
            // Enhanced analytical storage configuration
            analyticalStorageTtl: cosmosDbEnableAnalyticalStorage ? cosmosDbAnalyticalStoreTtl : null
            indexingPolicy: {
              indexingMode: 'consistent'
              automatic: true
              includedPaths: [
                {
                  path: '/userId/?'
                }
                {
                  path: '/sessionId/?'
                }
                {
                  path: '/messageId/?'
                }
                {
                  path: '/timestamp/?'
                }
                {
                  path: '/rating/?'
                }
                {
                  path: '/type/?'
                }
              ]
              excludedPaths: [
                {
                  path: '/*'
                }
              ]
              compositeIndexes: [
                [
                  {
                    path: '/sessionId'
                    order: 'ascending'
                  }
                  {
                    path: '/timestamp'
                    order: 'ascending'
                  }
                ]
                [
                  {
                    path: '/userId'
                    order: 'ascending'
                  }
                  {
                    path: '/rating'
                    order: 'ascending'
                  }
                  {
                    path: '/timestamp'
                    order: 'descending'
                  }
                ]
              ]
            }
          }
        ]
      }
    ]
  }
}

module ai 'core/ai/ai-environment.bicep' = if (useAiProject) {
  name: 'ai'
  scope: resourceGroup
  params: {
    // Limited region support: https://learn.microsoft.com/azure/ai-foundry/how-to/develop/evaluate-sdk#region-support
    location: 'eastus2'
    tags: tags
    hubName: 'aihub-${resourceToken}'
    projectName: 'aiproj-${resourceToken}'
    storageAccountId: storage.outputs.id
    applicationInsightsId: !useApplicationInsights ? '' : monitoring.outputs.applicationInsightsId
  }
}


// USER ROLES
var principalType = empty(runningOnGh) && empty(runningOnAdo) ? 'User' : 'ServicePrincipal'

module openAiRoleUser 'core/security/role.bicep' = if (isAzureOpenAiHost && deployAzureOpenAi) {
  scope: openAiResourceGroup
  name: 'openai-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
    principalType: principalType
  }
}

// For both document intelligence and computer vision
module cognitiveServicesRoleUser 'core/security/role.bicep' = {
  scope: resourceGroup
  name: 'cognitiveservices-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: 'a97b65f3-24c7-4388-baec-2e87135dc908'
    principalType: principalType
  }
}

module speechRoleUser 'core/security/role.bicep' = {
  scope: speechResourceGroup
  name: 'speech-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: 'f2dc8367-1007-4938-bd23-fe263f013447'
    principalType: principalType
  }
}

module storageRoleUser 'core/security/role.bicep' = {
  scope: storageResourceGroup
  name: 'storage-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'
    principalType: principalType
  }
}

module storageContribRoleUser 'core/security/role.bicep' = {
  scope: storageResourceGroup
  name: 'storage-contrib-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
    principalType: principalType
  }
}

module storageOwnerRoleUser 'core/security/role.bicep' = if (useUserUpload) {
  scope: storageResourceGroup
  name: 'storage-owner-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b'
    principalType: principalType
  }
}

module searchRoleUser 'core/security/role.bicep' = {
  scope: searchServiceResourceGroup
  name: 'search-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: '1407120a-92aa-4202-b7e9-c0e197c71c8f'
    principalType: principalType
  }
}

module searchContribRoleUser 'core/security/role.bicep' = {
  scope: searchServiceResourceGroup
  name: 'search-contrib-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
    principalType: principalType
  }
}

module searchSvcContribRoleUser 'core/security/role.bicep' = {
  scope: searchServiceResourceGroup
  name: 'search-svccontrib-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: '7ca78c08-252a-4471-8644-bb5ff32d4ba0'
    principalType: principalType
  }
}

module cosmosDbAccountContribRoleUser 'core/security/role.bicep' = if (useAuthentication && useChatHistoryCosmos) {
  scope: cosmosDbResourceGroup
  name: 'cosmosdb-account-contrib-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: '5bd9cd88-fe45-4216-938b-f97437e15450'
    principalType: principalType
  }
}

// RBAC for Cosmos DB
// https://learn.microsoft.com/azure/cosmos-db/nosql/security/how-to-grant-data-plane-role-based-access
module cosmosDbDataContribRoleUser 'core/security/documentdb-sql-role.bicep' = if (useAuthentication && useChatHistoryCosmos) {
  scope: cosmosDbResourceGroup
  name: 'cosmosdb-data-contrib-role-user'
  params: {
    databaseAccountName: (useAuthentication && useChatHistoryCosmos) ? cosmosDb.outputs.name : ''
    principalId: principalId
    // Cosmos DB Built-in Data Contributor role
    roleDefinitionId: (useAuthentication && useChatHistoryCosmos)
      ? '/${subscription().id}/resourceGroups/${cosmosDb.outputs.resourceGroupName}/providers/Microsoft.DocumentDB/databaseAccounts/${cosmosDb.outputs.name}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002'
      : ''
  }
}

// SYSTEM IDENTITIES
module openAiRoleBackend 'core/security/role.bicep' = if (isAzureOpenAiHost && deployAzureOpenAi) {
  scope: openAiResourceGroup
  name: 'openai-role-backend'
  params: {
    principalId: (deploymentTarget == 'appservice')
      ? backend.outputs.identityPrincipalId
      : acaBackend.outputs.identityPrincipalId
    roleDefinitionId: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
    principalType: 'ServicePrincipal'
  }
}

module openAiRoleSearchService 'core/security/role.bicep' = if (isAzureOpenAiHost && deployAzureOpenAi && (useIntegratedVectorization || useAgenticRetrieval)) {
  scope: openAiResourceGroup
  name: 'openai-role-searchservice'
  params: {
    principalId: searchService.outputs.principalId
    roleDefinitionId: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
    principalType: 'ServicePrincipal'
  }
}

module storageRoleBackend 'core/security/role.bicep' = {
  scope: storageResourceGroup
  name: 'storage-role-backend'
  params: {
    principalId: (deploymentTarget == 'appservice')
      ? backend.outputs.identityPrincipalId
      : acaBackend.outputs.identityPrincipalId
    roleDefinitionId: '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'
    principalType: 'ServicePrincipal'
  }
}

module storageOwnerRoleBackend 'core/security/role.bicep' = if (useUserUpload) {
  scope: storageResourceGroup
  name: 'storage-owner-role-backend'
  params: {
    principalId: (deploymentTarget == 'appservice')
      ? backend.outputs.identityPrincipalId
      : acaBackend.outputs.identityPrincipalId
    roleDefinitionId: 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b'
    principalType: 'ServicePrincipal'
  }
}

module storageRoleSearchService 'core/security/role.bicep' = if (useIntegratedVectorization) {
  scope: storageResourceGroup
  name: 'storage-role-searchservice'
  params: {
    principalId: searchService.outputs.principalId
    roleDefinitionId: '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'
    principalType: 'ServicePrincipal'
  }
}

// Used to issue search queries
// https://learn.microsoft.com/azure/search/search-security-rbac
module searchRoleBackend 'core/security/role.bicep' = {
  scope: searchServiceResourceGroup
  name: 'search-role-backend'
  params: {
    principalId: (deploymentTarget == 'appservice')
      ? backend.outputs.identityPrincipalId
      : acaBackend.outputs.identityPrincipalId
    roleDefinitionId: '1407120a-92aa-4202-b7e9-c0e197c71c8f'
    principalType: 'ServicePrincipal'
  }
}

module speechRoleBackend 'core/security/role.bicep' = {
  scope: speechResourceGroup
  name: 'speech-role-backend'
  params: {
    principalId: (deploymentTarget == 'appservice')
      ? backend.outputs.identityPrincipalId
      : acaBackend.outputs.identityPrincipalId
    roleDefinitionId: 'f2dc8367-1007-4938-bd23-fe263f013447'
    principalType: 'ServicePrincipal'
  }
}

// RBAC for Cosmos DB
// https://learn.microsoft.com/azure/cosmos-db/nosql/security/how-to-grant-data-plane-role-based-access
module cosmosDbRoleBackend 'core/security/documentdb-sql-role.bicep' = if (useAuthentication && useChatHistoryCosmos) {
  scope: cosmosDbResourceGroup
  name: 'cosmosdb-role-backend'
  params: {
    databaseAccountName: (useAuthentication && useChatHistoryCosmos) ? cosmosDb.outputs.name : ''
    principalId: (deploymentTarget == 'appservice')
      ? backend.outputs.identityPrincipalId
      : acaBackend.outputs.identityPrincipalId
    // Cosmos DB Built-in Data Contributor role
    roleDefinitionId: (useAuthentication && useChatHistoryCosmos)
      ? '/${subscription().id}/resourceGroups/${cosmosDb.outputs.resourceGroupName}/providers/Microsoft.DocumentDB/databaseAccounts/${cosmosDb.outputs.name}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002'
      : ''
  }
}

module isolation 'network-isolation.bicep' = {
  name: 'networks'
  scope: resourceGroup
  params: {
    deploymentTarget: deploymentTarget
    location: location
    tags: tags
    vnetName: '${abbrs.virtualNetworks}${resourceToken}'
    // Need to check deploymentTarget due to https://github.com/Azure/bicep/issues/3990
    appServicePlanName: deploymentTarget == 'appservice' ? appServicePlan.outputs.name : ''
    usePrivateEndpoint: usePrivateEndpoint
    // Enhanced networking configuration parameters
    vnetEnableCustomConfiguration: vnetEnableCustomConfiguration
    vnetAddressPrefix: vnetAddressPrefix
    appSubnetAddressPrefix: appSubnetAddressPrefix
    backendSubnetAddressPrefix: backendSubnetAddressPrefix
    privateEndpointSubnetAddressPrefix: privateEndpointSubnetAddressPrefix
    vmSubnetAddressPrefix: vmSubnetAddressPrefix
    enableServiceEndpoints: enableServiceEndpoints
    serviceEndpoints: serviceEndpoints
    enableCustomNsgRules: enableCustomNsgRules
    allowedInboundPorts: allowedInboundPorts
    allowedOutboundPorts: allowedOutboundPorts
    allowedSourceAddressPrefixes: allowedSourceAddressPrefixes
    allowedDestinationAddressPrefixes: allowedDestinationAddressPrefixes
    nsgRulePriorityStart: nsgRulePriorityStart
  }
}

var environmentData = environment()

var openAiPrivateEndpointConnection = (deployOpenAI && isAzureOpenAiHost && deployAzureOpenAi && deploymentTarget == 'appservice')
  ? [
      {
        groupId: 'account'
        dnsZoneName: 'privatelink.openai.azure.com'
        resourceIds: concat(
          deployOpenAI ? [openAi.outputs.resourceId] : [],
          (deployComputerVision && useGPT4V) ? [computerVision.outputs.resourceId] : [],
          (deployContentUnderstanding && useMediaDescriberAzureCU) ? [contentUnderstanding.outputs.resourceId] : [],
          (deployDocumentIntelligence && !useLocalPdfParser) ? [documentIntelligence.outputs.resourceId] : []
        )
      }
    ]
  : []
var otherPrivateEndpointConnections = (usePrivateEndpoint && deploymentTarget == 'appservice')
  ? [
      {
        groupId: 'blob'
        dnsZoneName: 'privatelink.blob.${environmentData.suffixes.storage}'
        resourceIds: concat(
          deployStorageAccount ? [storage.outputs.id] : [], 
          (deployUserStorage && useUserUpload) ? [userStorage.outputs.id] : []
        )
      }
      {
        groupId: 'searchService'
        dnsZoneName: 'privatelink.search.windows.net'
        resourceIds: deploySearchService ? [searchService.outputs.id] : []
      }
      {
        groupId: 'sites'
        dnsZoneName: 'privatelink.azurewebsites.net'
        resourceIds: [backend.outputs.id]
      }
      {
        groupId: 'sql'
        dnsZoneName: 'privatelink.documents.azure.com'
        resourceIds: (deployCosmosDB && useAuthentication && useChatHistoryCosmos) ? [cosmosDb.outputs.resourceId] : []
      }
    ]
  : []

var privateEndpointConnections = concat(otherPrivateEndpointConnections, openAiPrivateEndpointConnection)

module privateEndpoints 'private-endpoints.bicep' = if (usePrivateEndpoint && deploymentTarget == 'appservice') {
  name: 'privateEndpoints'
  scope: resourceGroup
  params: {
    location: location
    tags: tags
    resourceToken: resourceToken
    privateEndpointConnections: privateEndpointConnections
    applicationInsightsId: useApplicationInsights ? monitoring.outputs.applicationInsightsId : ''
    logAnalyticsWorkspaceId: useApplicationInsights ? monitoring.outputs.logAnalyticsWorkspaceId : ''
    vnetName: isolation.outputs.vnetName
    vnetPeSubnetName: isolation.outputs.backendSubnetId
  }
}

// Used to read index definitions (required when using authentication)
// https://learn.microsoft.com/azure/search/search-security-rbac
module searchReaderRoleBackend 'core/security/role.bicep' = if (deploySearchService && useAuthentication) {
  scope: searchServiceResourceGroup
  name: 'search-reader-role-backend'
  params: {
    principalId: (deploymentTarget == 'appservice')
      ? backend.outputs.identityPrincipalId
      : acaBackend.outputs.identityPrincipalId
    roleDefinitionId: 'acdd72a7-3385-48ef-bd42-f606fba81ae7'
    principalType: 'ServicePrincipal'
  }
}

// Used to add/remove documents from index (required for user upload feature)
module searchContribRoleBackend 'core/security/role.bicep' = if (deploySearchService && useUserUpload) {
  scope: searchServiceResourceGroup
  name: 'search-contrib-role-backend'
  params: {
    principalId: (deploymentTarget == 'appservice')
      ? backend.outputs.identityPrincipalId
      : acaBackend.outputs.identityPrincipalId
    roleDefinitionId: '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
    principalType: 'ServicePrincipal'
  }
}

// For computer vision access by the backend
module computerVisionRoleBackend 'core/security/role.bicep' = if (deployComputerVision && useGPT4V) {
  scope: computerVisionResourceGroup
  name: 'computervision-role-backend'
  params: {
    principalId: (deploymentTarget == 'appservice')
      ? backend.outputs.identityPrincipalId
      : acaBackend.outputs.identityPrincipalId
    roleDefinitionId: 'a97b65f3-24c7-4388-baec-2e87135dc908'
    principalType: 'ServicePrincipal'
  }
}

// For document intelligence access by the backend
module documentIntelligenceRoleBackend 'core/security/role.bicep' = if (deployDocumentIntelligence && useUserUpload) {
  scope: documentIntelligenceResourceGroup
  name: 'documentintelligence-role-backend'
  params: {
    principalId: (deploymentTarget == 'appservice')
      ? backend.outputs.identityPrincipalId
      : acaBackend.outputs.identityPrincipalId
    roleDefinitionId: 'a97b65f3-24c7-4388-baec-2e87135dc908'
    principalType: 'ServicePrincipal'
  }
}

// Enhanced Observability with Alerts
module observabilityAlerts 'observability-alerts.bicep' = if (useApplicationInsights && observabilityAlertsEnabled && deployMonitoring) {
  name: 'observability-alerts'
  params: {
    applicationInsightsName: monitoring.outputs.applicationInsightsName
    alertEmailAddress: alertEmailAddress
    environment: environmentName
  }
}

// RAG-Specific Dashboard  
module ragDashboard 'rag-dashboard.bicep' = if (useApplicationInsights && observabilityDashboardEnabled && deployMonitoring) {
  name: 'rag-dashboard'
  params: {
    applicationInsightsName: monitoring.outputs.applicationInsightsName
    dashboardName: '${resourceToken}-rag-dashboard'
  }
}

// =============================================================================
// ESSENTIAL OUTPUTS - Core values needed by deployment scripts and CI/CD
// =============================================================================

output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = tenantId
output AZURE_AUTH_TENANT_ID string = authTenantId
output AZURE_RESOURCE_GROUP string = resourceGroup.name

output BACKEND_URI string = deploymentTarget == 'appservice' ? backend.outputs.uri : acaBackend.outputs.uri
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = deploymentTarget == 'containerapps'
  ? containerApps.outputs.registryLoginServer
  : ''

output AZURE_USE_AUTHENTICATION bool = useAuthentication

// =============================================================================
// AI SERVICES CONFIGURATION - Consolidated OpenAI and AI services information
// =============================================================================

output OPENAI_CONFIGURATION object = {
  host: openAiHost
  isAzureHost: isAzureOpenAiHost
  // Service details
  serviceName: (deployOpenAI && isAzureOpenAiHost && deployAzureOpenAi) ? openAi.outputs.name : ''
  endpoint: isAzureOpenAiHost && deployAzureOpenAi ? openAi.outputs.endpoint : ''
  apiVersion: isAzureOpenAiHost ? azureOpenAiApiVersion : ''
  resourceGroup: isAzureOpenAiHost ? openAiResourceGroup.name : ''
  resourceId: (deployOpenAI && isAzureOpenAiHost && deployAzureOpenAi) ? openAi.outputs.resourceId : ''
  // Model configurations
  chatGpt: {
    modelName: chatGpt.modelName
    deploymentName: isAzureOpenAiHost ? chatGpt.deploymentName : ''
    deploymentVersion: isAzureOpenAiHost ? chatGpt.deploymentVersion : ''
    deploymentSku: isAzureOpenAiHost ? chatGpt.deploymentSkuName : ''
  }
  embedding: {
    modelName: embedding.modelName
    dimensions: embedding.dimensions
    deploymentName: isAzureOpenAiHost ? embedding.deploymentName : ''
    deploymentVersion: isAzureOpenAiHost ? embedding.deploymentVersion : ''
    deploymentSku: isAzureOpenAiHost ? embedding.deploymentSkuName : ''
  }
  gpt4v: {
    modelName: gpt4v.modelName
    deploymentName: isAzureOpenAiHost && useGPT4V ? gpt4v.deploymentName : ''
    deploymentVersion: isAzureOpenAiHost && useGPT4V ? gpt4v.deploymentVersion : ''
    deploymentSku: isAzureOpenAiHost && useGPT4V ? gpt4v.deploymentSkuName : ''
    enabled: useGPT4V
  }
  eval: {
    modelName: isAzureOpenAiHost && useEval ? eval.modelName : ''
    deploymentName: isAzureOpenAiHost && useEval ? eval.deploymentName : ''
    deploymentVersion: isAzureOpenAiHost && useEval ? eval.deploymentVersion : ''
    deploymentSku: isAzureOpenAiHost && useEval ? eval.deploymentSkuName : ''
    enabled: useEval
  }
  searchAgent: {
    modelName: isAzureOpenAiHost && useAgenticRetrieval ? searchAgent.modelName : ''
    deploymentName: isAzureOpenAiHost && useAgenticRetrieval ? searchAgent.deploymentName : ''
    enabled: useAgenticRetrieval
  }
  reasoningEffort: defaultReasoningEffort
}

output COGNITIVE_SERVICES object = {
  computerVision: {
    resourceId: (deployComputerVision && useGPT4V) ? computerVision.outputs.resourceId : ''
    endpoint: (deployComputerVision && useGPT4V) ? computerVision.outputs.endpoint : ''
    deployed: deployComputerVision && useGPT4V
  }
  documentIntelligence: {
    serviceName: deployDocumentIntelligence ? documentIntelligence.outputs.name : ''
    resourceId: deployDocumentIntelligence ? documentIntelligence.outputs.resourceId : ''
    endpoint: deployDocumentIntelligence ? documentIntelligence.outputs.endpoint : ''
    resourceGroup: documentIntelligenceResourceGroup.name
    deployed: deployDocumentIntelligence
  }
  speechService: {
    resourceId: (deploySpeechService && useSpeechOutputAzure) ? speech.outputs.resourceId : ''
    endpoint: (deploySpeechService && useSpeechOutputAzure) ? speech.outputs.endpoint : ''
    location: (deploySpeechService && useSpeechOutputAzure) ? speech.outputs.location : ''
    deployed: deploySpeechService && useSpeechOutputAzure
  }
  contentUnderstanding: {
    resourceId: (deployContentUnderstanding && useMediaDescriberAzureCU) ? contentUnderstanding.outputs.resourceId : ''
    endpoint: (deployContentUnderstanding && useMediaDescriberAzureCU) ? contentUnderstanding.outputs.endpoint : ''
    deployed: deployContentUnderstanding && useMediaDescriberAzureCU
  }
}

// =============================================================================
// SEARCH CONFIGURATION - Azure AI Search service details
// =============================================================================

output SEARCH_CONFIGURATION object = {
  serviceName: deploySearchService ? searchService.outputs.name : ''
  resourceId: deploySearchService ? searchService.outputs.id : ''
  endpoint: deploySearchService ? searchService.outputs.endpoint : ''
  resourceGroup: searchServiceResourceGroup.name
  principalId: deploySearchService ? searchService.outputs.principalId : ''
  indexName: searchIndexName
  agentName: searchAgentName
  semanticRanker: actualSearchServiceSemanticRankerLevel
  fieldNameEmbedding: searchFieldNameEmbedding
  deployed: deploySearchService
}

// =============================================================================
// STORAGE CONFIGURATION - Storage accounts and containers
// =============================================================================

output STORAGE_CONFIGURATION object = {
  mainStorage: {
    accountName: deployStorageAccount ? storage.outputs.name : ''
    resourceId: deployStorageAccount ? storage.outputs.id : ''
    primaryEndpoint: deployStorageAccount ? storage.outputs.primaryEndpoints.blob : ''
    containerName: storageContainerName
    resourceGroup: storageResourceGroup.name
    deployed: deployStorageAccount
  }
  userStorage: {
    accountName: (deployUserStorage && useUserUpload) ? userStorage.outputs.name : ''
    resourceId: (deployUserStorage && useUserUpload) ? userStorage.outputs.id : ''
    primaryEndpoint: (deployUserStorage && useUserUpload) ? userStorage.outputs.primaryEndpoints.blob : ''
    containerName: (deployUserStorage && useUserUpload) ? userStorageContainerName : ''
    resourceGroup: storageResourceGroup.name
    deployed: deployUserStorage && useUserUpload
  }
}

// =============================================================================
// DATABASE CONFIGURATION - Cosmos DB configuration
// =============================================================================

output DATABASE_CONFIGURATION object = {
  cosmosDb: {
    accountName: (deployCosmosDB && useAuthentication && useChatHistoryCosmos) ? cosmosDb.outputs.name : ''
    resourceId: (deployCosmosDB && useAuthentication && useChatHistoryCosmos) ? cosmosDb.outputs.resourceId : ''
    endpoint: (deployCosmosDB && useAuthentication && useChatHistoryCosmos) ? cosmosDb.outputs.endpoint : ''
    databaseName: chatHistoryDatabaseName
    chatHistoryContainer: chatHistoryContainerName
    userFeedbackContainer: userFeedbackContainerName
    version: chatHistoryVersion
    deployed: deployCosmosDB && useAuthentication && useChatHistoryCosmos
  }
}

// =============================================================================
// NETWORK CONFIGURATION - VNet and security settings
// =============================================================================

output NETWORK_CONFIGURATION object = {
  vnet: {
    name: isolation.outputs.vnetName
    customConfigEnabled: vnetEnableCustomConfiguration
  }
  subnets: {
    backend: isolation.outputs.backendSubnetId
    app: isolation.outputs.appSubnetId
  }
  security: {
    usePrivateEndpoints: usePrivateEndpoint
    publicNetworkAccess: publicNetworkAccess
    customNsgRules: enableCustomNsgRules
  }
}

// =============================================================================
// SECURITY CONFIGURATION - Identity and authentication details
// =============================================================================

output SECURITY_CONFIGURATION object = {
  authentication: {
    enabled: useAuthentication
    accessControlEnabled: enforceAccessControl
    tenantId: tenantId
    authTenantId: tenantIdForAuth
    issuerUri: authenticationIssuerUri
  }
  managedIdentity: {
    backendPrincipalId: deploymentTarget == 'appservice' ? backend.outputs.identityPrincipalId : acaBackend.outputs.identityPrincipalId
    searchServicePrincipalId: deploySearchService ? searchService.outputs.principalId : ''
  }
}

// =============================================================================
// FEATURE FLAGS - Application features and capabilities
// =============================================================================

output FEATURE_FLAGS object = {
  ai: {
    useVectors: useVectors
    useGPT4V: useGPT4V
    useEval: useEval
    useAgenticRetrieval: useAgenticRetrieval
    useIntegratedVectorization: useIntegratedVectorization
  }
  ui: {
    enableLanguagePicker: enableLanguagePicker
    useSpeechInputBrowser: useSpeechInputBrowser
    useSpeechOutputBrowser: useSpeechOutputBrowser
    useSpeechOutputAzure: useSpeechOutputAzure
    useChatHistoryBrowser: useChatHistoryBrowser
    useChatHistoryCosmos: useChatHistoryCosmos
  }
  data: {
    useUserUpload: useUserUpload
    useLocalPdfParser: useLocalPdfParser
    useLocalHtmlParser: useLocalHtmlParser
    useMediaDescriberAzureCU: useMediaDescriberAzureCU
  }
  citation: {
    baseUrl: citationBaseUrl
  }
}

// =============================================================================
// DEPLOYMENT STATUS - Service deployment indicators
// =============================================================================

output DEPLOYMENT_STATUS object = {
  services: {
    searchService: deploySearchService
    storageAccount: deployStorageAccount
    cosmosDb: deployCosmosDB
    openAi: deployOpenAI
    documentIntelligence: deployDocumentIntelligence
    computerVision: deployComputerVision
    speechService: deploySpeechService
    contentUnderstanding: deployContentUnderstanding
    monitoring: deployMonitoring
    userStorage: deployUserStorage
    redisCache: deployRedisCache
  }
  target: deploymentTarget
  environment: environmentName
}

// =============================================================================
// AI PROJECT - AI Foundry project details (if enabled)
// =============================================================================

output AI_PROJECT object = {
  projectName: useAiProject ? ai.outputs.projectName : ''
  enabled: useAiProject
}

// =============================================================================
// ENVIRONMENT SUMMARY - Complete environment overview for dashboards
// =============================================================================

output ENVIRONMENT_SUMMARY object = {
  location: location
  environmentName: environmentName
  resourceGroup: resourceGroup.name
  deploymentTarget: deploymentTarget
  servicesDeployed: {
    search: deploySearchService
    storage: deployStorageAccount
    cosmosDb: deployCosmosDB
    openAi: deployOpenAI
    documentIntelligence: deployDocumentIntelligence
    computerVision: deployComputerVision
    speechService: deploySpeechService
    contentUnderstanding: deployContentUnderstanding
    monitoring: deployMonitoring
    userStorage: deployUserStorage
    redisCache: deployRedisCache
  }
  featuresEnabled: {
    authentication: useAuthentication
    privateEndpoints: usePrivateEndpoint
    vectors: useVectors
    gpt4v: useGPT4V
    evaluation: useEval
    speechInput: useSpeechInputBrowser
    speechOutputBrowser: useSpeechOutputBrowser
    speechOutputAzure: useSpeechOutputAzure
    chatHistoryCosmos: useChatHistoryCosmos
    integratedVectorization: useIntegratedVectorization
    userUpload: useUserUpload
    agenticRetrieval: useAgenticRetrieval
    citationBaseUrl: !empty(citationBaseUrl)
  }
}

output OBSERVABILITY_ALERTS_ENABLED bool = observabilityAlertsEnabled
output OBSERVABILITY_DASHBOARD_ENABLED bool = observabilityDashboardEnabled
output ALERT_ACTION_GROUP_ID string = observabilityAlertsEnabled && useApplicationInsights ? observabilityAlerts.outputs.actionGroupId : ''
output RAG_DASHBOARD_ID string = observabilityDashboardEnabled && useApplicationInsights ? ragDashboard.outputs.dashboardId : ''
