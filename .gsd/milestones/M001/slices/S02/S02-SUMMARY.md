---
id: S02
parent: M001
milestone: M001
provides:
  - SecretsManager class with idempotent create_or_use_secret() method
  - IAMBootstrap class with idempotent create_or_use_execution_role() method
  - BootstrapOrchestrator with automatic rollback on partial failure
  - CLI bootstrap command with Rich table output
  - 117 comprehensive tests across 4 test files
requires:
  - slice: S01
    provides: PreflightResult with validated AWS session, region, and Zscaler credentials
affects:
  - S03 (Bedrock Runtime Deployment — will consume secret ARN and role ARN)
key_files:
  - src/zscaler_mcp_deploy/aws/__init__.py
  - src/zscaler_mcp_deploy/aws/secrets_manager.py
  - src/zscaler_mcp_deploy/aws/iam_bootstrap.py
  - src/zscaler_mcp_deploy/bootstrap.py
  - src/zscaler_mcp_deploy/models.py
  - src/zscaler_mcp_deploy/cli.py
  - tests/test_secrets_manager.py
  - tests/test_iam_bootstrap.py
  - tests/test_bootstrap.py
  - tests/test_bootstrap_integration.py
key_decisions:
  - Named module iam_bootstrap.py (not iam.py) to avoid conflict with validators/iam.py
  - Lazy boto3 initialization pattern for testability with injectable sessions
  - Idempotent operations return Result dataclass with created boolean flag
  - Exponential backoff for IAM propagation wait (1s + 2s + 4s, capped at 15s)
  - AWS-managed KMS key as default with optional customer-managed key support
  - Reverse-order rollback (role first, then secret) to handle dependencies
  - Error codes use S02-001 (Secrets), S02-002 (IAM), S02-003 (Orchestrator) taxonomy
  - JSON secret structure with username, password, api_key, cloud fields
patterns_established:
  - AWS resource modules follow lazy initialization with injectable boto3.Session
  - Orchestrator pattern with injected AWS service dependencies for testability
  - Resource tracking as list of tuples [(resource_type, resource_id)] for rollback ordering
  - Phase-based error tracking (preflight, secret, role, rollback) in BootstrapResult
  - CLI commands prompt for required values with --non-interactive flag for CI/CD
  - Table output uses color coding: green=created, blue=reused, red=failed
observability_surfaces:
  - Structured logging via logging module (operations at INFO, errors at ERROR)
  - BootstrapResult.to_dict() for complete result inspection
  - get_created_resources() method for runtime state check
  - Error codes S02-001-*, S02-002-*, S02-003-* with specific suffixes
  - Secret values never logged (only ARNs and names)
drill_down_paths:
  - .gsd/milestones/M001/slices/S02/tasks/T01-SUMMARY.md
  - .gsd/milestones/M001/slices/S02/tasks/T02-SUMMARY.md
  - .gsd/milestones/M001/slices/S02/tasks/T03-SUMMARY.md
  - .gsd/milestones/M001/slices/S02/tasks/T04-SUMMARY.md
  - .gsd/milestones/M001/slices/S02/tasks/T05-SUMMARY.md
duration: 150m
verification_result: passed
completed_at: 2026-03-14
---

# S02: Secrets Manager & IAM Bootstrap

**Idempotent AWS resource bootstrap with KMS-encrypted secrets, IAM execution roles, and automatic rollback**

## What Happened

Implemented the complete S02 slice delivering AWS Secrets Manager and IAM bootstrap functionality for Zscaler MCP deployment. The slice creates KMS-encrypted secrets for Zscaler credentials and IAM execution roles for Bedrock AgentCore with idempotent operations and automatic rollback on partial failures.

**Secrets Manager (T01):** Built `SecretsManager` class with lazy boto3 initialization for testability. The `create_or_use_secret()` method handles resource existence gracefully by catching `ResourceExistsException`, describing the existing secret, and returning `created=False`. Supports both AWS-managed and customer-managed KMS keys. JSON secret structure stores username, password, api_key, and cloud fields.

**IAM Bootstrap (T02):** Built `IAMBootstrap` class with trust policy generation for `bedrock.amazonaws.com` principal and inline policy for Secrets Manager read and CloudWatch Logs write permissions. Handles `EntityAlreadyExistsException` by validating trust policy compatibility — raises `TrustPolicyMismatchError` if existing role has incompatible trust policy. Implements 15-second IAM propagation wait with exponential backoff (1s + 2s + 4s retries).

**Bootstrap Orchestrator (T03):** Built `BootstrapOrchestrator` that coordinates the three-phase bootstrap process: preflight validation → secret creation → role creation. Tracks created resources and implements transactional rollback in reverse order (role first, then secret) on any failure. Integrates with S01 preflight validators to ensure AWS credentials are valid before resource creation.

**CLI Integration (T04):** Extended CLI with `bootstrap` command supporting all configuration options via flags or interactive prompts. Rich table output shows resource ARNs with color-coded status: green for created, blue for reused, red for failed. Added `--non-interactive` flag for CI/CD automation. Error handling follows S01 patterns with specific error codes and fix commands.

