"""MCP server implementation for Zscaler MCP Deployer."""

import argparse
import logging
import sys
from typing import Any

from fastmcp import FastMCP

from deploy_zscaler_mcp.config import Config, ConfigLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# Server name and version
SERVER_NAME = "deploy-zscaler-mcp"
SERVER_VERSION = "0.1.0"

# Create FastMCP instance
mcp = FastMCP(SERVER_NAME)

def register_tools(enable_write: bool = False) -> None:
    """Register MCP tools with the server.

    Args:
        enable_write: If True, register write tools.
    """
    # TODO: Implement actual tool registration
    # Register read tools
    # Register write tools if enabled
    
    logger.info(f"Tool registration complete: write tools enabled = {enable_write}")

def main(transport: str = "stdio", host: str = "0.0.0.0", port: int = 8000, enable_write: bool = False) -> None:
    """Main entry point for the MCP server.

    Args:
        transport: Transport protocol ("stdio" or "http").
        host: Host for HTTP transport.
        port: Port for HTTP transport.
        enable_write: Whether to enable write tools.
    """
    logger.info(f"Starting {SERVER_NAME} v{SERVER_VERSION}")
    logger.info(f"Transport: {transport}")
    
    if transport == "http":
        logger.info(f"HTTP server will bind to {host}:{port}")

    # Load configuration
    try:
        config_loader = ConfigLoader()
        config = config_loader.load_config()
        logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Register tools
    register_tools(enable_write=enable_write)

    # Run the server with the appropriate transport
    if transport == "stdio":
        # Stdio transport (default for Claude Desktop)
        mcp.run(transport="stdio")
    elif transport == "http":
        # Streamable HTTP transport
        mcp.run(transport="streamable-http", host=host, port=port)
    else:
        logger.error(f"Unknown transport: {transport}")
        sys.exit(1)

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Zscaler MCP Server")
    parser.add_argument("--transport", choices=["stdio", "http"], default="stdio", help="Transport protocol")
    parser.add_argument("--host", default="0.0.0.0", help="Host for HTTP transport")
    parser.add_argument("--port", type=int, default=8000, help="Port for HTTP transport")
    parser.add_argument("--enable-write-tools", action="store_true", help="Enable write tools")
    
    args = parser.parse_args()
    
    main(
        transport=args.transport,
        host=args.host,
        port=args.port,
        enable_write=args.enable_write_tools
    )