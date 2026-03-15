# M001: Bedrock Deploy CLI Foundation — Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

## Project Description

A one-command CLI that deploys the Zscaler MCP server to AWS Bedrock AgentCore. The CLI must be strict (fail early with clear errors), interactive (guide the operator through prompts), and complete (verify the runtime actually works and provide connection instructions).

## Why This Milestone

The official Zscaler Bedrock deployment guide exists but requires:
- Multiple manual AWS CLI commands
- Understanding of IAM roles, Secrets Manager, and Bedrock AgentCore
- Careful credential handling
- Manual verification that the deployment actually worked

This milestone removes that friction while staying strictly within Zscaler-supported methods.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Run `zscaler-mcp-deploy` and answer interactive prompts
- Have a working Zscaler MCP server running on AWS Bedrock AgentCore
- Receive runtime ID/ARN, verification commands, and MCP connection instructions
- Trust that strict preflight caught any issues before deployment started

### Entry point / environment

- Entry point: `zscaler-mcp-deploy` CLI command
- Environment: Operator's local terminal (macOS/Linux/Windows)
- Live dependencies involved: AWS APIs, Zscaler APIs (for credential validation)

## Completion Class

- **Contract complete means:** CLI code exists with preflight checks, AWS SDK integration, Secrets Manager handling, and runtime verification
- **Integration complete means:** Successfully deploys to real AWS Bedrock AgentCore, runtime is accessible
- **Operational complete means:** Operator can connect an MCP client and use Zscaler tools through the deployed runtime

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- A new user with AWS CLI configured and Zscaler credentials can run the CLI and get a working deployment
- The deployed runtime passes AWS health checks and shows successful credential injection in logs
- The operator receives clear instructions for connecting Claude Desktop, Cursor, or another MCP client
- Strict preflight catches missing permissions, invalid credentials, or unsupported regions before any AWS resources are created

## Risks and Unknowns

- **AWS permission complexity** — The IAM role needs specific permissions for ECR, Secrets Manager, CloudWatch, and Bedrock. Preflight must validate these precisely. — Affects R002
- **Secrets Manager bootstrap** — Creating secrets and IAM roles requires permissions the operator might not have. Need clear error paths. — Affects R002, R003
- **Zscaler credential validity** — We can validate format but not actual API access without calling Zscaler. Need to decide how deep validation goes. — Affects R002
- **Bedrock AgentCore availability** — Service might not be available in all regions or all AWS accounts. Need region validation. — Affects R002
- **ECR image sourcing** — Use official Zscaler Marketplace image or require operator to push to their ECR? Affects UX complexity. — Affects R004

## Existing Codebase / Prior Art

- `zscaler-mcp-remote-final.md` — Research document comparing deployment platforms, confirms Bedrock AgentCore is the Zscaler-supported enterprise path
- `zscaler-mcp-remote-architecture.mermaid` — Architecture diagram showing the full deployment flow
- `zscaler-mcp-remote-deployment.jsx` — UI prototype showing deployment tier strategy
- Upstream `zscaler-mcp-server` — The actual MCP server being deployed, already has Bedrock-specific image

## Relevant Requirements

- R001 — One-Command Interactive Deploy — Core user loop, this milestone's primary deliverable
- R002 — Strict Preflight Validation — Essential for safe AWS operations
- R003 — AWS Secrets Manager Integration — Security requirement
- R004 — Runtime Deployment Execution — The actual deployment
- R005 — Runtime Verification — Proof that it actually worked
- R006 — Connection Instructions Output — Completes the user loop
- R007 — Network/Security MCP Focus — Strategic constraint

## Scope

### In Scope

- Interactive CLI for AWS Bedrock AgentCore deployment
- Strict preflight validation of AWS permissions, region, credentials
- AWS Secrets Manager secret creation and IAM role configuration
- Bedrock AgentCore runtime creation via AWS APIs
- Runtime verification (status checks, log validation)
- Connection instruction output for MCP clients
- Documentation for first-time setup

### Out of Scope / Non-Goals

- Update/destroy lifecycle (M002)
- Status monitoring beyond initial verification (M002)
- Non-AWS platforms (deferred)
- Generic MCP server support (out of scope per R011)
- Automated MCP client configuration (operator manually adds to Claude/Cursor)
- Windows-specific preflight (support Windows, but primary target is macOS/Linux)

## Technical Constraints

- Python-based CLI (aligns with Zscaler MCP server ecosystem)
- AWS SDK (boto3) for all AWS operations
- Must work with standard AWS credential chain (env vars, ~/.aws/credentials, IAM role)
- Must handle AWS region selection explicitly (Bedrock AgentCore not available everywhere)
- Interactive prompts must work in standard terminal (rich or similar for UX)

## Integration Points

- **AWS IAM** — Create execution role with specific permissions
- **AWS Secrets Manager** — Create/read secrets, validate KMS encryption
- **AWS Bedrock AgentCore** — Create and manage AgentCore runtimes
- **AWS CloudWatch Logs** — Read runtime logs for verification
- **AWS ECR** — Potentially push/pull container images
- **Zscaler OneAPI** — Validate credentials (format check, potentially live check)

## Open Questions

- **Should we support direct env var credentials as fallback?** — Current thinking: No, Secrets Manager only for M001 per user direction
- **Should we validate Zscaler credentials with a live API call?** — Current thinking: Yes, but graceful fallback if Zscaler API is unreachable
- **Should we use official Zscaler Marketplace image or require ECR push?** — Current thinking: Marketplace image if possible (simpler), document ECR path if needed
- **How do we handle region selection?** — Current thinking: Interactive prompt with validation of Bedrock AgentCore availability
