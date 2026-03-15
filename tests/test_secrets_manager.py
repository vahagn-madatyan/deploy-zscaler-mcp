"""Tests for Secrets Manager module."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

from zscaler_mcp_deploy.aws.secrets_manager import (
    SecretsManager,
    SecretsManagerError,
    SecretResult,
)
from zscaler_mcp_deploy.models import SecretResult as SecretResultModel


class TestSecretResult:
    """Tests for SecretResult dataclass."""
    
    def test_secret_result_creation(self):
        """Test creating a SecretResult with all fields."""
        result = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test",
            name="test-secret",
            version_id="abc123",
            created=True,
            kms_key_id="alias/aws/secretsmanager"
        )
        
        assert result.arn == "arn:aws:secretsmanager:us-east-1:123456789:secret:test"
        assert result.name == "test-secret"
        assert result.version_id == "abc123"
        assert result.created is True
        assert result.kms_key_id == "alias/aws/secretsmanager"
    
    def test_secret_result_defaults(self):
        """Test SecretResult with default values."""
        result = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test",
            name="test-secret"
        )
        
        assert result.version_id is None
        assert result.created is False
        assert result.kms_key_id is None
    
    def test_secret_result_to_dict(self):
        """Test converting SecretResult to dictionary."""
        result = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test",
            name="test-secret",
            version_id="abc123",
            created=True,
            kms_key_id="alias/aws/secretsmanager"
        )
        
        d = result.to_dict()
        assert d["arn"] == "arn:aws:secretsmanager:us-east-1:123456789:secret:test"
        assert d["name"] == "test-secret"
        assert d["version_id"] == "abc123"
        assert d["created"] is True
        assert d["kms_key_id"] == "alias/aws/secretsmanager"


class TestSecretsManagerInitialization:
    """Tests for SecretsManager initialization."""
    
    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        sm = SecretsManager()
        assert sm._region is None
        assert sm._profile_name is None
        assert sm._session is None
        assert sm._client is None
    
    def test_init_with_region(self):
        """Test initialization with region parameter."""
        sm = SecretsManager(region="us-west-2")
        assert sm._region == "us-west-2"
        assert sm._profile_name is None
    
    def test_init_with_profile(self):
        """Test initialization with profile name."""
        sm = SecretsManager(profile_name="my-profile")
        assert sm._profile_name == "my-profile"
        assert sm._region is None
    
    def test_init_with_session(self):
        """Test initialization with pre-configured session."""
        mock_session = Mock()
        sm = SecretsManager(session=mock_session)
        assert sm._session is mock_session
    
    @patch("zscaler_mcp_deploy.aws.secrets_manager.boto3.Session")
    def test_lazy_session_creation_no_profile(self, mock_session_class):
        """Test lazy session creation without profile."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        sm = SecretsManager(region="us-east-1")
        session = sm.session
        
        mock_session_class.assert_called_once_with(region_name="us-east-1")
        assert session is mock_session
    
    @patch("zscaler_mcp_deploy.aws.secrets_manager.boto3.Session")
    def test_lazy_session_creation_with_profile(self, mock_session_class):
        """Test lazy session creation with profile."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        sm = SecretsManager(region="us-east-1", profile_name="my-profile")
        session = sm.session
        
        mock_session_class.assert_called_once_with(
            profile_name="my-profile",
            region_name="us-east-1"
        )
        assert session is mock_session
    
    def test_lazy_client_creation(self):
        """Test lazy client creation."""
        mock_session = Mock()
        mock_client = Mock()
        mock_session.client.return_value = mock_client
        
        sm = SecretsManager(session=mock_session)
        client = sm.client
        
        mock_session.client.assert_called_once_with("secretsmanager")
        assert client is mock_client
    
    def test_session_caching(self):
        """Test that session is cached after first access."""
        mock_session = Mock()
        sm = SecretsManager(session=mock_session)
        
        # Access session twice
        s1 = sm.session
        s2 = sm.session
        
        assert s1 is s2 is mock_session
    
    def test_client_caching(self):
        """Test that client is cached after first access."""
        mock_session = Mock()
        mock_client = Mock()
        mock_session.client.return_value = mock_client
        
        sm = SecretsManager(session=mock_session)
        
        # Access client twice
        c1 = sm.client
        c2 = sm.client
        
        assert c1 is c2 is mock_client
        mock_session.client.assert_called_once_with("secretsmanager")


class TestCreateOrUseSecret:
    """Tests for create_or_use_secret method."""
    
    def test_create_new_secret_success(self):
        """Test creating a new secret successfully."""
        mock_client = Mock()
        mock_client.create_secret.return_value = {
            "ARN": "arn:aws:secretsmanager:us-east-1:123456789:secret:zscaler-creds",
            "Name": "zscaler-creds",
            "VersionId": "v1-abc123"
        }
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        sm = SecretsManager(session=mock_session)
        result = sm.create_or_use_secret(
            secret_name="zscaler-creds",
            username="admin@example.com",
            password="secret123",
            api_key="api-key-123",
            cloud="zscaler"
        )
        
        # Verify the result
        assert result.arn == "arn:aws:secretsmanager:us-east-1:123456789:secret:zscaler-creds"
        assert result.name == "zscaler-creds"
        assert result.version_id == "v1-abc123"
        assert result.created is True
        assert result.kms_key_id == SecretsManager.DEFAULT_KMS_KEY
        
        # Verify the call
        call_args = mock_client.create_secret.call_args[1]
        assert call_args["Name"] == "zscaler-creds"
        assert call_args["Description"] == "Zscaler credentials for zscaler cloud"
        secret_value = json.loads(call_args["SecretString"])
        assert secret_value["username"] == "admin@example.com"
        assert secret_value["password"] == "secret123"
        assert secret_value["api_key"] == "api-key-123"
        assert secret_value["cloud"] == "zscaler"
        assert "KmsKeyId" not in call_args  # Should not specify for default key
    
    def test_create_secret_with_custom_kms_key(self):
        """Test creating a secret with custom KMS key."""
        mock_client = Mock()
        mock_client.create_secret.return_value = {
            "ARN": "arn:aws:secretsmanager:us-east-1:123456789:secret:zscaler-creds",
            "Name": "zscaler-creds",
            "VersionId": "v1-abc123"
        }
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        sm = SecretsManager(session=mock_session)
        result = sm.create_or_use_secret(
            secret_name="zscaler-creds",
            username="admin@example.com",
            password="secret123",
            api_key="api-key-123",
            cloud="zscaler",
            kms_key_id="arn:aws:kms:us-east-1:123456789:key/12345678-1234-1234-1234-123456789012"
        )
        
        assert result.kms_key_id == "arn:aws:kms:us-east-1:123456789:key/12345678-1234-1234-1234-123456789012"
        
        # Verify KMS key was passed
        call_args = mock_client.create_secret.call_args[1]
        assert call_args["KmsKeyId"] == "arn:aws:kms:us-east-1:123456789:key/12345678-1234-1234-1234-123456789012"
    
    def test_create_secret_with_description(self):
        """Test creating a secret with custom description."""
        mock_client = Mock()
        mock_client.create_secret.return_value = {
            "ARN": "arn:aws:secretsmanager:us-east-1:123456789:secret:zscaler-creds",
            "Name": "zscaler-creds",
            "VersionId": "v1-abc123"
        }
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        sm = SecretsManager(session=mock_session)
        sm.create_or_use_secret(
            secret_name="zscaler-creds",
            username="admin@example.com",
            password="secret123",
            api_key="api-key-123",
            cloud="zscaler",
            description="My custom description"
        )
        
        call_args = mock_client.create_secret.call_args[1]
        assert call_args["Description"] == "My custom description"
    
    def test_create_secret_with_tags(self):
        """Test creating a secret with tags."""
        mock_client = Mock()
        mock_client.create_secret.return_value = {
            "ARN": "arn:aws:secretsmanager:us-east-1:123456789:secret:zscaler-creds",
            "Name": "zscaler-creds",
            "VersionId": "v1-abc123"
        }
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        tags = [
            {"Key": "Environment", "Value": "Production"},
            {"Key": "Project", "Value": "ZscalerMCP"}
        ]
        
        sm = SecretsManager(session=mock_session)
        sm.create_or_use_secret(
            secret_name="zscaler-creds",
            username="admin@example.com",
            password="secret123",
            api_key="api-key-123",
            cloud="zscaler",
            tags=tags
        )
        
        call_args = mock_client.create_secret.call_args[1]
        assert call_args["Tags"] == tags
    
    def test_handle_existing_secret(self):
        """Test handling when secret already exists."""
        mock_client = Mock()
        
        # First call raises ResourceExistsException
        error_response = {
            "Error": {
                "Code": "ResourceExistsException",
                "Message": "A resource with the requested name already exists"
            }
        }
        mock_client.create_secret.side_effect = ClientError(error_response, "CreateSecret")
        
        # describe_secret returns existing secret
        mock_client.describe_secret.return_value = {
            "ARN": "arn:aws:secretsmanager:us-east-1:123456789:secret:zscaler-creds-Existing",
            "Name": "zscaler-creds",
            "CreatedDate": "2024-01-01T00:00:00Z"
        }
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        sm = SecretsManager(session=mock_session)
        result = sm.create_or_use_secret(
            secret_name="zscaler-creds",
            username="admin@example.com",
            password="secret123",
            api_key="api-key-123",
            cloud="zscaler"
        )
        
        # Verify result indicates existing secret
        assert result.arn == "arn:aws:secretsmanager:us-east-1:123456789:secret:zscaler-creds-Existing"
        assert result.name == "zscaler-creds"
        assert result.created is False
        assert result.version_id is None  # Not retrieved for existing secrets
        assert result.kms_key_id == SecretsManager.DEFAULT_KMS_KEY
        
        # Verify describe_secret was called
        mock_client.describe_secret.assert_called_once_with(SecretId="zscaler-creds")
    
    def test_handle_create_secret_other_error(self):
        """Test handling of other ClientErrors during create."""
        mock_client = Mock()
        
        error_response = {
            "Error": {
                "Code": "AccessDeniedException",
                "Message": "User is not authorized to perform operation"
            }
        }
        mock_client.create_secret.side_effect = ClientError(error_response, "CreateSecret")
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        sm = SecretsManager(session=mock_session)
        
        with pytest.raises(SecretsManagerError) as exc_info:
            sm.create_or_use_secret(
                secret_name="zscaler-creds",
                username="admin@example.com",
                password="secret123",
                api_key="api-key-123",
                cloud="zscaler"
            )
        
        assert "S02-001-AccessDeniedException" in str(exc_info.value.error_code)
        assert "zscaler-creds" in str(exc_info.value.context["secret_name"])
    
    def test_handle_describe_secret_error(self):
        """Test handling error when describing existing secret."""
        mock_client = Mock()
        
        # First call raises ResourceExistsException
        error_response = {
            "Error": {
                "Code": "ResourceExistsException",
                "Message": "A resource with the requested name already exists"
            }
        }
        mock_client.create_secret.side_effect = ClientError(error_response, "CreateSecret")
        
        # describe_secret also fails
        describe_error = {
            "Error": {
                "Code": "InternalServiceError",
                "Message": "Internal server error"
            }
        }
        mock_client.describe_secret.side_effect = ClientError(describe_error, "DescribeSecret")
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        sm = SecretsManager(session=mock_session)
        
        with pytest.raises(SecretsManagerError) as exc_info:
            sm.create_or_use_secret(
                secret_name="zscaler-creds",
                username="admin@example.com",
                password="secret123",
                api_key="api-key-123",
                cloud="zscaler"
            )
        
        assert "S02-001-InternalServiceError" in str(exc_info.value.error_code)


class TestGetSecretValue:
    """Tests for get_secret_value method."""
    
    def test_get_secret_value_success(self):
        """Test retrieving and parsing secret value."""
        mock_client = Mock()
        mock_client.get_secret_value.return_value = {
            "ARN": "arn:aws:secretsmanager:us-east-1:123456789:secret:zscaler-creds",
            "Name": "zscaler-creds",
            "SecretString": json.dumps({
                "username": "admin@example.com",
                "password": "secret123",
                "api_key": "api-key-123",
                "cloud": "zscaler"
            }),
            "VersionId": "v1-abc123"
        }
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        sm = SecretsManager(session=mock_session)
        value = sm.get_secret_value("zscaler-creds")
        
        assert value["username"] == "admin@example.com"
        assert value["password"] == "secret123"
        assert value["api_key"] == "api-key-123"
        assert value["cloud"] == "zscaler"
    
    def test_get_secret_value_binary_error(self):
        """Test error handling for binary secrets."""
        mock_client = Mock()
        mock_client.get_secret_value.return_value = {
            "ARN": "arn:aws:secretsmanager:us-east-1:123456789:secret:binary-secret",
            "Name": "binary-secret",
            "SecretBinary": b"binary-data"  # No SecretString
        }
        
        mock_session = Mock()
        mock_session
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        sm = SecretsManager(session=mock_session)
        
        with pytest.raises(SecretsManagerError) as exc_info:
            sm.get_secret_value("binary-secret")
        
        assert "S02-001-BinarySecret" in str(exc_info.value.error_code)
    
    def test_get_secret_value_json_error(self):
        """Test error handling for invalid JSON."""
        mock_client = Mock()
        mock_client.get_secret_value.return_value = {
            "ARN": "arn:aws:secretsmanager:us-east-1:123456789:secret:invalid-secret",
            "Name": "invalid-secret",
            "SecretString": "not-valid-json"
        }
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        sm = SecretsManager(session=mock_session)
        
        with pytest.raises(SecretsManagerError) as exc_info:
            sm.get_secret_value("invalid-secret")
        
        assert "S02-001-JSONError" in str(exc_info.value.error_code)
    
    def test_get_secret_value_client_error(self):
        """Test error handling for AWS client errors."""
        mock_client = Mock()
        error_response = {
            "Error": {
                "Code": "ResourceNotFoundException",
                "Message": "Secret not found"
            }
        }
        mock_client.get_secret_value.side_effect = ClientError(error_response, "GetSecretValue")
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        sm = SecretsManager(session=mock_session)
        
        with pytest.raises(SecretsManagerError) as exc_info:
            sm.get_secret_value("nonexistent-secret")
        
        assert "S02-001-ResourceNotFoundException" in str(exc_info.value.error_code)


class TestDeleteSecret:
    """Tests for delete_secret method."""
    
    def test_delete_secret_with_recovery_window(self):
        """Test deleting secret with recovery window."""
        mock_client = Mock()
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        sm = SecretsManager(session=mock_session)
        sm.delete_secret("zscaler-creds", recovery_window_in_days=7)
        
        mock_client.delete_secret.assert_called_once_with(
            SecretId="zscaler-creds",
            RecoveryWindowInDays=7
        )
    
    def test_delete_secret_force_delete(self):
        """Test force deleting secret without recovery."""
        mock_client = Mock()
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        sm = SecretsManager(session=mock_session)
        sm.delete_secret("zscaler-creds", force_delete_without_recovery=True)
        
        mock_client.delete_secret.assert_called_once_with(
            SecretId="zscaler-creds",
            ForceDeleteWithoutRecovery=True
        )
    
    def test_delete_secret_default_recovery(self):
        """Test deleting secret with default recovery window."""
        mock_client = Mock()
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        sm = SecretsManager(session=mock_session)
        sm.delete_secret("zscaler-creds")
        
        # Should not pass recovery window or force delete
        mock_client.delete_secret.assert_called_once_with(SecretId="zscaler-creds")
    
    def test_delete_secret_error(self):
        """Test error handling during secret deletion."""
        mock_client = Mock()
        error_response = {
            "Error": {
                "Code": "AccessDeniedException",
                "Message": "Not authorized to delete secret"
            }
        }
        mock_client.delete_secret.side_effect = ClientError(error_response, "DeleteSecret")
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        sm = SecretsManager(session=mock_session)
        
        with pytest.raises(SecretsManagerError) as exc_info:
            sm.delete_secret("zscaler-creds")
        
        assert "S02-001-AccessDeniedException" in str(exc_info.value.error_code)


class TestSecretsManagerError:
    """Tests for SecretsManagerError exception."""
    
    def test_error_default_code(self):
        """Test error with default error code."""
        error = SecretsManagerError("Test error message")
        assert error.message == "Test error message"
        assert error.error_code == "S02-001"
        assert error.category.value == "aws_permissions"
        assert error.severity.value == "error"
    
    def test_error_custom_code(self):
        """Test error with custom error code."""
        error = SecretsManagerError(
            "Test error message",
            error_code="S02-001-Custom"
        )
        assert error.error_code == "S02-001-Custom"
    
    def test_error_with_context(self):
        """Test error with context."""
        context = {"secret_name": "test-secret", "region": "us-east-1"}
        error = SecretsManagerError(
            "Test error message",
            context=context
        )
        assert error.context == context
    
    def test_error_to_error_message(self):
        """Test converting error to ErrorMessage."""
        error = SecretsManagerError(
            "Test error message",
            error_code="S02-001",
            context={"secret_name": "test"}
        )
        
        msg = error.to_error_message()
        assert msg.category.value == "aws_permissions"
        assert msg.severity.value == "error"
        assert msg.error_code == "S02-001"
