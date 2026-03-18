# Zscaler MCP Deployer

[![PyPI version](https://img.shields.io/pypi/v/deploy-zscaler-mcp.svg)](https://pypi.org/project/deploy-zscaler-mcp/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache--2.0-green.svg)](LICENSE)

CLI tool for deploying Zscaler MCP servers with AI assistants. Automate the deployment of production-ready Zscaler MCP servers on AWS with strict validation, secure credential handling, and clear connection instructions.

**Input:** Configuration via CLI or environment
**Output:** Deployed Zscaler MCP server ready for AI assistant integration

```text
  AI Assistant  ──▶  MCP Server  ──▶  Zscaler API
  (Claude, etc.)     (AWS Bedrock    (Cloud, Private
                      Runtime)        Access, ZPA)
```

---

## Installation

### Option 1: Install from PyPI (recommended)

```bash
pip install deploy-zscaler-mcp
```

### Option 2: Install with pipx (isolated environment)

```bash
pipx install deploy-zscaler-mcp
```

### Verify installation

```bash
deploy-zscaler-mcp --help
```

---

## Setup

### 1. Configure AWS Credentials

The deployer uses standard AWS credential configuration:

```bash
# Using AWS CLI
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

### 2. Get Zscaler API Credentials

1. Log in to the Zscaler admin portal
2. Navigate to **Administration** → **API**
3. Generate an API key with appropriate permissions

### 3. Configure Zscaler Credentials

Create a `.env` file with your Zscaler credentials:

```bash
# Zscaler cloud configuration
ZSCALER_CLOUD=zscaler  # or zscalerone, zscalergov, zscloudx, etc.
ZSCALER_USERNAME=your_email@example.com
ZSCALER_PASSWORD=your_password
ZSCALER_API_KEY=your_32_char_hex_api_key

# AWS configuration (optional, can use default profile)
AWS_PROFILE=default
AWS_REGION=us-east-1
```

---

## Usage

### Run preflight validation

```bash
# Validate all prerequisites
deploy-zscaler-mcp preflight

# With custom region
deploy-zscaler-mcp preflight --region us-west-2
```

### Deploy MCP server

```bash
# Interactive deployment
deploy-zscaler-mcp deploy

# With specific parameters
deploy-zscaler-mcp deploy \
  --runtime-name my-zscaler-mcp \
  --region us-east-1 \
  --enable-write-tools
```

### Configure AI Assistant (Claude Desktop)

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "zscaler-mcp": {
      "command": "deploy-zscaler-mcp",
      "args": ["serve"],
      "env": {
        "ZSCALER_CLOUD": "zscaler",
        "ZSCALER_USERNAME": "your_email@example.com",
        "ZSCALER_PASSWORD": "your_password",
        "ZSCALER_API_KEY": "your_32_char_hex_api_key"
      }
    }
  }
}
```

Or if using a `.env` file alongside the install:

```json
{
  "mcpServers": {
    "zscaler-mcp": {
      "command": "deploy-zscaler-mcp",
      "args": ["serve", "--env-file", "/path/to/your/.env"]
    }
  }
}
```

---

## Available Commands

### Core Commands

| Command | Description |
|---------|-------------|
| `preflight` | Validate AWS and Zscaler configurations |
| `deploy` | Deploy complete MCP server to AWS |
| `serve` | Run MCP server in stdio or HTTP mode |
| `verify` | Verify deployed runtime connectivity |

### Deployment Options

| Flag | Description | Default |
|------|-------------|---------|
| `--runtime-name` | AWS Bedrock runtime name | `zscaler-mcp-runtime` |
| `--region` | AWS region for deployment | `us-east-1` |
| `--enable-write-tools` | Enable write capabilities | Disabled |
| `--secret-name` | AWS Secrets Manager secret name | `zscaler/mcp/credentials` |
| `--role-name` | IAM execution role name | `zscaler-mcp-execution-role` |

---

## Safety Model

Four layers prevent accidental network changes:

1. **Read-only by default** — write tools aren't registered unless you opt in
2. **CLI flag** — must explicitly pass `--enable-write-tools`
3. **MCP annotations** — read tools tagged `readOnlyHint`, write tools tagged `destructiveHint` so the AI asks for confirmation
4. **Pre-flight validation** — credential and permission validation before any API call

---

## Environment Variables

### Zscaler Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `ZSCALER_CLOUD` | Zscaler cloud name (zscaler, zscalerone, etc.) | Yes |
| `ZSCALER_USERNAME` | Zscaler admin email | Yes |
| `ZSCALER_PASSWORD` | Zscaler admin password | Yes |
| `ZSCALER_API_KEY` | 32-character hex API key | Yes |

### AWS Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_PROFILE` | AWS CLI profile name | `default` |
| `AWS_REGION` | AWS region | `us-east-1` |
| `AWS_ACCESS_KEY_ID` | AWS access key | From profile |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | From profile |

---

## Supported Zscaler Clouds

| Cloud | Endpoint |
|-------|----------|
| Commercial (default) | `zscaler` |
| Zscaler One | `zscalerone` |
| Zscaler Government | `zscalergov` |
| Zscaler CloudX | `zscloudx` |
| Zscaler Beta | `zscalerbeta` |

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `AWS credentials not found` | Run `aws configure` or set AWS environment variables |
| `Zscaler authentication failed` | Verify credentials in Zscaler admin portal |
| `Region does not support Bedrock` | Use `us-east-1`, `us-west-2`, or `eu-west-1` |
| `Insufficient IAM permissions` | Ensure required Bedrock and IAM permissions |
| Write tools not appearing | Start server with `--enable-write-tools` flag |

---

## Contributing

### Build from source

```bash
git clone https://github.com/your-username/deploy-zscaler-mcp.git
cd deploy-zscaler-mcp

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install with dev dependencies
pip install -e ".[dev]"

# Run from source
python -m src.deploy_zscaler_mcp --help
```

### Run tests

```bash
pytest tests/ -v
pytest tests/ -v --tb=short
```

### Project structure

```text
src/
├── deploy_zscaler_mcp/
│   ├── __init__.py        # Package version
│   ├── __main__.py        # Module entry point
│   ├── cli.py             # CLI interface and commands
│   ├── deployer.py        # AWS deployment logic
│   ├── config.py          # Configuration management
│   ├── validator.py       # Preflight validation
│   └── server.py          # MCP server implementation
└── tests/
```

### Making a release

Releases are published to PyPI automatically via GitHub Actions when a version tag is pushed:

```bash
# Update version in pyproject.toml and src/deploy_zscaler_mcp/__init__.py
# Commit the version bump
git tag v0.2.0
git push origin v0.2.0
```

The CI pipeline builds the distribution, runs tests, publishes to TestPyPI on every push, and publishes to PyPI on tags matching `v*`.

---

## License

[Apache License 2.0](LICENSE)