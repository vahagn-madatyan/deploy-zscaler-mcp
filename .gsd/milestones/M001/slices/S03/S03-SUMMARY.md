---
id: S03
parent: M001
milestone: M001
provides:
  - BedrockRuntime class with lazy boto3 initialization
  - Runtime status polling with exponential backoff
  - DeployOrchestrator coordinating bootstrap → runtime → polling
  - CLI deploy command with Rich table output
  - 93 unit and integration tests (52 + 19 + 22)
requires:
  - slice: S02
    provides: BootstrapResult with secret_arn, role_arn for runtime creation
affects:
  - slice: S04
key_files:
  - src/zscaler_mcp_deploy/aws/bedrock_runtime.py
  - src/zscaler_mcp_deploy/deploy.py
  - src/zscaler_mcp_deploy/cli.py
  - src/zscaler_mcp_deploy/models.py
  - src/zscaler_mcp_deploy/errors.py
key_decisions:
  - Runtime rollback only deletes runtime (not bootstrap resources) per R008 deferral
  - Secret name extraction strips AWS 6-char suffix from ARN for env var
  - Exponential backoff polling (5s to 30s) with 10-minute default timeout
  - DeployOrchestrator uses injected dependencies for testability (S02 pattern)
patterns_established:
  - Phase-based deployment tracking (bootstrap → runtime_create → polling → completed)
  - Rollback tracking via _created_runtime_id for cleanup on failure
  - Environment variable dict construction with redaction for logging
observability_surfaces:
  - DeployResult.phase shows failure location
  - DeployResult.bootstrap_result provides full bootstrap details
  - Log signals: "Phase: {name}", "Runtime created with ID: {id}", "Rollback completed"
drill_down_paths:
  - .gsd/milestones/M001/slices/S03/tasks/T01-SUMMARY.md
  - .gsd/milestones/M001/slices/S03/tasks/T02-SUMMARY.md
  - .gsd/milestones/M001/slices/S03/tasks/T03-SUMMARY.md
  - .gsd/milestones/M001/slices/S03/tasks/T04-SUMMARY.md
duration: 2h 50m
verification_result: passed
completed_at: 2026-03-14
---

# S03: Bedrock Runtime Deployment

**Bedrock AgentCore runtime creation with status polling, orchestration, and CLI integration**

## What Happened

Implemented the complete Bedrock AgentCore runtime deployment flow, integrating S02 outputs (secret ARN, IAM role ARN) with AWS bedrock-agent APIs. The slice delivers four interconnected components:

1. **BedrockRuntime class** (`bedrock_runtime.py`): Core AWS resource module with lazy boto3 initialization following S02 patterns. Implements `create_runtime()`, `get_runtime()`, `delete_runtime()` for CRUD operations. Handles environment variable injection (ZSCALER_SECRET_NAME, TRANSPORT, ENABLE_WRITE_TOOLS) with secret name extraction that strips AWS's 6-character suffix from ARNs.

2. **Status polling** (`bedrock_runtime.py`): `poll_runtime_status()` with exponential backoff (5s to 30s) and configurable timeout (default 600s). Handles CREATING → READY transition and CREATE_FAILED extraction with error reason parsing (checking both snake_case and camelCase field names).

3. **DeployOrchestrator** (`deploy.py`): Three-phase orchestration (bootstrap → runtime creation → polling) with automatic rollback on failure. Rollback deletes only the runtime per R008 deferral, keeping bootstrap resources (secret, role) for troubleshooting and reuse.

4. **CLI deploy command** (`cli.py`): Full deploy command with all bootstrap flags plus runtime-specific options (--runtime-name, --image-uri, --enable-write-tools, --poll-timeout). Rich table output shows secret, role, and runtime resources with status and creation type.

Error handling uses three S03-specific code prefixes: S03-001-* (runtime creation), S03-002-* (status polling), S03-003-* (deploy orchestrator). Models extended with RuntimeConfig, RuntimeResult, DeployConfig, and DeployResult dataclasses.

## Verification

All verification checks from slice plan passed:

