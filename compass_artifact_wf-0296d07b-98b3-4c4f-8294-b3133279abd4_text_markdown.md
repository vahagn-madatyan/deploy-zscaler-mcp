# Zscaler MCP server can't run on Cloudflare Workers Python today

**The Zscaler MCP server cannot run on Cloudflare Workers Python in its current form, and the blocking issue is fundamental: `zscaler-sdk-python` uses the synchronous `requests` library, while Workers Python only supports async HTTP clients.** This isn't a minor compatibility gap — it's an architectural mismatch between the SDK's synchronous-only design and the WebAssembly sandbox's async-only networking model. The most viable path to deploying Zscaler MCP on Cloudflare is a TypeScript reimplementation using the Cloudflare Agents SDK, which provides first-class MCP primitives. Below is the full technical analysis across all ten dimensions of the investigation.

## Python Workers are real but still in beta with sharp constraints

Cloudflare Workers Python, announced in April 2024 and updated significantly in late 2025, runs **CPython compiled to WebAssembly via Pyodide** inside V8 isolates. It remains in **open beta** and requires the `python_workers` compatibility flag. The runtime runs **Python 3.12**, tracking Pyodide's release cycle roughly 6 months behind CPython releases.

The architecture is clever: Cloudflare injects Pyodide (~6.4 MB) into a V8 isolate, scans your import statements at deploy time, executes them, then **takes a snapshot of WebAssembly linear memory** that gets deployed globally. This brings cold starts down to **~1 second** with packages like httpx, FastAPI, and pydantic imported — faster than AWS Lambda (~2.5s) and Cloud Run (~3s) for equivalent configurations. Without snapshots, the same imports would take ~10 seconds.

Resource limits are identical to JavaScript Workers: **128 MB memory** per isolate (including Pyodide overhead), **10 ms CPU** on the free plan (30 seconds to 5 minutes on paid, configurable), **3 MB compressed bundle** (free) or **10 MB** (paid), and **50 subrequests** per request on free or **1,000** on paid. The memory ceiling is particularly tight given that Pyodide itself consumes a significant portion of the 128 MB budget before your application code runs.

Networking is the critical constraint: **only asynchronous HTTP libraries work**. Specifically, only `httpx` (patched to use JavaScript's `fetch()` via Pyodide's FFI) and `aiohttp` are supported for outbound requests. The `requests` library, `urllib3`, and all synchronous socket-based networking simply cannot function in the WebAssembly sandbox. Threading, multiprocessing, subprocess, and raw socket access are all unavailable.

## FastMCP and core MCP dependencies work, but zscaler-sdk-python does not

Cloudflare has an official Python MCP server demo at `github.com/cloudflare/ai/tree/main/demos/python-workers-mcp`, announced in the April 30, 2025 blog post "Bringing streamable HTTP transport and Python language support to MCP servers." The demo uses FastMCP inside a Durable Object, with Cloudflare's built-in ASGI server replacing uvicorn. Here's the package-by-package compatibility assessment:

| Package | Works? | Notes |
|---|---|---|
| **FastMCP** | ✅ Yes | Official Cloudflare demo exists; must use ASGI app pattern, not `mcp.run()` |
| **mcp (base SDK)** | ✅ Yes | Core protocol classes function correctly on Workers |
| **mcp[cli]** | ❌ No | CLI extras require uvicorn + subprocess — both blocked |
| **httpx** | ✅ Yes | Officially supported; patched to use JS `fetch()`; **async only** |
| **starlette** | ✅ Yes | Pure Python ASGI framework; used extensively in Workers demos |
| **uvicorn** | ❌ No | Requires socket binding, process management, optional uvloop (C extension) |
| **pydantic** | ✅ Yes | Works via pure-Python fallback; Rust core (`pydantic-core`) unavailable in Wasm |
| **zscaler-sdk-python** | ❌ **Blocked** | Uses synchronous `requests` library for all HTTP calls |

The `zscaler-sdk-python` package itself ships as a pure Python wheel (`py3-none-any.whl`) with no C extensions. Its transitive dependencies are mostly benign: `cryptography` and `pyyaml` have C extensions but are both already ported to Pyodide. The fatal dependency is `requests` — the SDK's entire HTTP layer is built on synchronous `requests.Session` with retry logic that catches `requests.RequestException`. Zscaler's own documentation explicitly states: **"Zscaler APIs DO NOT support Asynchronous I/O calls"** — the SDK was architecturally designed for synchronous-only operation.

## Streamable HTTP transport works in Python, but through a different path than TypeScript

Cloudflare's Python MCP demo uses a **Durable Object pattern** where FastMCP creates an SSE or Streamable HTTP ASGI app, and the Workers runtime serves it:

```python
class FastMCPServer(DurableObject):
    def __init__(self, ctx, env):
        self.mcp = FastMCP("Demo")
        @mcp.tool()
        def calculate_bmi(weight_kg: float, height_m: float) -> float:
            return weight_kg / (height_m**2)
        self.app = mcp.sse_app()

    async def call(self, request):
        import asgi
        return await asgi.fetch(self.app, request, self.env, self.ctx)
```

Python Workers fully support `async`/`await` — the `fetch()` handler is async, Pyodide bridges JavaScript Promises to Python awaitables, and `asyncio.gather()` works for concurrent operations. SSE streaming works through Starlette's ASGI streaming responses. However, **Python Workers lack the Agents SDK features**: no `McpAgent` class, no `createMcpHandler()`, no built-in OAuth Provider integration, no Durable Object-backed session management equivalent to the TypeScript path.

For long-lived connections, standard Workers have execution time limits, but Durable Objects (which back the Python MCP demo) have no such limits. The Python demo does use Durable Objects, which are supported via FFI — but the experience is less polished than the TypeScript `McpAgent` class.

