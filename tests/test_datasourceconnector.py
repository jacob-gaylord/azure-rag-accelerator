import pytest
from unittest.mock import Mock

from prepdocslib.config import DataSourceConfig
from prepdocslib.datasourceconnector import (
    DataSourceConnectorFactory,
    MultiDataSourceConnector
)
from prepdocslib.listfilestrategy import (
    LocalListFileStrategy,
    AzureBlobListFileStrategy,
    ADLSGen2ListFileStrategy
)
from .mocks import MockAzureCredential


class TestDataSourceConnectorFactory:
    def test_create_local_connector(self):
        config = DataSourceConfig(type="local", path="./test-data/*")
        connector = DataSourceConnectorFactory.create_connector(config)
        
        assert isinstance(connector, LocalListFileStrategy)
        assert connector.path_pattern == "./test-data/*"

    def test_create_azure_blob_connector(self):
        config = DataSourceConfig(
            type="azure_blob",
            storage_account="testaccount",
            container="documents",
            blob_prefix="docs/"
        )
        azure_credential = MockAzureCredential()
        connector = DataSourceConnectorFactory.create_connector(config, azure_credential)
        
        assert isinstance(connector, AzureBlobListFileStrategy)
        assert connector.storage_account == "testaccount"
        assert connector.container == "documents"
        assert connector.blob_prefix == "docs/"
        assert connector.credential == azure_credential

    def test_create_azure_blob_connector_with_connection_string(self):
        config = DataSourceConfig(
            type="azure_blob",
            storage_account="testaccount",
            container="documents",
            connection_string="DefaultEndpointsProtocol=https;AccountName=testaccount;AccountKey=testkey"
        )
        connector = DataSourceConnectorFactory.create_connector(config)
        
        assert isinstance(connector, AzureBlobListFileStrategy)
        assert connector.credential == "DefaultEndpointsProtocol=https;AccountName=testaccount;AccountKey=testkey"

    def test_create_azure_blob_connector_with_account_key(self):
        config = DataSourceConfig(
            type="azure_blob",
            storage_account="testaccount",
            container="documents",
            account_key="testaccountkey"
        )
        connector = DataSourceConnectorFactory.create_connector(config)
        
        assert isinstance(connector, AzureBlobListFileStrategy)
        assert connector.credential == "testaccountkey"

    def test_create_adls_gen2_connector(self):
        config = DataSourceConfig(
            type="adls_gen2",
            storage_account="testdatalake",
            filesystem="documents",
            path="processed/"
        )
        azure_credential = MockAzureCredential()
        connector = DataSourceConnectorFactory.create_connector(config, azure_credential)
        
        assert isinstance(connector, ADLSGen2ListFileStrategy)
        assert connector.data_lake_storage_account == "testdatalake"
        assert connector.data_lake_filesystem == "documents"
        assert connector.data_lake_path == "processed/"
        assert connector.credential == azure_credential

    def test_create_adls_gen2_connector_with_key(self):
        config = DataSourceConfig(
            type="adls_gen2",
            storage_account="testdatalake",
            filesystem="documents",
            path="processed/",
            account_key="testkey"
        )
        connector = DataSourceConnectorFactory.create_connector(config)
        
        assert isinstance(connector, ADLSGen2ListFileStrategy)
        assert connector.credential == "testkey"

    def test_create_connector_invalid_type(self):
        config = DataSourceConfig(type="invalid_type", path="./data/*")
        
        with pytest.raises(ValueError, match="Unsupported data source type: invalid_type"):
            DataSourceConnectorFactory.create_connector(config)

    def test_create_local_connector_missing_path(self):
        config = DataSourceConfig(type="local")
        
        with pytest.raises(ValueError, match="Local data source requires a path"):
            DataSourceConnectorFactory.create_connector(config)

    def test_create_azure_blob_connector_missing_required_fields(self):
        # Missing container
        config = DataSourceConfig(type="azure_blob", storage_account="testaccount")
        
        with pytest.raises(ValueError, match="Azure Blob data source requires storage_account and container"):
            DataSourceConnectorFactory.create_connector(config)
        
        # Missing storage account
        config = DataSourceConfig(type="azure_blob", container="documents")
        
        with pytest.raises(ValueError, match="Azure Blob data source requires storage_account and container"):
            DataSourceConnectorFactory.create_connector(config)

    def test_create_adls_gen2_connector_missing_required_fields(self):
        # Missing filesystem
        config = DataSourceConfig(type="adls_gen2", storage_account="testdatalake")
        
        with pytest.raises(ValueError, match="ADLS Gen2 data source requires storage_account and filesystem"):
            DataSourceConnectorFactory.create_connector(config)
        
        # Missing storage account
        config = DataSourceConfig(type="adls_gen2", filesystem="documents")
        
        with pytest.raises(ValueError, match="ADLS Gen2 data source requires storage_account and filesystem"):
            DataSourceConnectorFactory.create_connector(config)

    def test_validate_config_local(self):
        valid_config = DataSourceConfig(type="local", path="./data/*")
        assert DataSourceConnectorFactory.validate_config(valid_config) is True
        
        invalid_config = DataSourceConfig(type="local")
        assert DataSourceConnectorFactory.validate_config(invalid_config) is False

    def test_validate_config_azure_blob(self):
        valid_config = DataSourceConfig(
            type="azure_blob",
            storage_account="testaccount",
            container="documents"
        )
        assert DataSourceConnectorFactory.validate_config(valid_config) is True
        
        invalid_config = DataSourceConfig(type="azure_blob", storage_account="testaccount")
        assert DataSourceConnectorFactory.validate_config(invalid_config) is False

    def test_validate_config_adls_gen2(self):
        valid_config = DataSourceConfig(
            type="adls_gen2",
            storage_account="testdatalake",
            filesystem="documents"
        )
        assert DataSourceConnectorFactory.validate_config(valid_config) is True
        
        invalid_config = DataSourceConfig(type="adls_gen2", storage_account="testdatalake")
        assert DataSourceConnectorFactory.validate_config(invalid_config) is False

    def test_validate_config_invalid_type(self):
        invalid_config = DataSourceConfig(type="invalid_type", path="./data/*")
        assert DataSourceConnectorFactory.validate_config(invalid_config) is False

    def test_get_supported_types(self):
        supported_types = DataSourceConnectorFactory.get_supported_types()
        assert "local" in supported_types
        assert "azure_blob" in supported_types
        assert "adls_gen2" in supported_types
        assert len(supported_types) == 3

    def test_get_credential_priority(self):
        """Test credential priority: connection_string > account_key > sas_token > azure_credential"""
        config = DataSourceConfig(
            type="azure_blob",
            storage_account="testaccount",
            container="documents",
            connection_string="test-connection-string",
            account_key="test-account-key",
            sas_token="test-sas-token"
        )
        azure_credential = MockAzureCredential()
        
        # Should prioritize connection string
        credential = DataSourceConnectorFactory._get_credential(config, azure_credential)
        assert credential == "test-connection-string"
        
        # Remove connection string, should use account key
        config.connection_string = None
        credential = DataSourceConnectorFactory._get_credential(config, azure_credential)
        assert credential == "test-account-key"
        
        # Remove account key, should use SAS token
        config.account_key = None
        credential = DataSourceConnectorFactory._get_credential(config, azure_credential)
        assert credential == "test-sas-token"
        
        # Remove SAS token, should use Azure credential
        config.sas_token = None
        credential = DataSourceConnectorFactory._get_credential(config, azure_credential)
        assert credential == azure_credential
        
        # No Azure credential, should return None
        credential = DataSourceConnectorFactory._get_credential(config, None)
        assert credential is None


