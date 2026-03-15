---
id: T02
parent: S02
milestone: M001
provides:
  - IAMBootstrap class with idempotent create_or_use_execution_role() method
  - Trust policy generation for bedrock.amazonaws.com service principal
  - Inline policy generation for Secrets Manager read and CloudWatch Logs write
  - IAM propagation wait with exponential backoff
  - TrustPolicyMismatchError for incompatible existing roles
key_files:
  - src/zscaler_mcp_deploy/aws/iam_bootstrap.py
  - src/zscaler_mcp_deploy/models.py
  - tests/test_iam_bootstrap.py
key_decisions:
  - Named module iam_bootstrap.py (not iam.py) to avoid conflict with validators/iam.py
  - Lazy boto3 session/client initialization following SecretsManager pattern for testability
  - Exponential backoff for propagation wait: 1s + 2s + 4s = 7s minimum (capped at 15s target)
  - Trust policy validation checks for bedrock.amazonaws.com principal with sts:AssumeRole action
patterns_established:
  - AWS resource modules follow lazy initialization with injectable boto3.Session
  - Idempotent operations return Result dataclass with created boolean flag
  - Error codes use S02-002 prefix with specific suffixes (S02-002-TrustMismatch, S02-002-AccessDenied)
  - Structured logging for IAM operations at INFO level; errors at ERROR level
observability_surfaces:
  - Structured logs for role creation and propagation wait
  - Specific error codes (S02-002-*) with role name and missing permissions context
  - RoleResult.to_dict() for inspection
  - get_role() method for checking role existence
duration: 35m
verification_result: passed
completed_at: 2026-03-14
blocker_discovered: false
---

# T02: IAM Role Module

**IAMBootstrap class implemented with idempotent role creation, trust policy validation, and IAM propagation wait.**

## What Happened

Implemented the IAM role bootstrap module that creates or references existing IAM execution roles for Bedrock AgentCore. The module includes trust policy generation with `bedrock.amazonaws.com` service principal, inline policy attachment for Secrets Manager read and CloudWatch Logs write permissions, and a 15-second IAM propagation wait with exponential backoff.

Key implementation details:
- **IAMBootstrap class**: Lazy boto3 session initialization, supports injectable session for testing
- **Trust policy**: Generated with `bedrock.amazonaws.com` principal and `sts:AssumeRole` action
- **Inline policy**: Grants `secretsmanager:GetSecretValue` for specific secret ARN and CloudWatch Logs permissions for `/aws/bedrock/*` log groups
- **EntityAlreadyExists handling**: When role exists, validates trust policy compatibility and raises `TrustPolicyMismatchError` if incompatible
- **Propagation wait**: Exponential backoff with 3 retries (1s + 2s + 4s) targeting 15s total wait time
- **Error hierarchy**: `IAMBootstrapError` (S02-002) with specific `TrustPolicyMismatchError` (S02-002-TrustMismatch)
- **Models update**: Added `role_id` field to `IAMRoleResult` dataclass

## Verification

```bash
poetry run pytest tests/test_iam_bootstrap.py -v
```

All 39 tests passed:
- IAMRoleResult dataclass tests (3 tests)
- IAMBootstrap initialization tests (9 tests)
- Trust policy generation tests (1 test)
- Inline policy generation tests (3 tests)
- Trust policy validation tests (5 tests)
- Create or use execution role tests (6 tests)
- Propagation wait tests (2 tests)
- Get role tests (3 tests)
- Delete role tests (3 tests)
- Error class tests (4 tests)

## Diagnostics

**Inspect role creation:**
```python
from zscaler_mcp_deploy.aws.iam_bootstrap import IAMBootstrap
iam = IAMBootstrap()
result = iam.create_or_use_execution_role("my-role", "arn:aws:secretsmanager:...")
print(result.to_dict())
```

**Check role existence:**
```python
existing = iam.get_role("my-role")
if existing:
    print(f"Role exists: {existing.arn}")
```

**Error codes:**
- S02-002: General IAM bootstrap error
- S02-002-TrustMismatch: Existing role has incompatible trust policy
- S02-002-AccessDenied: Insufficient permissions
- S02-002-NoSuchEntity: Role not found

## Deviations

None. Implementation followed task plan specifications.

## Known Issues

None.

## Files Created/Modified

- `src/zscaler_mcp_deploy/aws/iam_bootstrap.py` — IAMBootstrap class with trust policy generation, inline policy attachment, propagation wait
- `src/zscaler_mcp_deploy/models.py` — Updated IAMRoleResult with role_id field
- `tests/test_iam_bootstrap.py` — 39 comprehensive unit tests with mocked boto3
