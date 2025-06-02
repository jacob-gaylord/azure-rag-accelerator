#!/usr/bin/env python3
"""
Basic tests for the new data source plugin architecture.
This validates that the refactoring maintains backward compatibility.
"""

import asyncio
import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, Any

# Test the plugin architecture
from prepdocslib.plugin_base import get_plugin_registry, DataSourceMetadata
from prepdocslib.datasourceconnector import DataSourceConnectorFactory, MultiDataSourceConnector
from prepdocslib.config import DataSourceConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_plugin_registry():
    """Test that the plugin registry is working correctly"""
    logger.info("Testing plugin registry...")
    
    registry = get_plugin_registry()
    
    # Check that legacy plugins are registered
    plugin_names = registry.list_plugin_names()
    logger.info(f"Registered plugins: {plugin_names}")
    
    expected_plugins = ["local", "azure_blob", "adls_gen2"]
    for plugin_name in expected_plugins:
        assert plugin_name in plugin_names, f"Plugin {plugin_name} not registered"
        
        plugin = registry.get_plugin(plugin_name)
        assert plugin is not None, f"Plugin {plugin_name} not found"
        
        metadata = plugin.metadata
        assert isinstance(metadata, DataSourceMetadata), f"Invalid metadata for {plugin_name}"
        logger.info(f"Plugin {plugin_name}: {metadata.description}")
    
    logger.info("✅ Plugin registry test passed")


async def test_local_file_connector():
    """Test the local file connector using both old and new approaches"""
    logger.info("Testing local file connector...")
    
    # Create a temporary directory with test files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files
        test_files = ["test1.txt", "test2.txt", "subdir/test3.txt"]
        for file_path in test_files:
            full_path = Path(temp_dir) / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(f"Content of {file_path}")
        
        # Test with DataSourceConfig (legacy approach)
        config_legacy = DataSourceConfig(
            type="local",
            path=f"{temp_dir}/*"
        )
        
        connector_legacy = DataSourceConnectorFactory.create_connector(
            config_legacy, 
            use_plugin_architecture=False
        )
        
        # Test with dict config (new approach)
        config_dict = {
            "type": "local",
            "path": f"{temp_dir}/*"
        }
        
        connector_new = DataSourceConnectorFactory.create_connector(
            config_dict,
            use_plugin_architecture=True
        )
        
        # Test both connectors produce the same results
        paths_legacy = []
        async for path in connector_legacy.list_paths():
            paths_legacy.append(path)
        
        paths_new = []
        async for path in connector_new.list_paths():
            paths_new.append(path)
        
        # Sort for comparison
        paths_legacy.sort()
        paths_new.sort()
        
        logger.info(f"Legacy connector found {len(paths_legacy)} files")
        logger.info(f"New connector found {len(paths_new)} files")
        
        assert len(paths_legacy) > 0, "Legacy connector found no files"
        assert len(paths_new) > 0, "New connector found no files"
        
        # Both should find the same files
        assert set(paths_legacy) == set(paths_new), "Connectors found different files"
        
    logger.info("✅ Local file connector test passed")


async def test_connector_factory_backward_compatibility():
    """Test that the connector factory maintains backward compatibility"""
    logger.info("Testing connector factory backward compatibility...")
    
    # Test supported types
    supported_types = DataSourceConnectorFactory.get_supported_types()
    logger.info(f"Supported types: {supported_types}")
    
    expected_types = ["local", "azure_blob", "adls_gen2"]
    for expected_type in expected_types:
        assert expected_type in supported_types, f"Type {expected_type} not supported"
    
    # Test config validation
    valid_local_config = DataSourceConfig(type="local", path="/tmp/*")
    assert DataSourceConnectorFactory.validate_config(valid_local_config), "Valid local config failed validation"
    
    invalid_local_config = DataSourceConfig(type="local", path=None)
    assert not DataSourceConnectorFactory.validate_config(invalid_local_config), "Invalid local config passed validation"
    
    # Test dict config validation
    valid_dict_config = {"type": "local", "path": "/tmp/*"}
    assert DataSourceConnectorFactory.validate_config(valid_dict_config), "Valid dict config failed validation"
    
    invalid_dict_config = {"type": "local"}
    assert not DataSourceConnectorFactory.validate_config(invalid_dict_config), "Invalid dict config passed validation"
    
    logger.info("✅ Connector factory backward compatibility test passed")


async def test_multi_data_source_connector():
    """Test the multi data source connector"""
    logger.info("Testing multi data source connector...")
    
    # Create temporary directories
    with tempfile.TemporaryDirectory() as temp_dir1, tempfile.TemporaryDirectory() as temp_dir2:
        # Create test files in both directories
        for i, temp_dir in enumerate([temp_dir1, temp_dir2], 1):
            test_file = Path(temp_dir) / f"test{i}.txt"
            test_file.write_text(f"Content from directory {i}")
        
        # Create configs for both directories
        configs = [
            {"type": "local", "path": f"{temp_dir1}/*"},
            {"type": "local", "path": f"{temp_dir2}/*"}
        ]
        
        # Test with new architecture
        multi_connector = MultiDataSourceConnector(
            configs=configs,
            use_plugin_architecture=True
        )
        
        # Count files from all sources
        all_paths = []
        async for path in multi_connector.list_all_paths():
            all_paths.append(path)
        
        logger.info(f"Multi-connector found {len(all_paths)} files total")
        assert len(all_paths) >= 2, "Multi-connector should find files from both sources"
        
        # Test that we can get files from both directories
        dir1_files = [p for p in all_paths if temp_dir1 in p]
        dir2_files = [p for p in all_paths if temp_dir2 in p]
        
        assert len(dir1_files) > 0, "No files found from first directory"
        assert len(dir2_files) > 0, "No files found from second directory"
        
    logger.info("✅ Multi data source connector test passed")


async def test_config_templates():
    """Test configuration templates for plugins"""
    logger.info("Testing configuration templates...")
    
    registry = get_plugin_registry()
    
    for plugin_name in ["local", "azure_blob", "adls_gen2"]:
        plugin = registry.get_plugin(plugin_name)
        assert plugin is not None, f"Plugin {plugin_name} not found"
        
        template = plugin.get_config_template()
        assert isinstance(template, dict), f"Template for {plugin_name} is not a dict"
        assert template.get("type") == plugin_name, f"Template type mismatch for {plugin_name}"
        
        logger.info(f"Template for {plugin_name}: {template}")
    
    logger.info("✅ Configuration templates test passed")


async def main():
    """Run all tests"""
    logger.info("Starting plugin architecture tests...")
    
    try:
        await test_plugin_registry()
        await test_local_file_connector()
        await test_connector_factory_backward_compatibility()
        await test_multi_data_source_connector()
        await test_config_templates()
        
        logger.info("🎉 All plugin architecture tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1) 