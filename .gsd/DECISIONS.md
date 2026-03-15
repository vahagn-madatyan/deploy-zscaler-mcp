# Decisions Register

<!-- Append-only. Never edit or remove existing rows.
     To reverse a decision, add a new row that supersedes it.
     Read this file at the start of any planning or research phase. -->

| # | When | Scope | Decision | Choice | Rationale | Revisable? |
|---|---|---|---|---|---|---|
| D001 | M001/Discuss | platform | Primary deployment platform | AWS Bedrock AgentCore | Zscaler officially supports this path with Marketplace image and CloudFormation templates. User wants officially supported methods. | No — unless Zscaler adds new official platforms |
| D002 | M001/Discuss | ux | Deployment execution mode | Perform deployment from terminal (not just generate templates) | User wants CLI to actually deploy, not just prepare. | No — core product definition |
| D003 | M001/Discuss | ux | User experience | One command + interactive prompts | Removes friction, guides operator through required inputs. | No — core UX pattern |
| D004 | M001/Discuss | security | Credential storage | AWS Secrets Manager only (not direct env vars) | User wants strict/safest path. Secrets Manager provides KMS encryption, CloudTrail audit, rotation support. | Revisable — could add direct env vars later for testing if user requests |
| D005 | M001/Discuss | validation | Preflight strictness | Strict preflight that stops early with exact fixes | User explicitly said "strict" and "none" for assumed prerequisites. Fail fast with actionable errors. | No — core reliability pattern |
| D006 | M001/Discuss | product | Product scope | Network/security MCP deployer (not generic MCP framework) | User explicitly said "for network/security mcp", not any MCP. Keeps scope focused. | Revisable — if product direction changes |
| D007 | M001/Discuss | verification | Success criteria | Runtime up + connection steps (not just CREATE_COMPLETE) | User wants verification that it actually works, not just that AWS accepted the request. | No — defines "done" for deploy |
