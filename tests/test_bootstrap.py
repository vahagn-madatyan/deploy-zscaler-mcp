"""Tests for Bootstrap Orchestrator module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

from zscaler_mcp_deploy.bootstrap import (
    BootstrapOrchestrator,
    BootstrapOrchestratorError,
    BootstrapResult,
    BootstrapConfig,
)
from zscaler_mcp_deploy.aws.secrets_manager import SecretsManager, SecretsManagerError
from zscaler_mcp_deploy.aws.iam_bootstrap import IAMBootstrap, IAMBootstrapError
from zscaler_mcp_deploy.models import SecretResult, IAMRoleResult
from zscaler_mcp_deploy.validators.aws import AWSSessionValidator


class TestBootstrapConfig:
    """Tests for BootstrapConfig dataclass."""
    
    def test_bootstrap_config_creation(self):
        """Test creating a BootstrapConfig with all fields."""
        config = BootstrapConfig(
            secret_name="test-secret",
            role_name="test-role",
            username="admin",
            password="pass123",
            api_key="key123",
            cloud="zscaler",
            kms_key_id="alias/my-key",
            region="us-east-1",
            profile_name="default",
            description="Test description",
            tags=[{"Key": "Env", "Value": "Test"}]
        )
        
        assert config.secret_name == "test-secret"
        assert config.role_name == "test-role"
        assert config.username == "admin"
        assert config.password == "pass123"
        assert config.api_key == "key123"
        assert config.cloud == "zscaler"
    
    def test_bootstrap_config_defaults(self):
        """Test BootstrapConfig with default values."""
        config = BootstrapConfig(
            secret_name="test-secret",
            role_name="test-role",
            username="admin",
            password="pass123",
            api_key="key123",
            cloud="zscaler"
        )
        
        assert config.kms_key_id is None
        assert config.region is None
        assert config.profile_name is None


class TestBootstrapResult:
    """Tests for BootstrapResult dataclass."""
    
    def test_bootstrap_result_creation(self):
        """Test creating a BootstrapResult with all fields."""
        result = BootstrapResult(
            secret_arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test",
            role_arn="arn:aws:iam::123456789:role/test-role",
            resource_ids=["test-secret", "test-role"],
            success=True,
            phase="completed",
            secret_created=True,
            role_created=True
        )
        
        assert result.secret_arn == "arn:aws:secretsmanager:us-east-1:123456789:secret:test"
        assert result.role_arn == "arn:aws:iam::123456789:role/test-role"
        assert result.success is True
        assert result.phase == "completed"
    
    def test_bootstrap_result_defaults(self):
        """Test BootstrapResult with default values."""
        result = BootstrapResult()
        
        assert result.secret_arn is None
        assert result.role_arn is None
        assert result.success is False
        assert result.resource_ids == []
    
    def test_bootstrap_result_to_dict(self):
        """Test converting BootstrapResult to dictionary."""
        result = BootstrapResult(
            secret_arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test",
            role_arn="arn:aws:iam::123456789:role/test-role",
            resource_ids=["test-secret"],
            success=True,
            phase="completed",
            secret_created=True,
            role_created=True
        )
        
        d = result.to_dict()
        assert d["secret_arn"] == "arn:aws:secretsmanager:us-east-1:123456789:secret:test"
        assert d["role_arn"] == "arn:aws:iam::123456789:role/test-role"
        assert d["success"] is True


class TestBootstrapOrchestratorInit:
    """Tests for BootstrapOrchestrator initialization."""
    
    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        orch = BootstrapOrchestrator()
        assert orch._region is None
        assert orch._profile_name is None
        assert orch._created_resources == []
    
    def test_init_with_region_and_profile(self):
        """Test initialization with region and profile."""
        orch = BootstrapOrchestrator(region="us-west-2", profile_name="my-profile")
        assert orch._region == "us-west-2"
        assert orch._profile_name == "my-profile"
    
    def test_init_with_injected_dependencies(self):
        """Test initialization with injected dependencies."""
        mock_sm = Mock(spec=SecretsManager)
        mock_iam = Mock(spec=IAMBootstrap)
        mock_validator = Mock(spec=AWSSessionValidator)
        
        orch = BootstrapOrchestrator(
            secrets_manager=mock_sm,
            iam_bootstrap=mock_iam,
            validator=mock_validator
        )
        
        assert orch._secrets_manager is mock_sm
        assert orch._iam_bootstrap is mock_iam
        assert orch._validator is mock_validator


class TestBootstrapOrchestratorPreflight:
    """Tests for preflight validation."""
    
    def test_preflight_validation_pass(self):
        """Test successful preflight validation."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["Credentials valid"])
        
        orch = BootstrapOrchestrator(validator=mock_validator)
        is_valid, messages = orch._run_preflight_validation()
        
        assert is_valid is True
        assert "Credentials valid" in messages
    
    def test_preflight_validation_fail(self):
        """Test failed preflight validation."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (False, ["No credentials found"])
        
        orch = BootstrapOrchestrator(validator=mock_validator)
        is_valid, messages = orch._run_preflight_validation()
        
        assert is_valid is False
    
    def test_bootstrap_fails_on_preflight_failure(self):
        """Test bootstrap returns error when preflight fails."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (False, ["Invalid credentials"])
        
        orch = BootstrapOrchestrator(validator=mock_validator)
        
        config = BootstrapConfig(
            secret_name="test-secret",
            role_name="test-role",
            username="admin",
            password="pass",
            api_key="key",
            cloud="zscaler"
        )
        
        result = orch.bootstrap_resources(config)
        
        assert result.success is False
        assert result.error_code == "S02-003-PreflightFailed"
        assert result.phase == "preflight"


