# Changelog

All notable changes to Zscaler MCP Deployer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release with core deployment functionality
- Preflight validation for AWS credentials, IAM permissions, and Zscaler credentials
- Bootstrap command for creating Secrets Manager secrets and IAM roles
- Deploy command for creating Bedrock AgentCore runtimes
- Runtime verification via CloudWatch logs
- Connection instructions for Claude Desktop and Cursor
- Comprehensive documentation and troubleshooting guides

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [0.1.0] - 2024-03-15

### Added
- Initial public release
- Core deployment functionality for Zscaler MCP on AWS Bedrock
- Preflight validation with actionable error messages
- Secure credential handling via AWS Secrets Manager
- One-command deployment workflow
- Runtime health verification
- Copy-paste connection instructions

[Unreleased]: https://github.com/zscaler/zscaler-mcp-deployer/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/zscaler/zscaler-mcp-deployer/releases/tag/v0.1.0