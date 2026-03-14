# Zscaler MCP Server — Remote Deployment Architecture
## From Local stdio to Globally Accessible Streamable HTTP

> **TL;DR** — Railway is the best hosting platform for making the Zscaler MCP server remotely accessible. One deploy button, zero repo config, ~$5/mo, full streaming support. For self-hosted: Coolify on any VPS. For enterprise: AWS Bedrock AgentCore.

---

## 1. Current State

The Zscaler MCP server (`zscaler-mcp` v0.6.2, MIT license) is a Python-based bridge between AI agents and Zscaler's Zero Trust Exchange. It exposes **150+ tools** across 8 product areas via the Model Context Protocol.

### Server Profile

| Attribute | Value |
|-----------|-------|
| Package | `zscaler-mcp` on PyPI |
| Runtime | Python 3.11–3.13 |
| Framework | FastMCP ≥2.5.1 + mcp[cli] ≥1.9.1 |
| HTTP | Synchronous `requests` via `zscaler-sdk-python` |
| Transports | stdio (default), SSE, Streamable HTTP |
| Auth to Zscaler | OneAPI OAuth 2.0 (recommended) or Legacy per-service |
| Security | 9-layer defense-in-depth, read-only by default |
| Docker | Supported |

### Product Coverage (150+ Tools)

| Product | Tools | Type |
|---------|------:|------|
| ZIA (Internet Access) | ~60 | Read + Write |
| ZPA (Private Access) | ~60 | Read + Write |
| Z-Insights Analytics | 16 | Read-only (GraphQL) |
| ZDX (Digital Experience) | 18 | Read + Write |
| ZTW (Workload Segmentation) | 20+ | Read + Write |
| ZEASM (Attack Surface) | 7 | Read-only |
| ZCC (Client Connector) | 4 | Read + Write |
| ZIdentity | 3 | Read + Write |

### Security Model (9 Layers)

1. **Read-Only Default** — Only `list_*`/`get_*` tools registered at startup
2. **Explicit Write Gate** — `--enable-write-tools` flag required
3. **Allowlist Patterns** — `--write-tools "zpa_create_*"` with wildcard support
4. **Double Delete Confirmation** — Agent dialog + server-side confirmation
5. **Destructive Hints** — `destructiveHint=True` metadata on all writes
6. **OAuth 2.1 + PKCE** — MCP spec-mandated for HTTP transport
7. **Origin Validation** — 403 on invalid Origin headers (DNS rebinding defense)
8. **TLS 1.3** — Mandatory encrypted transport
9. **Audit Logging** — All tool invocations logged with correlation IDs

---

## 2. Architecture: Server Internals

```
MCP Client (Claude Desktop / Cursor / VS Code / Custom)
    │
    │  Streamable HTTP  ←  POST /mcp  ←  JSON-RPC 2.0
    │  (or SSE / stdio)
    ▼
┌─────────────────────────────────────────────────────┐
│  TRANSPORT LAYER                                     │
│  Streamable HTTP (recommended) · SSE · stdio         │
│  uvicorn + starlette (or platform ASGI adapter)      │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  MCP PROTOCOL LAYER                                  │
│  FastMCP ≥2.5.1 · mcp[cli] ≥1.9.1                  │
│  Tool Registration · Capability Negotiation          │
│  Session Management · Mcp-Session-Id                 │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  SERVICE DISPATCH (verb-based naming)                │
│                                                      │
│  ZIAService     ZPAService     ZDXService           │
│  ZCCService     ZInsightsService  ZEASMService      │
│  ZTWService     ZIdentityService                    │
│                                                      │
│  zia_create_firewall_rule  →  ZIAService.create()   │
│  zpa_list_app_segments     →  ZPAService.list()     │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  ZSCALER PYTHON SDK (zscaler-sdk-python)             │
│  Synchronous requests.Session · OAuth 2.0            │
│  Retry logic · Rate limiting · Pagination            │
│  Session caching (TTL 3600s default)                 │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  ZSCALER ZERO TRUST EXCHANGE (Cloud APIs)            │
│  ZIA API · ZPA API · ZDX API · ZEASM API             │
│  OneAPI (OAuth 2.0 Client Credentials)               │
│  GraphQL (Z-Insights Analytics)                      │
└─────────────────────────────────────────────────────┘
```

