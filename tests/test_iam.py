"""Tests for IAM permission validation."""

import pytest
from unittest.mock import patch, MagicMock
from zscaler_mcp_deploy.validators.iam import IAMPermissionValidator


class TestIAMPermissionValidator:
    """Test IAM permission validation functionality."""

    def test_init(self):
        """Test initialization of IAMPermissionValidator."""
        validator = IAMPermissionValidator()
        assert validator.profile_name is None
        assert validator.region is None
        assert validator.session is None

        validator = IAMPermissionValidator(profile_name="test-profile", region="us-east-1")
        assert validator.profile_name == "test-profile"
        assert validator.region == "us-east-1"

    def test_required_permissions_structure(self):
        """Test that required permissions are properly structured."""
        validator = IAMPermissionValidator()
        
        # Check that we have the expected services
        assert 'bedrock' in validator.REQUIRED_PERMISSIONS
        assert 'secretsmanager' in validator.REQUIRED_PERMISSIONS
        assert 'sts' in validator.REQUIRED_PERMISSIONS
        
        # Check that each service has actions
        for service, actions in validator.REQUIRED_PERMISSIONS.items():
            assert isinstance(actions, list)
            assert len(actions) > 0
            for action in actions:
                assert isinstance(action, str)
                assert ':' in action  # Should be in format service:action

    @patch('boto3.Session')
    def test_get_session(self, mock_session_class):
        """Test session creation."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        validator = IAMPermissionValidator()
        session = validator._get_session()
        
        assert session == mock_session
        mock_session_class.assert_called_once()

    @patch('boto3.Session')
    def test_get_session_with_profile(self, mock_session_class):
        """Test session creation with profile."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        validator = IAMPermissionValidator(profile_name="test-profile")
        session = validator._get_session()
        
        assert session == mock_session
        mock_session_class.assert_called_once_with(profile_name="test-profile")

    @patch('boto3.Session')
    def test_get_session_reuse(self, mock_session_class):
        """Test that session is reused on subsequent calls."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        validator = IAMPermissionValidator()
        session1 = validator._get_session()
        session2 = validator._get_session()
        
        assert session1 == session2
        assert session1 == mock_session
        mock_session_class.assert_called_once()  # Should only be called once

    @patch('boto3.Session')
    @patch('zscaler_mcp_deploy.validators.iam.IAMPermissionValidator._validate_bedrock_permissions')
    def test_validate_permissions_bedrock(self, mock_validate_bedrock, mock_session_class):
        """Test permission validation for Bedrock service."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        # Mock the validation result
        mock_validate_bedrock.return_value = (True, ['bedrock:ListFoundationModels'], [])
        
        validator = IAMPermissionValidator()
        is_valid, allowed, denied = validator.validate_permissions('bedrock', ['bedrock:ListFoundationModels'])
        
        assert is_valid is True
        assert allowed == ['bedrock:ListFoundationModels']
        assert denied == []
        mock_validate_bedrock.assert_called_once_with(['bedrock:ListFoundationModels'], mock_session)

    @patch('boto3.Session')
    @patch('zscaler_mcp_deploy.validators.iam.IAMPermissionValidator._validate_secretsmanager_permissions')
    def test_validate_permissions_secretsmanager(self, mock_validate_secretsmanager, mock_session_class):
        """Test permission validation for Secrets Manager service."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        # Mock the validation result
        mock_validate_secretsmanager.return_value = (True, ['secretsmanager:GetSecretValue'], [])
        
        validator = IAMPermissionValidator()
        is_valid, allowed, denied = validator.validate_permissions('secretsmanager', ['secretsmanager:GetSecretValue'])
        
        assert is_valid is True
        assert allowed == ['secretsmanager:GetSecretValue']
        assert denied == []
        mock_validate_secretsmanager.assert_called_once_with(['secretsmanager:GetSecretValue'], mock_session)

    @patch('boto3.Session')
    @patch('zscaler_mcp_deploy.validators.iam.IAMPermissionValidator._validate_sts_permissions')
    def test_validate_permissions_sts(self, mock_validate_sts, mock_session_class):
        """Test permission validation for STS service."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        # Mock the validation result
        mock_validate_sts.return_value = (True, ['sts:AssumeRole'], [])
        
        validator = IAMPermissionValidator()
        is_valid, allowed, denied = validator.validate_permissions('sts', ['sts:AssumeRole'])
        
        assert is_valid is True
        assert allowed == ['sts:AssumeRole']
        assert denied == []
        mock_validate_sts.assert_called_once_with(['sts:AssumeRole'], mock_session)

    @patch('boto3.Session')
    def test_validate_permissions_unknown_service(self, mock_session_class):
        """Test permission validation for unknown service."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        validator = IAMPermissionValidator()
        is_valid, allowed, denied = validator.validate_permissions('unknown-service', ['unknown-service:SomeAction'])
        
        # For unknown services, we should get some result (implementation-dependent)
        assert isinstance(is_valid, bool)
        assert isinstance(allowed, list)
        assert isinstance(denied, list)

    @patch('boto3.Session')
    def test_validate_required_permissions(self, mock_session_class):
        """Test validation of all required permissions."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        validator = IAMPermissionValidator()
        
        # Mock the individual service validation methods to return successful results
        with patch.object(validator, 'validate_permissions', return_value=(True, ['action1'], [])) as mock_validate:
            results = validator.validate_required_permissions()
            
            # Should have results for all required services
            assert 'bedrock' in results
            assert 'secretsmanager' in results
            assert 'sts' in results
            
            # Each service should have valid results
            for service_result in results.values():
                assert service_result['valid'] is True
                assert service_result['allowed'] == ['action1']
                assert service_result['denied'] == []

    def test_get_permission_validation_summary_success(self):
        """Test successful permission validation summary."""
        validator = IAMPermissionValidator()
        
        # Mock the validate_required_permissions method
        with patch.object(validator, 'validate_required_permissions', return_value={
            'bedrock': {'valid': True, 'allowed': [], 'denied': []},
            'secretsmanager': {'valid': True, 'allowed': [], 'denied': []},
            'sts': {'valid': True, 'allowed': [], 'denied': []}
        }):
            is_valid, summary = validator.get_permission_validation_summary()
            
            assert is_valid is True
            assert "All required AWS permissions are available" in summary

    def test_get_permission_validation_summary_failure(self):
        """Test failed permission validation summary."""
        validator = IAMPermissionValidator()
        
        # Mock the validate_required_permissions method with some denied actions
        with patch.object(validator, 'validate_required_permissions', return_value={
            'bedrock': {'valid': False, 'allowed': ['bedrock:ListFoundationModels'], 'denied': ['bedrock:InvokeModel']},
            'secretsmanager': {'valid': True, 'allowed': [], 'denied': []},
            'sts': {'valid': False, 'allowed': [], 'denied': ['sts:AssumeRole']}
        }):
            is_valid, summary = validator.get_permission_validation_summary()
            
            assert is_valid is False
            assert "Missing permissions" in summary
            assert "bedrock:" in summary
            assert "sts:" in summary