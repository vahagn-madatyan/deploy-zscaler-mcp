"""Predefined error messages and user guidance for Zscaler MCP Deployer."""

from typing import Dict, List, Optional, Any
from .errors import ErrorMessage, ErrorCategory, ErrorSeverity


class ErrorMessageCatalog:
    """Catalog of predefined error messages with remediation guidance."""
    
    # AWS Credential Errors
    AWS_NO_CREDENTIALS = ErrorMessage(
        category=ErrorCategory.AWS_CREDENTIALS,
        severity=ErrorSeverity.ERROR,
        title="AWS Credentials Not Found",
        description="No AWS credentials were found in your environment.",
        remediation="Configure AWS credentials using one of the supported methods.",
        fix_commands=[
            "aws configure",
            "# Or set environment variables:",
            "export AWS_ACCESS_KEY_ID=your_access_key",
            "export AWS_SECRET_ACCESS_KEY=your_secret_key",
            "export AWS_DEFAULT_REGION=us-east-1"
        ]
    )
    
    AWS_PROFILE_NOT_FOUND = ErrorMessage(
        category=ErrorCategory.AWS_CREDENTIALS,
        severity=ErrorSeverity.ERROR,
        title="AWS Profile Not Found",
        description="The specified AWS profile could not be found.",
        remediation="Check your AWS profile name or configure a new profile.",
        fix_commands=[
            "aws configure --profile your-profile-name",
            "aws configure list-profiles"
        ]
    )
    
    AWS_INVALID_ACCESS_KEY = ErrorMessage(
        category=ErrorCategory.AWS_CREDENTIALS,
        severity=ErrorSeverity.ERROR,
        title="Invalid AWS Access Key",
        description="The AWS access key ID you provided is invalid or doesn't exist.",
        remediation="Verify your AWS access key ID is correct and active.",
        fix_commands=[
            "aws configure",
            "# Or rotate your access keys in the AWS IAM console"
        ]
    )
    
    AWS_SIGNATURE_MISMATCH = ErrorMessage(
        category=ErrorCategory.AWS_CREDENTIALS,
        severity=ErrorSeverity.ERROR,
        title="AWS Signature Mismatch",
        description="The AWS signature validation failed - likely due to an incorrect secret access key.",
        remediation="Verify your AWS secret access key is correct.",
        fix_commands=[
            "aws configure",
            "# Or rotate your access keys in the AWS IAM console"
        ]
    )
    
    AWS_INSUFFICIENT_PERMISSIONS = ErrorMessage(
        category=ErrorCategory.AWS_CREDENTIALS,
        severity=ErrorSeverity.WARNING,
        title="Insufficient AWS Permissions",
        description="Your AWS credentials are valid but lack basic permissions.",
        remediation="Add the sts:GetCallerIdentity permission to your AWS user/role.",
        fix_commands=[
            "# Add this policy to your IAM user/role:",
            "aws iam attach-user-policy --user-name your-user --policy-arn arn:aws:iam::aws:policy/PowerUserAccess"
        ]
    )
    
    # AWS Region Errors
    AWS_NO_REGION = ErrorMessage(
        category=ErrorCategory.AWS_REGION,
        severity=ErrorSeverity.ERROR,
        title="AWS Region Not Specified",
        description="No AWS region was specified for the deployment.",
        remediation="Specify an AWS region that supports Amazon Bedrock.",
        fix_commands=[
            "zscaler-mcp-deploy preflight --region us-east-1",
            "# Or set default region:",
            "export AWS_DEFAULT_REGION=us-east-1"
        ]
    )
    
    AWS_UNSUPPORTED_REGION = ErrorMessage(
        category=ErrorCategory.AWS_REGION,
        severity=ErrorSeverity.ERROR,
        title="Unsupported AWS Region",
        description="The specified AWS region does not support Amazon Bedrock.",
        remediation="Choose an AWS region that supports Amazon Bedrock.",
        fix_commands=[
            "zscaler-mcp-deploy preflight --region us-east-1",
            "# Supported regions: us-east-1, us-west-2, eu-west-1, etc."
        ]
    )
    
    # AWS Permissions Errors
    AWS_MISSING_PERMISSIONS = ErrorMessage(
        category=ErrorCategory.AWS_PERMISSIONS,
        severity=ErrorSeverity.ERROR,
        title="Missing AWS Permissions",
        description="Required AWS permissions are missing for Zscaler MCP deployment.",
        remediation="Add the required IAM permissions to your AWS user/role.",
        fix_commands=[
            "# Attach a managed policy with required permissions",
            "# Or create a custom policy with the missing actions shown below"
        ]
    )
    
    # Zscaler Credential Errors
    ZSCALER_MISSING_CREDENTIALS = ErrorMessage(
        category=ErrorCategory.ZSCALER_CREDENTIALS,
        severity=ErrorSeverity.ERROR,
        title="Missing Zscaler Credentials",
        description="Required Zscaler credentials were not provided.",
        remediation="Provide Zscaler username, password, and API key.",
        fix_commands=[
            "zscaler-mcp-deploy preflight --zscaler-username user@company.com --zscaler-password your_password --zscaler-api-key your_api_key",
            "# Or set as environment variables:",
            "export ZSCALER_USERNAME=user@company.com",
            "export ZSCALER_PASSWORD=your_password",
            "export ZSCALER_API_KEY=your_32_char_api_key"
        ]
    )
    
    ZSCALER_INVALID_USERNAME = ErrorMessage(
        category=ErrorCategory.ZSCALER_CREDENTIALS,
        severity=ErrorSeverity.ERROR,
        title="Invalid Zscaler Username",
        description="Zscaler username must be a valid email address.",
        remediation="Provide a valid email address for your Zscaler username.",
        fix_commands=[
            "zscaler-mcp-deploy preflight --zscaler-username user@company.com"
        ]
    )
    
    ZSCALER_INVALID_API_KEY = ErrorMessage(
        category=ErrorCategory.ZSCALER_CREDENTIALS,
        severity=ErrorSeverity.ERROR,
        title="Invalid Zscaler API Key",
        description="Zscaler API key must be 32 hexadecimal characters.",
        remediation="Verify your Zscaler API key format is correct.",
        fix_commands=[
            "# Generate a new API key in the Zscaler admin console",
            "# API key should be 32 characters like: 1a2b3c4d5e6f78901234567890abcdef"
        ]
    )
    
    # Zscaler Connectivity Errors
    ZSCALER_CONNECTIVITY_FAILED = ErrorMessage(
        category=ErrorCategory.ZSCALER_CONNECTIVITY,
        severity=ErrorSeverity.ERROR,
        title="Zscaler Connectivity Failed",
        description="Unable to connect to the specified Zscaler cloud.",
        remediation="Check network connectivity and verify the cloud name.",
        fix_commands=[
            "ping zsapi.zscaler.net",
            "zscaler-mcp-deploy preflight --zscaler-cloud zscaler"
        ]
    )
    
    # Zscaler Authentication Errors
    ZSCALER_AUTH_FAILED = ErrorMessage(
        category=ErrorCategory.ZSCALER_AUTHENTICATION,
        severity=ErrorSeverity.ERROR,
        title="Zscaler Authentication Failed",
        description="Unable to authenticate with Zscaler API using provided credentials.",
        remediation="Verify your Zscaler username, password, and API key are correct.",
        fix_commands=[
            "# Check credentials in Zscaler admin console",
            "# Ensure API access is enabled for your user",
            "# Verify you're using the correct cloud name"
        ]
    )
    
    @classmethod
    def get_message(cls, message_key: str) -> Optional[ErrorMessage]:
        """
        Get a predefined error message by key.
        
        Args:
            message_key: Key to look up the message (e.g., 'AWS_NO_CREDENTIALS')
            
        Returns:
            ErrorMessage object or None if not found
        """
        return getattr(cls, message_key, None)
    
    @classmethod
    def get_all_messages(cls) -> Dict[str, ErrorMessage]:
        """
        Get all predefined error messages.
        
        Returns:
            Dictionary mapping keys to ErrorMessage objects
        """
        messages = {}
        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            if isinstance(attr, ErrorMessage):
                messages[attr_name] = attr
        return messages


