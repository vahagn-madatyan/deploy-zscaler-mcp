import { useState } from "react";

const C = {
  bg: "#06090f", s1: "#0c1018", s2: "#131a26", s3: "#1a2435",
  bd: "#1c2a3a", ba: "#00e4b8", baDim: "#00e4b822", baGlow: "#00e4b812",
  txt: "#dfe6f0", dim: "#7e91a8", mut: "#4a5e73",
  g: "#00e4b8", b: "#3d8bfd", p: "#a78bfa", pk: "#f472b6",
  o: "#fb923c", r: "#f43f5e", y: "#eab308",
};

const font = "'Azeret Mono', 'JetBrains Mono', 'Fira Code', monospace";
const sans = "'DM Sans', 'Outfit', system-ui, sans-serif";

const B = ({ children, c = C.g, s }) => (
  <span style={{ display: "inline-block", padding: "2px 9px", borderRadius: 3, fontSize: 10, fontWeight: 600, fontFamily: font, color: c, background: c + "16", border: `1px solid ${c}2a`, letterSpacing: 0.3, ...s }}>{children}</span>
);

const Li = ({ children, c = C.dim }) => (
  <div style={{ display: "flex", gap: 7, fontSize: 11.5, color: c, padding: "3px 0", lineHeight: 1.5, alignItems: "start" }}>
    <span style={{ color: C.mut, fontSize: 5, marginTop: 6, flexShrink: 0 }}>●</span>
    <span>{children}</span>
  </div>
);

const Sect = ({ children, icon, title, sub }) => (
  <div style={{ marginBottom: 28 }}>
    <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginBottom: 14, borderBottom: `1px solid ${C.bd}`, paddingBottom: 10 }}>
      <span style={{ fontSize: 15 }}>{icon}</span>
      <span style={{ fontSize: 14, fontWeight: 700, color: C.txt, fontFamily: font, textTransform: "uppercase", letterSpacing: 1 }}>{title}</span>
      {sub && <span style={{ fontSize: 10, color: C.mut, fontFamily: font }}>{sub}</span>}
    </div>
    {children}
  </div>
);

const Box = ({ children, c = C.bd, style }) => (
  <div style={{ background: C.s1, border: `1px solid ${c}`, borderRadius: 8, padding: 16, ...style }}>{children}</div>
);

const Pill = ({ children, c = C.g }) => (
  <span style={{ display: "inline-block", padding: "1px 7px", borderRadius: 3, fontSize: 9.5, fontFamily: font, color: c, background: c + "12", margin: "1.5px" }}>{children}</span>
);

const Arrow = ({ label }) => (
  <div style={{ textAlign: "center", padding: "3px 0" }}>
    <div style={{ width: 1, height: 10, background: `linear-gradient(${C.g}55, ${C.g})`, margin: "0 auto" }} />
    <div style={{ color: C.g, fontSize: 9 }}>▼</div>
    {label && <div style={{ fontSize: 8, color: C.mut, fontFamily: font, letterSpacing: 1 }}>{label}</div>}
  </div>
);

const Stat = ({ n, l, c = C.g }) => (
  <div style={{ textAlign: "center", flex: 1 }}>
    <div style={{ fontSize: 26, fontWeight: 800, color: c, fontFamily: font, lineHeight: 1 }}>{n}</div>
    <div style={{ fontSize: 9, color: C.mut, fontFamily: font, textTransform: "uppercase", letterSpacing: 1, marginTop: 4 }}>{l}</div>
  </div>
);

const tabs = [
  { id: "arch", label: "Architecture", ic: "⬡" },
  { id: "plat", label: "Hosting", ic: "☁" },
  { id: "sec", label: "Security", ic: "◈" },
  { id: "plan", label: "Deploy Plan", ic: "▸" },
  { id: "cf", label: "CF Analysis", ic: "⚡" },
];

const products = [
  { n: "ZIA", t: "~60", d: "Internet Access", c: "#3d8bfd" },
  { n: "ZPA", t: "~60", d: "Private Access", c: "#a78bfa" },
  { n: "Z-Insights", t: "16", d: "Analytics (GraphQL)", c: "#06b6d4" },
  { n: "ZDX", t: "18", d: "Digital Experience", c: "#10b981" },
  { n: "ZTW", t: "20+", d: "Workload Seg.", c: "#f97316" },
  { n: "ZEASM", t: "7", d: "Attack Surface", c: "#eab308" },
  { n: "ZCC", t: "4", d: "Client Connector", c: "#ec4899" },
  { n: "ZIdentity", t: "3", d: "IAM", c: "#8b5cf6" },
];

