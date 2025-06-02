metadata description = 'Sets up private networking for all resources, using VNet, private endpoints, and DNS zones.'

@description('The name of the VNet to create')
param vnetName string

@description('The location to create the VNet and private endpoints')
param location string = resourceGroup().location

@description('The tags to apply to all resources')
param tags object = {}

@description('The name of an existing App Service Plan to connect to the VNet')
param appServicePlanName string

param usePrivateEndpoint bool = false

@allowed(['appservice', 'containerapps'])
param deploymentTarget string

// Enhanced Networking Configuration Parameters
@description('Enable custom VNet configuration (overrides default settings)')
param vnetEnableCustomConfiguration bool = false

@description('Custom VNet address prefix (CIDR notation)')
param vnetAddressPrefix string = '10.0.0.0/16'

@description('App Service integration subnet address prefix')
param appSubnetAddressPrefix string = '10.0.3.0/24'

@description('Backend services subnet address prefix')
param backendSubnetAddressPrefix string = '10.0.1.0/24'

@description('Private endpoints subnet address prefix (used for AzureBastionSubnet in current implementation)')
param privateEndpointSubnetAddressPrefix string = '10.0.2.0/24'

@description('Virtual machine subnet address prefix')
param vmSubnetAddressPrefix string = '10.0.4.0/24'

@description('Enable service endpoints for subnets')
param enableServiceEndpoints bool = false

@description('Service endpoints to enable (e.g., Microsoft.Storage, Microsoft.KeyVault)')
param serviceEndpoints array = ['Microsoft.Storage', 'Microsoft.KeyVault', 'Microsoft.AzureCosmosDB']

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

resource appServicePlan 'Microsoft.Web/serverfarms@2022-03-01' existing = if (deploymentTarget == 'appservice') {
  name: appServicePlanName
}

// Generate service endpoints array based on configuration
var serviceEndpointsEnabled = enableServiceEndpoints

// Create a basic Network Security Group if custom rules are enabled
// Note: Complex rule generation will be added in future iterations
resource networkSecurityGroup 'Microsoft.Network/networkSecurityGroups@2023-05-01' = if (enableCustomNsgRules && usePrivateEndpoint) {
  name: '${vnetName}-nsg'
  location: location
  tags: tags
  properties: {
    securityRules: [
      {
        name: 'AllowHttps'
        properties: {
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '443'
          sourceAddressPrefix: '*'
          destinationAddressPrefix: '*'
          access: 'Allow'
          priority: 1000
          direction: 'Inbound'
        }
      }
      {
        name: 'AllowHttp'
        properties: {
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '80'
          sourceAddressPrefix: '*'
          destinationAddressPrefix: '*'
          access: 'Allow'
          priority: 1001
          direction: 'Inbound'
        }
      }
    ]
  }
}

// Create custom VNet module if custom configuration is enabled
module customVnet './core/networking/vnet-custom.bicep' = if (usePrivateEndpoint && vnetEnableCustomConfiguration) {
  name: 'vnet-custom'
  params: {
    name: vnetName
    location: location
    tags: tags
    addressPrefix: vnetAddressPrefix
    subnets: [
      {
        name: 'backend-subnet'
        properties: {
          addressPrefix: backendSubnetAddressPrefix
          privateEndpointNetworkPolicies: 'Enabled'
          privateLinkServiceNetworkPolicies: 'Enabled'
          networkSecurityGroup: enableCustomNsgRules ? {
            id: networkSecurityGroup.id
          } : null
        }
      }
      {
        name: 'AzureBastionSubnet'
        properties: {
          addressPrefix: privateEndpointSubnetAddressPrefix
          privateEndpointNetworkPolicies: 'Enabled'
          privateLinkServiceNetworkPolicies: 'Enabled'
        }
      }
      {
        name: 'app-int-subnet'
        properties: {
          addressPrefix: appSubnetAddressPrefix
          privateEndpointNetworkPolicies: 'Enabled'
          privateLinkServiceNetworkPolicies: 'Enabled'
          networkSecurityGroup: enableCustomNsgRules ? {
            id: networkSecurityGroup.id
          } : null
          delegations: deploymentTarget == 'appservice' ? [
            {
              id: appServicePlan.id
              name: appServicePlan.name
              properties: {
                serviceName: 'Microsoft.Web/serverFarms'
              }
            }
          ] : []
        }
      }
      {
        name: 'vm-subnet'
        properties: {
          addressPrefix: vmSubnetAddressPrefix
          networkSecurityGroup: enableCustomNsgRules ? {
            id: networkSecurityGroup.id
          } : null
        }
      }
    ]
  }
  dependsOn: enableCustomNsgRules ? [networkSecurityGroup] : []
}

// Use default VNet module if custom configuration is disabled
module vnet './core/networking/vnet.bicep' = if (usePrivateEndpoint && !vnetEnableCustomConfiguration) {
  name: 'vnet'
  params: {
    name: vnetName
    location: location
    tags: tags
    subnets: [
      {
        name: 'backend-subnet'
        properties: {
          addressPrefix: '10.0.1.0/24'
          privateEndpointNetworkPolicies: 'Enabled'
          privateLinkServiceNetworkPolicies: 'Enabled'
          networkSecurityGroup: enableCustomNsgRules ? {
            id: networkSecurityGroup.id
          } : null
        }
      }
      {
        name: 'AzureBastionSubnet'
        properties: {
          addressPrefix: '10.0.2.0/24'
          privateEndpointNetworkPolicies: 'Enabled'
          privateLinkServiceNetworkPolicies: 'Enabled'
        }
      }
      {
        name: 'app-int-subnet'
        properties: {
          addressPrefix: '10.0.3.0/24'
          privateEndpointNetworkPolicies: 'Enabled'
          privateLinkServiceNetworkPolicies: 'Enabled'
          networkSecurityGroup: enableCustomNsgRules ? {
            id: networkSecurityGroup.id
          } : null
          delegations: deploymentTarget == 'appservice' ? [
            {
              id: appServicePlan.id
              name: appServicePlan.name
              properties: {
                serviceName: 'Microsoft.Web/serverFarms'
              }
            }
          ] : []
        }
      }
      {
        name: 'vm-subnet'
        properties: {
          addressPrefix: '10.0.4.0/24'
          networkSecurityGroup: enableCustomNsgRules ? {
            id: networkSecurityGroup.id
          } : null
        }
      }
    ]
  }
  dependsOn: enableCustomNsgRules ? [networkSecurityGroup] : []
}

output appSubnetId string = usePrivateEndpoint ? (vnetEnableCustomConfiguration ? customVnet.outputs.vnetSubnets[2].id : vnet.outputs.vnetSubnets[2].id) : ''
output backendSubnetId string = usePrivateEndpoint ? (vnetEnableCustomConfiguration ? customVnet.outputs.vnetSubnets[0].id : vnet.outputs.vnetSubnets[0].id) : ''
output vnetName string = usePrivateEndpoint ? (vnetEnableCustomConfiguration ? customVnet.outputs.name : vnet.outputs.name) : ''
output networkSecurityGroupId string = (enableCustomNsgRules && usePrivateEndpoint) ? networkSecurityGroup.id : ''