class TestBootstrapOrchestratorSuccess:
    """Tests for successful bootstrap scenarios."""
    
    def test_bootstrap_success_new_resources(self):
        """Test successful bootstrap with new resources."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["OK"])
        
        mock_sm = Mock(spec=SecretsManager)
        mock_sm.create_or_use_secret.return_value = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test",
            name="test-secret",
            created=True
        )
        
        mock_iam = Mock(spec=IAMBootstrap)
        mock_iam.create_or_use_execution_role.return_value = IAMRoleResult(
            arn="arn:aws:iam::123456789:role/test-role",
            name="test-role",
            created=True
        )
        
        orch = BootstrapOrchestrator(
            validator=mock_validator,
            secrets_manager=mock_sm,
            iam_bootstrap=mock_iam
        )
        
        config = BootstrapConfig(
            secret_name="test-secret",
            role_name="test-role",
            username="admin",
            password="pass",
            api_key="key",
            cloud="zscaler"
        )
        
        result = orch.bootstrap_resources(config)
        
        assert result.success is True
        assert result.secret_created is True
        assert result.role_created is True
        assert result.resource_ids == ["test-secret", "test-role"]
    
    def test_bootstrap_success_existing_resources(self):
        """Test successful bootstrap with existing resources."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["OK"])
        
        mock_sm = Mock(spec=SecretsManager)
        mock_sm.create_or_use_secret.return_value = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test",
            name="test-secret",
            created=False
        )
        
        mock_iam = Mock(spec=IAMBootstrap)
        mock_iam.create_or_use_execution_role.return_value = IAMRoleResult(
            arn="arn:aws:iam::123456789:role/test-role",
            name="test-role",
            created=False
        )
        
        orch = BootstrapOrchestrator(
            validator=mock_validator,
            secrets_manager=mock_sm,
            iam_bootstrap=mock_iam
        )
        
        config = BootstrapConfig(
            secret_name="test-secret",
            role_name="test-role",
            username="admin",
            password="pass",
            api_key="key",
            cloud="zscaler"
        )
        
        result = orch.bootstrap_resources(config)
        
        assert result.success is True
        assert result.secret_created is False
        assert result.role_created is False
        assert result.resource_ids == []
    
    def test_bootstrap_mixed_existing_and_new(self):
        """Test bootstrap with one existing and one new resource."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["OK"])
        
        mock_sm = Mock(spec=SecretsManager)
        mock_sm.create_or_use_secret.return_value = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test",
            name="test-secret",
            created=False
        )
        
        mock_iam = Mock(spec=IAMBootstrap)
        mock_iam.create_or_use_execution_role.return_value = IAMRoleResult(
            arn="arn:aws:iam::123456789:role/test-role",
            name="test-role",
            created=True
        )
        
        orch = BootstrapOrchestrator(
            validator=mock_validator,
            secrets_manager=mock_sm,
            iam_bootstrap=mock_iam
        )
        
        config = BootstrapConfig(
            secret_name="test-secret",
            role_name="test-role",
            username="admin",
            password="pass",
            api_key="key",
            cloud="zscaler"
        )
        
        result = orch.bootstrap_resources(config)
        
        assert result.success is True
        assert result.secret_created is False
        assert result.role_created is True
        assert result.resource_ids == ["test-role"]


class TestBootstrapOrchestratorFailure:
    """Tests for bootstrap failure scenarios."""
    
    def test_bootstrap_secret_creation_failure(self):
        """Test bootstrap fails when secret creation fails."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["OK"])
        
        mock_sm = Mock(spec=SecretsManager)
        error = SecretsManagerError(
            message="Permission denied",
            error_code="S02-001-AccessDenied"
        )
        mock_sm.create_or_use_secret.side_effect = error
        
        orch = BootstrapOrchestrator(
            validator=mock_validator,
            secrets_manager=mock_sm
        )
        
        config = BootstrapConfig(
            secret_name="test-secret",
            role_name="test-role",
            username="admin",
            password="pass",
            api_key="key",
            cloud="zscaler"
        )
        
        result = orch.bootstrap_resources(config)
        
        assert result.success is False
        assert result.phase == "secret"
        assert result.error_code == "S02-001-AccessDenied"
    
    def test_bootstrap_role_creation_failure_with_rollback(self):
        """Test bootstrap rolls back secret when role creation fails."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["OK"])
        
        mock_sm = Mock(spec=SecretsManager)
        mock_sm.create_or_use_secret.return_value = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test",
            name="test-secret",
            created=True
        )
        mock_sm.delete_secret = Mock()
        
        mock_iam = Mock(spec=IAMBootstrap)
        error = IAMBootstrapError(
            message="Role creation failed",
            error_code="S02-002-EntityAlreadyExists"
        )
        mock_iam.create_or_use_execution_role.side_effect = error
        mock_iam.delete_role = Mock()
        
        orch = BootstrapOrchestrator(
            validator=mock_validator,
            secrets_manager=mock_sm,
            iam_bootstrap=mock_iam
        )
        
        config = BootstrapConfig(
            secret_name="test-secret",
            role_name="test-role",
            username="admin",
            password="pass",
            api_key="key",
            cloud="zscaler"
        )
        
        result = orch.bootstrap_resources(config)
        
        assert result.success is False
        assert result.phase == "role"
        assert "Rollback completed" in result.error_message
        mock_sm.delete_secret.assert_called_once_with("test-secret", force_delete_without_recovery=True)
    
    def test_bootstrap_role_failure_no_rollback_for_existing_secret(self):
        """Test no rollback when role fails but secret was existing."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["OK"])
        
        mock_sm = Mock(spec=SecretsManager)
        mock_sm.create_or_use_secret.return_value = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test",
            name="test-secret",
            created=False  # Already existed
        )
        mock_sm.delete_secret = Mock()
        
        mock_iam = Mock(spec=IAMBootstrap)
        error = IAMBootstrapError(
            message="Role creation failed",
            error_code="S02-002-AccessDenied"
        )
        mock_iam.create_or_use_execution_role.side_effect = error
        
        orch = BootstrapOrchestrator(
            validator=mock_validator,
            secrets_manager=mock_sm,
            iam_bootstrap=mock_iam
        )
        
        config = BootstrapConfig(
            secret_name="test-secret",
            role_name="test-role",
            username="admin",
            password="pass",
            api_key="key",
            cloud="zscaler"
        )
        
        result = orch.bootstrap_resources(config)
        
        assert result.success is False
        mock_sm.delete_secret.assert_not_called()