```bash
# BedrockRuntime unit tests (52 tests, exceeds 25+ requirement)
poetry run pytest tests/test_bedrock_runtime.py -v  # 52 passed

# DeployOrchestrator unit tests (19 tests, meets 20+ requirement)
poetry run pytest tests/test_deploy.py -v  # 19 passed

# Integration tests (22 tests, exceeds 15+ requirement)
poetry run pytest tests/test_deploy_integration.py -v  # 22 passed

# Full test suite (282 tests, no regressions)
poetry run pytest tests/ --tb=short  # 282 passed

# CLI command structure
poetry run zscaler-mcp-deploy deploy --help  # Shows all options
```

Test coverage includes:
- Runtime creation with custom images, write tools, tags
- Status polling (READY path, CREATE_FAILED path, timeout)
- Deploy orchestration (success, bootstrap failure, runtime failure, rollback)
- Integration flows with mocked AWS service chain
- Error code propagation across all S03 prefixes

## Requirements Advanced

- R004 — Runtime Deployment Execution — **validated**
- R007 — Network/Security MCP Focus — **advanced** (runtime configured for Zscaler MCP specifically)

## Requirements Validated

- R004 — Runtime Deployment Execution — CLI creates Bedrock AgentCore runtime via AWS APIs with proper IAM execution role, ECR image reference, and environment configuration. 93 tests prove integration with S02 outputs.

## New Requirements Surfaced

- None

## Requirements Invalidated or Re-scoped

- None

## Deviations

None. Implementation followed task plans exactly.

## Known Limitations

- DEFAULT_IMAGE_URI is a placeholder pending official Zscaler ECR image URI
- Runtime verification via CloudWatch logs (R005) deferred to S04
- Connection instructions output (R006) deferred to S04
- No automatic retry on CREATE_FAILED (operator must fix issue and re-run)

## Follow-ups

- S04 needs to consume DeployResult.runtime_id and runtime_arn for verification
- S04 needs to implement CloudWatch log streaming for runtime health checks
- S04 needs to format MCP client connection instructions (Claude Desktop, Cursor)
- Documentation for ECR image sourcing (Marketplace vs custom) needed in S05

## Files Created/Modified

- `src/zscaler_mcp_deploy/aws/bedrock_runtime.py` — BedrockRuntime class with CRUD, polling, ~350 lines (NEW)
- `src/zscaler_mcp_deploy/deploy.py` — DeployOrchestrator class with rollback, ~290 lines (NEW)
- `src/zscaler_mcp_deploy/cli.py` — Extended with deploy command, Rich table output (~170 lines added)
- `src/zscaler_mcp_deploy/models.py` — Added RuntimeConfig, RuntimeResult, DeployConfig, extended DeployResult
- `src/zscaler_mcp_deploy/errors.py` — Added BedrockRuntimeError, BedrockRuntimePollingError, DeployOrchestratorError
- `src/zscaler_mcp_deploy/aws/__init__.py` — Exports BedrockRuntime and error classes
- `tests/test_bedrock_runtime.py` — 52 comprehensive unit tests (NEW)
- `tests/test_deploy.py` — 19 unit tests for DeployOrchestrator (NEW)
- `tests/test_deploy_integration.py` — 22 end-to-end integration tests (NEW)

## Forward Intelligence

### What the next slice should know
- DeployResult.phase field tracks exactly where failures occur (bootstrap, runtime_create, polling, completed)
- Runtime rollback is automatic on failure but only deletes the runtime — secret and role are kept for troubleshooting
- Bedrock runtime takes 2-5 minutes typically to reach READY; polling handles this with exponential backoff
- Environment variables include ZSCALER_SECRET_NAME (name only, not full ARN) — this is what the container expects

### What's fragile
- Secret name extraction from ARN uses regex to strip 6-char AWS suffix — if AWS changes ARN format, this breaks
- DEFAULT_IMAGE_URI is a placeholder — real Zscaler image URI needed before production use
- CREATE_FAILED error extraction checks both snake_case and camelCase fields — AWS inconsistency handled but fragile

### Authoritative diagnostics
- Check `DeployResult.phase` first to see where failure occurred
- Inspect `DeployResult.bootstrap_result` for full secret/role details even on runtime failure
- Runtime status: `BedrockRuntime.get_runtime_status(runtime_id)` gives current state without polling
- Error codes with S03-003-* prefix indicate orchestration failures, S03-001-* indicate AWS API failures

### What assumptions changed
- Assumed rollback would clean up everything — actually kept bootstrap resources per R008 deferral and operational wisdom
- Assumed single polling interval — actually implemented exponential backoff for better UX and API rate limit respect
