# Azure RAG Accelerator Scenarios

This guide demonstrates how to configure and deploy the Azure RAG Accelerator for various real-world scenarios. Each scenario includes configuration examples, deployment considerations, and best practices.

## 📋 Table of Contents

- [Scenario 1: Customer Support Knowledge Base](#scenario-1-customer-support-knowledge-base)
- [Scenario 2: Internal Documentation Search](#scenario-2-internal-documentation-search)
- [Scenario 3: SharePoint Enterprise Integration](#scenario-3-sharepoint-enterprise-integration)
- [Scenario 4: Multi-Source Data Integration](#scenario-4-multi-source-data-integration)
- [Scenario 5: High-Security Government Deployment](#scenario-5-high-security-government-deployment)
- [Scenario 6: Global Enterprise with Regional Compliance](#scenario-6-global-enterprise-with-regional-compliance)
- [Scenario 7: Small Business Quick Start](#scenario-7-small-business-quick-start)
- [Configuration Templates](#configuration-templates)
- [Performance Optimization](#performance-optimization)

---

## Scenario 1: Customer Support Knowledge Base

**Use Case**: External customer-facing AI assistant for technical support

### Requirements
- Public-facing web interface with authentication
- Integration with existing knowledge base (PDFs, HTML, etc.)
- High availability and scalability
- Comprehensive analytics and feedback tracking
- Multi-language support

### Configuration

**Environment Variables** (`.env`):
```bash
# Authentication - Public access with optional login
AZURE_USE_AUTHENTICATION=true
AZURE_REQUIRE_ACCESS_CONTROL=false
AZURE_AUTH_TYPE=azure_ad

# AI Services
AZURE_OPENAI_SERVICE=customer-support-openai
AZURE_OPENAI_GPT_DEPLOYMENT=gpt-4o
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Search Configuration
AZURE_SEARCH_SERVICE=customer-support-search
AZURE_SEARCH_INDEX=knowledge-base
AZURE_SEARCH_SEMANTIC_RANKER=true
AZURE_SEARCH_TOP_K=5

# Data Sources
AZURE_STORAGE_ACCOUNT=customersupportdocs
AZURE_STORAGE_CONTAINER=knowledge-base

# Features
USE_USER_UPLOAD=false
ENABLE_CHAT_HISTORY=true
ENABLE_FEEDBACK=true
ENABLE_SPEECH_INPUT=true
ENABLE_SPEECH_OUTPUT=true

# Observability
APPLICATIONINSIGHTS_CONNECTION_STRING=your-app-insights-connection
ENABLE_PERFORMANCE_TRACKING=true

# Citation and Content
CITATION_STRATEGY=link_to_source
CITATION_BASE_URL=https://docs.yourcompany.com

# Language Support
LANGUAGE_PICKER_ENABLED=true
DEFAULT_LANGUAGE=en
```

**Data Source Configuration** (`datasources.yaml`):
```yaml
data_sources:
  - type: azure_blob
    name: knowledge_base_pdfs
    storage_account: customersupportdocs
    container: pdfs
    supported_extensions: [".pdf", ".docx"]
    max_file_size_mb: 50
    
  - type: azure_blob  
    name: knowledge_base_html
    storage_account: customersupportdocs
    container: html-docs
    supported_extensions: [".html", ".htm"]
```

**Deployment Configuration** (`infra/main.parameters.json`):
```json
{
  "environmentName": "customer-support-prod",
  "location": "East US",
  "principalId": "your-principal-id",
  "useGPT4V": false,
  "useApplicationInsights": true,
  "useAuthentication": true,
  "enforcedAccessControl": false,
  "searchServiceSku": "standard",
  "searchIndexName": "knowledge-base",
  "openAiSku": "S0",
  "formRecognizerSku": "S0",
  "containerAppsEnvironmentName": "customer-support-env",
  "storageAccountName": "customersupportdocs",
  "openAiServiceName": "customer-support-openai",
  "searchServiceName": "customer-support-search"
}
```

### Implementation Steps

1. **Prepare Data Sources**:
   ```bash
   # Upload your knowledge base documents
   az storage blob upload-batch \
     --account-name customersupportdocs \
     --destination knowledge-base \
     --source ./knowledge-base-docs \
     --pattern "*.pdf"
   ```

2. **Deploy Infrastructure**:
   ```bash
   cd infra
   azd provision --environment customer-support-prod
   ```

3. **Index Documents**:
   ```bash
   python scripts/prepdocs.py \
     --storageaccount customersupportdocs \
     --container knowledge-base \
     --searchservice customer-support-search \
     --index knowledge-base \
     --verbose
   ```

4. **Configure Custom Domain** (Optional):
   ```bash
   # Configure custom domain for public access
   az containerapp hostname add \
     --hostname support.yourcompany.com \
     --resource-group rg-customer-support-prod \
     --name customer-support-web
   ```

### Best Practices

- **Content Strategy**: Organize documents by product/service categories
- **Prompt Engineering**: Customize system prompts for customer support tone
- **Feedback Loop**: Enable comprehensive feedback tracking for continuous improvement
- **Monitoring**: Set up alerts for high error rates or poor user satisfaction
- **Content Updates**: Implement automated document refresh workflows

---

## Scenario 2: Internal Documentation Search

**Use Case**: Enterprise internal knowledge management and documentation search

### Requirements
- Secure internal access with role-based permissions
- Integration with existing SharePoint and file shares
- Advanced user upload capabilities
- Comprehensive audit trail
- Integration with Teams/Slack

### Configuration

**Environment Variables** (`.env`):
```bash
# Authentication - Strict internal access
AZURE_USE_AUTHENTICATION=true
AZURE_REQUIRE_ACCESS_CONTROL=true
AZURE_AUTH_TYPE=azure_ad

# AI Services
AZURE_OPENAI_SERVICE=internal-docs-openai
AZURE_OPENAI_GPT_DEPLOYMENT=gpt-4o
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Search Configuration
AZURE_SEARCH_SERVICE=internal-docs-search
AZURE_SEARCH_INDEX=enterprise-docs
AZURE_SEARCH_USE_SEMANTIC_RANKER=true
AZURE_SEARCH_SEMANTIC_RANKER_SERVICE_NAME=internal-docs-semantic

# Data Sources (Multiple)
USE_AZURE_BLOB=true
USE_SHAREPOINT=true
USE_USER_UPLOAD=true

# Security
AZURE_ENFORCE_ACCESS_CONTROL=true
ENABLE_UNAUTHENTICATED_ACCESS=false

# Features
ENABLE_CHAT_HISTORY=true
ENABLE_FEEDBACK=true
ENABLE_USER_UPLOAD=true
ENABLE_QUERY_REWRITING=true

# Observability
APPLICATIONINSIGHTS_CONNECTION_STRING=your-app-insights-connection
ENABLE_PERFORMANCE_TRACKING=true
ENABLE_AUDIT_LOGGING=true

# Content Processing
USE_LOCAL_PDF_PARSER=true
USE_LOCAL_HTML_PARSER=true
DOCUMENT_INTELLIGENCE_SERVICE=internal-docs-docint
```

**SharePoint Configuration** (`sharepoint-config.yaml`):
```yaml
data_sources:
  - type: sharepoint
    name: hr_documents
    tenant_id: your-tenant-id
    client_id: your-app-registration-id
    site_url: https://yourcompany.sharepoint.com/sites/HR
    document_library: "Shared Documents"
    folder_path: "Policies and Procedures"
    supported_extensions: [".pdf", ".docx", ".pptx"]
    max_file_size_mb: 100
    batch_size: 50
    enable_incremental_sync: true
    
  - type: sharepoint
    name: engineering_docs
    tenant_id: your-tenant-id
    client_id: your-app-registration-id
    site_url: https://yourcompany.sharepoint.com/sites/Engineering
    document_library: "Technical Documentation"
    supported_extensions: [".md", ".pdf", ".docx"]
    max_file_size_mb: 200
    batch_size: 25
```

### Implementation Steps

1. **Set Up SharePoint App Registration**:
   ```bash
   # Create app registration with SharePoint permissions
   az ad app create \
     --display-name "Internal Docs RAG App" \
     --required-resource-accesses sharepoint-permissions.json
   ```

2. **Configure Multi-Source Data Processing**:
   ```bash
   # Process SharePoint documents
   python scripts/prepdocs.py \
     --config sharepoint-config.yaml \
     --searchservice internal-docs-search \
     --index enterprise-docs \
     --verbose
   
   # Process blob storage documents
   python scripts/prepdocs.py \
     --storageaccount internaldocs \
     --container documents \
     --searchservice internal-docs-search \
     --index enterprise-docs \
     --verbose
   ```

3. **Set Up Role-Based Access**:
   ```bash
   # Configure Azure AD groups for access control
   az ad group create --display-name "InternalDocs-Readers" --mail-nickname "internaldocs-readers"
   az ad group create --display-name "InternalDocs-Admins" --mail-nickname "internaldocs-admins"
   ```

---

## Scenario 3: SharePoint Enterprise Integration

**Use Case**: Large enterprise with extensive SharePoint Online infrastructure

### Requirements
- Multiple SharePoint sites and document libraries
- Incremental synchronization
- Metadata preservation
- Enterprise-grade security and compliance
- Advanced monitoring and reporting

### Configuration

**Multi-Site SharePoint Configuration** (`sharepoint-enterprise.yaml`):
```yaml
sharepoint:
  tenant_id: your-tenant-id
  client_id: your-enterprise-app-id
  client_secret: ${SHAREPOINT_CLIENT_SECRET}
  
data_sources:
  # Legal Department
  - type: sharepoint
    name: legal_documents
    site_url: https://yourcompany.sharepoint.com/sites/Legal
    document_library: "Legal Documents"
    folder_path: "Contracts and Policies"
    metadata:
      department: "Legal"
      classification: "Confidential"
    supported_extensions: [".pdf", ".docx"]
    max_file_size_mb: 100
    enable_incremental_sync: true
    sync_state_file: "legal_sync_state.json"
    
  # Human Resources
  - type: sharepoint
    name: hr_policies
    site_url: https://yourcompany.sharepoint.com/sites/HR
    document_library: "HR Policies"
    metadata:
      department: "HR"
      classification: "Internal"
    supported_extensions: [".pdf", ".docx", ".pptx"]
    enable_incremental_sync: true
    sync_state_file: "hr_sync_state.json"
    
  # Engineering Documentation
  - type: sharepoint
    name: engineering_specs
    site_url: https://yourcompany.sharepoint.com/sites/Engineering
    document_library: "Technical Specifications"
    folder_path: "System Architecture"
    metadata:
      department: "Engineering"
      classification: "Technical"
    supported_extensions: [".md", ".pdf", ".docx", ".xlsx"]
    batch_size: 25
    enable_incremental_sync: true
    sync_state_file: "engineering_sync_state.json"
    
  # Sales and Marketing
  - type: sharepoint
    name: sales_materials
    site_url: https://yourcompany.sharepoint.com/sites/Sales
    document_library: "Sales Materials"
    metadata:
      department: "Sales"
      classification: "Public"
    supported_extensions: [".pdf", ".pptx", ".docx"]
    enable_incremental_sync: true
    sync_state_file: "sales_sync_state.json"
```

**Advanced Environment Configuration**:
```bash
# Enhanced SharePoint Integration
SHAREPOINT_CLIENT_ID=your-enterprise-app-id
SHAREPOINT_CLIENT_SECRET=your-client-secret
SHAREPOINT_TENANT_ID=your-tenant-id

# Multi-site processing
ENABLE_SHAREPOINT_BATCH_PROCESSING=true
SHAREPOINT_MAX_CONCURRENT_SITES=5
SHAREPOINT_RETRY_ATTEMPTS=3
SHAREPOINT_CIRCUIT_BREAKER_THRESHOLD=10

# Metadata and Security
PRESERVE_SHAREPOINT_METADATA=true
ENABLE_SHAREPOINT_PERMISSIONS=true
SHAREPOINT_SECURITY_TRIMMING=true

# Monitoring
ENABLE_SHAREPOINT_HEALTH_MONITORING=true
SHAREPOINT_PERFORMANCE_METRICS=true
SHAREPOINT_ERROR_REPORTING=true
```

### Automated Sync Workflow

**Azure DevOps Pipeline** (`.azure-pipelines/sharepoint-sync.yml`):
```yaml
trigger:
  schedules:
  - cron: "0 2 * * *"  # Daily at 2 AM
    displayName: Daily SharePoint Sync
    branches:
      include:
      - main

variables:
  - group: SharePoint-Sync-Variables

stages:
- stage: SyncSharePoint
  displayName: 'Sync SharePoint Documents'
  jobs:
  - job: IncrementalSync
    displayName: 'Incremental Sync All Sites'
    pool:
      vmImage: 'ubuntu-latest'
    
    steps:
    - task: AzureCLI@2
      displayName: 'Sync Legal Documents'
      inputs:
        azureSubscription: 'Azure-RAG-Service-Connection'
        scriptType: 'bash'
        scriptLocation: 'inlineScript'
        inlineScript: |
          python scripts/prepdocs.py \
            --config sharepoint-enterprise.yaml \
            --filter-source legal_documents \
            --incremental \
            --searchservice $(SEARCH_SERVICE) \
            --index $(SEARCH_INDEX) \
            --verbose
    
    - task: AzureCLI@2
      displayName: 'Sync HR Policies'
      inputs:
        azureSubscription: 'Azure-RAG-Service-Connection'
        scriptType: 'bash'
        scriptLocation: 'inlineScript'
        inlineScript: |
          python scripts/prepdocs.py \
            --config sharepoint-enterprise.yaml \
            --filter-source hr_policies \
            --incremental \
            --searchservice $(SEARCH_SERVICE) \
            --index $(SEARCH_INDEX) \
            --verbose
    
    - task: AzureCLI@2
      displayName: 'Generate Sync Report'
      inputs:
        azureSubscription: 'Azure-RAG-Service-Connection'
        scriptType: 'bash'
        scriptLocation: 'inlineScript'
        inlineScript: |
          python scripts/generate_sync_report.py \
            --output-path $(Build.ArtifactStagingDirectory)/sync-report.html
    
    - task: PublishBuildArtifacts@1
      displayName: 'Publish Sync Report'
      inputs:
        pathToPublish: '$(Build.ArtifactStagingDirectory)'
        artifactName: 'sync-reports'
```

---

## Scenario 4: Multi-Source Data Integration

**Use Case**: Organization with diverse data sources requiring unified search

### Requirements
- Azure Blob Storage, SharePoint, and local files
- SQL Database integration for metadata
- Custom document processors
- Real-time data synchronization
- Advanced analytics and reporting

### Configuration

**Multi-Source Configuration** (`multi-source-config.yaml`):
```yaml
data_sources:
  # Primary Document Storage
  - type: azure_blob
    name: primary_documents
    storage_account: enterprisedocs
    container: documents
    blob_prefix: "published/"
    supported_extensions: [".pdf", ".docx", ".pptx", ".xlsx"]
    max_file_size_mb: 100
    metadata:
      source_type: "primary"
      
  # SharePoint Integration
  - type: sharepoint
    name: collaboration_docs
    tenant_id: your-tenant-id
    client_id: your-app-id
    site_url: https://yourcompany.sharepoint.com/sites/Collaboration
    document_library: "Shared Documents"
    enable_incremental_sync: true
    supported_extensions: [".pdf", ".docx", ".md"]
    metadata:
      source_type: "collaboration"
      
  # Azure Data Lake Gen2
  - type: adls_gen2
    name: data_lake_docs
    storage_account: enterprisedatalake
    filesystem: documents
    directory_path: "processed/"
    supported_extensions: [".pdf", ".json", ".csv"]
    metadata:
      source_type: "analytics"
      
  # Local Network Shares (via Azure File Share)
  - type: azure_blob
    name: legacy_documents
    storage_account: legacydocs
    container: migrated-files
    blob_prefix: "archive/"
    supported_extensions: [".pdf", ".doc", ".txt"]
    metadata:
      source_type: "legacy"
```

**Advanced Processing Configuration**:
```bash
# Multi-source processing
ENABLE_MULTI_SOURCE_PROCESSING=true
MAX_CONCURRENT_SOURCES=3
PROCESSING_BATCH_SIZE=50

# Custom Document Processors
USE_ADVANCED_PDF_PARSER=true
USE_CUSTOM_DOCX_PROCESSOR=true
ENABLE_OCR_PROCESSING=true
DOCUMENT_INTELLIGENCE_SERVICE=multi-source-docint

# Database Integration
ENABLE_SQL_METADATA=true
SQL_CONNECTION_STRING="Server=tcp:metadata-db.database.windows.net;Database=DocumentMetadata;Authentication=Active Directory Default;"

# Real-time Sync
ENABLE_CHANGE_FEED_MONITORING=true
BLOB_CHANGE_FEED_ACCOUNT=enterprisedocs
SHAREPOINT_WEBHOOK_NOTIFICATIONS=true

# Advanced Analytics
ENABLE_DOCUMENT_ANALYTICS=true
ANALYTICS_STORAGE_ACCOUNT=documentanalytics
ENABLE_USAGE_METRICS=true
ENABLE_CONTENT_QUALITY_SCORING=true
```

### Processing Workflow

**Multi-Source Processing Script** (`scripts/process_multi_source.py`):
```python
#!/usr/bin/env python3
"""
Multi-source document processing with parallel execution and monitoring.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import List, Dict, Any
import yaml

@dataclass
class ProcessingResult:
    source_name: str
    documents_processed: int
    documents_failed: int
    processing_time: float
    errors: List[str]

class MultiSourceProcessor:
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.logger = logging.getLogger(__name__)
    
    async def process_all_sources(self) -> List[ProcessingResult]:
        """Process all data sources in parallel."""
        tasks = []
        for source in self.config['data_sources']:
            task = asyncio.create_task(self.process_source(source))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, ProcessingResult)]
    
    async def process_source(self, source_config: Dict[str, Any]) -> ProcessingResult:
        """Process a single data source."""
        source_name = source_config['name']
        source_type = source_config['type']
        
        self.logger.info(f"Processing source: {source_name} (type: {source_type})")
        
        # Implementation would call appropriate processor based on source type
        # This is a simplified example
        
        return ProcessingResult(
            source_name=source_name,
            documents_processed=100,
            documents_failed=2,
            processing_time=45.6,
            errors=[]
        )

async def main():
    processor = MultiSourceProcessor('multi-source-config.yaml')
    results = await processor.process_all_sources()
    
    for result in results:
        print(f"Source: {result.source_name}")
        print(f"  Processed: {result.documents_processed}")
        print(f"  Failed: {result.documents_failed}")
        print(f"  Time: {result.processing_time}s")
        if result.errors:
            print(f"  Errors: {', '.join(result.errors)}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Scenario 5: High-Security Government Deployment

**Use Case**: Government agency requiring maximum security and compliance

### Requirements
- FedRAMP/FISMA compliance
- Data encryption at rest and in transit
- Network isolation and private endpoints
- Comprehensive audit logging
- No data egress to public internet

### Configuration

**High-Security Environment** (`.env.secure`):
```bash
# Authentication - Maximum security
AZURE_USE_AUTHENTICATION=true
AZURE_REQUIRE_ACCESS_CONTROL=true
AZURE_AUTH_TYPE=azure_ad
AZURE_ENFORCE_ACCESS_CONTROL=true

# Government Cloud
AZURE_CLOUD_TYPE=government
AZURE_TENANT_ID=your-gov-tenant-id

# Network Security
USE_PRIVATE_ENDPOINTS=true
ENABLE_VNET_INTEGRATION=true
AZURE_VNET_NAME=secure-rag-vnet
AZURE_SUBNET_NAME=secure-rag-subnet

# Data Encryption
AZURE_KEY_VAULT_NAME=secure-rag-kv
ENABLE_CUSTOMER_MANAGED_KEYS=true
ENCRYPTION_KEY_NAME=rag-encryption-key

# Compliance and Auditing
ENABLE_COMPREHENSIVE_AUDITING=true
AUDIT_STORAGE_ACCOUNT=secureragaudit
ENABLE_COMPLIANCE_LOGGING=true
LOG_RETENTION_DAYS=2555  # 7 years

# AI Services - Government Cloud
AZURE_OPENAI_SERVICE=secure-gov-openai
AZURE_OPENAI_ENDPOINT=https://secure-gov-openai.openai.azure.us/
AZURE_OPENAI_API_VERSION=2024-02-01

# Search - Government Cloud
AZURE_SEARCH_SERVICE=secure-gov-search
AZURE_SEARCH_ENDPOINT=https://secure-gov-search.search.azure.us

# Storage - Government Cloud
AZURE_STORAGE_ACCOUNT=securegovdocs
AZURE_STORAGE_ENDPOINT=https://securegovdocs.blob.core.usgovcloudapi.net/

# Disable External Services
ENABLE_SPEECH_OUTPUT=false
ENABLE_EXTERNAL_CITATIONS=false
USE_CDN=false
```

**Infrastructure with Private Endpoints** (`infra/secure-main.bicep`):
```bicep
@description('Deploy secure RAG infrastructure with private endpoints')
param environmentName string
param location string = resourceGroup().location
param principalId string

// Virtual Network
resource vnet 'Microsoft.Network/virtualNetworks@2023-05-01' = {
  name: 'vnet-${environmentName}'
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: ['10.0.0.0/16']
    }
    subnets: [
      {
        name: 'subnet-rag'
        properties: {
          addressPrefix: '10.0.1.0/24'
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
      {
        name: 'subnet-private-endpoints'
        properties: {
          addressPrefix: '10.0.2.0/24'
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
    ]
  }
}

// Key Vault with private endpoint
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: 'kv-${environmentName}'
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
    }
    accessPolicies: [
      {
        tenantId: subscription().tenantId
        objectId: principalId
        permissions: {
          keys: ['all']
          secrets: ['all']
          certificates: ['all']
        }
      }
    ]
  }
}

// Private endpoint for Key Vault
resource keyVaultPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-05-01' = {
  name: 'pe-keyvault-${environmentName}'
  location: location
  properties: {
    subnet: {
      id: '${vnet.id}/subnets/subnet-private-endpoints'
    }
    privateLinkServiceConnections: [
      {
        name: 'keyVaultConnection'
        properties: {
          privateLinkServiceId: keyVault.id
          groupIds: ['vault']
        }
      }
    ]
  }
}

// Additional private endpoints for Storage, Search, OpenAI...
```

### Security Checklist

- [ ] **Network Isolation**: All services use private endpoints
- [ ] **Encryption**: Customer-managed keys for all data
- [ ] **Authentication**: Azure AD with MFA required
- [ ] **Authorization**: RBAC with least privilege
- [ ] **Auditing**: Comprehensive logging enabled
- [ ] **Compliance**: Regular security assessments
- [ ] **Data Residency**: All data remains in specified region
- [ ] **Backup**: Encrypted backups with retention policy

---

## Configuration Templates

### Quick Start Template

**Basic Configuration** (`templates/quickstart.env`):
```bash
# === QUICK START TEMPLATE ===
# Copy this file to .env and update the values

# Required: Azure Services
AZURE_OPENAI_SERVICE=your-openai-service-name
AZURE_OPENAI_GPT_DEPLOYMENT=gpt-4o
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
AZURE_SEARCH_SERVICE=your-search-service-name
AZURE_SEARCH_INDEX=your-index-name
AZURE_STORAGE_ACCOUNT=your-storage-account-name
AZURE_STORAGE_CONTAINER=your-container-name

# Authentication (set to false for development only)
AZURE_USE_AUTHENTICATION=true

# Basic Features
ENABLE_CHAT_HISTORY=true
ENABLE_FEEDBACK=true
USE_USER_UPLOAD=false

# Optional: Observability
APPLICATIONINSIGHTS_CONNECTION_STRING=your-app-insights-connection
```

### Production Template

**Production Configuration** (`templates/production.env`):
```bash
# === PRODUCTION TEMPLATE ===
# Comprehensive production configuration

# Azure Services
AZURE_OPENAI_SERVICE=prod-openai-service
AZURE_OPENAI_GPT_DEPLOYMENT=gpt-4o
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
AZURE_SEARCH_SERVICE=prod-search-service
AZURE_SEARCH_INDEX=production-index
AZURE_STORAGE_ACCOUNT=proddocuments
AZURE_STORAGE_CONTAINER=documents

# Authentication and Security
AZURE_USE_AUTHENTICATION=true
AZURE_REQUIRE_ACCESS_CONTROL=true
AZURE_ENFORCE_ACCESS_CONTROL=true

# Performance and Scaling
AZURE_SEARCH_SEMANTIC_RANKER=true
AZURE_SEARCH_TOP_K=5
AZURE_OPENAI_TEMPERATURE=0.3
AZURE_OPENAI_MAX_TOKENS=1000

# Features
ENABLE_CHAT_HISTORY=true
ENABLE_FEEDBACK=true
USE_USER_UPLOAD=true
ENABLE_SPEECH_INPUT=true
ENABLE_SPEECH_OUTPUT=true
ENABLE_QUERY_REWRITING=true

# Observability
APPLICATIONINSIGHTS_CONNECTION_STRING=prod-app-insights-connection
ENABLE_PERFORMANCE_TRACKING=true
ENABLE_AUDIT_LOGGING=true

# Content Management
CITATION_STRATEGY=detailed_with_metadata
ENABLE_CONTENT_SAFETY=true
CONTENT_SAFETY_THRESHOLD=4

# Advanced Features
USE_SEMANTIC_RANKER=true
ENABLE_VECTOR_SEARCH=true
USE_HYBRID_SEARCH=true
```

---

## Performance Optimization

### Small Deployment (< 1000 documents)
```bash
# Optimized for cost and simplicity
AZURE_SEARCH_SERVICE_SKU=basic
AZURE_OPENAI_SKU=S0
AZURE_SEARCH_TOP_K=3
ENABLE_SEMANTIC_RANKER=false
USE_VECTOR_SEARCH=false
```

### Medium Deployment (1000-10000 documents)
```bash
# Balanced performance and cost
AZURE_SEARCH_SERVICE_SKU=standard
AZURE_OPENAI_SKU=S0
AZURE_SEARCH_TOP_K=5
ENABLE_SEMANTIC_RANKER=true
USE_VECTOR_SEARCH=true
USE_HYBRID_SEARCH=true
```

### Large Deployment (> 10000 documents)
```bash
# Optimized for performance and scale
AZURE_SEARCH_SERVICE_SKU=standard2
AZURE_OPENAI_SKU=S0
AZURE_SEARCH_TOP_K=10
ENABLE_SEMANTIC_RANKER=true
USE_VECTOR_SEARCH=true
USE_HYBRID_SEARCH=true
ENABLE_QUERY_REWRITING=true
MAX_CONCURRENT_REQUESTS=20
```

---

## Next Steps

1. **Choose Your Scenario**: Select the scenario that best matches your requirements
2. **Customize Configuration**: Adapt the provided templates to your specific needs
3. **Deploy Infrastructure**: Use the provided deployment configurations
4. **Test and Validate**: Verify the deployment meets your requirements
5. **Monitor and Optimize**: Use the observability features to continuously improve

For additional support and advanced scenarios, see the [Troubleshooting Guide](troubleshooting.md) and [API Documentation](api/README.md). 