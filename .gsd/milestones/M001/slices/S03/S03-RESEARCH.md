# S03: Bedrock Runtime Deployment — Research

**Date:** 2026-03-14

## Summary

Slice S03 implements the core deployment logic for creating AWS Bedrock AgentCore runtimes using the official Zscaler MCP container image. The implementation follows established patterns from S01 (validation) and S02 (AWS resource management) to create a `BedrockRuntime` class that orchestrates runtime creation, status monitoring, and verification.

Key findings from research:
1. **Bedrock AgentCore Control Plane API** provides `create_agent_runtime()` with required parameters: runtime name, ECR container URI, IAM role ARN, network configuration, and protocol configuration
2. **Runtime verification** requires polling `get_agent_runtime()` status (CREATING → READY/CREATE_FAILED) plus CloudWatch Logs inspection for credential injection confirmation
3. **Zscaler container image** can be sourced from AWS Marketplace (preferred) or operator's ECR with the official `zscaler-mcp` image
4. **Existing patterns** from S02's `IAMBootstrap` and `SecretsManager` provide the blueprint: lazy boto3 initialization, idempotent operations, comprehensive error handling with specific error codes

The primary recommendation is to create a `BedrockRuntime` class in `aws/bedrock_runtime.py` following S02's lazy initialization pattern, with `create_or_use_runtime()` method that handles both creation and status polling, returning a `RuntimeResult` dataclass defined in `models.py`.

## Recommendation

Create a new `aws/bedrock_runtime.py` module with:

1. **`BedrockRuntime` class** — Lazy boto3 client initialization following S02's established pattern
2. **`create_runtime()` method** — Primary API accepting runtime name, role ARN, secret ARN, and optional image URI
3. **Default image handling** — Use Zscaler's public ECR image or Marketplace image as default, allow operator override
4. **Environment variable injection** — Pass `ZSCALER_SECRET_NAME` to runtime via `environmentVariables` parameter
5. **Status polling with timeout** — Poll `get_agent_runtime()` with configurable timeout (default 10 minutes)
6. **CloudWatch log verification** — Query `/aws/bedrock/{runtime-id}` log group for startup success/failure patterns

This approach aligns with S02's proven architecture while adding Bedrock-specific lifecycle management. The class should integrate cleanly with `BootstrapResult` (role ARN and secret ARN) from S02.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Bedrock AgentCore API calls | boto3 `bedrock-agentcore-control` client | Official AWS SDK with proper error handling, pagination, waiters |
| Runtime status polling | boto3 waiter pattern or custom exponential backoff | AWS services have eventual consistency; polling is required |
| Log retrieval from CloudWatch | `logs.describe_log_streams()` + `logs.filter_log_events()` | Standard pattern for AWS container runtime verification |
| Error handling with codes | `ZscalerMCPError` hierarchy from `errors.py` | Consistent error categorization and user-facing messages |
| Result dataclasses | `models.py` pattern (SecretResult, IAMRoleResult) | Clean API contracts between components |

## Existing Code and Patterns

- `src/zscaler_mcp_deploy/aws/iam_bootstrap.py` — **Pattern to follow**: Lazy boto3 initialization via `@property` pattern, idempotent `create_or_use_*` methods, comprehensive error handling with `ClientError` catching
- `src/zscaler_mcp_deploy/aws/secrets_manager.py` — **Pattern to follow**: Resource existence handling, exponential backoff for propagation delays
- `src/zscaler_mcp_deploy/models.py` — **Extend**: Add `RuntimeResult`, `RuntimeConfig`, `DeployResult` dataclasses following existing patterns
- `src/zscaler_mcp_deploy/errors.py` — **Extend**: Add `BedrockRuntimeError` class with error codes S03-001-*
- `src/zscaler_mcp_deploy/bootstrap.py` — **Reference**: Orchestrator pattern for coordinating multiple AWS operations with rollback
- `src/zscaler_mcp_deploy/cli.py` — **Extend**: Add `deploy` command following `bootstrap` command structure with Rich table output

## Constraints

- **Bedrock AgentCore availability**: Not available in all AWS regions; must validate region support before deployment (S01 preflight already handles this)
- **IAM propagation delay**: Role created in S02 may not be immediately assumable; S03 may need retry logic if `create_agent_runtime` fails with IAM-related errors
- **Runtime name uniqueness**: AWS Bedrock runtime names must be unique per account/region; need conflict handling
- **Image sourcing decision**: Zscaler's official image location must be determined (Marketplace vs public ECR vs operator's ECR)
- **Write mode flags**: Must support `--enable-write-tools` and `--write-tools` passthrough to runtime environment variables

## Common Pitfalls

