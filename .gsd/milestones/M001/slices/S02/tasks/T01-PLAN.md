---
estimated_steps: 6
estimated_files: 3
---

# T01: Secrets Manager Module

**Slice:** S02 — Secrets Manager & IAM Bootstrap
**Milestone:** M001

## Description

Implement the Secrets Manager module that creates or references existing KMS-encrypted secrets for Zscaler credentials. This module provides idempotent secret creation with automatic handling of resource existence.

## Steps

1. Create `src/zscaler_mcp_deploy/aws/__init__.py` to establish the aws package
2. Create `src/zscaler_mcp_deploy/models.py` with `SecretResult` dataclass containing ARN, name, version_id, and created flag
3. Create `src/zscaler_mcp_deploy/aws/secrets_manager.py` with `SecretsManager` class
4. Implement `create_or_use_secret()` method with boto3 secretsmanager client
5. Handle `ResourceExistsException` by describing the secret and validating it has compatible structure
6. Write `tests/test_secrets_manager.py` with 15+ tests covering create, reuse, and error scenarios

## Must-Haves

- [ ] `SecretResult` dataclass with ARN, name, version_id, created flag
- [ ] SecretsManager class with lazy boto3 session initialization
- [ ] `create_or_use_secret()` returns SecretResult, handles ResourceExistsException
- [ ] JSON secret structure: `{"username": "...", "password": "...", "api_key": "...", "cloud": "..."}`
- [ ] Default to AWS-managed KMS key (aws/secretsmanager)
- [ ] Optional customer-managed KMS key ARN support
- [ ] 15+ unit tests with mocked boto3

## Verification

- `poetry run pytest tests/test_secrets_manager.py -v` passes all tests
- Tests cover: create new secret, reuse existing secret, KMS key handling, error scenarios
- No real AWS calls made (all mocked)

## Observability Impact

- Signals added/changed: Structured logging for secret creation events
- How a future agent inspects this: Run tests and check for pass/fail
- Failure state exposed: Specific error codes (S02-001) with secret name and error details

## Inputs

- `src/zscaler_mcp_deploy/errors.py` — Use existing error hierarchy for AWS errors
- `src/zscaler_mcp_deploy/validators/aws.py` — Follow boto3 session patterns

## Expected Output

- `src/zscaler_mcp_deploy/aws/__init__.py` — Package init
- `src/zscaler_mcp_deploy/models.py` — SecretResult dataclass
- `src/zscaler_mcp_deploy/aws/secrets_manager.py` — SecretsManager class
- `tests/test_secrets_manager.py` — 15+ unit tests
