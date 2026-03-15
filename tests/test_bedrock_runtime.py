"""Tests for Bedrock Runtime module."""

import pytest
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError

from zscaler_mcp_deploy.aws.bedrock_runtime import (
    BedrockRuntime,
    BedrockRuntimeError,
)
from zscaler_mcp_deploy.errors import BedrockRuntimePollingError
from zscaler_mcp_deploy.models import RuntimeConfig, RuntimeResult


class TestRuntimeResult:
    """Tests for RuntimeResult dataclass."""
    
    def test_runtime_result_creation(self):
        """Test creating a RuntimeResult with all fields."""
        result = RuntimeResult(
            runtime_id="abc123def456",
            runtime_arn="arn:aws:bedrock:us-east-1:123456789:runtime/abc123def456",
            status="READY",
            created=True,
            error_code=None,
            error_message=None,
            endpoint_url="https://runtime.bedrock.aws/abc123def456",
            created_at="2024-01-15T10:30:00Z"
        )
        
        assert result.runtime_id == "abc123def456"
        assert result.runtime_arn == "arn:aws:bedrock:us-east-1:123456789:runtime/abc123def456"
        assert result.status == "READY"
        assert result.created is True
        assert result.error_code is None
        assert result.error_message is None
        assert result.endpoint_url == "https://runtime.bedrock.aws/abc123def456"
        assert result.created_at == "2024-01-15T10:30:00Z"
    
    def test_runtime_result_defaults(self):
        """Test RuntimeResult with default values."""
        result = RuntimeResult(
            runtime_id="abc123",
            runtime_arn="arn:aws:bedrock:us-east-1:123:runtime/abc123",
            status="CREATING"
        )
        
        assert result.created is True
        assert result.error_code is None
        assert result.error_message is None
        assert result.endpoint_url is None
        assert result.created_at is None
    
    def test_runtime_result_to_dict(self):
        """Test converting RuntimeResult to dictionary."""
        result = RuntimeResult(
            runtime_id="abc123",
            runtime_arn="arn:aws:bedrock:us-east-1:123:runtime/abc123",
            status="READY",
            created=True,
            endpoint_url="https://runtime.bedrock.aws/abc123"
        )
        
        d = result.to_dict()
        assert d["runtime_id"] == "abc123"
        assert d["runtime_arn"] == "arn:aws:bedrock:us-east-1:123:runtime/abc123"
        assert d["status"] == "READY"
        assert d["created"] is True
        assert d["endpoint_url"] == "https://runtime.bedrock.aws/abc123"


class TestRuntimeConfig:
    """Tests for RuntimeConfig dataclass."""
    
    def test_runtime_config_creation(self):
        """Test creating a RuntimeConfig with all fields."""
        config = RuntimeConfig(
            runtime_name="zscaler-mcp-runtime",
            secret_arn="arn:aws:secretsmanager:us-east-1:123:secret:zscaler-creds",
            role_arn="arn:aws:iam::123:role/zscaler-bedrock-role",
            image_uri="public.ecr.aws/zscaler/mcp-server:latest",
            enable_write_tools=True,
            region="us-west-2",
            tags=[{"Key": "Env", "Value": "Prod"}]
        )
        
        assert config.runtime_name == "zscaler-mcp-runtime"
        assert config.secret_arn == "arn:aws:secretsmanager:us-east-1:123:secret:zscaler-creds"
        assert config.role_arn == "arn:aws:iam::123:role/zscaler-bedrock-role"
        assert config.image_uri == "public.ecr.aws/zscaler/mcp-server:latest"
        assert config.enable_write_tools is True
        assert config.region == "us-west-2"
        assert config.tags == [{"Key": "Env", "Value": "Prod"}]
    
    def test_runtime_config_defaults(self):
        """Test RuntimeConfig with default values."""
        config = RuntimeConfig(
            runtime_name="test-runtime",
            secret_arn="arn:aws:secretsmanager:us-east-1:123:secret:test",
            role_arn="arn:aws:iam::123:role/test-role",
            image_uri="public.ecr.aws/test/image:latest"
        )
        
        assert config.enable_write_tools is False
        assert config.region is None
        assert config.tags is None
    
    def test_runtime_config_to_dict(self):
        """Test converting RuntimeConfig to dictionary."""
        config = RuntimeConfig(
            runtime_name="test-runtime",
            secret_arn="arn:aws:secretsmanager:us-east-1:123:secret:test",
            role_arn="arn:aws:iam::123:role/test-role",
            image_uri="public.ecr.aws/test/image:latest",
            enable_write_tools=True
        )
        
        d = config.to_dict()
        assert d["runtime_name"] == "test-runtime"
        assert d["enable_write_tools"] is True


