---
estimated_steps: 8
estimated_files: 3
---

# T03: CLI Verification Integration

**Slice:** S04 — Verification & Connection Output
**Milestone:** M001

## Description

Wire the RuntimeVerifier and ConnectionFormatter into the deploy command to complete the deployment pipeline. This is the user-facing integration that shows verification status, CloudWatch evidence, and copy-paste-ready connection instructions. Adds --skip-verification flag, Rich panel output, and proper exit codes for different completion states.

## Steps

1. **Extend `cli.py` deploy command** to import and call RuntimeVerifier after successful DeployResult
2. **Add --skip-verification flag** to deploy command for cases where log format is unstable
3. **Implement verification status display** using Rich panels (green for HEALTHY, yellow for UNHEALTHY/PENDING, red for ERROR)
4. **Implement connection instructions output** showing Claude Desktop and Cursor config with file paths
5. **Extend `deploy.py` DeployOrchestrator** to include verification step in deployment flow
6. **Update DeployResult** to include optional verification_result field
7. **Handle verification failures gracefully** — show error details but still output connection info (runtime exists even if unhealthy)
8. **Implement exit codes**: 0 = verified+ready, 1 = deployed+verification-failed, 2 = deployment/verification error
9. **Create `tests/test_verification_integration.py`** with 20+ end-to-end integration tests

## Must-Haves

- [ ] Deploy command calls RuntimeVerifier.verify_runtime() after successful runtime creation
- [ ] --skip-verification flag added to deploy command (passes through to skip verify step)
- [ ] Rich panel display for verification status with color coding
- [ ] Connection instructions shown with platform-appropriate config file paths
- [ ] Copy-paste-ready MCP config JSON displayed in code blocks
- [ ] DeployOrchestrator extended with verification phase
- [ ] DeployResult includes verification_result field
- [ ] Graceful handling when verification fails (still show connection info)
- [ ] Exit code 0 for verified+ready, 1 for deployed+unverified, 2 for errors
- [ ] 20+ integration tests covering success, skip, failure, and error paths

## Verification

- `poetry run pytest tests/test_verification_integration.py -v` passes with 20+ tests
- `poetry run pytest tests/ --tb=short` — Full test suite passes (300+ tests expected)
- `poetry run zscaler-mcp-deploy deploy --help` shows --skip-verification flag
- Manual test: deploy command shows verification panel and connection instructions in output

## Observability Impact

- Signals added/changed: CLI output shows verification status panel; DeployResult.phase now includes "verification" phase; exit codes indicate deployment vs verification success/failure
- How a future agent inspects this: Run deploy command and observe exit code; check CLI output for verification panel and connection instructions; inspect DeployResult.verification_result
- Failure state exposed: Exit code 1 indicates deployed but unverified (runtime exists, may need troubleshooting); exit code 2 indicates deployment or verification error; Rich panels show specific error messages with remediation guidance

## Inputs

- `src/zscaler_mcp_deploy/aws/cloudwatch_verifier.py` — RuntimeVerifier from T01
- `src/zscaler_mcp_deploy/output/connection_formatter.py` — ConnectionFormatter from T02
- `src/zscaler_mcp_deploy/deploy.py` — DeployOrchestrator from S03 to extend
- `src/zscaler_mcp_deploy/cli.py` — Deploy command from S03 to extend
- `src/zscaler_mcp_deploy/models.py` — DeployResult to extend with verification_result

## Expected Output

- Updated `src/zscaler_mcp_deploy/cli.py` — Extended deploy command with verification and output (~100 lines added)
- Updated `src/zscaler_mcp_deploy/deploy.py` — Extended DeployOrchestrator with verification step (~80 lines added)
- Updated `src/zscaler_mcp_deploy/models.py` — DeployResult with verification_result field
- `tests/test_verification_integration.py` — End-to-end integration tests (~350 lines)
- CLI now shows complete deployment pipeline: bootstrap → runtime → verification → connection instructions
