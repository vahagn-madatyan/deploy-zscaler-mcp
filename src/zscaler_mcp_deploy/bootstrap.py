"""Bootstrap orchestrator for Zscaler MCP Deployer.

Coordinates secret and IAM role creation with rollback capability on partial failure.
Provides idempotent resource handling with preflight validation.
"""

import logging
from typing import List, Optional, Tuple
from dataclasses import dataclass

import boto3

from .aws.secrets_manager import SecretsManager, SecretsManagerError
from .aws.iam_bootstrap import IAMBootstrap, IAMBootstrapError
from .validators.aws import AWSSessionValidator
from .models import BootstrapResult, BootstrapConfig, SecretResult, IAMRoleResult
from .errors import ZscalerMCPError, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


class BootstrapOrchestratorError(ZscalerMCPError):
    """Error related to bootstrap orchestration operations."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        phase: Optional[str] = None,
        context: Optional[dict] = None
    ):
        full_context = context or {}
        if phase:
            full_context["phase"] = phase
        super().__init__(
            message=message,
            category=ErrorCategory.AWS_PERMISSIONS,
            severity=ErrorSeverity.ERROR,
            error_code=error_code or "S02-003",
            context=full_context
        )
        self.phase = phase


class BootstrapOrchestrator:
    """Orchestrates bootstrap operations for Zscaler MCP Deployer.
    
    Coordinates secret creation, IAM role creation, and rollback on failure.
    Performs preflight validation before any resource creation.
    """
    
    def __init__(
        self,
        region: Optional[str] = None,
        profile_name: Optional[str] = None,
        session: Optional[boto3.Session] = None,
        secrets_manager: Optional[SecretsManager] = None,
        iam_bootstrap: Optional[IAMBootstrap] = None,
        validator: Optional[AWSSessionValidator] = None
    ):
        """Initialize BootstrapOrchestrator.
        
        Args:
            region: AWS region (optional)
            profile_name: AWS profile name (optional)
            session: Pre-configured boto3 session (optional)
            secrets_manager: Pre-configured SecretsManager (optional, for testing)
            iam_bootstrap: Pre-configured IAMBootstrap (optional, for testing)
            validator: Pre-configured AWSSessionValidator (optional, for testing)
        """
        self._region = region
        self._profile_name = profile_name
        self._session = session
        self._secrets_manager = secrets_manager
        self._iam_bootstrap = iam_bootstrap
        self._validator = validator
        self._created_resources: List[Tuple[str, str]] = []  # [(resource_type, resource_id)]
    
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
    def secrets_manager(self) -> SecretsManager:
        """Lazy initialization of SecretsManager."""
        if self._secrets_manager is None:
            self._secrets_manager = SecretsManager(
                region=self._region,
                profile_name=self._profile_name,
                session=self._session
            )
        return self._secrets_manager
    
    @property
    def iam_bootstrap(self) -> IAMBootstrap:
        """Lazy initialization of IAMBootstrap."""
        if self._iam_bootstrap is None:
            self._iam_bootstrap = IAMBootstrap(
                region=self._region,
                profile_name=self._profile_name,
                session=self._session
            )
        return self._iam_bootstrap
    
    @property
    def validator(self) -> AWSSessionValidator:
        """Lazy initialization of AWSSessionValidator."""
        if self._validator is None:
            self._validator = AWSSessionValidator(
                profile_name=self._profile_name,
                region=self._region
            )
        return self._validator
    
    def _run_preflight_validation(self) -> Tuple[bool, List[str]]:
        """Run preflight validation before resource creation.
        
        Returns:
            Tuple of (is_valid, list_of_messages)
        """
        logger.info("Running preflight validation")
        return self.validator.validate_session(region=self._region)
    
    def _create_secret(self, config: BootstrapConfig) -> SecretResult:
        """Create or use existing secret.
        
        Args:
            config: Bootstrap configuration
            
        Returns:
            SecretResult from the operation
            
        Raises:
            SecretsManagerError: If secret creation fails
        """
        logger.info(f"Phase: secret creation - {config.secret_name}")
        
        return self.secrets_manager.create_or_use_secret(
            secret_name=config.secret_name,
            username=config.username,
            password=config.password,
            api_key=config.api_key,
            cloud=config.cloud,
            kms_key_id=config.kms_key_id,
            description=config.description or f"Zscaler credentials for {config.cloud} cloud",
            tags=config.tags
        )
    
    def _create_role(self, config: BootstrapConfig, secret_arn: str) -> IAMRoleResult:
        """Create or use existing IAM role.
        
        Args:
            config: Bootstrap configuration
            secret_arn: ARN of the secret for policy attachment
            
        Returns:
            IAMRoleResult from the operation
            
        Raises:
            IAMBootstrapError: If role creation fails
        """
        logger.info(f"Phase: role creation - {config.role_name}")
        
        return self.iam_bootstrap.create_or_use_execution_role(
            role_name=config.role_name,
            secret_arn=secret_arn,
            description=config.description or f"Execution role for Bedrock AgentCore - {config.role_name}",
            tags=config.tags
        )
    
    def bootstrap_resources(self, config: BootstrapConfig) -> BootstrapResult:
        """Orchestrate bootstrap resource creation.
        
        Performs preflight validation, creates secret, creates IAM role,
        and tracks resources for potential rollback on failure.
        
        Args:
            config: Bootstrap configuration
            
        Returns:
            BootstrapResult with operation results
        """
        self._created_resources = []  # Reset resource tracking
        
        # Phase 1: Preflight validation
        logger.info("Phase: preflight validation")
        is_valid, messages = self._run_preflight_validation()
        
        if not is_valid:
            error_msg = "; ".join(messages)
            logger.error(f"Preflight validation failed: {error_msg}")
            return BootstrapResult(
                success=False,
                error_message=error_msg,
                error_code="S02-003-PreflightFailed",
                phase="preflight"
            )
        
        logger.info("Preflight validation passed")
        
        secret_result: Optional[SecretResult] = None
        role_result: Optional[IAMRoleResult] = None
        
        try:
            # Phase 2: Create secret
            secret_result = self._create_secret(config)
            
            if secret_result.created:
                self._created_resources.append(("secret", secret_result.name))
                logger.info(f"Secret created: {secret_result.arn}")
            else:
                logger.info(f"Secret already exists: {secret_result.arn}")
            
            # Phase 3: Create IAM role
            role_result = self._create_role(config, secret_result.arn)
            
            if role_result.created:
                self._created_resources.append(("role", role_result.name))
                logger.info(f"Role created: {role_result.arn}")
            else:
                logger.info(f"Role already exists: {role_result.arn}")
            
            # Success!
            logger.info("Bootstrap completed successfully")
            return BootstrapResult(
                secret_arn=secret_result.arn,
                role_arn=role_result.arn,
                resource_ids=[r[1] for r in self._created_resources],
                success=True,
                secret_created=secret_result.created,
                role_created=role_result.created,
                phase="completed"
            )
            
        except SecretsManagerError as e:
            logger.error(f"Secret creation failed: {e.message}")
            return BootstrapResult(
                secret_arn=secret_result.arn if secret_result else None,
                success=False,
                error_message=e.message,
                error_code=e.error_code or "S02-003-SecretFailed",
                phase="secret",
                resource_ids=[r[1] for r in self._created_resources],
                secret_created=False
            )
            
        except IAMBootstrapError as e:
            logger.error(f"Role creation failed: {e.message}")
            
            # Attempt rollback if we created the secret
            if secret_result and secret_result.created:
                logger.warning("Initiating rollback due to role creation failure")
                rollback_success, rollback_errors = self.rollback()
                
                if not rollback_success:
                    error_msg = f"{e.message}; Rollback partially failed: {'; '.join(rollback_errors)}"
                else:
                    error_msg = f"{e.message}; Rollback completed successfully"
                    # Clear created resources since we rolled back
                    self._created_resources = []
            else:
                error_msg = e.message
            
            return BootstrapResult(
                secret_arn=secret_result.arn if secret_result else None,
                role_arn=role_result.arn if role_result else None,
                success=False,
                error_message=error_msg,
                error_code=e.error_code or "S02-003-RoleFailed",
                phase="role",
                resource_ids=[r[1] for r in self._created_resources],
                secret_created=secret_result.created if secret_result else False,
                role_created=False
            )
    
    def rollback(self) -> Tuple[bool, List[str]]:
        """Rollback created resources in reverse order.
        
        Deletes resources in the reverse order they were created:
        - Role first (if created)
        - Then secret (if created)
        
        Returns:
            Tuple of (success, list_of_error_messages)
        """
        logger.info(f"Starting rollback for {len(self._created_resources)} resources")
        
        errors = []
        
        # Process in reverse order (LIFO)
        for resource_type, resource_id in reversed(self._created_resources):
            try:
                if resource_type == "role":
                    logger.info(f"Rolling back role: {resource_id}")
                    self.iam_bootstrap.delete_role(resource_id)
                    logger.info(f"Role deleted: {resource_id}")
                    
                elif resource_type == "secret":
                    logger.info(f"Rolling back secret: {resource_id}")
                    self.secrets_manager.delete_secret(
                        resource_id,
                        force_delete_without_recovery=True
                    )
                    logger.info(f"Secret deleted: {resource_id}")
                    
            except Exception as e:
                error_msg = f"Failed to delete {resource_type} '{resource_id}': {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        success = len(errors) == 0
        
        if success:
            logger.info("Rollback completed successfully")
            # Clear tracked resources after successful rollback
            self._created_resources = []
        else:
            logger.error(f"Rollback completed with {len(errors)} errors")
        
        return success, errors
    
    def get_created_resources(self) -> List[Tuple[str, str]]:
        """Get list of resources created during bootstrap.
        
        Returns:
            List of (resource_type, resource_id) tuples
        """
        return self._created_resources.copy()
