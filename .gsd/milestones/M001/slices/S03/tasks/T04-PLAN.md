---
estimated_steps: 10
estimated_files: 3
---

# T04: Unit & Integration Tests

**Slice:** S03 — Bedrock Runtime Deployment
**Milestone:** M001

## Description

Create comprehensive test suite for S03 following the patterns established in S02 (117 tests across 4 files). The tests must cover BedrockRuntime creation, status polling, error handling, DeployOrchestrator flows, rollback scenarios, and CLI integration.

Test philosophy from S02: mock boto3 responses, test error paths thoroughly, verify dataclass outputs, test rollback ordering.

## Steps

1. Create `tests/test_bedrock_runtime.py` with test class `TestBedrockRuntime`
2. Write tests for: create_runtime success, create_runtime with write tools, API errors, retry logic
3. Write tests for: poll_runtime_status READY path, CREATE_FAILED path, timeout handling
4. Create `tests/test_deploy.py` with test class `TestDeployOrchestrator`
5. Write tests for: deploy success flow, runtime creation failure with rollback, bootstrap failure
6. Write tests for: partial failure scenarios, resource tracking, error propagation
7. Create `tests/test_deploy_integration.py` with end-to-end integration tests
8. Write tests for: full deploy flow with mocked AWS, error recovery, resource ordering
9. Run full test suite to ensure no regressions from S01/S02
10. Verify coverage >90% for new modules

## Must-Haves

- [ ] `test_bedrock_runtime.py` with 25+ tests covering creation, polling, errors
- [ ] `test_deploy.py` with 20+ tests covering orchestrator, rollback, edge cases
- [ ] `test_deploy_integration.py` with 15+ tests covering end-to-end flows
- [ ] Mock boto3 bedrock-agent-runtime and bedrock-agentcore-control clients
- [ ] Test coverage for all error codes S03-001-*, S03-002-*, S03-003-*
- [ ] All tests pass: `poetry run pytest tests/test_bedrock_runtime.py tests/test_deploy.py tests/test_deploy_integration.py -v`
- [ ] No regressions: full test suite passes (189+ tests)

## Verification

- `poetry run pytest tests/test_bedrock_runtime.py -v --tb=short` (25+ tests pass)
- `poetry run pytest tests/test_deploy.py -v --tb=short` (20+ tests pass)
- `poetry run pytest tests/test_deploy_integration.py -v --tb=short` (15+ tests pass)
- `poetry run pytest tests/ --tb=short` (all 250+ tests pass, no regressions)

## Observability Impact

None — this task creates tests, not runtime code.

## Inputs

- `tests/test_secrets_manager.py` — Pattern to follow for boto3 mocking
- `tests/test_bootstrap.py` — Pattern to follow for orchestrator testing
- `tests/test_bootstrap_integration.py` — Pattern to follow for integration tests
- T01, T02, T03 completed — all source code ready for testing

## Expected Output

- `tests/test_bedrock_runtime.py` — 25+ unit tests for BedrockRuntime
- `tests/test_deploy.py` — 20+ unit tests for DeployOrchestrator
- `tests/test_deploy_integration.py` — 15+ integration tests