class TestBedrockRuntimeInitialization:
    """Tests for BedrockRuntime initialization."""
    
    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        rt = BedrockRuntime()
        assert rt._region is None
        assert rt._profile_name is None
        assert rt._session is None
        assert rt._client is None
    
    def test_init_with_region(self):
        """Test initialization with region parameter."""
        rt = BedrockRuntime(region="us-west-2")
        assert rt._region == "us-west-2"
        assert rt._profile_name is None
    
    def test_init_with_profile(self):
        """Test initialization with profile name."""
        rt = BedrockRuntime(profile_name="my-profile")
        assert rt._profile_name == "my-profile"
        assert rt._region is None
    
    def test_init_with_session(self):
        """Test initialization with pre-configured session."""
        mock_session = Mock()
        rt = BedrockRuntime(session=mock_session)
        assert rt._session is mock_session
    
    @patch("zscaler_mcp_deploy.aws.bedrock_runtime.boto3.Session")
    def test_lazy_session_creation_no_profile(self, mock_session_class):
        """Test lazy session creation without profile."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        rt = BedrockRuntime(region="us-east-1")
        session = rt.session
        
        mock_session_class.assert_called_once_with(region_name="us-east-1")
        assert session is mock_session
    
    @patch("zscaler_mcp_deploy.aws.bedrock_runtime.boto3.Session")
    def test_lazy_session_creation_with_profile(self, mock_session_class):
        """Test lazy session creation with profile."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        rt = BedrockRuntime(region="us-east-1", profile_name="my-profile")
        session = rt.session
        
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
        
        rt = BedrockRuntime(session=mock_session)
        client = rt._bedrock_client
        
        mock_session.client.assert_called_once_with("bedrock-agent")
        assert client is mock_client
    
    def test_session_caching(self):
        """Test that session is cached after first access."""
        mock_session = Mock()
        rt = BedrockRuntime(session=mock_session)
        
        s1 = rt.session
        s2 = rt.session
        
        assert s1 is s2 is mock_session
    
    def test_client_caching(self):
        """Test that client is cached after first access."""
        mock_session = Mock()
        mock_client = Mock()
        mock_session.client.return_value = mock_client
        
        rt = BedrockRuntime(session=mock_session)
        
        c1 = rt._bedrock_client
        c2 = rt._bedrock_client
        
        assert c1 is c2 is mock_client
        mock_session.client.assert_called_once_with("bedrock-agent")
    
    def test_default_image_uri(self):
        """Test that default image URI is set."""
        rt = BedrockRuntime()
        assert rt.DEFAULT_IMAGE_URI == "public.ecr.aws/zscaler/mcp-server-zscaler:latest"
    
    def test_default_transport(self):
        """Test that default transport is stdio."""
        rt = BedrockRuntime()
        assert rt.DEFAULT_TRANSPORT == "stdio"


class TestExtractSecretName:
    """Tests for _extract_secret_name helper method."""
    
    def test_extract_from_full_arn(self):
        """Test extracting secret name from full ARN."""
        rt = BedrockRuntime()
        arn = "arn:aws:secretsmanager:us-east-1:123456789:secret:zscaler-creds-AbCdEf"
        result = rt._extract_secret_name(arn)
        assert result == "zscaler-creds"
    
    def test_extract_from_arn_without_suffix(self):
        """Test extracting from ARN without suffix."""
        rt = BedrockRuntime()
        arn = "arn:aws:secretsmanager:us-east-1:123456789:secret:my-secret-name"
        result = rt._extract_secret_name(arn)
        # "name" is 4 chars, not the AWS 6-char suffix, so full name returned
        assert result == "my-secret-name"
    
    def test_extract_from_plain_name(self):
        """Test extracting from plain name (no ARN format)."""
        rt = BedrockRuntime()
        name = "just-a-name"
        result = rt._extract_secret_name(name)
        assert result == "just-a-name"
    
    def test_extract_with_hyphens_in_name(self):
        """Test extracting when secret name contains hyphens."""
        rt = BedrockRuntime()
        arn = "arn:aws:secretsmanager:us-east-1:123:secret:my-app-secret-AbCdEf"
        result = rt._extract_secret_name(arn)
        assert result == "my-app-secret"
    
    def test_extract_with_numbers_in_suffix(self):
        """Test extracting when suffix contains numbers."""
        rt = BedrockRuntime()
        arn = "arn:aws:secretsmanager:us-east-1:123:secret:test-secret-a1B2c3"
        result = rt._extract_secret_name(arn)
        assert result == "test-secret"


