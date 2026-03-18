# Deployment Scenarios

This guide provides practical deployment scenarios for the Zscaler MCP Deployer CLI.

## Table of Contents

- [Basic Deployment](#basic-deployment)
- [Production Deployment](#production-deployment)
- [Multi-Environment Deployment](#multi-environment-deployment)
- [Custom Configuration](#custom-configuration)
- [Automated Deployment](#automated-deployment)
- [Troubleshooting Deployment](#troubleshooting-deployment)

## Basic Deployment

For getting started quickly with default settings:

```bash
# Install the CLI
pip install zscaler-mcp-deployer

# Configure AWS credentials
aws configure

# Run interactive deployment
zscaler-mcp-deploy deploy
```

The CLI will prompt for:
- Runtime name (e.g., `zscaler-mcp-prod`)
- Secret name (defaults to `zscaler/mcp/credentials`)
- Role name (defaults to `zscaler-mcp-execution-role`)
- Zscaler credentials

## Production Deployment

For production environments with explicit configuration:

```bash
# Deploy with all parameters specified
zscaler-mcp-deploy deploy \
  --runtime-name zscaler-mcp-production \
  --secret-name zscaler/mcp/prod/credentials \
  --role-name zscaler-mcp-prod-role \
  --region us-east-1 \
  --description "Production Zscaler MCP server" \
  --enable-write-tools \
  --non-interactive

# Verify deployment
aws bedrock get-agent-core-runtime \
  --agent-core-runtime-id <runtime-id-from-output> \
  --region us-east-1
```

## Multi-Environment Deployment

Deploy separate environments with different configurations:

### Development Environment

```bash
zscaler-mcp-deploy deploy \
  --runtime-name zscaler-mcp-dev \
  --secret-name zscaler/mcp/dev/credentials \
  --role-name zscaler-mcp-dev-role \
  --region us-west-2 \
  --description "Development Zscaler MCP server" \
  --non-interactive
```

### Staging Environment

```bash
zscaler-mcp-deploy deploy \
  --runtime-name zscaler-mcp-staging \
  --secret-name zscaler/mcp/staging/credentials \
  --role-name zscaler-mcp-staging-role \
  --region us-east-1 \
  --description "Staging Zscaler MCP server" \
  --enable-write-tools \
  --non-interactive
```

### Production Environment

```bash
zscaler-mcp-deploy deploy \
  --runtime-name zscaler-mcp-prod \
  --secret-name zscaler/mcp/prod/credentials \
  --role-name zscaler-mcp-prod-role \
  --region us-east-1 \
  --description "Production Zscaler MCP server" \
  --enable-write-tools \
  --non-interactive
```

## Custom Configuration

Using custom settings for specific requirements:

### Custom KMS Key

```bash
zscaler-mcp-deploy deploy \
  --runtime-name zscaler-mcp-custom \
  --secret-name zscaler/mcp/custom/credentials \
  --role-name zscaler-mcp-custom-role \
  --kms-key-id arn:aws:kms:us-east-1:123456789012:key/abcd1234-a123-456a-a12b-a123b4cd56ef \
  --region us-east-1 \
  --description "Custom Zscaler MCP server with custom KMS key" \
  --non-interactive
```

### Specific Zscaler Cloud

```bash
zscaler-mcp-deploy deploy \
  --runtime-name zscaler-mcp-gov \
  --secret-name zscaler/mcp/gov/credentials \
  --role-name zscaler-mcp-gov-role \
  --region us-east-1 \
  --zscaler-cloud zscalergov \
  --description "Government Zscaler MCP server" \
  --non-interactive
```

### Read-Only Deployment

```bash
zscaler-mcp-deploy deploy \
  --runtime-name zscaler-mcp-readonly \
  --secret-name zscaler/mcp/readonly/credentials \
  --role-name zscaler-mcp-readonly-role \
  --region us-east-1 \
  --description "Read-only Zscaler MCP server" \
  --non-interactive
```

## Automated Deployment

For CI/CD pipelines and automated environments:

```bash
# Pre-validate environment
zscaler-mcp-deploy preflight \
  --region us-east-1 \
  --zscaler-cloud zscaler \
  --skip-zscaler  # Skip interactive credential validation

# Deploy with all parameters from environment variables
zscaler-mcp-deploy deploy \
  --runtime-name $DEPLOYMENT_NAME \
  --secret-name zscaler/mcp/$ENVIRONMENT/credentials \
  --role-name zscaler-mcp-$ENVIRONMENT-role \
  --region $AWS_REGION \
  --description "$ENVIRONMENT Zscaler MCP server" \
  --enable-write-tools \
  --non-interactive \
  --poll-timeout 900 \
  --verification-timeout 180

# Check deployment status
if [ $? -eq 0 ]; then
  echo "Deployment successful"
else
  echo "Deployment failed"
  exit 1
fi
```

## Troubleshooting Deployment

When deployments fail, use these approaches:

### Quick Redeployment

```bash
# Run preflight first to identify issues
zscaler-mcp-deploy preflight --region us-east-1

# Deploy with increased timeouts for troubleshooting
zscaler-mcp-deploy deploy \
  --runtime-name zscaler-mcp-troubleshoot \
  --secret-name zscaler/mcp/troubleshoot/credentials \
  --role-name zscaler-mcp-troubleshoot-role \
  --region us-east-1 \
  --poll-timeout 1200 \
  --verification-timeout 300 \
  --non-interactive
```

### Minimal Deployment for Testing

```bash
# Skip verification for faster iterations
zscaler-mcp-deploy deploy \
  --runtime-name zscaler-mcp-test \
  --secret-name zscaler/mcp/test/credentials \
  --role-name zscaler-mcp-test-role \
  --region us-east-1 \
  --skip-verification \
  --non-interactive
```

### Manual Cleanup

If automated cleanup fails:

```bash
# Delete runtime manually
aws bedrock delete-agent-core-runtime \
  --agent-core-runtime-id your-runtime-id \
  --region us-east-1

# Delete role manually
aws iam delete-role \
  --role-name zscaler-mcp-execution-role

# Delete secret manually
aws secretsmanager delete-secret \
  --secret-id zscaler/mcp/credentials
```

### Log Analysis

```bash
# Tail CloudWatch logs for deployment
aws logs tail /aws/bedrock/your-runtime-id \
  --follow \
  --region us-east-1

# Filter for specific error patterns
aws logs filter-log-events \
  --log-group-name /aws/bedrock/your-runtime-id \
  --filter-pattern "ERROR" \
  --region us-east-1
```

## Best Practices

### Security

1. Use separate secrets for each environment
2. Enable write tools only when necessary
3. Use custom KMS keys for enhanced security
4. Regular rotation of Zscaler API keys

### Operations

1. Use descriptive names for resources
2. Tag resources for cost allocation
3. Monitor CloudWatch logs for errors
4. Implement proper error handling in automation

### Development

1. Test with `--skip-verification` for faster iterations
2. Use different regions for isolation
3. Keep CLI updated to latest version
4. Document your deployment process

### Troubleshooting

1. Always run preflight before deployment
2. Check IAM permissions when getting AccessDenied
3. Monitor CloudWatch logs for runtime issues
4. Clean up failed resources promptly
