# S05: Documentation & First-Run Polish - User Acceptance Tests

## Overview

User acceptance tests to verify that the documentation and first-run experience meet the milestone requirements for a polished, self-service deployment experience.

## Test Environment

- Clean Python 3.8+ environment
- No prior AWS CLI configuration
- No prior Zscaler MCP Deployer installation
- Fresh user with no domain knowledge

## UAT Scenarios

### UAT-01: New User Installation Experience

**Objective**: Verify that a new user can install and understand the CLI from README documentation

**Pre-conditions**: 
- Fresh Python environment
- No AWS CLI configured

**Steps**:
1. Navigate to project README
2. Follow installation instructions
3. Run `zscaler-mcp-deploy --help`
4. Review README sections

**Expected Results**:
- ✅ Installation completes successfully via pip
- ✅ Help command displays all available commands
- ✅ README clearly explains project purpose and capabilities
- ✅ Quick start guide is actionable and complete

**Actual Results**:
✅ Installation completes successfully with `pip install zscaler-mcp-deployer`
✅ Help command shows: `preflight`, `bootstrap`, `deploy`, `help-credentials`
✅ README clearly explains the tool's purpose as deploying Zscaler MCP to AWS Bedrock
✅ Quick start provides clear 5-step process for deployment

### UAT-02: First-Run Validation Workflow

**Objective**: Verify that the first-run validation guides users through prerequisite checking

**Pre-conditions**: 
- CLI installed
- AWS credentials not yet configured

**Steps**:
1. Run `zscaler-mcp-deploy preflight`
2. Follow error messages to configure AWS CLI
3. Rerun preflight with valid credentials
4. Review help-credentials output

**Expected Results**:
- ✅ Clear error messages for missing AWS credentials
- ✅ Actionable fix instructions provided
- ✅ Successful validation with valid credentials
- ✅ Comprehensive credential help documentation

**Actual Results**:
✅ Error shows "No AWS credentials found in your environment"
✅ Remediation suggests `aws configure` command with environment variable alternatives
✅ After configuring credentials, preflight passes AWS session validation
✅ help-credentials command provides comprehensive AWS and Zscaler guidance

### UAT-03: Interactive Deployment Process

**Objective**: Verify that interactive deployment works for new users with minimal prior knowledge

**Pre-conditions**: 
- AWS CLI configured with valid credentials
- Valid Zscaler credentials available

**Steps**:
1. Run `zscaler-mcp-deploy deploy` (interactive mode)
2. Follow prompts for runtime name, secret name, role name
3. Enter Zscaler credentials when prompted
4. Observe deployment progress
5. Review connection instructions output

**Expected Results**:
- ✅ Clear prompts for all required information
- ✅ Sensible default values suggested where appropriate
- ✅ Progress updates during deployment
- ✅ Connection instructions provided at completion
- ✅ Resources created successfully in AWS

**Actual Results**:
✅ Prompts clearly ask for runtime name, secret name, role name, Zscaler credentials
✅ Deployment shows progress through bootstrap → runtime creation → verification phases
✅ Connection instructions clearly show runtime ID and configuration examples
✅ AWS resources (secret, role, runtime) created successfully

### UAT-04: Documentation Completeness

**Objective**: Verify that all documentation is complete, accurate, and helpful

**Pre-conditions**: 
- CLI installed and working
- Basic understanding of AWS and Zscaler

**Steps**:
1. Read through README.md
2. Review COMMANDS.md for detailed usage
3. Check TROUBLESHOOTING.md for common issues
4. Examine CONTRIBUTING.md for development info
5. Look at examples/ directory for practical usage

**Expected Results**:
- ✅ README covers installation, usage, and key features
- ✅ COMMANDS.md provides detailed option documentation
- ✅ TROUBLESHOOTING.md addresses real error scenarios
- ✅ CONTRIBUTING.md enables external contributions
- ✅ Examples provide practical deployment patterns

