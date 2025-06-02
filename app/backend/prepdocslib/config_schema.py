"""
JSON Schema definitions for data source configurations.
"""

import json
from typing import Dict, Any


def get_sharepoint_schema() -> Dict[str, Any]:
    """Get JSON Schema for SharePoint configuration"""
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "title": "SharePoint Data Source Configuration",
        "description": "Configuration schema for SharePoint Online data source",
        "properties": {
            "type": {
                "type": "string",
                "const": "sharepoint",
                "description": "Data source type identifier"
            },
            "tenant_id": {
                "type": "string",
                "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
                "description": "Azure AD tenant ID in GUID format"
            },
            "client_id": {
                "type": "string",
                "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
                "description": "Azure AD application client ID in GUID format"
            },
            "client_secret": {
                "type": "string",
                "minLength": 1,
                "description": "Azure AD application client secret"
            },
            "site_url": {
                "type": "string",
                "pattern": "^https://[a-zA-Z0-9.-]+\\.sharepoint\\.(com|us|de)/sites/[a-zA-Z0-9-]+/?.*$",
                "description": "SharePoint site URL"
            },
            "document_library": {
                "type": "string",
                "minLength": 1,
                "default": "Shared Documents",
                "description": "Name of the SharePoint document library"
            },
            "folder_path": {
                "type": "string",
                "default": "",
                "description": "Specific folder path within the document library"
            },
            "max_file_size_mb": {
                "type": "integer",
                "minimum": 1,
                "maximum": 1000,
                "default": 100,
                "description": "Maximum file size in megabytes"
            },
            "supported_extensions": {
                "type": "array",
                "items": {
                    "type": "string",
                    "pattern": "^\\.[a-zA-Z0-9]+$"
                },
                "default": [".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls", ".txt", ".md"],
                "description": "List of supported file extensions"
            },
            "batch_size": {
                "type": "integer",
                "minimum": 1,
                "maximum": 1000,
                "default": 50,
                "description": "Number of files to process in each batch"
            },
            "enable_incremental_sync": {
                "type": "boolean",
                "default": True,
                "description": "Enable incremental synchronization"
            },
            "sync_state_file": {
                "type": "string",
                "description": "Path to sync state file (auto-generated if not specified)"
            },
            "metadata": {
                "type": "object",
                "additionalProperties": True,
                "description": "Additional metadata for the data source"
            }
        },
        "required": ["type", "tenant_id", "client_id", "client_secret", "site_url"],
        "additionalProperties": False
    }


def get_data_source_schema() -> Dict[str, Any]:
    """Get JSON Schema for any data source configuration"""
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "title": "Data Source Configuration",
        "description": "Configuration schema for all supported data sources",
        "oneOf": [
            {
                "title": "Local File System",
                "type": "object",
                "properties": {
                    "type": {"const": "local"},
                    "path": {
                        "type": "string",
                        "minLength": 1,
                        "description": "Path to local files or directory"
                    },
                    "metadata": {
                        "type": "object",
                        "additionalProperties": True
                    }
                },
                "required": ["type", "path"],
                "additionalProperties": False
            },
            {
                "title": "Azure Blob Storage",
                "type": "object",
                "properties": {
                    "type": {"const": "azure_blob"},
                    "storage_account": {
                        "type": "string",
                        "minLength": 1,
                        "description": "Azure Storage account name"
                    },
                    "container": {
                        "type": "string",
                        "minLength": 1,
                        "description": "Azure Blob container name"
                    },
                    "blob_prefix": {
                        "type": "string",
                        "description": "Optional blob prefix filter"
                    },
                    "connection_string": {
                        "type": "string",
                        "description": "Azure Storage connection string"
                    },
                    "account_key": {
                        "type": "string",
                        "description": "Azure Storage account key"
                    },
                    "sas_token": {
                        "type": "string",
                        "description": "Azure Storage SAS token"
                    },
                    "metadata": {
                        "type": "object",
                        "additionalProperties": True
                    }
                },
                "required": ["type", "storage_account", "container"],
                "anyOf": [
                    {"required": ["connection_string"]},
                    {"required": ["account_key"]},
                    {"required": ["sas_token"]}
                ],
                "additionalProperties": False
            },
            {
                "title": "Azure Data Lake Gen2",
                "type": "object",
                "properties": {
                    "type": {"const": "adls_gen2"},
                    "storage_account": {
                        "type": "string",
                        "minLength": 1,
                        "description": "Azure Data Lake storage account name"
                    },
                    "filesystem": {
                        "type": "string",
                        "minLength": 1,
                        "description": "Azure Data Lake filesystem name"
                    },
                    "path": {
                        "type": "string",
                        "description": "Optional path within filesystem"
                    },
                    "connection_string": {
                        "type": "string",
                        "description": "Azure Storage connection string"
                    },
                    "account_key": {
                        "type": "string",
                        "description": "Azure Storage account key"
                    },
                    "metadata": {
                        "type": "object",
                        "additionalProperties": True
                    }
                },
                "required": ["type", "storage_account", "filesystem"],
                "anyOf": [
                    {"required": ["connection_string"]},
                    {"required": ["account_key"]}
                ],
                "additionalProperties": False
            },
            get_sharepoint_schema()
        ]
    }


