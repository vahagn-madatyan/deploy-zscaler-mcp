---
estimated_steps: 6
estimated_files: 2
---

# T03: Bootstrap Orchestrator

**Slice:** S02 — Secrets Manager & IAM Bootstrap
**Milestone:** M001

## Description

Create the bootstrap orchestrator that coordinates secret and IAM role creation with rollback capability on partial failure. This is the glue that makes S02 a cohesive, reliable unit.

## Steps

1. Create `src/zscaler_mcp_deploy/bootstrap.py` with `BootstrapOrchestrator` class
2. Implement `bootstrap_resources(config)` method that orchestrates secret → role creation
3. Track created resources in a list for potential rollback
4. Implement `rollback()` method that deletes resources in reverse order (role first, then secret)
5. Integrate with S01 preflight validators to fail fast before creating resources
6. Write `tests/test_bootstrap.py` with 15+ tests covering success, partial failure, and rollback

## Must-Haves

- [ ] `BootstrapResult` dataclass with secret_arn, role_arn, resource_ids, success flag
- [ ] `BootstrapConfig` dataclass with secret_name, role_name, credentials, kms_key_id, region
- [ ] BootstrapOrchestrator class with secrets_manager and iam_bootstrap instances
- [ ] Resource tracking for rollback (list of created resources)
- [ ] Rollback on partial failure (delete in reverse order)
- [ ] Preflight validation before any resource creation
- [ ] 15+ unit tests with mocked dependencies

## Verification

- `poetry run pytest tests/test_bootstrap.py -v` passes all tests
- Tests cover: success path, secret creation failure, role creation failure with rollback, preflight failure
- No real AWS calls made (all mocked)

## Observability Impact

- Signals added/changed: Structured logging for bootstrap phases and rollback operations
- How a future agent inspects this: Run tests and check for pass/fail; inspect BootstrapResult
- Failure state exposed: Specific error codes (S02-003) with phase and resources created before failure

## Inputs

- `src/zscaler_mcp_deploy/aws/secrets_manager.py` — SecretsManager class from T01
- `src/zscaler_mcp_deploy/aws/iam_bootstrap.py` — IAMBootstrap class from T02
- `src/zscaler_mcp_deploy/models.py` — SecretResult and RoleResult dataclasses
- `src/zscaler_mcp_deploy/validators/aws.py` — AWSSessionValidator for preflight

## Expected Output

- `src/zscaler_mcp_deploy/bootstrap.py` — BootstrapOrchestrator class
- `src/zscaler_mcp_deploy/models.py` — Updated with BootstrapResult and BootstrapConfig
- `tests/test_bootstrap.py` — 15+ unit tests
