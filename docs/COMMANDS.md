# Command Reference

Detailed documentation for all CLI commands, options, and usage patterns.

## Global Options

| Option | Description | Default |
|--------|-------------|---------|
| `--version` | Show version and exit | |
| `--help` | Show help message and exit | |

## Commands

### `preflight`

Run preflight validation checks for AWS and Zscaler configurations.

#### Usage
```bash
zscaler-mcp-deploy preflight [OPTIONS]
```

#### Options

| Option | Type | Description | Default |
|--------|------|-------------|---------|
| `--profile`, `-p` | TEXT | AWS profile name | None |
| `--region`, `-r` | TEXT | AWS region | None |
| `--interactive`, `-i` | FLAG | Interactive region selection | False |
| `--skip-iam` | FLAG | Skip IAM permission validation | False |
| `--zscaler-cloud` | TEXT | Zscaler cloud name | zscaler |
| `--zscaler-username` | TEXT | Zscaler username (email) | None |
| `--zscaler-password` | TEXT | Zscaler password | None |
| `--zscaler-api-key` | TEXT | Zscaler API key | None |
| `--skip-zscaler` | FLAG | Skip Zscaler credential validation | False |
| `--help` | FLAG | Show help and exit | |

#### Examples

```bash
# Basic preflight check
zscaler-mcp-deploy preflight

# Preflight with specific region and profile
zscaler-mcp-deploy preflight --region us-west-2 --profile my-profile

# Interactive region selection
zscaler-mcp-deploy preflight --interactive

# Skip IAM validation (useful for read-only users)
zscaler-mcp-deploy preflight --skip-iam

# Skip Zscaler validation
zscaler-mcp-deploy preflight --skip-zscaler

# Full preflight with all credentials
zscaler-mcp-deploy preflight \
  --region us-east-1 \
  --zscaler-cloud zscaler \
  --zscaler-username user@example.com \
  --zscaler-password mypassword \
  --zscaler-api-key abcdef1234567890abcdef1234567890
```

### `bootstrap`

Bootstrap AWS resources for Zscaler MCP deployment (Secrets Manager secret and IAM role).

#### Usage
```bash
zscaler-mcp-deploy bootstrap [OPTIONS]
```

#### Options

| Option | Type | Description | Default |
|--------|------|-------------|---------|
| `--secret-name`, `-s` | TEXT | Name for the Secrets Manager secret | (prompted) |
| `--role-name`, `-r` | TEXT | Name for the IAM execution role | (prompted) |
| `--kms-key-id`, `-k` | TEXT | KMS key ARN for secret encryption | AWS managed key |
| `--use-existing` | FLAG | Allow using existing resources | False |
| `--region` | TEXT | AWS region | configured default |
| `--profile`, `-p` | TEXT | AWS profile name | None |
| `--username`, `-u` | TEXT | Zscaler username (email) | (prompted) |
| `--password` | TEXT | Zscaler password | (prompted) |
| `--api-key` | TEXT | Zscaler API key (32 hex chars) | (prompted) |
| `--cloud`, `-c` | TEXT | Zscaler cloud name | zscaler |
| `--description`, `-d` | TEXT | Description for created resources | Generated |
| `--non-interactive` | FLAG | Fail if required values missing | False |
| `--help` | FLAG | Show help and exit | |

#### Examples

```bash
# Interactive bootstrap
zscaler-mcp-deploy bootstrap

# Non-interactive bootstrap with all values specified
zscaler-mcp-deploy bootstrap \
  --secret-name zscaler/mcp/credentials \
  --role-name zscaler-mcp-execution-role \
  --username user@example.com \
  --password mypassword \
  --api-key abcdef1234567890abcdef1234567890 \
  --region us-east-1 \
  --non-interactive

# Use existing resources (idempotent operation)
zscaler-mcp-deploy bootstrap \
  --secret-name zscaler/mcp/credentials \
  --role-name zscaler-mcp-execution-role \
  --username user@example.com \
  --password mypassword \
  --api-key abcdef1234567890abcdef1234567890 \
  --use-existing \
  --non-interactive

# Use custom KMS key for encryption
zscaler-mcp-deploy bootstrap \
  --secret-name zscaler/mcp/credentials \
  --role-name zscaler-mcp-execution-role \
  --kms-key-id arn:aws:kms:us-east-1:123456789012:key/abcd1234-a123-456a-a12b-a123b4cd56ef \
  --username user@example.com \
  --password mypassword \
  --api-key abcdef1234567890abcdef1234567890 \
  --non-interactive
```

### `deploy`

Deploy Zscaler MCP server to AWS Bedrock AgentCore.

#### Usage
```bash
zscaler-mcp-deploy deploy [OPTIONS]
```

#### Options

