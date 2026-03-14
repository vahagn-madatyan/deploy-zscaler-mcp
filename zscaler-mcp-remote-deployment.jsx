import { useState } from "react";

const COLORS = {
  bg: "#0a0e17",
  surface: "#111827",
  surfaceHover: "#1a2332",
  border: "#1e2d3d",
  borderActive: "#00d4aa",
  accent: "#00d4aa",
  accentDim: "#00d4aa33",
  accentGlow: "#00d4aa22",
  warning: "#f59e0b",
  danger: "#ef4444",
  info: "#3b82f6",
  text: "#e2e8f0",
  textDim: "#8899aa",
  textMuted: "#556677",
  purple: "#a78bfa",
  pink: "#f472b6",
  orange: "#fb923c",
};

const Badge = ({ children, color = COLORS.accent, style }) => (
  <span
    style={{
      display: "inline-block",
      padding: "2px 10px",
      borderRadius: 4,
      fontSize: 11,
      fontWeight: 600,
      letterSpacing: 0.5,
      color: color,
      background: color + "18",
      border: `1px solid ${color}33`,
      fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
      ...style,
    }}
  >
    {children}
  </span>
);

const Metric = ({ label, value, sub }) => (
  <div style={{ textAlign: "center" }}>
    <div
      style={{
        fontSize: 28,
        fontWeight: 700,
        color: COLORS.accent,
        fontFamily: "'JetBrains Mono', monospace",
        lineHeight: 1,
      }}
    >
      {value}
    </div>
    <div
      style={{
        fontSize: 11,
        color: COLORS.textDim,
        marginTop: 4,
        textTransform: "uppercase",
        letterSpacing: 1,
      }}
    >
      {label}
    </div>
    {sub && (
      <div style={{ fontSize: 10, color: COLORS.textMuted, marginTop: 2 }}>
        {sub}
      </div>
    )}
  </div>
);

const SectionTitle = ({ children, icon }) => (
  <div
    style={{
      display: "flex",
      alignItems: "center",
      gap: 10,
      marginBottom: 20,
      paddingBottom: 12,
      borderBottom: `1px solid ${COLORS.border}`,
    }}
  >
    <span style={{ fontSize: 18 }}>{icon}</span>
    <h2
      style={{
        margin: 0,
        fontSize: 16,
        fontWeight: 700,
        color: COLORS.text,
        letterSpacing: 0.5,
        textTransform: "uppercase",
        fontFamily: "'JetBrains Mono', monospace",
      }}
    >
      {children}
    </h2>
  </div>
);

const Card = ({ children, style, onClick, active }) => (
  <div
    onClick={onClick}
    style={{
      background: active ? COLORS.surfaceHover : COLORS.surface,
      border: `1px solid ${active ? COLORS.borderActive : COLORS.border}`,
      borderRadius: 8,
      padding: 20,
      cursor: onClick ? "pointer" : "default",
      transition: "all 0.2s ease",
      ...(active && { boxShadow: `0 0 20px ${COLORS.accentGlow}` }),
      ...style,
    }}
  >
    {children}
  </div>
);

const FlowArrow = ({ label, vertical }) =>
  vertical ? (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        padding: "4px 0",
      }}
    >
      <div
        style={{
          width: 1,
          height: 16,
          background: `linear-gradient(to bottom, ${COLORS.accent}66, ${COLORS.accent})`,
        }}
      />
      <div style={{ fontSize: 10, color: COLORS.accent, margin: "2px 0" }}>
        ▼
      </div>
      {label && (
        <span
          style={{
            fontSize: 9,
            color: COLORS.textMuted,
            fontFamily: "monospace",
          }}
        >
          {label}
        </span>
      )}
    </div>
  ) : (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 4,
        padding: "0 4px",
      }}
    >
      <div
        style={{
          width: 16,
          height: 1,
          background: `linear-gradient(to right, ${COLORS.accent}66, ${COLORS.accent})`,
        }}
      />
      <span style={{ fontSize: 10, color: COLORS.accent }}>▶</span>
    </div>
  );

const ArchLayer = ({ title, items, color, icon }) => (
  <div
    style={{
      background: color + "0a",
      border: `1px solid ${color}33`,
      borderRadius: 6,
      padding: "10px 14px",
      borderLeft: `3px solid ${color}`,
    }}
  >
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 6,
        marginBottom: 6,
      }}
    >
      <span style={{ fontSize: 13 }}>{icon}</span>
      <span
        style={{
          fontSize: 11,
          fontWeight: 700,
          color: color,
          textTransform: "uppercase",
          letterSpacing: 0.8,
          fontFamily: "monospace",
        }}
      >
        {title}
      </span>
    </div>
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        gap: 4,
      }}
    >
      {items.map((item, i) => (
        <span
          key={i}
          style={{
            fontSize: 10,
            padding: "2px 8px",
            borderRadius: 3,
            background: color + "15",
            color: COLORS.textDim,
            fontFamily: "monospace",
          }}
        >
          {item}
        </span>
      ))}
    </div>
  </div>
);