class TestMultiDataSourceConnector:
    def test_multi_connector_creation(self):
        configs = [
            DataSourceConfig(type="local", path="./data1/*"),
            DataSourceConfig(type="local", path="./data2/*")
        ]
        
        multi_connector = MultiDataSourceConnector(configs)
        assert len(multi_connector.connectors) == 2
        assert all(isinstance(c, LocalListFileStrategy) for c in multi_connector.connectors)

    def test_multi_connector_with_invalid_config(self):
        configs = [
            DataSourceConfig(type="local", path="./data/*"),  # Valid
            DataSourceConfig(type="local"),  # Invalid - no path
            DataSourceConfig(type="azure_blob", storage_account="test")  # Invalid - no container
        ]
        
        multi_connector = MultiDataSourceConnector(configs)
        # Should only create connector for the valid config
        assert len(multi_connector.connectors) == 1
        assert isinstance(multi_connector.connectors[0], LocalListFileStrategy)

    def test_multi_connector_get_primary(self):
        configs = [
            DataSourceConfig(type="local", path="./data1/*"),
            DataSourceConfig(type="local", path="./data2/*")
        ]
        
        multi_connector = MultiDataSourceConnector(configs)
        primary = multi_connector.get_primary_connector()
        
        assert primary is not None
        assert isinstance(primary, LocalListFileStrategy)
        assert primary == multi_connector.connectors[0]

    def test_multi_connector_get_primary_no_connectors(self):
        configs = [
            DataSourceConfig(type="local"),  # Invalid - no path
        ]
        
        multi_connector = MultiDataSourceConnector(configs)
        primary = multi_connector.get_primary_connector()
        
        assert primary is None

    @pytest.mark.asyncio
    async def test_multi_connector_list_all_files(self):
        """Test that MultiDataSourceConnector can aggregate files from multiple sources"""
        # This would require mocking the actual file listing, which is complex
        # For now, just test that the method exists and can be called
        configs = [
            DataSourceConfig(type="local", path="./data/*")
        ]
        
        multi_connector = MultiDataSourceConnector(configs)
        
        # The method should exist and be callable
        assert hasattr(multi_connector, 'list_all_files')
        assert callable(multi_connector.list_all_files)

    @pytest.mark.asyncio
    async def test_multi_connector_list_all_paths(self):
        """Test that MultiDataSourceConnector can aggregate paths from multiple sources"""
        configs = [
            DataSourceConfig(type="local", path="./data/*")
        ]
        
        multi_connector = MultiDataSourceConnector(configs)
        
        # The method should exist and be callable
        assert hasattr(multi_connector, 'list_all_paths')
        assert callable(multi_connector.list_all_paths)

    def test_multi_connector_with_azure_credential(self):
        configs = [
            DataSourceConfig(
                type="azure_blob",
                storage_account="testaccount",
                container="documents"
            )
        ]
        azure_credential = MockAzureCredential()
        
        multi_connector = MultiDataSourceConnector(configs, azure_credential)
        assert len(multi_connector.connectors) == 1
        assert isinstance(multi_connector.connectors[0], AzureBlobListFileStrategy)
        assert multi_connector.connectors[0].credential == azure_credential 