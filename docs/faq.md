# Frequently Asked Questions (FAQ)

This document answers common questions about the Azure RAG Accelerator. If you don't find your question here, check the [troubleshooting guide](troubleshooting.md) or create an issue on GitHub.

## 📋 Table of Contents

- [General Questions](#general-questions)
- [Getting Started](#getting-started)
- [Deployment & Configuration](#deployment--configuration)
- [Data Sources & Documents](#data-sources--documents)
- [Performance & Scaling](#performance--scaling)
- [Security & Privacy](#security--privacy)
- [Customization](#customization)
- [Cost Management](#cost-management)
- [Troubleshooting](#troubleshooting)
- [Development & Contributing](#development--contributing)

## 🌟 General Questions

### What is the Azure RAG Accelerator?

The Azure RAG Accelerator is a production-ready implementation of Retrieval-Augmented Generation (RAG) using Azure services. It allows organizations to build intelligent chat applications that can answer questions based on their own documents and data sources, combining the power of Azure OpenAI with enterprise-grade security and scalability.

### How does RAG work?

RAG works in two main steps:
1. **Retrieval**: When you ask a question, the system searches through your indexed documents to find relevant information
2. **Generation**: The relevant information is then sent to a language model (like GPT-4) along with your question to generate an informed, accurate response with citations

This approach reduces hallucinations and ensures responses are grounded in your actual data.

### What makes this different from other RAG implementations?

Key differentiators include:
- **Enterprise-ready**: Built for production with Azure's security, compliance, and scalability
- **Multi-source**: Supports SharePoint, blob storage, local files, and more
- **Configurable**: Extensive customization options for search, AI models, and UI
- **Observability**: Built-in monitoring, analytics, and feedback collection
- **One-click deployment**: Automated infrastructure setup with Azure Developer CLI

### What Azure services does it use?

Core services include:
- **Azure OpenAI**: For language models and embeddings
- **Azure AI Search**: For document indexing and retrieval
- **Azure Container Apps**: For hosting the application
- **Azure Blob Storage**: For document storage
- **Azure Cosmos DB**: For feedback and session data
- **Azure Application Insights**: For monitoring and analytics

## 🚀 Getting Started

### What are the prerequisites?

You need:
- **Azure subscription** with appropriate permissions
- **Azure Developer CLI** installed
- **Access to Azure OpenAI** (requires approval)
- **Basic familiarity** with command line tools

### How long does deployment take?

Initial deployment typically takes 15-30 minutes, including:
- Azure resource provisioning (10-15 minutes)
- Application deployment (5-10 minutes)
- Initial configuration and testing (5 minutes)

### Can I try it without deploying to Azure?

Yes! You can run the accelerator locally for development and testing:
1. Clone the repository
2. Set up local environment variables
3. Run `./app/start.sh`
4. Access the application at `http://localhost:50505`

### What's the quickest way to get started?

1. **Install prerequisites**: Azure Developer CLI and ensure Azure OpenAI access
2. **Clone the repository**: `git clone https://github.com/Azure-Samples/azure-search-openai-demo`
3. **Deploy**: Run `azd up` and follow the prompts
4. **Upload documents**: Use the web interface to add your documents
5. **Start chatting**: Ask questions about your documents

## ⚙️ Deployment & Configuration

### Can I deploy to different Azure regions?

Yes, but consider these factors:
- **Azure OpenAI availability**: Not all regions support Azure OpenAI
- **Data residency**: Choose regions that meet your compliance requirements
- **Latency**: Deploy closer to your users for better performance

Supported OpenAI regions include: East US, South Central US, West Europe, France Central, Japan East.

### How do I configure authentication?

The accelerator supports:
- **Azure Active Directory**: For enterprise authentication (recommended)
- **No authentication**: For development/demo scenarios
- **Custom authentication**: Can be implemented with code modifications

Set `AZURE_USE_AUTHENTICATION=true` to enable Azure AD authentication.

### Can I use my own AI models?

Yes, you can configure:
- **Different Azure OpenAI models**: GPT-4, GPT-3.5-turbo, etc.
- **Custom deployments**: Your own fine-tuned models
- **Multiple models**: Different models for different purposes

Configure through environment variables like `AZURE_OPENAI_GPT_DEPLOYMENT`.

### How do I set up monitoring?

Monitoring is enabled by default with Application Insights:
- **Performance monitoring**: Response times, throughput, errors
- **Custom telemetry**: User interactions, search queries, feedback
- **Alerts**: Configure for critical issues
- **Dashboards**: Built-in admin dashboard for analytics

## 📄 Data Sources & Documents

### What document formats are supported?

Supported formats include:
- **Text files**: .txt, .md
- **Microsoft Office**: .docx, .pptx, .xlsx
- **PDFs**: Including scanned documents (with OCR)
- **Web content**: HTML files
- **Structured data**: JSON, CSV (with preprocessing)

### How do I add SharePoint as a data source?

1. **Create an app registration** in Azure AD
2. **Grant permissions**: Sites.Read.All, Files.Read.All
3. **Configure environment variables**:
   ```bash
   SHAREPOINT_TENANT_ID=your-tenant-id
   SHAREPOINT_CLIENT_ID=your-app-id
   SHAREPOINT_CLIENT_SECRET=your-secret
   ```
4. **Run ingestion**: Use the SharePoint connector to sync documents

### What's the maximum document size?

Current limits:
- **Individual files**: 100MB per document
- **Total storage**: No hard limit (depends on Azure storage limits)
- **Processing timeout**: 10 minutes per document
- **Recommended size**: Under 50MB for optimal performance

### How often are documents updated?

Document updates depend on your configuration:
- **Manual uploads**: Updated when you upload new versions
- **SharePoint sync**: Configurable (daily, hourly, or real-time)
- **Blob storage**: Can be configured with change detection
- **API ingestion**: Real-time as documents are added

### Can I control document access?

Yes, through several mechanisms:
- **Azure AD integration**: Document-level permissions based on user identity
- **Access Control Lists (ACLs)**: Fine-grained permission control
- **Source system permissions**: Inherit permissions from SharePoint, etc.
- **Custom filters**: Implement business logic for document visibility

## ⚡ Performance & Scaling

### How many users can it support?

Performance depends on your configuration:
- **Container Apps scaling**: Auto-scales based on demand
- **Azure OpenAI quotas**: Typically 240K tokens/minute for standard deployments
- **Search service tier**: Basic supports ~3 queries/second, Standard much higher
- **Typical capacity**: 50-500 concurrent users depending on usage patterns

### How can I improve response times?

Optimization strategies:
1. **Reduce search scope**: Limit `top` parameter (default: 5)
2. **Use faster models**: GPT-3.5-turbo instead of GPT-4 for simple queries
3. **Optimize chunks**: Smaller chunks reduce processing time
4. **Enable caching**: Implement Redis for frequent queries
5. **Scale resources**: Increase container CPU/memory or search service tier

### What are the latency expectations?

Typical response times:
- **Simple queries**: 2-5 seconds
- **Complex queries**: 5-15 seconds
- **First query**: May be slower due to cold start
- **Factors**: Document count, chunk size, model choice, search complexity

### How does it scale with document volume?

Scaling characteristics:
- **Search performance**: Remains fast up to millions of documents
- **Index size**: Limited by search service tier
- **Processing time**: Increases linearly with document count
- **Best practices**: Use incremental indexing, batch processing

## 🔒 Security & Privacy

### Is my data secure?

Security features include:
- **Encryption at rest**: All Azure services encrypt stored data
- **Encryption in transit**: HTTPS/TLS for all communications
- **Network isolation**: VNet integration and private endpoints supported
- **Access controls**: Azure AD integration and RBAC
- **Audit logs**: Comprehensive logging of all activities

### Where is data stored?

Data locations:
- **Documents**: Azure Blob Storage in your chosen region
- **Search index**: Azure AI Search in your region
- **Chat history**: Azure Cosmos DB (if enabled)
- **Logs**: Application Insights in your region
- **AI processing**: Azure OpenAI in configured region

### Can I use private endpoints?

Yes, the accelerator supports Azure Private Link:
- **Search service**: Private endpoint for search traffic
- **Storage account**: Private endpoint for document access
- **OpenAI service**: Private endpoint for AI calls
- **Cosmos DB**: Private endpoint for session data

### How do I ensure compliance?

Compliance features:
- **Data residency**: Deploy in regions that meet requirements
- **Audit trails**: Comprehensive logging of all activities
- **Data retention**: Configurable retention policies
- **Access controls**: Fine-grained permissions and authentication
- **Certifications**: Inherits Azure's compliance certifications (SOC, ISO, etc.)

### Can I delete user data?

Yes, data deletion options:
- **Individual documents**: Remove from search index and storage
- **User conversations**: Delete from Cosmos DB
- **Feedback data**: Remove user-specific entries
- **GDPR compliance**: Automated data deletion workflows available

## 🎨 Customization

### Can I customize the user interface?

Yes, the frontend is fully customizable:
- **React components**: Modify existing components or create new ones
- **Styling**: Custom CSS, themes, and branding
- **Layout**: Reorganize the interface to match your needs
- **Features**: Add or remove functionality as needed

### How do I modify the chat behavior?

Customization options:
- **System prompts**: Change how the AI responds
- **Search parameters**: Adjust retrieval behavior
- **Response format**: Customize citation styles and formatting
- **Conversation flow**: Modify multi-turn conversation handling

### Can I add custom data sources?

Yes, you can extend the system:
- **Custom connectors**: Implement new data source integrations
- **API integration**: Connect to external systems
- **Real-time data**: Stream live data into the system
- **Processing pipelines**: Custom document processing logic

### How do I integrate with existing systems?

Integration approaches:
- **REST APIs**: Full API access for programmatic integration
- **Single sign-on**: Azure AD integration with existing identity systems
- **Webhooks**: Real-time notifications and updates
- **Embedding**: Iframe or component embedding in existing applications

## 💰 Cost Management

### What does it cost to run?

Typical monthly costs (varies by usage):
- **Azure OpenAI**: $50-500 (depends on token usage)
- **Azure AI Search**: $25-250 (depends on tier and queries)
- **Container Apps**: $10-100 (depends on scale and usage)
- **Storage**: $5-50 (depends on document volume)
- **Other services**: $10-50 (Cosmos DB, App Insights, etc.)

### How can I optimize costs?

Cost optimization strategies:
1. **Right-size resources**: Use appropriate service tiers
2. **Optimize AI usage**: Shorter prompts, efficient models
3. **Scale down when idle**: Use auto-scaling features
4. **Monitor usage**: Set up cost alerts and budgets
5. **Use development tiers**: Lower-cost options for testing

### What affects Azure OpenAI costs?

OpenAI cost factors:
- **Token usage**: Input and output tokens are billed separately
- **Model choice**: GPT-4 costs more than GPT-3.5-turbo
- **Query frequency**: More queries = higher costs
- **Context length**: Longer contexts use more tokens
- **Optimization**: Efficient prompts and caching reduce costs

### Can I set spending limits?

Cost control options:
- **Azure budgets**: Set spending alerts and limits
- **Service quotas**: Limit token usage per minute/month
- **Auto-scaling**: Scale down during low usage
- **Development environments**: Use cheaper tiers for testing

## 🔧 Troubleshooting

### Why am I getting authentication errors?

Common authentication issues:
1. **App registration**: Ensure proper Azure AD app setup
2. **Redirect URIs**: Must match exactly (including trailing slashes)
3. **Permissions**: Grant required API permissions and admin consent
4. **Token expiration**: Check if tokens need refresh
5. **Environment variables**: Verify all auth variables are set correctly

### Documents aren't appearing in search results

Troubleshooting steps:
1. **Check processing status**: Look for errors in Application Insights
2. **Verify file formats**: Ensure supported document types
3. **Test search index**: Query Azure AI Search directly
4. **Review permissions**: Check if ACLs are blocking access
5. **Validate ingestion**: Confirm documents were processed successfully

### Responses are slow or timing out

Performance troubleshooting:
1. **Check resource utilization**: CPU, memory, and quota usage
2. **Optimize search queries**: Reduce top parameter, simplify queries
3. **Monitor Azure OpenAI**: Check for rate limiting or quota issues
4. **Review Application Insights**: Identify bottlenecks in the pipeline
5. **Scale resources**: Increase container or search service capacity

### How do I get detailed error information?

Debugging approaches:
1. **Application Insights**: Comprehensive error logging and telemetry
2. **Container logs**: Real-time logs from Container Apps
3. **Azure portal**: Service-specific logs and metrics
4. **Debug mode**: Enable verbose logging in development
5. **Health endpoints**: Check service status and configuration

## 🛠️ Development & Contributing

### How do I set up a development environment?

Development setup:
1. **Clone repository**: Get the latest code from GitHub
2. **Install dependencies**: Python packages and Node.js modules
3. **Configure environment**: Set up local environment variables
4. **Run locally**: Use `./app/start.sh` for local development
5. **Test changes**: Ensure all tests pass before committing

### Can I contribute to the project?

Yes! Contributions are welcome:
- **Bug reports**: Submit issues on GitHub
- **Feature requests**: Propose new functionality
- **Code contributions**: Submit pull requests
- **Documentation**: Improve guides and examples
- **Community support**: Help other users in discussions

### How do I add a new feature?

Feature development process:
1. **Create an issue**: Describe the proposed feature
2. **Get feedback**: Discuss with maintainers and community
3. **Fork repository**: Create your own copy for development
4. **Implement feature**: Write code, tests, and documentation
5. **Submit PR**: Request review and merge

### What's the testing strategy?

Testing approaches:
- **Unit tests**: Test individual components and functions
- **Integration tests**: Test service interactions
- **End-to-end tests**: Test complete user workflows
- **Performance tests**: Validate scalability and response times
- **Security tests**: Verify authentication and authorization

### How do I report security issues?

Security reporting:
- **Private disclosure**: Email security issues privately to maintainers
- **No public issues**: Don't create public GitHub issues for security problems
- **Responsible disclosure**: Allow time for fixes before public disclosure
- **Security best practices**: Follow Azure security guidelines

---

## 📞 Still Have Questions?

If you can't find the answer to your question:

1. **Search existing issues**: Check GitHub issues and discussions
2. **Check documentation**: Review the comprehensive docs in `/docs`
3. **Ask the community**: Start a discussion on GitHub
4. **Create an issue**: Report bugs or request features
5. **Enterprise support**: Contact Azure support for production issues

### Useful Resources

- **GitHub Repository**: [Azure RAG Accelerator](https://github.com/Azure-Samples/azure-search-openai-demo)
- **Azure Documentation**: [Azure OpenAI Service](https://docs.microsoft.com/azure/cognitive-services/openai/)
- **Community Forum**: [GitHub Discussions](https://github.com/Azure-Samples/azure-search-openai-demo/discussions)
- **Azure Support**: [Azure Portal Support](https://portal.azure.com/#blade/Microsoft_Azure_Support/HelpAndSupportBlade)

---

*This FAQ is regularly updated based on community questions and feedback. Last updated: 2024-01-15* 