const platforms = [
  {
    id: "cloudflare",
    name: "Cloudflare Workers",
    icon: "⚡",
    rating: "Best DX",
    color: COLORS.accent,
    pros: [
      "Zero cold starts (V8 isolates)",
      "Native MCP SDK (createMcpHandler)",
      "Built-in OAuth 2.1 provider lib",
      "Durable Objects for stateful sessions",
      "One-command deploy (wrangler)",
      "~$5/mo at low scale",
    ],
    cons: [
      "JS/TS only — no native Python",
      "10ms CPU limit (free plan)",
      "Must rewrite tool layer in TS",
      "No arbitrary binary execution",
    ],
    effort: "Medium-High",
    fit: "Ideal if rebuilding tool layer",
    deploy: "npx wrangler deploy",
  },
  {
    id: "aws",
    name: "AWS Lambda",
    icon: "☁️",
    rating: "Best for Python",
    color: COLORS.info,
    pros: [
      "Wraps existing stdio server directly",
      "Official awslabs adapter (337+ ★)",
      "Bedrock AgentCore integration",
      "Secrets Manager + KMS encryption",
      "CloudTrail audit logging",
      "IAM-based access control",
    ],
    cons: [
      "2-5s cold starts (Python)",
      "Complex CDK/CloudFormation setup",
      "DynamoDB needed for sessions",
      "Higher baseline cost ($15-50/mo)",
    ],
    effort: "Low (stdio wrap)",
    fit: "Best for existing Python server",
    deploy: "cdk deploy / CloudFormation",
  },
  {
    id: "vercel",
    name: "Vercel Functions",
    icon: "▲",
    rating: "Simplest Deploy",
    color: COLORS.purple,
    pros: [
      "~10 lines of code with @vercel/mcp-adapter",
      "Fluid Compute reduces cold starts",
      "50%+ CPU savings vs SSE",
      "Production-proven (Zapier, Composio)",
      "Free tier generous",
      "Git push to deploy",
    ],
    cons: [
      "JS/TS native only",
      "Limited Python runtime support",
      "Less control over infra",
      "No native Durable Objects equivalent",
    ],
    effort: "Medium (TS wrapper)",
    fit: "Fastest time-to-deploy",
    deploy: "vercel deploy",
  },
  {
    id: "docker",
    name: "Docker / Self-Hosted",
    icon: "🐳",
    rating: "Maximum Control",
    color: COLORS.orange,
    pros: [
      "Zero code changes (Supergateway wrap)",
      "Full infra control",
      "Air-gapped / regulated environments",
      "MCPJungle gateway (multi-server)",
      "Compose-based deployment",
      "Any language / runtime",
    ],
    cons: [
      "Manual TLS / cert management",
      "Must build own auth layer",
      "Server provisioning overhead",
      "No auto-scaling without K8s",
    ],
    effort: "Low (wrap) to High (production)",
    fit: "Regulated / on-prem environments",
    deploy: "docker compose up -d",
  },
];

const zscalerProducts = [
  { name: "ZIA", tools: "~60", desc: "Internet Access", color: "#3b82f6" },
  { name: "ZPA", tools: "~60", desc: "Private Access", color: "#8b5cf6" },
  { name: "Z-Insights", tools: "16", desc: "Analytics", color: "#06b6d4" },
  { name: "ZDX", tools: "18", desc: "Digital Experience", color: "#10b981" },
  { name: "ZEASM", tools: "7", desc: "Attack Surface", color: "#f59e0b" },
  { name: "ZCC", tools: "4", desc: "Client Connector", color: "#ec4899" },
  { name: "ZTW", tools: "20+", desc: "Workload Seg.", color: "#f97316" },
  { name: "ZIdentity", tools: "3", desc: "Identity/IAM", color: "#a78bfa" },
];

const securityLayers = [
  {
    name: "Read-Only Default",
    desc: "Only list/get tools registered on startup",
    icon: "🔒",
  },
  {
    name: "Explicit Write Gate",
    desc: "--enable-write-tools flag required",
    icon: "🚦",
  },
  {
    name: "Allowlist Patterns",
    desc: '--write-tools "zpa_create_*" wildcards',
    icon: "📋",
  },
  {
    name: "Double Delete Confirm",
    desc: "Agent + server-side confirmation",
    icon: "⚠️",
  },
  {
    name: "Destructive Hints",
    desc: "destructiveHint=True metadata",
    icon: "🏷️",
  },
  {
    name: "OAuth 2.1 + PKCE",
    desc: "Spec-mandated for HTTP transport",
    icon: "🔐",
  },
  {
    name: "Origin Validation",
    desc: "403 on invalid Origin headers",
    icon: "🌐",
  },
  {
    name: "TLS 1.3",
    desc: "Mandatory encrypted transport",
    icon: "🛡️",
  },
  {
    name: "Audit Logging",
    desc: "All tool invocations to SIEM",
    icon: "📊",
  },
];

const tabs = [
  { id: "overview", label: "Overview", icon: "◉" },
  { id: "architecture", label: "Architecture", icon: "⬡" },
  { id: "platforms", label: "Platforms", icon: "☰" },
  { id: "security", label: "Security", icon: "◈" },
  { id: "plan", label: "Deploy Plan", icon: "▸" },
];

