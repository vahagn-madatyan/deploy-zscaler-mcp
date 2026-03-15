"""Integration tests for S02 Bootstrap flow.

End-to-end tests exercising the full bootstrap flow with mocked AWS services.
Tests cover success paths, partial failures, rollback scenarios, and edge cases.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from botocore.exceptions import ClientError

from zscaler_mcp_deploy.bootstrap import BootstrapOrchestrator, BootstrapOrchestratorError
from zscaler_mcp_deploy.aws.secrets_manager import SecretsManager, SecretsManagerError
from zscaler_mcp_deploy.aws.iam_bootstrap import IAMBootstrap, IAMBootstrapError, TrustPolicyMismatchError
from zscaler_mcp_deploy.models import BootstrapConfig, BootstrapResult, SecretResult, IAMRoleResult
from zscaler_mcp_deploy.validators.aws import AWSSessionValidator


class TestBootstrapFullSuccessPath:
    """Tests for complete successful bootstrap flow."""
    
    def test_full_bootstrap_new_secret_new_role(self):
        """Test complete bootstrap creating both new secret and new role."""
        # Create mocks
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid", "Region us-east-1"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        secret_result = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test-secret-123",
            name="test-secret",
            version_id="v1",
            created=True,
            kms_key_id="alias/aws/secretsmanager"
        )
        mock_secrets_manager.create_or_use_secret.return_value = secret_result
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        role_result = IAMRoleResult(
            arn="arn:aws:iam::123456789:role/test-role",
            name="test-role",
            role_id="AROA1234567890EXAMPLE",
            created=True,
            trust_policy={"Version": "2012-10-17", "Statement": []}
        )
        mock_iam_bootstrap.create_or_use_execution_role.return_value = role_result
        
        # Create orchestrator with injected dependencies
        orchestrator = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        config = BootstrapConfig(
            secret_name="test-secret",
            role_name="test-role",
            username="admin@example.com",
            password="secret123",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = orchestrator.bootstrap_resources(config)
        
        assert result.success is True
        assert result.phase == "completed"
        assert result.secret_arn == secret_result.arn
        assert result.role_arn == role_result.arn
        assert result.secret_created is True
        assert result.role_created is True
        assert result.resource_ids == ["test-secret", "test-role"]
        
        # Verify all phases were called
        mock_validator.validate_session.assert_called_once_with(region="us-east-1")
        mock_secrets_manager.create_or_use_secret.assert_called_once()
        mock_iam_bootstrap.create_or_use_execution_role.assert_called_once()
    
    def test_full_bootstrap_existing_resources(self):
        """Test bootstrap when both resources already exist (idempotent)."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid", "Region us-east-1"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        secret_result = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789:secret:existing-secret",
            name="existing-secret",
            created=False  # Already existed
        )
        mock_secrets_manager.create_or_use_secret.return_value = secret_result
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        role_result = IAMRoleResult(
            arn="arn:aws:iam::123456789:role/existing-role",
            name="existing-role",
            created=False  # Already existed
        )
        mock_iam_bootstrap.create_or_use_execution_role.return_value = role_result
        
        orchestrator = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        config = BootstrapConfig(
            secret_name="existing-secret",
            role_name="existing-role",
            username="admin@example.com",
            password="secret123",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = orchestrator.bootstrap_resources(config)
        
        assert result.success is True
        assert result.secret_created is False
        assert result.role_created is False
        assert result.resource_ids == []  # No new resources created
    
    def test_full_bootstrap_mixed_existing_new(self):
        """Test bootstrap when secret exists but role is new."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid", "Region us-east-1"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        secret_result = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789:secret:existing-secret",
            name="existing-secret",
            created=False
        )
        mock_secrets_manager.create_or_use_secret.return_value = secret_result
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        role_result = IAMRoleResult(
            arn="arn:aws:iam::123456789:role/new-role",
            name="new-role",
            created=True
        )
        mock_iam_bootstrap.create_or_use_execution_role.return_value = role_result
        
        orchestrator = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        config = BootstrapConfig(
            secret_name="existing-secret",
            role_name="new-role",
            username="admin@example.com",
            password="secret123",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = orchestrator.bootstrap_resources(config)
        
        assert result.success is True
        assert result.secret_created is False
        assert result.role_created is True
        assert result.resource_ids == ["new-role"]  # Only role is new


class TestBootstrapPreflightFailures:
    """Tests for preflight validation failures."""
    
    def test_preflight_fails_no_aws_credentials(self):
        """Test bootstrap fails fast when AWS credentials are invalid."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (
            False, 
            ["Unable to locate credentials", "Region us-east-1"]
        )
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        
        orchestrator = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        config = BootstrapConfig(
            secret_name="test-secret",
            role_name="test-role",
            username="admin@example.com",
            password="secret123",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = orchestrator.bootstrap_resources(config)
        
        assert result.success is False
        assert result.phase == "preflight"
        assert "S02-003-PreflightFailed" in result.error_code
        assert result.secret_arn is None
        assert result.role_arn is None
        
        # Secret and role should not be created
        mock_secrets_manager.create_or_use_secret.assert_not_called()
        mock_iam_bootstrap.create_or_use_execution_role.assert_not_called()
    
    def test_preflight_fails_invalid_region(self):
        """Test bootstrap fails when region is invalid."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (
            False,
            ["Session valid", "Invalid region: invalid-region-1"]
        )
        
        orchestrator = BootstrapOrchestrator(
            region="invalid-region-1",
            validator=mock_validator,
            secrets_manager=Mock(),
            iam_bootstrap=Mock()
        )
        
        config = BootstrapConfig(
            secret_name="test-secret",
            role_name="test-role",
            username="admin@example.com",
            password="secret123",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = orchestrator.bootstrap_resources(config)
        
        assert result.success is False
        assert result.phase == "preflight"
        assert "credentials" in result.error_message.lower() or "region" in result.error_message.lower()


class TestBootstrapPartialFailuresWithRollback:
    """Tests for partial failure scenarios with rollback verification."""
    
    def test_role_failure_triggers_secret_rollback(self):
        """Test that secret is rolled back when role creation fails."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        secret_result = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test-secret",
            name="test-secret",
            version_id="v1",
            created=True
        )
        mock_secrets_manager.create_or_use_secret.return_value = secret_result
        mock_secrets_manager.delete_secret.return_value = None
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        error = IAMBootstrapError(
            message="Role creation failed: Access Denied",
            error_code="S02-002-AccessDenied"
        )
        mock_iam_bootstrap.create_or_use_execution_role.side_effect = error
        mock_iam_bootstrap.delete_role.return_value = None
        
        orchestrator = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        config = BootstrapConfig(
            secret_name="test-secret",
            role_name="test-role",
            username="admin@example.com",
            password="secret123",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = orchestrator.bootstrap_resources(config)
        
        assert result.success is False
        assert result.phase == "role"
        assert result.secret_created is True
        assert result.error_code == "S02-002-AccessDenied"
        assert "Rollback completed successfully" in result.error_message
        
        # Verify rollback was called
        mock_secrets_manager.delete_secret.assert_called_once_with(
            "test-secret",
            force_delete_without_recovery=True
        )
    
    def test_role_failure_no_rollback_for_existing_secret(self):
        """Test that existing secret is not deleted when role fails."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        secret_result = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789:secret:existing-secret",
            name="existing-secret",
            created=False  # Already existed
        )
        mock_secrets_manager.create_or_use_secret.return_value = secret_result
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        error = IAMBootstrapError(
            message="Role creation failed",
            error_code="S02-002"
        )
        mock_iam_bootstrap.create_or_use_execution_role.side_effect = error
        
        orchestrator = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        config = BootstrapConfig(
            secret_name="existing-secret",
            role_name="test-role",
            username="admin@example.com",
            password="secret123",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = orchestrator.bootstrap_resources(config)
        
        assert result.success is False
        # No rollback should happen since secret wasn't created
        mock_secrets_manager.delete_secret.assert_not_called()
        # Error message should NOT mention rollback
        assert "Rollback" not in result.error_message
    
    def test_partial_rollback_with_role_and_secret(self):
        """Test rollback deletes both role and secret when both were created."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        secret_result = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test-secret",
            name="test-secret",
            created=True
        )
        mock_secrets_manager.create_or_use_secret.return_value = secret_result
        mock_secrets_manager.delete_secret.return_value = None
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        role_result = IAMRoleResult(
            arn="arn:aws:iam::123456789:role:test-role",
            name="test-role",
            created=True
        )
        # First call succeeds, second fails (simulating update failure)
        mock_iam_bootstrap.create_or_use_execution_role.side_effect = [
            role_result,
            IAMBootstrapError("Update failed")
        ]
        mock_iam_bootstrap.delete_role.return_value = None
        
        orchestrator = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        config = BootstrapConfig(
            secret_name="test-secret",
            role_name="test-role",
            username="admin@example.com",
            password="secret123",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        # First bootstrap succeeds
        result1 = orchestrator.bootstrap_resources(config)
        assert result1.success is True
        
        # Reset for second call
        mock_secrets_manager.reset_mock()
        mock_iam_bootstrap.reset_mock()
        
        # Manually trigger rollback to test it works
        orchestrator._created_resources = [("secret", "test-secret"), ("role", "test-role")]
        success, errors = orchestrator.rollback()
        
        assert success is True
        assert errors == []
        
        # Verify deletion order: role first, then secret (reverse creation order)
        mock_iam_bootstrap.delete_role.assert_called_once_with("test-role")
        mock_secrets_manager.delete_secret.assert_called_once_with(
            "test-secret",
            force_delete_without_recovery=True
        )
    
    def test_rollback_failure_handling(self):
        """Test handling when rollback itself fails."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        secret_result = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test-secret",
            name="test-secret",
            created=True
        )
        mock_secrets_manager.create_or_use_secret.return_value = secret_result
        mock_secrets_manager.delete_secret.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Cannot delete secret"}},
            "DeleteSecret"
        )
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        mock_iam_bootstrap.create_or_use_execution_role.side_effect = IAMBootstrapError("Role failed")
        mock_iam_bootstrap.delete_role.return_value = None
        
        orchestrator = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        config = BootstrapConfig(
            secret_name="test-secret",
            role_name="test-role",
            username="admin@example.com",
            password="secret123",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = orchestrator.bootstrap_resources(config)
        
        assert result.success is False
        # Should mention rollback failure in error message
        assert "Rollback partially failed" in result.error_message
        assert "Cannot delete secret" in result.error_message


class TestBootstrapSecretFailures:
    """Tests for secret creation failure scenarios."""
    
    def test_secret_creation_fails_no_retry(self):
        """Test bootstrap stops when secret creation fails."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        error = SecretsManagerError(
            message="KMS key not found",
            error_code="S02-001-KMSNotFound"
        )
        mock_secrets_manager.create_or_use_secret.side_effect = error
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        
        orchestrator = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        config = BootstrapConfig(
            secret_name="test-secret",
            role_name="test-role",
            username="admin@example.com",
            password="secret123",
            api_key="a" * 32,
            cloud="zscaler",
            kms_key_id="arn:aws:kms:us-east-1:123456789:key/missing-key"
        )
        
        result = orchestrator.bootstrap_resources(config)
        
        assert result.success is False
        assert result.phase == "secret"
        assert result.error_code == "S02-001-KMSNotFound"
        assert "KMS key not found" in result.error_message
        
        # Role should not be attempted
        mock_iam_bootstrap.create_or_use_execution_role.assert_not_called()
    
    def test_secret_permission_denied(self):
        """Test handling of Secrets Manager permission denied."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        error = SecretsManagerError(
            message="User is not authorized to perform secretsmanager:CreateSecret",
            error_code="S02-001-AccessDenied"
        )
        mock_secrets_manager.create_or_use_secret.side_effect = error
        
        orchestrator = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=Mock()
        )
        
        config = BootstrapConfig(
            secret_name="test-secret",
            role_name="test-role",
            username="admin@example.com",
            password="secret123",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = orchestrator.bootstrap_resources(config)
        
        assert result.success is False
        assert "AccessDenied" in result.error_code


class TestBootstrapEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_bootstrap_with_all_optional_params(self):
        """Test bootstrap with all optional configuration parameters."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        secret_result = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test-secret",
            name="test-secret",
            created=True
        )
        mock_secrets_manager.create_or_use_secret.return_value = secret_result
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        role_result = IAMRoleResult(
            arn="arn:aws:iam::123456789:role/test-role",
            name="test-role",
            created=True
        )
        mock_iam_bootstrap.create_or_use_execution_role.return_value = role_result
        
        orchestrator = BootstrapOrchestrator(
            region="us-west-2",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        tags = [
            {"Key": "Environment", "Value": "Production"},
            {"Key": "Project", "Value": "ZscalerMCP"}
        ]
        
        config = BootstrapConfig(
            secret_name="test-secret",
            role_name="test-role",
            username="admin@company.com",
            password="SuperSecret123!",
            api_key="abcdef1234567890abcdef1234567890",
            cloud="zscalerthree",
            kms_key_id="arn:aws:kms:us-west-2:123456789:key/my-key",
            region="us-west-2",
            profile_name="production",
            description="Custom description for resources",
            tags=tags
        )
        
        result = orchestrator.bootstrap_resources(config)
        
        assert result.success is True
        
        # Verify all params passed to secrets manager
        call_kwargs = mock_secrets_manager.create_or_use_secret.call_args[1]
        assert call_kwargs["secret_name"] == "test-secret"
        assert call_kwargs["username"] == "admin@company.com"
        assert call_kwargs["password"] == "SuperSecret123!"
        assert call_kwargs["api_key"] == "abcdef1234567890abcdef1234567890"
        assert call_kwargs["cloud"] == "zscalerthree"
        assert call_kwargs["kms_key_id"] == "arn:aws:kms:us-west-2:123456789:key/my-key"
        assert call_kwargs["description"] == "Custom description for resources"
        assert call_kwargs["tags"] == tags
    
    def test_bootstrap_result_to_dict_serialization(self):
        """Test that BootstrapResult serializes correctly to dict."""
        result = BootstrapResult(
            secret_arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test",
            role_arn="arn:aws:iam::123456789:role/test",
            resource_ids=["test-secret", "test-role"],
            success=True,
            phase="completed",
            secret_created=True,
            role_created=True
        )
        
        d = result.to_dict()
        
        assert d["secret_arn"] == "arn:aws:secretsmanager:us-east-1:123456789:secret:test"
        assert d["role_arn"] == "arn:aws:iam::123456789:role/test"
        assert d["resource_ids"] == ["test-secret", "test-role"]
        assert d["success"] is True
        assert d["phase"] == "completed"
        assert d["secret_created"] is True
        assert d["role_created"] is True
    
    def test_multiple_bootstrap_runs_reset_state(self):
        """Test that multiple bootstrap runs properly reset resource tracking."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        mock_secrets_manager.create_or_use_secret.return_value = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test-secret",
            name="test-secret",
            created=True
        )
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        mock_iam_bootstrap.create_or_use_execution_role.return_value = IAMRoleResult(
            arn="arn:aws:iam::123456789:role/test-role",
            name="test-role",
            created=True
        )
        
        orchestrator = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        config = BootstrapConfig(
            secret_name="test-secret",
            role_name="test-role",
            username="admin@example.com",
            password="secret123",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        # First run
        result1 = orchestrator.bootstrap_resources(config)
        assert result1.success is True
        assert len(orchestrator.get_created_resources()) == 2
        
        # Second run should reset tracking
        result2 = orchestrator.bootstrap_resources(config)
        assert result2.success is True
        # Should still show 2 resources (new ones from second run)
        assert len(orchestrator.get_created_resources()) == 2
    
    def test_bootstrap_with_empty_description(self):
        """Test bootstrap handles empty/None description gracefully."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        mock_secrets_manager.create_or_use_secret.return_value = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test",
            name="test-secret",
            created=True
        )
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        mock_iam_bootstrap.create_or_use_execution_role.return_value = IAMRoleResult(
            arn="arn:aws:iam::123456789:role/test-role",
            name="test-role",
            created=True
        )
        
        orchestrator = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        # No description provided
        config = BootstrapConfig(
            secret_name="test-secret",
            role_name="test-role",
            username="admin@example.com",
            password="secret123",
            api_key="a" * 32,
            cloud="zscaler",
            description=None
        )
        
        result = orchestrator.bootstrap_resources(config)
        assert result.success is True
        
        # Should use default description
        call_kwargs = mock_secrets_manager.create_or_use_secret.call_args[1]
        assert "zscaler" in call_kwargs["description"].lower()


