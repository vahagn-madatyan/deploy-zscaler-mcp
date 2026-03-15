# M001: Bedrock Deploy CLI Foundation

**Vision:** An individual operator runs one command and has a verified, working Zscaler MCP server on AWS Bedrock AgentCore, with strict preflight validation, secure credential handling, and clear connection instructions.

## Success Criteria

- Operator with AWS CLI and Zscaler credentials can run `zscaler-mcp-deploy` and complete deployment without reading AWS docs
- Strict preflight catches missing permissions, invalid credentials, or unsupported regions before any AWS resources are created
- Deployment uses AWS Secrets Manager for credential storage (not env vars)
- Runtime verification proves the deployment actually works (not just CREATE_COMPLETE)
- Operator receives runtime ID/ARN, verification commands, and MCP client connection instructions

## Key Risks / Unknowns

- **AWS permission complexity** — IAM role needs specific permissions across ECR, Secrets Manager, CloudWatch, Bedrock. Preflight must validate precisely.
- **Secrets Manager bootstrap** — Creating secrets and IAM roles requires permissions operator might not have. Need clear error paths.
- **ECR image sourcing** — Marketplace image vs. operator's ECR affects UX complexity significantly.

## Proof Strategy

- AWS permission complexity → retire in S01 by proving preflight catches missing permissions with exact fix instructions
- Secrets Manager bootstrap → retire in S02 by proving secret creation works with proper IAM, or fails clearly with actionable errors
- ECR image sourcing → retire in S02 by documenting both Marketplace (preferred) and ECR-push paths

## Verification Classes

- **Contract verification:** Unit tests for preflight validators, AWS API mocking, Secrets Manager integration tests
- **Integration verification:** Real AWS Bedrock AgentCore deployment to live AWS account
- **Operational verification:** Runtime verification against live CloudWatch logs, MCP client connection test
- **UAT / human verification:** New user follows README and successfully deploys without assistance

## Milestone Definition of Done

This milestone is complete only when all are true:

- All slice deliverables are complete and verified
- CLI successfully deploys to real AWS Bedrock AgentCore in a clean AWS account
- Runtime verification passes against live CloudWatch logs
- A new user can follow documentation and deploy without hitting undocumented issues
- Preflight validation catches all known prerequisite failures before AWS resource creation
- Connection instructions are copy-paste ready for Claude Desktop and Cursor

## Requirement Coverage

- **Covers:** R001, R002, R003, R004, R005, R006
- **Partially covers:** R007 (establishes focus)
- **Leaves for later:** R008, R009 (lifecycle), R010 (non-AWS), R011/R012 (out of scope)
- **Orphan risks:** None

## Slices

- [ ] **S01: Preflight & Validation Engine** `risk:high` `depends:[]`
  > After this: CLI validates AWS permissions, region, Zscaler credentials, and fails fast with exact fix instructions before any deployment attempt.

- [ ] **S02: Secrets Manager & IAM Bootstrap** `risk:high` `depends:[S01]`
  > After this: CLI creates KMS-encrypted Secrets Manager secret and IAM execution role with proper permissions, or uses existing resources.

- [ ] **S03: Bedrock Runtime Deployment** `risk:medium` `depends:[S02]`
  > After this: CLI creates Bedrock AgentCore runtime with proper configuration, using official Zscaler image or operator's ECR.

- [ ] **S04: Verification & Connection Output** `risk:medium` `depends:[S03]`
  > After this: CLI verifies runtime health via CloudWatch logs, confirms credential injection, and outputs runtime ID/ARN with MCP connection instructions.

- [ ] **S05: Documentation & First-Run Polish** `risk:low` `depends:[S04]`
  > After this: README guides new users through install and first deploy, common issues documented, error messages are actionable.

## Boundary Map

### S01 → S02

**Produces:**
- `preflight.py` → `PreflightResult` with validated AWS region, permissions, credentials
- `validators.py` → `AwsPermissionsValidator`, `ZscalerCredentialsValidator`, `RegionValidator`
- Error message templates with exact fix instructions

**Consumes:**
- nothing (first slice)

### S02 → S03

**Produces:**
- `secrets_manager.py` → `create_or_use_secret()` returns secret ARN
- `iam.py` → `create_execution_role()` returns role ARN
- `bootstrap.py` → `BootstrapResult` with secret ARN, role ARN, and resource IDs

**Consumes from S01:**
- Validated AWS region and permissions
- Validated Zscaler credentials (to store in secret)

### S03 → S04

**Produces:**
- `bedrock.py` → `create_agent_runtime()` returns runtime ID/ARN
- `runtime.py` → `RuntimeConfig` with image URI, env vars, resource config
- `deploy.py` → `DeployResult` with runtime ID, ARN, and status

**Consumes from S02:**
- Secret ARN (for ZSCALER_SECRET_NAME env var)
- Role ARN (for execution role)

### S04 → S05

**Produces:**
- `verification.py` → `verify_runtime()` returns verification status and log evidence
- `output.py` → `format_connection_instructions()` returns formatted output
- `cli.py` → Final summary with runtime ID, ARN, verification, and connection steps

**Consumes from S03:**
- Runtime ID and ARN
- Runtime status from AWS APIs

### Cross-slice Contracts

- **AWS region validation:** Must happen in S01, used by all downstream slices
- **Secret naming convention:** `zscaler/mcp/credentials` or user-specified, established in S02
- **IAM role naming:** `zscaler-mcp-execution-role` or user-specified, established in S02
- **Runtime naming:** User-specified with validation, established in S03
- **Write mode flags:** Optional `--enable-write-tools` and `--write-tools` passed through to runtime env vars
