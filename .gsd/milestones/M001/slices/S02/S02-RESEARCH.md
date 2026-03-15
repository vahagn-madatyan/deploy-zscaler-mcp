# S02: Secrets Manager & IAM Bootstrap — Research

**Date:** 2026-03-14

## Summary

Slice S02 implements the AWS resource bootstrap layer for the Zscaler MCP deployment. This slice creates KMS-encrypted Secrets Manager secrets for Zscaler credentials and IAM execution roles for Bedrock AgentCore. 

The primary recommendation is to use boto3's `secretsmanager.create_secret()` with AWS-managed KMS keys (default encryption) for simplicity, while supporting customer-managed KMS keys as an optional advanced configuration. For IAM, we should create a dedicated execution role with a trust policy allowing Bedrock AgentCore service principal (`bedrock.amazonaws.com`) and attach a minimal permissions policy covering Secrets Manager read access and CloudWatch Logs write access.

Key risks center around permission bootstrapping: creating these resources requires specific IAM permissions that may not be present, and the error paths must be crystal clear. The design must also handle the "already exists" case gracefully — reusing existing secrets and roles when appropriate to support idempotent deployments.

## Recommendation

**Approach:** Implement a two-phase bootstrap module:

1. **Secrets Manager Module** (`secrets_manager.py`): Create or reference existing secrets using boto3. Use default AWS-managed KMS encryption (aws/secretsmanager) for simplicity, with optional customer-managed KMS key ARN for enterprise compliance. Store credentials as JSON: `{"username": "...", "password": "...", "api_key": "...", "cloud": "..."}`. Handle `ResourceExistsException` by offering to use the existing secret or abort.

2. **IAM Module** (`iam.py`): Create or reference existing IAM roles. The execution role needs a trust policy allowing `bedrock.amazonaws.com` service principal. Attach an inline policy with minimal permissions: `secretsmanager:GetSecretValue` for the specific secret ARN, and CloudWatch Logs permissions for runtime logging. Handle `EntityAlreadyExistsException` by validating the existing role has compatible trust policy and permissions.

3. **Bootstrap Orchestrator** (`bootstrap.py`): Coordinate secret and role creation with rollback on failure. Return a `BootstrapResult` dataclass containing secret ARN, role ARN, and any created resource IDs for downstream S03 consumption.

