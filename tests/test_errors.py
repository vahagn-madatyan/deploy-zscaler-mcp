"""
Test suite for error messaging system.
"""
import pytest
from zscaler_mcp_deploy.errors import (
    ErrorMessage,
    ZscalerMCPError,
    AWSCredentialsError,
    AWSRegionError,
    AWSPermissionsError,
    ZscalerCredentialsError,
    ZscalerConnectivityError,
    ZscalerAuthenticationError,
    ErrorCategory,
    ErrorSeverity
)
from zscaler_mcp_deploy.messages import ErrorMessageCatalog, UserGuidance


class TestErrorMessage:
    """Test ErrorMessage data class."""
    
    def test_error_message_creation(self):
        """Test creating an error message."""
        error_msg = ErrorMessage(
            category=ErrorCategory.AWS_CREDENTIALS,
            severity=ErrorSeverity.ERROR,
            title="Test Error",
            description="This is a test error",
            remediation="Fix the test error",
            context={"test": "value"},
            error_code="TEST_ERROR",
            fix_commands=["echo 'fix'"]
        )
        
        assert error_msg.category == ErrorCategory.AWS_CREDENTIALS
        assert error_msg.severity == ErrorSeverity.ERROR
        assert error_msg.title == "Test Error"
        assert error_msg.description == "This is a test error"
        assert error_msg.remediation == "Fix the test error"
        assert error_msg.context == {"test": "value"}
        assert error_msg.error_code == "TEST_ERROR"
        assert error_msg.fix_commands == ["echo 'fix'"]
    
    def test_error_message_to_dict(self):
        """Test converting error message to dictionary."""
        error_msg = ErrorMessage(
            category=ErrorCategory.AWS_CREDENTIALS,
            severity=ErrorSeverity.ERROR,
            title="Test Error",
            description="This is a test error",
            remediation="Fix the test error"
        )
        
        result = error_msg.to_dict()
        assert result["category"] == "aws_credentials"
        assert result["severity"] == "error"
        assert result["title"] == "Test Error"
        assert result["description"] == "This is a test error"
        assert result["remediation"] == "Fix the test error"
        assert result["fix_commands"] == []
    
    def test_error_message_format_for_cli(self):
        """Test formatting error message for CLI output."""
        error_msg = ErrorMessage(
            category=ErrorCategory.AWS_CREDENTIALS,
            severity=ErrorSeverity.ERROR,
            title="Test Error",
            description="This is a test error",
            remediation="Fix the test error",
            fix_commands=["echo 'fix1'", "echo 'fix2'"]
        )
        
        formatted = error_msg.format_for_cli()
        assert "❌ Test Error" in formatted
        assert "Description:" in formatted
        assert "Remediation:" in formatted
        assert "echo 'fix1'" in formatted


class TestZscalerMCPError:
    """Test ZscalerMCPError exception class."""
    
    def test_base_error_creation(self):
        """Test creating base error."""
        error = ZscalerMCPError("Test message")
        assert error.message == "Test message"
        assert error.category == ErrorCategory.UNKNOWN
        assert error.severity == ErrorSeverity.ERROR
    
    def test_error_with_category_and_context(self):
        """Test error with category and context."""
        error = ZscalerMCPError(
            message="Test message",
            category=ErrorCategory.AWS_CREDENTIALS,
            context={"test": "value"},
            fix_commands=["fix_command"]
        )
        
        assert error.category == ErrorCategory.AWS_CREDENTIALS
        assert error.context == {"test": "value"}
        assert error.fix_commands == ["fix_command"]
    
    def test_error_to_error_message(self):
        """Test converting error to error message."""
        error = ZscalerMCPError(
            message="Test message",
            category=ErrorCategory.AWS_CREDENTIALS,
            error_code="TEST_ERROR"
        )
        
        error_msg = error.to_error_message()
        assert error_msg.category == ErrorCategory.AWS_CREDENTIALS
        assert error_msg.title == "ZscalerMCP Error"
        assert error_msg.description == "Test message"
        assert error_msg.error_code == "TEST_ERROR"


