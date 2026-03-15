# S04: Verification & Connection Output — Research

**Date:** 2026-03-14

## Summary

Slice S04 delivers the final stage of the deployment pipeline: runtime verification via CloudWatch logs and copy-paste-ready MCP client connection instructions. This slice must consume the `DeployResult` from S03 and provide operational proof that the deployment actually works, not just that AWS accepted the creation request.

The implementation requires two primary components:
1. **Verification Engine** (`verification.py`): CloudWatch Logs integration to validate runtime health, credential injection success, and MCP server initialization
2. **Output Formatter** (`output.py`): MCP client configuration generation for Claude Desktop and Cursor

Research confirms boto3's CloudWatch Logs client provides the necessary APIs (`describe_log_streams`, `filter_log_events`) to tail runtime logs without external dependencies. MCP client configuration follows a standard JSON format across clients, differing primarily in file location and transport mode (stdio vs SSE).

**Primary Recommendation:** Build a `RuntimeVerifier` class following established S02/S03 patterns (lazy boto3 init, injected dependencies for testing, result dataclasses) that validates three health signals: (1) log stream existence, (2) credential retrieval confirmation, (3) MCP server initialization success. Pair with an `OutputFormatter` that generates platform-specific MCP configuration with clear next-step instructions.

## Recommendation

Implement S04 as two cohesive modules:

1. **`aws/cloudwatch_verifier.py`** — RuntimeVerifier class with:
   - `verify_runtime()` — Main entry point returning VerificationResult
   - Log stream discovery via `describe_log_streams` on `/aws/bedrock/{runtime_id}`
   - Event filtering via `filter_log_events` to find health indicators
   - Pattern matching for: "credential retrieved", "MCP server started", "listening"
   - Lazy boto3 client initialization (logs) following S03 pattern

2. **`output/connection_formatter.py`** — ConnectionFormatter class with:
   - `format_claude_desktop_config()` — JSON for `claude_desktop_config.json`
   - `format_cursor_config()` — JSON for Cursor MCP settings
   - `format_summary_table()` — Rich table for CLI final output
   - Copy-paste ready verification commands

3. **CLI Integration** — Extend `cli.py` `deploy` command:
   - Call verification after successful DeployResult
   - Display verification status with Rich panels
   - Output connection instructions with file paths
   - Exit codes: 0 = verified+ready, 1 = verified+failing, 2 = verification error

4. **Test Strategy** — 40+ unit tests:
   - Mock CloudWatch API responses
   - Test log pattern matching edge cases
   - Test formatter output validation
   - Integration tests with mocked AWS service chain

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| AWS CloudWatch Logs API | boto3 logs client | Native SDK, no external deps, already in project |
| Log pattern matching | Python `re` module | Standard library, sufficient for known log patterns |
| JSON config generation | Python `json` module | Standard library, cross-platform file paths via `pathlib` |
| Rich terminal output | Rich library (existing) | Already dependency, Table/Panel for structured output |
| Dataclass result patterns | `models.py` existing classes | Follow established BootstrapResult/DeployResult pattern |
| Error handling | `errors.py` hierarchy | Extend with VerificationError following existing patterns |

## Existing Code and Patterns

- `src/zscaler_mcp_deploy/aws/bedrock_runtime.py` — **Pattern to follow**: Lazy boto3 initialization via `_bedrock_client` property, injected session for testing
- `src/zscaler_mcp_deploy/deploy.py` — **Consume this**: `DeployResult` contains runtime_id, runtime_arn, endpoint_url needed for verification
- `src/zscaler_mcp_deploy/models.py` — **Extend this**: Add `VerificationResult`, `VerificationConfig` dataclasses following existing patterns
- `src/zscaler_mcp_deploy/errors.py` — **Extend this**: Add `VerificationError` with error codes S04-001-* (CloudWatch), S04-002-* (pattern matching), S04-003-* (formatter)
- `src/zscaler_mcp_deploy/messages.py` — **Pattern to follow**: `UserGuidance` class for help text, add connection help methods
- `src/zscaler_mcp_deploy/cli.py` — **Extend this**: Add verification step to deploy command success path, format final output with Rich
- `tests/test_deploy.py` — **Pattern to follow**: Mock injection for AWS clients, pytest fixtures for result objects
- `src/zscaler_mcp_deploy/aws/iam_bootstrap.py` — **Reference**: Shows CloudWatch log group ARN format `/aws/bedrock/*` for IAM permissions

