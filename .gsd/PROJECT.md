# Project: Zscaler MCP Deployer

## What This Is

A lightweight CLI tool that deploys the Zscaler MCP server to officially supported platforms. Starting with AWS Bedrock AgentCore, it provides a strict, guided deployment experience that handles the painful parts of the official process while maintaining security best practices.

## Core Value

An individual operator can run one command and have a working, verified Zscaler MCP server running on an officially supported platform with proper credential handling, runtime verification, and clear next steps for connecting an MCP client.

## Current State

**Milestone M001 complete.** CLI now supports full deployment pipeline:
- Comprehensive validation engine (AWS session, IAM permissions, Zscaler credentials)
- AWS Secrets Manager integration with KMS-encrypted secrets and idempotent creation
- IAM execution role bootstrap with trust policy validation and propagation wait
- Bootstrap orchestrator with automatic rollback on partial failure
- **BedrockRuntime class** with CRUD operations and status polling
- **DeployOrchestrator** coordinating bootstrap → runtime creation → polling with rollback
- **Runtime verification** via CloudWatch log analysis with health pattern matching
- **Connection formatter** generating cross-platform MCP client configs for Claude Desktop and Cursor
- **CLI deploy command** with verification panels, connection instructions, and proper exit codes
- **Comprehensive documentation** with README, command reference, and troubleshooting guides

All 372 tests passing (S01: 72, S02: 117, S03: 93, S04: 90, S05: 0). Requirements R001-R007 validated. The CLI delivers on its vision: an individual operator runs one command and has a verified, working Zscaler MCP server on AWS Bedrock AgentCore.

## Architecture / Key Patterns

- CLI-first: One command entry with interactive prompts
- Strict preflight: Fail early with exact fixes, no silent assumptions
- AWS-native: Uses official AWS SDKs and APIs
- Security-first: Secrets Manager for credentials, never env vars in production
- Verification-driven: Runtime must be proven up, not just created
- Phase-based deployment: Track exact failure location (bootstrap, runtime_create, polling)
- Selective rollback: Only delete runtime on failure, keep bootstrap resources for troubleshooting

## Capability Contract

See `.gsd/REQUIREMENTS.md` for the explicit capability contract, requirement status, and coverage mapping.

## Milestone Sequence

- [x] **M001:** Bedrock Deploy CLI Foundation — One-command interactive deploy to AWS Bedrock AgentCore with strict preflight, Secrets Manager integration, and runtime verification
- [ ] **M002:** AWS Hardening & Reusable Engine — Lifecycle management (update/destroy), status/reporting, reusable deployment abstractions
- [ ] **M003:** Multi-Server Network/Security MCP Support — Support additional network and security MCP servers beyond Zscaler, template system for owned servers
