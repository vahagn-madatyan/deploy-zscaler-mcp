---
id: T02
parent: S04
milestone: M001
provides:
  - ConnectionFormatter class for generating copy-paste-ready MCP client configs
  - Cross-platform config path resolution (macOS, Linux, Windows)
  - Existing config merging without overwriting existing servers
  - User guidance methods for connection instructions
key_files:
  - src/zscaler_mcp_deploy/output/__init__.py
  - src/zscaler_mcp_deploy/output/connection_formatter.py
  - src/zscaler_mcp_deploy/errors.py
  - src/zscaler_mcp_deploy/messages.py
  - tests/test_connection_formatter.py
key_decisions:
  - Used pathlib.Path for cross-platform path handling
  - Implemented existing config merge to preserve user's existing MCP servers
  - Used stdio transport with AWS CLI command pattern for MCP server config
  - Added S04-003-* error codes for formatter-specific issues
patterns_established:
  - Platform detection via platform.system() in __init__, stored as normalized lowercase
  - Lazy property pattern for platform checks (is_macos, is_linux, is_windows)
  - Config merge pattern: read → parse → merge mcpServers → write
  - Validation pattern: structural checks (dict → mcpServers → server fields)
observability_surfaces:
  - FormatterError with S04-003-* codes for diagnostics
  - ConnectionFormatter.validate_config() for config validation
  - ConnectionFormatter.get_config_summary() for logging config contents
  - Generated config dict structure logged at debug level (no secrets)
duration: ~25 minutes
verification_result: passed
completed_at: 2026-03-14T23:40:00Z
blocker_discovered: false
---

# T02: Connection Formatter

**Implemented ConnectionFormatter class that generates copy-paste-ready MCP client configuration for Claude Desktop and Cursor with cross-platform support and existing config merging.**

## What Happened

Implemented the ConnectionFormatter class as specified in T02-PLAN.md. The class provides operators with the exact configuration needed to connect their MCP client to the deployed Bedrock runtime. Key features include:

1. **Cross-platform config path resolution**: Automatic detection of macOS, Linux, and Windows with appropriate config file paths for both Claude Desktop and Cursor.

2. **Config generation**: format_claude_desktop_config() and format_cursor_config() methods generate proper MCP stdio transport configuration with AWS CLI bedrock-agent invoke commands.

3. **Existing config merging**: merge_with_existing_config() reads existing config files, adds new mcpServers entries without overwriting existing servers, and preserves other config keys.

4. **User guidance**: Added connection help methods to messages.py for post-deployment guidance with copy-paste-ready instructions.

5. **Error handling**: Added FormatterError class with S04-003-* error codes for platform detection failures, invalid JSON, permission errors, and unsupported platforms.

## Verification

- `poetry run pytest tests/test_connection_formatter.py -v` — **48 tests passed** (exceeds requirement of 15+)
- Tests cover: platform path resolution (12 tests), config generation (3 tests), config reading (4 tests), config merging (4 tests), config writing (5 tests), validation (7 tests), connection instructions (2 tests), JSON generation (2 tests), config summary (2 tests), messages integration (2 tests), FormatterError (2 tests)
- Full test suite: `poetry run pytest tests/ --tb=short -q` — **367 tests passed, no regressions**
- Generated config validates against MCP client config schema (stdio transport, command/args structure)

## Diagnostics

Future agents can inspect the formatter via:

```python
from zscaler_mcp_deploy.output.connection_formatter import ConnectionFormatter

formatter = ConnectionFormatter()

# Check platform
print(f"Platform: {formatter.platform}")
print(f"Is macOS: {formatter.is_macos()}")

# Get config paths
claude_path = formatter.get_claude_config_path()
cursor_path = formatter.get_cursor_config_path()

# Generate config
config = formatter.format_claude_desktop_config(
    runtime_id="my-runtime",
    runtime_arn="arn:aws:bedrock:us-east-1:123456789:agentcore-runtime/my-runtime",
    region="us-east-1"
)

# Validate config structure
is_valid = formatter.validate_config(config)

# Get summary for logging
summary = formatter.get_config_summary(config)
print(f"Servers: {summary['server_count']}")

# Write config to file (with merge)
formatter.write_claude_config(config, merge=True)
```

Error codes for troubleshooting:
- `S04-003-001`: Invalid existing config JSON
- `S04-003-002`: Permission denied writing config file
- `S04-003-003`: Platform detection failure (missing env var)
- `S04-003-004`: Unsupported platform
- `S04-003-005`: Config merge conflict

## Deviations

None. Implementation followed T02-PLAN.md specification exactly.

## Known Issues

None. All 48 tests pass and the full test suite (367 tests) shows no regressions.

## Files Created/Modified

- `src/zscaler_mcp_deploy/output/__init__.py` — Package init exporting ConnectionFormatter and FormatterError
- `src/zscaler_mcp_deploy/output/connection_formatter.py` — ConnectionFormatter class (~450 lines) with platform detection, config generation, merging, validation
- `src/zscaler_mcp_deploy/errors.py` — Added FormatterError class with S04-003-* error codes
- `src/zscaler_mcp_deploy/messages.py` — Added get_connection_help() and get_post_deploy_summary() user guidance methods
- `tests/test_connection_formatter.py` — Comprehensive test suite (48 tests, ~500 lines) covering all platforms, config merging, validation, error handling