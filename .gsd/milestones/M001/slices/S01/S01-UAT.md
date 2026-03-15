# S01: Preflight & Validation Engine — UAT

**Milestone:** M001
**Written:** 2026-03-14

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: The slice delivers validation logic and CLI commands with no runtime infrastructure. Verification is via tests and manual CLI execution.

## Preconditions

- Python 3.14+ installed
- Poetry installed and configured
- AWS CLI installed (optional — for testing actual AWS validation)

## Smoke Test

```bash
cd /Users/djbeatbug/RoadToMillion/zscaler-mcp-deployer
poetry run pytest tests/ -v
# Expected: All 72 tests pass
```

## Test Cases

### 1. CLI Version Command

1. Run: `poetry run zscaler-mcp-deploy --version`
2. **Expected:** Outputs "zscaler-mcp-deploy 0.1.0"

### 2. CLI Help Command

1. Run: `poetry run zscaler-mcp-deploy --help`
2. **Expected:** Shows two commands: `preflight` and `help-credentials`

### 3. Preflight Command Without AWS Credentials

1. Ensure no AWS credentials are configured (or use --profile with a non-existent profile)
2. Run: `poetry run zscaler-mcp-deploy preflight --profile nonexistent`
3. **Expected:** Fails with structured error message including error code (e.g., "AWS-001"), description, and remediation steps

### 4. Preflight Command With Skip Flags

1. Run: `poetry run zscaler-mcp-deploy preflight --skip-iam --skip-zscaler`
2. **Expected:** Completes AWS session validation only, showing status table

### 5. Help-Credentials Command

1. Run: `poetry run zscaler-mcp-deploy help-credentials`
2. **Expected:** Shows detailed help for AWS and Zscaler credential configuration with examples

### 6. Zscaler Credential Format Validation

1. Run: `poetry run zscaler-mcp-deploy preflight --zscaler-username invalid --zscaler-password test --zscaler-api-key invalid --skip-iam`
2. **Expected:** Fails with specific error indicating invalid username format and API key format requirements

## Edge Cases

### IAM Validation With No Bedrock Permissions

1. Configure AWS credentials for a user without Bedrock permissions
2. Run: `poetry run zscaler-mcp-deploy preflight`
3. **Expected:** Validation shows missing Bedrock permissions with suggested policy document

### Region Validation

1. Run: `poetry run zscaler-mcp-deploy preflight --region us-west-1 --skip-iam --skip-zscaler`
2. **Expected:** Fails with error indicating region does not support Amazon Bedrock

### Zscaler Invalid API Key Format

1. Run: `poetry run zscaler-mcp-deploy preflight --zscaler-username test@example.com --zscaler-password test --zscaler-api-key not32chars --skip-iam`
2. **Expected:** Fails with "Invalid API key format" error (must be 32 hex characters)

## Failure Signals

- Any test in the test suite fails
- CLI commands do not produce expected output
- Error messages do not include specific error codes or remediation steps
- Help text is missing or incomplete

## Requirements Proved By This UAT

- R001 — CLI version and help commands work; preflight command structure established
- R002 — Strict preflight validation works with comprehensive error messages
- R007 — Domain focus (network/security MCP) established via Zscaler-specific validators

## Not Proven By This UAT

- Actual AWS resource creation (S02)
- Secrets Manager integration (S02)
- Bedrock runtime deployment (S03)
- Runtime verification against live logs (S04)

## Notes for Tester

- The preflight command is designed to fail fast with clear errors. If AWS credentials are not configured, it will show specific guidance on how to configure them.
- The `--skip-iam` and `--skip-zscaler` flags allow testing partial validation.
- All error messages should include specific error codes (e.g., "AWS-001") and actionable remediation steps.
