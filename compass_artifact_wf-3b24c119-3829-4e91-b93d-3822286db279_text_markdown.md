# Deploying Zscaler's MCP server remotely: architecture, patterns, and security

**The Zscaler MCP server is a Python-based, 150+ tool bridge between AI agents and Zscaler's Zero Trust Exchange that currently runs locally via stdio — but the MCP ecosystem now offers mature pathways to deploy it (and any MCP server) remotely on Cloudflare Workers, AWS Lambda, Vercel, or Docker.** The protocol's new Streamable HTTP transport, introduced in March 2025 and now the standard, replaces the deprecated SSE transport with a single-endpoint, stateless-friendly design. Cloudflare leads in hosting tooling maturity, while AWS and Vercel have production-proven solutions. The critical challenge for security-sensitive servers like Zscaler's is authentication and defense-in-depth — OAuth 2.1 with PKCE is the spec-mandated approach, and Zscaler's own nine-layer security model provides an instructive template for any remote deployment.

---

## The Zscaler MCP server exposes 150+ tools across eight product areas

The Zscaler Integrations MCP Server (`zscaler-mcp` on PyPI, **v0.6.2** as of February 2026) translates natural language into Zscaler API calls via the official `zscaler-sdk-python`. It's MIT-licensed, authored by William Da Costa Guilherme (Principal Solutions Architect at Zscaler), and works with any MCP-compatible client — Claude Desktop, Cursor, VS Code with Copilot, and others.

The architecture follows a clean layered pattern: **MCP protocol layer → server registration layer → service layer → Zscaler Python SDK → Zscaler cloud APIs**. Each Zscaler product area has its own service class (`ZIAService`, `ZPAService`, `ZDXService`, etc.) that registers tools following a verb-based naming convention like `zia_create_firewall_rule` or `zpa_list_application_segments`. Tools span eight product areas:

- **ZIA (Zscaler Internet Access)**: ~60 tools for firewall rules, URL categories, SSL inspection rules, IP destination groups, locations, admin users, network services, and cloud app control — both read and write
- **ZPA (Zscaler Private Access)**: ~60 tools for application segments, segment groups, server groups, access policies, app connectors, and service edges
- **Z-Insights Analytics**: 16 read-only tools querying Zscaler's GraphQL API for web traffic, threat categories, cyber incidents, firewall actions, shadow IT detection, and IoT device stats
- **ZDX (Digital Experience)**: 18 tools for alerts, device traces, software inventory, and performance metrics
- **ZEASM (External Attack Surface Management)**: 7 tools for findings, scan outputs, and lookalike domain detection
- **ZCC (Client Connector)**: 4 tools for device enrollment, trusted networks, and forwarding profiles
- **ZTW (Workload Segmentation)**: 20+ tools for discovery and segmentation
- **ZIdentity**: 3 tools for identity and access management

The tech stack is **Python 3.11–3.13**, built on `FastMCP ≥2.5.1` and `mcp[cli] ≥1.9.1` (the official MCP Python SDK), with `uvicorn`, `httpx`, and `starlette` handling HTTP transport. Authentication to Zscaler uses either **OneAPI** (a single OAuth 2.0 client credentials flow via ZIdentity, recommended) or **Legacy** per-service credentials. The server already supports all three transports: `--transport stdio` (default), `--transport sse`, and `--transport streamable-http`, binding to configurable `--host` and `--port` (default `127.0.0.1:8000`).

Zscaler's **nine-layer security model** is its most notable architectural decision. The server is **read-only by default** — only `list_*` and `get_*` tools are registered. Enabling writes requires two explicit gates: `--enable-write-tools` AND `--write-tools "pattern"` with wildcard-supported allowlists (e.g., `zpa_create_*`). Delete operations demand both an AI agent confirmation dialog and server-side double confirmation. All write tools carry `destructiveHint=True` metadata annotations.

---

## Streamable HTTP is the new standard for remote MCP transport

The MCP specification defines two current transport mechanisms: **stdio** (local subprocess communication via stdin/stdout) and **Streamable HTTP** (the remote transport introduced in spec version 2025-03-26). The original SSE transport was **deprecated** in March 2025 and is being phased out.

