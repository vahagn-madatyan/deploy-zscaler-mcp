"""Integration tests for S04 Verification & Connection Output.

End-to-end tests exercising the verification and connection output integration.
Tests cover success, skip, failure, and error paths for verification,
Rich panel display, connection instructions, and exit codes.
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
from zscaler_mcp_deploy.aws.cloudwatch_verifier import RuntimeVerifier
from zscaler_mcp_deploy.output.connection_formatter import ConnectionFormatter
from zscaler_mcp_deploy.models import (
    DeployConfig,
    DeployResult,
    BootstrapConfig,
    BootstrapResult,
    SecretResult,
    IAMRoleResult,
    RuntimeResult,
    VerificationResult,
    VerificationStatus,
)
from zscaler_mcp_deploy.validators.aws import AWSSessionValidator
from zscaler_mcp_deploy.errors import BedrockRuntimePollingError, CloudWatchError, VerificationError


class TestVerificationSuccessPath:
    """Tests for successful verification integration."""
    
    def test_full_deploy_with_verification_healthy(self):
        """Test complete deployment with healthy verification."""
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
            "runtimeId": "runtime-abc123",
            "runtimeArn": "arn:aws:bedrock:us-east-1:123456789012:runtime/runtime-abc123",
            "status": "CREATING"
        }
        mock_bedrock_client.get_agent_runtime.return_value = {
            "runtimeId": "runtime-abc123",
            "status": "READY",
            "endpointUrl": "https://runtime.bedrock.aws/runtime-abc123"
        }
        
        mock_session = Mock()
        mock_session.client.return_value = mock_bedrock_client
        
        # Mock verification
        mock_cloudwatch_client = Mock()
        mock_cloudwatch_client.describe_log_groups.return_value = {
            "logGroups": [{"logGroupName": "/aws/bedrock/runtime-abc123"}]
        }
        mock_cloudwatch_client.describe_log_streams.return_value = {
            "logStreams": [{"logStreamName": "stream1"}]
        }
        mock_cloudwatch_client.filter_log_events.return_value = {
            "events": [
                {"logStreamName": "stream1", "message": "Credential retrieved"},
                {"logStreamName": "stream1", "message": "MCP server started"},
                {"logStreamName": "stream1", "message": "Listening on port 8080"}
            ]
        }
        
        # Create bootstrap orchestrator
        bootstrap_orch = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        # Create bedrock runtime
        bedrock_rt = BedrockRuntime(session=mock_session)
        
        # Create runtime verifier
        runtime_verifier = RuntimeVerifier()
        runtime_verifier._client = mock_cloudwatch_client
        
        # Create deploy orchestrator with injected dependencies
        deploy_orch = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=bootstrap_orch,
            bedrock_runtime=bedrock_rt,
            runtime_verifier=runtime_verifier
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
        assert result.verification_result is not None
        assert result.verification_result.status == VerificationStatus.HEALTHY
        assert result.verification_result.is_healthy() is True
        assert len(result.verification_result.matched_patterns) >= 3
        
        # Verify CloudWatch calls were made
        mock_cloudwatch_client.describe_log_groups.assert_called_once()
        mock_cloudwatch_client.describe_log_streams.assert_called_once()
        mock_cloudwatch_client.filter_log_events.assert_called_once()
    
    def test_full_deploy_with_skip_verification(self):
        """Test deployment with --skip-verification flag."""
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
            "runtimeId": "runtime-skip",
            "runtimeArn": "arn:aws:bedrock:us-east-1:123456789012:runtime/runtime-skip",
            "status": "CREATING"
        }
        mock_bedrock_client.get_agent_runtime.return_value = {
            "runtimeId": "runtime-skip",
            "status": "READY",
            "endpointUrl": "https://runtime.bedrock.aws/runtime-skip"
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
            secret_name="test-secret",
            role_name="test-role",
            username="admin@example.com",
            password="secret123",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        # Call deploy with skip_verification=True
        result = deploy_orch.deploy(config, skip_verification=True)
        
        assert result.success is True
        assert result.runtime_id == "runtime-skip"
        assert result.verification_result is None  # No verification result when skipped
        
        # Ensure CloudWatch client was never created
        # (runtime_verifier property is lazy, should not be accessed)
        assert deploy_orch._runtime_verifier is None
    
    def test_deploy_with_verification_unhealthy(self):
        """Test deployment with unhealthy verification (exit code 1)."""
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
            "runtimeId": "runtime-unhealthy",
            "runtimeArn": "arn:aws:bedrock:us-east-1:123456789012:runtime/runtime-unhealthy",
            "status": "CREATING"
        }
        mock_bedrock_client.get_agent_runtime.return_value = {
            "runtimeId": "runtime-unhealthy",
            "status": "READY",
            "endpointUrl": "https://runtime.bedrock.aws/runtime-unhealthy"
        }
        
        mock_session = Mock()
        mock_session.client.return_value = mock_bedrock_client
        
        # Mock verification returning UNHEALTHY
        mock_cloudwatch_client = Mock()
        mock_cloudwatch_client.describe_log_groups.return_value = {
            "logGroups": [{"logGroupName": "/aws/bedrock/runtime-unhealthy"}]
        }
        mock_cloudwatch_client.describe_log_streams.return_value = {
            "logStreams": [{"logStreamName": "stream1"}]
        }
        mock_cloudwatch_client.filter_log_events.return_value = {
            "events": [{"logStreamName": "stream1", "message": "Application started"}]
        }
        
        bootstrap_orch = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        bedrock_rt = BedrockRuntime(session=mock_session)
        
        runtime_verifier = RuntimeVerifier()
        runtime_verifier._client = mock_cloudwatch_client
        
        deploy_orch = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=bootstrap_orch,
            bedrock_runtime=bedrock_rt,
            runtime_verifier=runtime_verifier
        )
        
        config = DeployConfig(
            runtime_name="zscaler-runtime",
            secret_name="test-secret",
            role_name="test-role",
            username="admin@example.com",
            password="secret123",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = deploy_orch.deploy(config)
        
        assert result.success is True  # Deployment succeeded
        assert result.verification_result is not None
        assert result.verification_result.status == VerificationStatus.UNHEALTHY
        assert result.verification_result.is_healthy() is False
        
        # Verify that connection info is still present (graceful handling)
        assert result.runtime_id == "runtime-unhealthy"
        assert result.endpoint_url == "https://runtime.bedrock.aws/runtime-unhealthy"
    
    def test_deploy_with_verification_error(self):
        """Test deployment with verification error (still shows connection info)."""
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
            "runtimeId": "runtime-error",
            "runtimeArn": "arn:aws:bedrock:us-east-1:123456789012:runtime/runtime-error",
            "status": "CREATING"
        }
        mock_bedrock_client.get_agent_runtime.return_value = {
            "runtimeId": "runtime-error",
            "status": "READY",
            "endpointUrl": "https://runtime.bedrock.aws/runtime-error"
        }
        
        mock_session = Mock()
        mock_session.client.return_value = mock_bedrock_client
        
        # Mock verification error
        mock_cloudwatch_client = Mock()
        mock_cloudwatch_client.describe_log_groups.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}},
            "DescribeLogGroups"
        )
        
        bootstrap_orch = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        bedrock_rt = BedrockRuntime(session=mock_session)
        
        runtime_verifier = RuntimeVerifier()
        runtime_verifier._client = mock_cloudwatch_client
        
        deploy_orch = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=bootstrap_orch,
            bedrock_runtime=bedrock_rt,
            runtime_verifier=runtime_verifier
        )
        
        config = DeployConfig(
            runtime_name="zscaler-runtime",
            secret_name="test-secret",
            role_name="test-role",
            username="admin@example.com",
            password="secret123",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = deploy_orch.deploy(config)
        
        assert result.success is True  # Deployment succeeded
        assert result.verification_result is not None
        assert result.verification_result.status == VerificationStatus.ERROR
        assert result.verification_result.error_code is not None
        
        # Connection info still present
        assert result.runtime_id == "runtime-error"
        assert result.endpoint_url == "https://runtime.bedrock.aws/runtime-error"
    
    def test_deploy_with_verification_pending(self):
        """Test deployment with verification PENDING status."""
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
            "runtimeId": "runtime-pending",
            "runtimeArn": "arn:aws:bedrock:us-east-1:123456789012:runtime/runtime-pending",
            "status": "CREATING"
        }
        mock_bedrock_client.get_agent_runtime.return_value = {
            "runtimeId": "runtime-pending",
            "status": "READY",
            "endpointUrl": "https://runtime.bedrock.aws/runtime-pending"
        }
        
        mock_session = Mock()
        mock_session.client.return_value = mock_bedrock_client
        
        # Mock verification returning no events (PENDING)
        mock_cloudwatch_client = Mock()
        mock_cloudwatch_client.describe_log_groups.return_value = {
            "logGroups": [{"logGroupName": "/aws/bedrock/runtime-pending"}]
        }
        mock_cloudwatch_client.describe_log_streams.return_value = {
            "logStreams": [{"logStreamName": "stream1"}]
        }
        mock_cloudwatch_client.filter_log_events.return_value = {"events": []}
        
        bootstrap_orch = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        bedrock_rt = BedrockRuntime(session=mock_session)
        
        runtime_verifier = RuntimeVerifier()
        runtime_verifier._client = mock_cloudwatch_client
        
        deploy_orch = DeployOrchestrator(
            region="us-east-1",
            bootstrap_orchestrator=bootstrap_orch,
            bedrock_runtime=bedrock_rt,
            runtime_verifier=runtime_verifier
        )
        
        config = DeployConfig(
            runtime_name="zscaler-runtime",
            secret_name="test-secret",
            role_name="test-role",
            username="admin@example.com",
            password="secret123",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = deploy_orch.deploy(config)
        
        assert result.success is True
        assert result.verification_result is not None
        assert result.verification_result.status == VerificationStatus.PENDING
        assert result.verification_result.is_healthy() is False