# T02-PLAN

**Task:** Implement AWS session validation

**Steps:**
1. Create AWS session validator class
2. Handle credential chain (env vars, profile)
3. Validate Bedrock-supported regions
4. Add region selection prompt

**Must-Haves:**
- Detects missing/invalid AWS credentials
- Validates region against allowlist

**Verification:**
- `tests/test_aws_validation.py` with mocked credential failures

**Files:**
- src/zscaler_mcp_deploy/validators/aws.py
- tests/test_aws_validation.py