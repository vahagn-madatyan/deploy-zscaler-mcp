"""AWS session validation utilities."""

import boto3
from botocore.exceptions import (
    ClientError,
    CredentialRetrievalError,
    NoCredentialsError,
    PartialCredentialsError,
    ProfileNotFound,
)
from typing import Optional, Tuple, List
import os

from ..errors import (
    AWSCredentialsError, 
    AWSRegionError, 
    ErrorCategory, 
    ErrorSeverity
)


class AWSSessionValidator:
    """Validate AWS session credentials and region configuration."""
    
    # Regions that support Amazon Bedrock
    BEDROCK_SUPPORTED_REGIONS = {
        "us-east-1",      # US East (N. Virginia)
        "us-west-2",      # US West (Oregon)
        "ap-south-1",     # Asia Pacific (Mumbai)
        "ap-northeast-1", # Asia Pacific (Tokyo)
        "ap-northeast-2", # Asia Pacific (Seoul)
        "ap-southeast-1", # Asia Pacific (Singapore)
        "ap-southeast-2", # Asia Pacific (Sydney)
        "ca-central-1",   # Canada (Central)
        "eu-central-1",   # Europe (Frankfurt)
        "eu-west-1",      # Europe (Ireland)
        "eu-west-2",      # Europe (London)
        "eu-west-3",      # Europe (Paris)
        "sa-east-1",      # South America (São Paulo)
    }

    def __init__(self, profile_name: Optional[str] = None, region: Optional[str] = None):
        """
        Initialize AWS session validator.
        
        Args:
            profile_name: AWS profile name (optional)
            region: AWS region (optional)
        """
        self.profile_name = profile_name
        self.region = region
        self.session = None

    def validate_credentials(self) -> Tuple[bool, str]:
        """
        Validate AWS credentials through the credential chain.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Try to create session with specified profile or default
            if self.profile_name:
                self.session = boto3.Session(profile_name=self.profile_name)
            else:
                self.session = boto3.Session()
            
            # Test credentials by making a minimal API call
            sts = self.session.client('sts')
            identity = sts.get_caller_identity()
            
            return True, f"Authenticated as {identity.get('Arn', 'unknown')}"
            
        except ProfileNotFound:
            error = AWSCredentialsError(
                message=f"AWS profile '{self.profile_name}' not found. Please check your AWS configuration.",
                error_code="ProfileNotFound",
                context={"profile_name": self.profile_name}
            )
            return False, error.message
        except NoCredentialsError:
            error = AWSCredentialsError(
                message=(
                    "No AWS credentials found. Please configure your AWS credentials using one of:\n"
                    "- AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables\n"
                    "- ~/.aws/credentials file\n"
                    "- AWS profile configuration"
                ),
                error_code="NoCredentialsError"
            )
            return False, error.message
        except PartialCredentialsError:
            error = AWSCredentialsError(
                message="Incomplete AWS credentials. Please ensure both access key and secret key are provided.",
                error_code="PartialCredentialsError"
            )
            return False, error.message
        except CredentialRetrievalError as e:
            error = AWSCredentialsError(
                message=f"Failed to retrieve AWS credentials: {str(e)}",
                error_code="CredentialRetrievalError",
                context={"error_detail": str(e)}
            )
            return False, error.message
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'SignatureDoesNotMatch':
                error = AWSCredentialsError(
                    message="AWS signature validation failed. Please check your secret access key.",
                    error_code=error_code,
                    context={"aws_service": "sts", "operation": "GetCallerIdentity"}
                )
                return False, error.message
            elif error_code == 'InvalidAccessKeyId':
                error = AWSCredentialsError(
                    message="Invalid AWS access key ID. Please check your credentials.",
                    error_code=error_code,
                    context={"aws_service": "sts", "operation": "GetCallerIdentity"}
                )
                return False, error.message
            elif error_code == 'AccessDenied':
                error = AWSCredentialsError(
                    message=(
                        "AWS credentials valid but insufficient permissions. "
                        "At minimum, the sts:GetCallerIdentity permission is required."
                    ),
                    error_code=error_code,
                    context={"aws_service": "sts", "operation": "GetCallerIdentity"}
                )
                return False, error.message
            else:
                error = AWSCredentialsError(
                    message=f"AWS authentication failed: {error_code} - {e.response['Error']['Message']}",
                    error_code=error_code,
                    context={
                        "aws_service": "sts", 
                        "operation": "GetCallerIdentity",
                        "error_message": e.response['Error']['Message']
                    }
                )
                return False, error.message
        except Exception as e:
            error = AWSCredentialsError(
                message=f"Unexpected error validating AWS credentials: {str(e)}",
                error_code="UnexpectedError",
                context={"error_type": type(e).__name__, "error_detail": str(e)}
            )
            return False, error.message

    def validate_region(self, region: Optional[str] = None) -> Tuple[bool, str]:
        """
        Validate that the region supports Amazon Bedrock.
        
        Args:
            region: Region to validate (uses session region if not provided)
            
        Returns:
            Tuple of (is_valid, message)
        """
        target_region = region or self.region or (self.session.region_name if self.session else None)
        
        if not target_region:
            error = AWSRegionError(
                message="No AWS region specified. Please specify an AWS region.",
                context={"available_regions": sorted(list(self.BEDROCK_SUPPORTED_REGIONS))}
            )
            return False, error.message
            
        if target_region not in self.BEDROCK_SUPPORTED_REGIONS:
            error = AWSRegionError(
                message=(
                    f"Region '{target_region}' does not support Amazon Bedrock.\n"
                    f"Supported regions: {', '.join(sorted(self.BEDROCK_SUPPORTED_REGIONS))}"
                ),
                context={
                    "specified_region": target_region,
                    "supported_regions": sorted(list(self.BEDROCK_SUPPORTED_REGIONS))
                }
            )
            return False, error.message
            
        return True, f"Region '{target_region}' supports Amazon Bedrock"

    def get_available_regions(self) -> List[str]:
        """
        Get a sorted list of Bedrock-supported regions.
        
        Returns:
            List of supported regions
        """
        return sorted(list(self.BEDROCK_SUPPORTED_REGIONS))

    def prompt_for_region(self) -> Optional[str]:
        """
        Prompt user to select a region from the supported list.
        
        Returns:
            Selected region string or None if cancelled
        """
        regions = self.get_available_regions()
        
        print("\nAvailable AWS regions that support Amazon Bedrock:")
        for i, region in enumerate(regions, 1):
            print(f"  {i:2d}. {region}")
        
        try:
            choice = input(f"\nSelect a region (1-{len(regions)}) or press Enter to cancel: ").strip()
            if not choice:
                return None
            
            index = int(choice) - 1
            if 0 <= index < len(regions):
                return regions[index]
            else:
                print("Invalid selection. Please try again.")
                return self.prompt_for_region()
        except (ValueError, KeyboardInterrupt):
            return None

    def validate_session(self, region: Optional[str] = None) -> Tuple[bool, List[str]]:
        """
        Comprehensive validation of AWS session.
        
        Args:
            region: Specific region to validate (optional)
            
        Returns:
            Tuple of (is_valid, list_of_messages)
        """
        messages = []
        
        # Validate credentials
        creds_valid, creds_msg = self.validate_credentials()
        messages.append(creds_msg)
        
        if not creds_valid:
            return False, messages
            
        # Validate region
        region_valid, region_msg = self.validate_region(region)
        messages.append(region_msg)
        
        if not region_valid:
            return False, messages
            
        return True, messages