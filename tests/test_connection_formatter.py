"""
Test suite for ConnectionFormatter.

Tests platform detection, config path resolution, config generation,
merging, validation, and error handling.
"""
import json
import os
import platform
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

import pytest

from zscaler_mcp_deploy.output.connection_formatter import (
    ConnectionFormatter,
    FormatterError,
)


class TestConnectionFormatterInit:
    """Test ConnectionFormatter initialization."""

    def test_formatter_initialization(self):
        """Test creating a ConnectionFormatter instance."""
        formatter = ConnectionFormatter()
        assert formatter is not None
        assert isinstance(formatter.platform, str)

    def test_platform_property(self):
        """Test platform property returns system identifier."""
        formatter = ConnectionFormatter()
        platform_val = formatter.platform
        assert platform_val in ["darwin", "linux", "windows"]


class TestPlatformDetection:
    """Test platform detection methods."""

    def test_is_macos_true(self):
        """Test is_macos returns True on macOS."""
        with patch("zscaler_mcp_deploy.output.connection_formatter.platform.system", return_value="Darwin"):
            formatter = ConnectionFormatter()
            assert formatter.is_macos() is True
            assert formatter.is_linux() is False
            assert formatter.is_windows() is False

    def test_is_linux_true(self):
        """Test is_linux returns True on Linux."""
        with patch("zscaler_mcp_deploy.output.connection_formatter.platform.system", return_value="Linux"):
            formatter = ConnectionFormatter()
            assert formatter.is_macos() is False
            assert formatter.is_linux() is True
            assert formatter.is_windows() is False

    def test_is_windows_true(self):
        """Test is_windows returns True on Windows."""
        with patch("zscaler_mcp_deploy.output.connection_formatter.platform.system", return_value="Windows"):
            formatter = ConnectionFormatter()
            assert formatter.is_macos() is False
            assert formatter.is_linux() is False
            assert formatter.is_windows() is True


class TestConfigPathResolution:
    """Test cross-platform config path resolution."""

    def test_get_claude_config_path_macos(self):
        """Test Claude config path on macOS."""
        with patch("zscaler_mcp_deploy.output.connection_formatter.platform.system", return_value="Darwin"):
            formatter = ConnectionFormatter()
            path = formatter.get_claude_config_path()
            assert "Library/Application Support/Claude" in str(path)
            assert path.name == "claude_desktop_config.json"

    def test_get_claude_config_path_linux(self):
        """Test Claude config path on Linux."""
        with patch("zscaler_mcp_deploy.output.connection_formatter.platform.system", return_value="Linux"):
            formatter = ConnectionFormatter()
            path = formatter.get_claude_config_path()
            assert ".config/Claude" in str(path)
            assert path.name == "claude_desktop_config.json"

    def test_get_claude_config_path_windows(self):
        """Test Claude config path on Windows."""
        with patch("zscaler_mcp_deploy.output.connection_formatter.platform.system", return_value="Windows"):
            with patch.dict(os.environ, {"APPDATA": "C:\\Users\\Test\\AppData\\Roaming"}):
                formatter = ConnectionFormatter()
                path = formatter.get_claude_config_path()
                assert "Claude" in str(path)
                assert path.name == "claude_desktop_config.json"

    def test_get_claude_config_path_windows_no_appdata(self):
        """Test Claude config path error when APPDATA not set."""
        with patch("zscaler_mcp_deploy.output.connection_formatter.platform.system", return_value="Windows"):
            with patch.dict(os.environ, {}, clear=True):
                formatter = ConnectionFormatter()
                with pytest.raises(FormatterError) as exc_info:
                    formatter.get_claude_config_path()
                assert "S04-003-003" in str(exc_info.value.error_code)
                assert "APPDATA" in str(exc_info.value.message)

    def test_get_cursor_config_path_macos(self):
        """Test Cursor config path on macOS."""
        with patch("zscaler_mcp_deploy.output.connection_formatter.platform.system", return_value="Darwin"):
            formatter = ConnectionFormatter()
            path = formatter.get_cursor_config_path()
            assert ".cursor" in str(path)
            assert path.name == "mcp.json"

    def test_get_cursor_config_path_linux(self):
        """Test Cursor config path on Linux."""
        with patch("zscaler_mcp_deploy.output.connection_formatter.platform.system", return_value="Linux"):
            formatter = ConnectionFormatter()
            path = formatter.get_cursor_config_path()
            assert ".config/Cursor" in str(path)
            assert path.name == "mcp.json"

    def test_get_cursor_config_path_windows(self):
        """Test Cursor config path on Windows."""
        with patch("zscaler_mcp_deploy.output.connection_formatter.platform.system", return_value="Windows"):
            with patch.dict(os.environ, {"USERPROFILE": "C:\\Users\\Test"}):
                formatter = ConnectionFormatter()
                path = formatter.get_cursor_config_path()
                assert ".cursor" in str(path)
                assert path.name == "mcp.json"

    def test_get_cursor_config_path_windows_no_userprofile(self):
        """Test Cursor config path error when USERPROFILE not set."""
        with patch("zscaler_mcp_deploy.output.connection_formatter.platform.system", return_value="Windows"):
            with patch.dict(os.environ, {}, clear=True):
                formatter = ConnectionFormatter()
                with pytest.raises(FormatterError) as exc_info:
                    formatter.get_cursor_config_path()
                assert "S04-003-003" in str(exc_info.value.error_code)
                assert "USERPROFILE" in str(exc_info.value.message)

    def test_unsupported_platform_claude(self):
        """Test error on unsupported platform for Claude config."""
        with patch("zscaler_mcp_deploy.output.connection_formatter.platform.system", return_value="FreeBSD"):
            formatter = ConnectionFormatter()
            with pytest.raises(FormatterError) as exc_info:
                formatter.get_claude_config_path()
            assert "S04-003-004" in str(exc_info.value.error_code)
            assert "Unsupported platform" in str(exc_info.value.message)

    def test_unsupported_platform_cursor(self):
        """Test error on unsupported platform for Cursor config."""
        with patch("zscaler_mcp_deploy.output.connection_formatter.platform.system", return_value="FreeBSD"):
            formatter = ConnectionFormatter()
            with pytest.raises(FormatterError) as exc_info:
                formatter.get_cursor_config_path()
            assert "S04-003-004" in str(exc_info.value.error_code)
            assert "Unsupported platform" in str(exc_info.value.message)


