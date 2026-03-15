---
id: S01
parent: M001
milestone: M001
provides:
  - AWS session validation with credential chain support
  - IAM permission validation for Bedrock/SecretsManager/STS
  - Zscaler credential validation with format checking
  - Structured error messaging with actionable fix instructions
  - CLI preflight command for validation orchestration
requires: []
affects:
  - S02
key_files:
  - src/zscaler_mcp_deploy/cli.py
  - src/zscaler_mcp_deploy/errors.py
  - src/zscaler_mcp_deploy/messages.py
  - src/zscaler_mcp_deploy/validators/aws.py
  - src/zscaler_mcp_deploy/validators/iam.py
  - src/zscaler_mcp_deploy/validators/zscaler.py
key_decisions:
  - Chose Typer with Rich for CLI framework
  - Implemented comprehensive AWS credential chain validation
  - Used practical IAM validation by attempting actual service calls
  - Structured error hierarchy with context-rich messages
patterns_established:
  - Validator pattern with clear separation of concerns
  - Mock-based unit testing for AWS service interactions
  - Rich console output with structured status tables
  - Custom exception hierarchy for structured error handling
observability_surfaces:
  - CLI preflight command outputs structured validation status
  - help-credentials command provides detailed credential guidance
  - Error messages include specific error codes and remediation steps
  - Progress indicators for long-running validation operations
  - Test suite (72 tests) covers all validators
roll_down_paths:
  - .gsd/milestones/M001/slices/S01/tasks/T01-SUMMARY.md
  - .gsd/milestones/M001/slices/S01/tasks/T02-SUMMARY.md
  - .gsd/milestones/M001/slices/S01/tasks/T03-SUMMARY.md
  - .gsd/milestones/M001/slices/S01/tasks/T04-SUMMARY.md
  - .gsd/milestones/M001/slices/S01/tasks/T05-SUMMARY.md
duration: 10.7h
verification_result: passed
completed_at: 2026-03-14T23:33:00Z
---

# S01: Preflight & Validation Engine

**Structured preflight validation engine with AWS session validation, IAM permission checking, Zscaler credential validation, and actionable error messaging.**

## What Happened

Built a comprehensive preflight validation engine that catches all known prerequisite failures before any AWS resources are created. The slice delivers:

1. **CLI Structure (T01)**: Established Typer-based CLI with version, help, and preflight commands using Rich for formatted output.

2. **AWS Session Validation (T02)**: Implemented credential chain validation covering environment variables, `~/.aws/credentials`, and profiles. Validates regions against Bedrock-supported regions (us-east-1, us-west-2, eu-west-1, etc.) with interactive region selection.

3. **IAM Permission Validation (T03)**: Implemented practical permission checking by attempting actual AWS API calls for Bedrock, Secrets Manager, and STS. Generates policy documents for missing permissions with exact fix instructions.

4. **Zscaler Credential Validation (T04)**: Created credential validator checking format (email username, 32-character hex API key), network connectivity to Zscaler cloud endpoints, and authentication with actual API calls.

5. **Error Messaging System (T05)**: Built structured error hierarchy with `ZscalerMCPError` base class and specific error types. Error messages include specific error codes, context, and remediation steps. Added `help-credentials` command for detailed credential configuration guidance.

## Verification

- All 72 unit tests pass: `poetry run pytest tests/ -v`
- CLI commands work:
  - `poetry run zscaler-mcp-deploy --version` → outputs "zscaler-mcp-deploy 0.1.0"
  - `poetry run zscaler-mcp-deploy --help` → shows available commands
  - `poetry run zscaler-mcp-deploy help-credentials` → displays AWS/Zscaler credential help
  - `poetry run zscaler-mcp-deploy preflight --help` → shows all preflight options
- Error messages include specific AWS/Zscaler error codes and actionable guidance
- No sensitive credentials are logged or displayed (verified via obfuscation tests)

## Requirements Advanced

- R001 — One-Command Interactive Deploy — CLI structure established with help and preflight commands, interactive prompts for credentials in place
- R002 — Strict Preflight Validation — Comprehensive validation engine with AWS credentials, permissions, and Zscaler credentials
- R007 — Network/Security MCP Focus — Validators designed specifically for Zscaler MCP requirements

## Requirements Validated

- R001 — Interactive CLI foundation proven with working --version, --help, and preflight commands
- R002 — Strict preflight validation proven with 72 tests covering all failure modes and actionable error messages

## New Requirements Surfaced

None

## Requirements Invalidated or Re-scoped

None

## Deviations

None

## Known Limitations

- Some Bedrock and SecretsManager permissions cannot be safely tested without creating actual resources, so they are conservatively validated. This will improve in S02 when actual resource creation begins.
- Credential obfuscation in logs works but is basic; could be enhanced with full redaction for production hardening

## Follow-ups

- S02 will consume the preflight results to create actual AWS resources (Secrets Manager, IAM roles)
- Need to update error messaging based on real-world user feedback after first deployment attempts

## Files Created/Modified

- `src/zscaler_mcp_deploy/cli.py` — Main CLI with preflight and help-credentials commands
- `src/zscaler_mcp_deploy/errors.py` — Structured error hierarchy and exception types
- `src/zscaler_mcp_deploy/messages.py` — Error message catalog and user guidance
- `src/zscaler_mcp_deploy/validators/aws.py` — AWS session and region validation
- `src/zscaler_mcp_deploy/validators/iam.py` — IAM permission validation
- `src/zscaler_mcp_deploy/validators/zscaler.py` — Zscaler credential validation
- `tests/test_preflight.py` — CLI integration tests
- `tests/test_aws_validation.py` — AWS validation tests (16 tests)
- `tests/test_iam.py` — IAM validation tests (13 tests)
- `tests/test_zscaler.py` — Zscaler validation tests (18 tests)
- `tests/test_errors.py` — Error messaging tests (18 tests)

## Forward Intelligence

### What the next slice should know
- The preflight command can be run independently and produces a structured validation result. S02 should leverage this to fail fast before creating any AWS resources.
- AWS region validation is already done — S02 can trust the validated region parameter
- IAM permission validation provides detailed missing permissions — S02 can reference this when creating IAM roles
- Zscaler credentials are validated for format and connectivity — S02 should store these in Secrets Manager

### What's fragile
- IAM permission validation attempts actual AWS service calls. If AWS changes API behaviors or adds new required permissions, the validation may need updates.
- Zscaler API endpoints may change; cloud endpoint list in `zscaler.py` needs periodic review

### Authoritative diagnostics
- Run `poetry run pytest tests/ -v` — all 72 tests passing is the primary validation signal
- Run `poetry run zscaler-mcp-deploy preflight --help` — shows all CLI options available
- Logs from validators include specific error codes (e.g., "AWS-001", "Z-002") for debugging

### What assumptions changed
- Original assumption: IAM simulation would be complex — Actual: Practical validation by attempting service calls is simpler and more accurate than IAM policy simulation
- Original assumption: Zscaler validation would require special handling — Actual: Standard HTTP requests with proper authentication work fine
