---
estimated_steps: 7
estimated_files: 2
---

# T02: IAM Role Module

**Slice:** S02 — Secrets Manager & IAM Bootstrap
**Milestone:** M001

## Description

Implement the IAM role bootstrap module that creates or references existing IAM execution roles for Bedrock AgentCore. This includes trust policy generation, inline policy attachment, and IAM propagation wait handling.

## Steps

1. Create `src/zscaler_mcp_deploy/aws/iam_bootstrap.py` with `IAMBootstrap` class (named to avoid conflict with validators/iam.py)
2. Implement `create_or_use_execution_role()` method
3. Generate trust policy document with `bedrock.amazonaws.com` service principal
4. Generate inline policy with `secretsmanager:GetSecretValue` for specific secret ARN and CloudWatch Logs permissions
5. Handle `EntityAlreadyExistsException` by getting existing role and validating trust policy compatibility
6. Implement 15-second wait with exponential backoff after role creation for IAM propagation
7. Write `tests/test_iam_bootstrap.py` with 15+ tests covering trust policy, inline policy, and wait logic

## Must-Haves

- [ ] `RoleResult` dataclass with ARN, name, role_id, created flag
- [ ] IAMBootstrap class with lazy boto3 session initialization
- [ ] Trust policy: `bedrock.amazonaws.com` principal with `sts:AssumeRole` action
- [ ] Inline policy: Secrets Manager read (specific secret ARN), CloudWatch Logs write
- [ ] Handle EntityAlreadyExistsException with trust policy validation
- [ ] 15-second IAM propagation wait with exponential backoff
- [ ] 15+ unit tests with mocked boto3

## Verification

- `poetry run pytest tests/test_iam_bootstrap.py -v` passes all tests
- Tests cover: create new role, reuse existing role, trust policy validation, inline policy attachment, wait logic
- No real AWS calls made (all mocked)

## Observability Impact

- Signals added/changed: Structured logging for IAM role creation and propagation wait
- How a future agent inspects this: Run tests and check for pass/fail
- Failure state exposed: Specific error codes (S02-002) with role name and missing permissions

## Inputs

- `src/zscaler_mcp_deploy/errors.py` — Use existing error hierarchy for AWS IAM errors
- `src/zscaler_mcp_deploy/models.py` — Extend with RoleResult dataclass
- `src/zscaler_mcp_deploy/validators/iam.py` — Follow boto3 patterns and permission structures

## Expected Output

- `src/zscaler_mcp_deploy/aws/iam_bootstrap.py` — IAMBootstrap class
- `src/zscaler_mcp_deploy/models.py` — Updated with RoleResult dataclass
- `tests/test_iam_bootstrap.py` — 15+ unit tests