## Constraints

- **Log group naming**: AWS Bedrock AgentCore uses `/aws/bedrock/{runtime_id}` log group naming convention (inferred from IAM permissions pattern)
- **Log propagation delay**: CloudWatch logs have 5-30 second delay from container start to log availability — verification must poll with backoff
- **Credential redaction**: Log messages must never be displayed with credential values — pattern match only, no message display
- **MCP transport mode**: Bedrock AgentCore uses stdio transport (TRANSPORT env var set in S03), config must reflect this
- **Cross-platform paths**: Claude Desktop config location varies: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS), `%APPDATA%/Claude/claude_desktop_config.json` (Windows), `~/.config/Claude/claude_desktop_config.json` (Linux)
- **No external verification**: Cannot actually call MCP tools during verification (would require live Zscaler API calls) — rely on log evidence only
- **Idempotency**: Verification must be safe to run multiple times (no resource creation)

## Common Pitfalls

- **Log stream not found immediately** — Container may take 30-60s to start logging; implement exponential backoff (2s → 10s) with 2-minute timeout for verification
- **Pattern matching too strict** — Log messages may change between Zscaler MCP server versions; match on keywords not exact strings, allow partial matches
- **Log group permissions** — Operator may lack `logs:FilterLogEvents` permission even if deployment succeeded; handle AccessDenied gracefully with helpful message
- **Empty log streams** — Runtime may exist but have no logs (failed before logging); distinguish "no stream" from "empty stream" from "unhealthy logs"
- **Credential injection failure** — Most common failure mode; look for error patterns like "secret not found", "authentication failed", "unable to retrieve credentials"
- **Config file already exists** — Claude Desktop may already have MCP servers configured; must merge configs, not overwrite
- **Invalid JSON in existing config** — User may have malformed config; handle parse errors with guidance to fix manually

## Open Risks

- **Log message format instability** — Zscaler MCP server logging format is not contractually guaranteed; verification may falsely report failure if log format changes. *Mitigation*: Document this risk, allow `--skip-verification` flag, focus on critical error patterns which are more stable than success messages
- **Bedrock AgentCore log group naming** — Assumed `/aws/bedrock/{runtime_id}` based on IAM permissions; actual naming could differ. *Mitigation*: Implement log group discovery via `describe_log_groups` with prefix filter, don't assume exact name
- **MCP server health without logs** — Runtime could be healthy but logs delayed; verification timeout may report false negative. *Mitigation*: Check runtime status API first (READY), then verify logs; if READY but no logs, warn rather than fail
- **Claude Desktop config path changes** — Anthropic may change config file location in future versions. *Mitigation*: Document current version compatibility (Claude Desktop 0.9+), provide manual config snippet as fallback
- **Credential injection success detection** — Cannot distinguish "credentials retrieved but invalid" from "valid credentials" without live API call. *Mitigation*: Look for successful Zscaler client initialization message, document limitation

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| boto3 CloudWatch | (builtin) | Not applicable — using existing boto3 |
| MCP Protocol | None found | Will implement based on format research |
| Rich CLI | Already installed | Using existing Rich dependency |

## Sources

- CloudWatch Logs describe_log_streams/get_log_events API (source: [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/logs.html))
- Bedrock IAM permissions pattern shows log group format `/aws/bedrock/*` (source: `src/zscaler_mcp_deploy/aws/iam_bootstrap.py` lines referencing logs:CreateLogGroup)
- S03 DeployResult provides runtime_id for log group construction (source: `src/zscaler_mcp_deploy/models.py` DeployResult class)
- MCP client configuration format (stdio transport) based on Model Context Protocol specification:
  - Claude Desktop: `~/.config/claude/claude_desktop_config.json` with `mcpServers` object
  - Each server entry needs `command`, `args`, and `env` (if needed)
  - Transport inferred from `TRANSPORT=stdio` env var set in S03
