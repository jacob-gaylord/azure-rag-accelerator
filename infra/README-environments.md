# Environment-Specific Parameter Files

This directory contains three environment-specific parameter files that provide optimized configurations for different deployment scenarios of the Azure RAG Accelerator.

## Overview

| Environment | File | Purpose | Cost | Security | Performance |
|-------------|------|---------|------|----------|-------------|
| Development | `dev.parameters.json` | Local development & testing | Minimal | Basic | Basic |
| Staging | `staging.parameters.json` | Pre-production validation | Moderate | Production-like | Standard |
| Production | `prod.parameters.json` | Live production deployment | High | Maximum | Premium |

## File Usage

Deploy using the Azure CLI with environment-specific parameter files:

```bash
# Development deployment
az deployment group create \
  --resource-group myResourceGroup \
  --template-file main.bicep \
  --parameters @dev.parameters.json

# Staging deployment  
az deployment group create \
  --resource-group myResourceGroup \
  --template-file main.bicep \
  --parameters @staging.parameters.json

# Production deployment
az deployment group create \
  --resource-group myResourceGroup \
  --template-file main.bicep \
  --parameters @prod.parameters.json
```

## Environment Configurations

### Development Environment (`dev.parameters.json`)

**Primary Goal**: Minimize costs while enabling core functionality for development and testing.

#### Service Deployment
- ✅ **Deployed Services**: Search Service, Storage Account, OpenAI Service
- ❌ **Excluded Services**: Cosmos DB, Document Intelligence, Computer Vision, Speech Service, Content Understanding, Monitoring, User Storage, Redis Cache

#### Key Characteristics
- **App Service**: Basic tier (B1) with single instance, no autoscaling
- **Storage**: Standard LRS (Locally Redundant Storage)
- **Search**: Basic tier with free semantic ranker
- **OpenAI**: Standard deployment with minimal capacity (10 TPM each)
- **Authentication**: Disabled for easier development access
- **Networking**: Public access enabled, no private endpoints
- **Monitoring**: Application Insights disabled
- **Chat History**: Browser-based (no Cosmos DB required)

#### Estimated Monthly Cost
- **App Service Plan B1**: ~$13.14/month
- **Azure Cognitive Search Basic**: ~$250/month
- **Storage Account**: ~$0.05/month
- **OpenAI Standard**: Variable based on usage
- **Total**: ~$265-300/month (excluding OpenAI usage)

---

### Staging Environment (`staging.parameters.json`)

**Primary Goal**: Mirror production architecture at smaller scale for comprehensive testing.

#### Service Deployment
- ✅ **Deployed Services**: Search, Storage, OpenAI, Cosmos DB, Document Intelligence, Computer Vision, Monitoring, User Storage
- ❌ **Excluded Services**: Speech Service, Content Understanding, Redis Cache

#### Key Characteristics  
- **App Service**: Standard tier (S1) with autoscaling (1-5 instances)
- **Storage**: Standard GRS (Geo-Redundant Storage)
- **Search**: Standard tier with standard semantic ranker
- **OpenAI**: Standard deployment with moderate capacity (30 TPM)
- **Cosmos DB**: Provisioned throughput (400 RU/s), geo-redundant backup
- **Authentication**: Enabled with Azure AD integration
- **Networking**: Private endpoints for most services, custom VNet
- **Monitoring**: Full Application Insights and Log Analytics
- **Chat History**: Cosmos DB-based with persistence

#### Estimated Monthly Cost
- **App Service Plan S1**: ~$73/month
- **Azure Cognitive Search Standard**: ~$250/month
- **Storage Account GRS**: ~$0.10/month
- **Cosmos DB**: ~$24/month (400 RU/s)
- **Application Insights**: ~$2-5/month
- **Document Intelligence**: Variable based on usage
- **Computer Vision**: Variable based on usage
- **OpenAI Standard**: Variable based on usage
- **Total**: ~$350-450/month (excluding AI service usage)

---

### Production Environment (`prod.parameters.json`)

**Primary Goal**: Maximum performance, reliability, and security for production workloads.

#### Service Deployment
- ✅ **All Services Deployed**: Complete feature set including all AI services, monitoring, and caching

