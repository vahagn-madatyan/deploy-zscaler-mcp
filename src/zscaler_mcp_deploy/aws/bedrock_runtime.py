"""Bedrock Runtime client for Zscaler MCP Deployer.

Provides Bedrock AgentCore runtime creation with lazy boto3 initialization,
environment variable injection, and proper error handling.
"""

import logging
import time
from typing import Optional, Dict, Any, List

import boto3
from botocore.exceptions import ClientError

from ..models import RuntimeConfig, RuntimeResult
from ..errors import (
    ZscalerMCPError,
    ErrorCategory,
    ErrorSeverity,
    BedrockRuntimePollingError,
)

logger = logging.getLogger(__name__)


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


class BedrockRuntime:
    """Client for AWS Bedrock AgentCore runtime operations.
    
    Provides runtime creation with lazy boto3 client initialization,
    environment variable configuration, and idempotent handling.
    
    The default image URI is a placeholder that should be replaced with
    the official Zscaler MCP server image from ECR or AWS Marketplace.
    """
    
    # Default Zscaler ECR image URI (placeholder for official image)
    # Replace with actual image URI from Zscaler ECR or AWS Marketplace
    DEFAULT_IMAGE_URI = "public.ecr.aws/zscaler/mcp-server-zscaler:latest"
    
    # Default transport protocol
    DEFAULT_TRANSPORT = "stdio"
    
    def __init__(
        self,
        region: Optional[str] = None,
        profile_name: Optional[str] = None,
        session: Optional[boto3.Session] = None
    ):
        """Initialize BedrockRuntime.
        
        Args:
            region: AWS region (optional)
            profile_name: AWS profile name (optional)
            session: Pre-configured boto3 session (optional)
        """
        self._region = region
        self._profile_name = profile_name
        self._session = session
        self._client = None
    
    @property
    def session(self) -> boto3.Session:
        """Lazy initialization of boto3 session."""
        if self._session is None:
            if self._profile_name:
                self._session = boto3.Session(
                    profile_name=self._profile_name,
                    region_name=self._region
                )
            else:
                self._session = boto3.Session(region_name=self._region)
        return self._session
    
    @property
    def _bedrock_client(self):
        """Lazy initialization of Bedrock Agent client."""
        if self._client is None:
            self._client = self.session.client("bedrock-agent")
        return self._client
    
    def _extract_secret_name(self, secret_arn: str) -> str:
        """Extract secret name from full ARN.
        
        The Bedrock runtime expects just the secret name, not the full ARN.
        
        Args:
            secret_arn: Full ARN of the secret
            
        Returns:
            Secret name (last component of ARN)
        """
        # ARN format: arn:aws:secretsmanager:<region>:<account>:secret:<name>-<suffix>
        # We want just the <name> part before any suffix
        if ":secret:" in secret_arn:
            # Extract the part after :secret:
            secret_part = secret_arn.split(":secret:")[-1]
            # Remove any suffix (hyphen followed by 6 alphanumeric chars at the end)
            # AWS suffixes are exactly 6 alphanumeric characters
            if "-" in secret_part:
                parts = secret_part.rsplit("-", 1)
                if len(parts) == 2 and len(parts[1]) == 6 and parts[1].isalnum():
                    return parts[0]
            return secret_part
        return secret_arn
    
    def _build_environment_variables(
        self,
        secret_arn: str,
        enable_write_tools: bool = False
    ) -> Dict[str, str]:
        """Build environment variables for the runtime.
        
        Args:
            secret_arn: ARN of the secret containing Zscaler credentials
            enable_write_tools: Whether to enable write-capable MCP tools
            
        Returns:
            Dictionary of environment variable name-value pairs
        """
        secret_name = self._extract_secret_name(secret_arn)
        
        env_vars = {
            "ZSCALER_SECRET_NAME": secret_name,
            "TRANSPORT": self.DEFAULT_TRANSPORT,
        }
        
        if enable_write_tools:
            env_vars["ENABLE_WRITE_TOOLS"] = "true"
        
        return env_vars
    
    def _build_network_configuration(self) -> Dict[str, Any]:
        """Build network configuration for the runtime.
        
        Returns:
            Network configuration dictionary for Bedrock runtime
        """
        return {
            "vpcConfiguration": {
                "subnetIds": [],
                "securityGroupIds": [],
            }
        }
    
    def create_runtime(
        self,
        runtime_name: str,
        secret_arn: str,
        role_arn: str,
        image_uri: Optional[str] = None,
        enable_write_tools: bool = False,
        tags: Optional[List[Dict[str, str]]] = None
    ) -> RuntimeResult:
        """Create a Bedrock AgentCore runtime.
        
        Args:
            runtime_name: Name for the runtime resource
            secret_arn: ARN of the Secrets Manager secret
            role_arn: ARN of the IAM execution role
            image_uri: Container image URI (optional, uses default if not provided)
            enable_write_tools: Whether to enable write-capable MCP tools
            tags: List of tag dicts with 'Key' and 'Value' (optional)
            
        Returns:
            RuntimeResult containing runtime_id, runtime_arn, status, etc.
            
        Raises:
            BedrockRuntimeError: If runtime creation fails
        """
        effective_image_uri = image_uri or self.DEFAULT_IMAGE_URI
        env_vars = self._build_environment_variables(secret_arn, enable_write_tools)
        network_config = self._build_network_configuration()
        
        # Log configuration (redacting sensitive values)
        logger.info(f"Creating Bedrock runtime: {runtime_name}")
        logger.info(f"Using image URI: {effective_image_uri}")
        logger.info(f"Enable write tools: {enable_write_tools}")
        logger.info(f"Environment variables: ZSCALER_SECRET_NAME=<redacted>, TRANSPORT={self.DEFAULT_TRANSPORT}")
        if enable_write_tools:
            logger.info("Environment variable: ENABLE_WRITE_TOOLS=true")
        
        try:
            create_args = {
                "runtimeName": runtime_name,
                "agentRuntimeConfiguration": {
                    "containerConfiguration": {
                        "imageUri": effective_image_uri,
                        "executionRoleArn": role_arn,
                        "environmentVariables": env_vars,
                        "networkConfiguration": network_config,
                    }
                }
            }
            
            if tags:
                create_args["tags"] = tags
            
            logger.info(f"Calling create_agent_runtime for: {runtime_name}")
            
            response = self._bedrock_client.create_agent_runtime(**create_args)
            
            runtime_id = response.get("runtimeId", "")
            runtime_arn = response.get("runtimeArn", "")
            status = response.get("status", "CREATING")
            
            logger.info(f"Runtime created: {runtime_arn} (status: {status})")
            
            return RuntimeResult(
                runtime_id=runtime_id,
                runtime_arn=runtime_arn,
                status=status,
                created=True,
                created_at=response.get("createdAt")
            )
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            
            logger.error(f"Failed to create runtime: {error_code} - {error_message}")
            
            raise BedrockRuntimeError(
                message=f"Failed to create Bedrock runtime '{runtime_name}': {error_message}",
                error_code=f"S03-001-{error_code}",
                context={
                    "runtime_name": runtime_name,
                    "aws_error_code": error_code,
                    "image_uri": effective_image_uri,
                }
            )
    
    def get_runtime(self, runtime_id: str) -> RuntimeResult:
        """Get details of an existing runtime.
        
        Args:
            runtime_id: Runtime identifier
            
        Returns:
            RuntimeResult with current runtime details
            
        Raises:
            BedrockRuntimeError: If runtime retrieval fails
        """
        try:
            logger.info(f"Getting runtime details: {runtime_id}")
            
            response = self._bedrock_client.get_agent_runtime(
                runtimeId=runtime_id
            )
            
            # Extract error information for failed runtimes
            # AWS API uses different field names for errors
            error_code = response.get("errorCode") or response.get("failureCode")
            error_message = response.get("errorMessage") or response.get("failureMessage")
            
            return RuntimeResult(
                runtime_id=response.get("runtimeId", runtime_id),
                runtime_arn=response.get("runtimeArn", ""),
                status=response.get("status", "UNKNOWN"),
                created=False,
                error_code=error_code,
                error_message=error_message,
                endpoint_url=response.get("endpointUrl"),
                created_at=response.get("createdAt")
            )
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            
            logger.error(f"Failed to get runtime: {error_code} - {error_message}")
            
            raise BedrockRuntimeError(
                message=f"Failed to get runtime '{runtime_id}': {error_message}",
                error_code=f"S03-001-{error_code}",
                context={
                    "runtime_id": runtime_id,
                    "aws_error_code": error_code,
                }
            )
    
    def delete_runtime(self, runtime_id: str) -> None:
        """Delete a Bedrock runtime.
        
        Args:
            runtime_id: Runtime identifier to delete
            
        Raises:
            BedrockRuntimeError: If deletion fails
        """
        try:
            logger.info(f"Deleting runtime: {runtime_id}")
            
            self._bedrock_client.delete_agent_runtime(runtimeId=runtime_id)
            
            logger.info(f"Runtime deleted: {runtime_id}")
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            
            logger.error(f"Failed to delete runtime: {error_code} - {error_message}")
            
            raise BedrockRuntimeError(
                message=f"Failed to delete runtime '{runtime_id}': {error_message}",
                error_code=f"S03-001-{error_code}",
                context={
                    "runtime_id": runtime_id,
                    "aws_error_code": error_code,
                }
            )

    def get_runtime_status(self, runtime_id: str) -> str:
        """Get the current status of a runtime.
        
        Args:
            runtime_id: Runtime identifier
            
        Returns:
            Runtime status string (e.g., "CREATING", "READY", "CREATE_FAILED")
            
        Raises:
            BedrockRuntimePollingError: If status check fails
        """
        try:
            response = self._bedrock_client.get_agent_runtime(runtimeId=runtime_id)
            status = response.get("status", "UNKNOWN")
            logger.debug(f"Runtime {runtime_id} status: {status}")
            return status
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            
            logger.error(f"Failed to get runtime status: {error_code} - {error_message}")
            
            raise BedrockRuntimePollingError(
                message=f"Failed to get runtime status for '{runtime_id}': {error_message}",
                error_code=f"S03-002-{error_code}",
                context={
                    "runtime_id": runtime_id,
                    "aws_error_code": error_code,
                }
            )

    def poll_runtime_status(
        self,
        runtime_id: str,
        timeout_seconds: int = 600,
        initial_interval: float = 5.0,
        max_interval: float = 30.0,
        backoff_factor: float = 1.5,
    ) -> RuntimeResult:
        """Poll runtime status until it reaches a terminal state.
        
        AWS Bedrock AgentCore runtimes have an asynchronous lifecycle. After
        create_agent_runtime returns, the runtime is in CREATING status and
        must be polled until it reaches READY (success) or CREATE_FAILED (failure).
        
        Args:
            runtime_id: Runtime identifier to poll
            timeout_seconds: Maximum time to wait (default: 600 = 10 minutes)
            initial_interval: Initial polling interval in seconds (default: 5.0)
            max_interval: Maximum polling interval in seconds (default: 30.0)
            backoff_factor: Factor to increase interval each poll (default: 1.5)
            
        Returns:
            RuntimeResult with final status and details
            
        Raises:
            BedrockRuntimePollingError: If timeout occurs or status check fails
            BedrockRuntimeError: If runtime reaches CREATE_FAILED status
        """
        logger.info(f"Starting runtime status polling for: {runtime_id}")
        logger.info(f"Timeout: {timeout_seconds}s, initial interval: {initial_interval}s")
        
        start_time = time.time()
        interval = initial_interval
        poll_count = 0
        
        while True:
            poll_count += 1
            elapsed = time.time() - start_time
            
            # Check timeout
            if elapsed >= timeout_seconds:
                logger.error(f"Runtime polling timeout after {elapsed:.1f}s ({poll_count} polls)")
                raise BedrockRuntimePollingError(
                    message=f"Runtime '{runtime_id}' did not reach READY status within {timeout_seconds} seconds",
                    error_code="S03-002-Timeout",
                    context={
                        "runtime_id": runtime_id,
                        "timeout_seconds": timeout_seconds,
                        "poll_count": poll_count,
                        "elapsed_seconds": elapsed,
                    }
                )
            
            # Get current status
            try:
                result = self.get_runtime(runtime_id)
                status = result.status
            except BedrockRuntimeError:
                # Re-raise with polling error code if it's a status check failure
                raise
            
            logger.info(f"Poll {poll_count}: Runtime {runtime_id} status = {status} (elapsed: {elapsed:.1f}s)")
            
            # Handle terminal states
            if status == "READY":
                logger.info(f"Runtime {runtime_id} is READY after {elapsed:.1f}s ({poll_count} polls)")
                return result
            
            if status == "CREATE_FAILED":
                # Get detailed failure information
                error_message = result.error_message or "Unknown failure reason"
                error_code = result.error_code or "Unknown"
                
                logger.error(f"Runtime {runtime_id} CREATE_FAILED: {error_message}")
                
                raise BedrockRuntimeError(
                    message=f"Runtime '{runtime_id}' creation failed: {error_message}",
                    error_code=f"S03-002-CreateFailed",
                    context={
                        "runtime_id": runtime_id,
                        "failure_reason": error_message,
                        "aws_error_code": error_code,
                        "poll_count": poll_count,
                        "elapsed_seconds": elapsed,
                    }
                )
            
            # Non-terminal state (CREATING, UPDATING, etc.) - continue polling
            if status not in ("CREATING", "UPDATING"):
                logger.warning(f"Unexpected runtime status '{status}' for {runtime_id}")
            
            # Wait before next poll with exponential backoff
            sleep_time = min(interval, max_interval)
            time.sleep(sleep_time)
            interval = min(interval * backoff_factor, max_interval)

    def wait_for_ready(
        self,
        runtime_id: str,
        timeout_seconds: int = 600,
    ) -> RuntimeResult:
        """Convenience method to wait for runtime to reach READY status.
        
        This is a simplified wrapper around poll_runtime_status with
        sensible defaults for most use cases.
        
        Args:
            runtime_id: Runtime identifier to wait for
            timeout_seconds: Maximum time to wait (default: 600 = 10 minutes)
            
        Returns:
            RuntimeResult with READY status
            
        Raises:
            BedrockRuntimePollingError: If timeout occurs
            BedrockRuntimeError: If runtime creation fails
        """
        logger.info(f"Waiting for runtime {runtime_id} to be READY...")
        return self.poll_runtime_status(
            runtime_id=runtime_id,
            timeout_seconds=timeout_seconds,
        )