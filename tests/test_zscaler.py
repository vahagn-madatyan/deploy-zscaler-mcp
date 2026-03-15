"""
Test suite for Zscaler credential validation.
"""
import pytest
from unittest.mock import Mock, patch
import requests

from zscaler_mcp_deploy.validators.zscaler import ZscalerCredentialValidator, ZscalerCloud


class TestZscalerCloud:
    """Test Zscaler cloud constants."""
    
    def test_cloud_endpoints(self):
        """Test that all cloud endpoints are defined."""
        expected_clouds = {
            'zscaler', 'zscalerone', 'zscalertwo', 'zscalerthree', 
            'zscalergov', 'zscalerten'
        }
        assert set(ZscalerCloud.CLOUDS.keys()) == expected_clouds
        
        # Check that all URLs start with https
        for url in ZscalerCloud.CLOUDS.values():
            assert url.startswith('https://')


class TestZscalerCredentialValidator:
    """Test Zscaler credential validator."""
    
    def test_init_with_defaults(self):
        """Test initialization with default values."""
        validator = ZscalerCredentialValidator()
        assert validator.cloud == 'zscaler'
        assert validator.username is None
        assert validator.password is None
        assert validator.api_key is None
        assert validator.obfuscate is True
        assert validator.base_url == ZscalerCloud.CLOUDS['zscaler']
    
    def test_init_with_custom_values(self):
        """Test initialization with custom values."""
        validator = ZscalerCredentialValidator(
            cloud='zscalerone',
            username='test@example.com',
            password='testpass',
            api_key='a' * 32,
            obfuscate=False
        )
        assert validator.cloud == 'zscalerone'
        assert validator.username == 'test@example.com'
        assert validator.password == 'testpass'
        assert validator.api_key == 'a' * 32
        assert validator.obfuscate is False
        assert validator.base_url == ZscalerCloud.CLOUDS['zscalerone']
    
    def test_obfuscate_string(self):
        """Test string obfuscation."""
        validator = ZscalerCredentialValidator()
        
        # Test normal string - 8 chars, show 4 at start/end = all asterisks (4+4=8)
        result = validator._obfuscate_string('test1234')
        assert result == '********'
        
        # Test longer string - should show first 4 and last 4
        result = validator._obfuscate_string('test12345')
        assert result == 'test*2345'
        
        # Test short string
        result = validator._obfuscate_string('abc')
        assert result == '***'
        
        # Test empty string
        result = validator._obfuscate_string('')
        assert result == ''
    
    def test_obfuscate_creds(self):
        """Test credential obfuscation."""
        # Test with obfuscation enabled (default)
        validator = ZscalerCredentialValidator(
            username='test@example.com',
            api_key='a1b2c3d4e5f678901234567890abcdef'
        )
        obfuscated = validator._obfuscate_creds()
        assert obfuscated['username'] == 'test********.com'
        assert obfuscated['cloud'] == 'zscaler'
        assert obfuscated['api_key_length'] == 32
        
        # Test with obfuscation disabled
        validator_no_obfuscate = ZscalerCredentialValidator(
            username='test@example.com',
            api_key='a1b2c3d4e5f678901234567890abcdef',
            obfuscate=False
        )
        clear_creds = validator_no_obfuscate._obfuscate_creds()
        assert clear_creds['username'] == 'test@example.com'
        assert clear_creds['cloud'] == 'zscaler'
        assert clear_creds['api_key_length'] == 32
    
    def test_validate_credential_format_success(self):
        """Test successful credential format validation."""
        validator = ZscalerCredentialValidator(
            username='test@example.com',
            password='validpassword',
            api_key='a1b2c3d4e5f678901234567890abcdef'
        )
        is_valid, message = validator.validate_credential_format()
        assert is_valid is True
        assert message == "Zscaler credential format is valid"
    
    def test_validate_credential_format_missing_username(self):
        """Test validation with missing username."""
        validator = ZscalerCredentialValidator(
            password='validpassword',
            api_key='a1b2c3d4e5f678901234567890abcdef'
        )
        is_valid, message = validator.validate_credential_format()
        assert is_valid is False
        assert message == "Zscaler username is required"
    
    def test_validate_credential_format_missing_password(self):
        """Test validation with missing password."""
        validator = ZscalerCredentialValidator(
            username='test@example.com',
            api_key='a1b2c3d4e5f678901234567890abcdef'
        )
        is_valid, message = validator.validate_credential_format()
        assert is_valid is False
        assert message == "Zscaler password is required"
    
    def test_validate_credential_format_missing_api_key(self):
        """Test validation with missing API key."""
        validator = ZscalerCredentialValidator(
            username='test@example.com',
            password='validpassword'
        )
        is_valid, message = validator.validate_credential_format()
        assert is_valid is False
        assert message == "Zscaler API key is required"
    
    def test_validate_credential_format_invalid_email(self):
        """Test validation with invalid email format."""
        validator = ZscalerCredentialValidator(
            username='invalid-email',
            password='validpassword',
            api_key='a1b2c3d4e5f678901234567890abcdef'
        )
        is_valid, message = validator.validate_credential_format()
        assert is_valid is False
        assert "Invalid username format" in message
    
    def test_validate_credential_format_invalid_api_key(self):
        """Test validation with invalid API key format."""
        validator = ZscalerCredentialValidator(
            username='test@example.com',
            password='validpassword',
            api_key='invalid-key'
        )
        is_valid, message = validator.validate_credential_format()
        assert is_valid is False
        assert "Invalid API key format" in message
    
    @patch('requests.Session.get')
    def test_validate_connectivity_success(self, mock_get):
        """Test successful connectivity validation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        validator = ZscalerCredentialValidator()
        is_valid, message = validator.validate_connectivity()
        
        assert is_valid is True
        assert "Successfully connected" in message
        mock_get.assert_called_once_with(
            f"{validator.base_url}/api/v1/status",
            timeout=10
        )
    
    @patch('requests.Session.get')
    def test_validate_connectivity_401_response(self, mock_get):
        """Test connectivity validation with 401 response."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        validator = ZscalerCredentialValidator()
        is_valid, message = validator.validate_connectivity()
        
        assert is_valid is True
        assert "Successfully connected" in message
    
    @patch('requests.Session.get')
    def test_validate_connectivity_timeout(self, mock_get):
        """Test connectivity validation with timeout."""
        mock_get.side_effect = requests.exceptions.Timeout()
        
        validator = ZscalerCredentialValidator()
        is_valid, message = validator.validate_connectivity(timeout=5)
        
        assert is_valid is False
        assert "timed out" in message
    
    @patch('requests.Session.get')
    def test_validate_connectivity_connection_error(self, mock_get):
        """Test connectivity validation with connection error."""
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        validator = ZscalerCredentialValidator()
        is_valid, message = validator.validate_connectivity()
        
        assert is_valid is False
        assert "Failed to connect" in message
    
    @patch('requests.Session.post')
    def test_authenticate_success(self, mock_post):
        """Test successful authentication."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'JSESSIONID': 'test-session-id'}
        mock_post.return_value = mock_response
        
        validator = ZscalerCredentialValidator(
            username='test@example.com',
            password='testpass',
            api_key='a1b2c3d4e5f678901234567890abcdef'
        )
        is_valid, message, session_id = validator.authenticate()
        
        assert is_valid is True
        assert "Successfully authenticated" in message
        assert session_id == 'test-session-id'
        mock_post.assert_called_once()
    
    @patch('requests.Session.post')
    def test_authenticate_401_response(self, mock_post):
        """Test authentication with 401 response."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        
        validator = ZscalerCredentialValidator(
            username='test@example.com',
            password='testpass',
            api_key='a1b2c3d4e5f678901234567890abcdef'
        )
        is_valid, message, session_id = validator.authenticate()
        
        assert is_valid is False
        assert "Invalid credentials" in message
        assert session_id is None
    
    @patch('requests.Session.post')
    def test_authenticate_timeout(self, mock_post):
        """Test authentication timeout."""
        mock_post.side_effect = requests.exceptions.Timeout()
        
        validator = ZscalerCredentialValidator(
            username='test@example.com',
            password='testpass',
            api_key='a1b2c3d4e5f678901234567890abcdef'
        )
        is_valid, message, session_id = validator.authenticate()
        
        assert is_valid is False
        assert "timed out" in message
        assert session_id is None


if __name__ == "__main__":
    pytest.main([__file__])