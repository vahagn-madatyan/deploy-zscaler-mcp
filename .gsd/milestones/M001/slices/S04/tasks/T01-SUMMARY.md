---
id: T01
parent: S04
milestone: M001
provides:
  - RuntimeVerifier class for CloudWatch-based runtime health verification
  - VerificationResult/VerificationConfig models and VerificationStatus enum
  - CloudWatchError and VerificationError exception classes
  - Exponential backoff polling for log stream availability
  - Pattern matching for health indicators in CloudWatch logs
key_files:
  - src/zscaler_mcp_deploy/aws/cloudwatch_verifier.py
  - src/zscaler_mcp_deploy/models.py
  - src/zscaler_mcp_deploy/errors.py
  - src/zscaler_mcp_deploy/aws/__init__.py
  - tests/test_cloudwatch_verifier.py
key_decisions:
  - Used case-insensitive partial pattern matching for health indicators to catch variations like "Credential retrieved" and "credential"
  - Implemented log evidence as pattern indicators only ("matched_pattern:credential") not full log messages for privacy/security
  - HEALTHY threshold set at >=3 matched patterns, UNHEALTHY at 1-2 patterns, PENDING at 0 patterns with events present
  - Exponential backoff: 2s initial → 10s max with 2x factor, matching slice S04 requirement of 2s → 10s range
  - Error codes follow established S04-001-* (CloudWatch API) and S04-002-* (verification logic) conventions
patterns_established:
  - Lazy boto3 client initialization via @property pattern consistent with BedrockRuntime
  - Phase tracking (log_group_discovery → stream_discovery → event_fetching → pattern_matching) for diagnostic context
  - Structured error handling with error_code, phase, and context for traceability
observability_surfaces:
  - VerificationResult.status enum (HEALTHY/UNHEALTHY/PENDING/ERROR)
  - VerificationResult.matched_patterns list showing which health indicators were found
  - VerificationResult.log_evidence dict mapping stream names to pattern match indicators
  - VerificationResult.phase showing where failures occurred
  - VerificationResult.verification_duration_ms for timing analysis
duration: ~45 minutes
verification_result: passed
completed_at: 2026-03-14
blocker_discovered: false
---

# T01: CloudWatch Runtime Verifier

**Implemented RuntimeVerifier class that validates Bedrock AgentCore runtime health via CloudWatch Logs analysis**

## What Happened

Created the core operational verification component that proves deployment actually works — not just that AWS accepted the creation request. The RuntimeVerifier follows the S03 lazy initialization pattern, discovers log groups using `/aws/bedrock/{runtime_id}` naming convention, polls for log streams with exponential backoff (2s → 10s), filters recent log events, and pattern-matches for health indicators.

Key implementation decisions:
- **Log group discovery**: Uses `describe_log_groups` with prefix filter, handles pagination
- **Stream polling**: Exponential backoff from 2s to 10s with 2-minute timeout default
- **Pattern matching**: Case-insensitive partial matches for health signals ("credential", "retrieved", "MCP server", "started", "listening")
- **Privacy-conscious evidence**: Only pattern match indicators stored, never full log messages
- **Health scoring**: >=3 patterns = HEALTHY, 1-2 = UNHEALTHY, 0 = UNHEALTHY with "no indicators" reason

## Verification

```bash
# Task-specific tests
poetry run pytest tests/test_cloudwatch_verifier.py -v
# Result: 37 passed

# Full regression suite
poetry run pytest tests/ --tb=short
# Result: 319 passed (no regressions)
```

All tests cover:
- Log group discovery (found, not found, pagination, API errors)
- Stream discovery (found, empty, API errors)
- Event filtering (time ranges, patterns, API errors)
- Pattern matching (case-insensitive, partial, no matches)
- Polling logic (immediate find, timeout, backoff intervals)
- Full verification flow (healthy, unhealthy, pending, error states)
- Edge cases (empty runtime IDs, multiple streams, unexpected exceptions)

## Diagnostics

Future agents can inspect verification results via:

```python
from zscaler_mcp_deploy.aws.cloudwatch_verifier import RuntimeVerifier

verifier = RuntimeVerifier()
result = verifier.verify_runtime("my-runtime-id", timeout_seconds=120)

# Check operational health
if result.is_healthy():
    print(f"Runtime healthy! Found patterns: {result.matched_patterns}")
else:
    print(f"Status: {result.status.value}")
    print(f"Phase: {result.phase}")
    print(f"Error: {result.error_reason}")
    print(f"Error code: {result.error_code}")

# Inspect evidence (pattern indicators only, no sensitive log content)
for stream, indicators in result.log_evidence.items():
    print(f"Stream {stream}: {indicators}")
```

Error codes for troubleshooting:
- `S04-001-*`: CloudWatch API failures (AccessDeniedException, ResourceNotFoundException, etc.)
- `S04-002-001`: Timeout waiting for log streams
- `S04-002-004`: Unexpected exception during verification

## Deviations

None. Implementation followed the task plan exactly.

## Known Issues

None. All 37 tests pass and full regression suite (319 tests) passes.

## Files Created/Modified

- `src/zscaler_mcp_deploy/aws/cloudwatch_verifier.py` — RuntimeVerifier class (~270 lines) with lazy boto3 init, log group/stream discovery, event filtering, pattern matching, exponential backoff polling
- `src/zscaler_mcp_deploy/models.py` — Added VerificationStatus enum, VerificationConfig dataclass, VerificationResult dataclass with to_dict(), is_healthy(), has_errors() helpers
- `src/zscaler_mcp_deploy/errors.py` — Added CloudWatchError (S04-001-*) and VerificationError (S04-002-*) exception classes with phase tracking
- `src/zscaler_mcp_deploy/aws/__init__.py` — Exported RuntimeVerifier class
- `tests/test_cloudwatch_verifier.py` — 37 comprehensive unit tests covering all methods, error paths, edge cases, and integration scenarios
