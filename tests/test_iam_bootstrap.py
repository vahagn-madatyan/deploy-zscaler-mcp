"""Tests for IAM Bootstrap module."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from botocore.exceptions import ClientError

from zscaler_mcp_deploy.aws.iam_bootstrap import (
    IAMBootstrap,
    IAMBootstrapError,
    TrustPolicyMismatchError,
    IAMRoleResult,
)
from zscaler_mcp_deploy.models import IAMRoleResult as IAMRoleResultModel


class TestIAMRoleResult:
    """Tests for IAMRoleResult dataclass."""
    
    def test_iam_role_result_creation(self):
        """Test creating an IAMRoleResult with all fields."""
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "bedrock.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        result = IAMRoleResult(
            arn="arn:aws:iam::123456789:role/test-role",
            name="test-role",
            role_id="AROA1234567890EXAMPLE",
            created=True,
            trust_policy=trust_policy
        )
        
        assert result.arn == "arn:aws:iam::123456789:role/test-role"
        assert result.name == "test-role"
        assert result.role_id == "AROA1234567890EXAMPLE"
        assert result.created is True
        assert result.trust_policy == trust_policy
    
    def test_iam_role_result_defaults(self):
        """Test IAMRoleResult with default values."""
        result = IAMRoleResult(
            arn="arn:aws:iam::123456789:role/test-role",
            name="test-role"
        )
        
        assert result.role_id is None
        assert result.created is False
        assert result.trust_policy is None
    
    def test_iam_role_result_to_dict(self):
        """Test converting IAMRoleResult to dictionary."""
        trust_policy = {"Version": "2012-10-17", "Statement": []}
        
        result = IAMRoleResult(
            arn="arn:aws:iam::123456789:role/test-role",
            name="test-role",
            role_id="AROA1234567890EXAMPLE",
            created=True,
            trust_policy=trust_policy
        )
        
        d = result.to_dict()
        assert d["arn"] == "arn:aws:iam::123456789:role/test-role"
        assert d["name"] == "test-role"
        assert d["role_id"] == "AROA1234567890EXAMPLE"
        assert d["created"] is True
        assert d["trust_policy"] == trust_policy


class TestIAMBootstrapInitialization:
    """Tests for IAMBootstrap initialization."""
    
    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        iam = IAMBootstrap()
        assert iam._region is None
        assert iam._profile_name is None
        assert iam._session is None
        assert iam._client is None
    
    def test_init_with_region(self):
        """Test initialization with region parameter."""
        iam = IAMBootstrap(region="us-west-2")
        assert iam._region == "us-west-2"
        assert iam._profile_name is None
    
    def test_init_with_profile(self):
        """Test initialization with profile name."""
        iam = IAMBootstrap(profile_name="my-profile")
        assert iam._profile_name == "my-profile"
        assert iam._region is None
    
    def test_init_with_session(self):
        """Test initialization with pre-configured session."""
        mock_session = Mock()
        iam = IAMBootstrap(session=mock_session)
        assert iam._session is mock_session
    
    @patch("zscaler_mcp_deploy.aws.iam_bootstrap.boto3.Session")
    def test_lazy_session_creation_no_profile(self, mock_session_class):
        """Test lazy session creation without profile."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        iam = IAMBootstrap(region="us-east-1")
        session = iam.session
        
        mock_session_class.assert_called_once_with(region_name="us-east-1")
        assert session is mock_session
    
    @patch("zscaler_mcp_deploy.aws.iam_bootstrap.boto3.Session")
    def test_lazy_session_creation_with_profile(self, mock_session_class):
        """Test lazy session creation with profile."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        iam = IAMBootstrap(region="us-east-1", profile_name="my-profile")
        session = iam.session
        
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
        
        iam = IAMBootstrap(session=mock_session)
        client = iam.client
        
        mock_session.client.assert_called_once_with("iam")
        assert client is mock_client
    
    def test_session_caching(self):
        """Test that session is cached after first access."""
        mock_session = Mock()
        iam = IAMBootstrap(session=mock_session)
        
        s1 = iam.session
        s2 = iam.session
        
        assert s1 is s2 is mock_session
    
    def test_client_caching(self):
        """Test that client is cached after first access."""
        mock_session = Mock()
        mock_client = Mock()
        mock_session.client.return_value = mock_client
        
        iam = IAMBootstrap(session=mock_session)
        
        c1 = iam.client
        c2 = iam.client
        
        assert c1 is c2 is mock_client
        mock_session.client.assert_called_once_with("iam")


class TestTrustPolicyGeneration:
    """Tests for trust policy generation."""
    
    def test_generate_trust_policy_structure(self):
        """Test trust policy has correct structure."""
        iam = IAMBootstrap()
        policy = iam._generate_trust_policy()
        
        assert policy["Version"] == "2012-10-17"
        assert len(policy["Statement"]) == 1
        
        statement = policy["Statement"][0]
        assert statement["Effect"] == "Allow"
        assert statement["Principal"]["Service"] == "bedrock.amazonaws.com"
        assert statement["Action"] == "sts:AssumeRole"


class TestInlinePolicyGeneration:
    """Tests for inline policy generation."""
    
    def test_generate_inline_policy_structure(self):
        """Test inline policy has correct structure."""
        iam = IAMBootstrap()
        secret_arn = "arn:aws:secretsmanager:us-east-1:123456789:secret:test-secret"
        policy = iam._generate_inline_policy(secret_arn)
        
        assert policy["Version"] == "2012-10-17"
        assert len(policy["Statement"]) == 2
    
    def test_generate_inline_policy_secrets_manager(self):
        """Test inline policy includes Secrets Manager permissions."""
        iam = IAMBootstrap()
        secret_arn = "arn:aws:secretsmanager:us-east-1:123456789:secret:test-secret"
        policy = iam._generate_inline_policy(secret_arn)
        
        secrets_statement = policy["Statement"][0]
        assert secrets_statement["Effect"] == "Allow"
        assert "secretsmanager:GetSecretValue" in secrets_statement["Action"]
        assert secrets_statement["Resource"] == secret_arn
    
    def test_generate_inline_policy_cloudwatch(self):
        """Test inline policy includes CloudWatch Logs permissions."""
        iam = IAMBootstrap()
        secret_arn = "arn:aws:secretsmanager:us-east-1:123456789:secret:test-secret"
        policy = iam._generate_inline_policy(secret_arn)
        
        logs_statement = policy["Statement"][1]
        assert logs_statement["Effect"] == "Allow"
        assert "logs:CreateLogGroup" in logs_statement["Action"]
        assert "logs:CreateLogStream" in logs_statement["Action"]
        assert "logs:PutLogEvents" in logs_statement["Action"]
        assert "arn:aws:logs:*:*:log-group:/aws/bedrock/*" in logs_statement["Resource"]


class TestTrustPolicyValidation:
    """Tests for trust policy validation."""
    
    def test_validate_trust_policy_valid(self):
        """Test validation passes for valid trust policy."""
        iam = IAMBootstrap()
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "bedrock.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        assert iam._validate_trust_policy(policy, "bedrock.amazonaws.com") is True
    
    def test_validate_trust_policy_list_service(self):
        """Test validation passes when Service is a list."""
        iam = IAMBootstrap()
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": ["bedrock.amazonaws.com", "lambda.amazonaws.com"]},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        assert iam._validate_trust_policy(policy, "bedrock.amazonaws.com") is True
    
    def test_validate_trust_policy_mismatch(self):
        """Test validation fails for mismatched principal."""
        iam = IAMBootstrap()
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        assert iam._validate_trust_policy(policy, "bedrock.amazonaws.com") is False
    
    def test_validate_trust_policy_deny_statement(self):
        """Test validation skips Deny statements."""
        iam = IAMBootstrap()
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Deny",
                    "Principal": {"Service": "bedrock.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        assert iam._validate_trust_policy(policy, "bedrock.amazonaws.com") is False
    
    def test_validate_trust_policy_wrong_action(self):
        """Test validation fails for wrong action."""
        iam = IAMBootstrap()
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "bedrock.amazonaws.com"},
                    "Action": "sts:TagSession"
                }
            ]
        }
        
        assert iam._validate_trust_policy(policy, "bedrock.amazonaws.com") is False


class TestCreateOrUseExecutionRole:
    """Tests for create_or_use_execution_role method."""
    
    @patch.object(IAMBootstrap, '_wait_for_propagation')
    def test_create_new_role_success(self, mock_wait):
        """Test creating a new role successfully."""
        mock_client = Mock()
        mock_client.create_role.return_value = {
            "Role": {
                "Arn": "arn:aws:iam::123456789:role/zscaler-bedrock-role",
                "RoleName": "zscaler-bedrock-role",
                "RoleId": "AROA1234567890EXAMPLE"
            }
        }
        mock_client.put_role_policy.return_value = {}
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        iam = IAMBootstrap(session=mock_session)
        secret_arn = "arn:aws:secretsmanager:us-east-1:123456789:secret:zscaler-creds"
        
        result = iam.create_or_use_execution_role(
            role_name="zscaler-bedrock-role",
            secret_arn=secret_arn
        )
        
        # Verify result
        assert result.arn == "arn:aws:iam::123456789:role/zscaler-bedrock-role"
        assert result.name == "zscaler-bedrock-role"
        assert result.role_id == "AROA1234567890EXAMPLE"
        assert result.created is True
        assert result.trust_policy is not None
        
        # Verify create_role call
        call_args = mock_client.create_role.call_args[1]
        assert call_args["RoleName"] == "zscaler-bedrock-role"
        assert "AssumeRolePolicyDocument" in call_args
        assert call_args["Description"] == "Execution role for Bedrock AgentCore - zscaler-bedrock-role"
        
        # Verify inline policy attached
        policy_args = mock_client.put_role_policy.call_args[1]
        assert policy_args["RoleName"] == "zscaler-bedrock-role"
        assert policy_args["PolicyName"] == "zscaler-bedrock-role-bedrock-policy"
        
        # Verify wait was called
        mock_wait.assert_called_once()
    
    @patch.object(IAMBootstrap, '_wait_for_propagation')
    def test_create_role_with_custom_description(self, mock_wait):
        """Test creating a role with custom description."""
        mock_client = Mock()
        mock_client.create_role.return_value = {
            "Role": {
                "Arn": "arn:aws:iam::123456789:role/test-role",
                "RoleName": "test-role",
                "RoleId": "AROA1234567890EXAMPLE"
            }
        }
        mock_client.put_role_policy.return_value = {}
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        iam = IAMBootstrap(session=mock_session)
        
        iam.create_or_use_execution_role(
            role_name="test-role",
            secret_arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test",
            description="My custom role description"
        )
        
        call_args = mock_client.create_role.call_args[1]
        assert call_args["Description"] == "My custom role description"
    
    @patch.object(IAMBootstrap, '_wait_for_propagation')
    def test_create_role_with_tags(self, mock_wait):
        """Test creating a role with tags."""
        mock_client = Mock()
        mock_client.create_role.return_value = {
            "Role": {
                "Arn": "arn:aws:iam::123456789:role/test-role",
                "RoleName": "test-role",
                "RoleId": "AROA1234567890EXAMPLE"
            }
        }
        mock_client.put_role_policy.return_value = {}
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        iam = IAMBootstrap(session=mock_session)
        
        tags = [
            {"Key": "Environment", "Value": "Production"},
            {"Key": "Project", "Value": "ZscalerMCP"}
        ]
        
        iam.create_or_use_execution_role(
            role_name="test-role",
            secret_arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test",
            tags=tags
        )
        
        call_args = mock_client.create_role.call_args[1]
        assert call_args["Tags"] == tags
    
    def test_handle_existing_role(self):
        """Test handling when role already exists."""
        mock_client = Mock()
        
        # First call raises EntityAlreadyExists
        error_response = {
            "Error": {
                "Code": "EntityAlreadyExists",
                "Message": "Role with name test-role already exists"
            }
        }
        mock_client.create_role.side_effect = ClientError(error_response, "CreateRole")
        
        # get_role returns existing role
        mock_client.get_role.return_value = {
            "Role": {
                "Arn": "arn:aws:iam::123456789:role/test-role",
                "RoleName": "test-role",
                "RoleId": "AROA1234567890EXAMPLE",
                "AssumeRolePolicyDocument": {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"Service": "bedrock.amazonaws.com"},
                            "Action": "sts:AssumeRole"
                        }
                    ]
                }
            }
        }
        mock_client.put_role_policy.return_value = {}
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        iam = IAMBootstrap(session=mock_session)
        secret_arn = "arn:aws:secretsmanager:us-east-1:123456789:secret:test"
        
        result = iam.create_or_use_execution_role(
            role_name="test-role",
            secret_arn=secret_arn
        )
        
        # Verify result indicates existing role
        assert result.arn == "arn:aws:iam::123456789:role/test-role"
        assert result.name == "test-role"
        assert result.role_id == "AROA1234567890EXAMPLE"
        assert result.created is False
        
        # Verify get_role was called
        mock_client.get_role.assert_called_once_with(RoleName="test-role")
    
    def test_trust_policy_mismatch_error(self):
        """Test error when existing role has incompatible trust policy."""
        mock_client = Mock()
        
        # First call raises EntityAlreadyExists
        error_response = {
            "Error": {
                "Code": "EntityAlreadyExists",
                "Message": "Role with name test-role already exists"
            }
        }
        mock_client.create_role.side_effect = ClientError(error_response, "CreateRole")
        
        # get_role returns role with wrong trust policy (lambda instead of bedrock)
        mock_client.get_role.return_value = {
            "Role": {
                "Arn": "arn:aws:iam::123456789:role/test-role",
                "RoleName": "test-role",
                "RoleId": "AROA1234567890EXAMPLE",
                "AssumeRolePolicyDocument": {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"Service": "lambda.amazonaws.com"},
                            "Action": "sts:AssumeRole"
                        }
                    ]
                }
            }
        }
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        iam = IAMBootstrap(session=mock_session)
        
        with pytest.raises(TrustPolicyMismatchError) as exc_info:
            iam.create_or_use_execution_role(
                role_name="test-role",
                secret_arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test"
            )
        
        assert "S02-002-TrustMismatch" in str(exc_info.value.error_code)
        assert "lambda.amazonaws.com" in str(exc_info.value)
        assert "bedrock.amazonaws.com" in str(exc_info.value)
    
    def test_create_role_other_error(self):
        """Test handling of other ClientErrors during create."""
        mock_client = Mock()
        
        error_response = {
            "Error": {
                "Code": "AccessDenied",
                "Message": "User is not authorized to perform operation"
            }
        }
        mock_client.create_role.side_effect = ClientError(error_response, "CreateRole")
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        iam = IAMBootstrap(session=mock_session)
        
        with pytest.raises(IAMBootstrapError) as exc_info:
            iam.create_or_use_execution_role(
                role_name="test-role",
                secret_arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test"
            )
        
        assert "S02-002-AccessDenied" in str(exc_info.value.error_code)


class TestPropagationWait:
    """Tests for IAM propagation wait logic."""
    
    @patch('time.sleep')
    def test_wait_for_propagation(self, mock_sleep):
        """Test propagation wait with exponential backoff."""
        iam = IAMBootstrap()
        iam._wait_for_propagation()
        
        # Should sleep at least 2 times with exponential backoff
        assert mock_sleep.call_count >= 2
        
        # With 3 retries and backoff base 2: 1s + 2s + 4s = 7s minimum
        # Implementation caps at PROPAGATION_WAIT_SECONDS (15s)
        total_wait = sum(call_args[0][0] for call_args in mock_sleep.call_args_list)
        assert total_wait >= 7  # 2^0 + 2^1 + 2^2
    
    @patch('time.sleep')
    def test_wait_respects_max_retries(self, mock_sleep):
        """Test propagation wait respects max retries."""
        iam = IAMBootstrap()
        iam._wait_for_propagation()
        
        # Should not exceed max retries
        assert mock_sleep.call_count <= iam.PROPAGATION_MAX_RETRIES


class TestGetRole:
    """Tests for get_role method."""
    
    def test_get_role_success(self):
        """Test getting an existing role."""
        mock_client = Mock()
        mock_client.get_role.return_value = {
            "Role": {
                "Arn": "arn:aws:iam::123456789:role/test-role",
                "RoleName": "test-role",
                "RoleId": "AROA1234567890EXAMPLE",
                "AssumeRolePolicyDocument": {
                    "Version": "2012-10-17",
                    "Statement": []
                }
            }
        }
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        iam = IAMBootstrap(session=mock_session)
        result = iam.get_role("test-role")
        
        assert result is not None
        assert result.arn == "arn:aws:iam::123456789:role/test-role"
        assert result.name == "test-role"
        assert result.role_id == "AROA1234567890EXAMPLE"
        assert result.created is False
    
    def test_get_role_not_found(self):
        """Test getting a non-existent role returns None."""
        mock_client = Mock()
        error_response = {
            "Error": {
                "Code": "NoSuchEntity",
                "Message": "Role not found"
            }
        }
        mock_client.get_role.side_effect = ClientError(error_response, "GetRole")
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        iam = IAMBootstrap(session=mock_session)
        result = iam.get_role("nonexistent-role")
        
        assert result is None
    
    def test_get_role_error(self):
        """Test error handling when getting role fails."""
        mock_client = Mock()
        error_response = {
            "Error": {
                "Code": "AccessDenied",
                "Message": "Not authorized"
            }
        }
        mock_client.get_role.side_effect = ClientError(error_response, "GetRole")
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        iam = IAMBootstrap(session=mock_session)
        
        with pytest.raises(IAMBootstrapError) as exc_info:
            iam.get_role("test-role")
        
        assert "S02-002-AccessDenied" in str(exc_info.value.error_code)


class TestDeleteRole:
    """Tests for delete_role method."""
    
    def test_delete_role_success(self):
        """Test deleting a role successfully."""
        mock_client = Mock()
        mock_client.delete_role_policy.return_value = {}
        mock_client.delete_role.return_value = {}
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        iam = IAMBootstrap(session=mock_session)
        iam.delete_role("test-role")
        
        # Verify inline policy deleted first
        mock_client.delete_role_policy.assert_called_once_with(
            RoleName="test-role",
            PolicyName="test-role-bedrock-policy"
        )
        
        # Verify role deleted
        mock_client.delete_role.assert_called_once_with(RoleName="test-role")
    
    def test_delete_role_no_policy(self):
        """Test deleting role when inline policy doesn't exist."""
        mock_client = Mock()
        error_response = {
            "Error": {
                "Code": "NoSuchEntity",
                "Message": "Policy not found"
            }
        }
        mock_client.delete_role_policy.side_effect = ClientError(error_response, "DeleteRolePolicy")
        mock_client.delete_role.return_value = {}
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        iam = IAMBootstrap(session=mock_session)
        iam.delete_role("test-role")
        
        # Should still delete the role
        mock_client.delete_role.assert_called_once_with(RoleName="test-role")
    
    def test_delete_role_error(self):
        """Test error handling during role deletion."""
        mock_client = Mock()
        mock_client.delete_role_policy.return_value = {}
        error_response = {
            "Error": {
                "Code": "AccessDenied",
                "Message": "Not authorized"
            }
        }
        mock_client.delete_role.side_effect = ClientError(error_response, "DeleteRole")
        
        mock_session = Mock()
        mock_session.client.return_value = mock_client
        
        iam = IAMBootstrap(session=mock_session)
        
        with pytest.raises(IAMBootstrapError) as exc_info:
            iam.delete_role("test-role")
        
        assert "S02-002-AccessDenied" in str(exc_info.value.error_code)


