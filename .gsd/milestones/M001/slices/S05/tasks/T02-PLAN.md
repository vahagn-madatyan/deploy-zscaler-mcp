# T02: Command Reference and Advanced Usage Documentation

## Description

Document all CLI commands in comprehensive detail, including all flags, options, examples, and advanced usage scenarios. This documentation will serve as the detailed reference for users who need to understand the full capabilities of the tool.

## Must-Haves

1. Detailed documentation for each CLI command (`preflight`, `bootstrap`, `deploy`, `help-credentials`)
2. Complete list of all flags and options with descriptions and examples
3. Usage examples for common scenarios and edge cases
4. Explanation of exit codes and their meanings
5. Documentation of interactive vs non-interactive modes
6. Examples of using existing AWS resources vs creating new ones
7. Advanced configuration scenarios and best practices

## Steps

1. Document the `preflight` command in detail:
   - All options and flags with descriptions
   - Examples of different validation scenarios
   - Explanation of validation phases and what each checks
   - Common validation failures and how to resolve them

2. Document the `bootstrap` command in detail:
   - Resource creation process and idempotent behavior
   - All configuration options and their effects
   - Examples of using existing resources vs creating new ones
   - IAM role and Secrets Manager secret structure

3. Document the `deploy` command in detail:
   - Complete deployment workflow explanation
   - All configuration options and environment variables
   - Exit code meanings and automation integration
   - Verification process and skip options
   - Rollback behavior and resource management

4. Document the `help-credentials` command:
   - Purpose and output content
   - When to use this command

5. Create advanced usage examples:
   - CI/CD integration scenarios
   - Different cloud configurations
   - Custom image URI usage
   - KMS key integration
   - Profile and region management

## Verification

- [ ] All commands are documented with complete flag listings
- [ ] Examples are tested and work as described
- [ ] Exit codes are documented with clear explanations
- [ ] Interactive and non-interactive modes are explained
- [ ] Advanced scenarios include real-world use cases
- [ ] Documentation reflects actual CLI behavior and help text

## Inputs

- Existing CLI help text (`--help` output for all commands)
- Source code implementation in `src/zscaler_mcp_deploy/cli.py`
- Test examples from `tests/test_*.py` files
- Requirements from `.gsd/REQUIREMENTS.md`

## Expected Output

- Comprehensive command reference documentation covering:
  - Detailed `preflight` command documentation
  - Detailed `bootstrap` command documentation
  - Detailed `deploy` command documentation
  - Detailed `help-credentials` command documentation
  - Advanced usage examples and scenarios
  - Exit code documentation and automation integration