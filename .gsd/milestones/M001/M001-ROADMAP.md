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

- [x] **S01: Preflight & Validation Engine** `risk:high` `depends:[]`
  > After this: CLI validates AWS permissions, region, Zscaler credentials, and fails fast with exact fix instructions before any deployment attempt.

- [x] **S02: Secrets Manager & IAM Bootstrap** `risk:high` `depends:[S01]`
  > After this: CLI creates KMS-encrypted Secrets Manager secret and IAM execution role with proper permissions, or uses existing resources.

- [x] **S03: Bedrock Runtime Deployment** `risk:medium` `depends:[S02]`
  > After this: CLI creates Bedrock AgentCore runtime with proper configuration, using official Zscaler image or operator's ECR.

- [x] **S04: Verification & Connection Output** `risk:medium` `depends:[S03]`
  > After this: CLI verifies runtime health via CloudWatch logs, confirms credential injection, and outputs runtime ID/ARN with MCP connection instructions.

['x] **S05: Documentation & First-Run Polish** `risk:low` `depends:[S04]`\n  > After this: README guides new users through install and first deploy, common issues documented, error messages are actionable.\n\n## Boundary Map\n\n### S01 → S02\n']