---

## 3. Remote Deployment Architecture

### Transport: Streamable HTTP

The MCP spec (2025-03-26) defines Streamable HTTP as the standard remote transport, replacing the deprecated SSE transport. Key characteristics:

- **Single endpoint**: `POST https://your-server.com/mcp`
- **Dual response modes**: `application/json` for simple request/response, `text/event-stream` for streaming
- **Stateless-friendly**: Works without persistent sessions (serverless-compatible)
- **Session support**: Optional `Mcp-Session-Id` header for stateful sessions
- **Resumability**: SSE event IDs with `Last-Event-ID` for reconnection

The Zscaler MCP server already supports this via `--transport streamable-http`.

### Auth Layer for Remote Deployment

The MCP spec mandates OAuth 2.1 with PKCE for HTTP-based transports:

```
Client                    MCP Server              Auth Server
  │                           │                        │
  │── POST /mcp ──────────────▶                        │
  │◀── 401 WWW-Authenticate ──│                        │
  │                           │                        │
  │── GET /.well-known/oauth-protected-resource ──────▶│
  │◀── Resource metadata (RFC 9728) ──────────────────│
  │                           │                        │
  │── Authorization Code + PKCE flow ─────────────────▶│
  │◀── Access Token ──────────────────────────────────│
  │                           │                        │
  │── POST /mcp + Bearer token ▶                       │
  │◀── 200 OK (tool result) ──│                        │
```

In practice, most deployments use simpler patterns alongside OAuth: API key/Bearer tokens, or platform-native auth (Railway service tokens, AWS IAM).

### Bridge Tools (stdio → Remote)

For clients that only support stdio (Claude Desktop without mcp-remote):

| Tool | Language | Command | Purpose |
|------|----------|---------|---------|
| **Supergateway** | Node.js | `npx supergateway --stdio "zscaler-mcp" --outputTransport streamableHttp` | Wraps stdio as HTTP, zero code changes |
| **mcp-proxy** | Python | `pip install mcp-proxy` | Bidirectional stdio↔HTTP, multi-server aggregation |
| **mcp-remote** | Node.js | `npx mcp-remote https://your-server.com/mcp` | Client-side: local stdio → remote HTTP |

---

## 4. Platform Decision: Railway Wins

### Why Railway

| Criterion | Railway | Render | Fly.io | Heroku | AWS Lambda |
|-----------|:-------:|:------:|:------:|:------:|:----------:|
| Deploy button | ✅ | ✅ | ❌ | ✅ | ❌ |
| Repo config files needed | **None** | render.yaml | fly.toml | app.json | CDK/CFN |
| Clicks to deploy | **4-5** | 4-5 | 6-8 CLI | 3-4 | 8-12 |
| Always-on cost/mo | **~$5-8** | $7 flat | $2-4 | $7 | $6-8 |
| HTTP timeout | **None** | None | None | **30s ❌** | **15min** |
| Streaming HTTP | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| Docker auto-detect | ✅ | ✅ | ✅ | ✅ | Adapter needed |
| Cold starts | **None** | None | None | None | 2-5s |
| Free trial | $5 credit | Free tier (sleeps) | $0 (limited) | None | Free tier |

**Railway's killer feature: zero repo config.** The template is configured entirely in Railway's web UI — no `railway.json`, no `Procfile`, nothing added to the repository. This is critical for open-source projects where every config file adds friction.

**Heroku is eliminated** by its 30-second HTTP request timeout — many Zscaler API operations exceed this. AWS Lambda's 15-minute maximum and cold starts make it unsuitable for interactive MCP use.

### Deployment Tiers