| Option | Type | Description | Default |
|--------|------|-------------|---------|
| `--runtime-name`, `-n` | TEXT | Name for the Bedrock runtime | (prompted) |
| `--secret-name`, `-s` | TEXT | Name for the Secrets Manager secret | (prompted) |
| `--role-name`, `-r` | TEXT | Name for the IAM execution role | (prompted) |
| `--image-uri`, `-i` | TEXT | Container image URI | Official Zscaler image |
| `--enable-write-tools`, `-w` | FLAG | Enable write-capable MCP tools | False |
| `--kms-key-id`, `-k` | TEXT | KMS key ARN for secret encryption | None |
| `--region` | TEXT | AWS region | configured default |
| `--profile`, `-p` | TEXT | AWS profile name | None |
| `--username`, `-u` | TEXT | Zscaler username (email) | (prompted) |
| `--password` | TEXT | Zscaler password | (prompted) |
| `--api-key` | TEXT | Zscaler API key (32 hex chars) | (prompted) |
| `--cloud`, `-c` | TEXT | Zscaler cloud name | zscaler |
| `--description`, `-d` | TEXT | Description for created resources | Generated |
| `--non-interactive` | FLAG | Fail if required values missing | False |
| `--poll-timeout`, `-t` | INTEGER | Timeout for runtime polling (seconds) | 600 |
| `--skip-verification` | FLAG | Skip CloudWatch log verification | False |
| `--verification-timeout` | INTEGER | Timeout for verification (seconds) | 120 |
| `--help` | FLAG | Show help and exit | |

#### Examples

```bash
# Interactive deployment (recommended for first use)
zscaler-mcp-deploy deploy

# Non-interactive deployment with all values specified
zscaler-mcp-deploy deploy \
  --runtime-name my-zscaler-runtime \
  --secret-name zscaler/mcp/credentials \
  --role-name zscaler-mcp-execution-role \
  --username user@example.com \
  --password mypassword \
  --api-key abcdef1234567890abcdef1234567890 \
  --region us-east-1 \
  --non-interactive

# Deploy with write tools enabled
zscaler-mcp-deploy deploy \
  --runtime-name my-zscaler-runtime \
  --secret-name zscaler/mcp/credentials \
  --role-name zscaler-mcp-execution-role \
  --username user@example.com \
  --password mypassword \
  --api-key abcdef1234567890abcdef1234567890 \
  --enable-write-tools \
  --non-interactive

# Skip verification for faster deployment
zscaler-mcp-deploy deploy \
  --runtime-name my-zscaler-runtime \
  --secret-name zscaler/mcp/credentials \
  --role-name zscaler-mcp-execution-role \
  --username user@example.com \
  --password mypassword \
  --api-key abcdef1234567890abcdef1234567890 \
  --skip-verification \
  --non-interactive

# Custom verification timeout
zscaler-mcp-deploy deploy \
  --runtime-name my-zscaler-runtime \
  --secret-name zscaler/mcp/credentials \
  --role-name zscaler-mcp-execution-role \
  --username user@example.com \
  --password mypassword \
  --api-key abcdef1234567890abcdef1234567890 \
  --verification-timeout 300 \
  --non-interactive
```

### `help-credentials`

Show detailed help for configuring AWS and Zscaler credentials.

#### Usage
```bash
zscaler-mcp-deploy help-credentials
```

#### Examples

```bash
# Show credential configuration help
zscaler-mcp-deploy help-credentials
```

## Environment Variables

The CLI supports the following environment variables:

| Variable | Description | Equivalent Option |
|----------|-------------|-------------------|
| `AWS_PROFILE` | AWS profile name | `--profile` |
| `AWS_DEFAULT_REGION` | AWS region | `--region` |
| `ZSCALER_USERNAME` | Zscaler username | `--zscaler-username` |
| `ZSCALER_PASSWORD` | Zscaler password | `--zscaler-password` |
| `ZSCALER_API_KEY` | Zscaler API key | `--zscaler-api-key` |
| `ZSCALER_CLOUD` | Zscaler cloud name | `--zscaler-cloud` |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Preflight validation or verification failed |
| 2 | Deployment or runtime error |
| 3+ | Other errors |

## Configuration Files

### AWS Configuration

Located at `~/.aws/credentials` and `~/.aws/config`:

```ini
# ~/.aws/credentials
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY

[my-profile]
aws_access_key_id = ANOTHER_ACCESS_KEY
aws_secret_access_key = ANOTHER_SECRET_KEY
```

```ini
# ~/.aws/config
[default]
region = us-east-1
output = json

[profile my-profile]
region = us-west-2
output = table
```

### CLI Configuration

The CLI automatically uses AWS configuration. No separate configuration file is needed.

## IAM Permissions Required