class TestSpecificErrors:
    """Test specific error types."""
    
    def test_aws_credentials_error(self):
        """Test AWS credentials error."""
        error = AWSCredentialsError(
            message="Invalid credentials",
            error_code="InvalidAccessKeyId",
            context={"access_key": "test-key"}
        )
        
        assert isinstance(error, ZscalerMCPError)
        assert error.category == ErrorCategory.AWS_CREDENTIALS
        assert error.error_code == "InvalidAccessKeyId"
        assert error.context == {"access_key": "test-key"}
    
    def test_aws_region_error(self):
        """Test AWS region error."""
        error = AWSRegionError(
            message="Unsupported region",
            context={"region": "test-region"}
        )
        
        assert isinstance(error, ZscalerMCPError)
        assert error.category == ErrorCategory.AWS_REGION
        assert error.context == {"region": "test-region"}
    
    def test_aws_permissions_error(self):
        """Test AWS permissions error."""
        error = AWSPermissionsError(
            message="Missing permissions",
            missing_permissions=["s3:GetObject"],
            context={"service": "s3"}
        )
        
        assert isinstance(error, ZscalerMCPError)
        assert error.category == ErrorCategory.AWS_PERMISSIONS
        assert error.context["service"] == "s3"
    
    def test_zscaler_credentials_error(self):
        """Test Zscaler credentials error."""
        error = ZscalerCredentialsError(
            message="Invalid username",
            context={"username": "test"}
        )
        
        assert isinstance(error, ZscalerMCPError)
        assert error.category == ErrorCategory.ZSCALER_CREDENTIALS
        assert error.context == {"username": "test"}
    
    def test_zscaler_connectivity_error(self):
        """Test Zscaler connectivity error."""
        error = ZscalerConnectivityError(
            message="Connection failed",
            context={"cloud": "zscaler"}
        )
        
        assert isinstance(error, ZscalerMCPError)
        assert error.category == ErrorCategory.ZSCALER_CONNECTIVITY
        assert error.context == {"cloud": "zscaler"}
    
    def test_zscaler_authentication_error(self):
        """Test Zscaler authentication error."""
        error = ZscalerAuthenticationError(
            message="Auth failed",
            context={"status_code": 401}
        )
        
        assert isinstance(error, ZscalerMCPError)
        assert error.category == ErrorCategory.ZSCALER_AUTHENTICATION
        assert error.context == {"status_code": 401}


class TestErrorMessageCatalog:
    """Test error message catalog."""
    
    def test_get_message(self):
        """Test getting a predefined error message."""
        message = ErrorMessageCatalog.get_message("AWS_NO_CREDENTIALS")
        assert message is not None
        assert message.category == ErrorCategory.AWS_CREDENTIALS
        assert message.title == "AWS Credentials Not Found"
    
    def test_get_nonexistent_message(self):
        """Test getting a nonexistent error message."""
        message = ErrorMessageCatalog.get_message("NONEXISTENT_MESSAGE")
        assert message is None
    
    def test_get_all_messages(self):
        """Test getting all predefined error messages."""
        messages = ErrorMessageCatalog.get_all_messages()
        assert len(messages) > 0
        assert "AWS_NO_CREDENTIALS" in messages
        assert "ZSCALER_MISSING_CREDENTIALS" in messages


class TestUserGuidance:
    """Test user guidance helpers."""
    
    def test_get_aws_credential_help(self):
        """Test getting AWS credential help."""
        help_text = UserGuidance.get_aws_credential_help()
        assert isinstance(help_text, str)
        assert len(help_text) > 0
        assert "AWS Credential Configuration" in help_text
    
    def test_get_zscaler_credential_help(self):
        """Test getting Zscaler credential help."""
        help_text = UserGuidance.get_zscaler_credential_help()
        assert isinstance(help_text, str)
        assert len(help_text) > 0
        assert "Zscaler Credential Configuration" in help_text
    
    def test_get_common_issues_help(self):
        """Test getting common issues help."""
        help_text = UserGuidance.get_common_issues_help()
        assert isinstance(help_text, str)
        assert len(help_text) > 0
        assert "Common Issues and Troubleshooting" in help_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])