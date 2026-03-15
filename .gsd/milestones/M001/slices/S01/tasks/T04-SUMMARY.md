---
id: T04
parent: S01
milestone: M001
provides:
  - Zscaler credential validation with format checking and connectivity tests
  - CLI integration for Zscaler validation with --zscaler-* options
  - Comprehensive test suite for Zscaler validation logic
key_files:
  - src/zscaler_mcp_deploy/validators/zscaler.py
  - tests/test_zscaler.py
  - src/zscaler_mcp_deploy/cli.py
key_decisions:
  - Use requests library for HTTP connectivity testing instead of urllib
  - Implement credential obfuscation for secure logging
  - Focus on practical validation approach with actual API calls rather than simulation
patterns_established:
  - Validator pattern with clear separation of concerns
  - Mock-based unit testing for external service interactions
  - Consistent error messaging with actionable guidance
observability_surfaces:
  - CLI commands output structured status information in table format
  - Error messages include specific Zscaler error codes and actionable guidance
  - Validation failures are logged with context (credential type, connectivity issues)
  - Progress indicators show "Checking Zscaler credentials..." during validation
  - No sensitive credentials are logged or displayed in error messages
duration: 4.2h
verification_result: passed
completed_at: 2026-03-14T21:41:19Z
# Set blocker_discovered: true only if execution revealed the remaining slice plan
# is fundamentally invalid (wrong API, missing capability, architectural mismatch).
# Do NOT set true for ordinary bugs, minor deviations, or fixable issues.
blocker_discovered: false
---

# T04: Build Zscaler credential validator

**Added Zscaler credential validation with format checking, connectivity tests, and CLI integration**

## What Happened

Implemented a comprehensive Zscaler credential validator that performs format validation, connectivity testing, and authentication validation. The validator checks:
- Credential format (email username, 32-character hex API key)
- Network connectivity to Zscaler cloud endpoints
- Authentication with Zscaler API using provided credentials

Integrated the validator into the CLI preflight command with new options:
- `--zscaler-cloud` to specify the Zscaler cloud environment
- `--zscaler-username`, `--zscaler-password`, `--zscaler-api-key` for credentials
- `--skip-zscaler` to bypass Zscaler validation

Created a complete test suite with 18 test cases covering all validation scenarios, including edge cases and error conditions. All tests pass and follow the existing testing patterns established in the project.

## Verification

- `poetry run pytest tests/test_zscaler.py -v` - All 18 tests pass
- `poetry run pytest tests/ -v` - All 55 tests pass (including existing AWS/IAM tests)
- CLI help shows new Zscaler options: `poetry run zscaler-mcp-deploy preflight --help`
- Manual testing with invalid credentials shows proper error messages
- Credential obfuscation works correctly in logs and error messages

## Diagnostics

- CLI commands output structured status information in table format
- Error messages include specific validation failures with actionable guidance
- Validation failures are logged with context (credential type issues, connectivity problems)
- Progress indicators show "Checking Zscaler credentials..." during validation
- No sensitive credentials are logged or displayed in error messages (obfuscation working)
- Test suite covers all major failure modes for debugging future issues

## Deviations

None

## Known Issues

None

## Files Created/Modified

- `src/zscaler_mcp_deploy/validators/zscaler.py` — New Zscaler credential validator implementation with format validation, connectivity testing, and authentication
- `tests/test_zscaler.py` — Comprehensive test suite with 18 test cases for Zscaler validation
- `src/zscaler_mcp_deploy/cli.py` — Updated CLI to integrate Zscaler validation into preflight command
- `tests/test_preflight.py` — Updated preflight tests to include Zscaler validation options
- `pyproject.toml` — Added requests dependency for HTTP connectivity testing