class TestConfigGeneration:
    """Test MCP configuration generation."""

    def test_format_claude_desktop_config(self):
        """Test generating Claude Desktop config."""
        formatter = ConnectionFormatter()
        config = formatter.format_claude_desktop_config(
            runtime_id="test-runtime",
            runtime_arn="arn:aws:bedrock:us-east-1:123456789:agentcore-runtime/test-runtime",
            region="us-east-1"
        )

        assert "mcpServers" in config
        assert "zscaler-bedrock-runtime" in config["mcpServers"]

        server_config = config["mcpServers"]["zscaler-bedrock-runtime"]
        assert server_config["command"] == "aws"
        assert "bedrock-agent-runtime" in server_config["args"]
        assert "invoke-agent" in server_config["args"]
        assert "test-runtime" in server_config["args"]
        assert server_config["env"]["AWS_DEFAULT_REGION"] == "us-east-1"
        assert server_config["timeout"] == 300

    def test_format_claude_desktop_config_custom_timeout(self):
        """Test generating Claude Desktop config with custom timeout."""
        formatter = ConnectionFormatter()
        config = formatter.format_claude_desktop_config(
            runtime_id="test-runtime",
            runtime_arn="arn:aws:bedrock:us-east-1:123456789:agentcore-runtime/test-runtime",
            region="eu-west-1",
            timeout=600
        )

        server_config = config["mcpServers"]["zscaler-bedrock-runtime"]
        assert server_config["timeout"] == 600
        assert server_config["env"]["AWS_DEFAULT_REGION"] == "eu-west-1"

    def test_format_cursor_config(self):
        """Test generating Cursor config."""
        formatter = ConnectionFormatter()
        config = formatter.format_cursor_config(
            runtime_id="test-runtime",
            runtime_arn="arn:aws:bedrock:us-west-2:123456789:agentcore-runtime/test-runtime",
            region="us-west-2"
        )

        assert "mcpServers" in config
        assert "zscaler-bedrock-runtime" in config["mcpServers"]

        server_config = config["mcpServers"]["zscaler-bedrock-runtime"]
        assert server_config["command"] == "aws"
        assert server_config["env"]["AWS_DEFAULT_REGION"] == "us-west-2"


