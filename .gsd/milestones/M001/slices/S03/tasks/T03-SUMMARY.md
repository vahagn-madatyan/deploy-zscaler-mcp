---
id: T03
parent: S03
milestone: M001
provides:
  - DeployOrchestrator class coordinating bootstrap → runtime → polling
  - CLI deploy command with Rich table output
  - Rollback on runtime failure (runtime deleted, bootstrap resources kept)
  - DeployConfig and DeployResult dataclasses
  - S03-003-* error codes for orchestration failures
key_files:
  - src/zscaler_mcp_deploy/deploy.py
  - src/zscaler_mcp_deploy/cli.py
  - src/zscaler_mcp_deploy/models.py
  - src/zscaler_mcp_deploy/errors.py
  - tests/test_deploy.py
key_decisions:
  - Injected BootstrapOrchestrator and BedrockRuntime for testability (same pattern as S02)
  - Rollback only deletes runtime per R008; bootstrap resources kept for troubleshooting/reuse
  - DeployResult includes full BootstrapResult for downstream inspection
  - Lazy initialization via @property for session, bootstrap_orchestrator, bedrock_runtime
patterns_established:
  - Orchestrator pattern: DeployOrchestrator composes BootstrapOrchestrator + BedrockRuntime
  - Phase-based deployment: bootstrap → runtime_create → polling → completed
  - Rollback tracking: _created_runtime_id tracked for cleanup on failure
  - Error codes with phase context: S03-003-{BootstrapFailed|RuntimeCreateFailed|PollingTimeout|RuntimeFailed}
observability_surfaces:
  - DeployResult.phase shows failure location (bootstrap, runtime_create, polling)
  - DeployResult.bootstrap_result provides full bootstrap details for inspection
  - DeployResult.error_code with S03-003-* prefix for orchestration failures
  - Log signals: "Phase: {name}", "Runtime created with ID: {id}", "Rollback completed"
duration: 50m
verification_result: passed
completed_at: 2026-03-14
blocker_discovered: false
---

# T03: DeployOrchestrator & CLI Integration

**Created DeployOrchestrator class and CLI deploy command that coordinate complete deployment flow from bootstrap to runtime readiness.**

## What Happened

Created `DeployOrchestrator` class in `deploy.py` that orchestrates the three-phase deployment:
1. **Bootstrap phase**: Calls `BootstrapOrchestrator` to create/get secret and IAM role
2. **Runtime creation phase**: Calls `BedrockRuntime.create_runtime()` with credentials
3. **Polling phase**: Polls until runtime reaches READY or fails

Implemented rollback on runtime failure: only the runtime is deleted (per R008), while bootstrap resources (secret, IAM role) are kept for troubleshooting and reuse. This follows the principle that persistent infrastructure should not be destroyed on transient runtime failures.

Extended CLI with `deploy` command accepting all bootstrap flags plus runtime-specific flags (`--runtime-name`, `--image-uri`, `--enable-write-tools`, `--poll-timeout`). Rich table output shows all resources (secret, role, runtime) with their status and creation type (Created/Reused/READY).

Added `DeployConfig` dataclass combining bootstrap and runtime configuration, and extended `DeployResult` to include full `BootstrapResult` for downstream inspection. Added `DeployOrchestratorError` class to `errors.py` with S03-003-* error codes.

Created comprehensive test suite with 19 tests covering success paths, bootstrap failure, runtime creation failure, polling timeout with rollback, runtime CREATE_FAILED with rollback, rollback failure scenarios, and lazy initialization.

## Verification

- `poetry run pytest tests/test_deploy.py::TestDeployOrchestrator::test_deploy_orchestrator_success -xvs` passes
- `poetry run pytest tests/test_deploy.py::TestDeployOrchestrator::test_deploy_orchestrator_polling_timeout_with_rollback -xvs` passes
- `poetry run pytest tests/test_deploy.py::TestDeployOrchestrator::test_deploy_orchestrator_runtime_failed_with_rollback -xvs` passes
- `poetry run pytest tests/test_deploy.py -v` — all 19 tests pass
- `poetry run zscaler-mcp-deploy deploy --help` shows all options (--runtime-name, --image-uri, --enable-write-tools, --poll-timeout, etc.)
- `poetry run zscaler-mcp-deploy deploy --non-interactive 2>&1 | head -5` shows error for missing required flags

## Diagnostics

**How to inspect deployment state:**
- Check `DeployResult.phase` field: "bootstrap", "runtime_create", "polling", "completed"
- On failure, inspect `DeployResult.error_code` (e.g., "S03-003-RuntimeCreateFailed")
- Access full bootstrap details via `DeployResult.bootstrap_result`
- Use `DeployOrchestrator.get_created_runtime_id()` to get runtime ID for cleanup

**Log signals:**
- `"Phase: bootstrap - creating secret and IAM role"` — Bootstrap started
- `"Phase: runtime creation - {name}"` — Runtime creation started
- `"Phase: polling runtime status - {id}"` — Polling started
- `"Runtime created with ID: {id}"` — Runtime created successfully
- `"Phase: rollback - deleting runtime {id}"` — Rollback initiated
- `"Rollback completed: runtime {id} deleted"` — Rollback succeeded

**Error codes:**
- `S03-003-BootstrapFailed` — Bootstrap phase failed (check error_code from bootstrap)
- `S03-003-RuntimeCreateFailed` — Runtime creation API call failed
- `S03-003-PollingTimeout` — Runtime did not reach READY within timeout
- `S03-003-RuntimeFailed` — Runtime reached CREATE_FAILED state

## Deviations

None. Implementation followed task plan exactly.

## Known Issues

None.

## Files Created/Modified

- `src/zscaler_mcp_deploy/deploy.py` — DeployOrchestrator class (~290 lines) with deploy(), _run_bootstrap(), _create_runtime(), _poll_runtime(), _rollback_runtime() methods
- `src/zscaler_mcp_deploy/cli.py` — Extended with deploy command (~170 lines) with all flags and Rich table output
- `src/zscaler_mcp_deploy/models.py` — Added DeployConfig dataclass, extended DeployResult with bootstrap_result field
- `src/zscaler_mcp_deploy/errors.py` — Added DeployOrchestratorError class with S03-003-* error codes
- `tests/test_deploy.py` — 19 comprehensive unit tests for DeployOrchestrator, DeployResult, DeployConfig