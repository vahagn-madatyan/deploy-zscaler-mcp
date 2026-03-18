"""Configuration loader for Zscaler MCP Deployer.

Loads configuration from .env files and environment variables.
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import dotenv_values

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Supported Zscaler clouds
SUPPORTED_CLOUDS = frozenset(
    [
        "zscaler",
        "zscalerone",
        "zscalergov",
        "zscloudx",
        "zscalerbeta",
    ]
)

@dataclass
class ZscalerConfig:
    """Configuration for Zscaler API."""

    cloud: str
    username: str
    password: str
    api_key: str

@dataclass
class AWSConfig:
    """Configuration for AWS."""

    region: str
    profile: Optional[str] = None

@dataclass
class Config:
    """Main configuration class."""

    zscaler: ZscalerConfig
    aws: AWSConfig

class ConfigLoader:
    """Loads and validates configuration from .env file and environment."""

    def __init__(self, env_file: str | Path = ".env"):
        """Initialize configuration loader.

        Args:
            env_file: Path to the .env file to load.
        """
        self._env_file = Path(env_file)
        self._env_vars = {}

        # Load environment variables from .env file
        if self._env_file.exists():
            self._env_vars = dotenv_values(self._env_file)
            logger.info(f"Loaded configuration from {self._env_file}")
        else:
            logger.warning(f"Configuration file not found: {self._env_file}")

        # Merge with actual environment variables (environment takes precedence)
        self._env_vars.update(os.environ)

    def load_config(self) -> Config:
        """Load and validate configuration.

        Returns:
            Validated Config object.

        Raises:
            ValueError: If required configuration is missing or invalid.
        """
        # Load Zscaler configuration
        zscaler_config = self._load_zscaler_config()
        
        # Load AWS configuration
        aws_config = self._load_aws_config()

        return Config(
            zscaler=zscaler_config,
            aws=aws_config
        )

    def _load_zscaler_config(self) -> ZscalerConfig:
        """Load Zscaler configuration."""
        cloud = self._get_required_env_var("ZSCALER_CLOUD", default="zscaler")
        username = self._get_required_env_var("ZSCALER_USERNAME")
        password = self._get_required_env_var("ZSCALER_PASSWORD")
        api_key = self._get_required_env_var("ZSCALER_API_KEY")

        # Validate cloud
        if cloud not in SUPPORTED_CLOUDS:
            logger.warning(
                f"Unknown cloud '{cloud}'. "
                f"Supported clouds: {', '.join(SUPPORTED_CLOUDS)}. "
                f"Using anyway."
            )

        # Validate API key format (should be 32 hex characters)
        if len(api_key) != 32 or not all(c in '0123456789abcdefABCDEF' for c in api_key):
            logger.warning(
                f"API key does not appear to be valid format (32 hex characters). "
                f"Continuing anyway."
            )

        return ZscalerConfig(
            cloud=cloud,
            username=username,
            password=password,
            api_key=api_key,
        )

    def _load_aws_config(self) -> AWSConfig:
        """Load AWS configuration."""
        region = self._get_env_var("AWS_REGION", default="us-east-1")
        profile = self._get_env_var("AWS_PROFILE", default=None)

        return AWSConfig(
            region=region,
            profile=profile,
        )

    def _get_required_env_var(self, name: str, default: Optional[str] = None) -> str:
        """Get required environment variable."""
        value = self._env_vars.get(name, default)
        if value is None:
            raise ValueError(f"Required environment variable '{name}' is not set")
        return value

    def _get_env_var(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable with optional default."""
        return self._env_vars.get(name, default)