"""Data models for Zscaler MCP Deployer."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


@dataclass
class BootstrapConfig:
    """Configuration for bootstrap orchestration.
    
    Attributes:
        secret_name: Name of the secret to create/use
        role_name: Name of the IAM role to create/use
        username: Zscaler username
        password: Zscaler password
        api_key: Zscaler API key
        cloud: Zscaler cloud name
        kms_key_id: KMS key ARN for secret encryption (optional)
        region: AWS region (optional)
        profile_name: AWS profile name (optional)
        description: Description for resources (optional)
        tags: List of tag dicts with 'Key' and 'Value' (optional)
    """
    secret_name: str
    role_name: str
    username: str
    password: str
    api_key: str
    cloud: str
    kms_key_id: Optional[str] = None
    region: Optional[str] = None
    profile_name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[Dict[str, str]]] = None


@dataclass
class BootstrapResult:
    """Result of bootstrap orchestration.
    
    Attributes:
        secret_arn: ARN of the secret
        role_arn: ARN of the IAM role
        resource_ids: List of resource identifiers created (for rollback)
        success: True if bootstrap succeeded
        error_message: Error message if bootstrap failed
        error_code: Error code for diagnostics
        phase: Phase where failure occurred (preflight, secret, role, rollback)
        secret_created: True if secret was newly created
        role_created: True if role was newly created
    """
    secret_arn: Optional[str] = None
    role_arn: Optional[str] = None
    resource_ids: List[str] = field(default_factory=list)
    success: bool = False
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    phase: Optional[str] = None
    secret_created: bool = False
    role_created: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary."""
        return {
            "secret_arn": self.secret_arn,
            "role_arn": self.role_arn,
            "resource_ids": self.resource_ids,
            "success": self.success,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "phase": self.phase,
            "secret_created": self.secret_created,
            "role_created": self.role_created,
        }


@dataclass
class SecretResult:
    """Result of a secret creation or lookup operation.
    
    Attributes:
        arn: The ARN of the secret
        name: The name of the secret
        version_id: The version ID of the secret (if created/updated)
        created: True if the secret was newly created, False if it existed
        kms_key_id: The KMS key ID used for encryption (optional)
    """
    arn: str
    name: str
    version_id: Optional[str] = None
    created: bool = False
    kms_key_id: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert the result to a dictionary."""
        return {
            "arn": self.arn,
            "name": self.name,
            "version_id": self.version_id,
            "created": self.created,
            "kms_key_id": self.kms_key_id,
        }


@dataclass
class IAMRoleResult:
    """Result of an IAM role creation or lookup operation.
    
    Attributes:
        arn: The ARN of the IAM role
        name: The name of the role
        role_id: The unique role ID assigned by AWS
        created: True if the role was newly created, False if it existed
        trust_policy: The trust policy document attached to the role
    """
    arn: str
    name: str
    role_id: Optional[str] = None
    created: bool = False
    trust_policy: Optional[dict] = None
    
    def to_dict(self) -> dict:
        """Convert the result to a dictionary."""
        return {
            "arn": self.arn,
            "name": self.name,
            "role_id": self.role_id,
            "created": self.created,
            "trust_policy": self.trust_policy,
        }


@dataclass
class RuntimeConfig:
    """Configuration for Bedrock AgentCore runtime.
    
    Attributes:
        runtime_name: Name for the runtime resource
        secret_arn: ARN of the Secrets Manager secret
        role_arn: ARN of the IAM execution role
        image_uri: Container image URI for the runtime
        enable_write_tools: Whether to enable write-capable MCP tools
        region: AWS region for the runtime
        tags: List of tag dicts with 'Key' and 'Value' (optional)
    """
    runtime_name: str
    secret_arn: str
    role_arn: str
    image_uri: str
    enable_write_tools: bool = False
    region: Optional[str] = None
    tags: Optional[List[Dict[str, str]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the config to a dictionary."""
        return {
            "runtime_name": self.runtime_name,
            "secret_arn": self.secret_arn,
            "role_arn": self.role_arn,
            "image_uri": self.image_uri,
            "enable_write_tools": self.enable_write_tools,
            "region": self.region,
            "tags": self.tags,
        }