```
┌─────────────────────────────────────────────────────────────────┐
│  COMMUNITY (One-Click)                                           │
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │  Deploy on        │  │  Deploy to        │                     │
│  │  Railway          │  │  Render            │                     │
│  │  ~$5/mo           │  │  $7/mo flat        │                     │
│  │  Zero config      │  │  render.yaml       │                     │
│  └──────────────────┘  └──────────────────┘                     │
│                                                                   │
│  ┌──────────────────┐                                            │
│  │  Prefect Horizon  │  ← FastMCP-native, FREE, OAuth built-in  │
│  │  60s deploy       │                                            │
│  └──────────────────┘                                            │
├─────────────────────────────────────────────────────────────────┤
│  SELF-HOSTED                                                      │
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │  Docker Compose   │  │  Coolify (PaaS)   │                     │
│  │  Any server       │  │  45K+ GitHub ★     │                     │
│  │  Manual TLS       │  │  Auto-SSL/Traefik  │                     │
│  └──────────────────┘  └──────────────────┘                     │
├─────────────────────────────────────────────────────────────────┤
│  ENTERPRISE                                                       │
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │  AWS Bedrock      │  │  Railway Pro      │                     │
│  │  AgentCore        │  │  $20/seat          │                     │
│  │  IAM + CloudTrail │  │  32GB RAM          │                     │
│  │  KMS encryption   │  │  Team workspaces   │                     │
│  └──────────────────┘  └──────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Cloudflare Workers: Not Viable for Python

### The Blocking Issue

Cloudflare Workers Python runs CPython via Pyodide (WebAssembly). The `zscaler-sdk-python` uses synchronous `requests` — **the one HTTP library that cannot work in the Wasm sandbox**. Only async `httpx` and `aiohttp` are supported.

| Dependency | Works on CF Workers? | Issue |
|------------|:-------------------:|-------|
| FastMCP | ✅ | Official CF demo exists |
| mcp SDK | ✅ | Core protocol works |
| httpx | ✅ | Patched to use JS `fetch()` |
| pydantic | ✅ | Pure Python fallback |
| starlette | ✅ | ASGI framework works |
| **zscaler-sdk-python** | **❌ BLOCKED** | Uses synchronous `requests` |
| **uvicorn** | **❌ BLOCKED** | No socket binding in Wasm |

### Three Fundamental Blockers

1. **Synchronous HTTP** — SDK built on `requests.Session`; Workers only allow async
2. **ASGI server** — uvicorn can't run; must use CF's ASGI adapter
3. **Session model** — SDK maintains long-lived cached sessions; Workers are stateless

### TypeScript Wrapper Alternative

A TypeScript reimplementation using Cloudflare's Agents SDK (`McpAgent` + `createMcpHandler()`) is the viable CF path — 2-4 weeks effort, calling Zscaler REST APIs directly via `fetch()`. But this loses the Python SDK's auth management, retry logic, and pagination — all of which must be reimplemented.

**Verdict: Cloudflare Workers is not the right platform for this server.**

---

## 6. Threat Model for Remote Deployment

| Threat | Severity | Mitigation |
|--------|:--------:|------------|
| SSRF via OAuth metadata discovery | HIGH | Validate all URLs, restrict to known auth servers |
| Session hijacking | HIGH | Rotate Mcp-Session-Id, bind to client fingerprint |
| Credential exposure in logs | HIGH | Redact secrets from all output, structured logging |
| DNS rebinding | MEDIUM | Origin header validation (MCP spec-mandated) |
| Prompt injection via tool inputs | MEDIUM | Input validation on all tool params before SDK calls |
| Confused deputy (proxy client ID) | MEDIUM | Per-user token scoping, resource indicators (RFC 8707) |
| Tool enumeration abuse | LOW | Rate limiting per client, tool access audit logging |

### Non-Negotiable Security Checklist

- [ ] TLS 1.3 on all connections
- [ ] Token audience validation per RFC 9728
- [ ] Write tools disabled by default (`--enable-write-tools` only when needed)
- [ ] Narrow write allowlists (`--write-tools "zia_list_*,zpa_get_*"`)
- [ ] All tool invocations logged to SIEM with correlation IDs
- [ ] Origin header validation for public endpoints
- [ ] Zscaler credentials in secrets manager (not env vars in production)
- [ ] Container runs as non-root user

---

## 7. Implementation Roadmap

### Phase 1 — Zero-Change Docker Wrap (1-2 days)

```bash
# The server already supports Streamable HTTP natively
zscaler-mcp --transport streamable-http --host 0.0.0.0 --port 8000