Streamable HTTP uses a **single HTTP endpoint** (e.g., `https://example.com/mcp`) that accepts POST requests with JSON-RPC messages. The server responds with either `application/json` for simple request/response patterns or `text/event-stream` for streaming responses that include progress updates, intermediate notifications, and final results. Clients can optionally open a GET stream for server-initiated messages. Session management uses an `Mcp-Session-Id` header — but critically, the transport works in fully **stateless mode** too, which enables serverless deployment with scale-to-zero.

Key protocol features for remote deployment include **resumability** (SSE event IDs with `Last-Event-ID` for reconnection), **Origin header validation** (mandatory — servers must return 403 for invalid origins to prevent DNS rebinding), and **backward compatibility detection** (clients POST an `InitializeRequest`; if it fails with 4xx, they fall back to legacy SSE). The November 2025 spec added experimental **Tasks** for async/durable requests and **polling SSE streams** where servers can disconnect at will.

Three bridge tools enable converting between transports. **Supergateway** (`npx supergateway`) wraps any stdio MCP server as SSE or Streamable HTTP with one command. **mcp-proxy** (Python, by sparfenyuk) provides bidirectional bridging and can aggregate multiple named stdio servers behind a single HTTP endpoint. **mcp-remote** (npm) does the reverse — it runs as a local stdio process forwarding to a remote HTTP server, which is the primary way clients like Claude Desktop connect to remote MCP servers today. A critical RCE vulnerability in mcp-remote was patched in v0.1.16 (June 2025); always use ≥0.1.16.

---

## Cloudflare Workers offer the most polished remote MCP hosting

Cloudflare entered remote MCP hosting in March 2025 and has built the most comprehensive platform-native tooling. Their Agents SDK provides two primary approaches:

**`createMcpHandler()`** creates stateless Streamable HTTP servers in approximately 15 lines of code. It uses the standard `@modelcontextprotocol/sdk` under the hood, wrapping it with a `WorkerTransport` class that handles HTTP request/response, SSE streaming, session management, and CORS. Deployment is one command (`npx wrangler deploy`), and the server runs at the `/mcp` endpoint on `*.workers.dev`. Zero cold starts thanks to V8 isolates make this meaningfully faster than container-based alternatives.

**`McpAgent`** creates stateful servers backed by **Durable Objects**, providing per-session persistence with a built-in SQL database and WebSocket hibernation. Sessions sleep when inactive, preserving state while reducing compute costs. This is suited for MCP servers that need to maintain conversation context across requests.

For authentication, Cloudflare provides **`@cloudflare/workers-oauth-provider`**, a purpose-built OAuth 2.1 library that handles dynamic client registration (RFC 7591), PKCE, authorization server metadata, and encrypted token storage in Workers KV. Upstream provider tokens are never exposed to MCP clients — the library issues its own tokens and maintains a secure mapping. Ready-to-deploy templates exist for GitHub OAuth, Auth0, WorkOS, Stytch, Descope, and Cloudflare Access SSO.

The main limitations are **JavaScript/TypeScript only** (no Python Workers for MCP yet), a **10ms CPU limit** on the free plan, and the V8 runtime restriction that prevents running arbitrary binaries. For a Python-based server like Zscaler's, Cloudflare Workers can't run it natively — you'd need to rewrite the tool registration layer in TypeScript while keeping the Zscaler API calls as external HTTP requests, or use a different hosting platform.

---

## AWS Lambda wraps existing stdio servers with official tooling

AWS's primary offering is **`awslabs/run-model-context-protocol-servers-with-aws-lambda`** (337+ stars), which wraps existing stdio MCP servers in Lambda functions using a `StdioServerAdapterRequestHandler`. It supports three deployment patterns: Streamable HTTP via **Amazon Bedrock AgentCore Gateway** (OAuth-authenticated), custom Streamable HTTP with **Lambda Function URLs** (SigV4/IAM-authenticated), and direct Lambda invocation. The infrastructure uses CDK with DynamoDB for session management.