class TestIAMBootstrapError:
    """Tests for IAMBootstrapError exception."""
    
    def test_error_default_code(self):
        """Test error with default error code."""
        error = IAMBootstrapError("Test error message")
        assert error.message == "Test error message"
        assert error.error_code == "S02-002"
        assert error.category.value == "aws_permissions"
        assert error.severity.value == "error"
    
    def test_error_custom_code(self):
        """Test error with custom error code."""
        error = IAMBootstrapError(
            "Test error message",
            error_code="S02-002-Custom"
        )
        assert error.error_code == "S02-002-Custom"
    
    def test_error_with_context(self):
        """Test error with context."""
        context = {"role_name": "test-role", "region": "us-east-1"}
        error = IAMBootstrapError(
            "Test error message",
            context=context
        )
        assert error.context == context
    
    def test_trust_policy_mismatch_error(self):
        """Test TrustPolicyMismatchError creation."""
        error = TrustPolicyMismatchError(
            role_name="test-role",
            expected_principal="bedrock.amazonaws.com",
            actual_principal="lambda.amazonaws.com"
        )
        
        assert error.error_code == "S02-002-TrustMismatch"
        assert "test-role" in error.message
        assert "bedrock.amazonaws.com" in error.message
        assert "lambda.amazonaws.com" in error.message
        assert error.context["role_name"] == "test-role"
        assert error.context["expected_principal"] == "bedrock.amazonaws.com"
        assert error.context["actual_principal"] == "lambda.amazonaws.com"
