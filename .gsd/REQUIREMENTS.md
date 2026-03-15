# Requirements

This file is the explicit capability and coverage contract for the project.

## Validated

### R001 — One-Command Interactive Deploy
- **Class:** primary-user-loop
- **Status:** validated
- **Description:** Operator runs a single CLI command with interactive prompts to deploy Zscaler MCP to AWS Bedrock AgentCore. No config files to edit, no manual AWS console steps.
- **Why it matters:** Removes the friction of multi-step AWS setup and CloudFormation parameter configuration.
- **Source:** user
- **Primary owning slice:** M001/S01
- **Supporting slices:** M001/S02
- **Validation:** S01-UAT
- **Notes:** CLI structure with version, help, and preflight commands proven. Interactive prompts for credentials in place.

### R002 — Strict Preflight Validation
- **Class:** failure-visibility
- **Status:** validated
- **Description:** CLI validates all prerequisites before attempting deployment: AWS CLI configured with appropriate permissions, AWS region supported, Zscaler credentials valid, required IAM permissions available.
- **Why it matters:** AWS deploy failures are expensive and confusing. Strict preflight gives clear, actionable errors before any resources are created.
- **Source:** user
- **Primary owning slice:** M001/S01
- **Supporting slices:** none
- **Validation:** S01-UAT
- **Notes:** Comprehensive validation engine with 72 tests covering AWS session, IAM permissions, and Zscaler credentials. Fails fast with exact fix instructions.

## Validated

### R003 — AWS Secrets Manager Integration
- **Class:** compliance/security
- **Status:** validated
- **Description:** Zscaler API credentials stored in AWS Secrets Manager (KMS-encrypted), not passed as environment variables. Container retrieves credentials at runtime.
- **Why it matters:** Zero credentials in infrastructure configuration, CloudTrail audit logging, supports rotation. Aligns with Zscaler official recommended approach.
- **Source:** user
- **Primary owning slice:** M001/S02
- **Supporting slices:** M001/S01
- **Validation:** S02-UAT
- **Notes:** SecretsManager class with idempotent create_or_use_secret(), KMS encryption, JSON secret structure. 31 tests + integration coverage.

## Validated

### R004 — Runtime Deployment Execution
- **Class:** core-capability
- **Status:** validated
- **Description:** CLI creates the Bedrock AgentCore runtime using AWS APIs, with proper IAM execution role, ECR image reference, and environment configuration.
- **Why it matters:** The actual deployment must happen automatically, not just generate templates.
- **Source:** user
- **Primary owning slice:** M001/S03
- **Supporting slices:** M001/S02, M001/S01
- **Validation:** S03-UAT
- **Notes:** BedrockRuntime class with create_runtime(), status polling with exponential backoff, DeployOrchestrator coordinating bootstrap→runtime→polling, 93 tests proving integration with S02 outputs.

### R005 — Runtime Verification
- **Class:** failure-visibility
- **Status:** active
- **Description:** After deployment, CLI verifies the runtime is actually up and healthy: runtime status check, log stream validation, credential injection confirmation.
- **Why it matters:** AWS says "CREATE_COMPLETE" but runtime might still be failing. Verification proves it works before handing back to user.
- **Source:** user
- **Primary owning slice:** M001/S03
- **Supporting slices:** M001/S02
- **Validation:** unmapped
- **Notes:** Look for specific log patterns indicating successful credential retrieval

### R006 — Connection Instructions Output
- **Class:** primary-user-loop
- **Status:** active
- **Description:** CLI outputs clear, copy-paste-ready instructions for connecting an MCP client to the deployed runtime: runtime ID/ARN, endpoint URL, verification commands, next steps.
- **Why it matters:** Deployment is useless if operator doesn't know how to actually connect and use it.
- **Source:** user
- **Primary owning slice:** M001/S03
- **Supporting slices:** none
- **Validation:** unmapped
- **Notes:** Include runtime ID, ARN, verification command, and MCP client config snippet