class TestBuildEnvironmentVariables:
    """Tests for _build_environment_variables helper method."""
    
    def test_basic_env_vars(self):
        """Test building basic environment variables."""
        rt = BedrockRuntime()
        secret_arn = "arn:aws:secretsmanager:us-east-1:123:secret:zscaler-creds-AbCdEf"
        
        env_vars = rt._build_environment_variables(secret_arn)
        
        assert env_vars["ZSCALER_SECRET_NAME"] == "zscaler-creds"
        assert env_vars["TRANSPORT"] == "stdio"
        assert "ENABLE_WRITE_TOOLS" not in env_vars
    
    def test_env_vars_with_write_tools_enabled(self):
        """Test building env vars with write tools enabled."""
        rt = BedrockRuntime()
        secret_arn = "arn:aws:secretsmanager:us-east-1:123:secret:zscaler-creds-AbCdEf"
        
        env_vars = rt._build_environment_variables(secret_arn, enable_write_tools=True)
        
        assert env_vars["ZSCALER_SECRET_NAME"] == "zscaler-creds"
        assert env_vars["TRANSPORT"] == "stdio"
        assert env_vars["ENABLE_WRITE_TOOLS"] == "true"
    
    def test_env_vars_with_write_tools_disabled(self):
        """Test building env vars with write tools explicitly disabled."""
        rt = BedrockRuntime()
        secret_arn = "arn:aws:secretsmanager:us-east-1:123:secret:test-secret-AbCdEf"
        
        env_vars = rt._build_environment_variables(secret_arn, enable_write_tools=False)
        
        assert env_vars["ZSCALER_SECRET_NAME"] == "test-secret"
        assert "ENABLE_WRITE_TOOLS" not in env_vars


class TestBuildNetworkConfiguration:
    """Tests for _build_network_configuration helper method."""
    
    def test_network_config_structure(self):
        """Test network configuration structure."""
        rt = BedrockRuntime()
        config = rt._build_network_configuration()
        
        assert "vpcConfiguration" in config
        assert config["vpcConfiguration"]["subnetIds"] == []
        assert config["vpcConfiguration"]["securityGroupIds"] == []


