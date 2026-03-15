---
estimated_steps: 7
estimated_files: 3
---

# T02: Runtime Status Polling & Verification

**Slice:** S03 — Bedrock Runtime Deployment
**Milestone:** M001

## Description

Add status polling capabilities to `BedrockRuntime` class. AWS Bedrock AgentCore runtimes have an asynchronous lifecycle: after `create_agent_runtime` returns, the runtime is in CREATING status and must be polled until it reaches READY (success) or CREATE_FAILED (failure). This task implements the polling logic with configurable timeout and proper error handling.

Key insight from research: CREATE_COMPLETE ≠ READY. The creation API returns immediately with CREATING status. Runtime may transition to CREATE_FAILED minutes later. Must poll to terminal state.

## Steps

1. Add `get_runtime_status()` method to query runtime status via `get_agent_runtime` API
2. Implement `poll_runtime_status()` with configurable timeout (default 10 minutes)
3. Add exponential backoff between polls (start with 5s, max 30s)
4. Handle READY status — return success with runtime details
5. Handle CREATE_FAILED status — extract failure reason and raise BedrockRuntimeError
6. Add `wait_for_ready()` convenience method that wraps polling
7. Add error codes S03-002-* for polling-specific failures (timeout, status check errors)

## Must-Haves

- [ ] `poll_runtime_status()` polls until READY or CREATE_FAILED with configurable timeout
- [ ] Exponential backoff prevents API throttling while providing timely updates
- [ ] CREATE_FAILED extracts and reports failure reason from AWS response
- [ ] Timeout after default 10 minutes with clear error message
- [ ] Error codes S03-002-* for timeout and status check failures
- [ ] All polling methods return RuntimeResult with final status

## Verification

- `poetry run pytest tests/test_bedrock_runtime.py::test_poll_runtime_status_ready -xvs` passes
- `poetry run pytest tests/test_bedrock_runtime.py::test_poll_runtime_status_failed -xvs` passes
- `poetry run pytest tests/test_bedrock_runtime.py::test_poll_runtime_status_timeout -xvs` passes

## Observability Impact

- Signals added: Polling start, status transitions, timeout events
- How a future agent inspects this: RuntimeResult contains full polling history if needed
- Failure state exposed: S03-002-Timeout error code with configured timeout value

## Inputs

- `src/zscaler_mcp_deploy/aws/bedrock_runtime.py` — Extend with polling methods
- `src/zscaler_mcp_deploy/errors.py` — Extend with polling-specific error codes
- T01 completed — BedrockRuntime base class exists

## Expected Output

- `src/zscaler_mcp_deploy/aws/bedrock_runtime.py` — Extended with poll_runtime_status, wait_for_ready, get_runtime_status methods
- `src/zscaler_mcp_deploy/errors.py` — Extended with S03-002-* error codes
