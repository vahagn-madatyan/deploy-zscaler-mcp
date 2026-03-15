---
estimated_steps: 7
estimated_files: 4
---

# T02: Connection Formatter

**Slice:** S04 — Verification & Connection Output
**Milestone:** M001

## Description

Implement the ConnectionFormatter class that generates copy-paste-ready MCP client configuration for Claude Desktop and Cursor. This fulfills R006 by providing operators with the exact configuration needed to connect their MCP client to the deployed Bedrock runtime. Handles cross-platform config file paths, existing config merging, and proper stdio transport configuration.

## Steps

1. **Create `output/__init__.py`** to establish output package
2. **Create `output/connection_formatter.py`** with ConnectionFormatter class
3. **Implement cross-platform config path resolution** for Claude Desktop (macOS: ~/Library/Application Support/Claude/claude_desktop_config.json, Linux: ~/.config/Claude/claude_desktop_config.json, Windows: %APPDATA%/Claude/claude_desktop_config.json)
4. **Implement format_claude_desktop_config()** generating MCP server entry with stdio transport, command/args pointing to AWS CLI bedrock-agent invoke, and env vars for runtime connection
5. **Implement format_cursor_config()** for Cursor's MCP settings format (similar structure, different file location)
6. **Implement existing config merging** — read existing file, parse JSON, add new mcpServers entry without overwriting existing servers
7. **Add connection help text to `messages.py`** for post-deployment guidance
8. **Create `tests/test_connection_formatter.py`** with 15+ unit tests

## Must-Haves

- [ ] ConnectionFormatter class with platform detection (macOS, Linux, Windows)
- [ ] format_claude_desktop_config(runtime_id, runtime_arn, region) → dict method
- [ ] format_cursor_config(runtime_id, runtime_arn, region) → dict method
- [ ] get_claude_config_path() returning pathlib.Path for current platform
- [ ] get_cursor_config_path() returning pathlib.Path for current platform
- [ ] merge_with_existing_config(new_config, existing_path) handling existing mcpServers
- [ ] Proper stdio transport configuration with AWS CLI bedrock-agent invoke command
- [ ] JSON output validation (valid MCP client config structure)
- [ ] S04-003-* error codes for formatter/config issues
- [ ] 15+ unit tests covering all platforms, config merging, error cases

## Verification

- `poetry run pytest tests/test_connection_formatter.py -v` passes with 15+ tests
- Tests cover: platform path resolution, config generation, existing config merging, JSON validation, error handling
- Generated config validates against MCP client config schema (stdio transport, command/args structure)

## Observability Impact

- Signals added/changed: Generated config dict structure logged at debug level (no secrets); file write operations logged with paths
- How a future agent inspects this: Call ConnectionFormatter.format_claude_desktop_config() and inspect returned dict; check file system for written config files
- Failure state exposed: FormatterError with S04-003-* codes for invalid existing JSON, permission denied, or platform detection failure

## Inputs

- `src/zscaler_mcp_deploy/models.py` — DeployResult provides runtime_id, runtime_arn, endpoint_url
- `src/zscaler_mcp_deploy/messages.py` — Pattern for user guidance text
- `src/zscaler_mcp_deploy/errors.py` — Pattern for formatter-specific errors
- MCP stdio transport spec — Command/args/env structure for MCP server configuration

## Expected Output

- `src/zscaler_mcp_deploy/output/__init__.py` — Package init exporting ConnectionFormatter
- `src/zscaler_mcp_deploy/output/connection_formatter.py` — ConnectionFormatter class (~200 lines)
- `tests/test_connection_formatter.py` — Unit tests (~300 lines)
- Updated `src/zscaler_mcp_deploy/messages.py` — Connection help guidance methods
- Updated `src/zscaler_mcp_deploy/errors.py` — FormatterError class