class TestCreateRuntime:
    """Tests for create_runtime method."""
    
    def test_create_runtime_success(self):
        """Test successful runtime creation."""
        mock_client = Mock()
        mock_client.create_agent_runtime.return_value = {
            "runtimeId": "abc123def456",
            "runtimeArn": "arn:aws:bedrock:us-east-1:123456789:runtime/abc123def456",
            "status": "CREATING",
            "createdAt": "2024-01-15T10:30:00Z"
        }
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        rt = BedrockRuntime(session=mock_session)
        result = rt.create_runtime(
            runtime_name="zscaler-mcp-runtime",
            secret_arn="arn:aws:secretsmanager:us-east-1:123:secret:zscaler-creds-AbCdEf",
            role_arn="arn:aws:iam::123:role/zscaler-bedrock-role"
        )
        
        assert result.runtime_id == "abc123def456"
        assert result.runtime_arn == "arn:aws:bedrock:us-east-1:123456789:runtime/abc123def456"
        assert result.status == "CREATING"
        assert result.created is True
        assert result.created_at == "2024-01-15T10:30:00Z"
        
        # Verify the API call
        call_args = mock_client.create_agent_runtime.call_args[1]
        assert call_args["runtimeName"] == "zscaler-mcp-runtime"
        assert call_args["agentRuntimeConfiguration"]["containerConfiguration"]["imageUri"] == rt.DEFAULT_IMAGE_URI
        assert call_args["agentRuntimeConfiguration"]["containerConfiguration"]["executionRoleArn"] == "arn:aws:iam::123:role/zscaler-bedrock-role"
    
    def test_create_runtime_with_custom_image(self):
        """Test runtime creation with custom image URI."""
        mock_client = Mock()
        mock_client.create_agent_runtime.return_value = {
            "runtimeId": "abc123",
            "runtimeArn": "arn:aws:bedrock:us-east-1:123:runtime/abc123",
            "status": "CREATING"
        }
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        rt = BedrockRuntime(session=mock_session)
        result = rt.create_runtime(
            runtime_name="test-runtime",
            secret_arn="arn:aws:secretsmanager:us-east-1:123:secret:test-AbCdEf",
            role_arn="arn:aws:iam::123:role/test-role",
            image_uri="custom.ecr.aws/my-image:tag"
        )
        
        assert result.runtime_id == "abc123"
        
        call_args = mock_client.create_agent_runtime.call_args[1]
        assert call_args["agentRuntimeConfiguration"]["containerConfiguration"]["imageUri"] == "custom.ecr.aws/my-image:tag"
    
    def test_create_runtime_with_write_tools(self):
        """Test runtime creation with write tools enabled."""
        mock_client = Mock()
        mock_client.create_agent_runtime.return_value = {
            "runtimeId": "abc123",
            "runtimeArn": "arn:aws:bedrock:us-east-1:123:runtime/abc123",
            "status": "CREATING"
        }
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        rt = BedrockRuntime(session=mock_session)
        result = rt.create_runtime(
            runtime_name="test-runtime",
            secret_arn="arn:aws:secretsmanager:us-east-1:123:secret:zscaler-creds-AbCdEf",
            role_arn="arn:aws:iam::123:role/test-role",
            enable_write_tools=True
        )
        
        assert result.status == "CREATING"
        
        call_args = mock_client.create_agent_runtime.call_args[1]
        env_vars = call_args["agentRuntimeConfiguration"]["containerConfiguration"]["environmentVariables"]
        assert env_vars["ZSCALER_SECRET_NAME"] == "zscaler-creds"
        assert env_vars["TRANSPORT"] == "stdio"
        assert env_vars["ENABLE_WRITE_TOOLS"] == "true"
    
    def test_create_runtime_with_tags(self):
        """Test runtime creation with tags."""
        mock_client = Mock()
        mock_client.create_agent_runtime.return_value = {
            "runtimeId": "abc123",
            "runtimeArn": "arn:aws:bedrock:us-east-1:123:runtime/abc123",
            "status": "CREATING"
        }
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        tags = [
            {"Key": "Environment", "Value": "Production"},
            {"Key": "Project", "Value": "ZscalerMCP"}
        ]
        
        rt = BedrockRuntime(session=mock_session)
        result = rt.create_runtime(
            runtime_name="test-runtime",
            secret_arn="arn:aws:secretsmanager:us-east-1:123:secret:test-AbCdEf",
            role_arn="arn:aws:iam::123:role/test-role",
            tags=tags
        )
        
        call_args = mock_client.create_agent_runtime.call_args[1]
        assert call_args["tags"] == tags
    
    def test_create_runtime_error(self):
        """Test error handling during runtime creation."""
        mock_client = Mock()
        error_response = {
            "Error": {
                "Code": "AccessDeniedException",
                "Message": "User is not authorized to perform operation"
            }
        }
        mock_client.create_agent_runtime.side_effect = ClientError(error_response, "CreateAgentRuntime")
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        rt = BedrockRuntime(session=mock_session)
        
        with pytest.raises(BedrockRuntimeError) as exc_info:
            rt.create_runtime(
                runtime_name="test-runtime",
                secret_arn="arn:aws:secretsmanager:us-east-1:123:secret:test-AbCdEf",
                role_arn="arn:aws:iam::123:role/test-role"
            )
        
        assert "S03-001-AccessDeniedException" in str(exc_info.value.error_code)
        assert "test-runtime" in str(exc_info.value.context["runtime_name"])
    
    def test_create_runtime_already_exists(self):
        """Test handling when runtime already exists."""
        mock_client = Mock()
        error_response = {
            "Error": {
                "Code": "ConflictException",
                "Message": "Runtime with name 'test-runtime' already exists"
            }
        }
        mock_client.create_agent_runtime.side_effect = ClientError(error_response, "CreateAgentRuntime")
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        rt = BedrockRuntime(session=mock_session)
        
        with pytest.raises(BedrockRuntimeError) as exc_info:
            rt.create_runtime(
                runtime_name="test-runtime",
                secret_arn="arn:aws:secretsmanager:us-east-1:123:secret:test-AbCdEf",
                role_arn="arn:aws:iam::123:role/test-role"
            )
        
        assert "S03-001-ConflictException" in str(exc_info.value.error_code)