**MCPEngine** (by Featureform) is an open-source Python framework specifically designed for Lambda-hosted MCP servers. It provides built-in Google OAuth/IdP authentication via an `@engine.auth()` decorator, lifecycle context management for database connection pools, and `engine.get_lambda_handler()` for Lambda-compatible entry points. Terraform scripts handle full deployment including ECR, Lambda, RDS, and IAM.

The practical challenge with Lambda is **cold starts of 2–5 seconds** when spinning up a Python runtime with the MCP server and Zscaler SDK. Provisioned concurrency mitigates this but adds cost. For Zscaler's server specifically, the Lambda approach is attractive because the server is already Python-based and the AWS Lambda handler can wrap it without code changes — the `StdioServerAdapterRequestHandler` literally spawns the stdio process inside Lambda.

Zscaler already has an **AWS Bedrock AgentCore** deployment option (`zscaler-mcp-server-bedrock`, private repo) using CloudFormation one-click deployment with credentials stored in AWS Secrets Manager, KMS encryption, and CloudTrail audit logging. This is the enterprise-ready path for AWS-native organizations.

---

## Vercel delivers the simplest deployment with production-proven results

Vercel's **`@vercel/mcp-adapter`** (also published as `mcp-handler`) provides Streamable HTTP and SSE support for Next.js, Nuxt, SvelteKit, and plain Vercel Functions. The implementation is approximately 10 lines of code — create a handler, register tools, export as GET/POST/DELETE route handlers. Production deployments include **Zapier** (mcp.zapier.com), **Composio** (mcp.composio.dev), and **Solana** (mcp.solana.com).

Vercel's **Fluid Compute** significantly reduces cold starts by reusing allocated servers, and migrating from SSE to Streamable HTTP reportedly cut CPU usage by **50%+** for production MCP servers. For SSE transport (legacy clients), Redis via Upstash handles state management; Streamable HTTP is stateless by default, requiring no external state store.

The limitation for Zscaler's Python server is that Vercel Functions are JavaScript/TypeScript-native. Running Python requires Vercel's Python runtime, which has more constrained support. The more practical approach would be to create a thin TypeScript wrapper that delegates to the Zscaler API via HTTP calls.

---

## Docker and gateway solutions provide maximum control for self-hosting

For organizations requiring full control — especially those in regulated industries or air-gapped environments — Docker-based approaches offer the most flexibility.

**Docker's MCP Gateway** (built into Docker Desktop) manages server lifecycle, routing, and authentication as a centralized proxy. It starts MCP servers as isolated containers on demand, with built-in secret management that prevents credentials from being visible even during container inspection. The standalone binary is available for Docker Engine without Desktop.

**MCPJungle** is an open-source, self-hosted MCP gateway that aggregates multiple MCP servers (both stdio and HTTP) behind a single endpoint. It supports tool groups, enable/disable controls, enterprise mode with per-client access tokens, and PostgreSQL-backed persistence. Deployment is a single `docker compose up -d`.

For converting Zscaler's stdio server to a remote Docker deployment, the most direct path is **Supergateway in a Docker container**:

```bash
docker run -p 8000:8000 supercorp/supergateway \
  --stdio "zscaler-mcp --services zia,zpa,zdx" \
  --outputTransport streamableHttp --port 8000
```

This wraps the existing Zscaler MCP server without any code changes. Add a reverse proxy (nginx, Caddy, or Traefik) with TLS termination and OAuth middleware for production use.

Enterprise gateway solutions add additional security layers. **Microsoft MCP Gateway** provides Kubernetes-native session-aware routing with Azure Entra ID authentication. **IBM ContextForge** offers federated gateway support for MCP, A2A, and REST/gRPC with 40+ plugins and OpenTelemetry integration. **Lasso Security's MCP Gateway** focuses specifically on security — PII detection, prompt injection defense, and comprehensive audit trails.

---

## OAuth 2.1 with PKCE is the mandatory auth standard, but real-world patterns vary

The MCP specification mandates **OAuth 2.1 with PKCE** for HTTP-based transports. The June 2025 spec update significantly strengthened the model: MCP servers are now classified as **OAuth 2.0 Resource Servers** that must serve `/.well-known/oauth-protected-resource` (RFC 9728), validate token audience claims, and require **resource indicators** (RFC 8707) to prevent token mis-redemption attacks.

