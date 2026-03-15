---
estimated_steps: 5
estimated_files: 1
---

# T04: CLI Integration

**Slice:** S02 — Secrets Manager & IAM Bootstrap
**Milestone:** M001

## Description

Add the `bootstrap` command to the CLI that wires the bootstrap orchestrator into the user-facing interface. Uses Rich for formatted output table showing resource status.

## Steps

1. Extend `src/zscaler_mcp_deploy/cli.py` with `bootstrap` command
2. Add options: `--secret-name`, `--role-name`, `--kms-key-id`, `--use-existing`, `--region`, `--profile`
3. Create BootstrapConfig from CLI options and prompt for missing required values
4. Call BootstrapOrchestrator.bootstrap_resources() and display results in Rich table
5. Handle errors using S01 error patterns with specific fix commands

## Must-Haves

- [ ] `bootstrap` command with all required options
- [ ] Rich table output showing secret ARN, role ARN, and status (created/reused)
- [ ] Integration with existing `--profile` and `--region` patterns from preflight
- [ ] Error handling with S01 error message patterns
- [ ] Non-zero exit code on bootstrap failure

## Verification

- `poetry run zscaler-mcp-deploy bootstrap --help` shows all options
- `poetry run pytest tests/test_preflight.py -v` passes (no regression)
- CLI help text is accurate and complete

## Observability Impact

- Signals added/changed: CLI output table with resource status
- How a future agent inspects this: Run CLI command and inspect exit code and table output
- Failure state exposed: Error messages with specific error codes and fix commands

## Inputs

- `src/zscaler_mcp_deploy/bootstrap.py` — BootstrapOrchestrator from T03
- `src/zscaler_mcp_deploy/models.py` — BootstrapConfig from T03
- `src/zscaler_mcp_deploy/cli.py` — Existing CLI structure from S01
- `src/zscaler_mcp_deploy/errors.py` — Error handling patterns

## Expected Output

- `src/zscaler_mcp_deploy/cli.py` — Extended with bootstrap command
