---
estimated_steps: 8
estimated_files: 5
---

# T01: BedrockRuntime Class & Runtime Creation

**Slice:** S03 — Bedrock Runtime Deployment
**Milestone:** M001

## Description

Create the `BedrockRuntime` class in `aws/bedrock_runtime.py` following the proven lazy initialization pattern from S02's `SecretsManager` and `IAMBootstrap`. This is the foundational AWS resource module that calls the Bedrock AgentCore `create_agent_runtime` API.

The class must:
- Use lazy boto3 client initialization via `@property` pattern
- Accept secret ARN, role ARN, and runtime configuration
- Call `create_agent_runtime` with proper parameters (name, container URI, role ARN, network config, env vars)
- Support write mode flags via environment variables
- Return `RuntimeResult` dataclass with runtime_id, runtime_arn, status

## Steps

1. Extend `models.py` with `RuntimeResult`, `RuntimeConfig`, `DeployResult` dataclasses following existing patterns
2. Extend `errors.py` with `BedrockRuntimeError` class using S03-001-* error code prefix
3. Create `aws/bedrock_runtime.py` with `BedrockRuntime` class
4. Implement lazy boto3 client initialization via `_bedrock_client` @property
5. Implement `create_runtime()` method with all required parameters
6. Add default Zscaler ECR image URI constant (documented as placeholder for official image)
7. Implement environment variable dict construction (ZSCALER_SECRET_NAME, TRANSPORT, ENABLE_WRITE_TOOLS)
8. Extend `aws/__init__.py` to export `BedrockRuntime`

## Must-Haves

- [ ] `BedrockRuntime` class with lazy boto3 initialization following S02 pattern
- [ ] `create_runtime()` method calls boto3 `create_agent_runtime` with correct API structure
- [ ] Environment variables properly injected (ZSCALER_SECRET_NAME as secret name not full ARN)
- [ ] `RuntimeResult` dataclass with runtime_id, runtime_arn, status, created flag
- [ ] `BedrockRuntimeError` with error codes S03-001-* for creation failures
- [ ] Support for optional --image-uri override and --enable-write-tools flag

## Verification

- `poetry run pytest tests/test_bedrock_runtime.py::test_create_runtime_success -xvs` passes
- `poetry run pytest tests/test_bedrock_runtime.py::test_create_runtime_with_write_tools -xvs` passes
- `python -c "from zscaler_mcp_deploy.aws.bedrock_runtime import BedrockRuntime; print('Import OK')"` succeeds

## Observability Impact

- Signals added: Runtime creation start/complete/failed with error codes
- How a future agent inspects this: Check RuntimeResult.status and RuntimeResult.error_code
- Failure state exposed: S03-001-* error codes with specific AWS API error details

## Inputs

- `src/zscaler_mcp_deploy/aws/iam_bootstrap.py` — Pattern to follow for lazy boto3 initialization
- `src/zscaler_mcp_deploy/aws/secrets_manager.py` — Pattern to follow for idempotent operations
- `src/zscaler_mcp_deploy/models.py` — Extend with RuntimeResult, RuntimeConfig, DeployResult
- `src/zscaler_mcp_deploy/errors.py` — Extend with BedrockRuntimeError

## Expected Output

- `src/zscaler_mcp_deploy/aws/bedrock_runtime.py` — BedrockRuntime class with create_runtime method (~300 lines)
- `src/zscaler_mcp_deploy/models.py` — Extended with RuntimeResult, RuntimeConfig, DeployResult
- `src/zscaler_mcp_deploy/errors.py` — Extended with BedrockRuntimeError class
- `src/zscaler_mcp_deploy/aws/__init__.py` — Exports BedrockRuntime