class TestConfigReading:
    """Test reading existing config files."""

    def test_read_existing_config_success(self, tmp_path):
        """Test reading existing valid config file."""
        formatter = ConnectionFormatter()
        config_path = tmp_path / "test_config.json"
        config_path.write_text('{"mcpServers": {"existing": {"command": "test"}}}')

        result = formatter.read_existing_config(config_path)
        assert result is not None
        assert "mcpServers" in result
        assert "existing" in result["mcpServers"]

    def test_read_existing_config_not_exists(self, tmp_path):
        """Test reading non-existent config file returns None."""
        formatter = ConnectionFormatter()
        config_path = tmp_path / "nonexistent_config.json"

        result = formatter.read_existing_config(config_path)
        assert result is None

    def test_read_existing_config_empty(self, tmp_path):
        """Test reading empty config file returns None."""
        formatter = ConnectionFormatter()
        config_path = tmp_path / "empty_config.json"
        config_path.write_text("")

        result = formatter.read_existing_config(config_path)
        assert result is None

    def test_read_existing_config_invalid_json(self, tmp_path):
        """Test reading invalid JSON config raises FormatterError."""
        formatter = ConnectionFormatter()
        config_path = tmp_path / "invalid_config.json"
        config_path.write_text("not valid json {{[")

        with pytest.raises(FormatterError) as exc_info:
            formatter.read_existing_config(config_path)
        assert "S04-003-001" in str(exc_info.value.error_code)
        assert "Invalid JSON" in str(exc_info.value.message)


class TestConfigMerging:
    """Test config merging functionality."""

    def test_merge_with_no_existing(self, tmp_path):
        """Test merge when no existing config."""
        formatter = ConnectionFormatter()
        config_path = tmp_path / "nonexistent.json"
        new_config = {"mcpServers": {"new-server": {"command": "test"}}}

        result = formatter.merge_with_existing_config(new_config, config_path)
        assert result == new_config

    def test_merge_with_existing(self, tmp_path):
        """Test merging with existing config."""
        formatter = ConnectionFormatter()
        config_path = tmp_path / "existing.json"
        existing = {"mcpServers": {"existing-server": {"command": "existing"}}}
        config_path.write_text(json.dumps(existing))

        new_config = {"mcpServers": {"new-server": {"command": "new"}}}
        result = formatter.merge_with_existing_config(new_config, config_path)

        assert "existing-server" in result["mcpServers"]
        assert "new-server" in result["mcpServers"]
        assert result["mcpServers"]["existing-server"]["command"] == "existing"
        assert result["mcpServers"]["new-server"]["command"] == "new"

    def test_merge_overwrites_existing_server(self, tmp_path):
        """Test that merge updates existing server with same name."""
        formatter = ConnectionFormatter()
        config_path = tmp_path / "existing.json"
        existing = {"mcpServers": {"zscaler-bedrock-runtime": {"command": "old"}}}
        config_path.write_text(json.dumps(existing))

        new_config = {"mcpServers": {"zscaler-bedrock-runtime": {"command": "new"}}}
        result = formatter.merge_with_existing_config(new_config, config_path)

        assert result["mcpServers"]["zscaler-bedrock-runtime"]["command"] == "new"

    def test_merge_preserves_other_keys(self, tmp_path):
        """Test merge preserves non-mcpServers keys in existing config."""
        formatter = ConnectionFormatter()
        config_path = tmp_path / "existing.json"
        existing = {
            "otherSetting": "value",
            "mcpServers": {"existing-server": {"command": "existing"}}
        }
        config_path.write_text(json.dumps(existing))

        new_config = {"mcpServers": {"new-server": {"command": "new"}}}
        result = formatter.merge_with_existing_config(new_config, config_path)

        assert result["otherSetting"] == "value"
        assert "new-server" in result["mcpServers"]