@dataclass
class RuntimeResult:
    """Result of a Bedrock runtime creation operation.
    
    Attributes:
        runtime_id: Unique identifier for the runtime
        runtime_arn: ARN of the runtime resource
        status: Current status (CREATING, READY, CREATE_FAILED, etc.)
        created: True if the runtime was newly created
        error_code: Error code if creation failed
        error_message: Error message if creation failed
        endpoint_url: Runtime endpoint URL (optional)
        created_at: Creation timestamp (optional)
    """
    runtime_id: str
    runtime_arn: str
    status: str
    created: bool = True
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    endpoint_url: Optional[str] = None
    created_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary."""
        return {
            "runtime_id": self.runtime_id,
            "runtime_arn": self.runtime_arn,
            "status": self.status,
            "created": self.created,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "endpoint_url": self.endpoint_url,
            "created_at": self.created_at,
        }


@dataclass
class DeployConfig:
    """Configuration for full deployment operation.
    
    Combines bootstrap and runtime configuration for a complete deployment.
    
    Attributes:
        runtime_name: Name for the runtime resource
        secret_name: Name for the Secrets Manager secret
        role_name: Name for the IAM execution role
        username: Zscaler username
        password: Zscaler password
        api_key: Zscaler API key
        cloud: Zscaler cloud name
        image_uri: Container image URI (optional, uses default if not provided)
        enable_write_tools: Whether to enable write-capable MCP tools
        kms_key_id: KMS key ARN for secret encryption (optional)
        region: AWS region (optional)
        profile_name: AWS profile name (optional)
        description: Description for resources (optional)
        tags: List of tag dicts with 'Key' and 'Value' (optional)
    """
    runtime_name: str
    secret_name: str
    role_name: str
    username: str
    password: str
    api_key: str
    cloud: str
    image_uri: Optional[str] = None
    enable_write_tools: bool = False
    kms_key_id: Optional[str] = None
    region: Optional[str] = None
    profile_name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[Dict[str, str]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the config to a dictionary."""
        return {
            "runtime_name": self.runtime_name,
            "secret_name": self.secret_name,
            "role_name": self.role_name,
            "username": self.username,
            "password": "<redacted>",
            "api_key": "<redacted>",
            "cloud": self.cloud,
            "image_uri": self.image_uri,
            "enable_write_tools": self.enable_write_tools,
            "kms_key_id": self.kms_key_id,
            "region": self.region,
            "profile_name": self.profile_name,
            "description": self.description,
            "tags": self.tags,
        }


@dataclass
class DeployResult:
    """Result of a full deployment operation.
    
    Attributes:
        success: True if deployment succeeded
        runtime_id: Runtime identifier
        runtime_arn: Runtime ARN
        endpoint_url: Runtime endpoint URL
        status: Runtime status
        secret_arn: ARN of the secret used
        role_arn: ARN of the IAM role used
        secret_created: True if secret was newly created
        role_created: True if role was newly created
        runtime_created: True if runtime was newly created
        bootstrap_result: Full bootstrap result for detailed inspection
        error_message: Error message if deployment failed
        error_code: Error code for diagnostics
        phase: Phase where failure occurred (bootstrap, runtime_create, polling, rollback)
    """
    success: bool = False
    runtime_id: Optional[str] = None
    runtime_arn: Optional[str] = None
    endpoint_url: Optional[str] = None
    status: Optional[str] = None
    secret_arn: Optional[str] = None
    role_arn: Optional[str] = None
    secret_created: bool = False
    role_created: bool = False
    runtime_created: bool = False
    bootstrap_result: Optional[BootstrapResult] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    phase: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary."""
        return {
            "success": self.success,
            "runtime_id": self.runtime_id,
            "runtime_arn": self.runtime_arn,
            "endpoint_url": self.endpoint_url,
            "status": self.status,
            "secret_arn": self.secret_arn,
            "role_arn": self.role_arn,
            "secret_created": self.secret_created,
            "role_created": self.role_created,
            "runtime_created": self.runtime_created,
            "bootstrap_result": self.bootstrap_result.to_dict() if self.bootstrap_result else None,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "phase": self.phase,
        }