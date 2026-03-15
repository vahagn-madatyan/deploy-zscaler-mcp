---
id: T01
parent: S03
milestone: M001
provides:
  - BedrockRuntime class with lazy boto3 initialization
  - RuntimeResult, RuntimeConfig, DeployResult dataclasses
  - BedrockRuntimeError exception class with S03-001-* error codes
  - create_runtime() method calling AWS create_agent_runtime API
  - Environment variable injection (ZSCALER_SECRET_NAME, TRANSPORT, ENABLE_WRITE_TOOLS)
key_files:
  - src/zscaler_mcp_deploy/aws/bedrock_runtime.py
  - src/zscaler_mcp_deploy/models.py
  - src/zscaler_mcp_deploy/errors.py
  - src/zscaler_mcp_deploy/aws/__init__.py
  - tests/test_bedrock_runtime.py
key_decisions:
  - Used SecretsManager/IAMBootstrap lazy initialization pattern with @property for session and client
  - Implemented _extract_secret_name() to strip AWS suffix (6 alphanumeric chars) from secret ARN
  - Added DEFAULT_IMAGE_URI constant as placeholder for official Zscaler ECR image
  - Structured network configuration with empty vpcConfiguration for default networking
  - Error codes follow S03-001-* prefix pattern per slice plan
patterns_established:
  - Lazy boto3 client initialization via _bedrock_client @property
  - Environment variable dict construction with redaction for logging
  - RuntimeResult dataclass with status tracking (CREATING/READY/CREATE_FAILED)
observability_surfaces:
  - RuntimeResult.status field for runtime lifecycle state
  - RuntimeResult.error_code and error_message for failure details
  - BedrockRuntimeError with context containing runtime_name and aws_error_code
  - Logging at INFO level for creation start/complete/failed events
  - Sensitive values (secret ARN details) redacted in logs
---

duration: 35m
verification_result: passed
completed_at: 2024-01-15
blocker_discovered: false
---

# T01: BedrockRuntime Class & Runtime Creation

**Created BedrockRuntime class with lazy boto3 initialization, AWS API integration, and 40 unit tests**

## What Happened

Implemented the foundational Bedrock Runtime module following the proven S02 patterns from SecretsManager and IAMBootstrap. The BedrockRuntime class provides:

1. **Lazy Initialization**: Uses `@property` pattern for boto3 session and bedrock-agent client, caching after first access
2. **Runtime Creation**: Calls AWS `create_agent_runtime` API with proper container configuration including image URI, execution role ARN, environment variables, and network configuration
3. **Secret Name Extraction**: Implemented `_extract_secret_name()` to parse secret ARNs and strip the AWS-added 6-character suffix (e.g., "zscaler-creds-AbCdEf" → "zscaler-creds")
4. **Environment Variables**: Builds environment dict with ZSCALER_SECRET_NAME (name only, not full ARN), TRANSPORT (stdio), and ENABLE_WRITE_TOOLS (conditional)
5. **Error Handling**: BedrockRuntimeError with S03-001-* error codes for AWS API failures

Extended models.py with three new dataclasses:
- **RuntimeConfig**: Configuration container for runtime creation parameters
- **RuntimeResult**: Result container with runtime_id, runtime_arn, status, endpoint_url
- **DeployResult**: Future orchestrator result type (placeholder for T03)

## Verification

All verification checks from task plan passed:

```bash
# Test specific verification cases
poetry run pytest tests/test_bedrock_runtime.py::TestCreateRuntime::test_create_runtime_success -xvs  PASSED
poetry run pytest tests/test_bedrock_runtime.py::TestCreateRuntime::test_create_runtime_with_write_tools -xvs  PASSED
python -c "from zscaler_mcp_deploy.aws.bedrock_runtime import BedrockRuntime; print('Import OK')"  Import OK

# Full test suite
poetry run pytest tests/test_bedrock_runtime.py -v  40 passed
```

Test coverage includes:
- RuntimeResult/RuntimeConfig dataclass tests (6 tests)
- BedrockRuntime initialization and lazy loading (10 tests)
- Secret name extraction from ARNs (5 tests)
- Environment variable construction (3 tests)
- Network configuration building (1 test)
- create_runtime() success and error cases (6 tests)
- get_runtime() and delete_runtime() (3 tests)
- BedrockRuntimeError exception (4 tests)

## Diagnostics

**Inspecting runtime state:**
- Check `RuntimeResult.status` field: "CREATING", "READY", "CREATE_FAILED"
- On failure, inspect `RuntimeResult.error_code` (e.g., "S03-001-AccessDeniedException")
- Use `BedrockRuntime.get_runtime(runtime_id)` to poll current status

**Log signals:**
- "Creating Bedrock runtime: {name}" - Creation initiated
- "Runtime created: {arn} (status: {status})" - Creation succeeded
- "Failed to create runtime: {code} - {message}" - Creation failed

**Error context includes:**
- `runtime_name`: The runtime name that failed
- `aws_error_code`: AWS API error code
- `image_uri`: Container image URI used (for debugging)

## Deviations

None - implementation followed task plan exactly.

## Known Issues

None - all tests pass.

## Files Created/Modified

- `src/zscaler_mcp_deploy/aws/bedrock_runtime.py` — BedrockRuntime class with create_runtime(), get_runtime(), delete_runtime() methods (~270 lines)
- `src/zscaler_mcp_deploy/models.py` — Extended with RuntimeConfig, RuntimeResult, DeployResult dataclasses
- `src/zscaler_mcp_deploy/errors.py` — Extended with BedrockRuntimeError exception class
- `src/zscaler_mcp_deploy/aws/__init__.py` — Exports BedrockRuntime and BedrockRuntimeError
- `tests/test_bedrock_runtime.py` — 40 unit tests covering all functionality
