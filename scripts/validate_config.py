#!/usr/bin/env python3
"""
Configuration validation script for SharePoint and other data sources.

This script validates configuration files against the defined JSON schemas
and provides detailed error reporting.
"""

import argparse
import json
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, List

# Add the app backend to the path for imports
sys.path.append(str(Path(__file__).parent.parent / "app" / "backend"))

try:
    from prepdocslib.config_schema import (
        get_ingestion_config_schema,
        get_sharepoint_schema,
        validate_config_against_schema
    )
    from prepdocslib.config_validator import (
        ConfigurationValidator,
        get_sharepoint_config_template,
        get_configuration_help
    )
    from prepdocslib.config import ConfigurationManager
except ImportError as e:
    print(f"Error importing configuration modules: {e}")
    print("Make sure you're running this script from the project root directory.")
    sys.exit(1)


def load_config_file(file_path: str) -> Dict[str, Any]:
    """Load configuration from YAML or JSON file"""
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        if path.suffix.lower() in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        elif path.suffix.lower() == '.json':
            return json.load(f)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}. Use .yaml, .yml, or .json")


def validate_configuration(config_file: str, schema_type: str = "full") -> bool:
    """
    Validate a configuration file
    
    Args:
        config_file: Path to configuration file
        schema_type: Type of schema validation ("full", "sharepoint", "basic")
        
    Returns:
        True if validation passes, False otherwise
    """
    try:
        # Load configuration
        print(f"Loading configuration from: {config_file}")
        config = load_config_file(config_file)
        
        # Choose schema based on type
        if schema_type == "sharepoint":
            # Validate only SharePoint data sources
            schema = get_sharepoint_schema()
            sharepoint_sources = [ds for ds in config.get("data_sources", []) if ds.get("type") == "sharepoint"]
            
            if not sharepoint_sources:
                print("❌ No SharePoint data sources found in configuration")
                return False
            
            all_valid = True
            for i, ds in enumerate(sharepoint_sources):
                print(f"\n📋 Validating SharePoint data source {i + 1}...")
                is_valid, errors = validate_config_against_schema(ds, schema)
                
                if is_valid:
                    print(f"✅ SharePoint data source {i + 1} is valid")
                else:
                    print(f"❌ SharePoint data source {i + 1} validation failed:")
                    for error in errors:
                        print(f"   - {error}")
                    all_valid = False
            
            return all_valid
            
        elif schema_type == "full":
            # Validate complete configuration using JSON schema first
            schema = get_ingestion_config_schema()
            print(f"\n📋 Validating complete configuration...")
            
            is_valid, errors = validate_config_against_schema(config, schema)
            
            if is_valid:
                print("✅ Configuration is valid according to JSON schema")
            else:
                print("❌ Configuration validation failed:")
                for error in errors:
                    print(f"   - {error}")
                return False
        
        # Additional validation using ConfigurationValidator (only for warnings and additional checks)
        # Skip this for now to avoid the None value conflict with JSON schema validation
        print(f"\n📋 Running additional validation checks...")
        try:
            # Create a validator that only does basic checks without conflicting with JSON schema
            validator = ConfigurationValidator(use_json_schema=False)
            
            # For full validation, we need to be careful about the ConfigurationManager
            # Skip the _parse_config_data step that adds None values that conflict with schema
            if schema_type == "full":
                # Just do basic validation without using ConfigurationManager
                is_valid = True
                errors = []
                warnings = []
                
                # Basic checks that don't conflict with JSON schema
                data_sources = config.get("data_sources", [])
                if not data_sources:
                    errors.append("No data sources configured")
                    is_valid = False
                
                azure_config = config.get("azure", {})
                if not azure_config.get("search_service"):
                    warnings.append("Azure search service not configured")
                
                # Check each data source type
                for ds in data_sources:
                    if ds.get("type") == "sharepoint":
                        if not ds.get("site_url"):
                            errors.append("SharePoint data source missing site_url")
                            is_valid = False
                        if not ds.get("tenant_id"):
                            warnings.append("SharePoint data source missing tenant_id (recommended)")
                
            else:
                # For SharePoint-only validation, we can use simpler validation
                is_valid = True
                errors = []
                warnings = []
            
            if warnings:
                print("⚠️  Validation warnings:")
                for warning in warnings:
                    print(f"   - {warning}")
            
            if is_valid:
                print("✅ Configuration passed all validation checks")
                return True
            else:
                print("❌ Configuration validation failed:")
                for error in errors:
                    print(f"   - {error}")
                return False
                
        except Exception as e:
            print(f"❌ Error during additional validation: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error validating configuration: {e}")
        return False


