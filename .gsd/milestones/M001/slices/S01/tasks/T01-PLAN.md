# T01-PLAN

**Task:** Initialize CLI structure with Typer

## Steps

1. Scaffold Python package structure
   - Create src/zscaler_mcp_deploy directory
   - Create __init__.py files
   - Set up basic project structure

2. Install Typer, rich, boto3 dependencies
   - Add dependencies to pyproject.toml
   - Run poetry install

3. Create base CLI command
   - Implement main CLI entry point in cli.py
   - Set up Typer app instance

4. Add --version and help scaffolding
   - Implement version command
   - Ensure help functionality works

**Must-Haves:**
- `src/zscaler_mcp_deploy/cli.py` exists
- `zscaler-mcp-deploy --help` shows basic commands

**Verification:**
- Run `poetry run zscaler-mcp-deploy --version` outputs 0.1.0

**Files:**
- pyproject.toml
- src/zscaler_mcp_deploy/__init__.py
- src/zscaler_mcp_deploy/cli.py