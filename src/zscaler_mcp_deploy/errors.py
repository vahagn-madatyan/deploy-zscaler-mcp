"""Error handling and messaging utilities for Zscaler MCP Deployer."""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class ErrorSeverity(Enum):
    """Severity levels for errors."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categories of errors."""
    AWS_CREDENTIALS = "aws_credentials"
    AWS_REGION = "aws_region"
    AWS_PERMISSIONS = "aws_permissions"
    ZSCALER_CREDENTIALS = "zscaler_credentials"
    ZSCALER_CONNECTIVITY = "zscaler_connectivity"
    ZSCALER_AUTHENTICATION = "zscaler_authentication"
    CONFIGURATION = "configuration"
    NETWORK = "network"
    UNKNOWN = "unknown"


@dataclass
class ErrorMessage:
    """Structured error message with context and remediation."""
    
    category: ErrorCategory
    severity: ErrorSeverity
    title: str
    description: str
    remediation: str
    context: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    fix_commands: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error message to dictionary."""
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "remediation": self.remediation,
            "context": self.context,
            "error_code": self.error_code,
            "fix_commands": self.fix_commands or []
        }
    
    def format_for_cli(self) -> str:
        """Format error message for CLI output."""
        lines = []
        lines.append(f"[bold red]❌ {self.title}[/bold red]")
        lines.append(f"[yellow]Description:[/yellow] {self.description}")
        lines.append(f"[blue]Remediation:[/blue] {self.remediation}")
        
        if self.fix_commands:
            lines.append("[green]🔧 Suggested fix commands:[/green]")
            for command in self.fix_commands:
                lines.append(f"   [cyan]${command}[/cyan]")
        
        return "\n".join(lines)


class ZscalerMCPError(Exception):
    """Base exception class for Zscaler MCP Deployer."""
    
    def __init__(self, 
                 message: str, 
                 category: ErrorCategory = ErrorCategory.UNKNOWN,
                 severity: ErrorSeverity = ErrorSeverity.ERROR,
                 error_code: Optional[str] = None,
                 context: Optional[Dict[str, Any]] = None,
                 fix_commands: Optional[List[str]] = None):
        """
        Initialize Zscaler MCP error.
        
        Args:
            message: Error message
            category: Error category
            severity: Error severity
            error_code: Specific error code
            context: Additional context information
            fix_commands: List of commands to fix the error
        """
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.error_code = error_code
        self.context = context or {}
        self.fix_commands = fix_commands or []
    
    def to_error_message(self) -> ErrorMessage:
        """Convert exception to structured error message."""
        return ErrorMessage(
            category=self.category,
            severity=self.severity,
            title=self.__class__.__name__.replace("Error", " Error"),
            description=self.message,
            remediation=self._get_default_remediation(),
            context=self.context,
            error_code=self.error_code,
            fix_commands=self.fix_commands
        )
    
    def _get_default_remediation(self) -> str:
        """Get default remediation message based on error category."""
        remediation_map = {
            ErrorCategory.AWS_CREDENTIALS: "Configure AWS credentials using AWS CLI or environment variables",
            ErrorCategory.AWS_REGION: "Specify a supported AWS region for Bedrock",
            ErrorCategory.AWS_PERMISSIONS: "Add required IAM permissions to your AWS user/role",
            ErrorCategory.ZSCALER_CREDENTIALS: "Verify Zscaler credentials format and values",
            ErrorCategory.ZSCALER_CONNECTIVITY: "Check network connectivity to Zscaler cloud",
            ErrorCategory.ZSCALER_AUTHENTICATION: "Verify Zscaler username, password, and API key",
            ErrorCategory.CONFIGURATION: "Check your configuration settings",
            ErrorCategory.NETWORK: "Check network connectivity and firewall settings",
            ErrorCategory.UNKNOWN: "Review the error details and check documentation"
        }
        return remediation_map.get(self.category, remediation_map[ErrorCategory.UNKNOWN])


class AWSCredentialsError(ZscalerMCPError):
    """Error related to AWS credentials."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.AWS_CREDENTIALS,
            error_code=error_code,
            context=context
        )


class AWSRegionError(ZscalerMCPError):
    """Error related to AWS region configuration."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.AWS_REGION,
            context=context
        )


class AWSPermissionsError(ZscalerMCPError):
    """Error related to AWS IAM permissions."""
    
    def __init__(self, message: str, missing_permissions: Optional[List[str]] = None, context: Optional[Dict[str, Any]] = None):
        fix_commands = []
        if missing_permissions:
            # Generate a policy document suggestion
            policy_doc = self._generate_policy_document(missing_permissions)
            context = context or {}
            context["missing_policy"] = policy_doc
        
        super().__init__(
            message=message,
            category=ErrorCategory.AWS_PERMISSIONS,
            context=context,
            fix_commands=fix_commands
        )
    
    def _generate_policy_document(self, permissions: List[str]) -> str:
        """Generate a minimal IAM policy document."""
        actions = [f"        \"{perm}\"" for perm in permissions]
        actions_str = ",\n".join(actions)
        
        policy_doc = f"""{{
    "Version": "2012-10-17",
    "Statement": [
        {{
            "Effect": "Allow",
            "Action": [
{actions_str}
            ],
            "Resource": "*"
        }}
    ]
}}"""
        return policy_doc


class ZscalerCredentialsError(ZscalerMCPError):
    """Error related to Zscaler credentials."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.ZSCALER_CREDENTIALS,
            context=context
        )


class ZscalerConnectivityError(ZscalerMCPError):
    """Error related to Zscaler connectivity."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.ZSCALER_CONNECTIVITY,
            context=context
        )


class ZscalerAuthenticationError(ZscalerMCPError):
    """Error related to Zscaler authentication."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.ZSCALER_AUTHENTICATION,
            context=context
        )


class BedrockRuntimeError(ZscalerMCPError):
    """Error related to Bedrock runtime operations."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.AWS_PERMISSIONS,
            severity=ErrorSeverity.ERROR,
            error_code=error_code or "S03-001",
            context=context
        )


class BedrockRuntimePollingError(ZscalerMCPError):
    """Error related to Bedrock runtime polling operations."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.AWS_PERMISSIONS,
            severity=ErrorSeverity.ERROR,
            error_code=error_code or "S03-002",
            context=context
        )


class DeployOrchestratorError(ZscalerMCPError):
    """Error related to deployment orchestration operations.
    
    Error codes:
    - S03-003: Generic orchestration error
    - S03-003-BootstrapFailed: Bootstrap phase failed
    - S03-003-RuntimeCreateFailed: Runtime creation failed
    - S03-003-PollingTimeout: Runtime polling timed out
    - S03-003-RuntimeFailed: Runtime reached CREATE_FAILED state
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        phase: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        full_context = context or {}
        if phase:
            full_context["phase"] = phase
        super().__init__(
            message=message,
            category=ErrorCategory.AWS_PERMISSIONS,
            severity=ErrorSeverity.ERROR,
            error_code=error_code or "S03-003",
            context=full_context
        )
        self.phase = phase