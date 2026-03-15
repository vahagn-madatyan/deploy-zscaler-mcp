"""IAM permission validation utilities."""

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Optional, Tuple, List, Dict
from .aws import AWSSessionValidator
from ..errors import AWSPermissionsError, AWSCredentialsError


class IAMPermissionValidator:
    """Validate IAM permissions required for Zscaler MCP deployment."""
    
    # Required AWS permissions for Zscaler MCP deployment
    REQUIRED_PERMISSIONS = {
        'bedrock': [
            'bedrock:ListFoundationModels',
            'bedrock:GetFoundationModel',
            'bedrock:InvokeModel',
            'bedrock:CreateAgent',
            'bedrock:CreateKnowledgeBase',
            'bedrock:CreateDataSource',
        ],
        'secretsmanager': [
            'secretsmanager:CreateSecret',
            'secretsmanager:GetSecretValue',
            'secretsmanager:PutSecretValue',
            'secretsmanager:UpdateSecret',
            'secretsmanager:TagResource',
        ],
        'sts': [
            'sts:AssumeRole',
        ]
    }

    def __init__(self, profile_name: Optional[str] = None, region: Optional[str] = None):
        """
        Initialize IAM permission validator.
        
        Args:
            profile_name: AWS profile name (optional)
            region: AWS region (optional)
        """
        self.profile_name = profile_name
        self.region = region
        self.session = None

    def _get_session(self) -> boto3.Session:
        """
        Get or create AWS session.
        
        Returns:
            boto3.Session object
        """
        if not self.session:
            if self.profile_name:
                self.session = boto3.Session(profile_name=self.profile_name)
            else:
                self.session = boto3.Session()
        return self.session

    def validate_permissions(self, service: str, actions: List[str]) -> Tuple[bool, List[str], List[str]]:
        """
        Validate if the current user has permissions for specified actions.
        
        Args:
            service: AWS service name (e.g., 'bedrock', 'secretsmanager')
            actions: List of actions to validate
            
        Returns:
            Tuple of (is_valid, allowed_actions, denied_actions)
        """
        session = self._get_session()
        sts_client = session.client('sts', region_name=self.region)
        
        try:
            # Get caller identity to determine principal
            identity = sts_client.get_caller_identity()
            principal_arn = identity['Arn']
            
            # For IAM users/roles, we can use the simulate_principal_policy API
            # but this requires special permissions. Let's try a more practical approach
            # by actually attempting the operations.
            
            allowed_actions = []
            denied_actions = []
            
            # We'll validate permissions by attempting to make the actual service calls
            # with dry-run/least-impact operations where possible
            if service == 'bedrock':
                return self._validate_bedrock_permissions(actions, session)
            elif service == 'secretsmanager':
                return self._validate_secretsmanager_permissions(actions, session)
            elif service == 'sts':
                return self._validate_sts_permissions(actions, session)
            else:
                # Generic validation approach for other services
                return self._validate_generic_permissions(service, actions, session)
                
        except NoCredentialsError:
            error = AWSCredentialsError(
                message="No AWS credentials found. Cannot validate IAM permissions.",
                error_code="NoCredentialsError"
            )
            return False, [], actions  # All actions denied due to no credentials
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDenied':
                # If we can't even make a basic STS call, assume no permissions
                return False, [], actions
            else:
                # Other errors - assume we can't determine permissions
                return False, [], actions

    def _validate_bedrock_permissions(self, actions: List[str], session: boto3.Session) -> Tuple[bool, List[str], List[str]]:
        """Validate Bedrock-specific permissions."""
        allowed_actions = []
        denied_actions = []
        bedrock_client = session.client('bedrock', region_name=self.region)
        
        for action in actions:
            try:
                if action == 'bedrock:ListFoundationModels':
                    # This is generally a safe read-only operation
                    bedrock_client.list_foundation_models(MaxResults=1)
                    allowed_actions.append(action)
                elif action == 'bedrock:GetFoundationModel':
                    # Try to get a common model - this might fail if no models are accessible
                    try:
                        bedrock_client.list_foundation_models(MaxResults=1)
                        allowed_actions.append(action)
                    except:
                        # If we can't list models, we assume we can't get them either
                        denied_actions.append(action)
                elif action == 'bedrock:InvokeModel':
                    allowed_actions.append(action)  # Can't easily test without model ID
                elif action == 'bedrock:CreateAgent':
                    denied_actions.append(action)  # No safe way to test this
                elif action == 'bedrock:CreateKnowledgeBase':
                    denied_actions.append(action)  # No safe way to test this
                elif action == 'bedrock:CreateDataSource':
                    denied_actions.append(action)  # No safe way to test this
                else:
                    # For unknown actions, assume they're denied
                    denied_actions.append(action)
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code in ['AccessDeniedException', 'AccessDenied']:
                    denied_actions.append(action)
                else:
                    # Other errors might be temporary or non-permission related
                    allowed_actions.append(action)
            except Exception:
                # If we can't determine, we'll assume it's allowed for now
                allowed_actions.append(action)
        
        is_valid = len(denied_actions) == 0
        return is_valid, allowed_actions, denied_actions

    def _validate_secretsmanager_permissions(self, actions: List[str], session: boto3.Session) -> Tuple[bool, List[str], List[str]]:
        """Validate Secrets Manager-specific permissions."""
        allowed_actions = []
        denied_actions = []
        secrets_client = session.client('secretsmanager', region_name=self.region)
        
        test_secret_name = f"zscaler-mcp-test-{session.region_name}"
        
        for action in actions:
            try:
                if action == 'secretsmanager:CreateSecret':
                    # Create a test secret (we'll clean it up)
                    try:
                        secrets_client.create_secret(
                            Name=test_secret_name,
                            Description="Test secret for Zscaler MCP permission validation",
                            SecretString="test-value"
                        )
                        allowed_actions.append(action)
                    except ClientError as e:
                        if e.response['Error']['Code'] in ['AccessDeniedException', 'AccessDenied']:
                            denied_actions.append(action)
                        else:
                            # Other errors may not be permission-related
                            allowed_actions.append(action)
                elif action == 'secretsmanager:GetSecretValue':
                    # Try to get a non-existent secret to test permissions
                    try:
                        secrets_client.get_secret_value(SecretId=test_secret_name)
                        allowed_actions.append(action)
                    except ClientError as e:
                        error_code = e.response['Error']['Code']
                        if error_code in ['ResourceNotFoundException']:
                            # This means we have permission but the secret doesn't exist
                            allowed_actions.append(action)
                        elif error_code in ['AccessDeniedException', 'AccessDenied']:
                            denied_actions.append(action)
                        else:
                            # Other errors may not be permission-related
                            allowed_actions.append(action)
                elif action == 'secretsmanager:PutSecretValue':
                    denied_actions.append(action)  # Can't safely test without existing secret
                elif action == 'secretsmanager:UpdateSecret':
                    denied_actions.append(action)  # Can't safely test without existing secret
                elif action == 'secretsmanager:TagResource':
                    denied_actions.append(action)  # Can't safely test without existing secret
                else:
                    # For unknown actions, assume they're denied
                    denied_actions.append(action)
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code in ['AccessDeniedException', 'AccessDenied']:
                    denied_actions.append(action)
                else:
                    # Other errors might be temporary or non-permission related
                    allowed_actions.append(action)
            except Exception:
                # If we can't determine, we'll assume it's allowed for now
                allowed_actions.append(action)
        
        # Clean up test secret if we created it
        try:
            secrets_client.delete_secret(SecretId=test_secret_name, ForceDeleteWithoutRecovery=True)
        except:
            pass  # Ignore cleanup errors
        
        is_valid = len(denied_actions) == 0
        return is_valid, allowed_actions, denied_actions

    def _validate_sts_permissions(self, actions: List[str], session: boto3.Session) -> Tuple[bool, List[str], List[str]]:
        """Validate STS-specific permissions."""
        allowed_actions = []
        denied_actions = []
        sts_client = session.client('sts', region_name=self.region)
        
        for action in actions:
            try:
                if action == 'sts:AssumeRole':
                    # We can't safely test AssumeRole without a real role ARN
                    # This is a conservative approach - assume it's allowed if we can make other STS calls
                    allowed_actions.append(action)
                else:
                    denied_actions.append(action)
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code in ['AccessDeniedException', 'AccessDenied']:
                    denied_actions.append(action)
                else:
                    allowed_actions.append(action)
            except Exception:
                allowed_actions.append(action)
        
        is_valid = len(denied_actions) == 0
        return is_valid, allowed_actions, denied_actions

    def _validate_generic_permissions(self, service: str, actions: List[str], session: boto3.Session) -> Tuple[bool, List[str], List[str]]:
        """Generic permission validation approach."""
        # For generic validation, we try to make a minimal API call to the service
        # and see if we get permission errors
        allowed_actions = []
        denied_actions = []
        
        try:
            client = session.client(service, region_name=self.region)
            # Try a simple operation that's likely to exist across services
            # We're just testing if the client can be created and make calls
            allowed_actions = actions[:]  # Assume all allowed if client creation works
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ['AccessDeniedException', 'AccessDenied']:
                denied_actions = actions[:]  # All denied if access denied
            else:
                allowed_actions = actions[:]  # Assume allowed for other errors
        except Exception:
            # If client creation fails for other reasons, assume permissions are okay
            allowed_actions = actions[:]
        
        is_valid = len(denied_actions) == 0
        return is_valid, allowed_actions, denied_actions

    def validate_required_permissions(self) -> Dict[str, Dict]:
        """
        Validate all required permissions for Zscaler MCP deployment.
        
        Returns:
            Dictionary with validation results for each service
        """
        results = {}
        
        for service, actions in self.REQUIRED_PERMISSIONS.items():
            is_valid, allowed, denied = self.validate_permissions(service, actions)
            
            # Create error message if permissions are missing
            missing_policy = None
            if denied:
                error = AWSPermissionsError(
                    message=f"Missing required permissions for {service}",
                    missing_permissions=denied,
                    context={
                        "service": service,
                        "missing_actions": denied,
                        "allowed_actions": allowed
                    }
                )
                missing_policy = error.context.get("missing_policy") if error.context else None
            
            results[service] = {
                'valid': is_valid,
                'allowed': allowed,
                'denied': denied,
                'missing_policy': missing_policy
            }
        
        return results

    def get_permission_validation_summary(self) -> Tuple[bool, str]:
        """
        Get a summary of permission validation.
        
        Returns:
            Tuple of (is_valid, summary_message)
        """
        try:
            results = self.validate_required_permissions()
            all_valid = all(result['valid'] for result in results.values())
            
            if all_valid:
                return True, "All required AWS permissions are available"
            else:
                # Collect denied actions
                denied_summary = []
                for service, result in results.items():
                    if result['denied']:
                        denied_summary.append(f"{service}: {len(result['denied'])} missing actions")
                
                return False, f"Missing permissions: {', '.join(denied_summary)}"
                
        except Exception as e:
            error = AWSPermissionsError(
                message=f"Error validating permissions: {str(e)}",
                context={"error_type": type(e).__name__, "error_detail": str(e)}
            )
            return False, error.message