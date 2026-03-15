---
id: T03
parent: S02
milestone: M001
provides:
  - BootstrapOrchestrator class coordinating secret and IAM role creation
  - BootstrapResult and BootstrapConfig dataclasses
  - Rollback capability on partial failure
  - Preflight validation integration
key_files:
  - src/zscaler_mcp_deploy/bootstrap.py
  - src/zscaler_mcp_deploy/models.py
  - tests/test_bootstrap.py
key_decisions:
  - Injected dependencies pattern for testability (secrets_manager, iam_bootstrap, validator)
  - Resource tracking as list of tuples [(resource_type, resource_id)] for rollback ordering
  - Reverse-order rollback (role first, then secret) to avoid dependency conflicts
  - BootstrapOrchestratorError base class with phase tracking for diagnostics
  - Resource IDs cleared after successful rollback to prevent double-delete
patterns_established:
  - Orchestrator pattern with injected AWS service dependencies
  - Phase-based error tracking (preflight, secret, role, rollback)
  - Resource tracking for transactional rollback
  - Result dataclass with success flag and detailed context
observability_surfaces:
  - Structured logging for each bootstrap phase
  - BootstrapResult.to_dict() for inspection
  - get_created_resources() method for runtime state check
  - Error codes S02-003-* for orchestrator failures
  - Phase attribute in error results for failure analysis
duration: 25m
verification_result: passed
completed_at: 2025-03-14T23:35:00Z
blocker_discovered: false
---

# T03: Bootstrap Orchestrator

**Created BootstrapOrchestrator class that coordinates Secrets Manager and IAM role creation with automatic rollback on partial failure.**

## What Happened

Implemented the bootstrap orchestrator that ties together the Secrets Manager (T01) and IAM Bootstrap (T02) modules into a cohesive, reliable unit. The orchestrator follows a transactional pattern: validate first, then create resources, rolling back any newly created resources if a later step fails.

Key implementation details:
- **BootstrapConfig dataclass**: Holds all configuration parameters for bootstrap including secret/role names, credentials, KMS key, and tags
- **BootstrapResult dataclass**: Returns complete operation results including ARNs, resource IDs, success flag, error details, and creation flags for each resource
- **BootstrapOrchestrator class**: Orchestrates the three-phase process (preflight → secret → role) with resource tracking
- **Rollback logic**: Deletes resources in reverse order (role first, then secret) to handle dependencies correctly
- **Preflight integration**: Validates AWS credentials and region before any resource creation using S01's AWSSessionValidator
- **Error handling**: Distinguishes between preflight, secret, and role failure phases with appropriate error codes

The rollback behavior is conditional: only resources that were newly created during this bootstrap run are rolled back. Existing resources that were reused are left untouched.

## Verification

All 26 unit tests pass, covering:
- BootstrapConfig and BootstrapResult dataclass behavior (5 tests)
- Orchestrator initialization with defaults and injected dependencies (5 tests)
- Preflight validation pass/fail scenarios (3 tests)
- Success paths: new resources, existing resources, mixed (3 tests)
- Failure paths: secret creation failure, role creation failure with/without rollback (3 tests)
- Rollback functionality: reverse order deletion, error handling, resource clearing (5 tests)
- Integration and config passing verification (2 tests)

```bash
$ poetry run pytest tests/test_bootstrap.py -v
26 passed in 0.14s

$ poetry run pytest tests/test_secrets_manager.py tests/test_iam_bootstrap.py tests/test_bootstrap.py
96 passed in 0.11s
```

## Diagnostics

**How to inspect bootstrap results:**
```python
from zscaler_mcp_deploy.bootstrap import BootstrapOrchestrator, BootstrapConfig

orch = BootstrapOrchestrator()
config = BootstrapConfig(
    secret_name="my-secret",
    role_name="my-role",
    username="admin",
    password="pass",
    api_key="key",
    cloud="zscaler"
)
result = orch.bootstrap_resources(config)

# Check result
print(result.to_dict())
print(f"Success: {result.success}")
print(f"Phase: {result.phase}")
print(f"Resources created: {result.resource_ids}")
```

**Error codes:**
- `S02-003-PreflightFailed`: AWS credentials or region validation failed
- `S02-003-SecretFailed`: Secret creation failed (propagated from S02-001-*)
- `S02-003-RoleFailed`: Role creation failed (propagated from S02-002-*)

**Runtime inspection:**
```python
# Check resources created so far
resources = orch.get_created_resources()
# Returns: [("secret", "secret-name"), ("role", "role-name")]

# Manual rollback if needed
success, errors = orch.rollback()
```

## Deviations

None. Implementation followed the task plan exactly.

## Known Issues

None.

## Files Created/Modified

- `src/zscaler_mcp_deploy/bootstrap.py` — BootstrapOrchestrator class with full orchestration and rollback logic
- `src/zscaler_mcp_deploy/models.py` — Added BootstrapConfig and BootstrapResult dataclasses
- `tests/test_bootstrap.py` — 26 unit tests covering all paths