class TestConfigWriting:
    """Test config file writing."""

    def test_write_config_creates_directory(self, tmp_path):
        """Test write_config creates parent directories."""
        formatter = ConnectionFormatter()
        config_path = tmp_path / "nested" / "dirs" / "config.json"
        config = {"mcpServers": {"test": {"command": "test"}}}

        result = formatter.write_config(config, config_path, merge=False)
        assert result == config_path
        assert config_path.exists()

    def test_write_config_no_merge(self, tmp_path):
        """Test write_config without merging."""
        formatter = ConnectionFormatter()
        config_path = tmp_path / "config.json"
        config = {"mcpServers": {"test": {"command": "test"}}}

        formatter.write_config(config, config_path, merge=False)

        with open(config_path) as f:
            written = json.load(f)
        assert written == config

    def test_write_config_with_merge(self, tmp_path):
        """Test write_config with merging."""
        formatter = ConnectionFormatter()
        config_path = tmp_path / "config.json"
        existing = {"mcpServers": {"existing": {"command": "existing"}}}
        config_path.write_text(json.dumps(existing))

        new_config = {"mcpServers": {"new": {"command": "new"}}}
        formatter.write_config(new_config, config_path, merge=True)

        with open(config_path) as f:
            written = json.load(f)
        assert "existing" in written["mcpServers"]
        assert "new" in written["mcpServers"]

    def test_write_claude_config(self, tmp_path):
        """Test write_claude_config method."""
        with patch("zscaler_mcp_deploy.output.connection_formatter.platform.system", return_value="Darwin"):
            formatter = ConnectionFormatter()
            config = {"mcpServers": {"test": {"command": "test"}}}

            with patch.object(Path, "home", return_value=tmp_path):
                result = formatter.write_claude_config(config, merge=False)
                assert result.exists()
                with open(result) as f:
                    written = json.load(f)
                assert written == config

    def test_write_cursor_config(self, tmp_path):
        """Test write_cursor_config method."""
        with patch("zscaler_mcp_deploy.output.connection_formatter.platform.system", return_value="Darwin"):
            formatter = ConnectionFormatter()
            config = {"mcpServers": {"test": {"command": "test"}}}

            with patch.object(Path, "home", return_value=tmp_path):
                result = formatter.write_cursor_config(config, merge=False)
                assert result.exists()
                with open(result) as f:
                    written = json.load(f)
                assert written == config


class TestConfigValidation:
    """Test config validation."""

    def test_validate_config_valid(self):
        """Test validating correct config structure."""
        formatter = ConnectionFormatter()
        config = {
            "mcpServers": {
                "test-server": {
                    "command": "aws",
                    "args": ["arg1", "arg2"]
                }
            }
        }
        assert formatter.validate_config(config) is True

    def test_validate_config_not_dict(self):
        """Test validating non-dict config."""
        formatter = ConnectionFormatter()
        assert formatter.validate_config("not a dict") is False
        assert formatter.validate_config(["list"]) is False
        assert formatter.validate_config(123) is False

    def test_validate_config_missing_mcp_servers(self):
        """Test validating config without mcpServers."""
        formatter = ConnectionFormatter()
        config = {"otherKey": "value"}
        assert formatter.validate_config(config) is False

    def test_validate_config_mcp_servers_not_dict(self):
        """Test validating config with non-dict mcpServers."""
        formatter = ConnectionFormatter()
        config = {"mcpServers": ["not", "a", "dict"]}
        assert formatter.validate_config(config) is False

    def test_validate_config_server_missing_command(self):
        """Test validating config with server missing command."""
        formatter = ConnectionFormatter()
        config = {
            "mcpServers": {
                "test-server": {
                    "args": ["arg1"]
                }
            }
        }
        assert formatter.validate_config(config) is False

    def test_validate_config_server_missing_args(self):
        """Test validating config with server missing args."""
        formatter = ConnectionFormatter()
        config = {
            "mcpServers": {
                "test-server": {
                    "command": "aws"
                }
            }
        }
        assert formatter.validate_config(config) is False

    def test_validate_config_args_not_list(self):
        """Test validating config with non-list args."""
        formatter = ConnectionFormatter()
        config = {
            "mcpServers": {
                "test-server": {
                    "command": "aws",
                    "args": "not a list"
                }
            }
        }
        assert formatter.validate_config(config) is False