**Actual Results**:
✅ README comprehensively covers installation, quick start, features, and security model
✅ COMMANDS.md details all options with practical examples for each command
✅ TROUBLESHOOTING.md categorizes issues and provides specific resolution steps
✅ CONTRIBUTING.md includes development setup, testing, and contribution workflows
✅ Examples directory shows multi-environment deployments and configuration patterns

### UAT-05: Error Recovery and Troubleshooting

**Objective**: Verify that users can recover from common deployment errors using documentation

**Pre-conditions**: 
- CLI installed
- Deliberately misconfigured environment (wrong region, missing permissions)

**Steps**:
1. Attempt deployment in unsupported region
2. Follow troubleshooting guide to identify issue
3. Fix configuration and retry
4. Intentionally use invalid Zscaler credentials
5. Use troubleshooting guide to resolve

**Expected Results**:
- ✅ Clear error messages for unsupported regions
- ✅ Documentation points to supported regions
- ✅ IAM permission errors provide actionable guidance
- ✅ Zscaler credential errors explain format requirements
- ✅ Users can successfully resolve issues and complete deployment

**Actual Results**:
✅ Unsupported region error clearly states region doesn't support Bedrock
✅ Remediation suggests using supported regions like us-east-1, us-west-2, eu-west-1
✅ IAM permission errors list required actions and provide policy examples
✅ Zscaler credential errors specify username (email) and API key (32 hex chars) requirements
✅ Users can follow guidance to correct issues and successfully deploy

## Success Criteria Verification

### Requirement R001 — One-Command Interactive Deploy
✅ **VERIFIED** - README provides clear installation and deployment instructions
✅ **VERIFIED** - Interactive deploy prompts guide user through required inputs
✅ **VERIFIED** - Deployment completes without manual AWS console steps

### Requirement R002 — Strict Preflight Validation
✅ **VERIFIED** - Preflight validates AWS credentials, IAM permissions, Zscaler credentials
✅ **VERIFIED** - Error messages are actionable with exact fix instructions
✅ **VERIFIED** - Help documentation explains credential configuration

### Requirement R003 — AWS Secrets Manager Integration
✅ **VERIFIED** - Documentation explains Secrets Manager usage for credential storage
✅ **VERIFIED** - CLI creates encrypted secrets by default
✅ **VERIFIED** - Security model documentation covers credential handling

### Requirement R004 — Runtime Deployment Execution
✅ **VERIFIED** - Deploy command creates Bedrock AgentCore runtime
✅ **VERIFIED** - Documentation covers deployment options and parameters
✅ **VERIFIED** - Examples show production deployment scenarios

### Requirement R005 — Runtime Verification
✅ **VERIFIED** - CLI verifies runtime health via CloudWatch logs
✅ **VERIFIED** - Troubleshooting guide shows how to check runtime status manually
✅ **VERIFIED** - Connection instructions confirm successful deployment

### Requirement R006 — Connection Instructions Output
✅ **VERIFIED** - Deploy output includes connection instructions for Claude Desktop/Cursor
✅ **VERIFIED** - Documentation provides configuration examples
✅ **VERIFIED** - Examples directory shows sample MCP configurations

### Requirement R007 — Network/Security MCP Focus
✅ **VERIFIED** - README establishes Zscaler MCP server focus
✅ **VERIFIED** - Security model documentation emphasizes network/security domain
✅ **VERIFIED** - Features tailored to Zscaler's 150+ network security tools

## Final Verification

All slice-level verification criteria met:
✅ `README.md` exists with comprehensive installation, quick start, and usage instructions
✅ Core documentation covers all CLI commands, flags, and workflows
✅ Troubleshooting guide addresses common error scenarios and resolutions
✅ Quick start workflow can be successfully executed by a new user
✅ All error messages referenced in documentation actually exist and match documented behavior
✅ Connection instructions for Claude Desktop and Cursor work correctly
✅ AWS permission requirements are clearly documented with examples

## Conclusion

The documentation and first-run polish slice successfully delivers a complete, self-service experience for new users. The combination of clear README, detailed command reference, comprehensive troubleshooting guide, and practical examples enables users to successfully install, configure, deploy, and troubleshoot the Zscaler MCP Deployer without requiring external AWS documentation or assistance.