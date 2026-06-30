"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useMemo, useState } from "react";
import ChatBox from "@/components/chatbox";

type PageKey =
  | "dashboard"
  | "playground"
  | "models"
  | "api-keys"
  | "billing"
  | "usage"
  | "analytics"
  | "logs"
  | "settings"
  | "team"
  | "admin";

type DashboardProps = {
  page: PageKey;
};

const navItems: Array<{ key: PageKey; label: string; href: string; icon: string }> = [
  { key: "dashboard", label: "Dashboard", href: "/dashboard", icon: "D" },
  { key: "playground", label: "Playground", href: "/playground", icon: "P" },
  { key: "models", label: "Models", href: "/models", icon: "M" },
  { key: "api-keys", label: "API Keys", href: "/api-keys", icon: "K" },
  { key: "billing", label: "Billing", href: "/billing", icon: "B" },
  { key: "usage", label: "Usage", href: "/usage", icon: "U" },
  { key: "analytics", label: "Analytics", href: "/analytics", icon: "A" },
  { key: "logs", label: "Logs", href: "/logs", icon: "L" },
  { key: "settings", label: "Settings", href: "/settings", icon: "S" },
  { key: "team", label: "Team", href: "/team", icon: "T" },
  { key: "admin", label: "Admin", href: "/admin", icon: "!" },
];

const metrics = [
  { label: "Requests", value: "2.48M", change: "+18.4%", tone: "good" },
  { label: "Spend", value: "$1,842", change: "-6.1%", tone: "good" },
  { label: "Latency p95", value: "812 ms", change: "+42 ms", tone: "warn" },
  { label: "Success rate", value: "99.93%", change: "+0.08%", tone: "good" },
];

const usageSeries = [42, 58, 51, 76, 83, 69, 92, 88, 104, 97, 119, 132];
const providerSplit = [
  { name: "OpenAI", value: 38, color: "#2563eb" },
  { name: "Anthropic", value: 24, color: "#059669" },
  { name: "Gemini", value: 16, color: "#d97706" },
  { name: "Groq", value: 12, color: "#7c3aed" },
  { name: "Other", value: 10, color: "#64748b" },
];

const models = [
  { provider: "OpenAI", model: "gpt-4o-mini", status: "Healthy", latency: "690 ms", cost: "$0.0006 / 1K out" },
  { provider: "Anthropic", model: "claude-3-5-haiku", status: "Healthy", latency: "741 ms", cost: "$0.004 / 1K out" },
  { provider: "Gemini", model: "gemini-1.5-flash", status: "Healthy", latency: "522 ms", cost: "$0.0003 / 1K out" },
  { provider: "Mistral", model: "mistral-small", status: "Degraded", latency: "1.2 s", cost: "$0.0006 / 1K out" },
  { provider: "Ollama", model: "ollama/local", status: "Local", latency: "214 ms", cost: "$0.0000" },
];

const logs = [
  { time: "14:42:11", level: "info", event: "chat.completed", user: "api-key-prod", model: "gpt-4o-mini" },
  { time: "14:41:58", level: "warn", event: "provider.fallback", user: "api-key-prod", model: "mock" },
  { time: "14:40:07", level: "info", event: "key.rotated", user: "sara@company.com", model: "-" },
  { time: "14:38:29", level: "error", event: "provider.timeout", user: "batch-worker", model: "mistral-small" },
];

const requestLogs = [
  { id: "req_812", route: "/v1/chat", status: "200", latency: "684 ms", user: "prod-key", cost: "$0.0042" },
  { id: "req_811", route: "/v1/chat/stream", status: "200", latency: "421 ms", user: "playground", cost: "$0.0018" },
  { id: "req_810", route: "/billing/usage", status: "200", latency: "37 ms", user: "sara@company.com", cost: "$0.0000" },
  { id: "req_809", route: "/v1/chat", status: "500", latency: "2.8 s", user: "batch-worker", cost: "$0.0000" },
];

