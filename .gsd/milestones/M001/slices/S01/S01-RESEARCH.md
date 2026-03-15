# S01: Preflight & Validation Engine — Research

**Date:** 2026-03-14

## Summary

Slice S01 establishes the foundation of the Zscaler MCP Deploy CLI by building a strict preflight validation engine. This slice must validate AWS configuration (credentials, region, permissions), Zscaler credentials (format and optionally live validation), and fail fast with actionable error messages before any AWS resources are created. The research confirms AWS Bedrock AgentCore requires specific IAM permissions across multiple services (bedrock-agent-core, iam, secretsmanager, ecr, cloudwatch), and Zscaler credentials follow OneAPI OAuth 2.0 format. The preflight engine must use `boto3` for AWS validation and implement format validators for Zscaler credentials without requiring production dependencies.

The CLI framework choice is between **Typer** (modern, Pydantic-native, async-friendly) and **Click** (battle-tested, AWS CLI uses it). Given the need for interactive prompts and rich output, Typer with `rich` and `questionary` provides the better UX. For AWS permission validation, the approach is to use IAM's `simulate_principal_policy` rather than trial-and-error API calls — this validates permissions without side effects.

## Recommendation

**Use Typer + Rich + boto3 for the CLI framework**, implementing a three-phase preflight validator:

1. **Phase 1: AWS Session Validation** — Verify credentials are configured and can create a boto3 session
2. **Phase 2: Permission Simulation** — Use `iam.simulate_principal_policy` to check required permissions without making actual API calls
3. **Phase 3: Zscaler Credential Validation** — Validate format (client_id, client_secret, cloud) and optionally perform a live token introspection

This approach catches 90%+ of deployment failures before any AWS resources are touched. The error messages must include exact IAM policy snippets the operator can attach to their role/user.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| CLI framework | Typer (or Click) | Automatic help generation, type validation, shell completion |
| Interactive prompts | questionary | Cross-platform, handles arrow keys, validation, confirmation |
| Rich terminal output | rich | Tables, spinners, progress bars, syntax highlighting |
| AWS SDK | boto3 | Official SDK, handles credential chain, retries, pagination |
| AWS permission check | iam.simulate_principal_policy | No side effects, tests permissions without making changes |
| Zscaler API client | zscaler-sdk-python | Existing package for credential validation (optional) |
| Configuration | pydantic-settings | Type-safe env var and config file handling |
| HTTP requests | httpx | Async-capable, modern alternative to requests |

## Existing Code and Patterns

No existing codebase for this project. The slice creates the foundation. Key patterns to establish:

- **`src/zscaler_mcp_deploy/`** — Main package directory
- **`src/zscaler_mcp_deploy/preflight.py`** — Core preflight engine with `PreflightResult` dataclass
- **`src/zscaler_mcp_deploy/validators.py`** — AWS and Zscaler validators
- **`src/zscaler_mcp_deploy/cli.py`** — Typer entry point with interactive prompts
- **`src/zscaler_mcp_deploy/errors.py`** — Structured error types with fix instructions

### Validation Patterns from Research

**AWS Permission Validation Strategy:**
```python
# Use simulate_principal_policy for zero-side-effect validation
iam.simulate_principal_policy(
    PolicySourceArn=user_arn,
    ActionNames=[
        "bedrock-agent-core:CreateAgentRuntime",
        "iam:CreateRole",
        "secretsmanager:CreateSecret",
    ],
    ResourceArns=["*"]  # Check against all resources
)
```

**Zscaler Credential Format:**
- `ZSCALER_CLIENT_ID`: OAuth client ID from ZIdentity
- `ZSCALER_CLIENT_SECRET`: OAuth client secret
- `ZSCALER_CLOUD`: One of `zscaler`, `zscaler-one`, `zscaler-two`, `zscaler-three`
- Optional: `ZSCALER_VANITY_DOMAIN` for custom domains

**Required AWS Permissions (from Bedrock AgentCore docs):**

| Service | Actions | Purpose |
|---------|---------|---------|
| bedrock-agent-core | CreateAgentRuntime, GetAgentRuntime, DeleteAgentRuntime | Core runtime operations |
| iam | CreateRole, AttachRolePolicy, PassRole | Execution role bootstrap |
| secretsmanager | CreateSecret, PutSecretValue, GetSecretValue | Credential storage |
| ecr | GetAuthorizationToken, BatchCheckLayerAvailability | Image pull access |
| cloudwatch | CreateLogGroup, PutLogEvents, DescribeLogStreams | Runtime verification |
| kms | GenerateDataKey, Decrypt | Secret encryption (if using CMK) |

