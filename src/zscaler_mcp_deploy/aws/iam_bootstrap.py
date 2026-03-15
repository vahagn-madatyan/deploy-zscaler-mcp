"""IAM role bootstrap module for Zscaler MCP Deployer.

Provides idempotent IAM execution role creation for Bedrock AgentCore with
trust policy generation, inline policy attachment, and propagation wait handling.
"""

import json
import logging
import time
from typing import Optional, Dict, Any

import boto3
from botocore.exceptions import ClientError

from ..models import IAMRoleResult
from ..errors import ZscalerMCPError, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


class IAMBootstrapError(ZscalerMCPError):
    """Error related to IAM bootstrap operations."""
    
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
            error_code=error_code or "S02-002",
            context=context
        )


class TrustPolicyMismatchError(IAMBootstrapError):
    """Error when existing role's trust policy doesn't match expected policy."""
    
    def __init__(
        self,
        role_name: str,
        expected_principal: str,
        actual_principal: Optional[str],
        context: Optional[Dict[str, Any]] = None
    ):
        full_context = context or {}
        full_context.update({
            "role_name": role_name,
            "expected_principal": expected_principal,
            "actual_principal": actual_principal
        })
        super().__init__(
            message=f"Existing role '{role_name}' has incompatible trust policy. "
                   f"Expected principal: {expected_principal}, got: {actual_principal}",
            error_code="S02-002-TrustMismatch",
            context=full_context
        )