def get_ingestion_config_schema() -> Dict[str, Any]:
    """Get JSON Schema for complete ingestion configuration"""
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "title": "Ingestion Configuration",
        "description": "Complete configuration schema for data ingestion",
        "properties": {
            "data_sources": {
                "type": "array",
                "items": get_data_source_schema(),
                "minItems": 1,
                "description": "List of data sources to process"
            },
            "azure": {
                "type": "object",
                "properties": {
                    "search_service": {
                        "type": "string",
                        "description": "Azure Cognitive Search service name"
                    },
                    "search_index": {
                        "type": "string",
                        "description": "Azure Cognitive Search index name"
                    },
                    "storage_account": {
                        "type": "string",
                        "description": "Azure Storage account for processed content"
                    },
                    "storage_container": {
                        "type": "string",
                        "description": "Azure Storage container for processed content"
                    },
                    "openai_service": {
                        "type": "string",
                        "description": "Azure OpenAI service name"
                    },
                    "openai_endpoint": {
                        "type": "string",
                        "format": "uri",
                        "description": "Azure OpenAI endpoint URL"
                    },
                    "openai_deployment": {
                        "type": "string",
                        "description": "Azure OpenAI deployment name"
                    },
                    "openai_model": {
                        "type": "string",
                        "description": "Azure OpenAI model name"
                    },
                    "openai_api_version": {
                        "type": "string",
                        "description": "Azure OpenAI API version"
                    },
                    "document_intelligence_service": {
                        "type": "string",
                        "description": "Azure Document Intelligence service name"
                    },
                    "subscription_id": {
                        "type": "string",
                        "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
                        "description": "Azure subscription ID"
                    },
                    "tenant_id": {
                        "type": "string",
                        "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
                        "description": "Azure tenant ID"
                    }
                },
                "additionalProperties": False
            },
            "use_integrated_vectorization": {
                "type": "boolean",
                "default": False,
                "description": "Use integrated vectorization"
            },
            "use_gpt_vision": {
                "type": "boolean",
                "default": False,
                "description": "Use GPT-4 Vision for image processing"
            },
            "use_acls": {
                "type": "boolean",
                "default": False,
                "description": "Use access control lists"
            },
            "use_vectors": {
                "type": "boolean",
                "default": True,
                "description": "Use vector embeddings"
            },
            "use_local_pdf_parser": {
                "type": "boolean",
                "default": False,
                "description": "Use local PDF parser instead of Azure Document Intelligence"
            },
            "use_local_html_parser": {
                "type": "boolean",
                "default": False,
                "description": "Use local HTML parser"
            },
            "disable_batch_vectors": {
                "type": "boolean",
                "default": False,
                "description": "Disable batch vector processing"
            },
            "default_category": {
                "type": "string",
                "description": "Default category for documents"
            },
            "skip_blobs": {
                "type": "boolean",
                "default": False,
                "description": "Skip blob processing"
            },
            "verbose": {
                "type": "boolean",
                "default": False,
                "description": "Enable verbose logging"
            }
        },
        "required": ["data_sources"],
        "additionalProperties": False
    }


def validate_config_against_schema(config: Dict[str, Any], schema: Dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate configuration against JSON schema
    
    Args:
        config: Configuration dictionary to validate
        schema: JSON schema to validate against
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    try:
        import jsonschema
        validator = jsonschema.Draft7Validator(schema)
        errors = list(validator.iter_errors(config))
        
        if errors:
            error_messages = []
            for error in errors:
                path = ".".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"
                error_messages.append(f"{path}: {error.message}")
            return False, error_messages
        
        return True, []
        
    except ImportError:
        # Fall back to basic validation if jsonschema is not available
        return True, ["jsonschema library not available for advanced validation"]
    except Exception as e:
        return False, [f"Schema validation error: {str(e)}"] 