## Constraints

- **Python 3.11+** — Aligns with Zscaler MCP server requirements
- **AWS region availability** — Bedrock AgentCore not available in all regions (typically us-east-1, us-west-2, eu-west-1 initially)
- **Credential chain order** — Must respect standard AWS credential precedence: env vars → ~/.aws/credentials → IAM role
- **No hardcoded credentials** — All validation must work without persisting credentials to disk
- **Strict validation failures** — Any missing permission or invalid config must halt immediately with fix instructions
- **Zscaler credential validation limits** — Format check is reliable; live validation requires network and valid credentials

## Common Pitfalls

- **AWS STS GetCallerIdentity succeeds but permissions are missing** — Many operators have valid credentials but lack specific IAM permissions. Always use `simulate_principal_policy`, not just STS identity check.

- **Region mismatch** — Bedrock AgentCore might not be available in the configured default region. Must explicitly validate region support before attempting deployment.

- **IAM eventual consistency** — After creating an IAM role, there's a propagation delay before it can be used. Preflight can't catch this, but S02 must handle retry logic.

- **Zscaler cloud variants** — Zscaler has multiple cloud deployments (zscaler, zscaler-one, zscaler-two, zscaler-three). Invalid cloud selection causes auth failures that look like credential problems.

- **Secrets Manager cross-region** — Secrets are region-specific. Must validate the secret region matches the deployment region.

- **AssumeRole chains** — Operators using `AWS_PROFILE` with role assumption need special handling for permission simulation (must simulate the assumed role, not the base identity).

## Open Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Bedrock AgentCore region expansion | Medium | Maintain a configurable allowlist of regions, validate at runtime |
| AWS API changes | Low | Pin boto3 version, monitor AWS announcements |
| Zscaler API validation network failures | Low | Make live credential check optional with `--skip-zscaler-check` flag |
| IAM permission simulation false negatives | Medium | Document known edge cases, provide `--force` override |
| Corporate proxy MITM | Medium | Support `AWS_CA_BUNDLE` env var, document proxy config |
| MFA-required AWS sessions | Medium | Detect MFA requirement, prompt for token if needed |

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| boto3 (AWS SDK) | Context7 library `/websites/boto3_amazonaws_v1_api` | Available |
| AWS IAM | None found | Use boto3 simulate_principal_policy |
| Typer CLI | None found | Standard library, no skill needed |
| Zscaler SDK | None found | Use format validation only |

## Sources

- **AWS Bedrock AgentCore boto3 API** — `create_agent_runtime`, `get_agent_runtime`, `delete_agent_runtime` operations (source: boto3 documentation via Context7)
- **Zscaler MCP Server Architecture** — Security model (9-layer defense), credential handling, OneAPI OAuth flow (source: `zscaler-mcp-remote-final.md`)
- **AWS Permission Model** — IAM policy simulation for preflight validation (source: AWS IAM documentation, standard practice)
- **Remote Deployment Research** — Platform comparison, credential storage patterns (source: `compass_artifact_wf-0296d07b-98b3-4c4f-8294-b3133279abd4_text_markdown.md`)
- **MCP Protocol Security** — OAuth 2.1 + PKCE requirements, Origin validation (source: `compass_artifact_wf-3b24c119-3829-4e91-b93d-3822286db279_text_markdown.md`)
- **Milestone Requirements** — R001, R002 strict preflight validation mandate (source: `.gsd/REQUIREMENTS.md`)

## Implementation Notes

### PreflightResult Structure

```python
@dataclass
class PreflightResult:
    aws_region: str
    aws_account_id: str
    aws_identity_arn: str
    permissions_validated: dict[str, bool]  # action -> granted
    zscaler_credentials_valid: bool
    zscaler_cloud: str
    can_proceed: bool
    errors: list[PreflightError]
    warnings: list[str]
```

### Error Message Template

Each preflight failure must include:
1. **What failed** — Clear description
2. **Why it matters** — Impact on deployment
3. **How to fix** — Exact AWS CLI or console steps
4. **IAM policy snippet** — Copy-paste ready JSON

### Verification Plan

- Unit tests with mocked boto3 responses
- Integration test with real AWS credentials (read-only operations only)
- Zscaler credential format validation (no live API calls in unit tests)
- Error message clarity review (ask: would a new AWS user understand this?)