class TestBootstrapOrchestratorRollback:
    """Tests for rollback functionality."""
    
    def test_rollback_deletes_resources_in_reverse_order(self):
        """Test rollback deletes resources in correct order."""
        mock_iam = Mock(spec=IAMBootstrap)
        mock_iam.delete_role = Mock()
        
        mock_sm = Mock(spec=SecretsManager)
        mock_sm.delete_secret = Mock()
        
        orch = BootstrapOrchestrator(
            iam_bootstrap=mock_iam,
            secrets_manager=mock_sm
        )
        
        # Simulate resources were created
        orch._created_resources = [("secret", "test-secret"), ("role", "test-role")]
        
        success, errors = orch.rollback()
        
        assert success is True
        assert errors == []
        # Role should be deleted first (reverse order)
        mock_iam.delete_role.assert_called_once_with("test-role")
        mock_sm.delete_secret.assert_called_once_with("test-secret", force_delete_without_recovery=True)
    
    def test_rollback_with_secret_only(self):
        """Test rollback when only secret was created."""
        mock_sm = Mock(spec=SecretsManager)
        mock_sm.delete_secret = Mock()
        
        mock_iam = Mock(spec=IAMBootstrap)
        mock_iam.delete_role = Mock()
        
        orch = BootstrapOrchestrator(
            iam_bootstrap=mock_iam,
            secrets_manager=mock_sm
        )
        
        orch._created_resources = [("secret", "test-secret")]
        
        success, errors = orch.rollback()
        
        assert success is True
        mock_sm.delete_secret.assert_called_once_with("test-secret", force_delete_without_recovery=True)
        mock_iam.delete_role.assert_not_called()
    
    def test_rollback_handles_deletion_errors(self):
        """Test rollback continues even if one deletion fails."""
        mock_iam = Mock(spec=IAMBootstrap)
        mock_iam.delete_role = Mock(side_effect=Exception("Role deletion failed"))
        
        mock_sm = Mock(spec=SecretsManager)
        mock_sm.delete_secret = Mock()
        
        orch = BootstrapOrchestrator(
            iam_bootstrap=mock_iam,
            secrets_manager=mock_sm
        )
        
        orch._created_resources = [("secret", "test-secret"), ("role", "test-role")]
        
        success, errors = orch.rollback()
        
        assert success is False
        assert len(errors) == 1
        assert "Role deletion failed" in errors[0]
        # Secret should still be deleted after role fails
        mock_sm.delete_secret.assert_called_once()
    
    def test_rollback_clears_resources_on_success(self):
        """Test that created_resources is cleared after successful rollback."""
        mock_iam = Mock(spec=IAMBootstrap)
        mock_iam.delete_role = Mock()
        
        mock_sm = Mock(spec=SecretsManager)
        mock_sm.delete_secret = Mock()
        
        orch = BootstrapOrchestrator(
            iam_bootstrap=mock_iam,
            secrets_manager=mock_sm
        )
        
        orch._created_resources = [("secret", "test-secret")]
        
        success, errors = orch.rollback()
        
        assert success is True
        assert orch._created_resources == []
    
    def test_get_created_resources_returns_copy(self):
        """Test get_created_resources returns a copy of the list."""
        orch = BootstrapOrchestrator()
        orch._created_resources = [("secret", "test-secret")]
        
        resources = orch.get_created_resources()
        resources.append(("role", "test-role"))
        
        # Original should be unchanged
        assert orch._created_resources == [("secret", "test-secret")]