const platforms = [
  { id: "railway", name: "Railway", ic: "🚂", verdict: "PRIMARY", c: C.g,
    cost: "~$5-8/mo", clicks: "4-5", timeout: "None", btn: "✅ Zero config",
    pros: ["Zero repo config — template in Railway UI only", "Auto-detect Dockerfile, build, deploy", "No HTTP timeout on active connections", "Auto-SSL on *.up.railway.app", "$5 free trial, no credit card", "Per-minute billing, pay only for usage"],
    cons: ["No true free tier (trial only)", "US-only regions currently"],
    why: "Best deploy button + zero config + no timeout = perfect for MCP servers" },
  { id: "render", name: "Render", ic: "🎨", verdict: "SECONDARY", c: C.b,
    cost: "$7/mo flat", clicks: "4-5", timeout: "None", btn: "✅ render.yaml",
    pros: ["Flat-rate pricing — no surprise bills", "Mature deploy button with render.yaml", "BuildKit for Dockerfiles", "No HTTP request timeout", "Good docs for Python Docker apps"],
    cons: ["Requires render.yaml in repo", "Free tier sleeps after 15min (unusable for MCP)"],
    why: "Predictable cost, strong deploy button, but needs a config file in repo" },
  { id: "horizon", name: "Prefect Horizon", ic: "🌅", verdict: "FASTMCP-NATIVE", c: C.p,
    cost: "Free", clicks: "3 steps", timeout: "None", btn: "❌ Coming soon",
    pros: ["Built by FastMCP creators — native support", "Free for personal projects", "OAuth 2.1 built-in automatically", "60-second deploy time", "PR preview deployments", "Tool inspector + monitoring"],
    cons: ["No README deploy button yet", "Newer platform, less proven at scale", "Must visit horizon.prefect.io directly"],
    why: "Free + FastMCP-native + built-in OAuth — the future default for FastMCP servers" },
  { id: "coolify", name: "Coolify (Self-Host)", ic: "🧊", verdict: "SELF-HOSTED", c: C.o,
    cost: "$5-15/mo VPS", clicks: "~7 steps", timeout: "None", btn: "❌ N/A",
    pros: ["Open-source PaaS (45K+ GitHub ★)", "Run on any VPS — full control", "Auto-SSL via Traefik", "Web dashboard for deploys + env vars", "One-line install script"],
    cons: ["Must provision own VPS first", "No deploy button for README", "Manual server management"],
    why: "Best self-hosted option: free PaaS software on your own infrastructure" },
  { id: "aws", name: "AWS Bedrock AgentCore", ic: "🔒", verdict: "ENTERPRISE", c: C.y,
    cost: "$20-50/mo", clicks: "CloudFormation", timeout: "None", btn: "✅ Launch Stack",
    pros: ["MicroVM isolation per session", "IAM + Secrets Manager + KMS", "CloudTrail audit logging", "Zscaler provides official CFN template", "Already supported by Zscaler"],
    cons: ["Requires AWS account + Bedrock access", "Complex IAM setup", "Higher cost baseline", "Enterprise-only use case"],
    why: "Official Zscaler-supported enterprise path with full AWS security stack" },
];

const secLayers = [
  { n: "Read-Only Default", d: "Only list/get tools registered on startup", ic: "🔒", c: C.g },
  { n: "Write Gate Flag", d: "--enable-write-tools required explicitly", ic: "🚦", c: C.g },
  { n: "Allowlist Patterns", d: '--write-tools "zpa_create_*" wildcards', ic: "📋", c: C.b },
  { n: "Double Delete Confirm", d: "Agent dialog + server-side confirm", ic: "⚠️", c: C.o },
  { n: "Destructive Hints", d: "destructiveHint=True on all writes", ic: "🏷", c: C.b },
  { n: "OAuth 2.1 + PKCE", d: "MCP spec-mandated for HTTP transport", ic: "🔐", c: C.p },
  { n: "Origin Validation", d: "403 on invalid Origin headers", ic: "🌐", c: C.p },
  { n: "TLS 1.3", d: "Mandatory encrypted transport", ic: "🛡", c: C.g },
  { n: "Audit Logging", d: "All invocations to SIEM with CIDs", ic: "📊", c: C.o },
];