#### Key Characteristics
- **App Service**: Premium V3 tier (P1V3) with aggressive autoscaling (2-10 instances)
- **Storage**: Standard RAGRS (Read-Access Geo-Redundant Storage)
- **Search**: Standard tier with advanced query rewriting
- **OpenAI**: Provisioned Throughput deployment for guaranteed performance (100 TPM each)
- **Cosmos DB**: Multi-region, autoscaling, analytical storage, continuous backup
- **Authentication**: Complete Azure AD integration with access control
- **Networking**: All private endpoints enabled, DDoS protection, custom NSG rules
- **Monitoring**: Comprehensive Application Insights with dashboard
- **Features**: All advanced features enabled (GPT-4V, evaluation, speech, agentic retrieval)

#### Advanced Features
- **Multi-Model Support**: Chat, embedding, GPT-4V, evaluation, and search agent models
- **Geographic Distribution**: Multi-region Cosmos DB with write locations
- **Backup Strategy**: Continuous backup with 30-day retention
- **Network Security**: Custom VNet, all private endpoints, DDoS protection
- **Deployment Slots**: Multiple slots for blue-green deployments
- **High Availability**: Zone redundancy, multiple worker processes

#### Estimated Monthly Cost
- **App Service Plan P1V3**: ~$292/month (base) + autoscaling
- **Azure Cognitive Search Standard**: ~$250/month
- **Storage Account RAGRS**: ~$0.15/month
- **Cosmos DB Multi-region**: ~$500-1000/month (depending on usage)
- **Application Insights**: ~$10-50/month
- **OpenAI Provisioned Throughput**: ~$4,380/month (100 TPM × 2 models)
- **All AI Services**: Variable, potentially $100-500/month
- **DDoS Protection**: ~$2,944/month
- **Total**: ~$8,000-10,000/month (with full provisioned capacity)

## Configuration Differences Summary

| Parameter Category | Development | Staging | Production |
|-------------------|-------------|---------|------------|
| **Conditional Deployment** | Minimal (3 services) | Most services (8/11) | All services (11/11) |
| **App Service Tier** | Basic B1 | Standard S1 | Premium P1V3 |
| **Autoscaling** | Disabled | Basic (1-5) | Advanced (2-10) |
| **Storage Redundancy** | LRS | GRS | RAGRS |
| **Search Tier** | Basic | Standard | Standard |
| **OpenAI SKU** | Standard | Standard | Provisioned |
| **Cosmos DB** | Not deployed | Basic provisioned | Multi-region autoscale |
| **Private Endpoints** | None | Most services | All services |
| **Authentication** | Disabled | Enabled | Full enterprise |
| **Monitoring** | Minimal | Standard | Comprehensive |
| **Backup Strategy** | None | Periodic | Continuous |
| **Multi-region** | No | No | Yes |

## Environment Variables

Each parameter file uses environment variable substitution. Ensure your deployment environment has the appropriate variables set for:

- Resource naming (`AZURE_ENV_NAME`, service names)
- Location settings (`AZURE_LOCATION`, service locations)  
- Authentication settings (tenant, client IDs, secrets)
- Custom configurations (API keys, custom URLs)

## Best Practices

1. **Development**: Use for feature development, unit testing, and initial integration testing
2. **Staging**: Use for comprehensive testing, performance validation, and security testing
3. **Production**: Use only for live customer-facing deployments

4. **Cost Management**: 
   - Monitor usage in staging to predict production costs
   - Consider scaling down non-production environments outside business hours
   - Use development environment for most testing scenarios

5. **Security**: 
   - Never use production credentials in development/staging
   - Ensure proper network isolation in production
   - Regular security reviews of configuration differences

6. **Testing Strategy**:
   - Validate each parameter file with a test deployment
   - Verify conditional deployment flags work as expected
   - Test scaling policies under load in staging

## Migration Path

When promoting code through environments:

1. **Dev → Staging**: Validate all features work with authentication and private networking
2. **Staging → Production**: Verify performance at scale and complete security configuration
3. **Rollback Strategy**: Keep previous parameter file versions for quick rollback

---

*Last Updated: December 2024*
*Azure RAG Accelerator Infrastructure Configuration* 