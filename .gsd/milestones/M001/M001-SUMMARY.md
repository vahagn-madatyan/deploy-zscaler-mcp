---
id: M001
provides:
  - One-command interactive CLI deploy to AWS Bedrock AgentCore
  - Strict preflight validation of AWS credentials, IAM permissions, and Zscaler credentials
  - AWS Secrets Manager integration with KMS-encrypted secrets
  - Bedrock AgentCore runtime creation with IAM execution roles
  - Runtime verification via CloudWatch log analysis
  - Copy-paste ready MCP client connection instructions
key_decisions:
  - D001: Primary deployment platform is AWS Bedrock AgentCore
  - D002: CLI performs actual deployment (not just template generation)
  - D003: Interactive prompts for user experience
  - D004: AWS Secrets Manager only for credential storage
  - D005: Strict preflight validation with exact fix instructions
  - D006: Network/security MCP focus (not generic framework)
  - D007: Runtime verification required (not just AWS CREATE_COMPLETE)
  - D008: Typer with Rich for CLI framework
patterns_established:
  - Validator pattern with clear separation of concerns
  - AWS resource modules with lazy boto3 initialization
  - Orchestrator pattern with injected dependencies for testability
  - Idempotent operations with rollback on partial failure
  - Phase-based deployment tracking for precise diagnostics
  - Structured error hierarchy with actionable messages
  - Rich console output with color-coded status indicators
observability_surfaces:
  - CLI preflight command with structured validation status
  - Bootstrap command with Rich table output showing resource creation
  - Deploy command with verification panels and connection instructions
  - Structured logging via logging module
  - Error codes with specific prefixes (S01-*, S02-*, S03-*, S04-*)
  - Test suite (372 tests) covering all functionality
requirement_outcomes:
  - id: R001
    from_status: active
    to_status: validated
    proof: CLI structure with version, help, and preflight commands proven. Interactive prompts for credentials in place. S01-UAT validation passed.
  - id: R002
    from_status: active
    to_status: validated
    proof: Comprehensive validation engine with 72 tests covering AWS session, IAM permissions, and Zscaler credentials. Fails fast with exact fix instructions. S01-UAT validation passed.
  - id: R003
    from_status: active
    to_status: validated
    proof: SecretsManager class with idempotent create_or_use_secret(), KMS encryption, JSON secret structure. 31 tests + integration coverage. S02-UAT validation passed.
  - id: R004
    from_status: active
    to_status: validated
    proof: BedrockRuntime class with create_runtime(), status polling with exponential backoff, DeployOrchestrator coordinating bootstrap→runtime→polling, 93 tests proving integration with S02 outputs. S03-UAT validation passed.
  - id: R005
    from_status: active
    to_status: validated
    proof: CloudWatch log pattern matching for health indicators ("credential", "retrieved", "MCP server", "started", "listening"). S04-UAT validation passed.
  - id: R006
    from_status: active
    to_status: validated
    proof: Cross-platform MCP client config generation for Claude Desktop and Cursor with stdio transport. S04-UAT validation passed.
  - id: R007
    from_status: active
    to_status: validated
    proof: Documentation establishes clear Zscaler network/security focus. S05-UAT validation passed.
duration: 5h 57m
verification_result: passed
completed_at: 2026-03-15
---

# M001: Bedrock Deploy CLI Foundation

**One-command interactive CLI deployment to AWS Bedrock AgentCore with strict preflight, Secrets Manager integration, and runtime verification**

## What Happened

Milestone M001 delivered a complete CLI foundation for deploying Zscaler MCP servers to AWS Bedrock AgentCore. The milestone implemented a five-slice architecture that creates a seamless, validated deployment experience:

1. **S01: Preflight & Validation Engine** established the CLI structure with Typer/Rich and built comprehensive validators for AWS sessions, IAM permissions, and Zscaler credentials. The 72-test validation suite ensures operators receive specific, actionable error messages before any AWS resources are created.

2. **S02: Secrets Manager & IAM Bootstrap** implemented idempotent AWS resource creation with KMS-encrypted Secrets Manager secrets and IAM execution roles. The bootstrap orchestrator provides automatic rollback on partial failures and follows security-first patterns.

3. **S03: Bedrock Runtime Deployment** integrated S02 outputs to create Bedrock AgentCore runtimes via AWS APIs. The deploy orchestrator coordinates bootstrap → runtime creation → status polling with precise phase tracking and selective rollback.

4. **S04: Verification & Connection Output** proved runtime health through CloudWatch log analysis and generated cross-platform MCP client configurations. The verification engine uses keyword pattern matching resilient to log format changes.

5. **S05: Documentation & First-Run Polish** provided comprehensive README, command reference, and troubleshooting guides. The documentation enables new users to successfully deploy without external AWS documentation.

## Cross-Slice Verification

The milestone's success criteria were verified through multiple evidence sources:

