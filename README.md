# Zscaler MCP Deployer

[![PyPI version](https://img.shields.io/pypi/v/zscaler-mcp-deployer.svg)](https://pypi.org/project/zscaler-mcp-deployer/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A production-ready CLI tool for deploying the [Zscaler MCP Server](https://pypi.org/project/zscaler-mcp/) to AWS Bedrock AgentCore with strict preflight validation, secure credential handling, and clear connection instructions.

## Overview

Zscaler MCP Deployer streamlines the deployment of Zscaler MCP servers on AWS Bedrock AgentCore. It provides:

- ✅ **Strict preflight validation** — Catches missing permissions, invalid credentials, unsupported regions
- 🔐 **Secure credential handling** — Uses AWS Secrets Manager, never environment variables
- 🚀 **One-command deployment** — From zero to running MCP server in minutes
- 📊 **Runtime verification** — Proves deployment actually works, not just CREATE_COMPLETE
- 🔄 **Idempotent operations** — Safe to run multiple times without side effects
- 📋 **Actionable error messages** — Exact fix instructions for common failure modes

## Quick Start

1. **Install the CLI:**
   ```bash
   pip install zscaler-mcp-deployer
   ```

2. **Configure AWS credentials:**
   ```bash
   aws configure
   ```

3. **Validate prerequisites (optional but recommended):**
   ```bash
   zscaler-mcp-deploy preflight
   ```

4. **Deploy your MCP server:**
   ```bash
   zscaler-mcp-deploy deploy
   ```

5. **Connect your MCP client** (Claude Desktop or Cursor) using the generated configuration.

## Features

### Strict Preflight Validation

Before any AWS resources are created, the CLI validates:

- ✅ AWS credentials are configured and valid
- ✅ Required IAM permissions are available
- ✅ Selected AWS region supports Bedrock
- ✅ Zscaler credentials are valid and functional

### AWS Secrets Manager Integration

All Zscaler credentials are stored securely in AWS Secrets Manager:

- 🔒 Uses KMS encryption by default
- 📝 JSON secret structure with all required credentials
- 🔄 Supports existing secrets for idempotent operation

### Bedrock AgentCore Runtime

Deploys a production-ready Bedrock runtime with:

- 🐳 Container image from official Zscaler source
- 🔧 IAM execution role with minimal required permissions
- 🌐 Support for both read-only and write-capable tools
- 📊 Runtime health verification via CloudWatch logs

### Connection Instructions

Provides copy-paste-ready configuration for:

- Claude Desktop
- Cursor
- Any MCP-compatible client

## Prerequisites

### AWS Requirements

- **AWS CLI** configured with valid credentials
- **IAM permissions** for:
  - `secretsmanager:*`
  - `iam:CreateRole`, `iam:AttachRolePolicy`, `iam:GetRole`
  - `bedrock:CreateAgentCoreRuntime`, `bedrock:GetAgentCoreRuntime`
  - `logs:FilterLogEvents`, `logs:GetLogEvents`
- **AWS region** that supports Bedrock (e.g., `us-east-1`, `us-west-2`, `eu-west-1`)

### Zscaler Requirements

- **Admin credentials** for your Zscaler tenant
- **API key** (32 hexadecimal characters)
- **Cloud name** (e.g., `zscaler`, `zscalerone`, `zscalergov`)

## Installation

### Via pip (recommended)

```bash
pip install zscaler-mcp-deployer
```

### Via source

```bash
git clone <repository-url>
cd zscaler-mcp-deployer
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

## Usage

### First-run Validation

Validate all prerequisites before deployment:

```bash
# Interactive first-run validation
zscaler-mcp-deploy first-run

# Or validate with specific parameters
zscaler-mcp-deploy preflight --region us-east-1 --zscaler-cloud zscaler
```

### Deploy Command

Deploy a complete Zscaler MCP server to AWS Bedrock:

```bash
# Interactive deployment (recommended for first use)
zscaler-mcp-deploy deploy

# Or deploy with all parameters specified
zscaler-mcp-deploy deploy \
  --runtime-name my-zscaler-runtime \
  --secret-name zscaler/mcp/credentials \
  --role-name zscaler-mcp-execution-role \
  --region us-east-1 \
  --zscaler-cloud zscaler \
  --enable-write-tools
```

### Bootstrap Resources Only

Create AWS resources without deploying the runtime:

```bash
zscaler-mcp-deploy bootstrap \
  --secret-name zscaler/mcp/credentials \
  --role-name zscaler-mcp-execution-role
```

### Help and Version

```bash
# Show version
zscaler-mcp-deploy --version

# Show help
zscaler-mcp-deploy --help

# Show help for specific command
zscaler-mcp-deploy deploy --help
```

## Security Model

### Credential Handling

- **Never** uses environment variables for credentials
- **Always** stores Zscaler credentials in AWS Secrets Manager
- **Encrypts** secrets with AWS KMS by default
- **Rotates** credentials via the AWS console

### IAM Permissions

The CLI follows least-privilege principles:

1. **Bootstrap Role** — Minimal permissions for Secrets Manager and IAM
2. **Runtime Role** — Bedrock execution permissions only
3. **Execution Policy** — Read-only by default, write tools opt-in

### Write Capabilities

Write tools are **disabled by default** and require explicit opt-in:

```bash
# Enable all write tools
zscaler-mcp-deploy deploy --enable-write-tools

# Or enable specific tools
zscaler-mcp-deploy deploy --write-tools "zpa_create_app_segment"
```

## Troubleshooting

### Common Issues

**AWS Credential Errors:**
- `No AWS credentials found` → Run `aws configure`
- `AccessDenied` → Check IAM permissions with `aws sts get-caller-identity`
- `InvalidAccessKeyId` → Verify access key in `~/.aws/credentials`

**Zscaler Credential Errors:**
- `Invalid username format` → Must be email address
- `Invalid API key format` → Must be 32 hex characters
- `Authentication failed` → Verify all credentials in Zscaler admin console

**Region Issues:**
- `Region does not support Bedrock` → Use `us-east-1`, `us-west-2`, or `eu-west-1`

### Debugging Deployment

Check CloudWatch logs for runtime health:

```bash
# View CloudWatch logs for your runtime
aws logs tail /aws/bedrock/<runtime-id> --follow --region <region>
```

Check IAM role and secret status:

```bash
# Check IAM role
aws iam get-role --role-name zscaler-mcp-execution-role

# Check Secrets Manager secret
aws secretsmanager list-secrets --filters Key="name",Values="zscaler/mcp/credentials"
```

## Architecture

The deployment creates three main AWS resources:

1. **AWS Secrets Manager Secret** (encrypted with KMS)
   - Stores Zscaler credentials securely
   - Accessible only to the runtime role

2. **IAM Execution Role**
   - Minimal permissions for Bedrock runtime
   - Can retrieve the Secrets Manager secret

3. **Bedrock AgentCore Runtime**
   - Containerized Zscaler MCP server
   - Configured with secret reference for credential injection
   - Ready for client connections

## License

MIT License. See [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Support

For issues, please file a GitHub issue with:

1. The error message and traceback
2. Your AWS region and CLI version
3. Steps to reproduce the issue

## Requirements Coverage

This tool satisfies all requirements for M001 milestone:

✅ **R001** — One-Command Interactive Deploy  
✅ **R002** — Strict Preflight Validation  
✅ **R003** — AWS Secrets Manager Integration  
✅ **R004** — Runtime Deployment Execution  
✅ **R005** — Runtime Verification  
✅ **R006** — Connection Instructions Output  
✅ **R007** — Network/Security MCP Focus  

---