class TestBootstrapOrchestratorIntegration:
    """Integration-style tests for the full bootstrap flow."""
    
    def test_full_flow_new_secret_new_role(self):
        """Test complete flow with both resources new."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["OK"])
        
        mock_sm = Mock(spec=SecretsManager)
        mock_sm.create_or_use_secret.return_value = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test",
            name="test-secret",
            created=True
        )
        
        mock_iam = Mock(spec=IAMBootstrap)
        mock_iam.create_or_use_execution_role.return_value = IAMRoleResult(
            arn="arn:aws:iam::123456789:role/test-role",
            name="test-role",
            created=True
        )
        
        orch = BootstrapOrchestrator(
            validator=mock_validator,
            secrets_manager=mock_sm,
            iam_bootstrap=mock_iam
        )
        
        config = BootstrapConfig(
            secret_name="prod/zscaler/creds",
            role_name="zscaler-bedrock-role",
            username="admin@example.com",
            password="secret123",
            api_key="apikey123",
            cloud="zscaler",
            kms_key_id="alias/zscaler-key",
            description="Production Zscaler credentials"
        )
        
        result = orch.bootstrap_resources(config)
        
        assert result.success is True
        assert result.secret_arn == "arn:aws:secretsmanager:us-east-1:123456789:secret:test"
        assert result.role_arn == "arn:aws:iam::123456789:role/test-role"
        
        # Verify secret creation called with correct args
        mock_sm.create_or_use_secret.assert_called_once()
        call_kwargs = mock_sm.create_or_use_secret.call_args[1]
        assert call_kwargs["secret_name"] == "prod/zscaler/creds"
        assert call_kwargs["username"] == "admin@example.com"
        assert call_kwargs["cloud"] == "zscaler"
        assert call_kwargs["kms_key_id"] == "alias/zscaler-key"
        
        # Verify role creation called with secret ARN
        mock_iam.create_or_use_execution_role.assert_called_once()
        role_call_kwargs = mock_iam.create_or_use_execution_role.call_args[1]
        assert role_call_kwargs["role_name"] == "zscaler-bedrock-role"
        assert role_call_kwargs["secret_arn"] == "arn:aws:secretsmanager:us-east-1:123456789:secret:test"
    
    def test_bootstrap_resets_resource_tracking(self):
        """Test that bootstrap resets resource tracking on each call."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["OK"])
        
        mock_sm = Mock(spec=SecretsManager)
        mock_sm.create_or_use_secret.return_value = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test",
            name="test-secret",
            created=True
        )
        
        mock_iam = Mock(spec=IAMBootstrap)
        mock_iam.create_or_use_execution_role.return_value = IAMRoleResult(
            arn="arn:aws:iam::123456789:role/test-role",
            name="test-role",
            created=True
        )
        
        orch = BootstrapOrchestrator(
            validator=mock_validator,
            secrets_manager=mock_sm,
            iam_bootstrap=mock_iam
        )
        
        # Pre-populate with old resources
        orch._created_resources = [("secret", "old-secret")]
        
        config = BootstrapConfig(
            secret_name="test-secret",
            role_name="test-role",
            username="admin",
            password="pass",
            api_key="key",
            cloud="zscaler"
        )
        
        result = orch.bootstrap_resources(config)
        
        assert result.success is True
        assert result.resource_ids == ["test-secret", "test-role"]
        assert orch._created_resources == [("secret", "test-secret"), ("role", "test-role")]


