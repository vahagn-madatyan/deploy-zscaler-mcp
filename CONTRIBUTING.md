# Contributing to Zscaler MCP Deployer

Thank you for your interest in contributing to Zscaler MCP Deployer! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Documentation](#documentation)
- [Code Style](#code-style)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)
- [Community](#community)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment
4. Create a branch for your feature or bug fix
5. Make your changes
6. Add tests if applicable
7. Commit your changes
8. Push to your fork
9. Create a pull request

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip and virtualenv
- AWS CLI configured with test credentials
- Zscaler test account credentials

### Installation

```bash
# Clone your fork
git clone https://github.com/your-username/zscaler-mcp-deployer.git
cd zscaler-mcp-deployer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
# Or:
pip install pytest pytest-cov pytest-mock typer[all] boto3 moto rich
```

### Environment Setup

Create a `.env` file for local development:

```bash
# AWS credentials for testing (use test account!)
export AWS_ACCESS_KEY_ID=your_test_access_key
export AWS_SECRET_ACCESS_KEY=your_test_secret_key
export AWS_DEFAULT_REGION=us-east-1

# Zscaler test credentials (use test account!)
export ZSCALER_USERNAME=test@example.com
export ZSCALER_PASSWORD=test_password
export ZSCALER_API_KEY=test_api_key_32_chars
export ZSCALER_CLOUD=zscaler
```

## Project Structure

```
zscaler-mcp-deployer/
├── src/
│   └── zscaler_mcp_deploy/
│       ├── __init__.py
│       ├── cli.py              # Main CLI entry point
│       ├── models.py           # Data models and types
│       ├── messages.py         # Error messages and user guidance
│       ├── errors.py           # Custom exception classes
│       ├── validators/         # Preflight validation logic
│       │   ├── aws.py
│       │   ├── iam.py
│       │   ├── region.py
│       │   └── zscaler.py
│       ├── aws/                # AWS service integration
│       │   ├── secrets_manager.py
│       │   ├── iam.py
│       │   ├── bedrock.py
│       │   └── cloudwatch.py
│       ├── bootstrap.py        # Resource bootstrap logic
│       ├── deploy.py           # Deployment orchestration
│       └── output/            # Output formatting
│           └── connection_formatter.py
├── tests/                     # Unit and integration tests
├── docs/                      # Documentation files
├── examples/                  # Example configurations
├── .github/                   # GitHub workflows and templates
├── README.md
├── CONTRIBUTING.md
├── LICENSE
├── pyproject.toml
└── requirements.txt
```

## Development Workflow

### Creating a Feature Branch

```bash
# Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/your-feature-name
```

### Running the CLI Locally

```bash
# Run directly with Python
python -m src.zscaler_mcp_deploy.cli --help

# Or install in development mode and run
pip install -e .
zscaler-mcp-deploy --help
```

### Code Development

1. **Write tests first** - Follow TDD principles
2. **Keep functions small** - Single responsibility principle
3. **Use type hints** - For better code documentation and IDE support
4. **Handle errors gracefully** - Use custom exceptions and error messages
5. **Log appropriately** - Use appropriate log levels (debug, info, warning, error)

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=src/zscaler_mcp_deploy

# Run specific test file
pytest tests/test_cli.py

# Run tests with verbose output
pytest -v

# Run tests and generate coverage report
pytest --cov=src/zscaler_mcp_deploy --cov-report=html
```

### Test Structure

Tests follow the pattern:

```python
# tests/test_example.py
import pytest
from zscaler_mcp_deploy.example import ExampleClass

def test_example_function():
    # Arrange
    example = ExampleClass()
    
    # Act
    result = example.some_method()
    
    # Assert
    assert result == expected_value
```

### Testing Best Practices

1. **Use pytest fixtures** for setup/teardown
2. **Mock external dependencies** (AWS, Zscaler APIs)
3. **Test both success and failure cases**
4. **Use descriptive test names**
5. **Keep tests independent**
6. **Test edge cases and error conditions**

### Mocking AWS Services

Use moto for AWS service mocking:

```python
import boto3
from moto import mock_secretsmanager

@mock_secretsmanager
def test_secrets_manager_function():
    client = boto3.client('secretsmanager', region_name='us-east-1')
    # Test your function that uses Secrets Manager
```

## Documentation

### Code Documentation

- Use docstrings for all public functions and classes
- Follow Google Python Style Guide for docstrings
- Document parameters, return values, and exceptions

```python
def example_function(param1: str, param2: int) -> bool:
    """Brief description of what the function does.
    
    More detailed description if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param1 is invalid
        RuntimeError: When operation fails
    """
    pass
```

### User Documentation

- Update README.md for user-facing changes
- Add new command documentation to docs/COMMANDS.md
- Update troubleshooting guides for new error conditions
- Include examples for new features

## Code Style

### Python Style Guide

Follow PEP 8 with these additions:

1. **Line length**: Maximum 88 characters (Black default)
2. **Imports**: Use isort for consistent ordering
3. **Formatting**: Use Black for automatic formatting
4. **Type hints**: Required for all function signatures
5. **Naming conventions**: Use snake_case for functions/variables, PascalCase for classes

### Tools

```bash
# Format code with Black
black src tests

# Sort imports with isort
isort src tests

# Check code style with flake8
flake8 src tests

# Run all checks
tox -e check
```

### Pre-commit Hooks

Set up pre-commit hooks for automatic code quality checks:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

## Commit Messages

Follow conventional commits format:

```
<type>(<scope>): <description>

[body]

[footer]
```

### Commit Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Test-related changes
- **chore**: Maintenance tasks
- **perf**: Performance improvements
- **ci**: CI/CD configuration changes

### Examples

```
feat(cli): add interactive deployment mode

Add new interactive mode for guided deployment process with
user prompts for required parameters.

Closes #123
```

```
fix(aws): handle IAM role creation race conditions

Prevent failures when multiple deployments attempt to create
the same IAM role simultaneously by using proper error handling.

Fixes #456
```

## Pull Request Process

### Before Submitting

1. **Run all tests** and ensure they pass
2. **Check code coverage** - maintain or improve coverage
3. **Update documentation** for user-facing changes
4. **Follow code style** guidelines
5. **Write clear commit messages**
6. **Squash related commits** into logical units

### Pull Request Template

Use the GitHub pull request template or include:

- **Description** of changes
- **Related issues** (closes #123)
- **Testing performed**
- **Breaking changes** (if any)
- **Migration guide** (if needed)

### Review Process

1. **Automated checks** - CI tests must pass
2. **Code review** - At least one maintainer review required
3. **Documentation review** - For user-facing changes
4. **Security review** - For security-sensitive changes
5. **Merge** - Squash and merge for clean history

### Merge Requirements

- All CI checks pass
- At least one approved review
- No merge conflicts
- Documentation updated
- Tests added/updated

## Release Process

### Versioning

Follow Semantic Versioning (SemVer):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Steps

1. **Update version** in `src/zscaler_mcp_deploy/__init__.py`
2. **Update CHANGELOG.md** with release notes
3. **Create GitHub release** with tag (vX.Y.Z)
4. **Publish to PyPI** via GitHub Actions
5. **Announce release** in relevant channels

### Release Notes

Include in CHANGELOG.md:

- New features
- Bug fixes
- Breaking changes
- Migration instructions
- Contributors

## Community

### Communication Channels

- **GitHub Issues** - Bug reports and feature requests
- **GitHub Discussions** - General discussion and Q&A
- **Email** - For security disclosures

### Getting Help

1. **Check documentation** first
2. **Search existing issues** 
3. **Review examples** in the repository
4. **Ask in discussions** for general questions
5. **File an issue** for bugs or feature requests

### Reporting Bugs

Include in bug reports:

1. **Description** of the issue
2. **Steps to reproduce**
3. **Expected vs actual behavior**
4. **Environment details** (OS, Python version, CLI version)
5. **Error messages** and stack traces
6. **Relevant configuration**

### Suggesting Features

1. **Problem description** - What issue are you trying to solve?
2. **Proposed solution** - How should it work?
3. **Alternatives considered** - Other approaches
4. **Use cases** - Real-world scenarios
5. **Implementation ideas** - Technical approach (optional)

## Recognition

Contributors will be recognized in:

- **CHANGELOG.md** - Release notes
- **GitHub contributors** - Automatic recognition
- **Project documentation** - For significant contributions

Thank you for contributing to Zscaler MCP Deployer!