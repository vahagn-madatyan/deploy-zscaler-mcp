# S04: Verification & Connection Output

**Goal:** Verify deployed runtime health via CloudWatch logs and output copy-paste-ready MCP client connection instructions
**Demo:** Run `zscaler-mcp-deploy deploy` and see verification status, CloudWatch log evidence, and formatted connection config for Claude Desktop/Cursor

## Must-Haves

- CloudWatch log stream discovery and event filtering for runtime health signals
- Pattern matching for credential injection success and MCP server initialization
- Exponential backoff polling for log availability (handles 30-60s container startup delay)
- MCP client config generation for Claude Desktop (stdio transport)
- MCP client config generation for Cursor (stdio transport)
- Cross-platform config file path resolution (macOS, Linux, Windows)
- CLI integration showing verification status with Rich panels
- Error handling with S04-specific error codes (S04-001-*, S04-002-*, S04-003-*)
- 40+ unit tests covering CloudWatch API mocking, pattern matching, and formatter output

## Proof Level

- This slice proves: operational verification (logs prove runtime health, not just AWS status)
- Real runtime required: no (tests use mocked CloudWatch)
- Human/UAT required: no (automated test coverage sufficient)

## Verification

- `poetry run pytest tests/test_cloudwatch_verifier.py -v` — 25+ tests for RuntimeVerifier
- `poetry run pytest tests/test_connection_formatter.py -v` — 15+ tests for ConnectionFormatter
- `poetry run pytest tests/test_verification_integration.py -v` — Integration tests for full verification flow
- `poetry run pytest tests/ --tb=short` — Full suite (300+ tests expected, no regressions)

## Observability / Diagnostics

- Runtime signals: CloudWatch log events from `/aws/bedrock/{runtime_id}` log group, pattern matches for "credential retrieved", "MCP server started", "listening"
- Inspection surfaces: `RuntimeVerifier.verify_runtime()` returns `VerificationResult` with status, matched_patterns, error_reason, and log_evidence
- Failure visibility: VerificationResult.status enum (HEALTHY, UNHEALTHY, PENDING, ERROR), phase tracking (stream_discovery → event_fetching → pattern_matching), error codes with remediation guidance
- Redaction constraints: Log message content never displayed to user (pattern match only), only status and evidence indicators shown

## Integration Closure

- Upstream surfaces consumed: DeployResult (runtime_id, runtime_arn, endpoint_url) from S03 deploy command; AWS session from S01 preflight
- New wiring introduced in this slice: Verification step added to deploy command success path; ConnectionFormatter generates MCP client configs; Final CLI output shows Rich table with runtime ID, verification status, and connection instructions
- What remains before the milestone is truly usable end-to-end: S05 documentation polish and first-run README

## Tasks

- [x] **T01: CloudWatch Runtime Verifier** `est:45m`
  - Why: Implements R005 runtime verification via CloudWatch logs — the core operational proof that deployment actually works
  - Files: `src/zscaler_mcp_deploy/aws/cloudwatch_verifier.py`, `src/zscaler_mcp_deploy/models.py`, `src/zscaler_mcp_deploy/errors.py`, `tests/test_cloudwatch_verifier.py`
  - Do: Create RuntimeVerifier class with lazy boto3 logs client initialization; implement verify_runtime() with exponential backoff for log stream availability; use describe_log_streams and filter_log_events to find health indicators; pattern match for credential success and MCP initialization; return VerificationResult dataclass with status and evidence; add S04-001-* error codes for CloudWatch issues; follow S03 patterns for consistency
  - Verify: `poetry run pytest tests/test_cloudwatch_verifier.py -v` passes with 25+ tests
  - Done when: RuntimeVerifier can discover log streams, filter events, match health patterns, and return structured result with timeout handling

- [x] **T02: Connection Formatter** `est:35m`
  - Why: Implements R006 connection instructions — generates copy-paste-ready MCP client configs for Claude Desktop and Cursor
  - Files: `src/zscaler_mcp_deploy/output/connection_formatter.py`, `src/zscaler_mcp_deploy/models.py`, `src/zscaler_mcp_deploy/messages.py`, `tests/test_connection_formatter.py`
  - Do: Create ConnectionFormatter class with cross-platform config path resolution; implement format_claude_desktop_config() for stdio transport; implement format_cursor_config() for stdio transport; handle existing config file merging (don't overwrite); add S04-003-* error codes for formatter issues; update messages.py with connection help text; follow existing output patterns from S03
  - Verify: `poetry run pytest tests/test_connection_formatter.py -v` passes with 15+ tests
  - Done when: ConnectionFormatter generates valid MCP JSON configs for both clients with proper stdio command/args structure

- [x] **T03: CLI Verification Integration** `est:40m`
  - Why: Wires verification and connection output into the deploy command — the user-facing completion of the deployment pipeline
  - Files: `src/zscaler_mcp_deploy/cli.py`, `src/zscaler_mcp_deploy/deploy.py`, `tests/test_verification_integration.py`
  - Do: Extend deploy command to call RuntimeVerifier.verify_runtime() after successful DeployResult; display verification status with Rich panels (success/warning/error styling); output connection instructions with file paths and copy-paste config; add --skip-verification flag for cases where log format is unstable; handle verification failures gracefully (show error, still output connection info); update DeployResult to include verification status; exit codes: 0=verified+ready, 1=deployed+verification-failed, 2=error
  - Verify: `poetry run pytest tests/test_verification_integration.py -v` passes with 20+ integration tests; `poetry run zscaler-mcp-deploy deploy --help` shows --skip-verification flag
  - Done when: Deploy command shows verification status and connection instructions in final output

## Files Likely Touched

- `src/zscaler_mcp_deploy/aws/cloudwatch_verifier.py` — RuntimeVerifier class (NEW)
- `src/zscaler_mcp_deploy/output/__init__.py` — Package init (NEW)
- `src/zscaler_mcp_deploy/output/connection_formatter.py` — ConnectionFormatter class (NEW)
- `src/zscaler_mcp_deploy/models.py` — VerificationResult, VerificationConfig dataclasses
- `src/zscaler_mcp_deploy/errors.py` — VerificationError, CloudWatchError, FormatterError
- `src/zscaler_mcp_deploy/messages.py` — Connection help text
- `src/zscaler_mcp_deploy/cli.py` — Deploy command extension with verification and output
- `src/zscaler_mcp_deploy/deploy.py` — DeployOrchestrator extension for verification step
- `tests/test_cloudwatch_verifier.py` — RuntimeVerifier unit tests (NEW)
- `tests/test_connection_formatter.py` — ConnectionFormatter unit tests (NEW)
- `tests/test_verification_integration.py` — End-to-end verification tests (NEW)