export default function ZscalerMCPDashboard() {
  const [activeTab, setActiveTab] = useState("overview");
  const [activePlatform, setActivePlatform] = useState("aws");
  const [expandedPhase, setExpandedPhase] = useState(0);

  const selectedPlatform = platforms.find((p) => p.id === activePlatform);

  return (
    <div
      style={{
        background: COLORS.bg,
        color: COLORS.text,
        minHeight: "100vh",
        fontFamily:
          "'Geist', 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif",
      }}
    >
      {/* Header */}
      <div
        style={{
          background: `linear-gradient(135deg, ${COLORS.bg} 0%, #0d1422 50%, #0a1628 100%)`,
          borderBottom: `1px solid ${COLORS.border}`,
          padding: "24px 32px",
          position: "relative",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            position: "absolute",
            top: 0,
            right: 0,
            width: 400,
            height: 200,
            background: `radial-gradient(ellipse at top right, ${COLORS.accentGlow}, transparent 70%)`,
            pointerEvents: "none",
          }}
        />
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            marginBottom: 8,
          }}
        >
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: 8,
              background: `linear-gradient(135deg, ${COLORS.accent}, ${COLORS.info})`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 18,
              fontWeight: 800,
              color: COLORS.bg,
              fontFamily: "monospace",
            }}
          >
            Z
          </div>
          <div>
            <h1
              style={{
                margin: 0,
                fontSize: 22,
                fontWeight: 800,
                letterSpacing: -0.5,
                background: `linear-gradient(135deg, ${COLORS.text}, ${COLORS.accent})`,
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              Zscaler MCP → Remote Deployment
            </h1>
            <p
              style={{
                margin: 0,
                fontSize: 12,
                color: COLORS.textDim,
                fontFamily: "monospace",
              }}
            >
              zscaler-mcp v0.6.2 · 150+ tools · Python 3.11-3.13 · MIT License
            </p>
          </div>
        </div>

        {/* Tabs */}
        <div
          style={{
            display: "flex",
            gap: 2,
            marginTop: 16,
            background: COLORS.surface,
            borderRadius: 8,
            padding: 3,
            width: "fit-content",
          }}
        >
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: "8px 16px",
                borderRadius: 6,
                border: "none",
                cursor: "pointer",
                fontSize: 12,
                fontWeight: 600,
                fontFamily: "'JetBrains Mono', monospace",
                letterSpacing: 0.3,
                transition: "all 0.15s ease",
                background:
                  activeTab === tab.id ? COLORS.accentDim : "transparent",
                color:
                  activeTab === tab.id ? COLORS.accent : COLORS.textMuted,
              }}
            >
              <span style={{ marginRight: 6, fontSize: 10 }}>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div style={{ padding: "24px 32px", maxWidth: 1100 }}>
        {/* OVERVIEW TAB */}
        {activeTab === "overview" && (
          <div>
            {/* Metrics Row */}
            <Card
              style={{
                display: "flex",
                justifyContent: "space-around",
                padding: "24px 20px",
                marginBottom: 24,
                background: `linear-gradient(135deg, ${COLORS.surface}, ${COLORS.surfaceHover})`,
              }}
            >
              <Metric value="150+" label="MCP Tools" sub="Read & Write" />
              <div
                style={{
                  width: 1,
                  background: COLORS.border,
                  alignSelf: "stretch",
                }}
              />
              <Metric value="8" label="Product Areas" sub="ZIA, ZPA, ZDX..." />
              <div
                style={{
                  width: 1,
                  background: COLORS.border,
                  alignSelf: "stretch",
                }}
              />
              <Metric value="3" label="Transports" sub="stdio · SSE · HTTP" />
              <div
                style={{
                  width: 1,
                  background: COLORS.border,
                  alignSelf: "stretch",
                }}
              />
              <Metric value="9" label="Security Layers" sub="Defense-in-depth" />
            </Card>

            {/* Product Coverage Grid */}
            <SectionTitle icon="🎯">Zscaler Product Coverage</SectionTitle>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(4, 1fr)",
                gap: 10,
                marginBottom: 28,
              }}
            >
              {zscalerProducts.map((p) => (
                <div
                  key={p.name}
                  style={{
                    background: COLORS.surface,
                    border: `1px solid ${COLORS.border}`,
                    borderRadius: 8,
                    padding: "14px 16px",
                    borderTop: `2px solid ${p.color}`,
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      marginBottom: 4,
                    }}
                  >
                    <span
                      style={{
                        fontWeight: 700,
                        fontSize: 14,
                        fontFamily: "monospace",
                        color: p.color,
                      }}
                    >
                      {p.name}
                    </span>
                    <Badge color={p.color}>{p.tools} tools</Badge>
                  </div>
                  <div style={{ fontSize: 11, color: COLORS.textDim }}>
                    {p.desc}
                  </div>
                </div>
              ))}
            </div>

            {/* Current State */}
            <SectionTitle icon="📍">Current State vs Target</SectionTitle>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr auto 1fr",
                gap: 16,
                alignItems: "center",
              }}
            >
              <Card>
                <div
                  style={{
                    fontSize: 11,
                    textTransform: "uppercase",
                    letterSpacing: 1,
                    color: COLORS.textMuted,
                    marginBottom: 12,
                    fontFamily: "monospace",
                  }}
                >
                  ● Current: Local stdio
                </div>
                <div style={{ fontSize: 13, color: COLORS.textDim, lineHeight: 1.7 }}>
                  Runs as a <Badge color={COLORS.warning}>subprocess</Badge> on
                  the user's machine. Claude Desktop, Cursor, VS Code spawn
                  it via <code style={{ color: COLORS.accent, fontSize: 12 }}>
                  zscaler-mcp --transport stdio</code>. Credentials stored locally.
                  Single-user only.
                </div>
              </Card>

              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: 4,
                }}
              >
                <div
                  style={{
                    width: 60,
                    height: 1,
                    background: `linear-gradient(to right, ${COLORS.warning}, ${COLORS.accent})`,
                  }}
                />
                <span
                  style={{
                    fontSize: 10,
                    color: COLORS.textMuted,
                    fontFamily: "monospace",
                  }}
                >
                  MIGRATE
                </span>
                <div
                  style={{
                    width: 60,
                    height: 1,
                    background: `linear-gradient(to right, ${COLORS.warning}, ${COLORS.accent})`,
                  }}
                />
              </div>

              <Card
                style={{
                  borderColor: COLORS.borderActive,
                  boxShadow: `0 0 20px ${COLORS.accentGlow}`,
                }}
              >
                <div
                  style={{
                    fontSize: 11,
                    textTransform: "uppercase",
                    letterSpacing: 1,
                    color: COLORS.accent,
                    marginBottom: 12,
                    fontFamily: "monospace",
                  }}
                >
                  ◉ Target: Remote Streamable HTTP
                </div>
                <div style={{ fontSize: 13, color: COLORS.textDim, lineHeight: 1.7 }}>
                  Deployed on <Badge>Cloud Platform</Badge> with OAuth 2.1 auth,
                  TLS 1.3, audit logging. Multi-user, team-accessible. Agents
                  connect via{" "}
                  <code style={{ color: COLORS.accent, fontSize: 12 }}>
                    https://mcp.example.com/mcp
                  </code>
                </div>
              </Card>
            </div>
          </div>
        )}

        {/* ARCHITECTURE TAB */}
        {activeTab === "architecture" && (
          <div>
            <SectionTitle icon="⬡">Server Architecture Layers</SectionTitle>
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: 6,
                marginBottom: 28,
              }}
            >
              <ArchLayer
                icon="🤖"
                title="MCP Client"
                items={[
                  "Claude Desktop",
                  "Cursor",
                  "VS Code Copilot",
                  "Claude Code",
                  "Custom Agents",
                ]}
                color={COLORS.purple}
              />
              <FlowArrow vertical label="Streamable HTTP / SSE / stdio" />
              <ArchLayer
                icon="🔌"
                title="Transport Layer"
                items={[
                  "Streamable HTTP (recommended)",
                  "SSE (deprecated)",
                  "stdio (local only)",
                  "Origin Validation",
                  "Mcp-Session-Id",
                ]}
                color={COLORS.accent}
              />
              <FlowArrow vertical label="JSON-RPC 2.0" />
              <ArchLayer
                icon="⚙️"
                title="MCP Protocol Layer"
                items={[
                  "FastMCP ≥2.5.1",
                  "mcp[cli] ≥1.9.1",
                  "Tool Registration",
                  "Capability Negotiation",
                  "Session Mgmt",
                ]}
                color={COLORS.info}
              />
              <FlowArrow vertical label="Service Dispatch" />
              <ArchLayer
                icon="🏗️"
                title="Service Layer"
                items={[
                  "ZIAService",
                  "ZPAService",
                  "ZDXService",
                  "ZCCService",
                  "ZInsightsService",
                  "ZEASMService",
                  "ZTWService",
                  "ZIdentityService",
                ]}
                color={COLORS.orange}
              />
              <FlowArrow vertical label="zscaler-sdk-python" />
              <ArchLayer
                icon="☁️"
                title="Zscaler Cloud APIs"
                items={[
                  "ZIA API",
                  "ZPA API",
                  "ZDX API",
                  "OneAPI (OAuth 2.0)",
                  "GraphQL (Insights)",
                ]}
                color={COLORS.pink}
              />
            </div>

            {/* Remote Deployment Architecture */}
            <SectionTitle icon="🌐">
              Remote Deployment Architecture
            </SectionTitle>
            <Card style={{ padding: 24 }}>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr 1fr",
                  gap: 16,
                }}
              >
                {/* Auth Layer */}
                <div
                  style={{
                    gridColumn: "1 / -1",
                    background: COLORS.accent + "08",
                    border: `1px dashed ${COLORS.accent}44`,
                    borderRadius: 8,
                    padding: 16,
                  }}
                >
                  <div
                    style={{
                      fontSize: 11,
                      fontWeight: 700,
                      color: COLORS.accent,
                      fontFamily: "monospace",
                      textTransform: "uppercase",
                      letterSpacing: 1,
                      marginBottom: 10,
                    }}
                  >
                    🔐 Auth Gateway Layer
                  </div>
                  <div
                    style={{ display: "flex", gap: 8, flexWrap: "wrap" }}
                  >
                    {[
                      "OAuth 2.1 + PKCE",
                      "Token Audience Validation (RFC 9728)",
                      "Dynamic Client Registration",
                      "Resource Indicators (RFC 8707)",
                      "mTLS (enterprise)",
                    ].map((item) => (
                      <Badge key={item} color={COLORS.accent}>
                        {item}
                      </Badge>
                    ))}
                  </div>
                </div>

                {/* Three columns */}
                <div
                  style={{
                    background: COLORS.info + "0a",
                    border: `1px solid ${COLORS.info}33`,
                    borderRadius: 6,
                    padding: 14,
                  }}
                >
                  <div
                    style={{
                      fontSize: 11,
                      fontWeight: 700,
                      color: COLORS.info,
                      fontFamily: "monospace",
                      marginBottom: 8,
                    }}
                  >
                    ☁️ COMPUTE
                  </div>
                  <div
                    style={{
                      fontSize: 11,
                      color: COLORS.textDim,
                      lineHeight: 1.8,
                    }}
                  >
                    CF Workers / Lambda / Vercel Functions / Docker containers
                    running the MCP server process
                  </div>
                </div>
                <div
                  style={{
                    background: COLORS.purple + "0a",
                    border: `1px solid ${COLORS.purple}33`,
                    borderRadius: 6,
                    padding: 14,
                  }}
                >
                  <div
                    style={{
                      fontSize: 11,
                      fontWeight: 700,
                      color: COLORS.purple,
                      fontFamily: "monospace",
                      marginBottom: 8,
                    }}
                  >
                    🗄️ STATE
                  </div>
                  <div
                    style={{
                      fontSize: 11,
                      color: COLORS.textDim,
                      lineHeight: 1.8,
                    }}
                  >
                    Durable Objects / DynamoDB / Redis (Upstash) for session
                    management. Stateless mode preferred.
                  </div>
                </div>
                <div
                  style={{
                    background: COLORS.warning + "0a",
                    border: `1px solid ${COLORS.warning}33`,
                    borderRadius: 6,
                    padding: 14,
                  }}
                >
                  <div
                    style={{
                      fontSize: 11,
                      fontWeight: 700,
                      color: COLORS.warning,
                      fontFamily: "monospace",
                      marginBottom: 8,
                    }}
                  >
                    🔑 SECRETS
                  </div>
                  <div
                    style={{
                      fontSize: 11,
                      color: COLORS.textDim,
                      lineHeight: 1.8,
                    }}
                  >
                    Secrets Manager / Workers KV / Vault for Zscaler API
                    credentials. Never exposed to MCP clients.
                  </div>
                </div>

                {/* Observability */}
                <div
                  style={{
                    gridColumn: "1 / -1",
                    background: COLORS.pink + "08",
                    border: `1px dashed ${COLORS.pink}44`,
                    borderRadius: 8,
                    padding: 16,
                  }}
                >
                  <div
                    style={{
                      fontSize: 11,
                      fontWeight: 700,
                      color: COLORS.pink,
                      fontFamily: "monospace",
                      textTransform: "uppercase",
                      letterSpacing: 1,
                      marginBottom: 10,
                    }}
                  >
                    📊 Observability Layer
                  </div>
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    {[
                      "Tool invocation audit logs",
                      "SIEM integration",
                      "OpenTelemetry traces",
                      "Rate limiting metrics",
                      "Correlation IDs",
                    ].map((item) => (
                      <Badge key={item} color={COLORS.pink}>
                        {item}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* PLATFORMS TAB */}
        {activeTab === "platforms" && (
          <div>
            <SectionTitle icon="☰">Platform Comparison</SectionTitle>

            {/* Platform Selector */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(4, 1fr)",
                gap: 8,
                marginBottom: 20,
              }}
            >
              {platforms.map((p) => (
                <Card
                  key={p.id}
                  onClick={() => setActivePlatform(p.id)}
                  active={activePlatform === p.id}
                  style={{ padding: "14px 16px", textAlign: "center" }}
                >
                  <div style={{ fontSize: 24, marginBottom: 6 }}>{p.icon}</div>
                  <div
                    style={{
                      fontSize: 13,
                      fontWeight: 700,
                      color:
                        activePlatform === p.id ? p.color : COLORS.textDim,
                    }}
                  >
                    {p.name}
                  </div>
                  <Badge color={p.color} style={{ marginTop: 6 }}>
                    {p.rating}
                  </Badge>
                </Card>
              ))}
            </div>

            {/* Platform Detail */}
            {selectedPlatform && (
              <Card
                style={{
                  borderTop: `2px solid ${selectedPlatform.color}`,
                }}
              >
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: 24,
                  }}
                >
                  {/* Pros */}
                  <div>
                    <div
                      style={{
                        fontSize: 11,
                        fontWeight: 700,
                        color: COLORS.accent,
                        fontFamily: "monospace",
                        textTransform: "uppercase",
                        letterSpacing: 1,
                        marginBottom: 12,
                      }}
                    >
                      ✓ Advantages
                    </div>
                    {selectedPlatform.pros.map((pro, i) => (
                      <div
                        key={i}
                        style={{
                          display: "flex",
                          alignItems: "flex-start",
                          gap: 8,
                          marginBottom: 8,
                          fontSize: 12,
                          color: COLORS.textDim,
                          lineHeight: 1.5,
                        }}
                      >
                        <span
                          style={{
                            color: COLORS.accent,
                            fontSize: 8,
                            marginTop: 4,
                          }}
                        >
                          ●
                        </span>
                        {pro}
                      </div>
                    ))}
                  </div>

                  {/* Cons */}
                  <div>
                    <div
                      style={{
                        fontSize: 11,
                        fontWeight: 700,
                        color: COLORS.danger,
                        fontFamily: "monospace",
                        textTransform: "uppercase",
                        letterSpacing: 1,
                        marginBottom: 12,
                      }}
                    >
                      ✗ Limitations
                    </div>
                    {selectedPlatform.cons.map((con, i) => (
                      <div
                        key={i}
                        style={{
                          display: "flex",
                          alignItems: "flex-start",
                          gap: 8,
                          marginBottom: 8,
                          fontSize: 12,
                          color: COLORS.textDim,
                          lineHeight: 1.5,
                        }}
                      >
                        <span
                          style={{
                            color: COLORS.danger,
                            fontSize: 8,
                            marginTop: 4,
                          }}
                        >
                          ●
                        </span>
                        {con}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Footer meta */}
                <div
                  style={{
                    display: "flex",
                    gap: 24,
                    marginTop: 20,
                    paddingTop: 16,
                    borderTop: `1px solid ${COLORS.border}`,
                  }}
                >
                  <div>
                    <span
                      style={{
                        fontSize: 10,
                        color: COLORS.textMuted,
                        fontFamily: "monospace",
                      }}
                    >
                      EFFORT:{" "}
                    </span>
                    <Badge color={selectedPlatform.color}>
                      {selectedPlatform.effort}
                    </Badge>
                  </div>
                  <div>
                    <span
                      style={{
                        fontSize: 10,
                        color: COLORS.textMuted,
                        fontFamily: "monospace",
                      }}
                    >
                      BEST FIT:{" "}
                    </span>
                    <span style={{ fontSize: 12, color: COLORS.textDim }}>
                      {selectedPlatform.fit}
                    </span>
                  </div>
                  <div>
                    <span
                      style={{
                        fontSize: 10,
                        color: COLORS.textMuted,
                        fontFamily: "monospace",
                      }}
                    >
                      DEPLOY:{" "}
                    </span>
                    <code
                      style={{
                        fontSize: 11,
                        color: selectedPlatform.color,
                        background: selectedPlatform.color + "15",
                        padding: "2px 8px",
                        borderRadius: 4,
                      }}
                    >
                      {selectedPlatform.deploy}
                    </code>
                  </div>
                </div>
              </Card>
            )}

            {/* Bridge Tools */}
            <div style={{ marginTop: 24 }}>
              <SectionTitle icon="🔧">
                Bridge Tools (stdio → Remote)
              </SectionTitle>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(3, 1fr)",
                  gap: 12,
                }}
              >
                {[
                  {
                    name: "Supergateway",
                    pkg: "npx supergateway",
                    desc: "Wraps any stdio server as SSE or Streamable HTTP. Zero code changes. Docker-ready.",
                    lang: "Node.js",
                  },
                  {
                    name: "mcp-proxy",
                    pkg: "pip install mcp-proxy",
                    desc: "Python bridge — bidirectional stdio↔HTTP. Can aggregate multiple named servers.",
                    lang: "Python",
                  },
                  {
                    name: "mcp-remote",
                    pkg: "npx mcp-remote",
                    desc: "Client-side: local stdio → remote HTTP. How Claude Desktop connects to remote servers.",
                    lang: "Node.js",
                  },
                ].map((tool) => (
                  <Card key={tool.name} style={{ padding: 16 }}>
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        marginBottom: 8,
                      }}
                    >
                      <span
                        style={{
                          fontWeight: 700,
                          fontSize: 14,
                          color: COLORS.text,
                        }}
                      >
                        {tool.name}
                      </span>
                      <Badge>{tool.lang}</Badge>
                    </div>
                    <code
                      style={{
                        fontSize: 10,
                        color: COLORS.accent,
                        display: "block",
                        marginBottom: 8,
                        background: COLORS.accentDim,
                        padding: "4px 8px",
                        borderRadius: 4,
                      }}
                    >
                      {tool.pkg}
                    </code>
                    <div
                      style={{
                        fontSize: 11,
                        color: COLORS.textDim,
                        lineHeight: 1.6,
                      }}
                    >
                      {tool.desc}
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* SECURITY TAB */}
        {activeTab === "security" && (
          <div>
            <SectionTitle icon="◈">
              9-Layer Defense-in-Depth Model
            </SectionTitle>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(3, 1fr)",
                gap: 10,
                marginBottom: 28,
              }}
            >
              {securityLayers.map((layer, i) => (
                <Card key={i} style={{ padding: 14 }}>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                      marginBottom: 6,
                    }}
                  >
                    <span
                      style={{
                        width: 22,
                        height: 22,
                        borderRadius: 4,
                        background: COLORS.accentDim,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: 12,
                        fontWeight: 700,
                        color: COLORS.accent,
                        fontFamily: "monospace",
                      }}
                    >
                      {i + 1}
                    </span>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>
                      {layer.icon} {layer.name}
                    </span>
                  </div>
                  <div
                    style={{
                      fontSize: 11,
                      color: COLORS.textDim,
                      paddingLeft: 30,
                      lineHeight: 1.5,
                    }}
                  >
                    {layer.desc}
                  </div>
                </Card>
              ))}
            </div>

            {/* Threat Model */}
            <SectionTitle icon="⚠️">
              Remote Deployment Threat Model
            </SectionTitle>
            <Card>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(2, 1fr)",
                  gap: 12,
                }}
              >
                {[
                  {
                    threat: "SSRF via OAuth Metadata Discovery",
                    severity: "HIGH",
                    mitigation:
                      "Validate all URLs, restrict to known auth servers",
                    color: COLORS.danger,
                  },
                  {
                    threat: "Session Hijacking",
                    severity: "HIGH",
                    mitigation:
                      "Rotate Mcp-Session-Id, bind to client fingerprint",
                    color: COLORS.danger,
                  },
                  {
                    threat: "Prompt Injection via Tool Inputs",
                    severity: "MEDIUM",
                    mitigation:
                      "Input validation on all tool params, sanitize before SDK calls",
                    color: COLORS.warning,
                  },
                  {
                    threat: "Confused Deputy (Proxy Client ID)",
                    severity: "MEDIUM",
                    mitigation:
                      "Per-user token scoping, resource indicators (RFC 8707)",
                    color: COLORS.warning,
                  },
                  {
                    threat: "Credential Exposure in Logs",
                    severity: "HIGH",
                    mitigation:
                      "Redact secrets from all log output, use structured logging",
                    color: COLORS.danger,
                  },
                  {
                    threat: "DNS Rebinding",
                    severity: "MEDIUM",
                    mitigation:
                      "Origin header validation (403 on mismatch) — MCP spec mandated",
                    color: COLORS.warning,
                  },
                ].map((t, i) => (
                  <div
                    key={i}
                    style={{
                      background: t.color + "08",
                      border: `1px solid ${t.color}22`,
                      borderRadius: 6,
                      padding: 12,
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        marginBottom: 6,
                      }}
                    >
                      <span
                        style={{
                          fontSize: 12,
                          fontWeight: 600,
                          color: COLORS.text,
                        }}
                      >
                        {t.threat}
                      </span>
                      <Badge color={t.color}>{t.severity}</Badge>
                    </div>
                    <div
                      style={{
                        fontSize: 11,
                        color: COLORS.textDim,
                        lineHeight: 1.5,
                      }}
                    >
                      ↳ {t.mitigation}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        )}

        {/* DEPLOY PLAN TAB */}
        {activeTab === "plan" && (
          <div>
            <SectionTitle icon="▸">
              Phased Deployment Roadmap
            </SectionTitle>
            {[
              {
                phase: "Phase 1 — Zero-Change Wrap",
                duration: "1-2 days",
                color: COLORS.accent,
                steps: [
                  "Install Supergateway or mcp-proxy as transport bridge",
                  "Wrap existing zscaler-mcp stdio server → Streamable HTTP",
                  "Dockerize: base Python image + zscaler-mcp + bridge binary",
                  "Bind to 0.0.0.0:8000 with --transport streamable-http",
                  "Test with mcp-remote from Claude Desktop locally",
                ],
                output:
                  "Docker image exposing /mcp endpoint, running existing Python server unchanged",
              },
              {
                phase: "Phase 2 — Auth + TLS",
                duration: "2-3 days",
                color: COLORS.info,
                steps: [
                  "Add reverse proxy (Caddy/Traefik) for automatic TLS via Let's Encrypt",
                  "Implement OAuth 2.1 middleware or API key auth at the proxy layer",
                  "Configure Origin header validation whitelist",
                  "Store Zscaler credentials in secrets manager (not env vars)",
                  "Enable structured JSON logging with correlation IDs",
                ],
                output:
                  "Authenticated, TLS-encrypted remote endpoint with audit logging",
              },
              {
                phase: "Phase 3 — Platform Deploy",
                duration: "1-2 days",
                color: COLORS.purple,
                steps: [
                  "Push Docker image to ECR/GHCR/Docker Hub",
                  "Deploy to target: ECS Fargate / Cloud Run / fly.io / k8s",
                  "OR: Use AWS Lambda stdio adapter for serverless",
                  "OR: Use MCPJungle gateway for multi-server aggregation",
                  "Configure health checks, auto-restart, and scaling policies",
                ],
                output:
                  "Production deployment on chosen cloud platform with scaling",
              },
              {
                phase: "Phase 4 — Open Source Packaging",
                duration: "3-5 days",
                color: COLORS.orange,
                steps: [
                  "Create GitHub repo with deployment templates for each platform",
                  "docker-compose.yml for self-hosted (Supergateway + Caddy + Zscaler MCP)",
                  "AWS CDK / CloudFormation template (Lambda + API GW + Secrets Manager)",
                  "Cloudflare Workers template (TS wrapper + wrangler.toml)",
                  "Terraform modules for ECS/Fargate deployment",
                  "Write deployment guide + security hardening checklist",
                ],
                output:
                  "One-click deployable open-source repo with multi-platform support",
              },
            ].map((phase, i) => (
              <Card
                key={i}
                onClick={() =>
                  setExpandedPhase(expandedPhase === i ? -1 : i)
                }
                active={expandedPhase === i}
                style={{
                  marginBottom: 10,
                  borderLeft: `3px solid ${phase.color}`,
                  cursor: "pointer",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 12,
                    }}
                  >
                    <span
                      style={{
                        width: 28,
                        height: 28,
                        borderRadius: 6,
                        background: phase.color + "20",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: 13,
                        fontWeight: 800,
                        color: phase.color,
                        fontFamily: "monospace",
                      }}
                    >
                      {i + 1}
                    </span>
                    <span
                      style={{
                        fontSize: 15,
                        fontWeight: 700,
                        color: COLORS.text,
                      }}
                    >
                      {phase.phase}
                    </span>
                  </div>
                  <div
                    style={{ display: "flex", alignItems: "center", gap: 12 }}
                  >
                    <Badge color={phase.color}>{phase.duration}</Badge>
                    <span
                      style={{
                        color: COLORS.textMuted,
                        fontSize: 14,
                        transform:
                          expandedPhase === i
                            ? "rotate(90deg)"
                            : "rotate(0deg)",
                        transition: "transform 0.2s ease",
                      }}
                    >
                      ▸
                    </span>
                  </div>
                </div>

                {expandedPhase === i && (
                  <div style={{ marginTop: 16, paddingLeft: 40 }}>
                    {phase.steps.map((step, j) => (
                      <div
                        key={j}
                        style={{
                          display: "flex",
                          alignItems: "flex-start",
                          gap: 10,
                          marginBottom: 8,
                          fontSize: 12,
                          color: COLORS.textDim,
                          lineHeight: 1.5,
                        }}
                      >
                        <span
                          style={{
                            color: phase.color,
                            fontFamily: "monospace",
                            fontSize: 10,
                            marginTop: 3,
                            flexShrink: 0,
                          }}
                        >
                          {String(j + 1).padStart(2, "0")}
                        </span>
                        {step}
                      </div>
                    ))}
                    <div
                      style={{
                        marginTop: 12,
                        padding: "10px 14px",
                        background: phase.color + "0a",
                        border: `1px solid ${phase.color}22`,
                        borderRadius: 6,
                        fontSize: 11,
                        color: phase.color,
                      }}
                    >
                      <span style={{ fontWeight: 700 }}>OUTPUT → </span>
                      {phase.output}
                    </div>
                  </div>
                )}
              </Card>
            ))}

            {/* Quick Start Command */}
            <div style={{ marginTop: 24 }}>
              <SectionTitle icon="⚡">
                Quickstart (Zero Code Changes)
              </SectionTitle>
              <Card
                style={{
                  background: "#0d1117",
                  fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                  fontSize: 12,
                  lineHeight: 2,
                  overflow: "auto",
                }}
              >
                <div style={{ color: COLORS.textMuted }}># 1. Docker wrap with Supergateway</div>
                <div>
                  <span style={{ color: COLORS.accent }}>$</span>{" "}
                  <span style={{ color: COLORS.text }}>
                    docker run -p 8000:8000 \
                  </span>
                </div>
                <div style={{ paddingLeft: 20, color: COLORS.purple }}>
                  -e ZIA_USERNAME=... -e ZIA_PASSWORD=... \
                </div>
                <div style={{ paddingLeft: 20, color: COLORS.purple }}>
                  supercorp/supergateway \
                </div>
                <div style={{ paddingLeft: 20, color: COLORS.orange }}>
                  --stdio "zscaler-mcp --services zia,zpa,zdx" \
                </div>
                <div style={{ paddingLeft: 20, color: COLORS.orange }}>
                  --outputTransport streamableHttp --port 8000
                </div>
                <div style={{ height: 12 }} />
                <div style={{ color: COLORS.textMuted }}>
                  # 2. Connect from Claude Desktop via mcp-remote
                </div>
                <div>
                  <span style={{ color: COLORS.accent }}>$</span>{" "}
                  <span style={{ color: COLORS.text }}>
                    npx mcp-remote https://your-server.com/mcp
                  </span>
                </div>
              </Card>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
