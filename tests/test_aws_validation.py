"""Tests for AWS session validation."""

import pytest
from unittest.mock import patch, MagicMock
from zscaler_mcp_deploy.validators.aws import AWSSessionValidator


class TestAWSSessionValidator:
    """Test AWS session validation functionality."""

    def test_init(self):
        """Test initialization of AWSSessionValidator."""
        validator = AWSSessionValidator()
        assert validator.profile_name is None
        assert validator.region is None
        assert validator.session is None

        validator = AWSSessionValidator(profile_name="test-profile", region="us-east-1")
        assert validator.profile_name == "test-profile"
        assert validator.region == "us-east-1"

    @patch('boto3.Session')
    def test_validate_credentials_success(self, mock_session_class):
        """Test successful credential validation."""
        # Setup mock
        mock_session = MagicMock()
        mock_sts = MagicMock()
        mock_identity = {
            'Arn': 'arn:aws:iam::123456789012:user/test-user',
            'Account': '123456789012'
        }
        mock_sts.get_caller_identity.return_value = mock_identity
        mock_session.client.return_value = mock_sts
        mock_session_class.return_value = mock_session

        validator = AWSSessionValidator()
        is_valid, message = validator.validate_credentials()

        assert is_valid is True
        assert "Authenticated as arn:aws:iam::123456789012:user/test-user" in message

    @patch('boto3.Session')
    def test_validate_credentials_profile_not_found(self, mock_session_class):
        """Test credential validation with profile not found."""
        from botocore.exceptions import ProfileNotFound
        mock_session_class.side_effect = ProfileNotFound(profile='nonexistent')

        validator = AWSSessionValidator(profile_name="nonexistent")
        is_valid, message = validator.validate_credentials()

        assert is_valid is False
        assert "profile 'nonexistent' not found" in message

    @patch('boto3.Session')
    def test_validate_credentials_no_credentials(self, mock_session_class):
        """Test credential validation with no credentials."""
        from botocore.exceptions import NoCredentialsError
        mock_session_class.side_effect = NoCredentialsError()

        validator = AWSSessionValidator()
        is_valid, message = validator.validate_credentials()

        assert is_valid is False
        assert "No AWS credentials found" in message

    @patch('boto3.Session')
    def test_validate_credentials_partial_credentials(self, mock_session_class):
        """Test credential validation with partial credentials."""
        from botocore.exceptions import PartialCredentialsError
        mock_session_class.side_effect = PartialCredentialsError(provider='test', cred_var='AWS_SECRET_ACCESS_KEY')

        validator = AWSSessionValidator()
        is_valid, message = validator.validate_credentials()

        assert is_valid is False
        assert "Incomplete AWS credentials" in message

    @patch('boto3.Session')
    def test_validate_credentials_credential_retrieval_error(self, mock_session_class):
        """Test credential validation with credential retrieval error."""
        from botocore.exceptions import CredentialRetrievalError
        mock_session_class.side_effect = CredentialRetrievalError(provider='test', error_msg='test error')

        validator = AWSSessionValidator()
        is_valid, message = validator.validate_credentials()

        assert is_valid is False
        assert "Failed to retrieve AWS credentials" in message

    @patch('boto3.Session')
    def test_validate_credentials_client_error_signature(self, mock_session_class):
        """Test credential validation with signature error."""
        from botocore.exceptions import ClientError
        error_response = {
            'Error': {
                'Code': 'SignatureDoesNotMatch',
                'Message': 'The request signature we calculated does not match'
            }
        }
        mock_session_class.side_effect = ClientError(error_response, 'GetCallerIdentity')

        validator = AWSSessionValidator()
        is_valid, message = validator.validate_credentials()

        assert is_valid is False
        assert "AWS signature validation failed" in message

    @patch('boto3.Session')
    def test_validate_credentials_client_error_invalid_key(self, mock_session_class):
        """Test credential validation with invalid access key."""
        from botocore.exceptions import ClientError
        error_response = {
            'Error': {
                'Code': 'InvalidAccessKeyId',
                'Message': 'The AWS Access Key Id you provided does not exist'
            }
        }
        mock_session_class.side_effect = ClientError(error_response, 'GetCallerIdentity')

        validator = AWSSessionValidator()
        is_valid, message = validator.validate_credentials()

        assert is_valid is False
        assert "Invalid AWS access key ID" in message

    @patch('boto3.Session')
    def test_validate_credentials_client_error_access_denied(self, mock_session_class):
        """Test credential validation with access denied."""
        from botocore.exceptions import ClientError
        error_response = {
            'Error': {
                'Code': 'AccessDenied',
                'Message': 'User is not authorized to perform this operation'
            }
        }
        mock_session_class.side_effect = ClientError(error_response, 'GetCallerIdentity')

        validator = AWSSessionValidator()
        is_valid, message = validator.validate_credentials()

        assert is_valid is False
        assert "insufficient permissions" in message

    def test_validate_region_success(self):
        """Test successful region validation."""
        validator = AWSSessionValidator(region="us-east-1")
        is_valid, message = validator.validate_region()

        assert is_valid is True
        assert "supports Amazon Bedrock" in message

    def test_validate_region_unsupported(self):
        """Test validation of unsupported region."""
        validator = AWSSessionValidator(region="eu-north-1")
        is_valid, message = validator.validate_region()

        assert is_valid is False
        assert "does not support Amazon Bedrock" in message
        assert "Supported regions:" in message

    def test_validate_region_missing(self):
        """Test validation without region specified."""
        validator = AWSSessionValidator()
        is_valid, message = validator.validate_region()

        assert is_valid is False
        assert "No AWS region specified" in message

    def test_get_available_regions(self):
        """Test getting available Bedrock regions."""
        validator = AWSSessionValidator()
        regions = validator.get_available_regions()
        
        assert isinstance(regions, list)
        assert len(regions) > 0
        assert "us-east-1" in regions
        assert regions == sorted(regions)  # Should be sorted

    def test_prompt_for_region(self):
        """Test interactive region selection."""
        validator = AWSSessionValidator()
        regions = validator.get_available_regions()
        
        # Test that we get a list of regions
        assert isinstance(regions, list)
        assert len(regions) > 0
        
        # Test that the prompt method exists
        assert hasattr(validator, 'prompt_for_region')

    @patch('boto3.Session')
    def test_validate_session_comprehensive_success(self, mock_session_class):
        """Test comprehensive session validation success."""
        # Setup mock
        mock_session = MagicMock()
        mock_sts = MagicMock()
        mock_identity = {
            'Arn': 'arn:aws:iam::123456789012:user/test-user',
            'Account': '123456789012'
        }
        mock_sts.get_caller_identity.return_value = mock_identity
        mock_session.client.return_value = mock_sts
        mock_session_class.return_value = mock_session
        mock_session.region_name = "us-east-1"

        validator = AWSSessionValidator(region="us-east-1")
        is_valid, messages = validator.validate_session()

        assert is_valid is True
        assert len(messages) == 2
        assert any("Authenticated as" in msg for msg in messages)
        assert any("supports Amazon Bedrock" in msg for msg in messages)

    @patch('boto3.Session')
    def test_validate_session_credential_failure(self, mock_session_class):
        """Test comprehensive session validation with credential failure."""
        from botocore.exceptions import NoCredentialsError
        mock_session_class.side_effect = NoCredentialsError()

        validator = AWSSessionValidator()
        is_valid, messages = validator.validate_session()

        assert is_valid is False
        assert len(messages) == 1
        assert "No AWS credentials found" in messages[0]

    @patch('boto3.Session')
    def test_validate_session_region_failure(self, mock_session_class):
        """Test comprehensive session validation with region failure."""
        # Setup successful credential validation but unsupported region
        mock_session = MagicMock()
        mock_sts = MagicMock()
        mock_identity = {
            'Arn': 'arn:aws:iam::123456789012:user/test-user',
            'Account': '123456789012'
        }
        mock_sts.get_caller_identity.return_value = mock_identity
        mock_session.client.return_value = mock_sts
        mock_session_class.return_value = mock_session
        mock_session.region_name = "eu-north-1"

        validator = AWSSessionValidator(region="eu-north-1")
        is_valid, messages = validator.validate_session()

        assert is_valid is False
        assert len(messages) == 2
        assert any("Authenticated as" in msg for msg in messages)
        assert any("does not support Amazon Bedrock" in msg for msg in messages)