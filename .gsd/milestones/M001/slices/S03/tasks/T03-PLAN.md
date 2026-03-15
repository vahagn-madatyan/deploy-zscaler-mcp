---
estimated_steps: 9
estimated_files: 4
---

# T03: DeployOrchestrator & CLI Integration

**Slice:** S03 — Bedrock Runtime Deployment
**Milestone:** M001

## Description

Create the `DeployOrchestrator` class that coordinates the complete deployment flow: bootstrap (S02) → runtime creation (T01/T02). Also extend the CLI with the `deploy` command that users actually run. This is the composition layer that brings everything together.

The orchestrator must:
- Integrate with BootstrapOrchestrator to ensure resources exist
- Call BedrockRuntime to create and poll for runtime readiness
- Implement rollback on runtime failure (cleanup created runtime)
- Return DeployResult with all resource IDs, ARNs, and endpoint info

The CLI command must:
- Accept all flags from bootstrap command plus runtime-specific flags
- Show Rich table output with runtime details
- Support --runtime-name, --image-uri, --enable-write-tools flags

## Steps

1. Create `deploy.py` with `DeployOrchestrator` class
2. Implement `__init__` accepting optional BootstrapOrchestrator and BedrockRuntime (for injection)
3. Implement `deploy()` method chaining: bootstrap → create runtime → poll status
4. Add rollback logic: delete runtime on failure (role/secret kept per R008 deferred)
5. Extend `models.py` with `DeployConfig` dataclass
6. Extend CLI with `deploy` command in `cli.py`
7. Add all flags: --runtime-name (required), --image-uri (optional), --enable-write-tools
8. Implement Rich table output showing: runtime ARN, status, endpoint URL, next steps
9. Add error handling with specific error codes S03-003-* for orchestration failures

## Must-Haves

- [ ] `DeployOrchestrator` class with `deploy()` method coordinating bootstrap + runtime
- [ ] Rollback on runtime creation failure (delete runtime, keep bootstrap resources)
- [ ] CLI `deploy` command with all required and optional flags
- [ ] Rich table output showing runtime details, status, and endpoint
- [ ] Support for --enable-write-tools flag passing to runtime env vars
- [ ] Error codes S03-003-* for orchestration failures
- [ ] `DeployResult` dataclass with runtime_id, runtime_arn, endpoint_url, bootstrap_result

## Verification

- `poetry run pytest tests/test_deploy.py::test_deploy_orchestrator_success -xvs` passes
- `poetry run pytest tests/test_deploy.py::test_deploy_orchestrator_rollback -xvs` passes
- `poetry run zscaler-mcp-deploy deploy --help` shows all options
- `poetry run zscaler-mcp-deploy deploy --non-interactive 2>&1 | head -5` shows error (missing required flags)

## Observability Impact

- Signals added: Deploy phase tracking (bootstrap, runtime_create, polling), rollback events
- How a future agent inspects this: DeployResult.phase shows where failure occurred, DeployResult.resource_ids for cleanup
- Failure state exposed: S03-003-* error codes with phase information

## Inputs

- `src/zscaler_mcp_deploy/bootstrap.py` — BootstrapOrchestrator pattern to follow
- `src/zscaler_mcp_deploy/aws/bedrock_runtime.py` — BedrockRuntime from T01/T02
- `src/zscaler_mcp_deploy/models.py` — Extend with DeployConfig, DeployResult
- `src/zscaler_mcp_deploy/cli.py` — CLI structure, follow bootstrap command pattern
- T01 and T02 completed

## Expected Output

- `src/zscaler_mcp_deploy/deploy.py` — DeployOrchestrator class (~250 lines)
- `src/zscaler_mcp_deploy/models.py` — Extended with DeployConfig, DeployResult
- `src/zscaler_mcp_deploy/cli.py` — Extended with deploy command and Rich output
- `src/zscaler_mcp_deploy/errors.py` — Extended with S03-003-* error codes