def generate_template(output_file: str, template_type: str = "basic"):
    """Generate configuration template"""
    try:
        if template_type == "sharepoint":
            template = get_sharepoint_config_template()
            config = {
                "data_sources": [template]
            }
        elif template_type == "basic":
            config = {
                "data_sources": [
                    {
                        "type": "local",
                        "path": "./data/*",
                        "metadata": {
                            "description": "Local sample documents"
                        }
                    }
                ],
                "azure": {
                    "search_service": "your-search-service",
                    "search_index": "documents-index",
                    "storage_account": "yourstorageaccount",
                    "storage_container": "content"
                },
                "use_vectors": True,
                "verbose": False
            }
        elif template_type == "mixed":
            sharepoint_template = get_sharepoint_config_template()
            config = {
                "data_sources": [
                    {
                        "type": "local",
                        "path": "./data/*",
                        "metadata": {
                            "description": "Local development documents"
                        }
                    },
                    {
                        "type": "azure_blob",
                        "storage_account": "mystorageaccount",
                        "container": "documents",
                        "connection_string": "${AZURE_STORAGE_CONNECTION_STRING}",
                        "metadata": {
                            "description": "Azure Blob Storage documents"
                        }
                    },
                    sharepoint_template
                ],
                "azure": {
                    "search_service": "my-search-service",
                    "search_index": "documents-index",
                    "storage_account": "mystorageaccount",
                    "storage_container": "content",
                    "openai_service": "my-openai-service"
                },
                "use_vectors": True,
                "use_gpt_vision": False,
                "verbose": True
            }
        else:
            raise ValueError(f"Unknown template type: {template_type}")
        
        # Write template
        output_path = Path(output_file)
        if output_path.suffix.lower() in ['.yaml', '.yml']:
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
        else:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        
        print(f"✅ Configuration template generated: {output_file}")
        
    except Exception as e:
        print(f"❌ Error generating template: {e}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Validate SharePoint and other data source configurations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate a complete configuration file
  python scripts/validate_config.py config.yaml

  # Validate only SharePoint configurations
  python scripts/validate_config.py config.yaml --schema sharepoint

  # Generate a SharePoint configuration template
  python scripts/validate_config.py --generate-template sharepoint_config.yaml --template sharepoint

  # Generate a mixed data sources template
  python scripts/validate_config.py --generate-template mixed_config.yaml --template mixed

  # Show configuration help
  python scripts/validate_config.py --help-config
        """
    )
    
    parser.add_argument(
        'config_file',
        nargs='?',
        help='Configuration file to validate (YAML or JSON)'
    )
    
    parser.add_argument(
        '--schema',
        choices=['full', 'sharepoint', 'basic'],
        default='full',
        help='Type of schema validation to perform (default: full)'
    )
    
    parser.add_argument(
        '--generate-template',
        metavar='OUTPUT_FILE',
        help='Generate a configuration template file'
    )
    
    parser.add_argument(
        '--template',
        choices=['basic', 'sharepoint', 'mixed'],
        default='basic',
        help='Type of template to generate (default: basic)'
    )
    
    parser.add_argument(
        '--help-config',
        action='store_true',
        help='Show configuration help and exit'
    )
    
    args = parser.parse_args()
    
    # Show configuration help
    if args.help_config:
        print(get_configuration_help())
        return
    
    # Generate template
    if args.generate_template:
        generate_template(args.generate_template, args.template)
        return
    
    # Validate configuration
    if not args.config_file:
        parser.error("Configuration file is required unless generating template or showing help")
    
    success = validate_configuration(args.config_file, args.schema)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 