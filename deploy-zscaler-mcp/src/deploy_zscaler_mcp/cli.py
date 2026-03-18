"""CLI interface for Zscaler MCP Deployer."""

import argparse
import sys
from pathlib import Path
from typing import Optional

from deploy_zscaler_mcp import __version__

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Zscaler MCP Deployer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"deploy-zscaler-mcp {__version__}",
        help="Show version and exit",
    )

    parser.add_argument(
        "--env-file",
        type=Path,
        default=".env",
        help="Path to .env file (default: .env)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Preflight command
    preflight_parser = subparsers.add_parser("preflight", help="Run preflight validation")
    preflight_parser.add_argument("--region", help="AWS region")

    # Deploy command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy MCP server")
    deploy_parser.add_argument("--runtime-name", default="zscaler-mcp-runtime", help="Runtime name")
    deploy_parser.add_argument("--region", default="us-east-1", help="AWS region")
    deploy_parser.add_argument("--enable-write-tools", action="store_true", help="Enable write tools")

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Run MCP server")
    serve_parser.add_argument("--transport", choices=["stdio", "http"], default="stdio", help="Transport protocol")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Host for HTTP transport")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port for HTTP transport")

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify deployment")
    verify_parser.add_argument("--runtime-name", required=True, help="Runtime name to verify")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    # Import here to avoid slow imports when just showing help
    from deploy_zscaler_mcp.commands import handle_command
    handle_command(args)

if __name__ == "__main__":
    main()