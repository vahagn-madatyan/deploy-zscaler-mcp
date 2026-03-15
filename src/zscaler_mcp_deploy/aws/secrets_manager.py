"""Secrets Manager client for Zscaler MCP Deployer."""

import json
import logging
from typing import Optional, Dict, Any

import boto3
from botocore.exceptions import ClientError

from ..models import SecretResult
from ..errors import ZscalerMCPError, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


class SecretsManagerError(ZscalerMCPError):
    """Error related to Secrets Manager operations."""
    
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
            error_code=error_code or "S02-001",
            context=context
        )


class SecretsManager:
    """Client for AWS Secrets Manager operations.
    
    Provides idempotent secret creation with automatic handling of resource existence.
    Uses lazy initialization for boto3 session and client.
    """
    
    DEFAULT_KMS_KEY = "aws/secretsmanager"  # AWS-managed KMS key
    
    def __init__(
        self,
        region: Optional[str] = None,
        profile_name: Optional[str] = None,
        session: Optional[boto3.Session] = None
    ):
        """Initialize SecretsManager.
        
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
    def client(self):
        """Lazy initialization of Secrets Manager client."""
        if self._client is None:
            self._client = self.session.client("secretsmanager")
        return self._client
    
    def create_or_use_secret(
        self,
        secret_name: str,
        username: str,
        password: str,
        api_key: str,
        cloud: str,
        kms_key_id: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[list] = None
    ) -> SecretResult:
        """Create a new secret or use an existing one with idempotent handling.
        
        The secret structure follows:
        {
            "username": "...",
            "password": "...",
            "api_key": "...",
            "cloud": "..."
        }
        
        Args:
            secret_name: Name of the secret
            username: Zscaler username
            password: Zscaler password
            api_key: Zscaler API key
            cloud: Zscaler cloud name (e.g., "zscaler", "zscalerone")
            kms_key_id: KMS key ARN or alias for encryption (optional, defaults to AWS-managed key)
            description: Description for the secret (optional)
            tags: List of tag dicts with 'Key' and 'Value' (optional)
            
        Returns:
            SecretResult containing ARN, name, version_id, and created flag
            
        Raises:
            SecretsManagerError: If secret creation or retrieval fails
        """
        secret_value = json.dumps({
            "username": username,
            "password": password,
            "api_key": api_key,
            "cloud": cloud
        })
        
        # Use default KMS key if not specified
        effective_kms_key = kms_key_id or self.DEFAULT_KMS_KEY
        
        try:
            logger.info(f"Creating secret: {secret_name}")
            
            create_args = {
                "Name": secret_name,
                "SecretString": secret_value,
                "Description": description or f"Zscaler credentials for {cloud} cloud",
            }
            
            # Only specify KMS key if it's not the default AWS-managed key
            if kms_key_id:
                create_args["KmsKeyId"] = kms_key_id
            
            if tags:
                create_args["Tags"] = tags
            
            response = self.client.create_secret(**create_args)
            
            logger.info(f"Secret created successfully: {response.get('ARN')}")
            
            return SecretResult(
                arn=response["ARN"],
                name=secret_name,
                version_id=response.get("VersionId"),
                created=True,
                kms_key_id=effective_kms_key
            )
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            
            if error_code == "ResourceExistsException":
                logger.info(f"Secret already exists: {secret_name}")
                return self._handle_existing_secret(secret_name, effective_kms_key)
            
            logger.error(f"Failed to create secret: {error_code} - {e.response['Error']['Message']}")
            raise SecretsManagerError(
                message=f"Failed to create secret '{secret_name}': {e.response['Error']['Message']}",
                error_code=f"S02-001-{error_code}",
                context={
                    "secret_name": secret_name,
                    "aws_error_code": error_code,
                    "kms_key_id": effective_kms_key
                }
            )
    
    def _handle_existing_secret(
        self,
        secret_name: str,
        kms_key_id: str
    ) -> SecretResult:
        """Handle the case when a secret already exists.
        
        Validates the existing secret and returns its details.
        
        Args:
            secret_name: Name of the existing secret
            kms_key_id: The KMS key ID used for encryption
            
        Returns:
            SecretResult for the existing secret
            
        Raises:
            SecretsManagerError: If the secret cannot be retrieved
        """
        try:
            response = self.client.describe_secret(SecretId=secret_name)
            
            logger.info(f"Retrieved existing secret: {response.get('ARN')}")
            
            return SecretResult(
                arn=response["ARN"],
                name=secret_name,
                version_id=None,  # Not retrieving secret value, just describing
                created=False,
                kms_key_id=kms_key_id
            )
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            logger.error(f"Failed to describe existing secret: {error_code}")
            raise SecretsManagerError(
                message=f"Failed to retrieve existing secret '{secret_name}': {e.response['Error']['Message']}",
                error_code=f"S02-001-{error_code}",
                context={
                    "secret_name": secret_name,
                    "aws_error_code": error_code
                }
            )
    
    def get_secret_value(self, secret_name: str) -> Dict[str, Any]:
        """Retrieve and parse the secret value.
        
        Args:
            secret_name: Name or ARN of the secret
            
        Returns:
            Parsed secret value as dictionary
            
        Raises:
            SecretsManagerError: If the secret cannot be retrieved or parsed
        """
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            
            if "SecretString" in response:
                return json.loads(response["SecretString"])
            else:
                raise SecretsManagerError(
                    message=f"Secret '{secret_name}' contains binary data, expected JSON string",
                    error_code="S02-001-BinarySecret",
                    context={"secret_name": secret_name}
                )
                
        except json.JSONDecodeError as e:
            raise SecretsManagerError(
                message=f"Failed to parse secret '{secret_name}' as JSON: {str(e)}",
                error_code="S02-001-JSONError",
                context={"secret_name": secret_name}
            )
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            raise SecretsManagerError(
                message=f"Failed to retrieve secret '{secret_name}': {e.response['Error']['Message']}",
                error_code=f"S02-001-{error_code}",
                context={
                    "secret_name": secret_name,
                    "aws_error_code": error_code
                }
            )
    
    def delete_secret(
        self,
        secret_name: str,
        force_delete_without_recovery: bool = False,
        recovery_window_in_days: Optional[int] = None
    ) -> None:
        """Delete a secret.
        
        Args:
            secret_name: Name or ARN of the secret to delete
            force_delete_without_recovery: Force immediate deletion (no recovery)
            recovery_window_in_days: Recovery window in days (7-30, default 30)
            
        Raises:
            SecretsManagerError: If deletion fails
        """
        try:
            delete_args = {"SecretId": secret_name}
            
            if force_delete_without_recovery:
                delete_args["ForceDeleteWithoutRecovery"] = True
            elif recovery_window_in_days is not None:
                delete_args["RecoveryWindowInDays"] = recovery_window_in_days
            
            self.client.delete_secret(**delete_args)
            logger.info(f"Secret deleted: {secret_name}")
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            raise SecretsManagerError(
                message=f"Failed to delete secret '{secret_name}': {e.response['Error']['Message']}",
                error_code=f"S02-001-{error_code}",
                context={
                    "secret_name": secret_name,
                    "aws_error_code": error_code
                }
            )