const providerLatency = [
  { provider: "OpenAI", latency: 690, tokens: "1.28M", cost: "$482" },
  { provider: "Anthropic", latency: 741, tokens: "842K", cost: "$366" },
  { provider: "Gemini", latency: 522, tokens: "612K", cost: "$104" },
  { provider: "Groq", latency: 288, tokens: "418K", cost: "$72" },
];

const alerts = [
  { severity: "warning", title: "Mistral latency elevated", source: "provider", status: "Open" },
  { severity: "critical", title: "Error rate above 1 percent", source: "api", status: "Acknowledged" },
  { severity: "info", title: "Monthly token usage at 72 percent", source: "billing", status: "Open" },
];

const systemHealth = [
  { label: "API", status: "Healthy", value: "99.93%" },
  { label: "Database", status: "Healthy", value: "18 ms" },
  { label: "Providers", status: "Degraded", value: "7 / 8" },
  { label: "Queue", status: "Healthy", value: "0 pending" },
];

const tokenUsage = [
  { label: "Prompt", value: "1.94M", pct: 62 },
  { label: "Completion", value: "1.18M", pct: 38 },
  { label: "Cached", value: "420K", pct: 14 },
];

const team = [
  { name: "Aarav Mehta", email: "aarav@wefindbest.ai", role: "Owner", status: "Active" },
  { name: "Sara Lin", email: "sara@wefindbest.ai", role: "Admin", status: "Active" },
  { name: "Dev Patel", email: "dev@wefindbest.ai", role: "Developer", status: "Invited" },
];

function PageTitle({ page }: { page: PageKey }) {
  const current = navItems.find((item) => item.key === page);
  return (
    <div>
      <h1>{current?.label}</h1>
      <p>
        {page === "dashboard"
          ? "Live operating view for your AI gateway."
          : `Manage ${current?.label.toLowerCase()} for your AI platform.`}
      </p>
    </div>
  );
}

function StatGrid() {
  return (
    <section className="stat-grid">
      {metrics.map((metric) => (
        <article className="metric-card" key={metric.label}>
          <span>{metric.label}</span>
          <strong>{metric.value}</strong>
          <em data-tone={metric.tone}>{metric.change}</em>
        </article>
      ))}
    </section>
  );
}