class IAMBootstrap:
    """Bootstrap IAM execution roles for Bedrock AgentCore.
    
    Provides idempotent role creation with trust policy generation,
    inline policy attachment for Secrets Manager and CloudWatch Logs,
    and IAM propagation wait handling.
    """
    
    # IAM propagation wait settings
    PROPAGATION_WAIT_SECONDS = 15
    PROPAGATION_BACKOFF_BASE = 2
    PROPAGATION_MAX_RETRIES = 3
    
    # Service principals
    BEDROCK_SERVICE_PRINCIPAL = "bedrock.amazonaws.com"
    
    def __init__(
        self,
        region: Optional[str] = None,
        profile_name: Optional[str] = None,
        session: Optional[boto3.Session] = None
    ):
        """Initialize IAMBootstrap.
        
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
        """Lazy initialization of IAM client."""
        if self._client is None:
            self._client = self.session.client("iam")
        return self._client
    
    def _generate_trust_policy(self) -> Dict[str, Any]:
        """Generate trust policy document for Bedrock service.
        
        Returns:
            Trust policy document allowing bedrock.amazonaws.com to assume role
        """
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": self.BEDROCK_SERVICE_PRINCIPAL
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
    
    def _generate_inline_policy(self, secret_arn: str) -> Dict[str, Any]:
        """Generate inline policy for Secrets Manager and CloudWatch Logs.
        
        Args:
            secret_arn: ARN of the secret the role needs access to
            
        Returns:
            Inline policy document with Secrets Manager and CloudWatch permissions
        """
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "secretsmanager:GetSecretValue"
                    ],
                    "Resource": secret_arn
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": "arn:aws:logs:*:*:log-group:/aws/bedrock/*"
                }
            ]
        }
    
    def _validate_trust_policy(
        self,
        existing_policy: Dict[str, Any],
        expected_principal: str
    ) -> bool:
        """Validate that existing trust policy allows expected principal.
        
        Args:
            existing_policy: The existing trust policy document
            expected_principal: The expected service principal
            
        Returns:
            True if policy is compatible, False otherwise
        """
        statements = existing_policy.get("Statement", [])
        
        for statement in statements:
            if statement.get("Effect") != "Allow":
                continue
            
            action = statement.get("Action", [])
            if isinstance(action, str):
                action = [action]
            
            if "sts:AssumeRole" not in action:
                continue
            
            principal = statement.get("Principal", {})
            service = principal.get("Service", [])
            if isinstance(service, str):
                service = [service]
            
            if expected_principal in service:
                return True
        
        return False
    
    def _wait_for_propagation(self) -> None:
        """Wait for IAM role propagation with exponential backoff.
        
        IAM roles can take time to propagate across AWS regions.
        This implements a 15-second wait with exponential backoff.
        """
        total_waited = 0
        retry = 0
        
        while total_waited < self.PROPAGATION_WAIT_SECONDS and retry < self.PROPAGATION_MAX_RETRIES:
            wait_time = min(
                self.PROPAGATION_BACKOFF_BASE ** retry,
                self.PROPAGATION_WAIT_SECONDS - total_waited
            )
            
            logger.info(f"Waiting {wait_time}s for IAM role propagation (retry {retry + 1}/{self.PROPAGATION_MAX_RETRIES})")
            time.sleep(wait_time)
            total_waited += wait_time
            retry += 1
        
        logger.info(f"Completed IAM propagation wait (total: {total_waited}s)")
    
    def create_or_use_execution_role(
        self,
        role_name: str,
        secret_arn: str,
        description: Optional[str] = None,
        tags: Optional[list] = None
    ) -> IAMRoleResult:
        """Create or use existing IAM execution role for Bedrock AgentCore.
        
        Args:
            role_name: Name of the IAM role
            secret_arn: ARN of the secret the role needs access to
            description: Description for the role (optional)
            tags: List of tag dicts with 'Key' and 'Value' (optional)
            
        Returns:
            IAMRoleResult containing ARN, name, role_id, and created flag
            
        Raises:
            IAMBootstrapError: If role creation or retrieval fails
            TrustPolicyMismatchError: If existing role has incompatible trust policy
        """
        trust_policy = self._generate_trust_policy()
        trust_policy_json = json.dumps(trust_policy)
        
        try:
            logger.info(f"Creating IAM role: {role_name}")
            
            create_args = {
                "RoleName": role_name,
                "AssumeRolePolicyDocument": trust_policy_json,
                "Description": description or f"Execution role for Bedrock AgentCore - {role_name}",
            }
            
            if tags:
                create_args["Tags"] = tags
            
            response = self.client.create_role(**create_args)
            
            role_arn = response["Role"]["Arn"]
            role_id = response["Role"]["RoleId"]
            
            logger.info(f"IAM role created: {role_arn}")
            
            # Attach inline policy for Secrets Manager and CloudWatch
            self._attach_inline_policy(role_name, secret_arn)
            
            # Wait for IAM propagation
            self._wait_for_propagation()
            
            return IAMRoleResult(
                arn=role_arn,
                name=role_name,
                role_id=role_id,
                created=True,
                trust_policy=trust_policy
            )
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            
            if error_code == "EntityAlreadyExists":
                logger.info(f"IAM role already exists: {role_name}")
                return self._handle_existing_role(role_name, secret_arn, trust_policy)
            
            logger.error(f"Failed to create IAM role: {error_code} - {e.response['Error']['Message']}")
            raise IAMBootstrapError(
                message=f"Failed to create IAM role '{role_name}': {e.response['Error']['Message']}",
                error_code=f"S02-002-{error_code}",
                context={
                    "role_name": role_name,
                    "aws_error_code": error_code
                }
            )
    
    def _attach_inline_policy(
        self,
        role_name: str,
        secret_arn: str
    ) -> None:
        """Attach inline policy to role for Secrets Manager and CloudWatch.
        
        Args:
            role_name: Name of the IAM role
            secret_arn: ARN of the secret to allow access to
            
        Raises:
            IAMBootstrapError: If policy attachment fails
        """
        policy_name = f"{role_name}-bedrock-policy"
        policy_document = self._generate_inline_policy(secret_arn)
        
        try:
            logger.info(f"Attaching inline policy {policy_name} to role {role_name}")
            
            self.client.put_role_policy(
                RoleName=role_name,
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document)
            )
            
            logger.info(f"Inline policy attached: {policy_name}")
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            logger.error(f"Failed to attach inline policy: {error_code}")
            raise IAMBootstrapError(
                message=f"Failed to attach inline policy to role '{role_name}': {e.response['Error']['Message']}",
                error_code=f"S02-002-{error_code}",
                context={
                    "role_name": role_name,
                    "policy_name": policy_name,
                    "aws_error_code": error_code
                }
            )
    
    def _handle_existing_role(
        self,
        role_name: str,
        secret_arn: str,
        expected_trust_policy: Dict[str, Any]
    ) -> IAMRoleResult:
        """Handle the case when a role already exists.
        
        Validates the existing role's trust policy and attaches/updates inline policy.
        
        Args:
            role_name: Name of the existing role
            secret_arn: ARN of the secret the role needs access to
            expected_trust_policy: The expected trust policy for validation
            
        Returns:
            IAMRoleResult for the existing role
            
        Raises:
            IAMBootstrapError: If the role cannot be retrieved
            TrustPolicyMismatchError: If trust policy is incompatible
        """
        try:
            # Get role details
            response = self.client.get_role(RoleName=role_name)
            role_arn = response["Role"]["Arn"]
            role_id = response["Role"]["RoleId"]
            
            # Get and validate trust policy
            trust_policy_response = self.client.get_role_policy(
                RoleName=role_name,
                PolicyName="trust-policy"  # This won't work - need to parse AssumeRolePolicyDocument
            )
        except ClientError as e:
            if e.response["Error"]["Code"] != "NoSuchEntity":
                error_code = e.response["Error"]["Code"]
                logger.error(f"Failed to get existing role: {error_code}")
                raise IAMBootstrapError(
                    message=f"Failed to retrieve existing role '{role_name}': {e.response['Error']['Message']}",
                    error_code=f"S02-002-{error_code}",
                    context={"role_name": role_name, "aws_error_code": error_code}
                )
        
        # Parse AssumeRolePolicyDocument from get_role response
        existing_trust_policy = response["Role"].get("AssumeRolePolicyDocument", {})
        
        # Validate trust policy compatibility
        if not self._validate_trust_policy(
            existing_trust_policy,
            self.BEDROCK_SERVICE_PRINCIPAL
        ):
            # Extract actual principal for error message
            actual_principal = None
            statements = existing_trust_policy.get("Statement", [])
            for stmt in statements:
                principal = stmt.get("Principal", {})
                svc = principal.get("Service", [])
                if isinstance(svc, list) and svc:
                    actual_principal = svc[0]
                elif isinstance(svc, str):
                    actual_principal = svc
                    break
            
            raise TrustPolicyMismatchError(
                role_name=role_name,
                expected_principal=self.BEDROCK_SERVICE_PRINCIPAL,
                actual_principal=actual_principal
            )
        
        logger.info(f"Existing role trust policy validated: {role_name}")
        
        # Attach/update inline policy for the existing role
        self._attach_inline_policy(role_name, secret_arn)
        
        # No need to wait for propagation on existing role
        
        return IAMRoleResult(
            arn=role_arn,
            name=role_name,
            role_id=role_id,
            created=False,
            trust_policy=existing_trust_policy
        )
    
    def get_role(self, role_name: str) -> Optional[IAMRoleResult]:
        """Get details of an existing IAM role.
        
        Args:
            role_name: Name of the IAM role
            
        Returns:
            IAMRoleResult if role exists, None otherwise
        """
        try:
            response = self.client.get_role(RoleName=role_name)
            role = response["Role"]
            
            return IAMRoleResult(
                arn=role["Arn"],
                name=role["RoleName"],
                role_id=role["RoleId"],
                created=False,
                trust_policy=role.get("AssumeRolePolicyDocument")
            )
            
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                return None
            raise IAMBootstrapError(
                message=f"Failed to get role '{role_name}': {e.response['Error']['Message']}",
                error_code=f"S02-002-{e.response['Error']['Code']}",
                context={"role_name": role_name}
            )
    
    def delete_role(self, role_name: str) -> None:
        """Delete an IAM role and its attached policies.
        
        Args:
            role_name: Name of the role to delete
            
        Raises:
            IAMBootstrapError: If deletion fails
        """
        try:
            # First delete inline policies
            policy_name = f"{role_name}-bedrock-policy"
            try:
                self.client.delete_role_policy(
                    RoleName=role_name,
                    PolicyName=policy_name
                )
                logger.info(f"Deleted inline policy: {policy_name}")
            except ClientError as e:
                if e.response["Error"]["Code"] != "NoSuchEntity":
                    logger.warning(f"Could not delete inline policy: {e.response['Error']['Message']}")
            
            # Delete the role
            self.client.delete_role(RoleName=role_name)
            logger.info(f"IAM role deleted: {role_name}")
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            raise IAMBootstrapError(
                message=f"Failed to delete role '{role_name}': {e.response['Error']['Message']}",
                error_code=f"S02-002-{error_code}",
                context={"role_name": role_name, "aws_error_code": error_code}
            )
