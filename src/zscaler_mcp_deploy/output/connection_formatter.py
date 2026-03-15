"""Connection Formatter for Zscaler MCP Deployer.

Provides utilities to generate copy-paste-ready MCP client configuration
for Claude Desktop and Cursor. Handles cross-platform config file paths,
existing config merging, and proper stdio transport configuration.
"""

import json
import logging
import os
import platform
from pathlib import Path
from typing import Any, Dict, Optional

from ..errors import FormatterError

logger = logging.getLogger(__name__)


class ConnectionFormatter:
    """Formatter for MCP client connection configuration.
    
    Generates copy-paste-ready MCP client configuration for Claude Desktop
    and Cursor. Handles cross-platform config file paths, existing config
    merging, and proper stdio transport configuration.
    
    Example:
        formatter = ConnectionFormatter()
        
        # Generate Claude Desktop config
        config = formatter.format_claude_desktop_config(
            runtime_id="my-runtime",
            runtime_arn="arn:aws:bedrock:us-east-1:123456789:agentcore-runtime/my-runtime",
            region="us-east-1"
        )
        
        # Write config to file
        formatter.write_claude_config(config)
        
        # Get config path for current platform
        config_path = formatter.get_claude_config_path()
    """
    
    # MCP stdio transport configuration defaults
    DEFAULT_COMMAND = "aws"
    DEFAULT_TIMEOUT = 300  # 5 minutes
    
    def __init__(self):
        """Initialize ConnectionFormatter."""
        self._platform = platform.system().lower()
        logger.debug(f"ConnectionFormatter initialized for platform: {self._platform}")
    
    @property
    def platform(self) -> str:
        """Get the current platform identifier.
        
        Returns:
            Platform string: 'darwin' (macOS), 'linux', or 'windows'
        """
        return self._platform
    
    def is_macos(self) -> bool:
        """Check if running on macOS.
        
        Returns:
            True if on macOS, False otherwise
        """
        return self._platform == "darwin"
    
    def is_linux(self) -> bool:
        """Check if running on Linux.
        
        Returns:
            True if on Linux, False otherwise
        """
        return self._platform == "linux"
    
    def is_windows(self) -> bool:
        """Check if running on Windows.
        
        Returns:
            True if on Windows, False otherwise
        """
        return self._platform == "windows"
    
    def get_claude_config_path(self) -> Path:
        """Get the Claude Desktop config file path for the current platform.
        
        Platform paths:
        - macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
        - Linux: ~/.config/Claude/claude_desktop_config.json
        - Windows: %APPDATA%/Claude/claude_desktop_config.json
        
        Returns:
            Path object for the Claude Desktop config file
            
        Raises:
            FormatterError: If platform is not supported
        """
        home = Path.home()
        
        if self.is_macos():
            path = home / "Library/Application Support/Claude/claude_desktop_config.json"
        elif self.is_linux():
            path = home / ".config/Claude/claude_desktop_config.json"
        elif self.is_windows():
            appdata = os.environ.get("APPDATA")
            if not appdata:
                raise FormatterError(
                    message="APPDATA environment variable not set (Windows)",
                    error_code="S04-003-003",
                    context={"platform": self._platform}
                )
            path = Path(appdata) / "Claude/claude_desktop_config.json"
        else:
            raise FormatterError(
                message=f"Unsupported platform: {self._platform}",
                error_code="S04-003-004",
                context={"platform": self._platform}
            )
        
        logger.debug(f"Claude Desktop config path: {path}")
        return path
    
    def get_cursor_config_path(self) -> Path:
        """Get the Cursor MCP config file path for the current platform.
        
        Platform paths:
        - macOS: ~/.cursor/mcp.json
        - Linux: ~/.config/Cursor/mcp.json
        - Windows: %USERPROFILE%/.cursor/mcp.json
        
        Returns:
            Path object for the Cursor MCP config file
            
        Raises:
            FormatterError: If platform is not supported
        """
        home = Path.home()
        
        if self.is_macos():
            path = home / ".cursor/mcp.json"
        elif self.is_linux():
            path = home / ".config/Cursor/mcp.json"
        elif self.is_windows():
            userprofile = os.environ.get("USERPROFILE")
            if not userprofile:
                raise FormatterError(
                    message="USERPROFILE environment variable not set (Windows)",
                    error_code="S04-003-003",
                    context={"platform": self._platform}
                )
            path = Path(userprofile) / ".cursor/mcp.json"
        else:
            raise FormatterError(
                message=f"Unsupported platform: {self._platform}",
                error_code="S04-003-004",
                context={"platform": self._platform}
            )
        
        logger.debug(f"Cursor config path: {path}")
        return path
    
    def format_claude_desktop_config(
        self,
        runtime_id: str,
        runtime_arn: str,
        region: str,
        timeout: int = DEFAULT_TIMEOUT
    ) -> Dict[str, Any]:
        """Generate Claude Desktop MCP configuration.
        
        Creates an MCP server configuration entry for Claude Desktop with
        stdio transport using AWS CLI bedrock-agent invoke command.
        
        Args:
            runtime_id: Runtime identifier
            runtime_arn: Full runtime ARN
            region: AWS region (e.g., 'us-east-1')
            timeout: Command timeout in seconds (default: 300)
            
        Returns:
            Configuration dictionary for mcpServers entry
            
        Example output:
            {
                "mcpServers": {
                    "zscaler-bedrock-runtime": {
                        "command": "aws",
                        "args": [
                            "bedrock-agent",
                            "invoke-runtime",
                            "--runtime-id", "my-runtime",
                            "--region", "us-east-1"
                        ],
                        "env": {
                            "AWS_DEFAULT_REGION": "us-east-1"
                        },
                        "timeout": 300
                    }
                }
            }
        """
        server_name = "zscaler-bedrock-runtime"
        
        config = {
            "mcpServers": {
                server_name: {
                    "command": self.DEFAULT_COMMAND,
                    "args": [
                        "bedrock-agent-runtime",
                        "invoke-agent",
                        "--agent-id", runtime_id,
                        "--region", region
                    ],
                    "env": {
                        "AWS_DEFAULT_REGION": region
                    },
                    "timeout": timeout
                }
            }
        }
        
        logger.debug(f"Generated Claude Desktop config for runtime: {runtime_id}")
        logger.debug(f"Config structure: {json.dumps(config, indent=2)}")
        
        return config
    
    def format_cursor_config(
        self,
        runtime_id: str,
        runtime_arn: str,
        region: str,
        timeout: int = DEFAULT_TIMEOUT
    ) -> Dict[str, Any]:
        """Generate Cursor MCP configuration.
        
        Creates an MCP server configuration entry for Cursor with
        stdio transport using AWS CLI bedrock-agent invoke command.
        Cursor uses a similar structure to Claude Desktop but with
        slightly different file location.
        
        Args:
            runtime_id: Runtime identifier
            runtime_arn: Full runtime ARN
            region: AWS region (e.g., 'us-east-1')
            timeout: Command timeout in seconds (default: 300)
            
        Returns:
            Configuration dictionary for mcpServers entry
        """
        # Cursor uses the same MCP config format as Claude Desktop
        return self.format_claude_desktop_config(
            runtime_id=runtime_id,
            runtime_arn=runtime_arn,
            region=region,
            timeout=timeout
        )
    
    def read_existing_config(self, config_path: Path) -> Optional[Dict[str, Any]]:
        """Read existing MCP client configuration from file.
        
        Args:
            config_path: Path to the config file
            
        Returns:
            Parsed JSON config dict, or None if file doesn't exist
            
        Raises:
            FormatterError: If file exists but contains invalid JSON
        """
        if not config_path.exists():
            logger.debug(f"No existing config found at: {config_path}")
            return None
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            if not content.strip():
                logger.debug(f"Config file is empty: {config_path}")
                return None
            
            config = json.loads(content)
            logger.debug(f"Read existing config from: {config_path}")
            return config
            
        except json.JSONDecodeError as e:
            raise FormatterError(
                message=f"Invalid JSON in existing config file: {config_path}",
                error_code="S04-003-001",
                context={
                    "config_path": str(config_path),
                    "error": str(e)
                }
            )
    
    def merge_with_existing_config(
        self,
        new_config: Dict[str, Any],
        existing_path: Path
    ) -> Dict[str, Any]:
        """Merge new MCP config with existing configuration.
        
        Reads the existing config file (if it exists), merges the new
        mcpServers entry without overwriting existing servers, and
        returns the merged configuration.
        
        Args:
            new_config: New configuration dictionary to merge
            existing_path: Path to existing config file
            
        Returns:
            Merged configuration dictionary
            
        Raises:
            FormatterError: If existing config contains invalid JSON
        """
        existing = self.read_existing_config(existing_path)
        
        if existing is None:
            logger.debug(f"No existing config to merge, using new config only")
            return new_config
        
        # Merge mcpServers
        if "mcpServers" not in existing:
            existing["mcpServers"] = {}
        
        new_servers = new_config.get("mcpServers", {})
        existing_servers = existing.get("mcpServers", {})
        
        for server_name, server_config in new_servers.items():
            if server_name in existing_servers:
                logger.warning(
                    f"Server '{server_name}' already exists in config, "
                    "updating with new configuration"
                )
            existing_servers[server_name] = server_config
        
        existing["mcpServers"] = existing_servers
        
        logger.debug(f"Merged config with existing: {existing_path}")
        return existing
    
    def write_config(
        self,
        config: Dict[str, Any],
        config_path: Path,
        merge: bool = True
    ) -> Path:
        """Write MCP configuration to file.
        
        Args:
            config: Configuration dictionary to write
            config_path: Path to write config file
            merge: If True, merge with existing config (default: True)
            
        Returns:
            Path to the written config file
            
        Raises:
            FormatterError: If file cannot be written (permissions, etc.)
        """
        # Merge with existing if requested
        if merge:
            config = self.merge_with_existing_config(config, config_path)
        
        # Ensure parent directory exists
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise FormatterError(
                message=f"Failed to create config directory: {config_path.parent}",
                error_code="S04-003-002",
                context={
                    "config_path": str(config_path),
                    "error": str(e)
                }
            )
        
        # Write config file
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Wrote MCP config to: {config_path}")
            return config_path
            
        except OSError as e:
            raise FormatterError(
                message=f"Failed to write config file: {config_path}",
                error_code="S04-003-002",
                context={
                    "config_path": str(config_path),
                    "error": str(e)
                }
            )
    
    def write_claude_config(
        self,
        config: Dict[str, Any],
        merge: bool = True
    ) -> Path:
        """Write Claude Desktop configuration to file.
        
        Args:
            config: Configuration dictionary to write
            merge: If True, merge with existing config (default: True)
            
        Returns:
            Path to the written config file
        """
        config_path = self.get_claude_config_path()
        return self.write_config(config, config_path, merge=merge)
    
    def write_cursor_config(
        self,
        config: Dict[str, Any],
        merge: bool = True
    ) -> Path:
        """Write Cursor MCP configuration to file.
        
        Args:
            config: Configuration dictionary to write
            merge: If True, merge with existing config (default: True)
            
        Returns:
            Path to the written config file
        """
        config_path = self.get_cursor_config_path()
        return self.write_config(config, config_path, merge=merge)
    
    def format_connection_instructions(
        self,
        runtime_id: str,
        runtime_arn: str,
        region: str
    ) -> str:
        """Format user-friendly connection instructions.
        
        Generates copy-paste-ready connection instructions for the operator
        showing both manual config editing and automated config writing.
        
        Args:
            runtime_id: Runtime identifier
            runtime_arn: Full runtime ARN
            region: AWS region
            
        Returns:
            Formatted instruction string
        """
        config = self.format_claude_desktop_config(
            runtime_id=runtime_id,
            runtime_arn=runtime_arn,
            region=region
        )
        
        claude_path = self.get_claude_config_path()
        cursor_path = self.get_cursor_config_path()
        
        instructions = f"""
[b]MCP Client Connection Configuration[/b]

Your Bedrock AgentCore runtime is ready! Configure your MCP client to connect:

[b]Runtime Details:[/b]
  Runtime ID: {runtime_id}
  Runtime ARN: {runtime_arn}
  Region: {region}

[b]Manual Configuration:[/b]

1. [b]For Claude Desktop:[/b]
   Edit: [cyan]{claude_path}[/cyan]
   
   Add this to your mcpServers section:

[cyan]{json.dumps(config["mcpServers"], indent=2)}[/cyan]

2. [b]For Cursor:[/b]
   Edit: [cyan]{cursor_path}[/cyan]
   
   Add the same mcpServers configuration as above.

[b]After Configuration:[/b]

1. Restart your MCP client (Claude Desktop or Cursor)
2. The runtime will appear as an available MCP server
3. Start a new conversation to use the Zscaler MCP tools

[b]Troubleshooting:[/b]

- If the server doesn't appear, check that AWS credentials are configured
- Ensure the runtime is in READY state: [cyan]aws bedrock-agent get-agentcore-runtime --agentcore-runtime-id {runtime_id} --region {region}[/cyan]
- Check CloudWatch logs: /aws/bedrock/{runtime_id}
"""
        
        return instructions
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate MCP client configuration structure.
        
        Checks that the config has the required MCP structure:
        - Contains mcpServers key
        - Each server has command and args
        - Proper stdio transport configuration
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(config, dict):
            logger.warning("Config is not a dictionary")
            return False
        
        if "mcpServers" not in config:
            logger.warning("Config missing mcpServers key")
            return False
        
        servers = config.get("mcpServers", {})
        if not isinstance(servers, dict):
            logger.warning("mcpServers is not a dictionary")
            return False
        
        for server_name, server_config in servers.items():
            if not isinstance(server_config, dict):
                logger.warning(f"Server '{server_name}' config is not a dictionary")
                return False
            
            if "command" not in server_config:
                logger.warning(f"Server '{server_name}' missing 'command' field")
                return False
            
            if "args" not in server_config:
                logger.warning(f"Server '{server_name}' missing 'args' field")
                return False
            
            if not isinstance(server_config.get("args"), list):
                logger.warning(f"Server '{server_name}' args is not a list")
                return False
        
        logger.debug("Config validation passed")
        return True
    
    def generate_config_json(
        self,
        runtime_id: str,
        runtime_arn: str,
        region: str,
        client: str = "claude"
    ) -> str:
        """Generate MCP configuration as JSON string.
        
        Args:
            runtime_id: Runtime identifier
            runtime_arn: Full runtime ARN
            region: AWS region
            client: Client type ('claude' or 'cursor')
            
        Returns:
            JSON-formatted configuration string
        """
        if client == "cursor":
            config = self.format_cursor_config(runtime_id, runtime_arn, region)
        else:
            config = self.format_claude_desktop_config(runtime_id, runtime_arn, region)
        
        return json.dumps(config, indent=2)
    
    def get_config_summary(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summary of the configuration for logging/display.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Summary dictionary with server names and commands
        """
        servers = config.get("mcpServers", {})
        
        summary = {
            "server_count": len(servers),
            "servers": []
        }
        
        for server_name, server_config in servers.items():
            summary["servers"].append({
                "name": server_name,
                "command": server_config.get("command"),
                "has_env": "env" in server_config,
                "timeout": server_config.get("timeout")
            })
        
        return summary