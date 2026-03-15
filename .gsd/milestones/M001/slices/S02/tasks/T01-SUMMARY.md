---
id: T01
parent: S02
milestone: M001
provides:
  - SecretsManager class with idempotent create_or_use_secret() method
  - SecretResult dataclass for secret operation results
  - Comprehensive test suite (31 tests)
key_files:
  - src/zscaler_mcp_deploy/aws/__init__.py
  - src/zscaler_mcp_deploy/models.py
  - src/zscaler_mcp_deploy/aws/secrets_manager.py
  - tests/test_secrets_manager.py
key_decisions:
  - Lazy boto3 session/client initialization for testability
  - ResourceExistsException handled by describing existing secret and returning created=False
  - AWS-managed KMS key as default (aws/secretsmanager), with optional customer-managed key support
  - SecretsManagerError with error code S02-001 per slice error taxonomy
  - JSON secret structure with username, password, api_key, cloud fields
patterns_established:
  - AWS resource modules follow lazy initialization pattern with injectable boto3.Session
  - Idempotent operations return Result dataclass with created boolean flag
  - ClientError handling extracts AWS error codes and maps to domain errors with context
observability_surfaces:
  - Structured logging via logging module (secret creation events at INFO level, errors at ERROR)
  - Error context includes secret_name, aws_error_code, kms_key_id for diagnostics
  - Secret values never logged (only ARNs and names)
duration: 35m
verification_result: passed
completed_at: 2026-03-14
blocker_discovered: false
---

# T01: Secrets Manager Module

**Implemented SecretsManager class with idempotent KMS-encrypted secret creation for Zscaler credentials**

## What Happened

Created the Secrets Manager module that provides idempotent secret creation with automatic handling of resource existence. The module follows S01 patterns for boto3 session validation and error handling.

Key implementation details:
- **Lazy initialization**: boto3 Session and Secrets Manager client are created on first access to support test dependency injection
- **Idempotent create_or_use_secret()**: Creates new secret or returns existing secret details if ResourceExistsException is raised
- **KMS encryption**: Defaults to AWS-managed key (aws/secretsmanager), supports customer-managed key via kms_key_id parameter
- **JSON secret structure**: {"username": "...", "password": "...", "api_key": "...", "cloud": "..."}
- **Error handling**: SecretsManagerError with error code S02-001 includes full context (secret_name, aws_error_code, kms_key_id)
- **Additional operations**: get_secret_value() for retrieval, delete_secret() for cleanup

## Verification

```bash
poetry run pytest tests/test_secrets_manager.py -v
```

Result: **31 tests passed** (exceeds 15+ requirement)

Test coverage:
- SecretResult dataclass creation, defaults, and serialization (3 tests)
- SecretsManager initialization with various parameter combinations (7 tests)
- create_or_use_secret() success and error scenarios (7 tests)
- get_secret_value() success and error paths (4 tests)
- delete_secret() with various options (4 tests)
- SecretsManagerError behavior (4 tests)
- All tests use mocked boto3 (no real AWS calls)

## Diagnostics

- **Inspect test results**: `poetry run pytest tests/test_secrets_manager.py -v`
- **Check error codes**: Look for S02-001 prefix in error messages
- **Review logs**: Secret creation events logged at INFO level; errors at ERROR level
- **Verify secret structure**: `get_secret_value()` returns parsed JSON dict

## Deviations

None. Implementation followed task plan specifications.

## Known Issues

None.

## Files Created/Modified

- `src/zscaler_mcp_deploy/aws/__init__.py` — AWS package initialization with exports
- `src/zscaler_mcp_deploy/models.py` — Shared dataclasses (SecretResult, IAMRoleResult)
- `src/zscaler_mcp_deploy/aws/secrets_manager.py` — SecretsManager class with full CRUD operations
- `tests/test_secrets_manager.py` — 31 comprehensive unit tests with mocked boto3