class TestBootstrapOrchestratorConfigPassing:
    """Tests for proper config passing to underlying services."""
    
    def test_secret_manager_receives_all_config(self):
        """Test all config fields passed to secrets manager."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["OK"])
        
        mock_sm = Mock(spec=SecretsManager)
        mock_sm.create_or_use_secret.return_value = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test",
            name="test-secret",
            created=True
        )
        
        mock_iam = Mock(spec=IAMBootstrap)
        mock_iam.create_or_use_execution_role.return_value = IAMRoleResult(
            arn="arn:aws:iam::123456789:role/test-role",
            name="test-role",
            created=True
        )
        
        orch = BootstrapOrchestrator(
            validator=mock_validator,
            secrets_manager=mock_sm,
            iam_bootstrap=mock_iam
        )
        
        config = BootstrapConfig(
            secret_name="my-secret",
            role_name="my-role",
            username="user@example.com",
            password="mypassword",
            api_key="myapikey",
            cloud="zscalerone",
            kms_key_id="alias/custom-key",
            description="Custom description",
            tags=[{"Key": "Team", "Value": "Platform"}]
        )
        
        orch.bootstrap_resources(config)
        
        # Verify secrets manager called with all fields
        mock_sm.create_or_use_secret.assert_called_once_with(
            secret_name="my-secret",
            username="user@example.com",
            password="mypassword",
            api_key="myapikey",
            cloud="zscalerone",
            kms_key_id="alias/custom-key",
            description="Custom description",
            tags=[{"Key": "Team", "Value": "Platform"}]
        )
    
    def test_iam_bootstrap_receives_config(self):
        """Test all config fields passed to IAM bootstrap."""
        mock_validator = Mock(spec=AWSSessionValidator)
        mock_validator.validate_session.return_value = (True, ["OK"])
        
        mock_sm = Mock(spec=SecretsManager)
        mock_sm.create_or_use_secret.return_value = SecretResult(
            arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test",
            name="test-secret",
            created=True
        )
        
        mock_iam = Mock(spec=IAMBootstrap)
        mock_iam.create_or_use_execution_role.return_value = IAMRoleResult(
            arn="arn:aws:iam::123456789:role/test-role",
            name="test-role",
            created=True
        )
        
        orch = BootstrapOrchestrator(
            validator=mock_validator,
            secrets_manager=mock_sm,
            iam_bootstrap=mock_iam
        )
        
        config = BootstrapConfig(
            secret_name="test-secret",
            role_name="my-custom-role",
            username="admin",
            password="pass",
            api_key="key",
            cloud="zscaler",
            description="Role description",
            tags=[{"Key": "Env", "Value": "Prod"}]
        )
        
        orch.bootstrap_resources(config)
        
        # Verify IAM bootstrap called correctly
        mock_iam.create_or_use_execution_role.assert_called_once_with(
            role_name="my-custom-role",
            secret_arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test",
            description="Role description",
            tags=[{"Key": "Env", "Value": "Prod"}]
        )
