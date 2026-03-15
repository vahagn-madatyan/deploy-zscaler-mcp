"""Zscaler credential validation utilities."""

import re
import requests
from typing import Optional, Tuple, List
from datetime import datetime, timedelta

from ..errors import (
    ZscalerCredentialsError, 
    ZscalerConnectivityError, 
    ZscalerAuthenticationError,
    ErrorCategory, 
    ErrorSeverity
)


class ZscalerCloud:
    """Zscaler cloud endpoints."""
    
    # Zscaler cloud domains
    CLOUDS = {
        'zscaler': 'https://zsapi.zscaler.net',
        'zscalerone': 'https://zsapi.zscalerone.net',
        'zscalertwo': 'https://zsapi.zscalertwo.net',
        'zscalerthree': 'https://zsapi.zscalerthree.net',
        'zscalergov': 'https://zsapi.zscalergov.net',
        'zscalerten': 'https://zsapi.zscalerten.net',
    }


class ZscalerCredentialValidator:
    """Validate Zscaler API credentials and connectivity."""
    
    def __init__(self, 
                 cloud: str = 'zscaler',
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 api_key: Optional[str] = None,
                 obfuscate: bool = True):
        """
        Initialize Zscaler credential validator.
        
        Args:
            cloud: Zscaler cloud name (e.g., 'zscaler', 'zscalerone')
            username: Zscaler username
            password: Zscaler password
            api_key: Zscaler API key
            obfuscate: Whether to obfuscate sensitive data in logs
        """
        self.cloud = cloud.lower()
        self.username = username
        self.password = password
        self.api_key = api_key
        self.obfuscate = obfuscate
        self.base_url = self._get_base_url()
        self.session = requests.Session()
        
    def _get_base_url(self) -> str:
        """
        Get the base URL for the specified Zscaler cloud.
        
        Returns:
            Base URL for API calls
        """
        return ZscalerCloud.CLOUDS.get(self.cloud, ZscalerCloud.CLOUDS['zscaler'])
    
    def _obfuscate_string(self, value: str, show_chars: int = 4) -> str:
        """
        Obfuscate a string for safe logging.
        
        Args:
            value: String to obfuscate
            show_chars: Number of characters to show at the beginning/end
            
        Returns:
            Obfuscated string
        """
        if not value or len(value) <= show_chars * 2:
            return "*" * len(value) if value else ""
        return value[:show_chars] + "*" * (len(value) - show_chars * 2) + value[-show_chars:]
    
    def _obfuscate_creds(self) -> dict:
        """
        Get obfuscated credentials for logging.
        
        Returns:
            Dictionary with obfuscated credential info
        """
        if not self.obfuscate:
            return {
                'username': self.username,
                'cloud': self.cloud,
                'api_key_length': len(self.api_key) if self.api_key else 0
            }
        
        return {
            'username': self._obfuscate_string(self.username) if self.username else None,
            'cloud': self.cloud,
            'api_key_length': len(self.api_key) if self.api_key else 0
        }
    
    def validate_credential_format(self) -> Tuple[bool, str]:
        """
        Validate Zscaler credential format.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if we have the basic required credentials
        if not self.username:
            error = ZscalerCredentialsError(
                message="Zscaler username is required",
                context={"missing_field": "username"}
            )
            return False, error.message
        
        if not self.password:
            error = ZscalerCredentialsError(
                message="Zscaler password is required",
                context={"missing_field": "password"}
            )
            return False, error.message
            
        if not self.api_key:
            error = ZscalerCredentialsError(
                message="Zscaler API key is required",
                context={"missing_field": "api_key"}
            )
            return False, error.message
            
        # Validate username format (should be email)
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, self.username):
            error = ZscalerCredentialsError(
                message=f"Invalid username format. Expected email address, got: {self._obfuscate_string(self.username) if self.obfuscate else self.username}",
                context={
                    "username_provided": self._obfuscate_string(self.username) if self.obfuscate else self.username,
                    "expected_format": "email"
                }
            )
            return False, error.message
            
        # Validate API key format (should be 32 hex characters)
        api_key_pattern = r'^[a-fA-F0-9]{32}$'
        if not re.match(api_key_pattern, self.api_key):
            obfuscated_key = self._obfuscate_string(self.api_key) if self.obfuscate else self.api_key
            error = ZscalerCredentialsError(
                message=f"Invalid API key format. Expected 32 hex characters, got: {obfuscated_key}",
                context={
                    "api_key_provided": obfuscated_key,
                    "expected_format": "32 hex characters"
                }
            )
            return False, error.message
            
        return True, "Zscaler credential format is valid"
    
    def validate_connectivity(self, timeout: int = 10) -> Tuple[bool, str]:
        """
        Validate connectivity to Zscaler cloud.
        
        Args:
            timeout: Request timeout in seconds
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            # Make a simple GET request to the base URL
            response = self.session.get(
                f"{self.base_url}/api/v1/status",
                timeout=timeout
            )
            
            if response.status_code == 401:
                # This is expected for unauthenticated requests - it means we can reach the server
                return True, f"Successfully connected to Zscaler {self.cloud} cloud"
            elif response.status_code == 200:
                # Server is responding
                return True, f"Successfully connected to Zscaler {self.cloud} cloud"
            elif response.status_code in [403, 404]:
                # These responses still indicate connectivity
                return True, f"Successfully connected to Zscaler {self.cloud} cloud"
            else:
                error = ZscalerConnectivityError(
                    message=f"Unexpected response from Zscaler {self.cloud} cloud: {response.status_code} - {response.text[:200]}",
                    context={
                        "cloud": self.cloud,
                        "status_code": response.status_code,
                        "response_text": response.text[:200]
                    }
                )
                return False, error.message
                
        except requests.exceptions.Timeout:
            error = ZscalerConnectivityError(
                message=f"Connection to Zscaler {self.cloud} cloud timed out after {timeout} seconds",
                context={
                    "cloud": self.cloud,
                    "timeout_seconds": timeout
                }
            )
            return False, error.message
        except requests.exceptions.ConnectionError:
            error = ZscalerConnectivityError(
                message=f"Failed to connect to Zscaler {self.cloud} cloud. Please check your network connectivity and cloud name.",
                context={
                    "cloud": self.cloud,
                    "base_url": self.base_url
                }
            )
            return False, error.message
        except requests.exceptions.RequestException as e:
            error = ZscalerConnectivityError(
                message=f"Error connecting to Zscaler {self.cloud} cloud: {str(e)}",
                context={
                    "cloud": self.cloud,
                    "error_type": type(e).__name__,
                    "error_detail": str(e)
                }
            )
            return False, error.message
        except Exception as e:
            error = ZscalerConnectivityError(
                message=f"Unexpected error connecting to Zscaler {self.cloud} cloud: {str(e)}",
                context={
                    "cloud": self.cloud,
                    "error_type": type(e).__name__,
                    "error_detail": str(e)
                }
            )
            return False, error.message
    
    def authenticate(self, timeout: int = 30) -> Tuple[bool, str, Optional[str]]:
        """
        Authenticate with Zscaler API to validate credentials.
        
        Args:
            timeout: Request timeout in seconds
            
        Returns:
            Tuple of (is_valid, message, session_id)
        """
        try:
            # Prepare authentication payload
            auth_payload = {
                "username": self.username,
                "password": self.password,
                "apiKey": self.api_key,
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
            
            # Make authentication request
            response = self.session.post(
                f"{self.base_url}/api/v1/authenticate",
                json=auth_payload,
                timeout=timeout
            )
            
            if response.status_code == 200:
                auth_data = response.json()
                session_id = auth_data.get('JSESSIONID')
                if session_id:
                    return True, "Successfully authenticated with Zscaler API", session_id
                else:
                    return False, "Authentication successful but no session ID returned", None
            elif response.status_code == 401:
                error = ZscalerAuthenticationError(
                    message="Authentication failed: Invalid credentials. Please check your username, password, and API key.",
                    context={
                        "status_code": response.status_code,
                        "cloud": self.cloud
                    }
                )
                return False, error.message, None
            elif response.status_code == 403:
                error = ZscalerAuthenticationError(
                    message="Authentication forbidden: Account may be locked or API access not enabled.",
                    context={
                        "status_code": response.status_code,
                        "cloud": self.cloud
                    }
                )
                return False, error.message, None
            elif response.status_code == 429:
                error = ZscalerAuthenticationError(
                    message="Rate limit exceeded. Please wait before trying again.",
                    context={
                        "status_code": response.status_code,
                        "cloud": self.cloud
                    }
                )
                return False, error.message, None
            else:
                error = ZscalerAuthenticationError(
                    message=f"Authentication failed with status {response.status_code}: {response.text[:200]}",
                    context={
                        "status_code": response.status_code,
                        "response_text": response.text[:200],
                        "cloud": self.cloud
                    }
                )
                return False, error.message, None
                
        except requests.exceptions.Timeout:
            error = ZscalerAuthenticationError(
                message=f"Authentication timed out after {timeout} seconds",
                context={
                    "timeout_seconds": timeout,
                    "cloud": self.cloud
                }
            )
            return False, error.message, None
        except requests.exceptions.ConnectionError:
            error = ZscalerAuthenticationError(
                message="Failed to connect to Zscaler authentication API",
                context={
                    "cloud": self.cloud,
                    "base_url": self.base_url
                }
            )
            return False, error.message, None
        except requests.exceptions.RequestException as e:
            error = ZscalerAuthenticationError(
                message=f"Error during authentication: {str(e)}",
                context={
                    "error_type": type(e).__name__,
                    "error_detail": str(e),
                    "cloud": self.cloud
                }
            )
            return False, error.message, None
        except Exception as e:
            error = ZscalerAuthenticationError(
                message=f"Unexpected error during authentication: {str(e)}",
                context={
                    "error_type": type(e).__name__,
                    "error_detail": str(e),
                    "cloud": self.cloud
                }
            )
            return False, error.message, None
    
    def validate_session(self, session_id: str, timeout: int = 10) -> Tuple[bool, str]:
        """
        Validate an existing session.
        
        Args:
            session_id: Session ID to validate
            timeout: Request timeout in seconds
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            # Set session header
            self.session.headers.update({'JSESSIONID': session_id})
            
            # Make a session validation request
            response = self.session.get(
                f"{self.base_url}/api/v1/status",
                timeout=timeout
            )
            
            if response.status_code == 200:
                return True, "Session is valid"
            elif response.status_code == 401:
                error = ZscalerAuthenticationError(
                    message="Session is invalid or expired",
                    context={
                        "status_code": response.status_code
                    }
                )
                return False, error.message
            else:
                error = ZscalerAuthenticationError(
                    message=f"Unexpected response during session validation: {response.status_code}",
                    context={
                        "status_code": response.status_code
                    }
                )
                return False, error.message
                
        except Exception as e:
            error = ZscalerAuthenticationError(
                message=f"Error validating session: {str(e)}",
                context={
                    "error_type": type(e).__name__,
                    "error_detail": str(e)
                }
            )
            return False, error.message
    
    def validate_credentials(self, timeout: int = 30) -> Tuple[bool, List[str]]:
        """
        Comprehensive validation of Zscaler credentials.
        
        Args:
            timeout: Request timeout in seconds
            
        Returns:
            Tuple of (is_valid, list_of_messages)
        """
        messages = []
        
        # Validate credential format
        format_valid, format_msg = self.validate_credential_format()
        messages.append(format_msg)
        
        if not format_valid:
            return False, messages
            
        # Validate connectivity
        connectivity_valid, connectivity_msg = self.validate_connectivity(timeout)
        messages.append(connectivity_msg)
        
        if not connectivity_valid:
            return False, messages
            
        # Validate authentication
        auth_valid, auth_msg, session_id = self.authenticate(timeout)
        messages.append(auth_msg)
        
        if not auth_valid:
            return False, messages
            
        # Validate session (if we got one)
        if session_id:
            session_valid, session_msg = self.validate_session(session_id, timeout)
            messages.append(session_msg)
            
            if not session_valid:
                return False, messages
        
        return True, messages