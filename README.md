<!--
---
name: Azure RAG Accelerator - Enterprise-Ready RAG Chat App
description: Production-ready ChatGPT-like app with Azure OpenAI, Azure AI Search, configurable data sources, feedback system, and enterprise features.
languages:
- python
- typescript
- bicep
- azdeveloper
products:
- azure-openai
- azure-cognitive-search
- azure-app-service
- azure-cosmos-db
- azure-container-apps
- azure
page_type: sample
urlFragment: azure-rag-accelerator
---
-->

# Azure RAG Accelerator - Enterprise-Ready RAG Chat Application

[![Open in GitHub Codespaces](https://img.shields.io/static/v1?style=for-the-badge&label=GitHub+Codespaces&message=Open&color=brightgreen&logo=github)](https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=599293758&machine=standardLinux32gb&devcontainer_path=.devcontainer%2Fdevcontainer.json&location=WestUs2)
[![Open in Dev Containers](https://img.shields.io/static/v1?style=for-the-badge&label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/azure-samples/azure-search-openai-demo)

A comprehensive, production-ready Retrieval Augmented Generation (RAG) solution built on Azure. This accelerator provides a ChatGPT-like experience over your own enterprise data, featuring configurable data ingestion, advanced citation linking, user feedback systems, admin dashboards, and comprehensive observability.

> **🚀 Ready for Production**: This accelerator has been enhanced with enterprise-grade features including configurable data sources, comprehensive security, monitoring, and admin capabilities.

## 🌟 Key Features

### 🔧 **Configurable Data Ingestion**
- **Multiple Data Sources**: Local files, Azure Blob Storage, ADLS Gen2, SharePoint Online
- **Flexible Configuration**: JSON/YAML configuration files with environment variable fallbacks
- **Plugin Architecture**: Extensible system for adding new data source connectors
- **Enterprise Integration**: Native SharePoint connector with Microsoft Graph API

### 💬 **Advanced Chat Experience**
- **Multi-turn Conversations**: Contextual chat with memory
- **Rich Citations**: Configurable citation linking to external systems
- **Real-time Feedback**: User rating and comment system
- **Accessibility**: Optional speech input/output support

### 📊 **Admin Dashboard & Analytics**
- **Feedback Analytics**: Comprehensive feedback analysis and trends
- **Chat History Management**: Session tracking and conversation analytics
- **Data Export**: CSV/JSON export capabilities
- **Real-time Metrics**: Interactive charts and visualizations

### 🔍 **Enterprise Security & Compliance**
- **Authentication Integration**: Microsoft Entra ID support
- **Access Control**: User-based data access controls
- **Audit Logging**: Comprehensive activity tracking
- **Configurable Citations**: Secure document linking with authentication

### 📈 **Observability & Monitoring**
- **Application Insights Integration**: Performance and usage analytics
- **Custom Telemetry**: RAG-specific metrics and tracking
- **Performance Monitoring**: Response times and system health
- **Alert Management**: Automated alerting for issues

### ⚙️ **Flexible Deployment**
- **Multiple Hosting Options**: Azure Container Apps (default) or App Service
- **Environment-Specific Configs**: Development, staging, production templates
- **Cost Optimization**: Multiple deployment tiers for different budgets
- **Infrastructure as Code**: Comprehensive Bicep templates

## 🏗️ Architecture

![RAG Architecture](docs/images/appcomponents.png)

The Azure RAG Accelerator follows a modern, scalable architecture with:

- **Frontend**: React TypeScript application with Fluent UI components
- **Backend**: Python (Quart) API with async processing
- **Data Layer**: Azure AI Search for indexing, Azure Cosmos DB for chat history and feedback
- **AI Services**: Azure OpenAI for language models, Azure AI Document Intelligence for processing
- **Monitoring**: Application Insights for observability and analytics

## 📋 Prerequisites

### Azure Account Requirements

**Essential Requirements:**
- **Azure account** with active subscription ([get free Azure credits](https://azure.microsoft.com/free/cognitive-search/))
- **Microsoft.Authorization/roleAssignments/write** permissions ([Role Based Access Control Administrator](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles#role-based-access-control-administrator-preview), [User Access Administrator](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles#user-access-administrator), or [Owner](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles#owner))
- **Microsoft.Resources/deployments/write** permissions on subscription level

### Development Environment

**Required Tools:**
- [Azure Developer CLI](https://aka.ms/azure-dev/install)
- [Python 3.9, 3.10, or 3.11](https://www.python.org/downloads/)
- [Node.js 20+](https://nodejs.org/download/)
- [Git](https://git-scm.com/downloads)
- [PowerShell 7+ (pwsh)](https://github.com/powershell/powershell) - Windows only

## 💰 Cost Estimation

Pricing varies by region and usage. Use the [Azure pricing calculator](https://azure.com/e/e3490de2372a4f9b909b0d032560e41b) for accurate estimates.

### **Deployment Tiers**

| Tier | Monthly Cost (Est.) | Use Case | Key Features |
|------|---------------------|----------|--------------|
| **Development** | $265-300 | Testing, prototyping | Basic SKUs, minimal replicas |
| **Staging** | $350-450 | Pre-production testing | Production-like configuration |
| **Production** | $600-800 | Enterprise deployment | High availability, scaling |

**Cost Optimization**: See our [low-cost deployment guide](docs/deploy_lowcost.md) for strategies to minimize costs.

⚠️ **Important**: Resources incur costs immediately upon deployment. Use `azd down` to clean up when not in use.

## 🚀 Quick Start

### Option 1: GitHub Codespaces (Recommended)
[![Open in GitHub Codespaces](https://img.shields.io/static/v1?style=for-the-badge&label=GitHub+Codespaces&message=Open&color=brightgreen&logo=github)](https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=599293758&machine=standardLinux32gb&devcontainer_path=.devcontainer%2Fdevcontainer.json&location=WestUs2)

### Option 2: VS Code Dev Containers
[![Open in Dev Containers](https://img.shields.io/static/v1?style=for-the-badge&label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/azure-samples/azure-search-openai-demo)

### Option 3: Local Development

1. **Initialize the project:**
   ```bash
   azd init -t azure-search-openai-demo
   cd azure-search-openai-demo
   ```

2. **Deploy to Azure:**
   ```bash
   azd auth login
   azd env new
   azd up
   ```

3. **Access your deployment:**
   The deployment URL will be displayed after successful completion.

## 🔧 Configuration & Customization

### Data Source Configuration

The accelerator supports multiple data sources through a flexible configuration system:

```yaml
# accelerator_config.yaml
data_sources:
  - type: "sharepoint"
    config:
      tenant_id: "your-tenant-id"
      client_id: "your-client-id"
      site_url: "https://yourtenant.sharepoint.com/sites/yoursite"
      document_library: "Shared Documents"
      
  - type: "azure_blob"
    config:
      account_name: "yourstorageaccount"
      container_name: "documents"
      
  - type: "local"
    config:
      path: "./data"
```

### Environment-Specific Deployments

Deploy optimized configurations for different environments:

```bash
# Development (cost-optimized)
az deployment group create \
  --resource-group rg-ragchat-dev \
  --template-file infra/main.bicep \
  --parameters infra/dev.parameters.json

# Production (enterprise-ready)
az deployment group create \
  --resource-group rg-ragchat-prod \
  --template-file infra/main.bicep \
  --parameters infra/prod.parameters.json
```

## 📖 Documentation

Comprehensive documentation is available in the [docs](docs/README.md) folder:

### **📚 Getting Started**
- [Quick Start Guide](docs/quickstart.md) - Get up and running in minutes
- [Local Development](docs/localdev.md) - Development environment setup
- [Deployment Guide](docs/deployment.md) - Comprehensive deployment instructions

### **🔧 Configuration**
- [Data Source Configuration](docs/data_ingestion.md) - Configure multiple data sources
- [SharePoint Integration](docs/sharepoint_configuration.md) - Enterprise SharePoint setup
- [Citation Configuration](docs/configurable-citation-linking.md) - Custom citation linking
- [Security Configuration](docs/login_and_acl.md) - Authentication and access control

### **🎯 Features**
- [Feedback System](docs/feedback-schema.md) - User feedback and analytics
- [Admin Dashboard](docs/admin-dashboard.md) - Management interface
- [Monitoring & Observability](docs/monitoring.md) - Application insights and tracking
- [Performance Optimization](docs/performance.md) - Scaling and optimization

### **🚀 Deployment**
- [Azure Container Apps](docs/azure_container_apps.md) - Default deployment target
- [Azure App Service](docs/azure_app_service.md) - Alternative hosting option
- [Environment-Specific Deployments](docs/environment-deployments.md) - Multi-environment setup
- [Cost Optimization](docs/deploy_lowcost.md) - Budget-friendly deployments

### **🔍 Advanced Topics**
- [Customization Guide](docs/customization.md) - Extend and modify the application
- [API Documentation](docs/api/README.md) - Complete API reference
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions
- [Production Readiness](docs/productionizing.md) - Production deployment checklist

## 🛠️ Development

### Running Locally

After successful `azd up` deployment:

```bash
# Authenticate
azd auth login

# Start development server
./app/start.sh    # Linux/Mac
./app/start.ps1   # Windows
```

Navigate to `http://localhost:50505` to access the application.

### Features Overview

- **Chat Interface**: Multi-turn conversations with context
- **Admin Dashboard**: Access via `/admin` route (requires authentication)
- **Feedback System**: Rate responses and provide comments
- **Citation Linking**: Configurable links to source documents
- **Real-time Analytics**: Monitor usage and performance

## 🔄 Updates & Maintenance

### Updating the Application

**Code-only changes:**
```bash
azd deploy
```

**Infrastructure changes:**
```bash
azd up
```

### Monitoring & Health

- **Application Insights**: Monitor performance and usage
- **Health Endpoints**: `/health` for application status
- **Admin Dashboard**: Real-time metrics and analytics

## 🧹 Cleanup

To remove all Azure resources:

```bash
azd down
```

Confirm deletion when prompted to avoid ongoing costs.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:

- Code standards and style
- Testing requirements  
- Pull request process
- Security considerations

## 📞 Support

- **GitHub Issues**: [Report bugs or request features](/issues)
- **Microsoft Employees**: [Internal Teams channel](https://aka.ms/azai-python-help)
- **Documentation**: [Comprehensive guides](docs/README.md)

> **Note**: This repository is maintained by the community, not Microsoft Support. Please use GitHub Issues for assistance.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Important Security Notice

This template showcases Azure AI services and should not be used in production without implementing additional security measures. Review our [production readiness guide](docs/productionizing.md) and the [Azure OpenAI Landing Zone reference architecture](https://techcommunity.microsoft.com/blog/azurearchitectureblog/azure-openai-landing-zone-reference-architecture/3882102) for best practices.

---

### 🔗 Additional Resources

- [📖 Azure AI Search Documentation](https://learn.microsoft.com/azure/search/search-what-is-azure-search)
- [📖 Azure OpenAI Service Documentation](https://learn.microsoft.com/azure/cognitive-services/openai/overview)  
- [📺 Video: RAG Application Development](https://youtu.be/j8i-OM5kwiY)
- [📺 AI Chat App Tutorial Series](https://www.youtube.com/playlist?list=PL5lwDBUC0ag6_dGZst5m3G72ewfwXLcXV)
- [🏛️ Azure OpenAI Landing Zone Architecture](https://techcommunity.microsoft.com/blog/azurearchitectureblog/azure-openai-landing-zone-reference-architecture/3882102)

> **💡 Tip**: Star this repository to stay updated with the latest features and improvements!

---

*Built with ❤️ by the Azure AI team and community contributors*
