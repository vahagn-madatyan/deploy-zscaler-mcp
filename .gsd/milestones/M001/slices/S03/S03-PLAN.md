# S03: Bedrock Runtime Deployment

**Goal:** Create Bedrock AgentCore runtime with proper IAM execution role, ECR image reference, and environment configuration
**Demo:** Operator runs `zscaler-mcp-deploy deploy` and receives runtime ID/ARN with connection instructions

## Must-Haves

- `BedrockRuntime` class with lazy boto3 initialization following S02 patterns
- `create_runtime()` method calling AWS `create_agent_runtime` API with proper parameters
- Status polling with configurable timeout (CREATING → READY or CREATE_FAILED)
- Environment variable injection (ZSCALER_SECRET_NAME, TRANSPORT, ENABLE_WRITE_TOOLS)
- Support for write mode flags (--enable-write-tools, --write-tools)
- `DeployOrchestrator` coordinating bootstrap + runtime creation with rollback
- CLI `deploy` command with Rich table output showing runtime details
- Comprehensive unit tests following S02 test patterns (30+ tests)

## Proof Level

- This slice proves: **integration** — integrates S02 outputs (secret ARN, role ARN) with Bedrock AgentCore API
- Real runtime required: **no** — unit tests use mocked boto3 responses
- Human/UAT required: **no** — automated tests sufficient

## Verification

- `poetry run pytest tests/test_bedrock_runtime.py -v` — BedrockRuntime unit tests (25+ tests)
- `poetry run pytest tests/test_deploy.py -v` — DeployOrchestrator unit tests (20+ tests)
- `poetry run pytest tests/test_deploy_integration.py -v` — Integration tests (15+ tests)
- `poetry run zscaler-mcp-deploy deploy --help` — CLI command structure verified

## Observability / Diagnostics

- Runtime signals: Bedrock runtime status (CREATING/READY/CREATE_FAILED), creation timestamp, failure reasons
- Inspection surfaces: `get_agent_runtime()` API, CloudWatch Logs `/aws/bedrock/{runtime-id}`
- Failure visibility: Error codes S03-001-* (Runtime creation), S03-002-* (Status polling), S03-003-* (Deploy orchestrator)
- Redaction constraints: Secret values never logged (only ARNs), credential env vars shown as `<redacted>`

## Integration Closure

- Upstream surfaces consumed: `BootstrapResult.secret_arn`, `BootstrapResult.role_arn` from S02
- New wiring introduced in this slice: `DeployOrchestrator` composes `BootstrapOrchestrator` + `BedrockRuntime`, CLI `deploy` command
- What remains before the milestone is truly usable end-to-end: S04 (Verification & Connection Output) — runtime verification and MCP client instructions

## Tasks

- [x] **T01: BedrockRuntime Class & Runtime Creation** `est:45m`
  - Why: Core AWS resource module for Bedrock AgentCore runtime creation; follows proven S02 patterns
  - Files: `src/zscaler_mcp_deploy/aws/bedrock_runtime.py`, `src/zscaler_mcp_deploy/aws/__init__.py`, `src/zscaler_mcp_deploy/errors.py`, `src/zscaler_mcp_deploy/models.py`
  - Do: Create `BedrockRuntime` class with lazy boto3 initialization; implement `create_runtime()` with environment variable injection; add `BedrockRuntimeError` error class; extend `models.py` with `RuntimeResult`, `RuntimeConfig`, `DeployResult`; default image URI from Zscaler ECR/Marketplace
  - Verify: `poetry run pytest tests/test_bedrock_runtime.py -v` passes
  - Done when: BedrockRuntime creates mocked runtime and returns RuntimeResult with runtime_id, runtime_arn, status

- [x] **T02: Runtime Status Polling & Verification** `est:40m`
  - Why: Bedrock runtime has lifecycle (CREATING → READY/CREATE_FAILED) requiring active polling; isolates timeout/retry complexity
  - Files: `src/zscaler_mcp_deploy/aws/bedrock_runtime.py`, `src/zscaler_mcp_deploy/errors.py`
  - Do: Add `poll_runtime_status()` with configurable timeout (default 10 min); exponential backoff polling; handle CREATE_FAILED with error reason extraction; add `wait_for_ready()` method; update error codes S03-002-* for polling failures
  - Verify: `poetry run pytest tests/test_bedrock_runtime.py::test_poll_runtime_status -v` passes
  - Done when: Polling correctly transitions through CREATING → READY and handles CREATE_FAILED with error reason

- [x] **T03: DeployOrchestrator & CLI Integration** `est:50m`
  - Why: Orchestrates full deploy flow (bootstrap → runtime creation) and exposes to users via CLI
  - Files: `src/zscaler_mcp_deploy/deploy.py`, `src/zscaler_mcp_deploy/cli.py`, `src/zscaler_mcp_deploy/models.py`
  - Do: Create `DeployOrchestrator` class (similar to BootstrapOrchestrator); implement `deploy()` method chaining bootstrap + runtime creation; add rollback on runtime failure; extend CLI with `deploy` command; Rich table output showing runtime ARN, endpoint, status; support --runtime-name, --image-uri, --enable-write-tools flags
  - Verify: `poetry run pytest tests/test_deploy.py -v` passes, `poetry run zscaler-mcp-deploy deploy --help` shows options
  - Done when: DeployOrchestrator returns DeployResult with runtime_id, runtime_arn, endpoint_url; CLI displays formatted output

- [x] **T04: Unit & Integration Tests** `est:45m`
  - Why: Prove correctness of BedrockRuntime, polling, orchestrator, CLI; prevent regressions
  - Files: `tests/test_bedrock_runtime.py`, `tests/test_deploy.py`, `tests/test_deploy_integration.py`
  - Do: Create test_bedrock_runtime.py with 25+ tests (creation, errors, retry logic); create test_deploy.py with 20+ tests (orchestrator phases, rollback); create test_deploy_integration.py with 15+ tests (end-to-end flows, partial failures); mock boto3 bedrock-agent-runtime client responses
  - Verify: `poetry run pytest tests/test_bedrock_runtime.py tests/test_deploy.py tests/test_deploy_integration.py -v` all pass
  - Done when: 60+ new tests pass, coverage >90% for new modules

## Files Likely Touched

- `src/zscaler_mcp_deploy/aws/bedrock_runtime.py` (new)
- `src/zscaler_mcp_deploy/aws/__init__.py` (extend exports)
- `src/zscaler_mcp_deploy/deploy.py` (new)
- `src/zscaler_mcp_deploy/models.py` (extend with RuntimeResult, RuntimeConfig, DeployResult)
- `src/zscaler_mcp_deploy/errors.py` (extend with BedrockRuntimeError)
- `src/zscaler_mcp_deploy/cli.py` (extend with deploy command)
- `tests/test_bedrock_runtime.py` (new)
- `tests/test_deploy.py` (new)
- `tests/test_deploy_integration.py` (new)
