# SharePoint Configuration Guide

This guide provides comprehensive instructions for configuring SharePoint as a data source in the Azure RAG Accelerator.

## Overview

The SharePoint connector enables ingestion of documents from SharePoint Online document libraries using the Microsoft Graph API. It supports:

- OAuth2/Azure AD authentication
- Multiple SharePoint sites and document libraries
- Incremental synchronization
- File filtering by type and size
- Batch processing for performance
- Rich metadata extraction

## Prerequisites

### 1. Azure AD App Registration

Before configuring SharePoint, you need to register an application in Azure AD:

1. Go to [Azure Portal](https://portal.azure.com) → Azure Active Directory → App registrations
2. Click "New registration"
3. Provide a name (e.g., "RAG Accelerator SharePoint Connector")
4. Select "Accounts in this organizational directory only"
5. Click "Register"

### 2. API Permissions

Configure the following Microsoft Graph API permissions:

**Application Permissions (Recommended for unattended scenarios):**
- `Sites.Read.All` - Read items in all site collections
- `Files.Read.All` - Read files in all site collections

**Delegated Permissions (For user context scenarios):**
- `Sites.Read.All` - Read items in all site collections
- `Files.Read.All` - Read files in all site collections

### 3. Client Secret

1. In your app registration, go to "Certificates & secrets"
2. Click "New client secret"
3. Provide a description and expiration period
4. Copy the secret value (you won't be able to see it again)

## Configuration Schema

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `type` | string | Must be "sharepoint" | `"sharepoint"` |
| `tenant_id` | string | Azure AD tenant ID | `"12345678-1234-1234-1234-123456789012"` |
| `client_id` | string | Azure AD app client ID | `"87654321-4321-4321-4321-210987654321"` |
| `client_secret` | string | Azure AD app client secret | `"your-secret-value"` |
| `site_url` | string | SharePoint site URL | `"https://contoso.sharepoint.com/sites/documents"` |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `document_library` | string | `"Shared Documents"` | Name of the document library |
| `folder_path` | string | `""` | Specific folder path within the library |
| `max_file_size_mb` | integer | `100` | Maximum file size in MB |
| `supported_extensions` | array | `[".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls", ".txt", ".md"]` | Allowed file extensions |
| `batch_size` | integer | `50` | Number of files to process in each batch |
| `enable_incremental_sync` | boolean | `true` | Enable incremental synchronization |
| `sync_state_file` | string | Auto-generated | Path to sync state file |

## Configuration Examples

### Basic SharePoint Configuration

```json
{
  "data_sources": [
    {
      "type": "sharepoint",
      "tenant_id": "12345678-1234-1234-1234-123456789012",
      "client_id": "87654321-4321-4321-4321-210987654321",
      "client_secret": "your-secret-value",
      "site_url": "https://contoso.sharepoint.com/sites/documents",
      "metadata": {
        "description": "Main document repository"
      }
    }
  ]
}
```

### Advanced SharePoint Configuration

```json
{
  "data_sources": [
    {
      "type": "sharepoint",
      "tenant_id": "12345678-1234-1234-1234-123456789012",
      "client_id": "87654321-4321-4321-4321-210987654321",
      "client_secret": "your-secret-value",
      "site_url": "https://contoso.sharepoint.com/sites/policies",
      "document_library": "Policy Documents",
      "folder_path": "current-policies",
      "max_file_size_mb": 50,
      "supported_extensions": [".pdf", ".docx"],
      "batch_size": 25,
      "enable_incremental_sync": true,
      "metadata": {
        "description": "Current company policies",
        "category": "policies"
      }
    }
  ]
}
```

### Multiple SharePoint Sources

```json
{
  "data_sources": [
    {
      "type": "sharepoint",
      "tenant_id": "12345678-1234-1234-1234-123456789012",
      "client_id": "87654321-4321-4321-4321-210987654321",
      "client_secret": "your-secret-value",
      "site_url": "https://contoso.sharepoint.com/sites/hr",
      "document_library": "HR Documents",
      "metadata": {
        "description": "HR policies and procedures"
      }
    },
    {
      "type": "sharepoint",
      "tenant_id": "12345678-1234-1234-1234-123456789012",
      "client_id": "87654321-4321-4321-4321-210987654321",
      "client_secret": "your-secret-value",
      "site_url": "https://contoso.sharepoint.com/sites/engineering",
      "document_library": "Technical Docs",
      "folder_path": "specifications",
      "metadata": {
        "description": "Technical specifications"
      }
    }
  ]
}
```

## Environment Variables

You can also configure SharePoint using environment variables:

```bash
# Required
SHAREPOINT_TENANT_ID=12345678-1234-1234-1234-123456789012
SHAREPOINT_CLIENT_ID=87654321-4321-4321-4321-210987654321
SHAREPOINT_CLIENT_SECRET=your-secret-value
SHAREPOINT_SITE_URL=https://contoso.sharepoint.com/sites/documents

# Optional
SHAREPOINT_DOCUMENT_LIBRARY=Shared Documents
SHAREPOINT_FOLDER_PATH=policies
SHAREPOINT_MAX_FILE_SIZE_MB=100
SHAREPOINT_ENABLE_INCREMENTAL_SYNC=true
```

## Security Considerations

### 1. Client Secret Management

- Store client secrets securely (Azure Key Vault, environment variables)
- Rotate secrets regularly
- Use different secrets for different environments

### 2. Permissions

- Use least privilege principle
- Consider using application permissions for unattended scenarios
- Use delegated permissions when user context is required

### 3. Network Security

- Ensure secure network connectivity to SharePoint Online
- Consider using Azure Private Endpoints if available

## Incremental Synchronization

The SharePoint connector supports incremental sync to process only new or modified files:

### How It Works

1. **First Run**: Processes all files in the specified location
2. **Subsequent Runs**: Only processes files modified since the last successful sync
3. **State Tracking**: Maintains sync state in a local JSON file

### Configuration

```json
{
  "enable_incremental_sync": true,
  "sync_state_file": ".sharepoint_sync_custom.json"
}
```

### State File Format

```json
{
  "last_sync_timestamp": "2024-01-15T10:30:00Z",
  "site_url": "https://contoso.sharepoint.com/sites/documents",
  "document_library": "Shared Documents"
}
```

## Performance Optimization

### Batch Processing

Configure batch size based on your environment:

```json
{
  "batch_size": 50  // Adjust based on memory and network capacity
}
```

### File Filtering

Optimize performance by filtering files:

```json
{
  "max_file_size_mb": 100,
  "supported_extensions": [".pdf", ".docx"],  // Only process specific types
  "folder_path": "important-docs"  // Target specific folders
}
```

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Verify tenant ID, client ID, and client secret
   - Check API permissions in Azure AD
   - Ensure app registration is not expired

2. **Site Not Found**
   - Verify site URL format
   - Ensure the app has access to the site
   - Check if site exists and is accessible

3. **Document Library Not Found**
   - Verify document library name (case-sensitive)
   - Check if the library exists in the specified site
   - Ensure proper permissions to access the library

4. **Large File Issues**
   - Adjust `max_file_size_mb` setting
   - Monitor memory usage during processing
   - Consider processing large files separately

### Logging

Enable verbose logging for troubleshooting:

```json
{
  "verbose": true
}
```

### Testing Connection

The connector includes connection testing capabilities:

```python
from prepdocslib.plugins.sharepoint_connector import SharePointConnector

config = {
    "tenant_id": "your-tenant-id",
    "client_id": "your-client-id", 
    "client_secret": "your-client-secret",
    "site_url": "https://contoso.sharepoint.com/sites/documents"
}

connector = SharePointConnector(config)
success = await connector.test_connection()
print(f"Connection test: {'Success' if success else 'Failed'}")
```

## Migration from Other Sources

### From File Shares

When migrating from file shares to SharePoint:

1. Upload files to SharePoint document libraries
2. Maintain folder structure if needed
3. Update configuration to point to SharePoint
4. Test with a subset of documents first

### From Other Cloud Storage

When migrating from other cloud storage:

1. Consider using SharePoint migration tools
2. Preserve metadata where possible
3. Update file paths in configuration
4. Validate document accessibility

## Best Practices

1. **Start Small**: Begin with a single document library
2. **Test Thoroughly**: Validate configuration with test documents
3. **Monitor Performance**: Watch for memory and network usage
4. **Regular Maintenance**: Monitor sync state files and logs
5. **Security First**: Follow security best practices for credentials
6. **Documentation**: Document your SharePoint site structure and configuration

## Support

For additional support:

1. Check the application logs for detailed error messages
2. Verify Azure AD app registration and permissions
3. Test connectivity to SharePoint Online
4. Review Microsoft Graph API documentation
5. Contact your SharePoint administrator for site-specific issues 