import json
import os
import tempfile
import pytest
from unittest.mock import patch

from prepdocslib.config import (
    DataSourceConfig,
    AzureConfig,
    IngestionConfig,
    ConfigurationManager,
    get_configuration_manager
)


class TestDataSourceConfig:
    def test_local_data_source_config(self):
        config = DataSourceConfig(type="local", path="./data/*")
        assert config.type == "local"
        assert config.path == "./data/*"
        assert config.storage_account is None
        assert config.metadata == {}

    def test_azure_blob_data_source_config(self):
        config = DataSourceConfig(
            type="azure_blob",
            storage_account="testaccount",
            container="documents",
            blob_prefix="docs/",
            metadata={"description": "Test documents"}
        )
        assert config.type == "azure_blob"
        assert config.storage_account == "testaccount"
        assert config.container == "documents"
        assert config.blob_prefix == "docs/"
        assert config.metadata["description"] == "Test documents"

    def test_adls_gen2_data_source_config(self):
        config = DataSourceConfig(
            type="adls_gen2",
            storage_account="testdatalake",
            filesystem="documents",
            path="processed/",
            account_key="test-key"
        )
        assert config.type == "adls_gen2"
        assert config.storage_account == "testdatalake"
        assert config.filesystem == "documents"
        assert config.path == "processed/"
        assert config.account_key == "test-key"


class TestAzureConfig:
    def test_azure_config_creation(self):
        config = AzureConfig(
            search_service="test-search",
            search_index="test-index",
            storage_account="teststorage",
            openai_service="test-openai"
        )
        assert config.search_service == "test-search"
        assert config.search_index == "test-index"
        assert config.storage_account == "teststorage"
        assert config.openai_service == "test-openai"


class TestIngestionConfig:
    def test_ingestion_config_defaults(self):
        config = IngestionConfig()
        assert config.data_sources == []
        assert isinstance(config.azure, AzureConfig)
        assert config.use_integrated_vectorization is False
        assert config.use_gpt_vision is False
        assert config.use_acls is False
        assert config.use_vectors is True

    def test_ingestion_config_with_data_sources(self):
        data_source = DataSourceConfig(type="local", path="./data/*")
        azure_config = AzureConfig(search_service="test-search")
        
        config = IngestionConfig(
            data_sources=[data_source],
            azure=azure_config,
            use_gpt_vision=True
        )
        
        assert len(config.data_sources) == 1
        assert config.data_sources[0].type == "local"
        assert config.azure.search_service == "test-search"
        assert config.use_gpt_vision is True


