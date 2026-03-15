---
estimated_steps: 4
estimated_files: 1
---

# T05: Integration Tests

**Slice:** S02 — Secrets Manager & IAM Bootstrap
**Milestone:** M001

## Description

Write comprehensive integration tests that exercise the full S02 bootstrap flow with mocked AWS services. Ensure all components work together and reach the target of 40+ new tests for S02.

## Steps

1. Create `tests/test_bootstrap_integration.py` with end-to-end tests
2. Test full success path: preflight → secret creation → role creation → result output
3. Test partial failure scenarios with rollback verification
4. Add edge case tests to reach 40+ total S02 tests across all test files
5. Verify all S02 tests pass and coverage targets are met

## Must-Haves

- [ ] End-to-end integration test with mocked AWS services
- [ ] Partial failure test with rollback verification
- [ ] Combined S02 test count of 40+ across all test files
- [ ] All tests pass with `poetry run pytest tests/`

## Verification

- `poetry run pytest tests/ --tb=short` shows 40+ new tests from S02
- `poetry run pytest tests/test_bootstrap_integration.py -v` passes
- No test failures or warnings

## Observability Impact

- Signals added/changed: Test suite providing verification of S02 behavior
- How a future agent inspects this: Run `poetry run pytest tests/ -v` and check pass/fail
- Failure state exposed: Specific test failures indicating which component failed

## Inputs

- `src/zscaler_mcp_deploy/bootstrap.py` — BootstrapOrchestrator
- `src/zscaler_mcp_deploy/cli.py` — CLI with bootstrap command
- `tests/test_secrets_manager.py` — T01 tests
- `tests/test_iam_bootstrap.py` — T02 tests
- `tests/test_bootstrap.py` — T03 tests

## Expected Output

- `tests/test_bootstrap_integration.py` — Integration tests
- Verification that S02 delivers 40+ new passing tests
