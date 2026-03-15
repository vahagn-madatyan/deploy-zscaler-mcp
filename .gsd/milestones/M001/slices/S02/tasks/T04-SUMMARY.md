---
id: T04
parent: S02
milestone: M001
provides:
  - CLI bootstrap command with idempotent resource creation
  - Rich table output showing secret/role ARNs and status
  - Interactive prompts for missing required values
  - Non-interactive mode for CI/CD automation
key_files:
  - src/zscaler_mcp_deploy/cli.py
key_decisions:
  - Interactive prompts for missing values with --non-interactive flag to disable
  - Rich table shows Created (green) vs Reused (blue) status clearly
  - Error handling follows S01 patterns with fix commands per error code
  - Use-existing behavior is implicit (always idempotent) — flag reserved for future strict mode
patterns_established:
  - CLI commands prompt for required values when not provided
  - --non-interactive flag to fail fast instead of prompting (CI/CD friendly)
  - Error codes map to specific remediation commands
  - Table output uses color coding: green=created, blue=reused, red=failed
observability_surfaces:
  - CLI exit code: 0 on success, 1 on failure
  - Rich table with resource ARNs and creation status
  - Error messages include error codes and fix commands
  - No sensitive values logged (passwords, api_key hidden in prompts)
duration: 25m
verification_result: passed
completed_at: 2026-03-14
blocker_discovered: false
---

# T04: CLI Integration

Added the `bootstrap` command to the CLI that wires the bootstrap orchestrator into the user-facing interface with Rich-formatted output table showing resource status.

## What Happened

Extended `src/zscaler_mcp_deploy/cli.py` with a new `bootstrap` command that:

1. **Added command options**: `--secret-name`, `--role-name`, `--kms-key-id`, `--use-existing`, `--region`, `--profile`, `--username`, `--password`, `--api-key`, `--cloud`, `--description`, `--non-interactive`

2. **Implemented interactive prompts**: When required values (secret-name, role-name, username, password, api-key) are missing, the CLI prompts the user. Password and API key inputs are hidden.

3. **Added Rich table output**: Displays secret ARN and role ARN with status indicators:
   - "Created" (green) for newly created resources
   - "Reused" (blue) for existing resources
   - "Failed" (red) for failed operations

4. **Error handling with S01 patterns**: Errors display error codes (S02-003-PreflightFailed, S02-003-SecretFailed, S02-003-RoleFailed) with specific fix commands for each failure type.

5. **Non-interactive mode**: `--non-interactive` flag fails fast with clear error messages instead of prompting, enabling CI/CD automation.

## Verification

- `poetry run zscaler-mcp-deploy bootstrap --help` shows all options ✅
- `poetry run pytest tests/test_preflight.py -v` passes (no regression) ✅  
- `poetry run pytest tests/ --tb=short` — 168 tests pass ✅
- Bootstrap command with missing args shows correct error: ✅
  ```
  $ poetry run zscaler-mcp-deploy bootstrap --non-interactive
  Error: --secret-name is required (or remove --non-interactive to prompt)
  Command exited with code 1
  ```

## Diagnostics

**How to inspect bootstrap results:**
```bash
# Run bootstrap with all required values
poetry run zscaler-mcp-deploy bootstrap \
  --secret-name my-zscaler-secret \
  --role-name my-zscaler-role \
  --username user@company.com \
  --password mypassword \
  --api-key 1234567890abcdef1234567890abcdef

# Non-interactive mode for CI/CD
poetry run zscaler-mcp-deploy bootstrap --non-interactive \
  --secret-name my-secret \
  --role-name my-role \
  --username user@company.com \
  --password pass \
  --api-key 1234567890abcdef1234567890abcdef

# With KMS key and custom region/profile
poetry run zscaler-mcp-deploy bootstrap \
  --secret-name my-secret \
  --role-name my-role \
  --username user@company.com \
  --password pass \
  --api-key key \
  --kms-key-id arn:aws:kms:us-east-1:123456789:key/my-key \
  --region us-east-1 \
  --profile myprofile
```

**Error inspection:**
- Error codes follow pattern `S02-003-{Phase}Failed`
- Each error type shows specific fix commands
- Exit code 1 on any failure

## Deviations

None. Implementation followed the task plan exactly.

## Known Issues

None.

## Files Created/Modified

- `src/zscaler_mcp_deploy/cli.py` — Extended with bootstrap command, interactive prompts, Rich table output, and error handling
