---
estimated_steps: 8
estimated_files: 4
---

# T01: CloudWatch Runtime Verifier

**Slice:** S04 — Verification & Connection Output
**Milestone:** M001

## Description

Implement the RuntimeVerifier class that validates Bedrock AgentCore runtime health via CloudWatch Logs. This is the core operational verification component that proves the deployment actually works — not just that AWS accepted the creation request. The verifier discovers log streams, filters events, and pattern-matches for health indicators like credential injection success and MCP server initialization.

## Steps

1. **Create `aws/cloudwatch_verifier.py`** with RuntimeVerifier class following S03 lazy initialization pattern
2. **Add models** for VerificationResult, VerificationConfig, VerificationStatus enum to `models.py`
3. **Add errors** for CloudWatchError, VerificationError with S04-001-* and S04-002-* codes to `errors.py`
4. **Implement log group discovery** using describe_log_groups with prefix filter for `/aws/bedrock/`
5. **Implement log stream discovery** using describe_log_streams on discovered log group
6. **Implement event filtering** using filter_log_events to fetch recent log entries
7. **Implement pattern matching** for health signals: "credential", "retrieved", "MCP server", "started", "listening"
8. **Implement exponential backoff polling** for log availability (2s → 10s) with 2-minute timeout
9. **Create `tests/test_cloudwatch_verifier.py`** with 25+ unit tests mocking CloudWatch APIs

## Must-Haves

- [ ] RuntimeVerifier class with lazy boto3 logs client initialization
- [ ] verify_runtime(runtime_id: str, timeout_seconds: int = 120) → VerificationResult method
- [ ] Log group discovery via describe_log_groups with `/aws/bedrock/{runtime_id}` pattern
- [ ] Log stream discovery via describe_log_streams
- [ ] Event filtering via filter_log_events with time window
- [ ] Pattern matching for health indicators (case-insensitive, partial matches)
- [ ] Exponential backoff polling for log stream availability
- [ ] VerificationResult with status (HEALTHY, UNHEALTHY, PENDING, ERROR), matched_patterns, error_reason, log_evidence
- [ ] S04-001-* error codes for CloudWatch API failures
- [ ] S04-002-* error codes for pattern matching/verification failures
- [ ] 25+ unit tests with mocked CloudWatch responses

## Verification

- `poetry run pytest tests/test_cloudwatch_verifier.py -v` passes with 25+ tests
- Tests cover: log group discovery, stream discovery, event filtering, pattern matching, timeout handling, error cases
- Mock boto3 CloudWatch Logs client responses for deterministic testing

## Observability Impact

- Signals added/changed: VerificationResult.status shows operational health; matched_patterns list shows which health indicators were found; error_reason provides diagnostic context
- How a future agent inspects this: Call RuntimeVerifier.verify_runtime() and inspect returned VerificationResult; check VerificationResult.log_evidence for raw log indicators
- Failure state exposed: VerificationStatus.ERROR with error_reason describing CloudWatch API failure or timeout; specific error codes (S04-001-001 for log group not found, etc.)

## Inputs

- `src/zscaler_mcp_deploy/aws/bedrock_runtime.py` — Pattern to follow: lazy boto3 initialization via property
- `src/zscaler_mcp_deploy/models.py` — Extend with VerificationResult following BootstrapResult/DeployResult patterns
- `src/zscaler_mcp_deploy/errors.py` — Extend with VerificationError following BedrockRuntimeError pattern
- S03 Research — Log group naming convention `/aws/bedrock/{runtime_id}` from IAM permissions

## Expected Output

- `src/zscaler_mcp_deploy/aws/cloudwatch_verifier.py` — RuntimeVerifier class (~250 lines)
- `tests/test_cloudwatch_verifier.py` — Comprehensive unit tests (~400 lines)
- Updated `src/zscaler_mcp_deploy/models.py` — VerificationResult, VerificationConfig dataclasses
- Updated `src/zscaler_mcp_deploy/errors.py` — CloudWatchError, VerificationError classes
- `src/zscaler_mcp_deploy/aws/__init__.py` — Export RuntimeVerifier and error classes