function UsageChart() {
  const max = Math.max(...usageSeries);
  const points = usageSeries
    .map((value, index) => {
      const x = (index / (usageSeries.length - 1)) * 100;
      const y = 100 - (value / max) * 86;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <section className="panel chart-panel">
      <div className="panel-heading">
        <div>
          <h2>Gateway Traffic</h2>
          <p>Requests over the last 12 hours</p>
        </div>
        <button className="icon-button" aria-label="Download chart" title="Download chart">
          DL
        </button>
      </div>
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="line-chart" aria-label="Usage chart">
        <polyline points={points} fill="none" stroke="currentColor" strokeWidth="3" />
      </svg>
      <div className="chart-axis">
        <span>03:00</span>
        <span>09:00</span>
        <span>15:00</span>
      </div>
    </section>
  );
}

function ProviderChart() {
  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h2>Provider Mix</h2>
          <p>Share of successful requests</p>
        </div>
      </div>
      <div className="provider-bars">
        {providerSplit.map((provider) => (
          <div key={provider.name}>
            <div className="bar-label">
              <span>{provider.name}</span>
              <strong>{provider.value}%</strong>
            </div>
            <div className="bar-track">
              <span style={{ width: `${provider.value}%`, background: provider.color }} />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function ModelTable() {
  return (
    <section className="panel table-panel">
      <div className="panel-heading">
        <div>
          <h2>Models</h2>
          <p>Provider routing and health</p>
        </div>
      </div>
      <div className="data-table">
        <div className="table-row table-head">
          <span>Provider</span>
          <span>Model</span>
          <span>Status</span>
          <span>Latency</span>
          <span>Cost</span>
        </div>
        {models.map((model) => (
          <div className="table-row" key={`${model.provider}-${model.model}`}>
            <span>{model.provider}</span>
            <span className="mono">{model.model}</span>
            <span>
              <b className="status-dot" data-status={model.status.toLowerCase()} />
              {model.status}
            </span>
            <span>{model.latency}</span>
            <span>{model.cost}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

function LogsTable() {
  return (
    <section className="panel table-panel">
      <div className="panel-heading">
        <div>
          <h2>Recent Logs</h2>
          <p>Gateway events and audit trail</p>
        </div>
      </div>
      <div className="data-table compact">
        {logs.map((log) => (
          <div className="table-row" key={`${log.time}-${log.event}`}>
            <span className="mono">{log.time}</span>
            <span data-level={log.level}>{log.level}</span>
            <span>{log.event}</span>
            <span>{log.user}</span>
            <span className="mono">{log.model}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

function RequestLogTable() {
  return (
    <section className="panel table-panel">
      <div className="panel-heading">
        <div>
          <h2>Request Logs</h2>
          <p>API status, latency, and cost by request</p>
        </div>
      </div>
      <div className="data-table request-table">
        <div className="table-row table-head">
          <span>ID</span>
          <span>Route</span>
          <span>Status</span>
          <span>Latency</span>
          <span>User</span>
          <span>Cost</span>
        </div>
        {requestLogs.map((log) => (
          <div className="table-row" key={log.id}>
            <span className="mono">{log.id}</span>
            <span className="mono">{log.route}</span>
            <span data-level={log.status === "500" ? "error" : "info"}>{log.status}</span>
            <span>{log.latency}</span>
            <span>{log.user}</span>
            <span>{log.cost}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

function AlertsPanel() {
  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h2>Alerts</h2>
          <p>Open operational signals</p>
        </div>
      </div>
      <div className="alert-list">
        {alerts.map((alert) => (
          <div className="alert-row" key={alert.title}>
            <span data-alert={alert.severity}>{alert.severity}</span>
            <div>
              <strong>{alert.title}</strong>
              <p>{alert.source} - {alert.status}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function SystemHealthPanel() {
  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h2>System Health</h2>
          <p>Core dependency status</p>
        </div>
      </div>
      <div className="health-grid">
        {systemHealth.map((item) => (
          <div className="health-row" key={item.label}>
            <span>{item.label}</span>
            <strong>{item.value}</strong>
            <em data-health={item.status.toLowerCase()}>{item.status}</em>
          </div>
        ))}
      </div>
    </section>
  );
}

function TokenUsagePanel() {
  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h2>Token Usage</h2>
          <p>Monthly token mix</p>
        </div>
      </div>
      <div className="provider-bars">
        {tokenUsage.map((item) => (
          <div key={item.label}>
            <div className="bar-label">
              <span>{item.label}</span>
              <strong>{item.value}</strong>
            </div>
            <div className="bar-track">
              <span style={{ width: `${item.pct}%` }} />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function ProviderLatencyPanel() {
  const max = Math.max(...providerLatency.map((provider) => provider.latency));
  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h2>Provider Latency</h2>
          <p>Average completion latency</p>
        </div>
      </div>
      <div className="provider-bars">
        {providerLatency.map((provider) => (
          <div key={provider.provider}>
            <div className="bar-label">
              <span>{provider.provider}</span>
              <strong>{provider.latency} ms</strong>
            </div>
            <div className="bar-track">
              <span style={{ width: `${(provider.latency / max) * 100}%` }} />
            </div>
            <p className="inline-meta">{provider.tokens} tokens - {provider.cost}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function CostDashboardPanel() {
  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h2>Cost Dashboard</h2>
          <p>Estimated provider spend</p>
        </div>
      </div>
      <div className="cost-grid">
        <div>
          <span>Month to date</span>
          <strong>$1,284</strong>
        </div>
        <div>
          <span>Projected</span>
          <strong>$2,410</strong>
        </div>
        <div>
          <span>Avg request</span>
          <strong>$0.0028</strong>
        </div>
      </div>
    </section>
  );
}

function DashboardHome() {
  return (
    <>
      <StatGrid />
      <div className="content-grid">
        <UsageChart />
        <SystemHealthPanel />
      </div>
      <div className="content-grid">
        <ProviderLatencyPanel />
        <AlertsPanel />
      </div>
      <RequestLogTable />
    </>
  );
}

function PlaygroundPage() {
  return (
    <section className="playground-layout">
      <div className="panel playground-config">
        <h2>Request</h2>
        <label>
          Provider
          <select defaultValue="mock">
            <option>mock</option>
            <option>openai</option>
            <option>anthropic</option>
            <option>gemini</option>
            <option>mistral</option>
            <option>cohere</option>
            <option>groq</option>
            <option>ollama</option>
            <option>openrouter</option>
          </select>
        </label>
        <label>
          Model
          <input defaultValue="mock" />
        </label>
        <label>
          Temperature
          <input type="range" min="0" max="2" step="0.1" defaultValue="0.7" />
        </label>
      </div>
      <div className="panel chat-panel">
        <ChatBox />
      </div>
    </section>
  );
}

function APIKeysPage() {
  return (
    <section className="panel table-panel">
      <div className="panel-heading">
        <div>
          <h2>API Keys</h2>
          <p>Create, rotate, and revoke gateway credentials</p>
        </div>
        <button className="primary-button">New key</button>
      </div>
      <div className="key-list">
        {["Production", "Staging", "Analytics worker"].map((name, index) => (
          <div className="key-row" key={name}>
            <span className="key-icon">K</span>
            <div>
              <strong>{name}</strong>
              <p className="mono">wfb_{index === 0 ? "prod" : index === 1 ? "stage" : "worker"}_**********</p>
            </div>
            <span>{index === 2 ? "7d ago" : "Today"}</span>
            <button className="ghost-button">Rotate</button>
          </div>
        ))}
      </div>
    </section>
  );
}

function BillingPage() {
  return (
    <>
      <div className="content-grid">
        <section className="panel">
          <h2>Current Plan</h2>
          <div className="billing-price">$249</div>
          <p>Scale plan with 10M monthly gateway requests.</p>
          <button className="primary-button">Manage plan</button>
        </section>
        <section className="panel">
          <h2>Invoice Summary</h2>
          <div className="invoice-row"><span>Model usage</span><strong>$1,284</strong></div>
          <div className="invoice-row"><span>Gateway platform</span><strong>$249</strong></div>
          <div className="invoice-row"><span>Credits</span><strong>-$120</strong></div>
        </section>
      </div>
      <div className="content-grid">
        <CostDashboardPanel />
        <TokenUsagePanel />
      </div>
    </>
  );
}

function UsagePage() {
  return (
    <>
      <StatGrid />
      <div className="content-grid">
        <UsageChart />
        <TokenUsagePanel />
      </div>
      <CostDashboardPanel />
    </>
  );
}

function AnalyticsPage() {
  return (
    <>
      <div className="content-grid">
        <UsageChart />
        <ProviderLatencyPanel />
      </div>
      <div className="content-grid">
        <section className="panel">
          <h2>Top Routes</h2>
          <div className="provider-bars">
            {["/v1/chat", "/v1/chat/stream", "/auth/login", "/v1/providers/health"].map((route, index) => (
              <div key={route}>
                <div className="bar-label"><span>{route}</span><strong>{[51, 26, 14, 9][index]}%</strong></div>
                <div className="bar-track"><span style={{ width: `${[51, 26, 14, 9][index]}%` }} /></div>
              </div>
            ))}
          </div>
        </section>
        <AlertsPanel />
      </div>
    </>
  );
}

function SettingsPage() {
  return (
    <section className="settings-grid">
      {["Gateway routing", "Fallback policy", "Security", "Notifications"].map((name) => (
        <div className="panel settings-panel" key={name}>
          <h2>{name}</h2>
          <label>
            Enabled
            <input type="checkbox" defaultChecked />
          </label>
          <label>
            Value
            <input defaultValue={name === "Fallback policy" ? "mock" : "default"} />
          </label>
        </div>
      ))}
    </section>
  );
}

function TeamPage() {
  return (
    <section className="panel table-panel">
      <div className="panel-heading">
        <div>
          <h2>Team Members</h2>
          <p>Organization roles and invitations</p>
        </div>
        <button className="primary-button">Invite</button>
      </div>
      <div className="data-table">
        {team.map((member) => (
          <div className="table-row" key={member.email}>
            <span>{member.name}</span>
            <span>{member.email}</span>
            <span>{member.role}</span>
            <span>{member.status}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

function AdminPage() {
  return (
    <>
      <StatGrid />
      <div className="content-grid">
        <SystemHealthPanel />
        <AlertsPanel />
      </div>
      <RequestLogTable />
      <div className="content-grid">
        <LogsTable />
        <section className="panel control-panel">
          <h2>Controls</h2>
          <button className="danger-button">Disable provider</button>
          <button className="ghost-button">Export audit logs</button>
          <button className="ghost-button">Review team roles</button>
        </section>
      </div>
    </>
  );
}

function PageContent({ page }: { page: PageKey }) {
  switch (page) {
    case "dashboard":
      return <DashboardHome />;
    case "playground":
      return <PlaygroundPage />;
    case "models":
      return (
        <>
          <ModelTable />
          <ProviderChart />
        </>
      );
    case "api-keys":
      return <APIKeysPage />;
    case "billing":
      return <BillingPage />;
    case "usage":
      return <UsagePage />;
    case "analytics":
      return <AnalyticsPage />;
    case "logs":
      return (
        <>
          <RequestLogTable />
          <LogsTable />
        </>
      );
    case "settings":
      return <SettingsPage />;
    case "team":
      return <TeamPage />;
    case "admin":
      return <AdminPage />;
  }
}

export default function SaaSDashboard({ page }: DashboardProps) {
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [dark, setDark] = useState(false);
  const [query, setQuery] = useState("");
  const filteredNav = useMemo(
    () => navItems.filter((item) => item.label.toLowerCase().includes(query.toLowerCase())),
    [query],
  );

  return (
    <main className="saas-shell" data-theme={dark ? "dark" : "light"}>
      <aside className={`sidebar ${sidebarOpen ? "open" : ""}`}>
        <div className="brand">
          <span>W</span>
          <div>
            <strong>WeFindBest</strong>
            <small>AI Gateway</small>
          </div>
        </div>
        <nav>
          {filteredNav.map((item) => (
            <Link
              key={item.key}
              className={pathname === item.href ? "active" : ""}
              href={item.href}
              onClick={() => setSidebarOpen(false)}
            >
              <span aria-hidden="true">{item.icon}</span>
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <button className="icon-button mobile-menu" onClick={() => setSidebarOpen((value) => !value)} aria-label="Open navigation" title="Open navigation">
            M
          </button>
          <div className="search-box">
            <span aria-hidden="true">Q</span>
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search pages, models, logs..." />
          </div>
          <button className="icon-button" onClick={() => setDark((value) => !value)} aria-label="Toggle theme" title="Toggle theme">
            {dark ? "L" : "D"}
          </button>
          <button className="notification-button" aria-label="Notifications" title="Notifications">
            !
            <span />
          </button>
        </header>

        <div className="page-header">
          <PageTitle page={page} />
          <div className="page-actions">
            <button className="ghost-button">Export</button>
            <button className="primary-button">Create</button>
          </div>
        </div>

        <div className="page-content">
          <PageContent page={page} />
        </div>
      </section>
    </main>
  );
}