**Integration Tests (T05):** Created comprehensive integration test suite with 21 end-to-end tests exercising full bootstrap flows, partial failures with rollback, error propagation, and resource ordering verification.

## Verification

```bash
# S02-specific tests (117 total)
poetry run pytest tests/test_secrets_manager.py tests/test_iam_bootstrap.py tests/test_bootstrap.py tests/test_bootstrap_integration.py -v
# Result: 117 passed

# Full test suite (no regressions)
poetry run pytest tests/ --tb=short
# Result: 189 passed

# CLI help verification
poetry run zscaler-mcp-deploy bootstrap --help
# Result: Shows all options including --secret-name, --role-name, --kms-key-id, --non-interactive
```

**Test Coverage by Module:**
- `test_secrets_manager.py`: 31 tests (SecretResult, CRUD operations, error handling)
- `test_iam_bootstrap.py`: 39 tests (trust policy, inline policy, propagation wait, error classes)
- `test_bootstrap.py`: 26 tests (orchestrator phases, rollback, resource tracking)
- `test_bootstrap_integration.py`: 21 tests (end-to-end flows, partial failures, edge cases)

## Requirements Advanced

- R003 — AWS Secrets Manager Integration — **Validated**: CLI creates KMS-encrypted secrets with idempotent handling. 31 unit tests + integration coverage prove capability.
- R004 — Runtime Deployment Execution — **Advanced**: IAM execution role creation complete with proper trust policy and permissions. Secret ARN and role ARN ready for S03 consumption.

## Requirements Validated

- R003 — AWS Secrets Manager Integration — CLI creates KMS-encrypted secrets with automatic handling of existing resources. JSON secret structure stores Zscaler credentials securely. Error codes S02-001-* with specific context.

## New Requirements Surfaced

- None

## Requirements Invalidated or Re-scoped

- None

## Deviations

None. Implementation followed slice plan exactly.

## Known Limitations

- **R004 incomplete**: IAM role creation is done, but actual Bedrock AgentCore runtime deployment requires S03. Role ARN and secret ARN are produced and ready for consumption.
- **Manual cleanup**: Rollback handles resources created during failed bootstrap, but no standalone `destroy` command exists yet (deferred to M002 per R008).
- **Single region**: Resources created in single AWS region; cross-region replication not implemented.

## Follow-ups

- S03 will consume secret ARN and role ARN from `BootstrapResult` to create Bedrock AgentCore runtime
- Consider adding secret rotation configuration in future slice
- IAM policy least-privilege review when Bedrock runtime requirements are fully known

## Files Created/Modified

- `src/zscaler_mcp_deploy/aws/__init__.py` — AWS package initialization with exports
- `src/zscaler_mcp_deploy/aws/secrets_manager.py` — SecretsManager class with full CRUD (250 lines)
- `src/zscaler_mcp_deploy/aws/iam_bootstrap.py` — IAMBootstrap class with trust/inline policies (350 lines)
- `src/zscaler_mcp_deploy/bootstrap.py` — BootstrapOrchestrator with rollback logic (280 lines)
- `src/zscaler_mcp_deploy/models.py` — Shared dataclasses (SecretResult, IAMRoleResult, BootstrapResult, BootstrapConfig)
- `src/zscaler_mcp_deploy/cli.py` — Extended with bootstrap command and Rich table output
- `tests/test_secrets_manager.py` — 31 unit tests
- `tests/test_iam_bootstrap.py` — 39 unit tests
- `tests/test_bootstrap.py` — 26 unit tests
- `tests/test_bootstrap_integration.py` — 21 integration tests

## Forward Intelligence

### What the next slice should know
- Secret ARN format: `arn:aws:secretsmanager:{region}:{account}:secret:{name}-{random_suffix}`
- Role ARN format: `arn:aws:iam::{account}:role/{role_name}`
- BootstrapResult provides both ARNs and created/reused flags for S03 consumption
- IAM role trust policy requires `bedrock.amazonaws.com` principal with `sts:AssumeRole`
- Inline policy grants `secretsmanager:GetSecretValue` for specific secret ARN only
- 15-second propagation wait implemented but may need adjustment based on real AWS behavior

### What's fragile
- **IAM eventual consistency**: The 15-second propagation wait is based on AWS documentation but real-world timing may vary. S03 may need retry logic when assuming the role fails initially.
- **Trust policy validation**: Only checks for bedrock.amazonaws.com principal presence; doesn't validate full policy structure. Edge case: additional conditions in trust policy may not be detected.

### Authoritative diagnostics
- Error code prefix indicates failure domain: S02-001 (Secrets Manager), S02-002 (IAM), S02-003 (Orchestrator)
- `BootstrapResult.phase` shows exactly where failure occurred: preflight, secret, role
- `BootstrapResult.resource_ids` lists resources created before failure (for manual cleanup if rollback fails)
- CloudWatch Logs for IAM role: check `/aws/bedrock/` log groups after runtime creation

### What assumptions changed
- None — assumptions from S01 planning held true
