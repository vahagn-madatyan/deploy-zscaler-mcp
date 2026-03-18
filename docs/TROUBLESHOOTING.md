# Troubleshooting Guide

Common issues, error messages, and resolution strategies for Zscaler MCP Deployer.

## Table of Contents

- [Preflight Validation Issues](#preflight-validation-issues)
- [Bootstrap Issues](#bootstrap-issues)
- [Deployment Issues](#deployment-issues)
- [Verification Issues](#verification-issues)
- [Connection Issues](#connection-issues)
- [AWS-Specific Issues](#aws-specific-issues)
- [Zscaler-Specific Issues](#zscaler-specific-issues)
- [Performance Issues](#performance-issues)
- [Advanced Debugging](#advanced-debugging)

## Preflight Validation Issues

### AWS Credential Errors

**Error:** "No AWS credentials found in your environment"
**Solution:** Configure AWS credentials
```bash
aws configure
# Or set environment variables:
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

**Error:** "The specified AWS profile could not be found"
**Solution:** Check profile name or create new profile
```bash
aws configure --profile your-profile-name
aws configure list-profiles
```

**Error:** "The AWS access key ID you provided is invalid"
**Solution:** Verify access key
```bash
# Check current credentials
aws sts get-caller-identity

# Reconfigure if needed
aws configure
```

**Error:** "AWS signature validation failed"
**Solution:** Verify secret access key
```bash
# Reconfigure AWS CLI
aws configure
```

**Error:** "Your AWS credentials are valid but lack basic permissions"
**Solution:** Add required IAM permissions
```bash
# Test basic permission
aws sts get-caller-identity

# Add PowerUserAccess or custom policy
aws iam attach-user-policy --user-name your-user --policy-arn arn:aws:iam::aws:policy/PowerUserAccess
```

### AWS Region Issues

**Error:** "No AWS region was specified"
**Solution:** Specify region
```bash
zscaler-mcp-deploy preflight --region us-east-1
# Or set environment variable:
export AWS_DEFAULT_REGION=us-east-1
```

**Error:** "The specified AWS region does not support Amazon Bedrock"
**Solution:** Use supported region
```bash
# Supported regions include: us-east-1, us-west-2, eu-west-1
zscaler-mcp-deploy preflight --region us-east-1
```

### IAM Permission Errors

**Error:** "Required AWS permissions are missing"
**Solution:** Add required IAM permissions
```bash
# Check current permissions
aws sts get-caller-identity

# Test specific service permissions
aws secretsmanager list-secrets --max-items 1
aws iam list-roles --max-items 1
aws bedrock list-agent-runtimes --max-results 1
```

### Zscaler Credential Errors

**Error:** "Required Zscaler credentials were not provided"
**Solution:** Provide all required credentials
```bash
zscaler-mcp-deploy preflight --zscaler-username user@company.com --zscaler-password your_password --zscaler-api-key your_api_key
# Or set environment variables:
export ZSCALER_USERNAME=user@company.com
export ZSCALER_PASSWORD=your_password
export ZSCALER_API_KEY=your_32_char_api_key
```

**Error:** "Zscaler username must be a valid email address"
**Solution:** Use email format for username
```bash
zscaler-mcp-deploy preflight --zscaler-username user@company.com
```

**Error:** "Zscaler API key must be 32 hexadecimal characters"
**Solution:** Verify API key format
```bash
# API key should be 32 hex characters like: 1a2b3c4d5e6f78901234567890abcdef
echo $ZSCALER_API_KEY
```

**Error:** "Unable to authenticate with Zscaler API"
**Solution:** Verify all credentials
```bash
# Check credentials in Zscaler admin console
# Ensure API access is enabled for your user
# Verify you're using the correct cloud name
zscaler-mcp-deploy preflight --zscaler-cloud zscaler
```

## Bootstrap Issues

### Secret Creation Failures

**Error:** "AccessDeniedException when calling the CreateSecret operation"
**Solution:** Check Secrets Manager permissions
```bash
# Test Secrets Manager permissions
aws secretsmanager list-secrets

# If denied, add required permissions to your IAM user/role
```

**Error:** "ResourceExistsException: The secret zscaler/mcp/credentials already exists"
**Solution:** Use existing resource or delete existing secret
```bash
# Option 1: Use existing secret with bootstrap
zscaler-mcp-deploy bootstrap --use-existing --secret-name zscaler/mcp/credentials

# Option 2: Delete existing secret (careful!)
aws secretsmanager delete-secret --secret-id zscaler/mcp/credentials
```

**Error:** "InvalidRequestException: You can't create more than 2000 secrets"
**Solution:** Clean up unused secrets
```bash
# List all secrets to identify unused ones
aws secretsmanager list-secrets

# Delete unused secrets
aws secretsmanager delete-secret --secret-id secret-name-to-delete
```

### Role Creation Failures

**Error:** "AccessDenied when calling the CreateRole operation"
**Solution:** Check IAM permissions
```bash
# Test IAM permissions
aws iam list-roles --max-items 1

# Add required IAM permissions to your user/role
```

**Error:** "EntityAlreadyExists: Role with name zscaler-mcp-execution-role already exists"
**Solution:** Use existing role or delete existing role
```bash
# Option 1: Use existing role
zscaler-mcp-deploy bootstrap --use-existing --role-name zscaler-mcp-execution-role

# Option 2: Delete existing role (careful! Ensure it's not in use)
aws iam delete-role --role-name zscaler-mcp-execution-role
```

**Error:** "InvalidClientTokenId: The security token included in the request is invalid"
**Solution:** Check AWS credentials and region
```bash
# Verify credentials
aws sts get-caller-identity

# Verify region
echo $AWS_DEFAULT_REGION
```

## Deployment Issues

### Runtime Creation Failures

**Error:** "AccessDenied when calling the CreateAgentCoreRuntime operation"
**Solution:** Check Bedrock permissions
```bash
# Test Bedrock permissions
aws bedrock list-agent-runtimes --max-results 1

# Add required Bedrock permissions to your IAM user/role
```

**Error:** "InvalidParameterValue: Runtime name must be between 1 and 64 characters"
**Solution:** Use valid runtime name
```bash
# Runtime name must be 1-64 alphanumeric characters and hyphens
zscaler-mcp-deploy deploy --runtime-name my-zscaler-runtime-001
```

**Error:** "ImageNotFoundException: The specified image could not be found"
**Solution:** Check image URI or use default
```bash
# Omit --image-uri to use the default official Zscaler image
# Or verify custom image URI
aws ecr describe-images --repository-name your-repo-name
```

### Polling Timeouts

**Error:** "Runtime creation timed out"
**Solution:** Increase timeout or check runtime status
```bash
# Increase poll timeout
zscaler-mcp-deploy deploy --poll-timeout 1200

# Check runtime status manually
aws bedrock list-agent-runtimes
```

**Error:** "Runtime status is CREATE_FAILED"
**Solution:** Check CloudWatch logs for details
```bash
# Check CloudWatch logs for error details
aws logs describe-log-groups --log-group-name-prefix /aws/bedrock/

# Tail logs for the specific runtime
aws logs tail /aws/bedrock/YOUR_RUNTIME_ID --follow
```

## Verification Issues

### Health Check Failures

**Error:** "Runtime verification failed: No health indicators found"
**Solution:** Extend verification timeout or check logs
```bash
# Increase verification timeout
zscaler-mcp-deploy deploy --verification-timeout 300

# Manually check logs for credential messages
aws logs filter-log-events --log-group-name /aws/bedrock/YOUR_RUNTIME_ID --filter-pattern "credential"
```

**Error:** "Runtime verification failed: Error connecting to log stream"
**Solution:** Check CloudWatch permissions
```bash
# Test CloudWatch Logs permissions
aws logs describe-log-groups --log-group-name-prefix /aws/bedrock/

# Add required CloudWatch Logs permissions to your IAM user/role
```

### Log Analysis

**No credential messages found:**
```bash
# Check if container is starting properly
aws logs tail /aws/bedrock/YOUR_RUNTIME_ID --filter-pattern "ERROR"

# Look for startup issues
aws logs filter-log-events --log-group-name /aws/bedrock/YOUR_RUNTIME_ID --filter-pattern "startup failed"
```

**Authentication errors:**
```bash
# Look for Zscaler authentication issues
aws logs filter-log-events --log-group-name /aws/bedrock/YOUR_RUNTIME_ID --filter-pattern "Zscaler authentication"

# Check credential retrieval
aws logs filter-log-events --log-group-name /aws/bedrock/YOUR_RUNTIME_ID --filter-pattern "Secrets Manager"
```

## Connection Issues

### MCP Client Configuration

**Error:** "MCP server not appearing in client"
**Solution:** Verify runtime status and client configuration
```bash
# Check runtime is READY
aws bedrock get-agent-core-runtime --agent-core-runtime-id YOUR_RUNTIME_ID

# Verify AWS credentials in MCP client environment
# Check that runtime ID matches configuration
```

**Error:** "Connection timeout when invoking agent"
**Solution:** Check network connectivity and IAM permissions
```bash
# Test AWS CLI connectivity
aws sts get-caller-identity

# Check runtime endpoint
aws bedrock get-agent-core-runtime --agent-core-runtime-id YOUR_RUNTIME_ID
```

### Claude Desktop Issues

**Error:** "Command 'aws' not found"
**Solution:** Install AWS CLI
```bash
# Install AWS CLI (macOS)
brew install awscli

# Install AWS CLI (Linux)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Install AWS CLI (Windows)
# Download from https://aws.amazon.com/cli/
```

**Error:** "Invalid AWS credentials in Claude Desktop"
**Solution:** Configure AWS credentials in Claude Desktop environment
```bash
# Ensure AWS credentials are available in the environment where Claude runs
# On macOS, this might require adding credentials to ~/.aws/ or using environment variables
```

## AWS-Specific Issues

### Quota Limits

**Error:** "Service limit exceeded for Secrets Manager"
**Solution:** Request quota increase
```bash
# Check current usage
aws secretsmanager list-secrets

# Request quota increase through AWS Support Center
```

**Error:** "Rate exceeded" (throttling)
**Solution:** Implement retry with exponential backoff
```bash
# The CLI already implements exponential backoff
# For manual operations, add delays between requests
sleep 1 && aws command
```

### Region Availability

**Error:** "Bedrock not available in selected region"
**Solution:** Use supported region
```bash
# Check supported regions
aws bedrock list-foundations-models --region us-east-1

# Use a supported region like: us-east-1, us-west-2, eu-west-1
```

### Cross-Account Access

**Error:** "AccessDenied for resources in another account"
**Solution:** Ensure cross-account IAM permissions
```bash
# Ensure your IAM role has permissions in the target account
# This typically requires resource-based policies or cross-account roles
```

## Zscaler-Specific Issues

### Cloud Selection

**Error:** "Unknown Zscaler cloud specified"
**Solution:** Use correct cloud name
```bash
# Valid cloud names:
# zscaler (default), zscalerone, zscalertwo, zscalerthree, zscalergov, zscalerten

zscaler-mcp-deploy preflight --zscaler-cloud zscaler
```

### API Key Issues

**Error:** "API key has expired or been revoked"
**Solution:** Generate new API key
```bash
# Generate new API key in Zscaler admin console
# Navigate to Administration > API Keys
```

**Error:** "API key rate limit exceeded"
**Solution:** Add delays or use multiple keys
```bash
# The Zscaler MCP server handles rate limiting automatically
# For high-volume operations, consider timing requests appropriately
```

### Network Connectivity

**Error:** "Unable to connect to Zscaler cloud"
**Solution:** Check network and proxy settings
```bash
# Test connectivity to Zscaler
ping zsapi.zscaler.net

# Check for proxy settings that might interfere
echo $HTTP_PROXY
echo $HTTPS_PROXY
```

## Performance Issues

### Slow Deployments

**Solution:** Optimize timeouts and check resource availability
```bash
# Increase timeouts for slow environments
zscaler-mcp-deploy deploy --poll-timeout 1800 --verification-timeout 300

# Check AWS service health
aws health describe-events --service-names BEDROCK
```

### High Resource Usage

**Solution:** Monitor and optimize
```bash
# Check CloudWatch metrics for the runtime
aws cloudwatch list-metrics --namespace AWS/Bedrock

# Monitor log volume
aws logs describe-log-groups --log-group-name-prefix /aws/bedrock/
```

## Advanced Debugging

### Enable Verbose Logging

```bash
# Set AWS CLI to debug mode
export AWS_DEBUG=true

# Enable detailed CloudWatch logging
aws logs tail /aws/bedrock/YOUR_RUNTIME_ID --follow
```

### Manual Resource Verification

```bash
# Check secret
aws secretsmanager describe-secret --secret-id zscaler/mcp/credentials

# Check role
aws iam get-role --role-name zscaler-mcp-execution-role

# Check runtime
aws bedrock get-agent-core-runtime --agent-core-runtime-id YOUR_RUNTIME_ID

# Check logs
aws logs describe-log-streams --log-group-name /aws/bedrock/YOUR_RUNTIME_ID
```

### Cleanup Resources

If deployment fails and you need to clean up:

```bash
# Delete runtime (if created)
aws bedrock delete-agent-core-runtime --agent-core-runtime-id YOUR_RUNTIME_ID

# Delete role (if created)
aws iam delete-role --role-name zscaler-mcp-execution-role

# Delete secret (if created)
aws secretsmanager delete-secret --secret-id zscaler/mcp/credentials
```

### Report Issues

When reporting issues, include:

1. **Error message and traceback**
2. **CLI version:** `zscaler-mcp-deploy --version`
3. **AWS region and account info:** `aws sts get-caller-identity`
4. **Steps to reproduce**
5. **Relevant log excerpts**

## Common Error Patterns

### Pattern 1: Credential Issues
```bash
# These typically involve:
# - AWS credential configuration
# - Zscaler credential validation
# - IAM permission validation

# Debug approach:
aws sts get-caller-identity
zscaler-mcp-deploy preflight --skip-zscaler
```

### Pattern 2: Resource Creation Issues
```bash
# These typically involve:
# - IAM role creation permissions
# - Secrets Manager permissions
# - Bedrock runtime permissions

# Debug approach:
# Test individual service permissions
aws secretsmanager list-secrets --max-items 1
aws iam list-roles --max-items 1
aws bedrock list-agent-runtimes --max-results 1
```

### Pattern 3: Runtime Health Issues
```bash
# These typically involve:
# - Container startup failures
# - Credential injection problems
# - Network connectivity issues

# Debug approach:
# Check CloudWatch logs thoroughly
aws logs tail /aws/bedrock/YOUR_RUNTIME_ID --follow
aws logs filter-log-events --log-group-name /aws/bedrock/YOUR_RUNTIME_ID --filter-pattern "ERROR"
```

## Prevention Best Practices

1. **Always run preflight validation first**
2. **Use descriptive resource names**
3. **Test IAM permissions before deployment**
4. **Monitor CloudWatch logs during deployment**
5. **Keep CLI and dependencies updated**
6. **Use `--non-interactive` in automated environments**
7. **Document your resource names and configurations**

## Need Help?

If you continue to experience issues:

1. **File a GitHub issue** with:
   - Complete error message and traceback
   - CLI version (`zscaler-mcp-deploy --version`)
   - AWS region and account information
   - Steps to reproduce the issue

2. **Check AWS Service Health Dashboard**
3. **Review AWS CloudTrail logs for permission issues**
4. **Contact AWS Support** for AWS-related issues
5. **Contact Zscaler Support** for Zscaler credential/API issues