class TestGetRuntime:
    """Tests for get_runtime method."""
    
    def test_get_runtime_success(self):
        """Test successful runtime retrieval."""
        mock_client = Mock()
        mock_client.get_agent_runtime.return_value = {
            "runtimeId": "abc123",
            "runtimeArn": "arn:aws:bedrock:us-east-1:123:runtime/abc123",
            "status": "READY",
            "endpointUrl": "https://runtime.bedrock.aws/abc123",
            "createdAt": "2024-01-15T10:30:00Z"
        }
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        rt = BedrockRuntime(session=mock_session)
        result = rt.get_runtime("abc123")
        
        assert result.runtime_id == "abc123"
        assert result.runtime_arn == "arn:aws:bedrock:us-east-1:123:runtime/abc123"
        assert result.status == "READY"
        assert result.created is False  # Existing runtime
        assert result.endpoint_url == "https://runtime.bedrock.aws/abc123"
        assert result.created_at == "2024-01-15T10:30:00Z"
        
        mock_client.get_agent_runtime.assert_called_once_with(runtimeId="abc123")
    
    def test_get_runtime_not_found(self):
        """Test handling when runtime not found."""
        mock_client = Mock()
        error_response = {
            "Error": {
                "Code": "ResourceNotFoundException",
                "Message": "Runtime not found"
            }
        }
        mock_client.get_agent_runtime.side_effect = ClientError(error_response, "GetAgentRuntime")
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        rt = BedrockRuntime(session=mock_session)
        
        with pytest.raises(BedrockRuntimeError) as exc_info:
            rt.get_runtime("nonexistent")
        
        assert "S03-001-ResourceNotFoundException" in str(exc_info.value.error_code)
        assert "nonexistent" in str(exc_info.value.context["runtime_id"])


class TestDeleteRuntime:
    """Tests for delete_runtime method."""
    
    def test_delete_runtime_success(self):
        """Test successful runtime deletion."""
        mock_client = Mock()
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        rt = BedrockRuntime(session=mock_session)
        rt.delete_runtime("abc123")
        
        mock_client.delete_agent_runtime.assert_called_once_with(runtimeId="abc123")
    
    def test_delete_runtime_error(self):
        """Test error handling during runtime deletion."""
        mock_client = Mock()
        error_response = {
            "Error": {
                "Code": "AccessDeniedException",
                "Message": "Not authorized to delete runtime"
            }
        }
        mock_client.delete_agent_runtime.side_effect = ClientError(error_response, "DeleteAgentRuntime")
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        rt = BedrockRuntime(session=mock_session)
        
        with pytest.raises(BedrockRuntimeError) as exc_info:
            rt.delete_runtime("abc123")
        
        assert "S03-001-AccessDeniedException" in str(exc_info.value.error_code)


class TestBedrockRuntimeError:
    """Tests for BedrockRuntimeError exception."""
    
    def test_error_default_code(self):
        """Test error with default error code."""
        error = BedrockRuntimeError("Test error message")
        assert error.message == "Test error message"
        assert error.error_code == "S03-001"
        assert error.category.value == "aws_permissions"
        assert error.severity.value == "error"
    
    def test_error_custom_code(self):
        """Test error with custom error code."""
        error = BedrockRuntimeError(
            "Test error message",
            error_code="S03-001-Custom"
        )
        assert error.error_code == "S03-001-Custom"
    
    def test_error_with_context(self):
        """Test error with context."""
        context = {"runtime_name": "test-runtime", "region": "us-east-1"}
        error = BedrockRuntimeError(
            "Test error message",
            context=context
        )
        assert error.context == context
    
    def test_error_to_error_message(self):
        """Test converting error to ErrorMessage."""
        error = BedrockRuntimeError(
            "Test error message",
            error_code="S03-001",
            context={"runtime_name": "test"}
        )
        
        msg = error.to_error_message()
        assert msg.category.value == "aws_permissions"
        assert msg.severity.value == "error"
        assert msg.error_code == "S03-001"


