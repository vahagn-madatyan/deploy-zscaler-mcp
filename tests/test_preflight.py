"""
Test suite for the Zscaler MCP Deployer preflight validation.
"""
import subprocess
import sys

def test_version_command():
    """Test that the version command outputs the correct version."""
    result = subprocess.run(
        ["deploy-zscaler-mcp", "--version"],
        capture_output=True,
        text=True,
        cwd="."
    )
    assert result.returncode == 0
    assert "0.1.0" in result.stdout

def test_help_command():
    """Test that the help command works."""
    result = subprocess.run(
        ["deploy-zscaler-mcp", "--help"],
        capture_output=True,
        text=True,
        cwd="."
    )
    assert result.returncode == 0
    assert "Zscaler MCP Deployment Validator" in result.stdout

def test_preflight_command():
    """Test that the preflight command works and validates AWS credentials."""
    result = subprocess.run(
        ["deploy-zscaler-mcp", "preflight"],
        capture_output=True,
        text=True,
        cwd="."
    )
    # The command should fail due to missing AWS credentials, but should still output the validation message
    assert result.returncode == 1
    assert "Zscaler MCP Deployment Preflight Validator" in result.stdout
    assert "AWS Session" in result.stdout
    assert "No AWS credentials found" in result.stdout

def test_preflight_command_skip_iam():
    """Test that the preflight command works with IAM validation skipped."""
    result = subprocess.run(
        ["deploy-zscaler-mcp", "preflight", "--skip-iam"],
        capture_output=True,
        text=True,
        cwd="."
    )
    # The command should fail due to missing AWS credentials, but should still output the validation message
    assert result.returncode == 1
    assert "Zscaler MCP Deployment Preflight Validator" in result.stdout
    assert "AWS Session" in result.stdout
    assert "No AWS credentials found" in result.stdout

def test_preflight_help_includes_iam_option():
    """Test that the preflight help includes the IAM skip option."""
    result = subprocess.run(
        ["deploy-zscaler-mcp", "preflight", "--help"],
        capture_output=True,
        text=True,
        cwd="."
    )
    assert result.returncode == 0
    assert "--skip-iam" in result.stdout

def test_preflight_help_includes_zscaler_options():
    """Test that the preflight help includes Zscaler options."""
    result = subprocess.run(
        ["deploy-zscaler-mcp", "preflight", "--help"],
        capture_output=True,
        text=True,
        cwd="."
    )
    assert result.returncode == 0
    assert "--zscaler-cloud" in result.stdout
    assert "--zscaler-username" in result.stdout
    assert "--zscaler-password" in result.stdout
    assert "--zscaler-api-key" in result.stdout
    assert "--skip-zscaler" in result.stdout

def test_preflight_with_skip_all():
    """Test that the preflight command works with all validations skipped."""
    result = subprocess.run(
        ["deploy-zscaler-mcp", "preflight", "--skip-iam", "--skip-zscaler"],
        capture_output=True,
        text=True,
        cwd="."
    )
    # The command should fail due to missing AWS credentials, but should still output the validation message
    assert result.returncode == 1
    assert "Zscaler MCP Deployment Preflight Validator" in result.stdout
    assert "AWS Session" in result.stdout
    assert "No AWS credentials found" in result.stdout

if __name__ == "__main__":
    test_version_command()
    test_help_command()
    test_preflight_command()
    test_preflight_command_skip_iam()
    test_preflight_help_includes_iam_option()
    test_preflight_help_includes_zscaler_options()
    test_preflight_with_skip_all()
    print("All tests passed!")