- **CLI functionality**: `zscaler-mcp-deploy --version`, `--help`, `preflight`, `bootstrap`, and `deploy` commands work correctly with interactive prompts and Rich output formatting
- **Unit test coverage**: 372 comprehensive tests across all slices (S01: 72, S02: 117, S03: 93, S04: 90) covering validators, AWS resource modules, orchestrators, and integration flows
- **Integration verification**: End-to-end deployment flows proven through orchestrator integration tests that exercise bootstrap→runtime→verification chains
- **Runtime verification**: CloudWatch log pattern matching for health indicators ("credential", "retrieved", "MCP server", "started", "listening") proves actual runtime functionality beyond AWS CREATE_COMPLETE
- **Connection instructions**: Cross-platform MCP client config generation for Claude Desktop and Cursor produces copy-paste ready configurations with proper stdio transport
- **User experience**: Documentation verified through S05-UAT that new users can follow README and successfully deploy without hitting undocumented issues

## Requirement Changes

- R001: active → validated — CLI structure with version, help, and preflight commands proven. Interactive prompts for credentials in place. S01-UAT validation passed.
- R002: active → validated — Comprehensive validation engine with 72 tests covering AWS session, IAM permissions, and Zscaler credentials. Fails fast with exact fix instructions. S01-UAT validation passed.
- R003: active → validated — SecretsManager class with idempotent create_or_use_secret(), KMS encryption, JSON secret structure. 31 tests + integration coverage. S02-UAT validation passed.
- R004: active → validated — BedrockRuntime class with create_runtime(), status polling with exponential backoff, DeployOrchestrator coordinating bootstrap→runtime→polling, 93 tests proving integration with S02 outputs. S03-UAT validation passed.
- R005: active → validated — CloudWatch log pattern matching for health indicators ("credential", "retrieved", "MCP server", "started", "listening"). S04-UAT validation passed.
- R006: active → validated — Cross-platform MCP client config generation for Claude Desktop and Cursor with stdio transport. S04-UAT validation passed.
- R007: active → validated — Documentation establishes clear Zscaler network/security focus. S05-UAT validation passed.

## Forward Intelligence

### What the next milestone should know
- Secret ARN format includes AWS-generated 6-character suffix that must be stripped for environment variable injection
- IAM role requires bedrock.amazonaws.com principal with sts:AssumeRole and secretsmanager:GetSecretValue permissions
- Bedrock runtime creation takes 2-5 minutes typically with exponential backoff polling (5s to 30s intervals)
- CloudWatch log verification uses keyword-based pattern matching resilient to format changes
- Deploy orchestrator provides precise phase tracking (bootstrap, runtime_create, polling, completed) for diagnostics

### What's fragile
- Secret name extraction from ARN uses regex that may break if AWS changes ARN format
- IAM eventual consistency handled with 15-second propagation wait but real-world timing may vary
- CloudWatch log pattern matching depends on Zscaler MCP server log format stability

### Authoritative diagnostics
- Check DeployResult.phase first to see exactly where failures occurred during deployment orchestration
- Inspect error codes with S02-* (bootstrap), S03-* (runtime), S04-* (verification) prefixes for rapid categorization
- Review BootstrapResult.resource_ids list for resources created before failure (manual cleanup if rollback fails)
- Use RuntimeVerifier directly to check runtime health status without redeploying

### What assumptions changed
- Assumed IAM simulation would be complex but practical validation via actual service calls proved simpler and more accurate
- Expected single polling interval but exponential backoff provided better UX and API rate limit respect
- Thought rollback would clean up everything but keeping bootstrap resources for troubleshooting proved operationally wise

## Files Created/Modified

- `src/zscaler_mcp_deploy/cli.py` — Main CLI with preflight, bootstrap, and deploy commands
- `src/zscaler_mcp_deploy/errors.py` — Structured error hierarchy with S01-S04 prefixes
- `src/zscaler_mcp_deploy/messages.py` — Error message catalog and user guidance
- `src/zscaler_mcp_deploy/validators/aws.py` — AWS session and region validation
- `src/zscaler_mcp_deploy/validators/iam.py` — IAM permission validation
- `src/zscaler_mcp_deploy/validators/zscaler.py` — Zscaler credential validation
- `src/zscaler_mcp_deploy/aws/secrets_manager.py` — SecretsManager class with CRUD operations
- `src/zscaler_mcp_deploy/aws/iam_bootstrap.py` — IAMBootstrap class with trust/inline policies
- `src/zscaler_mcp_deploy/aws/bedrock_runtime.py` — BedrockRuntime class with status polling
- `src/zscaler_mcp_deploy/bootstrap.py` — BootstrapOrchestrator with rollback logic
- `src/zscaler_mcp_deploy/deploy.py` — DeployOrchestrator coordinating full deployment
- `src/zscaler_mcp_deploy/aws/cloudwatch_verifier.py` — RuntimeVerifier with log pattern matching
- `src/zscaler_mcp_deploy/output/connection_formatter.py` — ConnectionFormatter for MCP client configs
- `tests/` — 372 comprehensive unit and integration tests across all modules
- `README.md` — Comprehensive user documentation with installation and usage guides