# S02: Secrets Manager & IAM Bootstrap — UAT

**Milestone:** M001
**Written:** 2026-03-14

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: S02 delivers library modules and CLI command with comprehensive mocked testing. No live AWS resources required — all functionality verified via 117 unit/integration tests with mocked boto3. Runtime verification will happen in S03 with live AWS testing.

## Preconditions

- Python 3.12+ with Poetry
- AWS CLI configured (credentials not used in mocked tests)
- Project installed: `poetry install`

## Smoke Test

```bash
poetry run zscaler-mcp-deploy bootstrap --help
```

**Expected:** Help text displays with all options including `--secret-name`, `--role-name`, `--kms-key-id`, `--non-interactive`

## Test Cases

### 1. Bootstrap Command Help

1. Run: `poetry run zscaler-mcp-deploy bootstrap --help`
2. **Expected:** Rich-formatted help shows description, all options, defaults

### 2. Non-Interactive Mode Fails Fast

1. Run: `poetry run zscaler-mcp-deploy bootstrap --non-interactive`
2. **Expected:** Error message indicates missing required values, exit code 1

### 3. Test Suite Passes

1. Run: `poetry run pytest tests/test_secrets_manager.py tests/test_iam_bootstrap.py tests/test_bootstrap.py tests/test_bootstrap_integration.py -v`
2. **Expected:** 117 tests pass with no failures

### 4. Full Test Suite (No Regressions)

1. Run: `poetry run pytest tests/ --tb=short`
2. **Expected:** 189 tests pass (72 from S01 + 117 from S02)

### 5. SecretResult Dataclass

1. Run Python:
   ```python
   from zscaler_mcp_deploy.models import SecretResult
   r = SecretResult(arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test", name="test", created=True)
   print(r.to_dict())
   ```
2. **Expected:** Dict with arn, name, version_id, created fields

### 6. IAMRoleResult Dataclass

1. Run Python:
   ```python
   from zscaler_mcp_deploy.models import IAMRoleResult
   r = IAMRoleResult(arn="arn:aws:iam::123456789:role/test", name="test", role_id="AROA123", created=True)
   print(r.to_dict())
   ```
2. **Expected:** Dict with arn, name, role_id, created fields

## Edge Cases

### BootstrapResult Serialization

1. Run Python:
   ```python
   from zscaler_mcp_deploy.models import BootstrapResult
   r = BootstrapResult(success=True, secret_arn="arn:aws:secretsmanager:us-east-1:123:secret/test-AbCdEf", role_arn="arn:aws:iam::123:role/test-role")
   print(r.to_dict())
   ```
2. **Expected:** Complete dict with all fields including success=True, phase=None

### Error Code Propagation

1. Run Python:
   ```python
   from zscaler_mcp_deploy.bootstrap import BootstrapOrchestrator, BootstrapConfig
   from zscaler_mcp_deploy.aws.secrets_manager import SecretsManagerError
   
   # Force error by mocking
   import unittest.mock as mock
   orch = BootstrapOrchestrator()
   config = BootstrapConfig(secret_name="test", role_name="test", username="u", password="p", api_key="k")
   
   with mock.patch.object(orch.secrets_manager, 'create_or_use_secret', side_effect=SecretsManagerError("test", error_code="S02-001-Test")):
       result = orch.bootstrap_resources(config)
   
   print(result.error_code)  # Should propagate S02-001-Test
   ```
2. **Expected:** Error code propagates from Secrets Manager through to BootstrapResult

## Failure Signals

- Help text missing bootstrap command → CLI integration failed
- Test failures in S02 test files → Module implementation issue
- S01 tests failing → Regression introduced
- Missing error codes in error messages → Error handling broken

## Requirements Proved By This UAT

- R003 — AWS Secrets Manager Integration — Proved by 31 passing tests covering create, reuse, error paths

## Not Proven By This UAT

- Actual AWS resource creation (requires live AWS account)
- IAM propagation wait timing (needs real AWS)
- Bedrock AgentCore runtime deployment (S03 scope)
- Runtime verification against CloudWatch logs (S04 scope)

## Notes for Tester

- All tests use mocked boto3 — no AWS charges incurred
- Test coverage exceeds target (117 vs 40+ required)
- Error codes follow taxonomy: S02-001 (Secrets), S02-002 (IAM), S02-003 (Orchestrator)
- Secret values never appear in logs or test output