The discovery flow works as follows: a client sends an initial request, receives HTTP 401 with a `WWW-Authenticate` header pointing to resource metadata, discovers the authorization server, optionally performs dynamic client registration, and then executes a standard OAuth 2.1 flow. Two grant types are supported: **Authorization Code** (with PKCE, for human users) and **Client Credentials** (for machine-to-machine).

In practice, many deployments use simpler patterns alongside OAuth. **API key/Bearer token authentication** is widely supported — Atlassian's MCP server, for instance, accepts Bearer tokens in the Authorization header configured directly in the client. FastMCP provides `BearerAuth` for Python clients, and the MCP TypeScript framework includes `APIKeyAuthProvider` and `JWTAuthProvider` built-in classes. **Mutual TLS** is recommended for enterprise zero-trust deployments, typically implemented at the service mesh layer (Istio, Linkerd) for automatic certificate rotation.

For the Zscaler MCP server specifically, remote deployment introduces unique risks. The server holds credentials to security infrastructure — **a compromised instance could manipulate firewall rules, access policies, and URL categories across an organization**. Zscaler's defense-in-depth model (read-only default, mandatory write allowlists, double delete confirmation) mitigates much of this risk, but remote exposure adds attack surface. Critical threats include SSRF during OAuth metadata discovery, session hijacking, prompt injection through tool inputs, and the "confused deputy" problem where a proxy's static client ID can be exploited.

---

## A practical deployment architecture for Zscaler's MCP server

For deploying Zscaler's MCP server remotely with proper security, the recommended architecture depends on organizational context:

**For AWS-native organizations**, the existing Bedrock AgentCore path is the most secure: CloudFormation deployment, Secrets Manager for credentials, KMS encryption, IAM-based access control, and CloudTrail audit logging. For a custom Lambda deployment, wrap the stdio server with `StdioServerAdapterRequestHandler`, front it with API Gateway, and store sessions in DynamoDB.

**For rapid prototyping or edge deployment**, a Docker-based approach using Supergateway or mcp-proxy to wrap the existing Python server requires zero code changes. Add Caddy or Traefik as a reverse proxy with automatic TLS and OAuth middleware. MCPJungle provides a more feature-rich gateway with per-client tokens and tool-level access control.

**For maximum control and security**, deploy the Docker image on ECS/Fargate or Kubernetes behind an enterprise MCP gateway (Microsoft's for Azure environments, IBM ContextForge for multi-protocol needs, or Lasso for security-focused deployments). Implement mTLS at the service mesh layer, OAuth 2.1 at the gateway, and maintain the server's built-in read-only defaults with narrowly scoped write allowlists.

Regardless of platform, five non-negotiable security measures apply: **enforce TLS 1.3** on all connections, **validate token audiences** per RFC 9728, **keep write tools disabled** unless explicitly needed with narrow allowlists, **log all tool invocations** to a SIEM with correlation IDs, and **bind to 127.0.0.1** on localhost deployments or use Origin header validation for public endpoints.

## Conclusion

The MCP ecosystem has matured rapidly — Streamable HTTP transport, platform-native hosting on Cloudflare/AWS/Vercel, and enterprise gateway solutions make remote deployment practical today. Zscaler's MCP server is architecturally well-positioned for remote deployment: it already supports Streamable HTTP transport, has Docker support, and implements defense-in-depth security. The primary gap is that wrapping it for production remote use requires adding an authentication layer (OAuth 2.1 or gateway-based), TLS termination, and audit logging infrastructure that the server doesn't bundle natively. The bridge tools (Supergateway, mcp-proxy) eliminate the need for code changes, while platform-specific solutions (AWS Bedrock AgentCore, Cloudflare's Agents SDK with a TypeScript wrapper) offer deeper integration. The MCP Transport Working Group's roadmap for June 2026 — including stateless protocols, MCP Server Cards (`.well-known/mcp.json`), and HTTP-level method routing — will further simplify remote deployment, but the current tooling is sufficient for production use today.