class TestBootstrapErrorPropagation:
    """Tests for error propagation between components."""
    
    def test_secrets_manager_error_propagates_with_code(self):
        """Test that Secrets Manager errors maintain their error codes."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        error = SecretsManagerError(
            message="Secret already exists with different value",
            error_code="S02-001-AlreadyExists"
        )
        mock_secrets_manager.create_or_use_secret.side_effect = error
        
        orchestrator = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=Mock()
        )
        
        config = BootstrapConfig(
            secret_name="test-secret",
            role_name="test-role",
            username="admin@example.com",
            password="secret123",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = orchestrator.bootstrap_resources(config)
        
        assert result.success is False
        assert result.error_code == "S02-001-AlreadyExists"
        assert result.phase == "secret"
    
    def test_iam_error_propagates_with_code(self):
        """Test that IAM errors maintain their error codes."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        mock_secrets_manager.create_or_use_secret.return_value = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test",
            name="test-secret",
            created=True
        )
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        error = IAMBootstrapError(
            message="Trust policy mismatch",
            error_code="S02-002-TrustMismatch"
        )
        mock_iam_bootstrap.create_or_use_execution_role.side_effect = error
        mock_iam_bootstrap.delete_role.return_value = None
        
        orchestrator = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        config = BootstrapConfig(
            secret_name="test-secret",
            role_name="test-role",
            username="admin@example.com",
            password="secret123",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = orchestrator.bootstrap_resources(config)
        
        assert result.success is False
        assert result.error_code == "S02-002-TrustMismatch"
        assert result.phase == "role"
    
    def test_error_without_code_gets_default(self):
        """Test that errors without codes get default codes assigned."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        error = SecretsManagerError(message="Generic error", error_code=None)
        mock_secrets_manager.create_or_use_secret.side_effect = error
        
        orchestrator = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=Mock()
        )
        
        config = BootstrapConfig(
            secret_name="test-secret",
            role_name="test-role",
            username="admin@example.com",
            password="secret123",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        result = orchestrator.bootstrap_resources(config)
        
        assert result.success is False
        assert "S02-001" in result.error_code  # Secret error code propagated


class TestBootstrapResourceOrdering:
    """Tests for resource creation and rollback ordering."""
    
    def test_resource_creation_order_secret_before_role(self):
        """Test that secret is always created before role."""
        creation_order = []
        
        def mock_create_secret(**kwargs):
            creation_order.append("secret")
            return SecretResult(
                arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test",
                name="test-secret",
                created=True
            )
        
        def mock_create_role(**kwargs):
            creation_order.append("role")
            return IAMRoleResult(
                arn="arn:aws:iam::123456789:role/test-role",
                name="test-role",
                created=True
            )
        
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        mock_secrets_manager.create_or_use_secret.side_effect = mock_create_secret
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        mock_iam_bootstrap.create_or_use_execution_role.side_effect = mock_create_role
        
        orchestrator = BootstrapOrchestrator(
            region="us-east-1",
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        config = BootstrapConfig(
            secret_name="test-secret",
            role_name="test-role",
            username="admin@example.com",
            password="secret123",
            api_key="a" * 32,
            cloud="zscaler"
        )
        
        orchestrator.bootstrap_resources(config)
        
        assert creation_order == ["secret", "role"]
    
    def test_rollback_order_reverses_creation(self):
        """Test that rollback deletes in reverse order of creation."""
        deletion_order = []
        
        def mock_delete_secret(name, **kwargs):
            deletion_order.append(f"secret:{name}")
        
        def mock_delete_role(name):
            deletion_order.append(f"role:{name}")
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        mock_secrets_manager.delete_secret.side_effect = mock_delete_secret
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        mock_iam_bootstrap.delete_role.side_effect = mock_delete_role
        
        orchestrator = BootstrapOrchestrator(
            region="us-east-1",
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        # Simulate resources were created
        orchestrator._created_resources = [
            ("secret", "first-secret"),
            ("role", "first-role"),
            ("secret", "second-secret"),
            ("role", "second-role")
        ]
        
        orchestrator.rollback()
        
        # Should delete in reverse order: second-role, second-secret, first-role, first-secret
        assert deletion_order == [
            "role:second-role",
            "secret:second-secret",
            "role:first-role",
            "secret:first-secret"
        ]


class TestBootstrapWithRealisticAWSResponses:
    """Tests with realistic AWS API response structures."""
    
    def test_bootstrap_with_realistic_secret_arn(self):
        """Test bootstrap handles realistic AWS secret ARN format."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Session valid"])
        
        mock_secrets_manager = Mock(spec=SecretsManager)
        # Realistic ARN format with AWS suffix
        secret_result = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789012:secret:prod/zscaler/credentials-AbCdEf",
            name="prod/zscaler/credentials",
            version_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            created=True,
            kms_key_id="arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012"
        )
        mock_secrets_manager.create_or_use_secret.return_value = secret_result
        
        mock_iam_bootstrap = Mock(spec=IAMBootstrap)
        mock_iam_bootstrap.create_or_use_execution_role.return_value = IAMRoleResult(
            arn="arn:aws:iam::123456789012:role/ZscalerMCPExecutionRole",
            name="ZscalerMCPExecutionRole",
            role_id="AROA1234567890EXAMPLE123",
            created=True
        )
        
        orchestrator = BootstrapOrchestrator(
            validator=mock_validator,
            secrets_manager=mock_secrets_manager,
            iam_bootstrap=mock_iam_bootstrap
        )
        
        config = BootstrapConfig(
            secret_name="prod/zscaler/credentials",
            role_name="ZscalerMCPExecutionRole",
            username="admin@company.com",
            password="SecureP@ssw0rd!",
            api_key="1234567890abcdef1234567890abcdef",
            cloud="zscaler"
        )
        
        result = orchestrator.bootstrap_resources(config)
        
        assert result.success is True
        assert "123456789012" in result.secret_arn  # Account ID present
        assert "123456789012" in result.role_arn