const threats = [
  { t: "SSRF via OAuth metadata", s: "HIGH", m: "Validate URLs, restrict to known auth servers", c: C.r },
  { t: "Session hijacking", s: "HIGH", m: "Rotate Mcp-Session-Id, bind to client", c: C.r },
  { t: "Credential exposure in logs", s: "HIGH", m: "Redact secrets, structured logging", c: C.r },
  { t: "DNS rebinding", s: "MED", m: "Origin header validation (spec-mandated)", c: C.o },
  { t: "Prompt injection via inputs", s: "MED", m: "Validate all tool params before SDK calls", c: C.o },
  { t: "Confused deputy (proxy ID)", s: "MED", m: "Per-user token scoping, RFC 8707", c: C.o },
];

const phases = [
  { ph: "Phase 1", t: "Zero-Change Wrap", d: "1-2 days", c: C.g,
    steps: ["Run zscaler-mcp --transport streamable-http --host 0.0.0.0 --port 8000", "Dockerize with existing Dockerfile", "Test locally with npx mcp-remote http://localhost:8000/mcp", "Verify all 150+ tools respond correctly over HTTP"],
    out: "Docker image exposing /mcp endpoint, unchanged Python server" },
  { ph: "Phase 2", t: "Auth + TLS", d: "2-3 days", c: C.b,
    steps: ["Add Caddy/Traefik reverse proxy for auto-TLS", "Implement API key auth or OAuth 2.1 at proxy layer", "Configure Origin header validation whitelist", "Move Zscaler creds to secrets manager", "Enable structured JSON logging with correlation IDs"],
    out: "Authenticated, TLS-encrypted endpoint with audit logging" },
  { ph: "Phase 3", t: "Deploy Buttons + README", d: "1-2 days", c: C.p,
    steps: ["Create Railway template (web UI, zero repo files)", "Create render.yaml for Render deploy button", "Write docker-compose.remote.yml for self-hosted", "Add deploy badge images to README.md", "Document Prefect Horizon as free alternative", "Publish to Smithery.ai + mcp.so registries"],
    out: "README with one-click deploy badges, multiple paths documented" },
  { ph: "Phase 4", t: "Enterprise + Observability", d: "3-5 days", c: C.o,
    steps: ["AWS Bedrock AgentCore CloudFormation template", "Terraform modules for ECS/Fargate deployment", "OpenTelemetry instrumentation for all tool calls", "SIEM integration (Splunk/Datadog/Elastic)", "Per-client rate limiting", "Security hardening checklist document"],
    out: "Enterprise-grade deployment with full observability stack" },
];

const cfPkgs = [
  { p: "FastMCP", ok: true, n: "Official CF demo exists" },
  { p: "mcp SDK", ok: true, n: "Core protocol works" },
  { p: "httpx", ok: true, n: "Patched to use JS fetch()" },
  { p: "pydantic", ok: true, n: "Pure Python fallback (no Rust core)" },
  { p: "starlette", ok: true, n: "ASGI framework works" },
  { p: "zscaler-sdk-python", ok: false, n: "Uses synchronous requests — BLOCKED" },
  { p: "uvicorn", ok: false, n: "No socket binding in Wasm" },
  { p: "mcp[cli]", ok: false, n: "Requires uvicorn + subprocess" },
];