class TestConnectionInstructions:
    """Test connection instruction formatting."""

    def test_format_connection_instructions(self):
        """Test formatting connection instructions."""
        with patch("zscaler_mcp_deploy.output.connection_formatter.platform.system", return_value="Darwin"):
            formatter = ConnectionFormatter()
            instructions = formatter.format_connection_instructions(
                runtime_id="test-runtime",
                runtime_arn="arn:aws:bedrock:us-east-1:123456789:agentcore-runtime/test-runtime",
                region="us-east-1"
            )

            assert "test-runtime" in instructions
            assert "us-east-1" in instructions
            assert "MCP Client Connection Configuration" in instructions
            assert "zscaler-bedrock-runtime" in instructions

    def test_format_connection_instructions_includes_paths(self):
        """Test connection instructions include config paths."""
        with patch("zscaler_mcp_deploy.output.connection_formatter.platform.system", return_value="Darwin"):
            formatter = ConnectionFormatter()
            instructions = formatter.format_connection_instructions(
                runtime_id="test-runtime",
                runtime_arn="arn:aws:bedrock:us-east-1:123456789:agentcore-runtime/test-runtime",
                region="us-east-1"
            )

            assert "claude_desktop_config.json" in instructions
            assert "mcp.json" in instructions


class TestConfigJSONGeneration:
    """Test JSON config generation."""

    def test_generate_config_json_claude(self):
        """Test generating JSON for Claude."""
        formatter = ConnectionFormatter()
        json_str = formatter.generate_config_json(
            runtime_id="test-runtime",
            runtime_arn="arn:aws:bedrock:us-east-1:123456789:agentcore-runtime/test-runtime",
            region="us-east-1",
            client="claude"
        )

        config = json.loads(json_str)
        assert "mcpServers" in config
        assert "zscaler-bedrock-runtime" in config["mcpServers"]

    def test_generate_config_json_cursor(self):
        """Test generating JSON for Cursor."""
        formatter = ConnectionFormatter()
        json_str = formatter.generate_config_json(
            runtime_id="test-runtime",
            runtime_arn="arn:aws:bedrock:us-east-1:123456789:agentcore-runtime/test-runtime",
            region="us-east-1",
            client="cursor"
        )

        config = json.loads(json_str)
        assert "mcpServers" in config


class TestConfigSummary:
    """Test config summary generation."""

    def test_get_config_summary(self):
        """Test getting config summary."""
        formatter = ConnectionFormatter()
        config = {
            "mcpServers": {
                "server1": {
                    "command": "aws",
                    "args": ["arg1"],
                    "env": {"KEY": "value"},
                    "timeout": 300
                },
                "server2": {
                    "command": "test",
                    "args": ["arg2"]
                }
            }
        }

        summary = formatter.get_config_summary(config)
        assert summary["server_count"] == 2
        assert len(summary["servers"]) == 2
        assert summary["servers"][0]["has_env"] is True
        assert summary["servers"][0]["timeout"] == 300

    def test_get_config_summary_empty(self):
        """Test getting summary of empty config."""
        formatter = ConnectionFormatter()
        config = {"mcpServers": {}}

        summary = formatter.get_config_summary(config)
        assert summary["server_count"] == 0
        assert summary["servers"] == []


class TestMessagesIntegration:
    """Test integration with messages module."""

    def test_user_guidance_connection_help(self):
        """Test UserGuidance connection help method."""
        from zscaler_mcp_deploy.messages import UserGuidance

        help_text = UserGuidance.get_connection_help(
            runtime_id="my-runtime",
            runtime_arn="arn:aws:bedrock:us-east-1:123456789:agentcore-runtime/my-runtime",
            region="us-east-1"
        )

        assert "my-runtime" in help_text
        assert "us-east-1" in help_text
        assert "MCP Client Connection Configuration" in help_text

    def test_user_guidance_post_deploy_summary(self):
        """Test UserGuidance post-deploy summary method."""
        from zscaler_mcp_deploy.messages import UserGuidance

        summary = UserGuidance.get_post_deploy_summary(
            runtime_id="my-runtime",
            runtime_arn="arn:aws:bedrock:us-east-1:123456789:agentcore-runtime/my-runtime",
            region="us-east-1",
            verification_status="HEALTHY"
        )

        assert "my-runtime" in summary
        assert "HEALTHY" in summary
        assert "Deployment Complete!" in summary
        assert "✅" in summary


class TestFormatterError:
    """Test FormatterError exception."""

    def test_formatter_error_creation(self):
        """Test creating FormatterError."""
        error = FormatterError(
            message="Test error",
            error_code="S04-003-TEST",
            context={"key": "value"}
        )

        assert error.message == "Test error"
        assert error.error_code == "S04-003-TEST"
        assert error.context == {"key": "value"}

    def test_formatter_error_default_code(self):
        """Test FormatterError with default error code."""
        error = FormatterError(message="Test error")

        assert error.error_code == "S04-003"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])