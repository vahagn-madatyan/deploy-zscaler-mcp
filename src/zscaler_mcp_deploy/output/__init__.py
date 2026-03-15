"""Output package for Zscaler MCP Deployer.

Provides utilities for generating MCP client configurations and
formatting connection instructions for operators.
"""

from .connection_formatter import ConnectionFormatter, FormatterError

__all__ = ["ConnectionFormatter", "FormatterError"]