export default function Dashboard() {
  const [tab, setTab] = useState("arch");
  const [selPlat, setSelPlat] = useState("railway");
  const [openPhase, setOpenPhase] = useState(0);

  const sp = platforms.find(p => p.id === selPlat);

  return (
    <div style={{ background: C.bg, color: C.txt, minHeight: "100vh", fontFamily: sans }}>
      {/* ── Header ── */}
      <div style={{ background: `linear-gradient(135deg, ${C.bg}, #0a1020, #081018)`, borderBottom: `1px solid ${C.bd}`, padding: "20px 28px", position: "relative", overflow: "hidden" }}>
        <div style={{ position: "absolute", top: -40, right: -40, width: 300, height: 300, background: `radial-gradient(circle, ${C.baGlow}, transparent 70%)`, pointerEvents: "none" }} />
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6, position: "relative" }}>
          <div style={{ width: 34, height: 34, borderRadius: 7, background: `linear-gradient(135deg, ${C.g}, ${C.b})`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 17, fontWeight: 900, color: C.bg, fontFamily: font }}>Z</div>
          <div>
            <h1 style={{ margin: 0, fontSize: 20, fontWeight: 800, letterSpacing: -0.5, background: `linear-gradient(135deg, ${C.txt}, ${C.g})`, WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>Zscaler MCP → Remote Deployment</h1>
            <p style={{ margin: 0, fontSize: 10.5, color: C.mut, fontFamily: font }}>zscaler-mcp v0.6.2 · 150+ tools · Python 3.11-3.13 · FastMCP · MIT</p>
          </div>
        </div>
        {/* Stats */}
        <div style={{ display: "flex", gap: 2, background: C.s1, border: `1px solid ${C.bd}`, borderRadius: 8, padding: "12px 8px", margin: "12px 0" }}>
          <Stat n="150+" l="MCP Tools" /><Stat n="8" l="Products" c={C.b} /><Stat n="9" l="Security Layers" c={C.r} /><Stat n="3" l="Transports" c={C.p} /><Stat n="$5" l="/mo hosting" c={C.o} />
        </div>
        {/* Tabs */}
        <div style={{ display: "flex", gap: 2, background: C.s1, borderRadius: 7, padding: 3, width: "fit-content" }}>
          {tabs.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)} style={{ padding: "7px 14px", borderRadius: 5, border: "none", cursor: "pointer", fontSize: 11, fontWeight: 600, fontFamily: font, transition: "all 0.15s", background: tab === t.id ? C.baDim : "transparent", color: tab === t.id ? C.g : C.mut }}>
              <span style={{ marginRight: 5, fontSize: 9 }}>{t.ic}</span>{t.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Content ── */}
      <div style={{ padding: "20px 28px", maxWidth: 1050 }}>

        {/* ═══ ARCHITECTURE ═══ */}
        {tab === "arch" && (<div>
          <Sect icon="🎯" title="Zscaler Product Coverage" sub="8 product areas">
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8 }}>
              {products.map(p => (
                <div key={p.n} style={{ background: C.s1, border: `1px solid ${C.bd}`, borderRadius: 7, padding: "12px 14px", borderTop: `2px solid ${p.c}` }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 3 }}>
                    <span style={{ fontWeight: 700, fontSize: 13, fontFamily: font, color: p.c }}>{p.n}</span>
                    <B c={p.c}>{p.t}</B>
                  </div>
                  <div style={{ fontSize: 10.5, color: C.dim }}>{p.d}</div>
                </div>
              ))}
            </div>
          </Sect>

          <Sect icon="⬡" title="Server Architecture" sub="6 layers">
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {[
                { t: "MCP Clients", items: ["Claude Desktop", "Cursor", "VS Code", "Claude Code", "Custom Agents"], c: C.p, ic: "🤖" },
                { t: "Transport", items: ["Streamable HTTP (default)", "SSE (deprecated)", "stdio (local)", "Mcp-Session-Id", "Origin validation"], c: C.g, ic: "📡" },
                { t: "Protocol Layer", items: ["FastMCP ≥2.5.1", "mcp[cli] ≥1.9.1", "Tool Registry (150+)", "Capability Negotiation"], c: C.b, ic: "⚙️" },
                { t: "Service Dispatch", items: ["ZIAService", "ZPAService", "ZDXService", "ZInsightsService", "ZCCService", "ZTWService", "+2"], c: C.o, ic: "🏗" },
                { t: "Zscaler SDK", items: ["zscaler-sdk-python", "Sync requests", "OAuth 2.0 CC", "Retry + cache", "Rate limiting"], c: C.pk, ic: "📦" },
                { t: "Zscaler Cloud", items: ["ZIA API", "ZPA API", "ZDX API", "OneAPI", "GraphQL"], c: C.y, ic: "☁️" },
              ].map((layer, i) => (
                <div key={i}>
                  <div style={{ background: layer.c + "08", border: `1px solid ${layer.c}22`, borderRadius: 6, padding: "9px 13px", borderLeft: `3px solid ${layer.c}` }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 5 }}>
                      <span style={{ fontSize: 12 }}>{layer.ic}</span>
                      <span style={{ fontSize: 10.5, fontWeight: 700, color: layer.c, fontFamily: font, textTransform: "uppercase", letterSpacing: 0.8 }}>{layer.t}</span>
                    </div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 3 }}>{layer.items.map((item, j) => <Pill key={j} c={layer.c}>{item}</Pill>)}</div>
                  </div>
                  {i < 5 && <Arrow label={["Streamable HTTP / SSE / stdio", "JSON-RPC 2.0", "Service dispatch", "zscaler-sdk-python", "HTTPS"][i]} />}
                </div>
              ))}
            </div>
          </Sect>

          <Sect icon="🔌" title="Bridge Tools" sub="stdio → remote">
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10 }}>
              {[
                { n: "Supergateway", cmd: "npx supergateway", lang: "Node", d: "Wraps any stdio server as Streamable HTTP. Zero code changes. Docker-ready." },
                { n: "mcp-proxy", cmd: "pip install mcp-proxy", lang: "Python", d: "Bidirectional stdio↔HTTP. Can aggregate multiple named servers behind one endpoint." },
                { n: "mcp-remote", cmd: "npx mcp-remote", lang: "Node", d: "Client-side: local stdio → remote HTTP. How Claude Desktop connects to remote MCP servers." },
              ].map(t => (
                <Box key={t.n}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                    <span style={{ fontWeight: 700, fontSize: 13, color: C.txt }}>{t.n}</span><B>{t.lang}</B>
                  </div>
                  <code style={{ fontSize: 10, color: C.g, display: "block", marginBottom: 6, background: C.baDim, padding: "3px 7px", borderRadius: 3, fontFamily: font }}>{t.cmd}</code>
                  <div style={{ fontSize: 11, color: C.dim, lineHeight: 1.5 }}>{t.d}</div>
                </Box>
              ))}
            </div>
          </Sect>
        </div>)}

        {/* ═══ HOSTING ═══ */}
        {tab === "plat" && (<div>
          <Sect icon="🏆" title="Platform Recommendation" sub="Railway wins">
            <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 6, marginBottom: 16 }}>
              {platforms.map(p => (
                <div key={p.id} onClick={() => setSelPlat(p.id)} style={{ background: selPlat === p.id ? C.s2 : C.s1, border: `1px solid ${selPlat === p.id ? p.c : C.bd}`, borderRadius: 7, padding: "12px 10px", textAlign: "center", cursor: "pointer", transition: "all 0.15s", ...(selPlat === p.id && { boxShadow: `0 0 16px ${p.c}18` }) }}>
                  <div style={{ fontSize: 22, marginBottom: 4 }}>{p.ic}</div>
                  <div style={{ fontSize: 11.5, fontWeight: 700, color: selPlat === p.id ? p.c : C.dim }}>{p.name}</div>
                  <B c={p.c} s={{ marginTop: 5 }}>{p.verdict}</B>
                </div>
              ))}
            </div>

            {sp && (
              <Box style={{ borderTop: `2px solid ${sp.c}` }}>
                <div style={{ display: "flex", gap: 20, flexWrap: "wrap", marginBottom: 16, padding: "8px 0", borderBottom: `1px solid ${C.bd}` }}>
                  {[["Cost", sp.cost], ["Clicks", sp.clicks], ["Timeout", sp.timeout], ["Button", sp.btn]].map(([l, v]) => (
                    <div key={l}><span style={{ fontSize: 9, color: C.mut, fontFamily: font, textTransform: "uppercase", letterSpacing: 1 }}>{l}: </span><span style={{ fontSize: 12, fontWeight: 600, color: C.txt }}>{v}</span></div>
                  ))}
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
                  <div>
                    <div style={{ fontSize: 10, fontWeight: 700, color: C.g, fontFamily: font, textTransform: "uppercase", letterSpacing: 1, marginBottom: 8 }}>✓ Advantages</div>
                    {sp.pros.map((p, i) => <Li key={i} c={C.dim}>{p}</Li>)}
                  </div>
                  <div>
                    <div style={{ fontSize: 10, fontWeight: 700, color: C.r, fontFamily: font, textTransform: "uppercase", letterSpacing: 1, marginBottom: 8 }}>✗ Limitations</div>
                    {sp.cons.map((c, i) => <Li key={i} c={C.dim}>{c}</Li>)}
                  </div>
                </div>
                <div style={{ marginTop: 14, padding: "10px 12px", background: sp.c + "08", border: `1px solid ${sp.c}1a`, borderRadius: 6, fontSize: 11.5, color: sp.c, lineHeight: 1.5 }}>
                  <span style={{ fontWeight: 700 }}>WHY → </span>{sp.why}
                </div>
              </Box>
            )}
          </Sect>

          <Sect icon="❌" title="Eliminated Platforms" sub="and why">
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              <Box style={{ borderLeft: `3px solid ${C.r}` }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: C.r, marginBottom: 6 }}>Heroku — 30s HTTP Timeout</div>
                <div style={{ fontSize: 11, color: C.dim, lineHeight: 1.6 }}>The Heroku router terminates requests where the server hasn't sent an initial response within 30 seconds. Many Zscaler API operations exceed this, especially bulk queries across ZIA, ZPA, or ZDX. The 55-second rolling chunk timeout is also tight for complex operations.</div>
              </Box>
              <Box style={{ borderLeft: `3px solid ${C.r}` }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: C.r, marginBottom: 6 }}>AWS Lambda — Wrong Architecture</div>
                <div style={{ fontSize: 11, color: C.dim, lineHeight: 1.6 }}>Lambda is event-driven with a 15-min max timeout. The awslabs stdio adapter only works for stateless stdio servers. Cold starts of 2-5s are unacceptable for interactive MCP. No deploy button for README. Provisioned Concurrency adds cost and complexity.</div>
              </Box>
              <Box style={{ borderLeft: `3px solid ${C.o}` }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: C.o, marginBottom: 6 }}>Replit — Expensive, Not Ideal</div>
                <div style={{ fontSize: 11, color: C.dim, lineHeight: 1.6 }}>$45-75/month for always-on deploys. No Docker support. More of a dev environment than a hosting platform. Doesn't support deploy buttons for README integration.</div>
              </Box>
              <Box style={{ borderLeft: `3px solid ${C.o}` }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: C.o, marginBottom: 6 }}>Cloudflare Workers — Python Blocked</div>
                <div style={{ fontSize: 11, color: C.dim, lineHeight: 1.6 }}>zscaler-sdk-python uses synchronous `requests` — the one HTTP library that can't work in Wasm. Requires full TS rewrite. See CF Analysis tab for details.</div>
              </Box>
            </div>
          </Sect>

          <Sect icon="📋" title="Deployment Tier Strategy">
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10 }}>
              {[
                { t: "Community", sub: "One-click from README", items: ["Railway button (zero config)", "Render button (render.yaml)", "Prefect Horizon (free)"], c: C.g },
                { t: "Self-Hosted", sub: "Own infrastructure", items: ["Docker Compose in repo", "Coolify (open-source PaaS)", "Portainer (Docker GUI)"], c: C.o },
                { t: "Enterprise", sub: "Full security stack", items: ["AWS Bedrock AgentCore", "Railway Pro ($20/seat)", "Terraform for ECS/Fargate"], c: C.y },
              ].map(tier => (
                <Box key={tier.t} style={{ borderTop: `2px solid ${tier.c}` }}>
                  <div style={{ fontSize: 12, fontWeight: 700, color: tier.c, marginBottom: 2 }}>{tier.t}</div>
                  <div style={{ fontSize: 9.5, color: C.mut, marginBottom: 10, fontFamily: font }}>{tier.sub}</div>
                  {tier.items.map((item, i) => <Li key={i}>{item}</Li>)}
                </Box>
              ))}
            </div>
          </Sect>
        </div>)}

        {/* ═══ SECURITY ═══ */}
        {tab === "sec" && (<div>
          <Sect icon="🛡" title="9-Layer Defense-in-Depth" sub="Zscaler's security model">
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
              {secLayers.map((l, i) => (
                <Box key={i} style={{ padding: 12 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 5 }}>
                    <span style={{ width: 20, height: 20, borderRadius: 4, background: l.c + "1a", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 800, color: l.c, fontFamily: font }}>{i + 1}</span>
                    <span style={{ fontSize: 11.5, fontWeight: 600 }}>{l.ic} {l.n}</span>
                  </div>
                  <div style={{ fontSize: 10.5, color: C.dim, paddingLeft: 26, lineHeight: 1.4 }}>{l.d}</div>
                </Box>
              ))}
            </div>
          </Sect>

          <Sect icon="⚠️" title="Remote Deployment Threats" sub="6 identified">
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              {threats.map((t, i) => (
                <div key={i} style={{ background: t.c + "08", border: `1px solid ${t.c}1a`, borderRadius: 6, padding: 12 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5 }}>
                    <span style={{ fontSize: 11.5, fontWeight: 600, color: C.txt }}>{t.t}</span>
                    <B c={t.c}>{t.s}</B>
                  </div>
                  <div style={{ fontSize: 10.5, color: C.dim, lineHeight: 1.4 }}>↳ {t.m}</div>
                </div>
              ))}
            </div>
          </Sect>

          <Sect icon="✅" title="Security Checklist">
            <Box>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 4 }}>
                {[
                  "TLS 1.3 on all connections",
                  "Token audience validation (RFC 9728)",
                  "Write tools disabled by default",
                  "Narrow write allowlists only",
                  "All invocations logged to SIEM",
                  "Origin header validation enabled",
                  "Credentials in secrets manager",
                  "Container runs as non-root user",
                ].map((item, i) => (
                  <div key={i} style={{ display: "flex", gap: 8, fontSize: 11.5, color: C.dim, padding: "4px 0" }}>
                    <span style={{ color: C.g, fontSize: 11, fontFamily: font }}>☐</span>{item}
                  </div>
                ))}
              </div>
            </Box>
          </Sect>
        </div>)}

        {/* ═══ DEPLOY PLAN ═══ */}
        {tab === "plan" && (<div>
          <Sect icon="▸" title="Implementation Roadmap" sub="4 phases · ~8-12 days total">
            {phases.map((p, i) => (
              <div key={i} onClick={() => setOpenPhase(openPhase === i ? -1 : i)} style={{ marginBottom: 8, borderRadius: 8, overflow: "hidden", border: `1px solid ${openPhase === i ? p.c + "44" : C.bd}`, cursor: "pointer", transition: "all 0.15s", background: openPhase === i ? C.s2 : C.s1, borderLeft: `3px solid ${p.c}` }}>
                <div style={{ padding: "12px 16px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <span style={{ width: 24, height: 24, borderRadius: 5, background: p.c + "1a", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 800, color: p.c, fontFamily: font }}>{i + 1}</span>
                    <span style={{ fontSize: 14, fontWeight: 700, color: C.txt }}>{p.ph} — {p.t}</span>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <B c={p.c}>{p.d}</B>
                    <span style={{ color: C.mut, fontSize: 12, transform: openPhase === i ? "rotate(90deg)" : "rotate(0deg)", transition: "transform 0.15s" }}>▸</span>
                  </div>
                </div>
                {openPhase === i && (
                  <div style={{ padding: "0 16px 14px 50px" }}>
                    {p.steps.map((step, j) => (
                      <div key={j} style={{ display: "flex", alignItems: "start", gap: 8, marginBottom: 6, fontSize: 12, color: C.dim, lineHeight: 1.5 }}>
                        <span style={{ color: p.c, fontFamily: font, fontSize: 10, marginTop: 2, flexShrink: 0 }}>{String(j + 1).padStart(2, "0")}</span>{step}
                      </div>
                    ))}
                    <div style={{ marginTop: 10, padding: "8px 12px", background: p.c + "0a", border: `1px solid ${p.c}1a`, borderRadius: 5, fontSize: 11, color: p.c }}>
                      <span style={{ fontWeight: 700 }}>OUTPUT → </span>{p.out}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </Sect>

          <Sect icon="⚡" title="Quickstart" sub="zero code changes">
            <Box style={{ background: "#080c14", fontFamily: font, fontSize: 11, lineHeight: 2.1, overflow: "auto" }}>
              <div style={{ color: C.mut }}># Option A: Native streamable HTTP (server already supports it)</div>
              <div><span style={{ color: C.g }}>$</span> zscaler-mcp --transport streamable-http --host 0.0.0.0 --port 8000</div>
              <div style={{ height: 8 }} />
              <div style={{ color: C.mut }}># Option B: Wrap stdio with Supergateway (zero changes)</div>
              <div><span style={{ color: C.g }}>$</span> docker run -p 8000:8000 \</div>
              <div style={{ paddingLeft: 16, color: C.p }}>-e ZSCALER_CLIENT_ID=... -e ZSCALER_CLIENT_SECRET=... \</div>
              <div style={{ paddingLeft: 16, color: C.o }}>supercorp/supergateway \</div>
              <div style={{ paddingLeft: 16, color: C.b }}>--stdio "zscaler-mcp --services zia,zpa,zdx" \</div>
              <div style={{ paddingLeft: 16, color: C.b }}>--outputTransport streamableHttp --port 8000</div>
              <div style={{ height: 8 }} />
              <div style={{ color: C.mut }}># Connect from Claude Desktop</div>
              <div><span style={{ color: C.g }}>$</span> npx mcp-remote https://your-server.up.railway.app/mcp</div>
            </Box>
          </Sect>
        </div>)}

        {/* ═══ CF ANALYSIS ═══ */}
        {tab === "cf" && (<div>
          <Sect icon="⚡" title="Cloudflare Workers Python Analysis" sub="NOT VIABLE">
            <Box style={{ borderLeft: `3px solid ${C.r}`, marginBottom: 16 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: C.r, marginBottom: 8 }}>Verdict: Cannot Run Zscaler MCP on CF Workers Python</div>
              <div style={{ fontSize: 12, color: C.dim, lineHeight: 1.6 }}>
                Cloudflare Workers Python runs CPython via Pyodide (WebAssembly). The <code style={{ color: C.o, fontFamily: font }}>zscaler-sdk-python</code> uses synchronous <code style={{ color: C.r, fontFamily: font }}>requests</code> — the one HTTP library that cannot work in the Wasm sandbox. Only async <code style={{ color: C.g, fontFamily: font }}>httpx</code> and <code style={{ color: C.g, fontFamily: font }}>aiohttp</code> are supported. This is a fundamental architectural mismatch.
              </div>
            </Box>
          </Sect>

          <Sect icon="📦" title="Package Compatibility" sub="5 pass · 3 blocked">
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
              {cfPkgs.map((p, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 12px", borderRadius: 6, background: p.ok ? C.g + "06" : C.r + "06", border: `1px solid ${p.ok ? C.g : C.r}1a` }}>
                  <span style={{ fontSize: 14, flexShrink: 0 }}>{p.ok ? "✅" : "❌"}</span>
                  <div>
                    <span style={{ fontSize: 12, fontWeight: 600, color: p.ok ? C.g : C.r, fontFamily: font }}>{p.p}</span>
                    <div style={{ fontSize: 10, color: C.dim }}>{p.n}</div>
                  </div>
                </div>
              ))}
            </div>
          </Sect>

          <Sect icon="🧱" title="Three Fundamental Blockers">
            {[
              { n: "Synchronous HTTP", d: "zscaler-sdk-python built entirely on requests.Session — Workers only allow async httpx/aiohttp. Fixing requires forking the SDK and rewriting every HTTP call.", c: C.r },
              { n: "ASGI Server", d: "Zscaler MCP uses uvicorn — no socket binding or process management in Wasm. Must replace with CF's ASGI adapter (asgi.fetch()).", c: C.o },
              { n: "Session Model Mismatch", d: "SDK maintains long-lived sessions with 3600s cache TTL. Workers are request-driven with no guaranteed persistence. Durable Objects partially mitigate but add complexity.", c: C.y },
            ].map((b, i) => (
              <Box key={i} style={{ borderLeft: `3px solid ${b.c}`, marginBottom: 8 }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: b.c, marginBottom: 5 }}>Blocker {i + 1}: {b.n}</div>
                <div style={{ fontSize: 11.5, color: C.dim, lineHeight: 1.6 }}>{b.d}</div>
              </Box>
            ))}
          </Sect>

          <Sect icon="🔀" title="TypeScript Wrapper: The CF Alternative" sub="2-4 weeks effort">
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              <Box style={{ borderTop: `2px solid ${C.r}` }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: C.r, fontFamily: font, marginBottom: 8 }}>PYTHON ON CF WORKERS</div>
                {["Requires forked zscaler-sdk-python", "Must rewrite all HTTP to async httpx", "Beta runtime, manual vendoring", "FastMCP via ASGI (limited features)", "1 demo, minimal docs", "128MB memory including Pyodide"].map((item, i) => <Li key={i}>{item}</Li>)}
              </Box>
              <Box style={{ borderTop: `2px solid ${C.g}` }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: C.g, fontFamily: font, marginBottom: 8 }}>TYPESCRIPT ON CF WORKERS</div>
                {["Direct REST calls to Zscaler APIs", "Native fetch() — zero friction", "McpAgent + createMcpHandler()", "workers-oauth-provider for auth", "GA runtime, battle-tested", "13+ reference servers from CF"].map((item, i) => <Li key={i}>{item}</Li>)}
              </Box>
            </div>
          </Sect>
        </div>)}

        {/* ── Footer ── */}
        <div style={{ marginTop: 20, padding: "14px 16px", borderRadius: 8, background: `linear-gradient(135deg, ${C.g}06, ${C.b}06)`, border: `1px dashed ${C.g}22`, textAlign: "center" }}>
          <div style={{ fontFamily: font, fontSize: 12, fontWeight: 700, color: C.g, marginBottom: 4 }}>
            Railway → Streamable HTTP → OAuth 2.1 → Production
          </div>
          <div style={{ fontSize: 10, color: C.mut }}>
            One deploy button · Zero repo config · ~$5/mo · No HTTP timeout · Full streaming support
          </div>
        </div>
      </div>
    </div>
  );
}