class UserGuidance:
    """Helper class for providing user guidance and help messages."""
    
    @staticmethod
    def get_aws_credential_help() -> str:
        """Get help text for AWS credential configuration."""
        return """
[b]AWS Credential Configuration[/b]

Zscaler MCP Deployer supports multiple ways to configure AWS credentials:

1. [b]AWS CLI Configuration[/b] (Recommended):
   Run: [cyan]aws configure[/cyan]
   This creates ~/.aws/credentials with your access keys.

2. [b]Environment Variables[/b]:
   [cyan]export AWS_ACCESS_KEY_ID=your_access_key[/cyan]
   [cyan]export AWS_SECRET_ACCESS_KEY=your_secret_key[/cyan]
   [cyan]export AWS_DEFAULT_REGION=us-east-1[/cyan]

3. [b]AWS Profiles[/b]:
   [cyan]aws configure --profile your-profile[/cyan]
   Then use: [cyan]zscaler-mcp-deploy preflight --profile your-profile[/cyan]

4. [b]EC2 Instance Profiles[/b] (for EC2 deployments):
   No configuration needed if running on EC2 with proper IAM role.

[b]Required AWS Permissions[/b]:
- Amazon Bedrock operations
- AWS Secrets Manager operations
- AWS STS operations (sts:GetCallerIdentity at minimum)

[b]Need help finding your credentials?[/b]
Check the AWS IAM console or contact your AWS administrator.
"""
    
    @staticmethod
    def get_zscaler_credential_help() -> str:
        """Get help text for Zscaler credential configuration."""
        return """
[b]Zscaler Credential Configuration[/b]

Zscaler MCP Deployer requires the following credentials:

1. [b]Username[/b]: Your Zscaler admin username (email address)
2. [b]Password[/b]: Your Zscaler admin password
3. [b]API Key[/b]: 32-character hexadecimal API key

[b]How to obtain Zscaler credentials:[/b]

1. [b]Username & Password[/b]:
   Use your regular Zscaler admin credentials.

2. [b]API Key[/b]:
   - Log into Zscaler admin console
   - Navigate to Administration > API Keys
   - Generate or copy an existing API key
   - Format should be 32 hex characters (e.g., 1a2b3c4d5e6f78901234567890abcdef)

[b]Supported Zscaler Clouds:[/b]
- zscaler (default)
- zscalerone
- zscalertwo
- zscalerthree
- zscalergov
- zscalerten

[b]Command-line usage:[/b]
[cyan]zscaler-mcp-deploy preflight --zscaler-username user@company.com --zscaler-password your_password --zscaler-api-key your_32_char_api_key[/cyan]

[b]Environment variable usage:[/b]
[cyan]export ZSCALER_USERNAME=user@company.com[/cyan]
[cyan]export ZSCALER_PASSWORD=your_password[/cyan]
[cyan]export ZSCALER_API_KEY=your_32_char_api_key[/cyan]
"""
    
    @staticmethod
    def get_common_issues_help() -> str:
        """Get help text for common issues and troubleshooting."""
        return """
[b]Common Issues and Troubleshooting[/b]

1. [b]AWS Credential Issues[/b]:
   - Error: "No AWS credentials found"
     [yellow]Solution:[/yellow] Run [cyan]aws configure[/cyan] or set AWS environment variables
   - Error: "InvalidAccessKeyId"
     [yellow]Solution:[yellow] Check your AWS access key in ~/.aws/credentials
   - Error: "SignatureDoesNotMatch"
     [yellow]Solution:[/yellow] Verify your AWS secret access key

2. [b]AWS Region Issues[/b]:
   - Error: "Region does not support Amazon Bedrock"
     [yellow]Solution:[/yellow] Use a supported region like us-east-1, us-west-2, eu-west-1
   - List supported regions: [cyan]aws ec2 describe-regions --region us-east-1[/cyan]

3. [b]AWS Permission Issues[/b]:
   - Error: "AccessDenied"
     [yellow]Solution:[/yellow] Add required IAM permissions to your user/role
   - Missing permissions are shown with suggested policy documents

4. [b]Zscaler Credential Issues[/b]:
   - Error: "Invalid username format"
     [yellow]Solution:[/yellow] Username must be an email address
   - Error: "Invalid API key format"
     [yellow]Solution:[/yellow] API key must be 32 hex characters
   - Error: "Authentication failed"
     [yellow]Solution:[/yellow] Verify all credentials and cloud name

5. [b]Network/Connectivity Issues[/b]:
   - Error: "Connection timed out"
     [yellow]Solution:[/yellow] Check firewall and proxy settings
   - Error: "Failed to connect"
     [yellow]Solution:[/yellow] Verify network connectivity to AWS and Zscaler

[b]For detailed help:[/b]
[cyan]zscaler-mcp-deploy --help[/cyan]
[cyan]zscaler-mcp-deploy preflight --help[/cyan]
"""