## The Agents SDK and createMcpHandler() are TypeScript-only

**`createMcpHandler()` and `McpAgent` are exclusively TypeScript constructs** — they are not available in Python. The Cloudflare Agents SDK (`github.com/cloudflare/agents`) states plainly: "An agent is a TypeScript class." It provides three TypeScript-only approaches for MCP servers:

- **`createMcpHandler()`**: Stateless MCP server using `WorkerTransport` for Streamable HTTP
- **`McpAgent`**: Durable Object per session with built-in state management, elicitation support, dual SSE/Streamable HTTP
- **Raw transport**: Full control using `@modelcontextprotocol/sdk` directly

For Python, Cloudflare offers a completely separate path: FastMCP + ASGI + Durable Objects, without the Agents SDK's convenience features. All **13+ of Cloudflare's own MCP servers** (in the `cloudflare/mcp-server-cloudflare` repository) are written in TypeScript. Every official template and quickstart guide focuses on TypeScript. The Python path is viable for simpler MCP servers but has significantly less tooling, documentation, and feature parity.

## No one has deployed a Zscaler MCP server on Cloudflare Workers in any language

Searching GitHub, Cloudflare community forums, and the broader web yields **zero examples** of the Zscaler MCP server running on Cloudflare Workers in Python or TypeScript. The closest related content is general Zscaler zero-trust integration articles about using Zscaler as a security layer in front of Workers — unrelated to MCP. The Zscaler MCP server (`github.com/zscaler/zscaler-mcp-server`) supports three transports (stdio, SSE, streamable-http) and provides 50+ tools across ZIA, ZPA, ZDX, ZCC, and ZIdentity, but it's designed for traditional server environments, not serverless edge runtimes.

## Three blocking issues prevent the Python Workers approach

**Blocker 1 — Synchronous HTTP (`requests`)**: The `zscaler-sdk-python` HTTP layer is built entirely on synchronous `requests`. Workers Python only supports async `httpx` and `aiohttp`. Fixing this requires forking the SDK and rewriting every HTTP call to use `httpx.AsyncClient`, including authentication flows, retry logic, rate limiting, and pagination. This is a substantial rewrite touching the SDK's core architecture.

**Blocker 2 — ASGI server replacement**: The Zscaler MCP server uses `uvicorn` as its ASGI server. On Workers, uvicorn cannot run (no socket binding, no process management). You'd need to replace the server entry point with Cloudflare's ASGI adapter (`asgi.fetch()`). This is less severe than Blocker 1 but still requires non-trivial restructuring.

**Blocker 3 — Serverless session model mismatch**: The `zscaler-sdk-python` maintains long-lived sessions with caching (`ZSCALER_CLIENT_CACHE_DEFAULT_TTL` defaults to 3600 seconds), authentication state, and retry counters that assume a persistent server process. Workers are fundamentally request-driven with no guaranteed instance persistence. Durable Objects could partially address this, but adapting the SDK's session management to this model adds significant complexity.

## TypeScript wrapper is the practical path forward

The TypeScript approach sidesteps every blocking issue and leverages Cloudflare's strongest MCP tooling:

| Dimension | Python Workers | TypeScript Wrapper |
|---|---|---|
| SDK dependency | Requires forked `zscaler-sdk-python` | Direct REST calls to Zscaler APIs |
| HTTP client | Must rewrite to async `httpx` | Native `fetch()` — zero friction |
| MCP framework | FastMCP via ASGI (limited features) | `McpAgent` or `EdgeFastMCP` (full features) |
| Auth/OAuth | Manual implementation | `workers-oauth-provider` library |
| State management | Durable Objects via FFI | Native Durable Objects with `McpAgent` |
| Production readiness | Beta runtime, manual vendoring | GA runtime, battle-tested |
| Cloudflare support | 1 demo, minimal docs | 13+ reference servers, extensive docs |

The TypeScript approach works because **Zscaler's APIs are standard REST/JSON endpoints**. The Python SDK is a convenience wrapper; its core value (auth management, retries, pagination, rate limiting) is straightforward to reimplement in TypeScript. Zscaler's OneAPI framework uses standard OAuth2 with a single endpoint, and the new `EdgeFastMCP` class from the TypeScript FastMCP package (`fastmcp/edge`) is explicitly designed for Cloudflare Workers with Streamable HTTP transport.

The estimated effort for a TypeScript wrapper is **2–4 weeks** for a senior developer to implement core authentication plus the 20–30 most commonly used tools, with the remaining tools being mechanical additions. Zscaler already has a platform-specific variant (`zscaler-mcp-server-bedrock` for AWS), suggesting openness to deployment-specific adaptations.

## Conclusion

The Zscaler MCP server **cannot run on Cloudflare Workers Python today**, and the fix is not simple — it requires forking and substantially rewriting `zscaler-sdk-python` to replace synchronous `requests` with async `httpx`, a change that Zscaler's own documentation suggests they don't support. Even if the HTTP layer were rewritten, Python Workers remain in beta with tighter constraints (128 MB memory including Pyodide overhead, manual package vendoring, no Agents SDK features).

The **TypeScript wrapper approach is decisively superior** for this use case. It leverages Cloudflare's most mature MCP infrastructure (`McpAgent`, Streamable HTTP, OAuth Provider, Durable Objects), avoids all Pyodide/Wasm compatibility issues, and treats Zscaler APIs as what they fundamentally are: REST endpoints that any HTTP client can call. The Python codebase serves as excellent documentation for which API endpoints to call and what parameters they expect, making the TypeScript reimplementation largely mechanical rather than creative work.