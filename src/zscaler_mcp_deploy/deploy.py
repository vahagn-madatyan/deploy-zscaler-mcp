"""Deployment orchestrator for Zscaler MCP Deployer.

Coordinates the complete deployment flow: bootstrap (S02) → runtime creation (T01/T02).
Provides rollback on runtime failure and comprehensive deployment results.
"""

import logging
from typing import Optional

import boto3

from .bootstrap import BootstrapOrchestrator, BootstrapConfig
from .aws.bedrock_runtime import BedrockRuntime, BedrockRuntimeError
from .models import DeployConfig, DeployResult, BootstrapResult, RuntimeResult
from .errors import (
    ZscalerMCPError,
    ErrorCategory,
    ErrorSeverity,
    BedrockRuntimePollingError,
    DeployOrchestratorError,
)

logger = logging.getLogger(__name__)


class DeployOrchestrator:
    """Orchestrates complete deployment for Zscaler MCP Deployer.
    
    Coordinates bootstrap operations (secret + IAM role) with Bedrock runtime
    creation and polling. Implements rollback on runtime failure.
    """
    
    def __init__(
        self,
        region: Optional[str] = None,
        profile_name: Optional[str] = None,
        session: Optional[boto3.Session] = None,
        bootstrap_orchestrator: Optional[BootstrapOrchestrator] = None,
        bedrock_runtime: Optional[BedrockRuntime] = None,
    ):
        """Initialize DeployOrchestrator.
        
        Args:
            region: AWS region (optional)
            profile_name: AWS profile name (optional)
            session: Pre-configured boto3 session (optional)
            bootstrap_orchestrator: Pre-configured BootstrapOrchestrator (optional, for testing)
            bedrock_runtime: Pre-configured BedrockRuntime (optional, for testing)
        """
        self._region = region
        self._profile_name = profile_name
        self._session = session
        self._bootstrap_orchestrator = bootstrap_orchestrator
        self._bedrock_runtime = bedrock_runtime
        self._created_runtime_id: Optional[str] = None
    
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
    def bootstrap_orchestrator(self) -> BootstrapOrchestrator:
        """Lazy initialization of BootstrapOrchestrator."""
        if self._bootstrap_orchestrator is None:
            self._bootstrap_orchestrator = BootstrapOrchestrator(
                region=self._region,
                profile_name=self._profile_name,
                session=self._session
            )
        return self._bootstrap_orchestrator
    
    @property
    def bedrock_runtime(self) -> BedrockRuntime:
        """Lazy initialization of BedrockRuntime."""
        if self._bedrock_runtime is None:
            self._bedrock_runtime = BedrockRuntime(
                region=self._region,
                profile_name=self._profile_name,
                session=self._session
            )
        return self._bedrock_runtime
    
    def _run_bootstrap(self, config: DeployConfig) -> BootstrapResult:
        """Run bootstrap phase to create/get secret and IAM role.
        
        Args:
            config: Deployment configuration
            
        Returns:
            BootstrapResult from the operation
        """
        logger.info("Phase: bootstrap - creating secret and IAM role")
        
        bootstrap_config = BootstrapConfig(
            secret_name=config.secret_name,
            role_name=config.role_name,
            username=config.username,
            password=config.password,
            api_key=config.api_key,
            cloud=config.cloud,
            kms_key_id=config.kms_key_id,
            region=config.region,
            profile_name=config.profile_name,
            description=config.description,
            tags=config.tags
        )
        
        return self.bootstrap_orchestrator.bootstrap_resources(bootstrap_config)
    
    def _create_runtime(
        self,
        config: DeployConfig,
        secret_arn: str,
        role_arn: str
    ) -> RuntimeResult:
        """Create Bedrock runtime.
        
        Args:
            config: Deployment configuration
            secret_arn: ARN of the secret
            role_arn: ARN of the IAM role
            
        Returns:
            RuntimeResult from the operation
            
        Raises:
            BedrockRuntimeError: If runtime creation fails
        """
        logger.info(f"Phase: runtime creation - {config.runtime_name}")
        
        result = self.bedrock_runtime.create_runtime(
            runtime_name=config.runtime_name,
            secret_arn=secret_arn,
            role_arn=role_arn,
            image_uri=config.image_uri,
            enable_write_tools=config.enable_write_tools,
            tags=config.tags
        )
        
        # Track created runtime for potential rollback
        if result.created:
            self._created_runtime_id = result.runtime_id
            logger.info(f"Runtime created with ID: {result.runtime_id}")
        
        return result
    
    def _poll_runtime(self, runtime_id: str, timeout_seconds: int = 600) -> RuntimeResult:
        """Poll runtime until it reaches READY or fails.
        
        Args:
            runtime_id: Runtime identifier to poll
            timeout_seconds: Maximum time to wait
            
        Returns:
            RuntimeResult with final status
            
        Raises:
            BedrockRuntimePollingError: If timeout occurs
            BedrockRuntimeError: If runtime creation fails
        """
        logger.info(f"Phase: polling runtime status - {runtime_id}")
        
        return self.bedrock_runtime.poll_runtime_status(
            runtime_id=runtime_id,
            timeout_seconds=timeout_seconds
        )
    
    def _rollback_runtime(self, runtime_id: str) -> bool:
        """Rollback created runtime on failure.
        
        Per R008, only the runtime is deleted on failure. Bootstrap resources
        (secret and IAM role) are kept for troubleshooting and reuse.
        
        Args:
            runtime_id: Runtime identifier to delete
            
        Returns:
            True if rollback succeeded, False otherwise
        """
        logger.info(f"Phase: rollback - deleting runtime {runtime_id}")
        
        try:
            self.bedrock_runtime.delete_runtime(runtime_id)
            logger.info(f"Rollback completed: runtime {runtime_id} deleted")
            self._created_runtime_id = None
            return True
        except BedrockRuntimeError as e:
            logger.error(f"Rollback failed: {e.message}")
            return False
    
    def deploy(
        self,
        config: DeployConfig,
        poll_timeout_seconds: int = 600
    ) -> DeployResult:
        """Orchestrate complete deployment: bootstrap → runtime → polling.
        
        Args:
            config: Deployment configuration
            poll_timeout_seconds: Maximum time to wait for runtime READY status
            
        Returns:
            DeployResult with all resource details and status
        """
        self._created_runtime_id = None  # Reset tracking
        
        # Phase 1: Bootstrap
        logger.info("Starting deployment - phase: bootstrap")
        bootstrap_result = self._run_bootstrap(config)
        
        if not bootstrap_result.success:
            logger.error(f"Bootstrap failed: {bootstrap_result.error_message}")
            return DeployResult(
                success=False,
                error_message=bootstrap_result.error_message,
                error_code=bootstrap_result.error_code or "S03-003-BootstrapFailed",
                phase="bootstrap",
                bootstrap_result=bootstrap_result,
                secret_arn=bootstrap_result.secret_arn,
                role_arn=bootstrap_result.role_arn,
                secret_created=bootstrap_result.secret_created,
                role_created=bootstrap_result.role_created,
            )
        
        logger.info("Bootstrap completed successfully")
        
        # Phase 2: Create runtime
        try:
            runtime_result = self._create_runtime(
                config=config,
                secret_arn=bootstrap_result.secret_arn,
                role_arn=bootstrap_result.role_arn
            )
        except BedrockRuntimeError as e:
            logger.error(f"Runtime creation failed: {e.message}")
            return DeployResult(
                success=False,
                error_message=e.message,
                error_code=e.error_code or "S03-003-RuntimeCreateFailed",
                phase="runtime_create",
                bootstrap_result=bootstrap_result,
                secret_arn=bootstrap_result.secret_arn,
                role_arn=bootstrap_result.role_arn,
                secret_created=bootstrap_result.secret_created,
                role_created=bootstrap_result.role_created,
            )
        
        # Phase 3: Poll for READY status
        try:
            final_result = self._poll_runtime(
                runtime_id=runtime_result.runtime_id,
                timeout_seconds=poll_timeout_seconds
            )
        except BedrockRuntimePollingError as e:
            logger.error(f"Runtime polling failed: {e.message}")
            
            # Attempt rollback on timeout
            rollback_success = self._rollback_runtime(runtime_result.runtime_id)
            
            error_msg = e.message
            if not rollback_success:
                error_msg += " (rollback also failed)"
            
            return DeployResult(
                success=False,
                runtime_id=runtime_result.runtime_id,
                runtime_arn=runtime_result.runtime_arn,
                error_message=error_msg,
                error_code=e.error_code or "S03-003-PollingTimeout",
                phase="polling",
                bootstrap_result=bootstrap_result,
                secret_arn=bootstrap_result.secret_arn,
                role_arn=bootstrap_result.role_arn,
                secret_created=bootstrap_result.secret_created,
                role_created=bootstrap_result.role_created,
                runtime_created=True,
            )
        except BedrockRuntimeError as e:
            # Runtime reached CREATE_FAILED state
            logger.error(f"Runtime creation failed during polling: {e.message}")
            
            # Attempt rollback
            rollback_success = self._rollback_runtime(runtime_result.runtime_id)
            
            error_msg = e.message
            if not rollback_success:
                error_msg += " (rollback also failed)"
            
            return DeployResult(
                success=False,
                runtime_id=runtime_result.runtime_id,
                runtime_arn=runtime_result.runtime_arn,
                status="CREATE_FAILED",
                error_message=error_msg,
                error_code=e.error_code or "S03-003-RuntimeFailed",
                phase="polling",
                bootstrap_result=bootstrap_result,
                secret_arn=bootstrap_result.secret_arn,
                role_arn=bootstrap_result.role_arn,
                secret_created=bootstrap_result.secret_created,
                role_created=bootstrap_result.role_created,
                runtime_created=True,
            )
        
        # Success!
        logger.info(f"Deployment completed successfully - runtime {final_result.runtime_id} is READY")
        
        return DeployResult(
            success=True,
            runtime_id=final_result.runtime_id,
            runtime_arn=final_result.runtime_arn,
            endpoint_url=final_result.endpoint_url,
            status=final_result.status,
            secret_arn=bootstrap_result.secret_arn,
            role_arn=bootstrap_result.role_arn,
            secret_created=bootstrap_result.secret_created,
            role_created=bootstrap_result.role_created,
            runtime_created=True,
            bootstrap_result=bootstrap_result,
            phase="completed",
        )
    
    def get_created_runtime_id(self) -> Optional[str]:
        """Get the runtime ID created during deployment (for testing/inspection).
        
        Returns:
            Runtime ID if created, None otherwise
        """
        return self._created_runtime_id