### Minimum Permissions for Deployment

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "sts:GetCallerIdentity"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:CreateSecret",
                "secretsmanager:DescribeSecret",
                "secretsmanager:GetSecretValue",
                "secretsmanager:PutSecretValue"
            ],
            "Resource": "arn:aws:secretsmanager:*:*:secret:zscaler/mcp/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "iam:CreateRole",
                "iam:GetRole",
                "iam:AttachRolePolicy",
                "iam:PutRolePolicy"
            ],
            "Resource": "arn:aws:iam::*:role/zscaler-mcp-execution-role"
        },
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:CreateAgentCoreRuntime",
                "bedrock:GetAgentCoreRuntime",
                "bedrock:ListAgentCoreRuntimes"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:FilterLogEvents",
                "logs:GetLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:log-group:/aws/bedrock/*"
        }
    ]
}
```

### Permissions for Existing Resource Management

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret"
            ],
            "Resource": "arn:aws:secretsmanager:*:*:secret:zscaler/mcp/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "iam:GetRole"
            ],
            "Resource": "arn:aws:iam::*:role/zscaler-mcp-execution-role"
        }
    ]
}
```

## Resource Naming Conventions

### Default Names

| Resource | Default Name | Customizable |
|----------|--------------|--------------|
| Secrets Manager Secret | `zscaler/mcp/credentials` | Yes |
| IAM Role | `zscaler-mcp-execution-role` | Yes |
| Bedrock Runtime | (User specified) | Yes |

### Resource ARN Patterns

| Resource | ARN Pattern |
|----------|-------------|
| Secret | `arn:aws:secretsmanager:REGION:ACCOUNT:secret:zscaler/mcp/credentials-HASH` |
| Role | `arn:aws:iam::ACCOUNT:role/zscaler-mcp-execution-role` |
| Runtime | `arn:aws:bedrock:REGION:ACCOUNT:agentcore-runtime/RUNTIME_ID` |

## Troubleshooting Flow

### 1. Preflight Errors

**AWS Session Issues:**
```bash
# Check AWS configuration
aws sts get-caller-identity

# Reconfigure AWS CLI
aws configure

# Test with specific profile
aws sts get-caller-identity --profile my-profile
```

**IAM Permission Issues:**
```bash
# Check current permissions
aws sts get-caller-identity

# Test specific actions
aws secretsmanager list-secrets --max-items 1
aws iam list-roles --max-items 1
aws bedrock list-agent-runtimes --max-results 1
```

**Zscaler Credential Issues:**
```bash
# Verify Zscaler credentials in environment
echo $ZSCALER_USERNAME
echo $ZSCALER_CLOUD

# Test connectivity
ping zsapi.zscaler.net
```

### 2. Bootstrap Issues

**Secret Creation Failures:**
```bash
# Check existing secrets
aws secretsmanager list-secrets

# Delete problematic secret (if needed)
aws secretsmanager delete-secret --secret-id zscaler/mcp/credentials
```

**Role Creation Failures:**
```bash
# Check existing roles
aws iam list-roles --path-prefix /zscaler/

# Delete problematic role (if needed)
aws iam delete-role --role-name zscaler-mcp-execution-role
```

### 3. Deployment Issues

**Runtime Creation Failures:**
```bash
# Check existing runtimes
aws bedrock list-agent-runtimes

# Check CloudWatch logs
aws logs describe-log-groups --log-group-name-prefix /aws/bedrock/

# Tail logs for a specific runtime
aws logs tail /aws/bedrock/RUNTIME_ID --follow
```

### 4. Verification Issues

**Health Check Failures:**
```bash
# Check runtime status
aws bedrock get-agent-core-runtime --agent-core-runtime-id RUNTIME_ID

# Manually check logs for credential messages
aws logs filter-log-events --log-group-name /aws/bedrock/RUNTIME_ID --filter-pattern "credential"

# Look for startup messages
aws logs filter-log-events --log-group-name /aws/bedrock/RUNTIME_ID --filter-pattern "MCP server started"
```

## Best Practices

### 1. Security

- Always use IAM roles with least-privilege permissions
- Store credentials in AWS Secrets Manager, not environment variables
- Enable KMS encryption for sensitive data
- Disable write tools unless explicitly needed

### 2. Operations

- Use descriptive names for resources
- Tag resources for cost tracking
- Monitor CloudWatch logs for health indicators
- Regular rotation of Zscaler API keys

### 3. Development

- Test with `--skip-verification` for faster iterations
- Use `--poll-timeout` and `--verification-timeout` appropriately
- Keep CLI updated to latest version
- Use `--non-interactive` in automated environments

### 4. Troubleshooting

- Always run preflight before deployment
- Check IAM permissions when getting AccessDenied errors
- Monitor CloudWatch logs for runtime health
- Use `--help` to understand all available options