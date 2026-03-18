"""Entry point for running the server as a module or console script.

Usage:
    python -m deploy_zscaler_mcp [options]
    deploy-zscaler-mcp [options]
"""

from deploy_zscaler_mcp.cli import main

if __name__ == "__main__":
    main()