**Why this approach:**
- Uses established boto3 patterns from S01
- Follows AWS least-privilege best practices
- Supports both greenfield and brownfield deployments
- Clear error messages for missing permissions (leveraging S01's error system)
- Idempotent by design — running twice shouldn't fail or create duplicates

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| IAM policy document generation | Python `json` module with dict structures | AWS expects specific JSON structure; hand-rolling strings is error-prone |
| Secrets Manager secret naming | Use `/` path separators like `zscaler/mcp/credentials` | AWS Secrets Manager supports path-like naming for organization; follows AWS best practices |
| IAM role trust policy validation | boto3 `iam.get_role()` then parse `AssumeRolePolicyDocument` | Trust policies have specific structure; boto3 returns parsed JSON |
| Resource existence checking | Catch `ClientError` with `EntityAlreadyExistsException` or `ResourceExistsException` | AWS APIs have consistent exception patterns for duplicates |
| Waiting for IAM propagation | Use `time.sleep()` with retry loop (IAM has eventual consistency) | IAM changes propagate asynchronously; immediate use may fail |
| Rollback on partial failure | Track created resources and delete in reverse order | AWS doesn't have transactions across services; manual rollback required |

## Existing Code and Patterns

- `src/zscaler_mcp_deploy/errors.py` — Error hierarchy with `ZscalerMCPError` base class, `AWSPermissionsError`, `AWSCredentialsError`. **Pattern to follow:** All exceptions include `error_code`, `context`, and `fix_commands` for actionable errors.
- `src/zscaler_mcp_deploy/validators/aws.py` — `AWSSessionValidator` with boto3 session management. **Pattern to follow:** Store session as instance variable, lazy-initialize in methods. Uses `botocore.exceptions` for specific error handling.
- `src/zscaler_mcp_deploy/validators/iam.py` — `IAMPermissionValidator` with practical permission checking. **Pattern to follow:** Attempt actual API calls and catch `ClientError` with specific error codes. Generates policy documents programmatically.
- `src/zscaler_mcp_deploy/cli.py` — Typer CLI with Rich console output. **Pattern to follow:** Use `typer.Option()` for flags, `Console()` from Rich for formatted output.
- `tests/test_aws_validation.py` — Mock-based testing with `@patch('boto3.Session')`. **Pattern to follow:** Mock boto3 clients, set up return values, verify calls.

## Constraints

- **IAM eventual consistency:** IAM roles and policies may take a few seconds to propagate. Cannot immediately use a created role for Bedrock deployment — must implement wait/retry logic.
- **Secret naming:** AWS Secrets Manager secret names must be ASCII letters, digits, or the characters `/_+=.@-` and cannot start with `aws-` prefix. Maximum 512 characters.
- **Role name limits:** IAM role names maximum 64 characters. Must be unique within AWS account.
- **Permission boundaries:** If the operator has a permissions boundary set, creating IAM roles may fail even with `iam:CreateRole` permission. Error messages must detect and explain this.
- **KMS key access:** Using a customer-managed KMS key requires the operator to have `kms:GenerateDataKey` and `kms:Decrypt` permissions on that key. Must validate this before attempting secret creation.
- **Cross-service dependencies:** Secrets Manager secret must exist before IAM role can reference it in policy (though can use wildcard ARN patterns).

## Common Pitfalls

- **Trust policy mismatch** — Bedrock AgentCore requires specific service principal (`bedrock.amazonaws.com`). Using wrong principal like `lambda.amazonaws.com` will cause runtime failures. **How to avoid:** Hardcode the correct principal, document it clearly.

- **IAM propagation delays** — Creating a role then immediately trying to use it for Bedrock runtime creation often fails with "role not found" or "role cannot be assumed." **How to avoid:** Implement 10-15 second wait with exponential backoff retry after IAM role creation.

- **Secret ARN vs Name confusion** — Some AWS APIs want the secret ARN, others want the secret name. **How to avoid:** Always store and pass ARNs internally, convert to name only when required by specific API.

- **KMS key policy restrictions** — If using customer-managed KMS keys, the key policy must allow the Secrets Manager service to use the key. **How to avoid:** Default to AWS-managed keys (`aws/secretsmanager`) unless explicitly specified.

- **Race conditions in concurrent deployments** — Multiple concurrent deployments could collide on secret/role names. **How to avoid:** Use deterministic naming with user-specified prefix, handle `EntityAlreadyExistsException` gracefully.

- **Orphaned resources on failure** — Partial bootstrap (secret created, role failed) leaves resources behind. **How to avoid:** Track created resources, implement rollback method that deletes in reverse order.

## Open Risks

- **AWS permission gaps:** The operator may have permissions to deploy Bedrock runtimes but not create IAM roles or Secrets Manager secrets. This is a common enterprise scenario where IAM is centralized. **Mitigation:** Clear error messages with exact IAM policy needed, suggestion to have admin create resources first.

- **KMS key policy complexity:** Customer-managed KMS keys often have restrictive key policies that don't allow Secrets Manager access. **Mitigation:** Default to AWS-managed keys, provide troubleshooting guidance for KMS errors.

- **IAM role name collisions:** In shared AWS accounts, `zscaler-mcp-execution-role` may already exist with different trust policy. **Mitigation:** Support custom role name prefix, validate existing role compatibility before reuse.

- **Secrets Manager VPC endpoint issues:** In VPC-isolated environments, Secrets Manager requires VPC endpoints. **Mitigation:** Document this requirement, detect connectivity issues in error handling.

- **Bedrock AgentCore service availability:** The service principal or required permissions may change as Bedrock AgentCore evolves. **Mitigation:** Stay current with AWS documentation, make trust policy configurable if needed.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| AWS Boto3 | Built-in (already used in S01) | Already installed |
| AWS IAM | Built-in (already used in S01) | Already installed |
| AWS Secrets Manager | Built-in (already used in S01) | Already installed |

No additional skills required — boto3 patterns established in S01 are sufficient.

## Sources

- **AWS Secrets Manager create_secret API** — boto3 supports KMS encryption, tagging, and automatic versioning. Source: [Boto3 SecretsManager Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/secretsmanager/client/create_secret)

- **IAM create_role API** — Requires `AssumeRolePolicyDocument` as JSON string, supports tags and max session duration. Source: [Boto3 IAM Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam/client/create_role)

- **Bedrock AgentCore IAM requirements** — Execution role needs `bedrock.amazonaws.com` trust principal with `sts:AssumeRole` action. Source: S01 IAM validator research and `zscaler-mcp-remote-final.md` architecture document.

- **Zscaler credential format** — Credentials validated in S01: email username, 32-char hex API key. Stored as JSON in Secrets Manager. Source: `src/zscaler_mcp_deploy/validators/zscaler.py`

- **S01 forward intelligence** — Pre-flight validation provides AWS region, permissions check. S02 should fail fast if `secretsmanager:CreateSecret` or `iam:CreateRole` permissions missing. Source: `.gsd/milestones/M001/slices/S01/S01-SUMMARY.md`

---

## Implementation Notes for S02 Tasks

### S02-T01: Secrets Manager Module
- Create `src/zscaler_mcp_deploy/aws/secrets_manager.py`
- Function: `create_or_use_secret(name, credentials, kms_key_id=None, region=None)`
- Returns: `SecretResult` dataclass with ARN, name, version_id
- Handle `ResourceExistsException`: check if existing secret has compatible structure, prompt to use or abort
- Use default KMS key if `kms_key_id` is None

### S02-T02: IAM Role Module
- Create `src/zscaler_mcp_deploy/aws/iam.py`
- Function: `create_or_use_execution_role(name, secret_arn, region=None)`
- Returns: `RoleResult` dataclass with ARN, name, role_id
- Trust policy: `bedrock.amazonaws.com` service principal
- Inline policy: `secretsmanager:GetSecretValue` for specific secret, CloudWatch Logs permissions
- Handle `EntityAlreadyExistsException`: validate trust policy compatibility, prompt to use or abort
- Implement 15-second wait after creation for IAM propagation

### S02-T03: Bootstrap Orchestrator
- Create `src/zscaler_mcp_deploy/bootstrap.py`
- Function: `bootstrap_resources(config)` that orchestrates secret → role creation
- Returns: `BootstrapResult` with both ARNs
- Implement rollback: track created resources, delete on failure
- Integration with S01 preflight: check for required permissions before attempting creation

### S02-T04: CLI Integration
- Extend CLI with `bootstrap` command
- Options: `--secret-name`, `--role-name`, `--kms-key-id`, `--use-existing`
- Output: Rich table showing created/reused resources with ARNs
- Error handling: Use S01 error patterns with specific fix commands

### S02-T05: Testing
- Mock-based unit tests for secrets_manager, iam, bootstrap modules
- Test coverage: create flow, reuse flow, error handling, rollback
- Target: 40+ new tests following S01 patterns
