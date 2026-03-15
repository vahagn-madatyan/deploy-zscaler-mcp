"""Unit tests for DeployOrchestrator."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from zscaler_mcp_deploy.deploy import DeployOrchestrator
from zscaler_mcp_deploy.models import (
    DeployConfig,
    DeployResult,
    BootstrapResult,
    RuntimeResult,
)
from zscaler_mcp_deploy.aws.bedrock_runtime import BedrockRuntimeError
from zscaler_mcp_deploy.errors import BedrockRuntimePollingError


class TestDeployOrchestrator:
    """Test suite for DeployOrchestrator."""
    
    @pytest.fixture
    def deploy_config(self):
        """Create a test deployment configuration."""
        return DeployConfig(
            runtime_name="test-runtime",
            secret_name="test-secret",
            role_name="test-role",
            username="test@example.com",
            password="test-password",
            api_key="12345678901234567890123456789012",
            cloud="zscaler",
            image_uri=None,
            enable_write_tools=False,
            region="us-east-1",
            profile_name=None,
            description="Test deployment",
            tags=None
        )
    
    @pytest.fixture
    def mock_bootstrap_result(self):
        """Create a successful bootstrap result."""
        return BootstrapResult(
            secret_arn="arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret-AbCdEf",
            role_arn="arn:aws:iam::123456789012:role/test-role",
            resource_ids=["test-secret", "test-role"],
            success=True,
            secret_created=True,
            role_created=True,
            phase="completed"
        )
    
    @pytest.fixture
    def mock_runtime_result(self):
        """Create a successful runtime creation result."""
        return RuntimeResult(
            runtime_id="test-runtime-id",
            runtime_arn="arn:aws:bedrock:us-east-1:123456789012:agent-runtime/test-runtime-id",
            status="CREATING",
            created=True,
            created_at=datetime.now().isoformat()
        )
    
    @pytest.fixture
    def mock_runtime_ready(self):
        """Create a READY runtime result."""
        return RuntimeResult(
            runtime_id="test-runtime-id",
            runtime_arn="arn:aws:bedrock:us-east-1:123456789012:agent-runtime/test-runtime-id",
            status="READY",
            created=True,
            endpoint_url="https://bedrock-runtime.us-east-1.amazonaws.com/test-runtime-id",
            created_at=datetime.now().isoformat()
        )
    
    @pytest.fixture
    def mock_bootstrap_orchestrator(self, mock_bootstrap_result):
        """Create a mock BootstrapOrchestrator."""
        mock = MagicMock()
        mock.bootstrap_resources.return_value = mock_bootstrap_result
        return mock
    
    @pytest.fixture
    def mock_bedrock_runtime(self, mock_runtime_result, mock_runtime_ready):
        """Create a mock BedrockRuntime."""
        mock = MagicMock()
        mock.create_runtime.return_value = mock_runtime_result
        mock.poll_runtime_status.return_value = mock_runtime_ready
        mock.delete_runtime.return_value = None
        return mock
    
    def test_deploy_orchestrator_success(
        self,
        deploy_config,
        mock_bootstrap_orchestrator,
        mock_bedrock_runtime,
        mock_bootstrap_result,
        mock_runtime_ready
    ):
        """Test successful deployment orchestration."""
        # Arrange
        orchestrator = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=mock_bootstrap_orchestrator,
            bedrock_runtime=mock_bedrock_runtime
        )
        
        # Act
        result = orchestrator.deploy(deploy_config)
        
        # Assert
        assert result.success is True
        assert result.runtime_id == "test-runtime-id"
        assert result.runtime_arn == "arn:aws:bedrock:us-east-1:123456789012:agent-runtime/test-runtime-id"
        assert result.status == "READY"
        assert result.endpoint_url == "https://bedrock-runtime.us-east-1.amazonaws.com/test-runtime-id"
        assert result.secret_arn == mock_bootstrap_result.secret_arn
        assert result.role_arn == mock_bootstrap_result.role_arn
        assert result.secret_created is True
        assert result.role_created is True
        assert result.runtime_created is True
        assert result.phase == "completed"
        assert result.bootstrap_result is not None
        
        # Verify bootstrap was called
        mock_bootstrap_orchestrator.bootstrap_resources.assert_called_once()
        
        # Verify runtime creation was called
        mock_bedrock_runtime.create_runtime.assert_called_once()
        create_call = mock_bedrock_runtime.create_runtime.call_args
        assert create_call.kwargs["runtime_name"] == "test-runtime"
        assert create_call.kwargs["secret_arn"] == mock_bootstrap_result.secret_arn
        assert create_call.kwargs["role_arn"] == mock_bootstrap_result.role_arn
        assert create_call.kwargs["enable_write_tools"] is False
        
        # Verify polling was called
        mock_bedrock_runtime.poll_runtime_status.assert_called_once_with(
            runtime_id="test-runtime-id",
            timeout_seconds=600
        )
    
    def test_deploy_orchestrator_bootstrap_failure(
        self,
        deploy_config,
        mock_bedrock_runtime
    ):
        """Test deployment when bootstrap fails."""
        # Arrange
        failed_bootstrap = BootstrapResult(
            success=False,
            error_message="Permission denied",
            error_code="S02-003-PreflightFailed",
            phase="preflight"
        )
        mock_bootstrap = MagicMock()
        mock_bootstrap.bootstrap_resources.return_value = failed_bootstrap
        
        orchestrator = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=mock_bootstrap,
            bedrock_runtime=mock_bedrock_runtime
        )
        
        # Act
        result = orchestrator.deploy(deploy_config)
        
        # Assert
        assert result.success is False
        assert result.error_code == "S02-003-PreflightFailed"
        assert result.error_message == "Permission denied"
        assert result.phase == "bootstrap"
        assert result.runtime_id is None
        
        # Verify bootstrap was called but runtime was not
        mock_bootstrap.bootstrap_resources.assert_called_once()
        mock_bedrock_runtime.create_runtime.assert_not_called()
    
    def test_deploy_orchestrator_runtime_create_failure(
        self,
        deploy_config,
        mock_bootstrap_orchestrator,
        mock_bootstrap_result
    ):
        """Test deployment when runtime creation fails."""
        # Arrange
        mock_runtime = MagicMock()
        mock_runtime.create_runtime.side_effect = BedrockRuntimeError(
            message="Access denied to Bedrock",
            error_code="S03-001-AccessDeniedException",
            context={"runtime_name": "test-runtime"}
        )
        
        orchestrator = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=mock_bootstrap_orchestrator,
            bedrock_runtime=mock_runtime
        )
        
        # Act
        result = orchestrator.deploy(deploy_config)
        
        # Assert
        assert result.success is False
        assert result.error_code == "S03-001-AccessDeniedException"
        assert "Access denied" in result.error_message
        assert result.phase == "runtime_create"
        assert result.secret_arn == mock_bootstrap_result.secret_arn
        assert result.role_arn == mock_bootstrap_result.role_arn
        assert result.secret_created is True
        assert result.role_created is True
        
        # Verify bootstrap and create were called
        mock_bootstrap_orchestrator.bootstrap_resources.assert_called_once()
        mock_runtime.create_runtime.assert_called_once()
    
    def test_deploy_orchestrator_polling_timeout_with_rollback(
        self,
        deploy_config,
        mock_bootstrap_orchestrator,
        mock_bootstrap_result,
        mock_runtime_result
    ):
        """Test deployment rollback on polling timeout."""
        # Arrange
        mock_runtime = MagicMock()
        mock_runtime.create_runtime.return_value = mock_runtime_result
        mock_runtime.poll_runtime_status.side_effect = BedrockRuntimePollingError(
            message="Runtime did not reach READY status within 600 seconds",
            error_code="S03-002-Timeout",
            context={"runtime_id": "test-runtime-id"}
        )
        mock_runtime.delete_runtime.return_value = None
        
        orchestrator = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=mock_bootstrap_orchestrator,
            bedrock_runtime=mock_runtime
        )
        
        # Act
        result = orchestrator.deploy(deploy_config)
        
        # Assert
        assert result.success is False
        assert result.error_code == "S03-002-Timeout"
        assert result.phase == "polling"
        assert result.runtime_id == "test-runtime-id"
        assert result.runtime_created is True
        
        # Verify rollback was called
        mock_runtime.delete_runtime.assert_called_once_with("test-runtime-id")
    
    def test_deploy_orchestrator_runtime_failed_with_rollback(
        self,
        deploy_config,
        mock_bootstrap_orchestrator,
        mock_bootstrap_result,
        mock_runtime_result
    ):
        """Test deployment rollback when runtime reaches CREATE_FAILED."""
        # Arrange
        mock_runtime = MagicMock()
        mock_runtime.create_runtime.return_value = mock_runtime_result
        mock_runtime.poll_runtime_status.side_effect = BedrockRuntimeError(
            message="Runtime creation failed: Container image not found",
            error_code="S03-002-CreateFailed",
            context={"runtime_id": "test-runtime-id", "failure_reason": "Container image not found"}
        )
        mock_runtime.delete_runtime.return_value = None
        
        orchestrator = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=mock_bootstrap_orchestrator,
            bedrock_runtime=mock_runtime
        )
        
        # Act
        result = orchestrator.deploy(deploy_config)
        
        # Assert
        assert result.success is False
        assert result.error_code == "S03-002-CreateFailed"
        assert result.phase == "polling"
        assert result.status == "CREATE_FAILED"
        
        # Verify rollback was called
        mock_runtime.delete_runtime.assert_called_once_with("test-runtime-id")
    
    def test_deploy_orchestrator_rollback_failure(
        self,
        deploy_config,
        mock_bootstrap_orchestrator,
        mock_bootstrap_result,
        mock_runtime_result
    ):
        """Test deployment when both polling and rollback fail."""
        # Arrange
        mock_runtime = MagicMock()
        mock_runtime.create_runtime.return_value = mock_runtime_result
        mock_runtime.poll_runtime_status.side_effect = BedrockRuntimePollingError(
            message="Runtime did not reach READY status",
            error_code="S03-002-Timeout"
        )
        mock_runtime.delete_runtime.side_effect = BedrockRuntimeError(
            message="Failed to delete runtime",
            error_code="S03-001-AccessDeniedException"
        )
        
        orchestrator = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=mock_bootstrap_orchestrator,
            bedrock_runtime=mock_runtime
        )
        
        # Act
        result = orchestrator.deploy(deploy_config)
        
        # Assert
        assert result.success is False
        assert result.error_code == "S03-002-Timeout"
        assert "rollback also failed" in result.error_message
    
    def test_deploy_orchestrator_with_write_tools_enabled(
        self,
        deploy_config,
        mock_bootstrap_orchestrator,
        mock_bedrock_runtime
    ):
        """Test deployment with write tools enabled."""
        # Arrange
        deploy_config.enable_write_tools = True
        orchestrator = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=mock_bootstrap_orchestrator,
            bedrock_runtime=mock_bedrock_runtime
        )
        
        # Act
        result = orchestrator.deploy(deploy_config)
        
        # Assert
        assert result.success is True
        
        # Verify enable_write_tools was passed
        create_call = mock_bedrock_runtime.create_runtime.call_args
        assert create_call.kwargs["enable_write_tools"] is True
    
    def test_deploy_orchestrator_with_custom_image_uri(
        self,
        deploy_config,
        mock_bootstrap_orchestrator,
        mock_bedrock_runtime
    ):
        """Test deployment with custom image URI."""
        # Arrange
        deploy_config.image_uri = "custom.ecr.repo/image:tag"
        orchestrator = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=mock_bootstrap_orchestrator,
            bedrock_runtime=mock_bedrock_runtime
        )
        
        # Act
        result = orchestrator.deploy(deploy_config)
        
        # Assert
        assert result.success is True
        
        # Verify custom image URI was passed
        create_call = mock_bedrock_runtime.create_runtime.call_args
        assert create_call.kwargs["image_uri"] == "custom.ecr.repo/image:tag"
    
    def test_deploy_orchestrator_custom_poll_timeout(
        self,
        deploy_config,
        mock_bootstrap_orchestrator,
        mock_bedrock_runtime
    ):
        """Test deployment with custom poll timeout."""
        # Arrange
        orchestrator = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=mock_bootstrap_orchestrator,
            bedrock_runtime=mock_bedrock_runtime
        )
        
        # Act
        result = orchestrator.deploy(deploy_config, poll_timeout_seconds=300)
        
        # Assert
        assert result.success is True
        
        # Verify custom timeout was used
        mock_bedrock_runtime.poll_runtime_status.assert_called_once_with(
            runtime_id="test-runtime-id",
            timeout_seconds=300
        )
    
    def test_deploy_orchestrator_bootstrap_reused_resources(
        self,
        deploy_config,
        mock_bedrock_runtime
    ):
        """Test deployment when bootstrap reuses existing resources."""
        # Arrange
        reused_bootstrap = BootstrapResult(
            secret_arn="arn:aws:secretsmanager:us-east-1:123456789012:secret:existing-secret",
            role_arn="arn:aws:iam::123456789012:role/existing-role",
            resource_ids=[],
            success=True,
            secret_created=False,
            role_created=False,
            phase="completed"
        )
        mock_bootstrap = MagicMock()
        mock_bootstrap.bootstrap_resources.return_value = reused_bootstrap
        
        orchestrator = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=mock_bootstrap,
            bedrock_runtime=mock_bedrock_runtime
        )
        
        # Act
        result = orchestrator.deploy(deploy_config)
        
        # Assert
        assert result.success is True
        assert result.secret_created is False
        assert result.role_created is False
        assert result.runtime_created is True
    
    def test_deploy_orchestrator_tracks_runtime_id(
        self,
        deploy_config,
        mock_bootstrap_orchestrator,
        mock_runtime_result
    ):
        """Test that orchestrator tracks created runtime ID."""
        # Arrange
        mock_runtime = MagicMock()
        mock_runtime.create_runtime.return_value = mock_runtime_result
        mock_runtime.poll_runtime_status.return_value = mock_runtime_result
        
        orchestrator = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=mock_bootstrap_orchestrator,
            bedrock_runtime=mock_runtime
        )
        
        # Act
        orchestrator.deploy(deploy_config)
        
        # Assert
        assert orchestrator.get_created_runtime_id() == "test-runtime-id"


class TestDeployOrchestratorLazyInit:
    """Test lazy initialization of dependencies."""
    
    def test_lazy_bootstrap_orchestrator(self):
        """Test that BootstrapOrchestrator is lazily initialized."""
        orchestrator = DeployOrchestrator(region="us-east-1")
        
        # Should be None initially
        assert orchestrator._bootstrap_orchestrator is None
        
        # Accessing property should create it
        bs = orchestrator.bootstrap_orchestrator
        assert bs is not None
        assert orchestrator._bootstrap_orchestrator is not None
    
    def test_lazy_bedrock_runtime(self):
        """Test that BedrockRuntime is lazily initialized."""
        orchestrator = DeployOrchestrator(region="us-east-1")
        
        # Should be None initially
        assert orchestrator._bedrock_runtime is None
        
        # Accessing property should create it
        rt = orchestrator.bedrock_runtime
        assert rt is not None
        assert orchestrator._bedrock_runtime is not None
    
    def test_lazy_session(self):
        """Test that boto3 session is lazily initialized."""
        orchestrator = DeployOrchestrator(region="us-east-1")
        
        # Should be None initially
        assert orchestrator._session is None
        
        # Accessing property should create it
        session = orchestrator.session
        assert session is not None
        assert orchestrator._session is not None
    
    def test_injected_dependencies_used(self):
        """Test that injected dependencies are used instead of creating new ones."""
        mock_bootstrap = MagicMock()
        mock_runtime = MagicMock()
        mock_session = MagicMock()
        
        orchestrator = DeployOrchestrator(
            region="us-east-1",
            session=mock_session,
            bootstrap_orchestrator=mock_bootstrap,
            bedrock_runtime=mock_runtime
        )
        
        # Should use injected dependencies
        assert orchestrator._bootstrap_orchestrator is mock_bootstrap
        assert orchestrator._bedrock_runtime is mock_runtime
        assert orchestrator._session is mock_session
        
        # Properties should return injected instances
        assert orchestrator.bootstrap_orchestrator is mock_bootstrap
        assert orchestrator.bedrock_runtime is mock_runtime
        assert orchestrator.session is mock_session


class TestDeployResult:
    """Test DeployResult dataclass."""
    
    def test_deploy_result_to_dict(self):
        """Test DeployResult serialization to dict."""
        bootstrap_result = BootstrapResult(
            secret_arn="arn:aws:secretsmanager:us-east-1:123456789012:secret:test",
            role_arn="arn:aws:iam::123456789012:role/test",
            success=True,
            secret_created=True,
            role_created=True,
            phase="completed"
        )
        
        result = DeployResult(
            success=True,
            runtime_id="runtime-123",
            runtime_arn="arn:aws:bedrock:us-east-1:123456789012:agent-runtime/runtime-123",
            endpoint_url="https://endpoint",
            status="READY",
            secret_arn="arn:aws:secretsmanager:us-east-1:123456789012:secret:test",
            role_arn="arn:aws:iam::123456789012:role/test",
            secret_created=True,
            role_created=True,
            runtime_created=True,
            bootstrap_result=bootstrap_result,
            phase="completed"
        )
        
        d = result.to_dict()
        
        assert d["success"] is True
        assert d["runtime_id"] == "runtime-123"
        assert d["status"] == "READY"
        assert d["bootstrap_result"] is not None
        assert d["bootstrap_result"]["secret_arn"] == "arn:aws:secretsmanager:us-east-1:123456789012:secret:test"
    
    def test_deploy_result_minimal(self):
        """Test DeployResult with minimal fields."""
        result = DeployResult(success=False)
        
        d = result.to_dict()
        
        assert d["success"] is False
        assert d["runtime_id"] is None
        assert d["bootstrap_result"] is None


class TestDeployConfig:
    """Test DeployConfig dataclass."""
    
    def test_deploy_config_to_dict_redacts_secrets(self):
        """Test that DeployConfig.to_dict() redacts sensitive values."""
        config = DeployConfig(
            runtime_name="test-runtime",
            secret_name="test-secret",
            role_name="test-role",
            username="user@example.com",
            password="super-secret-password",
            api_key="12345678901234567890123456789012",
            cloud="zscaler"
        )
        
        d = config.to_dict()
        
        # Sensitive fields should be redacted
        assert d["password"] == "<redacted>"
        assert d["api_key"] == "<redacted>"
        
        # Non-sensitive fields should be present
        assert d["runtime_name"] == "test-runtime"
        assert d["username"] == "user@example.com"
        assert d["cloud"] == "zscaler"
    
    def test_deploy_config_optional_fields(self):
        """Test DeployConfig with optional fields."""
        config = DeployConfig(
            runtime_name="test",
            secret_name="secret",
            role_name="role",
            username="user",
            password="pass",
            api_key="12345678901234567890123456789012",
            cloud="zscaler",
            image_uri="custom:image",
            enable_write_tools=True,
            region="us-west-2",
            description="Test deployment"
        )
        
        assert config.image_uri == "custom:image"
        assert config.enable_write_tools is True
        assert config.region == "us-west-2"
        assert config.description == "Test deployment"