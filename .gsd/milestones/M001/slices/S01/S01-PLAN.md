# S01-PLAN

**Goal:** Strict CLI preflight validation engine that checks AWS configuration/permissions and Zscaler credentials
**Demo:** Running `zscaler-mcp-deploy preflight` shows validation status and stops on errors with fix instructions

## Must-Haves

- AWS session validation (credentials, region availability)
- IAM permission simulation for required Bedrock/SecretsManager actions
- Zscaler credential format validation
- Actionable error messages with AWS CLI fix commands

## Verification

- `pytest tests/test_preflight.py -v`
- Manual test with invalid credentials shows proper error
- AWS permission failure shows exact IAM policy snippet

## Observability / Diagnostics

- CLI commands output structured status information
- Error messages include specific AWS/Zscaler error codes
- Validation failures are logged with context for debugging
- Progress indicators for long-running validation operations
- No sensitive credentials are logged or displayed in error messages

## Tasks

- [x] **T01: Initialize CLI structure with Typer** `est:45m`
  - Why: Set up the base CLI structure using Typer for building the command-line interface
  - Files: pyproject.toml, src/zscaler_mcp_deploy/__init__.py, src/zscaler_mcp_deploy/cli.py
  - Do: Scaffold Python package, install dependencies, create base CLI with version/help
  - Verify: `poetry run zscaler-mcp-deploy --version` outputs 0.1.0 and `--help` works

- [x] **T02: Implement AWS session validation** `est:1h`
  - Why: Validate that AWS credentials are properly configured and can establish a session
  - Files: src/zscaler_mcp_deploy/aws.py, tests/test_aws.py
  - Do: Create AWS session validation function, handle credential errors
  - Verify: Function correctly identifies valid/invalid credentials and region settings

- [x] **T03: Add IAM permission simulator** `est:2h`
  - Why: Check if user has required permissions for Bedrock and SecretsManager operations
  - Files: src/zscaler_mcp_deploy/iam.py, tests/test_iam.py
  - Do: Implement IAM permission simulation, create policy check functions
  - Verify: Permission checks correctly identify missing actions and suggest policy fixes

- [x] **T04: Build Zscaler credential validator** `est:1.5h`
  - Why: Validate Zscaler API credentials format and basic connectivity
  - Files: src/zscaler_mcp_deploy/zscaler.py, tests/test_zscaler.py
  - Do: Create credential validation logic, implement connectivity tests
  - Verify: Validator correctly identifies valid/invalid credential formats and connection issues

- [x] **T05: Create error messaging system** `est:1h`
  - Why: Provide actionable error messages with specific fix instructions
  - Files: src/zscaler_mcp_deploy/errors.py, src/zscaler_mcp_deploy/messages.py
  - Do: Implement error formatting, create helpful error messages with fix commands
  - Verify: Error messages include specific remediation steps and example commands