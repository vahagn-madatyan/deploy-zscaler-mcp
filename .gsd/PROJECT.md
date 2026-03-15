# Project: Zscaler MCP Deployer

## What This Is

A lightweight CLI tool that deploys the Zscaler MCP server to officially supported platforms. Starting with AWS Bedrock AgentCore, it provides a strict, guided deployment experience that handles the painful parts of the official process while maintaining security best practices.

## Core Value

An individual operator can run one command and have a working, verified Zscaler MCP server running on an officially supported platform with proper credential handling, runtime verification, and clear next steps for connecting an MCP client.

## Current State

New project. Repository contains research artifacts (architecture analysis, deployment comparison) but no implementation. The upstream `zscaler-mcp-server` package already supports the server runtime; this CLI orchestrates the deployment to AWS Bedrock AgentCore.

## Architecture / Key Patterns

- CLI-first: One command entry with interactive prompts
- Strict preflight: Fail early with exact fixes, no silent assumptions
- AWS-native: Uses official AWS SDKs and APIs
- Security-first: Secrets Manager for credentials, never env vars in production
- Verification-driven: Runtime must be proven up, not just created

## Capability Contract

See `.gsd/REQUIREMENTS.md` for the explicit capability contract, requirement status, and coverage mapping.

## Milestone Sequence

- [ ] **M001:** Bedrock Deploy CLI Foundation — One-command interactive deploy to AWS Bedrock AgentCore with strict preflight, Secrets Manager integration, and runtime verification
- [ ] **M002:** AWS Hardening & Reusable Engine — Lifecycle management (update/destroy), status/reporting, reusable deployment abstractions
- [ ] **M003:** Multi-Server Network/Security MCP Support — Support additional network and security MCP servers beyond Zscaler, template system for owned servers