### R007 — Network/Security MCP Focus
- **Class:** differentiator
- **Status:** active
- **Description:** Product is explicitly designed for network and security MCP servers (Zscaler now, others later), not a generic MCP deployment framework.
- **Why it matters:** Keeps scope focused, allows domain-specific optimizations and security patterns that generic tools can't provide.
- **Source:** user
- **Primary owning slice:** M001 (foundation), M003 (expansion)
- **Supporting slices:** all
- **Validation:** unmapped
- **Notes:** This is a strategic constraint, not a technical one

## Deferred

### R008 — Lifecycle Management (Update/Destroy)
- **Class:** operability
- **Status:** deferred
- **Description:** CLI supports updating runtime configuration and clean destruction of all created resources.
- **Why it matters:** Real operations require lifecycle management, not just initial deploy.
- **Source:** inferred
- **Primary owning slice:** M002
- **Supporting slices:** none
- **Validation:** unmapped
- **Notes:** Deferred to M002; M001 is deploy-only

### R009 — Status Reporting & Monitoring
- **Class:** operability
- **Status:** deferred
- **Description:** CLI can report runtime status, recent logs, health checks on demand without redeploying.
- **Why it matters:** Operators need visibility into running systems.
- **Source:** inferred
- **Primary owning slice:** M002
- **Supporting slices:** none
- **Validation:** unmapped
- **Notes:** Deferred to M002

### R010 — Non-AWS Platform Support
- **Class:** core-capability
- **Status:** deferred
- **Description:** Support deployment to other officially supported platforms beyond AWS Bedrock AgentCore.
- **Why it matters:** Future expansion to other Zscaler-supported or network/security MCP deployment targets.
- **Source:** inferred
- **Primary owning slice:** M003
- **Supporting slices:** none
- **Validation:** unmapped
- **Notes:** Depends on Zscaler adding official support for other platforms

## Out of Scope

### R011 — Generic MCP Deployment Framework
- **Class:** anti-feature
- **Status:** out-of-scope
- **Description:** A pluggable framework for deploying any MCP server to any platform.
- **Why it matters:** Prevents scope creep into generic PaaS territory. Product stays focused on network/security MCP with specific patterns.
- **Source:** user
- **Primary owning slice:** none
- **Supporting slices:** none
- **Validation:** n/a
- **Notes:** User explicitly said "network/security MCP" not "any MCP"

### R012 — Community-Only Deployment Paths
- **Class:** constraint
- **Status:** out-of-scope
- **Description:** Support for deployment paths not officially supported by Zscaler (Railway, Render, Coolify, etc).
- **Why it matters:** M001 must use officially supported methods per user direction. These may be added later if Zscaler officially supports them.
- **Source:** user
- **Primary owning slice:** none
- **Supporting slices:** none
- **Validation:** n/a
- **Notes:** Research artifacts exist for these, but not in scope for M001

## Traceability

| ID | Class | Status | Primary owner | Supporting | Proof |
|---|---|---|---|---|---|
| R001 | primary-user-loop | validated | M001/S01 | M001/S02 | S01-UAT |
| R002 | failure-visibility | validated | M001/S01 | none | S01-UAT |
| R003 | compliance/security | validated | M001/S02 | M001/S01 | S02-UAT |
| R004 | core-capability | validated | M001/S03 | M001/S02 | S03-UAT |
| R005 | failure-visibility | active | M001/S03 | M001/S02 | unmapped |
| R006 | primary-user-loop | active | M001/S03 | none | unmapped |
| R007 | differentiator | active | M001 | M003 | unmapped |
| R008 | operability | deferred | M002 | none | unmapped |
| R009 | operability | deferred | M002 | none | unmapped |
| R010 | core-capability | deferred | M003 | none | unmapped |
| R011 | anti-feature | out-of-scope | none | none | n/a |
| R012 | constraint | out-of-scope | none | none | n/a |

## Coverage Summary

- Active requirements: 5
- Mapped to slices: 6
- Validated: 4
- Unmapped active requirements: 0
