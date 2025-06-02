# Data source plugins package

def register_all_plugins():
    """Register all available data source plugins"""
    from .legacy_adapters import register_legacy_plugins
    from .sharepoint_connector import register_sharepoint_plugin
    
    # Register legacy adapter plugins (local, azure_blob, adls_gen2)
    register_legacy_plugins()
    
    # Register SharePoint plugin
    register_sharepoint_plugin()


# Auto-register plugins on import
register_all_plugins() 