"""Integration tests for S03 Deployment flow.

End-to-end tests exercising the complete deployment flow with mocked AWS services.
Tests cover success paths, partial failures, rollback scenarios, and edge cases
spanning bootstrap, runtime creation, and polling phases.
"""

import json
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, call
from botocore.exceptions import ClientError

from zscaler_mcp_deploy.deploy import DeployOrchestrator
from zscaler_mcp_deploy.bootstrap import BootstrapOrchestrator, BootstrapOrchestratorError
from zscaler_mcp_deploy.aws.bedrock_runtime import BedrockRuntime, BedrockRuntimeError
from zscaler_mcp_deploy.aws.secrets_manager import SecretsManager, SecretsManagerError
from zscaler_mcp_deploy.aws.iam_bootstrap import IAMBootstrap, IAMBootstrapError
from zscaler_mcp_deploy.models import (
    DeployConfig,
    DeployResult,
    BootstrapConfig,
    BootstrapResult,
    SecretResult,
    IAMRoleResult,
    RuntimeResult,
)
from zscaler_mcp_deploy.validators.aws import AWSSessionValidator
from zscaler_mcp_deploy.errors import BedrockRuntimePollingError


class TestDeployFullSuccessPath:
    """Tests for complete successful deployment flow."""
    
    def test_full_deploy_new_resources(self):
        """Test complete deployment creating all new resources."""
        # Create mocks for all dependencies
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid", "Region us-east-1"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        secret_result = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret-AbCdEf",
            name="test-secret",
            version_id="v1",
            created=True,
            kms_key_id="alias/aws/secretsmanager"
        )
        mock_secrets_manager.create_or_use_secret.return_value = secret_result
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        role_result = IAMRoleResult(
            arn="arn:aws:iam::123456789012:role/test-role",
            name="test-role",
            role_id="AROA1234567890EXAMPLE",
            created=True,
            trust_policy={"Version": "2012-10-17", "Statement": []}
        )
        mock_iam_bootstrap.create_or_use_execution_role.return_value = role_result
        
        mock_bedrock_client = Mock()
        mock_bedrock_client.create_agent_runtime.return_value = {
            "runtimeId": "runtime-abc123",
            "runtimeArn": "arn:aws:bedrock:us-east-1:123456789012:runtime/runtime-abc123",
            "status": "CREATING",
            "createdAt": datetime.now().isoformat()
        }
        # Poll: first CREATING, then READY
        mock_bedrock_client.get_agent_runtime.side_effect = [
            {"runtimeId": "runtime-abc123", "status": "CREATING"},
            {"runtimeId": "runtime-abc123", "status": "READY", "endpointUrl": "https://runtime.bedrock.aws/runtime-abc123"}
        ]
        
        mock_session = Mock()
        mock_session.client.return_value = mock_bedrock_client
        
        # Create bootstrap orchestrator
        bootstrap_orch = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        # Create bedrock runtime
        bedrock_rt = BedrockRuntime(session=mock_session)
        
        # Create deploy orchestrator with injected dependencies
        deploy_orch = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=bootstrap_orch,
            bedrock_runtime=bedrock_rt
        )
        
        config = DeployConfig(
            runtime_name="zscaler-mcp-runtime",
            secret_name="test-secret",
            role_name="test-role",
            username="admin@example.com",
            password="secret123",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = deploy_orch.deploy(config, poll_timeout_seconds=60)
        
        assert result.success is True
        assert result.runtime_id == "runtime-abc123"
        assert result.status == "READY"
        assert result.endpoint_url == "https://runtime.bedrock.aws/runtime-abc123"
        assert result.secret_created is True
        assert result.role_created is True
        assert result.runtime_created is True
        assert result.phase == "completed"
        assert result.secret_arn == secret_result.arn
        assert result.role_arn == role_result.arn
        
        # Verify all phases were called
        mock_validator.validate_session.assert_called_once()
        mock_secrets_manager.create_or_use_secret.assert_called_once()
        mock_iam_bootstrap.create_or_use_execution_role.assert_called_once()
        mock_bedrock_client.create_agent_runtime.assert_called_once()
        assert mock_bedrock_client.get_agent_runtime.call_count == 2
    
    def test_full_deploy_existing_resources(self):
        """Test deployment when all resources already exist."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        mock_secrets_manager.create_or_use_secret.return_value = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789012:secret:existing-secret",
            name="existing-secret",
            created=False  # Already existed
        )
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        mock_iam_bootstrap.create_or_use_execution_role.return_value = IAMRoleResult(
            arn="arn:aws:iam::123456789012:role/existing-role",
            name="existing-role",
            created=False  # Already existed
        )
        
        mock_bedrock_client = Mock()
        mock_bedrock_client.create_agent_runtime.return_value = {
            "runtimeId": "new-runtime",
            "runtimeArn": "arn:aws:bedrock:us-east-1:123456789012:runtime/new-runtime",
            "status": "CREATING"
        }
        mock_bedrock_client.get_agent_runtime.return_value = {
            "runtimeId": "new-runtime",
            "status": "READY",
            "endpointUrl": "https://runtime.bedrock.aws/new-runtime"
        }
        
        mock_session = Mock()
        mock_session.client.return_value = mock_bedrock_client
        
        bootstrap_orch = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        bedrock_rt = BedrockRuntime(session=mock_session)
        
        deploy_orch = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=bootstrap_orch,
            bedrock_runtime=bedrock_rt
        )
        
        config = DeployConfig(
            runtime_name="zscaler-runtime",
            secret_name="existing-secret",
            role_name="existing-role",
            username="admin@example.com",
            password="secret123",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = deploy_orch.deploy(config)
        
        assert result.success is True
        assert result.secret_created is False
        assert result.role_created is False
        assert result.runtime_created is True
    
    def test_full_deploy_with_all_options(self):
        """Test deployment with all optional configuration."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        mock_secrets_manager.create_or_use_secret.return_value = SecretResult(
            arn="arn:aws:secretsmanager:us-west-2:123456789012:secret:prod-secret",
            name="prod-secret",
            created=True
        )
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        mock_iam_bootstrap.create_or_use_execution_role.return_value = IAMRoleResult(
            arn="arn:aws:iam::123456789012:role/prod-role",
            name="prod-role",
            created=True
        )
        
        mock_bedrock_client = Mock()
        mock_bedrock_client.create_agent_runtime.return_value = {
            "runtimeId": "prod-runtime",
            "runtimeArn": "arn:aws:bedrock:us-west-2:123456789012:runtime/prod-runtime",
            "status": "CREATING"
        }
        mock_bedrock_client.get_agent_runtime.return_value = {
            "runtimeId": "prod-runtime",
            "status": "READY",
            "endpointUrl": "https://runtime.bedrock.aws/prod-runtime"
        }
        
        mock_session = Mock()
        mock_session.client.return_value = mock_bedrock_client
        
        bootstrap_orch = BootstrapOrchestrator(
            region="us-west-2",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        bedrock_rt = BedrockRuntime(session=mock_session)
        
        deploy_orch = DeployOrchestrator(
            region="us-west-2",
            bootstrap_orchestrator=bootstrap_orch,
            bedrock_runtime=bedrock_rt
        )
        
        tags = [
            {"Key": "Environment", "Value": "Production"},
            {"Key": "Project", "Value": "ZscalerMCP"}
        ]
        
        config = DeployConfig(
            runtime_name="prod-zscaler-runtime",
            secret_name="prod-secret",
            role_name="prod-role",
            username="admin@company.com",
            password="SuperSecure123!",
            api_key="abcdef1234567890abcdef1234567890",
            cloud="zscalerthree",
            image_uri="custom.ecr.aws/zscaler/mcp-server:v1.0.0",
            enable_write_tools=True,
            kms_key_id="arn:aws:kms:us-west-2:123456789012:key/my-key",
            region="us-west-2",
            profile_name="production",
            description="Production Zscaler MCP deployment",
            tags=tags
        )
        
        result = deploy_orch.deploy(config)
        
        assert result.success is True
        
        # Verify all options were passed through
        create_call = mock_bedrock_client.create_agent_runtime.call_args[1]
        assert create_call["runtimeName"] == "prod-zscaler-runtime"
        container_config = create_call["agentRuntimeConfiguration"]["containerConfiguration"]
        assert container_config["imageUri"] == "custom.ecr.aws/zscaler/mcp-server:v1.0.0"
        env_vars = container_config["environmentVariables"]
        assert env_vars["ENABLE_WRITE_TOOLS"] == "true"
        assert create_call["tags"] == tags


class TestDeployBootstrapFailures:
    """Tests for bootstrap phase failures."""
    
    def test_deploy_fails_when_preflight_fails(self):
        """Test deployment stops when preflight validation fails."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (
            False,
            ["No AWS credentials found"]
        )
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        mock_bedrock_client = Mock()
        
        mock_session = Mock()
        mock_session.client.return_value = mock_bedrock_client
        
        bootstrap_orch = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        bedrock_rt = BedrockRuntime(session=mock_session)
        
        deploy_orch = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=bootstrap_orch,
            bedrock_runtime=bedrock_rt
        )
        
        config = DeployConfig(
            runtime_name="test-runtime",
            secret_name="test-secret",
            role_name="test-role",
            username="admin",
            password="pass",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = deploy_orch.deploy(config)
        
        assert result.success is False
        assert result.phase == "bootstrap"
        assert "S02-003-PreflightFailed" in result.error_code
        assert result.runtime_id is None
        
        # No AWS calls should be made
        mock_secrets_manager.create_or_use_secret.assert_not_called()
        mock_iam_bootstrap.create_or_use_execution_role.assert_not_called()
        mock_bedrock_client.create_agent_runtime.assert_not_called()
    
    def test_deploy_fails_when_secret_creation_fails(self):
        """Test deployment stops when secret creation fails."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        error = SecretsManagerError(
            message="Access denied to Secrets Manager",
            error_code="S02-001-AccessDeniedException"
        )
        mock_secrets_manager.create_or_use_secret.side_effect = error
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        mock_bedrock_client = Mock()
        
        mock_session = Mock()
        mock_session.client.return_value = mock_bedrock_client
        
        bootstrap_orch = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        bedrock_rt = BedrockRuntime(session=mock_session)
        
        deploy_orch = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=bootstrap_orch,
            bedrock_runtime=bedrock_rt
        )
        
        config = DeployConfig(
            runtime_name="test-runtime",
            secret_name="test-secret",
            role_name="test-role",
            username="admin",
            password="pass",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = deploy_orch.deploy(config)
        
        assert result.success is False
        assert result.phase == "bootstrap"
        assert result.error_code == "S02-001-AccessDeniedException"
        
        # No runtime creation should be attempted
        mock_bedrock_client.create_agent_runtime.assert_not_called()
    
    def test_deploy_fails_when_role_creation_fails(self):
        """Test deployment stops and rolls back when role creation fails."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        mock_secrets_manager.create_or_use_secret.return_value = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret",
            name="test-secret",
            created=True
        )
        mock_secrets_manager.delete_secret.return_value = None
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        error = IAMBootstrapError(
            message="Role creation failed",
            error_code="S02-002-AccessDeniedException"
        )
        mock_iam_bootstrap.create_or_use_execution_role.side_effect = error
        mock_iam_bootstrap.delete_role.return_value = None
        
        mock_bedrock_client = Mock()
        
        mock_session = Mock()
        mock_session.client.return_value = mock_bedrock_client
        
        bootstrap_orch = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        bedrock_rt = BedrockRuntime(session=mock_session)
        
        deploy_orch = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=bootstrap_orch,
            bedrock_runtime=bedrock_rt
        )
        
        config = DeployConfig(
            runtime_name="test-runtime",
            secret_name="test-secret",
            role_name="test-role",
            username="admin",
            password="pass",
            api_key="a" * 32,
            cloud="zscaler"
        )        
        result = deploy_orch.deploy(config)
        
        assert result.success is False
        assert result.phase == "bootstrap"
        assert result.error_code == "S02-002-AccessDeniedException"
        
        # Secret should be rolled back since it was created
        mock_secrets_manager.delete_secret.assert_called_once_with(
            "test-secret",
            force_delete_without_recovery=True
        )
        
        # No runtime creation should be attempted
        mock_bedrock_client.create_agent_runtime.assert_not_called()


class TestDeployRuntimeFailures:
    """Tests for runtime creation and polling failures."""
    
    def test_deploy_fails_when_runtime_creation_fails(self):
        """Test deployment stops when runtime creation fails."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        mock_secrets_manager.create_or_use_secret.return_value = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret",
            name="test-secret",
            created=True
        )
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        mock_iam_bootstrap.create_or_use_execution_role.return_value = IAMRoleResult(
            arn="arn:aws:iam::123456789012:role:test-role",
            name="test-role",
            created=True
        )
        
        mock_bedrock_client = Mock()
        error_response = {
            "Error": {
                "Code": "AccessDeniedException",
                "Message": "Not authorized to create Bedrock runtime"
            }
        }
        mock_bedrock_client.create_agent_runtime.side_effect = ClientError(
            error_response, "CreateAgentRuntime"
        )
        
        mock_session = Mock()
        mock_session.client.return_value = mock_bedrock_client
        
        bootstrap_orch = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        bedrock_rt = BedrockRuntime(session=mock_session)
        
        deploy_orch = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=bootstrap_orch,
            bedrock_runtime=bedrock_rt
        )
        
        config = DeployConfig(
            runtime_name="test-runtime",
            secret_name="test-secret",
            role_name="test-role",
            username="admin",
            password="pass",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = deploy_orch.deploy(config)
        
        assert result.success is False
        assert result.phase == "runtime_create"
        assert "S03-001-AccessDeniedException" in result.error_code
        
        # Bootstrap resources should NOT be rolled back per R008
        mock_secrets_manager.delete_secret.assert_not_called()
        mock_iam_bootstrap.delete_role.assert_not_called()
    
    def test_deploy_rolls_back_on_polling_timeout(self):
        """Test runtime is deleted when polling times out."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        mock_secrets_manager.create_or_use_secret.return_value = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret",
            name="test-secret",
            created=True
        )
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        mock_iam_bootstrap.create_or_use_execution_role.return_value = IAMRoleResult(
            arn="arn:aws:iam::123456789012:role:test-role",
            name="test-role",
            created=True
        )
        
        mock_bedrock_client = Mock()
        mock_bedrock_client.create_agent_runtime.return_value = {
            "runtimeId": "slow-runtime",
            "runtimeArn": "arn:aws:bedrock:us-east-1:123456789012:runtime/slow-runtime",
            "status": "CREATING"
        }
        # Always return CREATING to trigger timeout
        mock_bedrock_client.get_agent_runtime.return_value = {
            "runtimeId": "slow-runtime",
            "status": "CREATING"
        }
        mock_bedrock_client.delete_agent_runtime.return_value = None
        
        mock_session = Mock()
        mock_session.client.return_value = mock_bedrock_client
        
        bootstrap_orch = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        bedrock_rt = BedrockRuntime(session=mock_session)
        
        deploy_orch = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=bootstrap_orch,
            bedrock_runtime=bedrock_rt
        )
        
        config = DeployConfig(
            runtime_name="test-runtime",
            secret_name="test-secret",
            role_name="test-role",
            username="admin",
            password="pass",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = deploy_orch.deploy(config, poll_timeout_seconds=0.5)
        
        assert result.success is False
        assert result.phase == "polling"
        assert "S03-002-Timeout" in result.error_code
        assert result.runtime_id == "slow-runtime"
        
        # Runtime should be rolled back
        mock_bedrock_client.delete_agent_runtime.assert_called_once_with(
            runtimeId="slow-runtime"
        )
    
    def test_deploy_rolls_back_on_create_failed(self):
        """Test runtime is deleted when it reaches CREATE_FAILED."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        mock_secrets_manager.create_or_use_secret.return_value = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret",
            name="test-secret",
            created=True
        )
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        mock_iam_bootstrap.create_or_use_execution_role.return_value = IAMRoleResult(
            arn="arn:aws:iam::123456789012:role:test-role",
            name="test-role",
            created=True
        )
        
        mock_bedrock_client = Mock()
        mock_bedrock_client.create_agent_runtime.return_value = {
            "runtimeId": "failing-runtime",
            "runtimeArn": "arn:aws:bedrock:us-east-1:123456789012:runtime/failing-runtime",
            "status": "CREATING"
        }
        mock_bedrock_client.get_agent_runtime.return_value = {
            "runtimeId": "failing-runtime",
            "status": "CREATE_FAILED",
            "errorCode": "ContainerImageNotFound",
            "errorMessage": "Container image not accessible"
        }
        mock_bedrock_client.delete_agent_runtime.return_value = None
        
        mock_session = Mock()
        mock_session.client.return_value = mock_bedrock_client
        
        bootstrap_orch = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        bedrock_rt = BedrockRuntime(session=mock_session)
        
        deploy_orch = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=bootstrap_orch,
            bedrock_runtime=bedrock_rt
        )
        
        config = DeployConfig(
            runtime_name="test-runtime",
            secret_name="test-secret",
            role_name="test-role",
            username="admin",
            password="pass",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = deploy_orch.deploy(config)
        
        assert result.success is False
        assert result.phase == "polling"
        assert result.status == "CREATE_FAILED"
        assert "S03-002-CreateFailed" in result.error_code
        
        # Runtime should be rolled back
        mock_bedrock_client.delete_agent_runtime.assert_called_once_with(
            runtimeId="failing-runtime"
        )


class TestDeployErrorPropagation:
    """Tests for error code propagation between components."""
    
    def test_bootstrap_error_code_propagated(self):
        """Test that bootstrap error codes are preserved."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        error = SecretsManagerError(
            message="KMS key not found",
            error_code="S02-001-KMSNotFoundException"
        )
        mock_secrets_manager.create_or_use_secret.side_effect = error
        
        mock_bedrock_client = Mock()
        mock_session = Mock()
        mock_session.client.return_value = mock_bedrock_client
        
        bootstrap_orch = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=Mock(spec=IAMBootstrap)
        )
        
        bedrock_rt = BedrockRuntime(session=mock_session)
        
        deploy_orch = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=bootstrap_orch,
            bedrock_runtime=bedrock_rt
        )
        
        config = DeployConfig(
            runtime_name="test-runtime",
            secret_name="test-secret",
            role_name="test-role",
            username="admin",
            password="pass",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = deploy_orch.deploy(config)
        
        assert result.success is False
        assert result.error_code == "S02-001-KMSNotFoundException"
    
    def test_runtime_error_code_propagated(self):
        """Test that runtime error codes are preserved."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        mock_secrets_manager.create_or_use_secret.return_value = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret",
            name="test-secret",
            created=True
        )
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        mock_iam_bootstrap.create_or_use_execution_role.return_value = IAMRoleResult(
            arn="arn:aws:iam::123456789012:role:test-role",
            name="test-role",
            created=True
        )
        
        mock_bedrock_client = Mock()
        error_response = {
            "Error": {
                "Code": "ResourceLimitExceeded",
                "Message": "Too many Bedrock runtimes"
            }
        }
        mock_bedrock_client.create_agent_runtime.side_effect = ClientError(
            error_response, "CreateAgentRuntime"
        )
        
        mock_session = Mock()
        mock_session.client.return_value = mock_bedrock_client
        
        bootstrap_orch = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        bedrock_rt = BedrockRuntime(session=mock_session)
        
        deploy_orch = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=bootstrap_orch,
            bedrock_runtime=bedrock_rt
        )
        
        config = DeployConfig(
            runtime_name="test-runtime",
            secret_name="test-secret",
            role_name="test-role",
            username="admin",
            password="pass",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = deploy_orch.deploy(config)
        
        assert result.success is False
        assert "S03-001-ResourceLimitExceeded" in result.error_code
    
    def test_polling_error_code_propagated(self):
        """Test that polling error codes are preserved."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        mock_secrets_manager.create_or_use_secret.return_value = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret",
            name="test-secret",
            created=True
        )
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        mock_iam_bootstrap.create_or_use_execution_role.return_value = IAMRoleResult(
            arn="arn:aws:iam::123456789012:role:test-role",
            name="test-role",
            created=True
        )
        
        mock_bedrock_client = Mock()
        mock_bedrock_client.create_agent_runtime.return_value = {
            "runtimeId": "test-runtime",
            "runtimeArn": "arn:aws:bedrock:us-east-1:123456789012:runtime/test-runtime",
            "status": "CREATING"
        }
        error_response = {
            "Error": {
                "Code": "ThrottlingException",
                "Message": "Rate exceeded"
            }
        }
        mock_bedrock_client.get_agent_runtime.side_effect = ClientError(
            error_response, "GetAgentRuntime"
        )
        mock_bedrock_client.delete_agent_runtime.return_value = None
        
        mock_session = Mock()
        mock_session.client.return_value = mock_bedrock_client
        
        bootstrap_orch = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        bedrock_rt = BedrockRuntime(session=mock_session)
        
        deploy_orch = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=bootstrap_orch,
            bedrock_runtime=bedrock_rt
        )
        
        config = DeployConfig(
            runtime_name="test-runtime",
            secret_name="test-secret",
            role_name="test-role",
            username="admin",
            password="pass",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = deploy_orch.deploy(config)
        
        assert result.success is False
        # Error code contains ThrottlingException from AWS API
        assert "ThrottlingException" in result.error_code


class TestDeployResourceTracking:
    """Tests for resource tracking and cleanup."""
    
    def test_deploy_tracks_runtime_for_cleanup(self):
        """Test that deploy tracks created runtime ID."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        mock_secrets_manager.create_or_use_secret.return_value = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret",
            name="test-secret",
            created=True
        )
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        mock_iam_bootstrap.create_or_use_execution_role.return_value = IAMRoleResult(
            arn="arn:aws:iam::123456789012:role:test-role",
            name="test-role",
            created=True
        )
        
        mock_bedrock_client = Mock()
        mock_bedrock_client.create_agent_runtime.return_value = {
            "runtimeId": "tracked-runtime",
            "runtimeArn": "arn:aws:bedrock:us-east-1:123456789012:runtime/tracked-runtime",
            "status": "CREATING"
        }
        mock_bedrock_client.get_agent_runtime.return_value = {
            "runtimeId": "tracked-runtime",
            "status": "READY",
            "endpointUrl": "https://runtime.bedrock.aws/tracked-runtime"
        }
        
        mock_session = Mock()
        mock_session.client.return_value = mock_bedrock_client
        
        bootstrap_orch = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        bedrock_rt = BedrockRuntime(session=mock_session)
        
        deploy_orch = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=bootstrap_orch,
            bedrock_runtime=bedrock_rt
        )
        
        config = DeployConfig(
            runtime_name="test-runtime",
            secret_name="test-secret",
            role_name="test-role",
            username="admin",
            password="pass",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        # Before deploy, no runtime ID tracked
        assert deploy_orch.get_created_runtime_id() is None
        
        # After deploy, runtime ID is tracked
        result = deploy_orch.deploy(config)
        assert result.success is True
        assert deploy_orch.get_created_runtime_id() == "tracked-runtime"
    
    def test_deploy_clears_tracking_on_rollback(self):
        """Test that runtime tracking is cleared after rollback."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        mock_secrets_manager.create_or_use_secret.return_value = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret",
            name="test-secret",
            created=True
        )
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        mock_iam_bootstrap.create_or_use_execution_role.return_value = IAMRoleResult(
            arn="arn:aws:iam::123456789012:role:test-role",
            name="test-role",
            created=True
        )
        
        mock_bedrock_client = Mock()
        mock_bedrock_client.create_agent_runtime.return_value = {
            "runtimeId": "rolled-back-runtime",
            "runtimeArn": "arn:aws:bedrock:us-east-1:123456789012:runtime/rolled-back-runtime",
            "status": "CREATING"
        }
        mock_bedrock_client.get_agent_runtime.return_value = {
            "runtimeId": "rolled-back-runtime",
            "status": "CREATE_FAILED",
            "errorCode": "ImageNotFound",
            "errorMessage": "Image not found"
        }
        mock_bedrock_client.delete_agent_runtime.return_value = None
        
        mock_session = Mock()
        mock_session.client.return_value = mock_bedrock_client
        
        bootstrap_orch = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        bedrock_rt = BedrockRuntime(session=mock_session)
        
        deploy_orch = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=bootstrap_orch,
            bedrock_runtime=bedrock_rt
        )
        
        config = DeployConfig(
            runtime_name="test-runtime",
            secret_name="test-secret",
            role_name="test-role",
            username="admin",
            password="pass",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = deploy_orch.deploy(config)
        
        assert result.success is False
        # Runtime ID should be cleared after successful rollback
        assert deploy_orch.get_created_runtime_id() is None


class TestDeployEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_deploy_with_reused_secret_new_role(self):
        """Test deployment when secret exists but role is new."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        mock_secrets_manager.create_or_use_secret.return_value = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789012:secret:existing-secret",
            name="existing-secret",
            created=False  # Already existed
        )
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        mock_iam_bootstrap.create_or_use_execution_role.return_value = IAMRoleResult(
            arn="arn:aws:iam::123456789012:role:new-role",
            name="new-role",
            created=True
        )
        
        mock_bedrock_client = Mock()
        mock_bedrock_client.create_agent_runtime.return_value = {
            "runtimeId": "runtime-123",
            "runtimeArn": "arn:aws:bedrock:us-east-1:123456789012:runtime/runtime-123",
            "status": "CREATING"
        }
        mock_bedrock_client.get_agent_runtime.return_value = {
            "runtimeId": "runtime-123",
            "status": "READY",
            "endpointUrl": "https://runtime.bedrock.aws/runtime-123"
        }
        
        mock_session = Mock()
        mock_session.client.return_value = mock_bedrock_client
        
        bootstrap_orch = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        bedrock_rt = BedrockRuntime(session=mock_session)
        
        deploy_orch = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=bootstrap_orch,
            bedrock_runtime=bedrock_rt
        )
        
        config = DeployConfig(
            runtime_name="test-runtime",
            secret_name="existing-secret",
            role_name="new-role",
            username="admin",
            password="pass",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = deploy_orch.deploy(config)
        
        assert result.success is True
        assert result.secret_created is False
        assert result.role_created is True
        assert result.runtime_created is True
    
    def test_deploy_polling_multiple_status_changes(self):
        """Test polling through multiple status transitions."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        mock_secrets_manager.create_or_use_secret.return_value = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret",
            name="test-secret",
            created=True
        )
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        mock_iam_bootstrap.create_or_use_execution_role.return_value = IAMRoleResult(
            arn="arn:aws:iam::123456789012:role:test-role",
            name="test-role",
            created=True
        )
        
        mock_bedrock_client = Mock()
        mock_bedrock_client.create_agent_runtime.return_value = {
            "runtimeId": "multi-status-runtime",
            "runtimeArn": "arn:aws:bedrock:us-east-1:123456789012:runtime/multi-status-runtime",
            "status": "CREATING"
        }
        # Multiple status transitions: CREATING -> CREATING -> READY
        mock_bedrock_client.get_agent_runtime.side_effect = [
            {"runtimeId": "multi-status-runtime", "status": "CREATING"},
            {"runtimeId": "multi-status-runtime", "status": "CREATING"},
            {"runtimeId": "multi-status-runtime", "status": "CREATING"},
            {"runtimeId": "multi-status-runtime", "status": "READY", "endpointUrl": "https://runtime.endpoint"}
        ]
        
        mock_session = Mock()
        mock_session.client.return_value = mock_bedrock_client
        
        bootstrap_orch = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        bedrock_rt = BedrockRuntime(session=mock_session)
        
        deploy_orch = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=bootstrap_orch,
            bedrock_runtime=bedrock_rt
        )
        
        config = DeployConfig(
            runtime_name="test-runtime",
            secret_name="test-secret",
            role_name="test-role",
            username="admin",
            password="pass",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = deploy_orch.deploy(config, poll_timeout_seconds=60)
        
        assert result.success is True
        assert result.status == "READY"
        assert mock_bedrock_client.get_agent_runtime.call_count == 4
    
    def test_deploy_result_includes_bootstrap_details(self):
        """Test that DeployResult includes full bootstrap result."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        mock_secrets_manager.create_or_use_secret.return_value = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret",
            name="test-secret",
            created=True
        )
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        mock_iam_bootstrap.create_or_use_execution_role.return_value = IAMRoleResult(
            arn="arn:aws:iam::123456789012:role:test-role",
            name="test-role",
            created=True
        )
        
        mock_bedrock_client = Mock()
        mock_bedrock_client.create_agent_runtime.return_value = {
            "runtimeId": "test-runtime",
            "runtimeArn": "arn:aws:bedrock:us-east-1:123456789012:runtime/test-runtime",
            "status": "CREATING"
        }
        mock_bedrock_client.get_agent_runtime.return_value = {
            "runtimeId": "test-runtime",
            "status": "READY",
            "endpointUrl": "https://runtime.bedrock.aws/test-runtime"
        }
        
        mock_session = Mock()
        mock_session.client.return_value = mock_bedrock_client
        
        bootstrap_orch = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        bedrock_rt = BedrockRuntime(session=mock_session)
        
        deploy_orch = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=bootstrap_orch,
            bedrock_runtime=bedrock_rt
        )
        
        config = DeployConfig(
            runtime_name="test-runtime",
            secret_name="test-secret",
            role_name="test-role",
            username="admin",
            password="pass",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = deploy_orch.deploy(config)
        
        assert result.success is True
        assert result.bootstrap_result is not None
        assert result.bootstrap_result.secret_arn == "arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret"
        assert result.bootstrap_result.role_arn == "arn:aws:iam::123456789012:role:test-role"
        assert result.bootstrap_result.secret_created is True
        assert result.bootstrap_result.role_created is True
    
    def test_deploy_with_long_resource_names(self):
        """Test deployment with long resource names."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        mock_secrets_manager.create_or_use_secret.return_value = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789012:secret:very-long-secret-name-that-is-valid",
            name="very-long-secret-name-that-is-valid",
            created=True
        )
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        mock_iam_bootstrap.create_or_use_execution_role.return_value = IAMRoleResult(
            arn="arn:aws:iam::123456789012:role:VeryLongRoleNameThatIsStillValidAndWithinLimits",
            name="VeryLongRoleNameThatIsStillValidAndWithinLimits",
            created=True
        )
        
        mock_bedrock_client = Mock()
        mock_bedrock_client.create_agent_runtime.return_value = {
            "runtimeId": "runtime-long",
            "runtimeArn": "arn:aws:bedrock:us-east-1:123456789012:runtime/runtime-long",
            "status": "CREATING"
        }
        mock_bedrock_client.get_agent_runtime.return_value = {
            "runtimeId": "runtime-long",
            "status": "READY",
            "endpointUrl": "https://runtime.bedrock.aws/runtime-long"
        }
        
        mock_session = Mock()
        mock_session.client.return_value = mock_bedrock_client
        
        bootstrap_orch = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        bedrock_rt = BedrockRuntime(session=mock_session)
        
        deploy_orch = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=bootstrap_orch,
            bedrock_runtime=bedrock_rt
        )
        
        config = DeployConfig(
            runtime_name="very-long-runtime-name-that-is-still-valid",
            secret_name="very-long-secret-name-that-is-valid",
            role_name="VeryLongRoleNameThatIsStillValidAndWithinLimits",
            username="admin@example.com",
            password="secret123",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = deploy_orch.deploy(config)
        
        assert result.success is True
        assert result.runtime_id == "runtime-long"


class TestDeployPhaseProgression:
    """Tests for deployment phase progression."""
    
    def test_successful_phase_progression(self):
        """Test phase field progresses through bootstrap -> runtime_create -> polling -> completed."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        mock_secrets_manager.create_or_use_secret.return_value = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret",
            name="test-secret",
            created=True
        )
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        mock_iam_bootstrap.create_or_use_execution_role.return_value = IAMRoleResult(
            arn="arn:aws:iam::123456789012:role:test-role",
            name="test-role",
            created=True
        )
        
        mock_bedrock_client = Mock()
        mock_bedrock_client.create_agent_runtime.return_value = {
            "runtimeId": "phase-test-runtime",
            "runtimeArn": "arn:aws:bedrock:us-east-1:123456789012:runtime/phase-test-runtime",
            "status": "CREATING"
        }
        mock_bedrock_client.get_agent_runtime.return_value = {
            "runtimeId": "phase-test-runtime",
            "status": "READY",
            "endpointUrl": "https://runtime.bedrock.aws/phase-test-runtime"
        }
        
        mock_session = Mock()
        mock_session.client.return_value = mock_bedrock_client
        
        bootstrap_orch = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        bedrock_rt = BedrockRuntime(session=mock_session)
        
        deploy_orch = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=bootstrap_orch,
            bedrock_runtime=bedrock_rt
        )
        
        config = DeployConfig(
            runtime_name="test-runtime",
            secret_name="test-secret",
            role_name="test-role",
            username="admin",
            password="pass",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = deploy_orch.deploy(config)
        
        assert result.success is True
        assert result.phase == "completed"
    
    def test_bootstrap_failure_phase(self):
        """Test phase is 'bootstrap' when bootstrap fails."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (False, ["Invalid credentials"])
        
        mock_bedrock_client = Mock()
        mock_session = Mock()
        mock_session.client.return_value = mock_bedrock_client
        
        bootstrap_orch = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=Mock(spec=SecretsManager),
            iam_bootstrap=Mock(spec=IAMBootstrap)
        )
        
        bedrock_rt = BedrockRuntime(session=mock_session)
        
        deploy_orch = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=bootstrap_orch,
            bedrock_runtime=bedrock_rt
        )
        
        config = DeployConfig(
            runtime_name="test-runtime",
            secret_name="test-secret",
            role_name="test-role",
            username="admin",
            password="pass",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = deploy_orch.deploy(config)
        
        assert result.success is False
        assert result.phase == "bootstrap"
    
    def test_runtime_create_failure_phase(self):
        """Test phase is 'runtime_create' when runtime creation fails."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        mock_secrets_manager.create_or_use_secret.return_value = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret",
            name="test-secret",
            created=True
        )
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        mock_iam_bootstrap.create_or_use_execution_role.return_value = IAMRoleResult(
            arn="arn:aws:iam::123456789012:role:test-role",
            name="test-role",
            created=True
        )
        
        mock_bedrock_client = Mock()
        error_response = {
            "Error": {
                "Code": "ValidationException",
                "Message": "Invalid runtime configuration"
            }
        }
        mock_bedrock_client.create_agent_runtime.side_effect = ClientError(
            error_response, "CreateAgentRuntime"
        )
        
        mock_session = Mock()
        mock_session.client.return_value = mock_bedrock_client
        
        bootstrap_orch = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        bedrock_rt = BedrockRuntime(session=mock_session)
        
        deploy_orch = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=bootstrap_orch,
            bedrock_runtime=bedrock_rt
        )
        
        config = DeployConfig(
            runtime_name="test-runtime",
            secret_name="test-secret",
            role_name="test-role",
            username="admin",
            password="pass",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = deploy_orch.deploy(config)
        
        assert result.success is False
        assert result.phase == "runtime_create"
    
    def test_polling_failure_phase(self):
        """Test phase is 'polling' when polling fails or times out."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        mock_secrets_manager.create_or_use_secret.return_value = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret",
            name="test-secret",
            created=True
        )
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        mock_iam_bootstrap.create_or_use_execution_role.return_value = IAMRoleResult(
            arn="arn:aws:iam::123456789012:role:test-role",
            name="test-role",
            created=True
        )
        
        mock_bedrock_client = Mock()
        mock_bedrock_client.create_agent_runtime.return_value = {
            "runtimeId": "timeout-runtime",
            "runtimeArn": "arn:aws:bedrock:us-east-1:123456789012:runtime/timeout-runtime",
            "status": "CREATING"
        }
        mock_bedrock_client.get_agent_runtime.return_value = {
            "runtimeId": "timeout-runtime",
            "status": "CREATING"
        }
        mock_bedrock_client.delete_agent_runtime.return_value = None
        
        mock_session = Mock()
        mock_session.client.return_value = mock_bedrock_client
        
        bootstrap_orch = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        bedrock_rt = BedrockRuntime(session=mock_session)
        
        deploy_orch = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=bootstrap_orch,
            bedrock_runtime=bedrock_rt
        )
        
        config = DeployConfig(
            runtime_name="test-runtime",
            secret_name="test-secret",
            role_name="test-role",
            username="admin",
            password="pass",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = deploy_orch.deploy(config, poll_timeout_seconds=0.5)
        
        assert result.success is False
        assert result.phase == "polling"
        assert result.runtime_created is True  # Runtime was created before polling failed
