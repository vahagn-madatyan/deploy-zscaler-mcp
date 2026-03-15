---
id: T02
parent: S03
milestone: M001
provides:
  - Runtime status polling with exponential backoff
  - get_runtime_status(), poll_runtime_status(), wait_for_ready() methods
  - BedrockRuntimePollingError with S03-002-* error codes
key_files:
  - src/zscaler_mcp_deploy/aws/bedrock_runtime.py
  - src/zscaler_mcp_deploy/errors.py
  - tests/test_bedrock_runtime.py
key_decisions:
  - Implemented exponential backoff (5s to 30s) to prevent API throttling while providing timely updates
  - poll_runtime_status() accepts configurable timeout (default 600s = 10 minutes)
  - CREATE_FAILED extracts errorCode/errorMessage from AWS response (checking both snake_case and camelCase field names for robustness)
  - Separated polling errors (S03-002-*) from creation errors (S03-001-*)
patterns_established:
  - Polling methods return RuntimeResult with final status
  - Timeout errors include poll_count and elapsed_seconds for diagnostics
  - Convenience wrapper wait_for_ready() with sensible defaults
observability_surfaces:
  - Log signals: "Starting runtime status polling", "Poll N: Runtime X status = Y", "Runtime X is READY", "Runtime X CREATE_FAILED"
  - RuntimeResult contains error_code and error_message for failed runtimes
  - BedrockRuntimePollingError.context includes timeout_seconds, poll_count, elapsed_seconds
duration: ~15 minutes
verification_result: passed
completed_at: 2025-03-14
blocker_discovered: false
---

# T02: Runtime Status Polling & Verification

**Added status polling capabilities to BedrockRuntime class with exponential backoff and proper error handling**

## What Happened

Implemented the async lifecycle polling for AWS Bedrock AgentCore runtimes. After `create_agent_runtime` returns, the runtime is in CREATING status and must be polled until it reaches READY (success) or CREATE_FAILED (failure). This task adds:

1. `get_runtime_status()` — lightweight method to query current status
2. `poll_runtime_status()` — full polling with exponential backoff, timeout handling, and terminal state detection
3. `wait_for_ready()` — convenience wrapper with sensible defaults
4. `BedrockRuntimePollingError` with S03-002-* error codes

Key implementation details:
- Exponential backoff starts at 5s, maxes at 30s, factor of 1.5
- Default timeout is 10 minutes (600s), configurable per call
- CREATE_FAILED extracts `errorCode`/`errorMessage` or `failureCode`/`failureMessage` from AWS response
- Timeout errors include diagnostic context: poll_count, elapsed_seconds

## Verification

All verification tests pass:
- `poetry run pytest tests/test_bedrock_runtime.py::TestPollRuntimeStatus::test_poll_runtime_status_ready -xvs` ✅
- `poetry run pytest tests/test_bedrock_runtime.py::TestPollRuntimeStatus::test_poll_runtime_status_failed -xvs` ✅
- `poetry run pytest tests/test_bedrock_runtime.py::TestPollRuntimeStatus::test_poll_runtime_status_timeout -xvs` ✅

Full test suite: 52 tests pass in test_bedrock_runtime.py

## Diagnostics

**How to inspect runtime polling:**
- Check `RuntimeResult.status` field: "CREATING", "READY", "CREATE_FAILED"
- On CREATE_FAILED, inspect `RuntimeResult.error_code` and `RuntimeResult.error_message`
- Use `BedrockRuntime.poll_runtime_status()` with short timeout for quick status checks

**Log signals:**
- `"Starting runtime status polling for: {runtime_id}"` — Polling initiated
- `"Poll {n}: Runtime {id} status = {status} (elapsed: {elapsed}s)"` — Status transition
- `"Runtime {id} is READY after {elapsed}s ({poll_count} polls)"` — Success
- `"Runtime {id} CREATE_FAILED: {reason}"` — Failure with reason
- `"Runtime polling timeout after {elapsed}s ({poll_count} polls)"` — Timeout

**Error codes:**
- `S03-002-Timeout` — Polling exceeded timeout_seconds
- `S03-002-{AWSCode}` — Status check API errors
- `S03-002-CreateFailed` — Runtime reached CREATE_FAILED state

## Deviations

None

## Known Issues

None

## Files Created/Modified

- `src/zscaler_mcp_deploy/aws/bedrock_runtime.py` — Added get_runtime_status(), poll_runtime_status(), wait_for_ready() methods; updated get_runtime() to extract error fields
- `src/zscaler_mcp_deploy/errors.py` — Added BedrockRuntimePollingError class with S03-002 default error code
- `tests/test_bedrock_runtime.py` — Added TestGetRuntimeStatus, TestPollRuntimeStatus, TestWaitForReady, TestBedrockRuntimePollingError test classes (12 new tests)
