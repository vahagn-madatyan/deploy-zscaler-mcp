# S03: Bedrock Runtime Deployment — UAT

**Milestone:** M001
**Written:** 2026-03-14

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: S03 delivers code artifacts (BedrockRuntime class, DeployOrchestrator, CLI command) with comprehensive unit and integration tests. No live AWS deployment required for slice verification — mocked AWS APIs prove integration. Live deployment verification is S04's scope.

## Preconditions

- Python 3.11+ with poetry installed
- AWS CLI configured (or mock environment for testing)
- Zscaler credentials available (or mock for testing)
- Dependencies installed: `poetry install`

## Smoke Test

```bash
# Verify CLI shows deploy command with all options
poetry run zscaler-mcp-deploy deploy --help

# Expected: Help output shows --runtime-name, --image-uri, --enable-write-tools, --poll-timeout flags
```

## Test Cases

### 1. Deploy Help Shows All Options

1. Run: `poetry run zscaler-mcp-deploy deploy --help`
2. **Expected:** Help displays all options including:
   - --runtime-name, --secret-name, --role-name
   - --image-uri, --enable-write-tools
   - --poll-timeout (default: 600)
   - All bootstrap options from S02

### 2. Unit Tests Pass

1. Run: `poetry run pytest tests/test_bedrock_runtime.py -v --tb=short`
2. **Expected:** 52 tests pass, no failures

### 3. Deploy Orchestrator Tests Pass

1. Run: `poetry run pytest tests/test_deploy.py -v --tb=short`
2. **Expected:** 19 tests pass, covering success, failure, and rollback scenarios

### 4. Integration Tests Pass

1. Run: `poetry run pytest tests/test_deploy_integration.py -v --tb=short`
2. **Expected:** 22 tests pass, covering end-to-end flows with mocked AWS services

### 5. Full Test Suite Passes

1. Run: `poetry run pytest tests/ --tb=short`
2. **Expected:** 282 tests pass (S01: 72, S02: 117, S03: 93), no regressions

## Edge Cases

### Polling Timeout Handling

1. Simulate: Deploy with very short --poll-timeout (e.g., 1 second)
2. **Expected:** Deploy fails with S03-003-PollingTimeout error, runtime is rolled back (deleted)

### Runtime CREATE_FAILED Handling

1. Simulate: AWS returns CREATE_FAILED status with error reason
2. **Expected:** Deploy fails with S03-003-RuntimeFailed error, error reason extracted and displayed, runtime rolled back

### Bootstrap Resource Reuse

1. Simulate: Deploy when secret and role already exist from previous run
2. **Expected:** Deploy succeeds, uses existing secret/role, creates new runtime, shows "Reused" status for bootstrap resources

## Failure Signals

- Tests fail with import errors → Missing __init__.py exports
- Tests fail with AttributeError → BedrockRuntime methods not implemented
- CLI --help missing flags → CLI command not properly registered
- Integration tests fail → Cross-component wiring issue

## Requirements Proved By This UAT

- R004 — Runtime Deployment Execution — Proved via 93 tests covering runtime creation, polling, orchestration, and CLI integration

## Not Proven By This UAT

- Actual AWS Bedrock runtime creation (requires real AWS account)
- CloudWatch log verification (R005 — deferred to S04)
- MCP client connection instructions (R06 — deferred to S04)
- Real runtime health checks (requires live deployment)

## Notes for Tester

- All tests use mocked boto3 responses — no AWS charges incurred
- DEFAULT_IMAGE_URI is a placeholder — real deployments will need actual Zscaler ECR image
- Rollback verification in tests uses mock assertions to confirm delete_runtime was called
- Test output shows poll counts and elapsed times for timeout scenarios
