# S04: Verification & Connection Output - User Acceptance Test

## Test Objective

Verify that the CLI completes the deployment pipeline by verifying runtime health via CloudWatch logs and outputting copy-paste-ready MCP client connection instructions.

## Prerequisites

- AWS CLI configured with appropriate permissions
- Valid Zscaler credentials (username, password, API key)
- Python 3.9+ with Poetry installed
- All 372 tests passing (`poetry run pytest tests/ --tb=short`)

## Test Cases

### TC01: Successful Deployment with Healthy Verification

**Setup:**
```bash
# Clean state - no existing resources with these names
poetry run zscaler-mcp-deploy deploy \
  --runtime-name uat-test-runtime \
  --secret-name uat-test-secret \
  --role-name uat-test-role \
  --username test@example.com \
  --password testpass123 \
  --api-key a1b2c3d4e5f678901234567890abcdef \
  --non-interactive
```

**Expected Results:**
- ✅ Exit code 0 (deployment successful and verified)
- ✅ Rich panel showing "Runtime Verification: HEALTHY" in green
- ✅ CloudWatch log evidence showing matched health patterns
- ✅ Connection instructions with runtime ID/ARN
- ✅ Copy-paste ready MCP config JSON for Claude Desktop
- ✅ Copy-paste ready MCP config JSON for Cursor
- ✅ Platform-appropriate config file paths displayed

### TC02: Deployment with Unhealthy Verification

**Setup:**
```bash
# Simulate log delay or credential issues by setting short timeout
poetry run zscaler-mcp-deploy deploy \
  --runtime-name uat-test-runtime2 \
  --secret-name uat-test-secret2 \
  --role-name uat-test-role2 \
  --username test@example.com \
  --password testpass123 \
  --api-key a1b2c3d4e5f678901234567890abcdef \
  --verification-timeout 1 \
  --non-interactive
```

**Expected Results:**
- ✅ Exit code 1 (deployment successful but verification failed/unhealthy)
- ✅ Rich panel showing "Runtime Verification: UNHEALTHY" or "PENDING" in yellow
- ✅ Error message indicating timeout or insufficient health patterns
- ✅ Connection instructions still shown for manual troubleshooting
- ✅ Runtime ID/ARN and config JSON still provided

### TC03: Deployment with Verification Skipped

**Setup:**
```bash
poetry run zscaler-mcp-deploy deploy \
  --runtime-name uat-test-runtime3 \
  --secret-name uat-test-secret3 \
  --role-name uat-test-role3 \
  --username test@example.com \
  --password testpass123 \
  --api-key a1b2c3d4e5f678901234567890abcdef \
  --skip-verification \
  --non-interactive
```

**Expected Results:**
- ✅ Exit code 0 (deployment successful with verification skipped)
- ✅ Rich panel showing "Runtime Verification: SKIPPED" in blue
- ✅ Connection instructions with runtime ID/ARN
- ✅ Copy-paste ready MCP config JSON provided
- ✅ No CloudWatch log polling attempted

### TC04: Verification CLI Help

**Setup:**
```bash
poetry run zscaler-mcp-deploy deploy --help
```

**Expected Results:**
- ✅ `--skip-verification` flag documented
- ✅ `--verification-timeout` option documented with default value (120)
- ✅ Help text explains verification purpose and exit codes

## Verification Commands

After successful deployment, verify the runtime exists:
```bash
aws bedrock list-agent-core-runtimes --region us-east-1 | grep uat-test-runtime
```

Check CloudWatch log group was created:
```bash
aws logs describe-log-groups --log-group-name-prefix /aws/bedrock/uat-test-runtime --region us-east-1
```

## Cleanup

Remove test resources:
```bash
# Delete runtimes (secrets and roles kept for troubleshooting per D024)
aws bedrock delete-agent-core-runtime --agent-core-runtime-id <runtime-id> --region us-east-1
```

## Success Criteria

All test cases pass with:
- ✅ Correct exit codes (0, 1, 2) for different scenarios
- ✅ Color-coded Rich panels with appropriate status messages
- ✅ Valid CloudWatch log evidence when verification runs
- ✅ Copy-paste ready MCP client configurations
- ✅ Cross-platform config paths (tested on target platform)
- ✅ Proper error handling and user guidance
- ✅ No regressions in existing functionality

## Expected Behavior Matrix

| Scenario | Exit Code | Verification Panel | Connection Output | Resource State |
|----------|-----------|-------------------|-------------------|----------------|
| Healthy verification | 0 | Green HEALTHY | Yes, full | Runtime + secret + role |
| Unhealthy verification | 1 | Yellow UNHEALTHY/PENDING | Yes, with warning | Runtime + secret + role |
| Verification skipped | 0 | Blue SKIPPED | Yes, full | Runtime + secret + role |
| Deployment error | 2 | Red ERROR | No (or partial) | Partial bootstrap |

## Diagnostic Checks

For troubleshooting failed verifications:
- Check CloudWatch log group exists: `/aws/bedrock/{runtime-id}`
- Check log streams appear within 30-60s of container start
- Look for health pattern matches: "credential", "retrieved", "MCP server", "started", "listening"
- Verify IAM role has CloudWatch Logs read permissions
- Check AWS region support for CloudWatch Logs filtering

This UAT proves the slice delivers on its promise: operators receive verified runtime health status and copy-paste-ready connection instructions for Claude Desktop and Cursor MCP clients.