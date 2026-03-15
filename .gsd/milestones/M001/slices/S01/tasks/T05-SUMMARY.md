---
id: T05
parent: S01
milestone: M001
provides:
  - Comprehensive error messaging system with structured error handling
  - Predefined error messages with actionable remediation guidance
  - User guidance system with detailed credential configuration help
  - Enhanced error reporting in all validator modules
key_files:
  - src/zscaler_mcp_deploy/errors.py
  - src/zscaler_mcp_deploy/messages.py
  - src/zscaler_mcp_deploy/validators/aws.py
  - src/zscaler_mcp_deploy/validators/iam.py
  - src/zscaler_mcp_deploy/validators/zscaler.py
  - src/zscaler_mcp_deploy/cli.py
  - tests/test_errors.py
key_decisions:
  - Created structured error hierarchy with specific error types for different validation categories
  - Implemented context-rich error messages that include remediation steps and fix commands
  - Added user guidance system with detailed help for credential configuration
  - Enhanced all validator modules to use the new error messaging system
patterns_established:
  - Structured error handling with custom exception types
  - Context-rich error reporting with remediation guidance
  - Predefined error message catalog for consistent error messaging
  - User guidance system integrated into CLI
observability_surfaces:
  - Structured error messages with context and remediation
  - CLI help commands for detailed credential configuration guidance
  - Enhanced error reporting in validation summaries
duration: 2h
verification_result: passed
completed_at: 2026-03-14T21:42:00Z
blocker_discovered: false
---

# T05: Create error messaging system

**Implemented comprehensive error messaging system with structured error handling and user guidance**

## What Happened

Created a complete error messaging system for the Zscaler MCP Deployer that provides:
1. **Structured Error Handling**: Implemented a hierarchy of custom exception types (`ZscalerMCPError`, `AWSCredentialsError`, `AWSRegionError`, `AWSPermissionsError`, `ZscalerCredentialsError`, `ZscalerConnectivityError`, `ZscalerAuthenticationError`) with specific categories and severity levels.

2. **Error Message Catalog**: Created `ErrorMessage` data class and `ErrorMessageCatalog` with predefined error messages for common failure scenarios, each including detailed descriptions, remediation steps, and fix commands.

3. **User Guidance System**: Implemented `UserGuidance` class with comprehensive help text for AWS and Zscaler credential configuration, plus troubleshooting guidance for common issues.

4. **Enhanced Validator Modules**: Updated all validator modules (AWS, IAM, Zscaler) to use the new error messaging system, providing context-rich error messages with specific error codes and actionable remediation guidance.

5. **CLI Integration**: Added new `help-credentials` command to the CLI that provides detailed guidance for configuring AWS and Zscaler credentials, plus enhanced error reporting in the preflight validation.

6. **Comprehensive Testing**: Created extensive test suite covering all error types, message formatting, and user guidance functionality.

## Verification

- All existing tests continue to pass (72/72 tests passing)
- New error messaging system tests pass (18/18 tests passing)
- CLI commands work correctly:
  - `poetry run zscaler-mcp-deploy --help` shows new help-credentials command
  - `poetry run zscaler-mcp-deploy help-credentials` displays detailed guidance
  - `poetry run zscaler-mcp-deploy preflight --help` shows all options
- Error handling enhanced in all validator modules with structured error messages
- No breaking changes to existing functionality

## Diagnostics

- Error messages now include specific error codes, context information, and remediation guidance
- CLI provides detailed help through `help-credentials` command
- Structured error reporting with consistent formatting across all validators
- Enhanced observability through context-rich error messages that aid debugging

## Deviations

None - implementation followed the planned approach of creating error messaging system files and integrating them into existing validator modules.

## Known Issues

None - all functionality working as designed.

## Files Created/Modified

- `src/zscaler_mcp_deploy/errors.py` — Core error handling system with custom exception types and structured error messages
- `src/zscaler_mcp_deploy/messages.py` — Predefined error message catalog and user guidance system
- `src/zscaler_mcp_deploy/validators/aws.py` — Enhanced AWS validator with structured error handling
- `src/zscaler_mcp_deploy/validators/iam.py` — Enhanced IAM validator with structured error handling
- `src/zscaler_mcp_deploy/validators/zscaler.py` — Enhanced Zscaler validator with structured error handling
- `src/zscaler_mcp_deploy/cli.py` — Added help-credentials command and enhanced error reporting
- `tests/test_errors.py` — Comprehensive test suite for error messaging system