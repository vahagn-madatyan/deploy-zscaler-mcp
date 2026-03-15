# S02: Secrets Manager & IAM Bootstrap

**Goal:** Create KMS-encrypted Secrets Manager secrets for Zscaler credentials and IAM execution roles for Bedrock AgentCore, with idempotent resource handling and clear error paths.
**Demo:** Operator runs `zscaler-mcp-deploy bootstrap` and sees created/reused secret ARN and role ARN in a formatted table, with clear status for each resource.

## Must-Haves

- Create or reuse Secrets Manager secrets with KMS encryption
- Create or reuse IAM execution roles with Bedrock trust policy
- Handle resource existence gracefully (idempotent operations)
- Implement rollback for partial failures
- Clear error messages with specific IAM policy fix instructions
- 15-second IAM propagation wait after role creation

## Proof Level

- This slice proves: integration
- Real runtime required: no (mock-based testing per S01 patterns)
- Human/UAT required: no

## Verification

- `poetry run pytest tests/test_secrets_manager.py -v` — Secrets Manager module tests (15+ tests)
- `poetry run pytest tests/test_iam_bootstrap.py -v` — IAM bootstrap module tests (15+ tests)
- `poetry run pytest tests/test_bootstrap.py -v` — Bootstrap orchestrator tests (15+ tests)
- `poetry run zscaler-mcp-deploy bootstrap --help` — CLI shows bootstrap command options
- `poetry run pytest tests/ --tb=short` — All tests pass (target: 40+ new tests)

## Observability / Diagnostics

- Runtime signals: Structured logs for secret creation, IAM role creation, and rollback operations
- Inspection surfaces: CLI bootstrap command outputs Rich table with resource ARNs and status
- Failure visibility: Specific error codes (S02-001 for secret errors, S02-002 for IAM errors, S02-003 for rollback errors) with full context
- Redaction constraints: Secret values never logged; only ARNs and names visible

## Integration Closure

- Upstream surfaces consumed: S01 preflight validators (AWS session, IAM permissions, Zscaler credentials)
- New wiring introduced in this slice:
  - `src/zscaler_mcp_deploy/aws/secrets_manager.py` — New AWS resource module
  - `src/zscaler_mcp_deploy/aws/iam_bootstrap.py` — New IAM resource module (renamed from iam.py to avoid conflict with validators/iam.py)
  - `src/zscaler_mcp_deploy/bootstrap.py` — New orchestrator module
  - CLI `bootstrap` command in `cli.py`
- What remains before the milestone is truly usable end-to-end: S03 (Bedrock runtime deployment) will consume the secret ARN and role ARN produced by this slice

## Tasks

- [x] **T01: Secrets Manager Module** `est:45m`
  - Why: S02 needs to create KMS-encrypted secrets for Zscaler credentials. This is the simpler of the two AWS resources and establishes boto3 patterns for the slice.
  - Files: `src/zscaler_mcp_deploy/aws/__init__.py`, `src/zscaler_mcp_deploy/aws/secrets_manager.py`, `tests/test_secrets_manager.py`
  - Do: Create SecretsManager class with `create_or_use_secret()` method. Handle `ResourceExistsException` by checking secret compatibility. Use default AWS-managed KMS key. Store credentials as JSON. Return `SecretResult` dataclass with ARN, name, version_id.
  - Verify: `poetry run pytest tests/test_secrets_manager.py -v` passes with 15+ tests covering create, reuse, and error paths
  - Done when: Secrets Manager module passes all tests and handles resource existence gracefully

- [x] **T02: IAM Role Module** `est:60m`
  - Why: Bedrock AgentCore requires a dedicated execution role with specific trust policy and minimal permissions. This is more complex than Secrets Manager due to IAM eventual consistency and policy document generation.
  - Files: `src/zscaler_mcp_deploy/aws/iam_bootstrap.py`, `tests/test_iam_bootstrap.py`
  - Do: Create IAMBootstrap class with `create_or_use_execution_role()` method. Generate trust policy with `bedrock.amazonaws.com` principal. Create inline policy with Secrets Manager read and CloudWatch Logs write permissions. Handle `EntityAlreadyExistsException` by validating existing role compatibility. Implement 15-second wait after creation for IAM propagation.
  - Verify: `poetry run pytest tests/test_iam_bootstrap.py -v` passes with 15+ tests covering trust policy, inline policy, and wait logic
  - Done when: IAM module passes all tests and implements IAM propagation wait

- [x] **T03: Bootstrap Orchestrator** `est:45m`
  - Why: Need to coordinate secret and role creation with rollback on failure. This is the glue that makes S02 a cohesive unit.
  - Files: `src/zscaler_mcp_deploy/bootstrap.py`, `src/zscaler_mcp_deploy/models.py`, `tests/test_bootstrap.py`
  - Do: Create `BootstrapOrchestrator` class with `bootstrap_resources()` method. Track created resources. Implement rollback method that deletes in reverse order on failure. Return `BootstrapResult` dataclass with secret ARN and role ARN. Integrate with S01 preflight validators.
  - Verify: `poetry run pytest tests/test_bootstrap.py -v` passes with 15+ tests covering success path, partial failure, and rollback
  - Done when: Bootstrap orchestrator passes all tests and correctly implements rollback

- [x] **T04: CLI Integration** `est:30m`
  - Why: Operators need a user-friendly command to run the bootstrap process. This wires the orchestrator into the existing CLI.
  - Files: `src/zscaler_mcp_deploy/cli.py`
  - Do: Add `bootstrap` command to CLI with options: `--secret-name`, `--role-name`, `--kms-key-id`, `--use-existing`. Use Rich to display formatted table of created/reused resources. Handle errors using S01 error patterns.
  - Verify: `poetry run zscaler-mcp-deploy bootstrap --help` shows all options; `poetry run pytest tests/test_preflight.py -v` passes (ensures no regression)
  - Done when: CLI bootstrap command works and displays formatted output

- [x] **T05: Integration Tests** `est:30m`
  - Why: Ensure all S02 components work together and meet the target of 40+ new tests.
  - Files: `tests/test_bootstrap_integration.py`
  - Do: Write integration tests that exercise the full bootstrap flow with mocked AWS services. Test error scenarios and verify rollback behavior. Add tests to reach 40+ total new tests for S02.
  - Verify: `poetry run pytest tests/ --tb=short` shows 40+ new tests from S02, all passing
  - Done when: All S02 tests pass and coverage targets are met

## Files Likely Touched

- `src/zscaler_mcp_deploy/aws/__init__.py` (new)
- `src/zscaler_mcp_deploy/aws/secrets_manager.py` (new)
- `src/zscaler_mcp_deploy/aws/iam_bootstrap.py` (new)
- `src/zscaler_mcp_deploy/bootstrap.py` (new)
- `src/zscaler_mcp_deploy/models.py` (new — shared dataclasses)
- `src/zscaler_mcp_deploy/cli.py` (modify — add bootstrap command)
- `tests/test_secrets_manager.py` (new)
- `tests/test_iam_bootstrap.py` (new)
- `tests/test_bootstrap.py` (new)
- `tests/test_bootstrap_integration.py` (new)