class TestGetRuntimeStatus:
    """Tests for get_runtime_status method."""
    
    def test_get_runtime_status_success(self):
        """Test successful status retrieval."""
        mock_client = Mock()
        mock_client.get_agent_runtime.return_value = {
            "runtimeId": "abc123",
            "status": "READY"
        }
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        rt = BedrockRuntime(session=mock_session)
        status = rt.get_runtime_status("abc123")
        
        assert status == "READY"
        mock_client.get_agent_runtime.assert_called_once_with(runtimeId="abc123")
    
    def test_get_runtime_status_creating(self):
        """Test status retrieval for CREATING state."""
        mock_client = Mock()
        mock_client.get_agent_runtime.return_value = {
            "runtimeId": "abc123",
            "status": "CREATING"
        }
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        rt = BedrockRuntime(session=mock_session)
        status = rt.get_runtime_status("abc123")
        
        assert status == "CREATING"
    
    def test_get_runtime_status_error(self):
        """Test error handling during status retrieval."""
        mock_client = Mock()
        error_response = {
            "Error": {
                "Code": "ResourceNotFoundException",
                "Message": "Runtime not found"
            }
        }
        mock_client.get_agent_runtime.side_effect = ClientError(error_response, "GetAgentRuntime")
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        rt = BedrockRuntime(session=mock_session)
        
        with pytest.raises(BedrockRuntimePollingError) as exc_info:
            rt.get_runtime_status("nonexistent")
        
        assert "S03-002-ResourceNotFoundException" in str(exc_info.value.error_code)


class TestPollRuntimeStatus:
    """Tests for poll_runtime_status method."""
    
    def test_poll_runtime_status_ready(self):
        """Test polling until runtime reaches READY status."""
        mock_client = Mock()
        # First two calls return CREATING, third returns READY
        mock_client.get_agent_runtime.side_effect = [
            {
                "runtimeId": "abc123",
                "runtimeArn": "arn:aws:bedrock:us-east-1:123:runtime/abc123",
                "status": "CREATING",
                "createdAt": "2024-01-15T10:30:00Z"
            },
            {
                "runtimeId": "abc123",
                "runtimeArn": "arn:aws:bedrock:us-east-1:123:runtime/abc123",
                "status": "CREATING",
                "createdAt": "2024-01-15T10:30:00Z"
            },
            {
                "runtimeId": "abc123",
                "runtimeArn": "arn:aws:bedrock:us-east-1:123:runtime/abc123",
                "status": "READY",
                "endpointUrl": "https://runtime.bedrock.aws/abc123",
                "createdAt": "2024-01-15T10:30:00Z"
            },
        ]
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        rt = BedrockRuntime(session=mock_session)
        result = rt.poll_runtime_status(
            runtime_id="abc123",
            timeout_seconds=60,
            initial_interval=0.01,  # Fast polling for tests
        )
        
        assert result.status == "READY"
        assert result.runtime_id == "abc123"
        assert result.endpoint_url == "https://runtime.bedrock.aws/abc123"
        assert mock_client.get_agent_runtime.call_count == 3
    
    def test_poll_runtime_status_failed(self):
        """Test polling when runtime reaches CREATE_FAILED status."""
        mock_client = Mock()
        mock_client.get_agent_runtime.side_effect = [
            {
                "runtimeId": "abc123",
                "runtimeArn": "arn:aws:bedrock:us-east-1:123:runtime/abc123",
                "status": "CREATING",
                "createdAt": "2024-01-15T10:30:00Z"
            },
            {
                "runtimeId": "abc123",
                "runtimeArn": "arn:aws:bedrock:us-east-1:123:runtime/abc123",
                "status": "CREATE_FAILED",
                "errorCode": "ContainerImageNotFound",
                "errorMessage": "Container image not found in ECR",
                "createdAt": "2024-01-15T10:30:00Z"
            },
        ]
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        rt = BedrockRuntime(session=mock_session)
        
        with pytest.raises(BedrockRuntimeError) as exc_info:
            rt.poll_runtime_status(
                runtime_id="abc123",
                timeout_seconds=60,
                initial_interval=0.01,
            )
        
        assert "S03-002-CreateFailed" in str(exc_info.value.error_code)
        assert "Container image not found in ECR" in str(exc_info.value.message)
        assert exc_info.value.context["runtime_id"] == "abc123"
        assert exc_info.value.context["aws_error_code"] == "ContainerImageNotFound"
    
    def test_poll_runtime_status_timeout(self):
        """Test polling timeout when runtime never reaches READY."""
        mock_client = Mock()
        # Always return CREATING status
        mock_client.get_agent_runtime.return_value = {
            "runtimeId": "abc123",
            "runtimeArn": "arn:aws:bedrock:us-east-1:123:runtime/abc123",
            "status": "CREATING",
            "createdAt": "2024-01-15T10:30:00Z"
        }
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        rt = BedrockRuntime(session=mock_session)
        
        with pytest.raises(BedrockRuntimePollingError) as exc_info:
            rt.poll_runtime_status(
                runtime_id="abc123",
                timeout_seconds=0.5,  # Short timeout for tests
                initial_interval=0.1,
            )
        
        assert "S03-002-Timeout" in str(exc_info.value.error_code)
        assert "abc123" in str(exc_info.value.message)
        assert "0.5 seconds" in str(exc_info.value.message)
        assert exc_info.value.context["timeout_seconds"] == 0.5
        assert exc_info.value.context["runtime_id"] == "abc123"
    
    def test_poll_runtime_status_immediate_ready(self):
        """Test polling when runtime is already READY."""
        mock_client = Mock()
        mock_client.get_agent_runtime.return_value = {
            "runtimeId": "abc123",
            "runtimeArn": "arn:aws:bedrock:us-east-1:123:runtime/abc123",
            "status": "READY",
            "endpointUrl": "https://runtime.bedrock.aws/abc123",
            "createdAt": "2024-01-15T10:30:00Z"
        }
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        rt = BedrockRuntime(session=mock_session)
        result = rt.poll_runtime_status(
            runtime_id="abc123",
            timeout_seconds=60,
            initial_interval=0.01,
        )
        
        assert result.status == "READY"
        assert mock_client.get_agent_runtime.call_count == 1