# Or wrap existing stdio with Supergateway
npx supergateway \
  --stdio "zscaler-mcp --services zia,zpa,zdx" \
  --outputTransport streamableHttp --port 8000
```

**Output:** Docker image exposing `/mcp` endpoint, running unchanged Python server.

### Phase 2 — Auth + TLS (2-3 days)

- Add reverse proxy (Caddy/Traefik) for automatic TLS
- Implement OAuth 2.1 middleware or API key auth at proxy layer
- Configure Origin header validation whitelist
- Move Zscaler credentials to secrets manager
- Enable structured JSON logging with correlation IDs

**Output:** Authenticated, TLS-encrypted remote endpoint with audit logging.

### Phase 3 — Platform Deploy + README Buttons (1-2 days)

- Create Railway template (web UI, no repo files)
- Create `render.yaml` for Render deploy button
- Create `docker-compose.remote.yml` for self-hosted
- Add deploy buttons to README
- Document Prefect Horizon as alternative
- Publish to Smithery.ai registry

**Output:** README with one-click deploy badges, multiple deployment paths.

### Phase 4 — Enterprise + Monitoring (3-5 days)

- AWS Bedrock AgentCore deployment (CloudFormation)
- Terraform modules for ECS/Fargate
- OpenTelemetry instrumentation
- SIEM integration for audit trail
- Rate limiting per client
- Security hardening checklist document

**Output:** Enterprise-grade deployment templates with full observability.

---

## 8. Quick Reference: Docker Compose for Self-Hosted

```yaml
version: "3.9"
services:
  zscaler-mcp:
    image: ghcr.io/zscaler/zscaler-mcp-server:latest
    # Or build from source:
    # build: .
    ports:
      - "8000:8000"
    environment:
      - ZSCALER_CLIENT_ID=${ZSCALER_CLIENT_ID}
      - ZSCALER_CLIENT_SECRET=${ZSCALER_CLIENT_SECRET}
      - ZSCALER_CLOUD=${ZSCALER_CLOUD:-zscaler}
    command: >
      zscaler-mcp
        --transport streamable-http
        --host 0.0.0.0
        --port 8000
        --services zia,zpa,zdx
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3

  # Optional: Caddy for automatic TLS
  caddy:
    image: caddy:2-alpine
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
    depends_on:
      - zscaler-mcp

volumes:
  caddy_data:
```

---

## 9. Key Decisions Summary

| Decision | Choice | Why |
|----------|--------|-----|
| Primary hosting | Railway | Zero repo config, deploy button, no HTTP timeout, ~$5/mo |
| Secondary hosting | Render | Flat-rate pricing ($7/mo), mature deploy button |
| FastMCP-native | Prefect Horizon | Free, OAuth built-in, 60s deploy, by FastMCP team |
| Self-hosted PaaS | Coolify | Open-source, auto-SSL, 45K+ GitHub stars |
| Enterprise | AWS Bedrock AgentCore | IAM, CloudTrail, KMS, microVM isolation |
| Transport | Streamable HTTP | MCP spec standard, stateless-friendly, streaming |
| CF Workers | Not viable | `zscaler-sdk-python` uses sync `requests` — blocked by Wasm |
| Auth | OAuth 2.1 + PKCE | MCP spec-mandated; API keys as practical alternative |
| Bridge tool | Supergateway | Zero code changes, Docker-ready, wraps stdio → HTTP |