- **IAM eventual consistency** — The role ARN from S02 may fail initially when Bedrock tries to assume it. Implement retry with exponential backoff (similar to S02's 15-second wait, but potentially longer for runtime creation). **Avoid**: Single-shot creation without status verification.
- **CREATE_COMPLETE ≠ READY** — `create_agent_runtime` returns immediately with status CREATING. Runtime may transition to CREATE_FAILED minutes later. **Avoid**: Returning success on creation API response; must poll to READY or timeout.
- **Log group delay** — CloudWatch log group `/aws/bedrock/{runtime-id}` may not exist immediately. **Avoid**: Immediate log verification; wait for runtime to reach READY first.
- **Secret ARN format** — Must pass secret name (not full ARN) in `ZSCALER_SECRET_NAME` environment variable for Zscaler MCP server to properly resolve via AWS SDK. **Verify**: Check Zscaler MCP server documentation for expected format.

## Open Risks

- **Zscaler container image location** — Need to confirm official image URI (likely AWS Marketplace or public ECR). Risk: Image may require subscription or authentication. **Mitigation**: Document both Marketplace and ECR-push paths; allow operator override via `--image-uri`.
- **Bedrock AgentCore service quotas** — New AWS accounts may have low or zero quotas for AgentCore runtimes. Risk: Deployment fails with quota exceeded error. **Mitigation**: Add quota check in preflight or catch `ServiceQuotaExceededException` with specific guidance.
- **Network configuration complexity** — PUBLIC mode is simpler but VPC mode may be required for enterprise. Risk: Implementation focused on PUBLIC may not easily extend to VPC. **Mitigation**: Start with PUBLIC, design `networkConfiguration` as parameterized dict for VPC extension.
- **Runtime deletion/recreation** — Updating runtime may require delete+recreate rather than update. Risk: Operator expects update-in-place. **Mitigation**: Document lifecycle behavior; implement idempotent `create_or_use` that checks existing runtime compatibility.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| boto3 | Already available via pip | Installed |
| AWS Bedrock AgentCore | No specific skill found | Use boto3 documentation |

No additional skills required — boto3 SDK provides all necessary Bedrock AgentCore APIs.

## Sources

- **Bedrock AgentCore Control Plane API** — `create_agent_runtime`, `get_agent_runtime`, `list_agent_runtimes` (source: [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agentcore-control/client/create_agent_runtime))
- **Runtime Creation Parameters** — Required: `agentRuntimeName`, `agentRuntimeArtifact.containerConfiguration.containerUri`, `roleArn`, `networkConfiguration.networkMode`; Optional: `protocolConfiguration.serverProtocol`, `environmentVariables`, `tags` (source: Boto3 API reference)
- **Runtime Status Lifecycle** — `CREATING` → `READY` | `CREATE_FAILED` → `DELETING` (source: Boto3 API reference)
- **CloudWatch Logs Integration** — Log group pattern `/aws/bedrock/{runtime-id}`, use `describe_log_streams` and `filter_log_events` for verification (source: Boto3 logs client documentation)
- **Zscaler MCP Server Container Support** — Server supports `--transport streamable-http` and Docker deployment (source: `zscaler-mcp-remote-final.md` research document)
- **Zscaler Enterprise Deployment** — AWS Bedrock AgentCore is the Zscaler-supported enterprise path with IAM + CloudTrail + KMS encryption (source: `zscaler-mcp-remote-final.md`)

## API Details

### Key Bedrock AgentCore API Parameters

```python
# create_agent_runtime request structure
{
    "agentRuntimeName": "zscaler-mcp-runtime",  # Required
    "description": "Zscaler MCP Server on Bedrock AgentCore",
    "agentRuntimeArtifact": {
        "containerConfiguration": {
            "containerUri": "123456789012.dkr.ecr.us-east-1.amazonaws.com/zscaler-mcp:latest"
        }
    },
    "roleArn": "arn:aws:iam::123456789012:role/zscaler-mcp-execution-role",  # From S02
    "networkConfiguration": {
        "networkMode": "PUBLIC"  # or "VPC" with networkModeConfig
    },
    "protocolConfiguration": {
        "serverProtocol": "MCP"  # or "HTTP"
    },
    "environmentVariables": {
        "ZSCALER_SECRET_NAME": "zscaler/mcp/credentials",  # From S02
        "TRANSPORT": "streamable-http",
        "ENABLE_WRITE_TOOLS": "true"  # Optional, based on flags
    },
    "tags": {
        "Project": "ZscalerMCP",
        "ManagedBy": "zscaler-mcp-deploy"
    }
}
```

### Response Structure

```python
{
    "agentRuntimeArn": "arn:aws:bedrock:us-east-1:123456789012:agent-runtime/brt-xxxxxxxxxxxxxxxxx",
    "agentRuntimeId": "brt-xxxxxxxxxxxxxxxxx",
    "agentRuntimeVersion": "1.0",
    "createdAt": datetime(2026, 3, 14, 12, 0, 0),
    "status": "CREATING"  # Poll until READY or CREATE_FAILED
}
```

## Integration Points

### Consumes from S02
- `BootstrapResult.role_arn` — IAM execution role for runtime
- `BootstrapResult.secret_arn` — Secret for ZSCALER_SECRET_NAME env var

### Produces for S04
- `RuntimeResult.runtime_id` — Bedrock runtime ID (e.g., `brt-xxxxxxxxxxxxxxxxx`)
- `RuntimeResult.runtime_arn` — Full ARN for MCP client configuration
- `RuntimeResult.status` — Final status (READY or CREATE_FAILED)
- `RuntimeResult.endpoint_url` — Runtime endpoint for MCP connection

## File Structure Plan

```
src/zscaler_mcp_deploy/
├── aws/
│   ├── __init__.py              # Add BedrockRuntime export
│   ├── bedrock_runtime.py       # NEW: BedrockRuntime class
│   └── ... (existing files)
├── models.py                    # Extend: RuntimeResult, RuntimeConfig
├── errors.py                    # Extend: BedrockRuntimeError
├── deploy.py                    # NEW: DeployOrchestrator (similar to bootstrap.py)
└── cli.py                       # Extend: deploy command
```
