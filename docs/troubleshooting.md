# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the Azure RAG Accelerator. Use the table of contents to quickly find solutions to specific problems.

## 📋 Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Authentication Issues](#authentication-issues)
- [Azure Service Configuration](#azure-service-configuration)
- [Data Source Issues](#data-source-issues)
- [SharePoint Integration Problems](#sharepoint-integration-problems)
- [Search and AI Service Issues](#search-and-ai-service-issues)
- [Performance Problems](#performance-problems)
- [Chat and API Issues](#chat-and-api-issues)
- [Upload and File Processing](#upload-and-file-processing)
- [Observability and Monitoring](#observability-and-monitoring)
- [Common Error Messages](#common-error-messages)
- [Performance Optimization](#performance-optimization)
- [Debugging Tools](#debugging-tools)
- [Known Limitations](#known-limitations)
- [FAQ](#faq)

## 🩺 Quick Diagnostics

### Health Check Endpoints

1. **Application Health**:
   ```bash
   curl https://your-app.azurecontainerapps.io/health
   ```

2. **Configuration Check**:
   ```bash
   curl https://your-app.azurecontainerapps.io/config
   ```

3. **Authentication Status**:
   ```bash
   curl https://your-app.azurecontainerapps.io/auth_setup
   ```

### Log Locations

- **Container Apps Logs**: Azure Portal → Container Apps → Your App → Monitoring → Log stream
- **Application Insights**: Azure Portal → Application Insights → Transaction search
- **Azure Search Logs**: Azure Portal → Cognitive Search → Monitoring → Diagnostic settings

## 🔐 Authentication Issues

### Problem: "Authentication failed" or 401 errors

**Symptoms**:
- Users cannot access the application
- API calls return 401 Unauthorized
- Authentication redirect loops

**Solutions**:

1. **Check Azure AD Configuration**:
   ```bash
   # Verify app registration exists
   az ad app list --display-name "your-app-name"
   
   # Check redirect URIs
   az ad app show --id "your-app-id" --query "web.redirectUris"
   ```

2. **Verify Environment Variables**:
   ```bash
   # Required authentication variables
   AZURE_AUTH_TYPE=azure_ad
   AZURE_CLIENT_ID=your-client-id
   AZURE_TENANT_ID=your-tenant-id
   AZURE_CLIENT_SECRET=your-client-secret
   ```

3. **Check Application Permissions**:
   - Navigate to Azure Portal → Azure AD → App registrations
   - Ensure your app has proper API permissions
   - Grant admin consent if required

### Problem: "Invalid tenant ID" errors

**Solutions**:
1. Verify `AZURE_TENANT_ID` is correct
2. Check that the user belongs to the correct tenant
3. Ensure the app registration is in the correct tenant

## ⚙️ Azure Service Configuration

### Problem: "Service not found" or connection errors

**Common Issues**:

1. **Resource Names Mismatch**:
   ```bash
   # Check if resources exist
   az search service show --name "your-search-service" --resource-group "your-rg"
   az cognitiveservices account show --name "your-openai-service" --resource-group "your-rg"
   ```

2. **Missing Role Assignments**:
   ```bash
   # Grant necessary permissions
   az role assignment create \
     --assignee "your-user-or-service-principal" \
     --role "Cognitive Services OpenAI User" \
     --scope "/subscriptions/your-sub/resourceGroups/your-rg/providers/Microsoft.CognitiveServices/accounts/your-openai"
   ```

3. **Network Access Issues**:
   - Check if services are behind private endpoints
   - Verify firewall rules allow your application's IP
   - Ensure VNet integration is configured correctly

### Problem: "Quota exceeded" errors

**Solutions**:
1. **Check OpenAI Quotas**:
   ```bash
   az cognitiveservices account list-usage \
     --name "your-openai-service" \
     --resource-group "your-rg"
   ```

2. **Monitor Search Service Usage**:
   - Navigate to Azure Portal → Cognitive Search → Monitoring
   - Check search unit consumption

3. **Request Quota Increases**:
   - Submit support request for OpenAI quota increase
   - Consider upgrading to higher SKU tiers

## 📊 Data Source Issues

### Problem: Documents not appearing in search results

**Diagnostic Steps**:

1. **Check Document Processing Status**:
   ```bash
   # Run document processing manually
   python scripts/prepdocs.py \
     --storageaccount your-storage \
     --container your-container \
     --searchservice your-search \
     --verbose
   ```

2. **Verify Search Index**:
   ```bash
   # Check if index exists and has documents
   az search index show --index-name your-index --service-name your-search
   ```

3. **Check Document Format Support**:
   - Ensure file extensions are supported (.pdf, .docx, .txt, etc.)
   - Verify file sizes are within limits (default: 100MB)
   - Check for corruption in source documents

### Problem: SharePoint documents not syncing

**Solutions**:

1. **Verify SharePoint Permissions**:
   ```bash
   # Test SharePoint connection
   python scripts/test_sharepoint_connection.py \
     --tenant-id your-tenant \
     --client-id your-client \
     --site-url your-site-url
   ```

2. **Check Incremental Sync State**:
   ```bash
   # Look for sync state files
   ls -la .sharepoint_sync_*.json
   
   # Reset sync state if needed
   rm .sharepoint_sync_*.json
   ```

3. **Monitor SharePoint API Limits**:
   - Check for throttling errors in logs
   - Implement exponential backoff
   - Reduce batch sizes in configuration

## 🔍 Search and AI Service Issues

### Problem: Poor search relevance or no results

**Solutions**:

1. **Verify Search Configuration**:
   ```bash
   # Check search index schema
   az search index show \
     --index-name your-index \
     --service-name your-search \
     --query "fields[].{name:name,type:type,searchable:searchable}"
   ```

2. **Test Different Search Modes**:
   ```json
   {
     "context": {
       "overrides": {
         "retrieval_mode": "hybrid", // Try "text", "vector", or "hybrid"
         "semantic_ranker": true,
         "top": 10
       }
     }
   }
   ```

3. **Check Vector Embeddings**:
   - Ensure embedding model is available
   - Verify vector fields exist in search index
   - Test embedding generation manually

### Problem: OpenAI API errors or timeouts

**Common Solutions**:

1. **Check API Key and Endpoint**:
   ```bash
   # Test OpenAI connection
   curl -H "Authorization: Bearer $AZURE_OPENAI_API_KEY" \
     "https://your-openai.openai.azure.com/openai/deployments?api-version=2023-12-01-preview"
   ```

2. **Verify Model Deployments**:
   ```bash
   # List available deployments
   az cognitiveservices account deployment list \
     --name your-openai-service \
     --resource-group your-rg
   ```

3. **Handle Rate Limits**:
   - Implement exponential backoff
   - Monitor tokens per minute (TPM) usage
   - Consider upgrading to higher quota

## 🚀 Performance Problems

### Problem: Slow response times

**Diagnostic Steps**:

1. **Check Application Insights**:
   - Navigate to Performance blade
   - Identify slow operations
   - Check for dependency failures

2. **Monitor Resource Usage**:
   ```bash
   # Check container app resource usage
   az containerapp show \
     --name your-app \
     --resource-group your-rg \
     --query "properties.template.containers[0].resources"
   ```

3. **Optimize Search Queries**:
   - Reduce `top` parameter for fewer results
   - Use semantic captions instead of full content
   - Implement result caching

### Problem: High memory usage or out-of-memory errors

**Solutions**:

1. **Increase Container Resources**:
   ```yaml
   # In your bicep template
   resources: {
     cpu: json('1.0')
     memory: '2Gi'
   }
   ```

2. **Optimize Document Processing**:
   - Process documents in smaller batches
   - Reduce concurrent processing
   - Clear temporary files regularly

3. **Profile Memory Usage**:
   ```python
   # Add memory profiling
   import tracemalloc
   tracemalloc.start()
   # Your code here
   current, peak = tracemalloc.get_traced_memory()
   print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
   ```

## 💬 Chat and API Issues

### Problem: Chat responses are incomplete or cut off

**Solutions**:

1. **Check Token Limits**:
   ```json
   {
     "context": {
       "overrides": {
         "max_tokens": 1000, // Increase if needed
         "temperature": 0.7
       }
     }
   }
   ```

2. **Monitor Context Length**:
   - Reduce conversation history length
   - Implement conversation summarization
   - Split long documents into smaller chunks

3. **Check for Content Filtering**:
   - Review Azure OpenAI content filtering logs
   - Adjust content safety settings if appropriate

### Problem: Citations not working correctly

**Solutions**:

1. **Verify Citation Configuration**:
   ```bash
   # Check environment variables
   echo $CITATION_STRATEGY
   echo $CITATION_BASE_URL
   ```

2. **Check Source Document URLs**:
   - Ensure blob storage is publicly accessible or properly authenticated
   - Verify URL format matches expected pattern
   - Test document access manually

3. **Debug Citation Extraction**:
   ```python
   # Add debug logging for citations
   import logging
   logging.getLogger('app.backend.approaches').setLevel(logging.DEBUG)
   ```

## 📤 Upload and File Processing

### Problem: File uploads failing

**Solutions**:

1. **Check File Size Limits**:
   ```bash
   # Environment variables
   AZURE_BLOB_MAX_UPLOAD_SIZE=100MB
   MAX_UPLOAD_FILE_SIZE=50MB
   ```

2. **Verify Blob Storage Permissions**:
   ```bash
   # Test blob storage access
   az storage blob upload \
     --account-name your-storage \
     --container-name uploads \
     --name test.txt \
     --file test.txt
   ```

3. **Check Supported File Types**:
   - Ensure file extension is in allowed list
   - Verify Document Intelligence service is available
   - Check for file corruption

### Problem: Document processing errors

**Solutions**:

1. **Check Document Intelligence Service**:
   ```bash
   # Verify service availability
   az cognitiveservices account show \
     --name your-doc-intelligence \
     --resource-group your-rg
   ```

2. **Monitor Processing Logs**:
   ```bash
   # Check for processing errors
   az monitor activity-log list \
     --resource-group your-rg \
     --start-time 2024-01-01T00:00:00Z
   ```

3. **Test Document Processing Manually**:
   ```python
   # Test document processing
   python scripts/test_document_processing.py \
     --file path/to/test.pdf \
     --verbose
   ```

## 📊 Observability and Monitoring

### Problem: Missing logs or telemetry

**Solutions**:

1. **Verify Application Insights Configuration**:
   ```bash
   # Check connection string
   echo $APPLICATIONINSIGHTS_CONNECTION_STRING
   ```

2. **Enable Detailed Logging**:
   ```bash
   # Environment variables
   AZURE_LOG_LEVEL=DEBUG
   ENABLE_PERFORMANCE_TRACKING=true
   ```

3. **Check Sampling Settings**:
   ```python
   # Adjust sampling rate in config
   sampling_percentage = 100  # For development
   ```

## ❌ Common Error Messages

### "Azure Developer CLI could not be found"

**Solution**:
```bash
# Install Azure Developer CLI
curl -fsSL https://aka.ms/install-azd.sh | bash

# Or use package manager
pip install azure-dev
```

### "Invalid subscription or resource group"

**Solution**:
```bash
# Set correct subscription
az account set --subscription "your-subscription-id"

# Verify resource group exists
az group show --name "your-resource-group"
```

### "Microsoft Graph API permission denied"

**Solution**:
1. Navigate to Azure Portal → Azure AD → App registrations
2. Select your application
3. Go to API permissions
4. Add Microsoft Graph permissions (Sites.Read.All, Files.Read.All)
5. Grant admin consent

### "Search index not found"

**Solution**:
```bash
# Create search index
python scripts/prepdocs.py \
  --storageaccount your-storage \
  --container your-container \
  --searchservice your-search \
  --index your-index \
  --verbose
```

### "Cosmos DB connection failed"

**Solution**:
1. Check Cosmos DB connection string
2. Verify database and container exist
3. Check firewall settings
4. Ensure proper role assignments

## 🔧 Performance Optimization

### Search Performance

1. **Index Optimization**:
   - Use appropriate field types (searchable vs. retrievable)
   - Implement search scoring profiles
   - Consider index partitioning for large datasets

2. **Query Optimization**:
   ```json
   {
     "search": "your query",
     "top": 5,
     "searchMode": "all",
     "queryType": "semantic",
     "semanticConfiguration": "default"
   }
   ```

3. **Caching Strategies**:
   - Implement Redis cache for frequent queries
   - Cache embedding vectors
   - Use CDN for static content

### AI Service Optimization

1. **Model Selection**:
   - Use GPT-3.5 for faster responses
   - Reserve GPT-4 for complex queries
   - Implement smart model routing

2. **Token Management**:
   - Monitor token usage patterns
   - Implement conversation summarization
   - Use shorter system prompts

3. **Batch Processing**:
   - Process multiple requests together
   - Use async processing for non-critical operations
   - Implement queue-based processing

## 🛠️ Debugging Tools

### Log Analysis Scripts

```bash
# Extract errors from logs
az monitor activity-log list \
  --resource-group your-rg \
  --status Failed \
  --start-time 2024-01-01T00:00:00Z

# Search specific error patterns
az logs query \
  --workspace your-workspace \
  --analytics-query "
    traces 
    | where message contains 'error'
    | order by timestamp desc
    | take 50"
```

### Health Check Scripts

```python
#!/usr/bin/env python3
"""
Comprehensive health check script for Azure RAG Accelerator
"""

import asyncio
import httpx
import os
from datetime import datetime

async def check_service_health():
    base_url = os.getenv('BASE_URL', 'https://your-app.azurecontainerapps.io')
    
    checks = [
        ('Application Health', f'{base_url}/health'),
        ('Configuration', f'{base_url}/config'),
        ('Authentication Setup', f'{base_url}/auth_setup')
    ]
    
    async with httpx.AsyncClient() as client:
        for name, url in checks:
            try:
                response = await client.get(url, timeout=10)
                status = "✅ PASS" if response.status_code == 200 else "❌ FAIL"
                print(f"{status} {name}: {response.status_code}")
            except Exception as e:
                print(f"❌ FAIL {name}: {e}")

if __name__ == "__main__":
    asyncio.run(check_service_health())
```

### Performance Monitoring

```python
#!/usr/bin/env python3
"""
Performance monitoring script
"""

import time
import httpx
import statistics

async def measure_response_times():
    url = "https://your-app.azurecontainerapps.io/ask"
    headers = {"Authorization": "Bearer your-token"}
    payload = {"question": "What is cloud computing?"}
    
    times = []
    for i in range(10):
        start = time.time()
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
        end = time.time()
        times.append(end - start)
        print(f"Request {i+1}: {end - start:.2f}s")
    
    print(f"\nAverage: {statistics.mean(times):.2f}s")
    print(f"Median: {statistics.median(times):.2f}s")
    print(f"95th percentile: {sorted(times)[int(0.95 * len(times))]:.2f}s")
```

## 🚫 Known Limitations

### Current Limitations

1. **File Size Limits**:
   - Maximum document size: 100MB per file
   - Total upload limit: 1GB per user session
   - Processing timeout: 10 minutes per document

2. **Search Limitations**:
   - Maximum search results: 1000 items
   - Query length limit: 1000 characters
   - Vector search dimensions: 1536 (OpenAI ada-002)

3. **Authentication Constraints**:
   - Single tenant Azure AD only
   - No support for B2C scenarios
   - Session timeout: 60 minutes

4. **SharePoint Limitations**:
   - SharePoint Online only (no on-premises)
   - Maximum site collection: 50 per configuration
   - API throttling: 600 requests per minute

### Workarounds

1. **Large File Processing**:
   - Split large documents into smaller chunks
   - Use document splitting tools before upload
   - Process files in background jobs

2. **Multi-tenant Support**:
   - Deploy separate instances per tenant
   - Use configuration-based tenant routing
   - Implement custom authentication middleware

3. **SharePoint Scale**:
   - Implement incremental synchronization
   - Use multiple app registrations for higher limits
   - Process sites in parallel with rate limiting

## ❓ FAQ

### General Questions

**Q: How do I reset the search index?**

A: Delete and recreate the index:
```bash
az search index delete --index-name your-index --service-name your-search
python scripts/prepdocs.py --storageaccount your-storage --container your-container --searchservice your-search --index your-index
```

**Q: Can I use custom AI models?**

A: Yes, you can configure custom OpenAI deployments:
```bash
AZURE_OPENAI_GPT_DEPLOYMENT=your-custom-gpt4
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=your-custom-embedding
```

**Q: How do I backup my data?**

A: Backup these components:
- Search index (export to JSON)
- Blob storage (use `azcopy` or backup tools)
- Cosmos DB (automated backups or manual export)
- Configuration files and environment variables

**Q: How do I scale for high traffic?**

A: Use these approaches:
- Scale Container Apps to multiple replicas
- Implement Redis caching
- Use CDN for static content
- Optimize search queries and AI model usage

### Troubleshooting Specific Scenarios

**Q: Documents appear in search but not in chat responses**

A: This usually indicates:
- Citation URL configuration issues
- Content filtering blocking responses
- Token limit exceeded in conversation

Check logs for specific error messages and verify citation configuration.

**Q: SharePoint sync is slow or timing out**

A: Common solutions:
- Reduce batch size in configuration
- Implement incremental sync
- Check for API throttling
- Use multiple service principals for higher limits

**Q: Users report authentication loops**

A: Check these settings:
- Redirect URIs match exactly (including trailing slashes)
- App registration has correct permissions
- Token lifetime settings
- Browser cookie settings

## 📞 Getting Help

### Support Channels

1. **GitHub Issues**: Report bugs and request features
2. **Documentation**: Check the latest docs at `/docs`
3. **Community Discussions**: Join discussions on GitHub
4. **Enterprise Support**: Contact your Azure support team

### When Creating Support Requests

Include this information:
- Azure subscription ID
- Resource group and resource names
- Error messages and timestamps
- Steps to reproduce the issue
- Browser/client information (if applicable)
- Configuration details (sanitized)

### Useful Commands for Support

```bash
# Collect diagnostic information
az group show --name your-rg --output table
az resource list --resource-group your-rg --output table
az monitor activity-log list --resource-group your-rg --status Failed --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%SZ)

# Export configuration (remove sensitive data)
env | grep AZURE_ | sort

# Check service availability
curl -s https://your-app.azurecontainerapps.io/health | jq
```

---

*Last updated: 2024-01-15*
*Version: 1.0* 