class TestConfigurationManager:
    def test_load_from_json_file(self):
        config_data = {
            "data_sources": [
                {
                    "type": "local",
                    "path": "./test-data/*",
                    "metadata": {"description": "Test files"}
                }
            ],
            "azure": {
                "search_service": "test-search-service",
                "search_index": "test-index"
            },
            "use_gpt_vision": True,
            "verbose": True
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            manager = ConfigurationManager(temp_path)
            config = manager.load_config()
            
            assert len(config.data_sources) == 1
            assert config.data_sources[0].type == "local"
            assert config.data_sources[0].path == "./test-data/*"
            assert config.azure.search_service == "test-search-service"
            assert config.azure.search_index == "test-index"
            assert config.use_gpt_vision is True
            assert config.verbose is True
        finally:
            os.unlink(temp_path)

    def test_load_from_environment_variables(self):
        env_vars = {
            "AZURE_SEARCH_SERVICE": "env-search-service",
            "AZURE_SEARCH_INDEX": "env-search-index",
            "AZURE_STORAGE_ACCOUNT": "env-storage-account",
            "AZURE_STORAGE_CONTAINER": "env-container",
            "AZURE_OPENAI_SERVICE": "env-openai-service",
            "USE_GPT4V": "true",
            "USE_VECTORS": "false",
            "AZURE_ENFORCE_ACCESS_CONTROL": "true"
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            manager = ConfigurationManager("nonexistent-file.json")
            config = manager.load_config()
            
            # Should create a local data source by default
            assert len(config.data_sources) == 1
            assert config.data_sources[0].type == "local"
            assert config.data_sources[0].path == "./data/*"
            
            # Azure config from environment
            assert config.azure.search_service == "env-search-service"
            assert config.azure.search_index == "env-search-index"
            assert config.azure.storage_account == "env-storage-account"
            assert config.azure.storage_container == "env-container"
            assert config.azure.openai_service == "env-openai-service"
            
            # Boolean flags
            assert config.use_gpt_vision is True
            assert config.use_vectors is False
            assert config.use_acls is True

    def test_load_from_environment_with_adls_gen2(self):
        env_vars = {
            "AZURE_ADLS_GEN2_STORAGE_ACCOUNT": "test-datalake",
            "AZURE_ADLS_GEN2_FILESYSTEM": "documents",
            "AZURE_ADLS_GEN2_FILESYSTEM_PATH": "processed/",
            "AZURE_ADLS_GEN2_KEY": "test-key",
            "AZURE_SEARCH_SERVICE": "test-search"
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            manager = ConfigurationManager("nonexistent-file.json")
            config = manager.load_config()
            
            # Should create ADLS Gen2 data source
            assert len(config.data_sources) == 1
            assert config.data_sources[0].type == "adls_gen2"
            assert config.data_sources[0].storage_account == "test-datalake"
            assert config.data_sources[0].filesystem == "documents"
            assert config.data_sources[0].path == "processed/"
            assert config.data_sources[0].account_key == "test-key"

    def test_environment_overlay_on_file_config(self):
        # Create a config file
        config_data = {
            "data_sources": [{"type": "local", "path": "./data/*"}],
            "azure": {
                "search_service": "file-search-service",
                "search_index": "file-index"
            },
            "use_gpt_vision": False
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        # Set environment variables that should override
        env_vars = {
            "AZURE_SEARCH_SERVICE": "env-search-service",
            "USE_GPT4V": "true"
        }
        
        try:
            with patch.dict(os.environ, env_vars, clear=False):
                manager = ConfigurationManager(temp_path)
                config = manager.load_config()
                
                # Environment should override file values
                assert config.azure.search_service == "env-search-service"
                assert config.use_gpt_vision is True
                
                # File values should remain for non-overridden settings
                assert config.azure.search_index == "file-index"
        finally:
            os.unlink(temp_path)

    def test_save_config_to_json(self):
        data_source = DataSourceConfig(
            type="azure_blob",
            storage_account="testaccount",
            container="documents",
            metadata={"description": "Test docs"}
        )
        azure_config = AzureConfig(
            search_service="test-search",
            search_index="test-index"
        )
        config = IngestionConfig(
            data_sources=[data_source],
            azure=azure_config,
            use_gpt_vision=True,
            verbose=True
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            manager = ConfigurationManager()
            manager.save_config(config, temp_path)
            
            # Load and verify
            with open(temp_path, 'r') as f:
                saved_data = json.load(f)
            
            assert len(saved_data["data_sources"]) == 1
            assert saved_data["data_sources"][0]["type"] == "azure_blob"
            assert saved_data["data_sources"][0]["storage_account"] == "testaccount"
            assert saved_data["azure"]["search_service"] == "test-search"
            assert saved_data["use_gpt_vision"] is True
            assert saved_data["verbose"] is True
        finally:
            os.unlink(temp_path)

    def test_get_configuration_manager_factory(self):
        manager = get_configuration_manager()
        assert isinstance(manager, ConfigurationManager)
        assert manager.config_path is None
        
        manager_with_path = get_configuration_manager("test-config.json")
        assert isinstance(manager_with_path, ConfigurationManager)
        assert manager_with_path.config_path == "test-config.json"


@pytest.mark.asyncio
async def test_configuration_integration():
    """Integration test to ensure configuration works with the overall system"""
    config_data = {
        "data_sources": [
            {
                "type": "local",
                "path": "./test-data/*",
                "metadata": {"description": "Integration test files"}
            }
        ],
        "azure": {
            "search_service": "integration-test-search",
            "search_index": "integration-test-index",
            "storage_account": "integrationteststorage",
            "storage_container": "test-container"
        },
        "use_integrated_vectorization": False,
        "use_gpt_vision": False,
        "use_acls": False,
        "verbose": True
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name
    
    try:
        manager = ConfigurationManager(temp_path)
        config = manager.load_config()
        
        # Verify the configuration can be used for data source creation
        from prepdocslib.datasourceconnector import DataSourceConnectorFactory
        
        # This should not raise an exception
        connector = DataSourceConnectorFactory.create_connector(config.data_sources[0])
        assert connector is not None
        
        # Verify configuration validation
        assert DataSourceConnectorFactory.validate_config(config.data_sources[0]) is True
        
    finally:
        os.unlink(temp_path) 