class TestWaitForReady:
    """Tests for wait_for_ready convenience method."""
    
    def test_wait_for_ready_success(self):
        """Test wait_for_ready success path."""
        mock_client = Mock()
        mock_client.get_agent_runtime.return_value = {
            "runtimeId": "abc123",
            "runtimeArn": "arn:aws:bedrock:us-east-1:123:runtime/abc123",
            "status": "READY",
            "endpointUrl": "https://runtime.bedrock.aws/abc123",
            "createdAt": "2024-01-15T10:30:00Z"
        }
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        rt = BedrockRuntime(session=mock_session)
        result = rt.wait_for_ready("abc123", timeout_seconds=30)
        
        assert result.status == "READY"
        assert result.endpoint_url == "https://runtime.bedrock.aws/abc123"
    
    def test_wait_for_ready_timeout(self):
        """Test wait_for_ready timeout."""
        mock_client = Mock()
        mock_client.get_agent_runtime.return_value = {
            "runtimeId": "abc123",
            "runtimeArn": "arn:aws:bedrock:us-east-1:123:runtime/abc123",
            "status": "CREATING",
            "createdAt": "2024-01-15T10:30:00Z"
        }
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        rt = BedrockRuntime(session=mock_session)
        
        with pytest.raises(BedrockRuntimePollingError) as exc_info:
            rt.wait_for_ready("abc123", timeout_seconds=0.5)
        
        assert "S03-002-Timeout" in str(exc_info.value.error_code)


class TestBedrockRuntimePollingError:
    """Tests for BedrockRuntimePollingError exception."""
    
    def test_polling_error_default_code(self):
        """Test polling error with default error code."""
        error = BedrockRuntimePollingError("Polling failed")
        assert error.message == "Polling failed"
        assert error.error_code == "S03-002"
        assert error.category.value == "aws_permissions"
    
    def test_polling_error_custom_code(self):
        """Test polling error with custom error code."""
        error = BedrockRuntimePollingError(
            "Polling failed",
            error_code="S03-002-Timeout"
        )
        assert error.error_code == "S03-002-Timeout"
    
    def test_polling_error_with_context(self):
        """Test polling error with context."""
        context = {
            "runtime_id": "abc123",
            "timeout_seconds": 600,
            "poll_count": 50
        }
        error = BedrockRuntimePollingError(
            "Timeout waiting for runtime",
            error_code="S03-002-Timeout",
            context=context
        )
        assert error.context == context
        assert error.context["timeout_seconds"] == 600
