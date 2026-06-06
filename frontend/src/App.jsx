import {
  Activity,
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Clock,
  Database,
  GitBranch,
  LayoutDashboard,
  Plus,
  RefreshCw,
  Rocket,
  Server,
  ShieldAlert,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "./api.js";

const views = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "services", label: "Services", icon: Server },
  { id: "incidents", label: "Incidents", icon: ShieldAlert },
  { id: "incident-detail", label: "Incident Detail", icon: Clock },
  { id: "deployments", label: "Deployments", icon: Rocket },
  { id: "metrics", label: "Metrics", icon: BarChart3 },
];

const emptyService = {
  name: "",
  owner: "",
  environment: "production",
  status: "healthy",
  slo_target: 99.9,
  service_url: "",
  current_version: "v1.0.0",
};

const emptyIncident = {
  service_id: "",
  title: "",
  severity: "P2",
  status: "investigating",
};

const emptyDeployment = {
  service_id: "",
  version: "",
  commit_sha: "",
  status: "success",
};

function formatDate(value) {
  if (!value) return "Not set";
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function statusClass(status) {
  return `status status-${String(status).replace("_", "-")}`;
}

function severityClass(severity) {
  return `severity severity-${String(severity).toLowerCase()}`;
}

function App() {
  const [activeView, setActiveView] = useState("dashboard");
  const [services, setServices] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [deployments, setDeployments] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [selectedIncidentId, setSelectedIncidentId] = useState(null);
  const [incidentDetail, setIncidentDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const [serviceForm, setServiceForm] = useState(emptyService);
  const [incidentForm, setIncidentForm] = useState(emptyIncident);
  const [deploymentForm, setDeploymentForm] = useState(emptyDeployment);
  const [timelineForm, setTimelineForm] = useState({
    message: "",
    status: "identified",
  });

  const serviceById = useMemo(
    () => Object.fromEntries(services.map((service) => [service.id, service])),
    [services],
  );

  const selectedIncident =
    incidentDetail || incidents.find((incident) => incident.id === selectedIncidentId);

  const refreshAll = useCallback(async () => {
    setError("");
    setLoading(true);
    try {
      const [nextMetrics, nextServices, nextIncidents, nextDeployments] =
        await Promise.all([
          api.getMetrics(),
          api.getServices(),
          api.getIncidents(),
          api.getDeployments(),
        ]);
      setMetrics(nextMetrics);
      setServices(nextServices);
      setIncidents(nextIncidents);
      setDeployments(nextDeployments);
      if (!selectedIncidentId && nextIncidents.length > 0) {
        setSelectedIncidentId(nextIncidents[0].id);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [selectedIncidentId]);

  useEffect(() => {
    refreshAll();
  }, [refreshAll]);

  useEffect(() => {
    if (!selectedIncidentId) return;
    api
      .getIncident(selectedIncidentId)
      .then(setIncidentDetail)
      .catch((err) => setError(err.message));
  }, [selectedIncidentId]);

  async function handleCreateService(event) {
    event.preventDefault();
    const payload = {
      ...serviceForm,
      slo_target: Number(serviceForm.slo_target),
      service_url: serviceForm.service_url || null,
    };
    await api.createService(payload);
    setServiceForm(emptyService);
    setNotice("Service created");
    await refreshAll();
  }

  async function handleServiceStatus(serviceId, status) {
    await api.updateServiceStatus(serviceId, status);
    setNotice("Service status updated");
    await refreshAll();
  }

  async function handleCreateIncident(event) {
    event.preventDefault();
    await api.createIncident({
      ...incidentForm,
      service_id: Number(incidentForm.service_id),
    });
    setIncidentForm(emptyIncident);
    setNotice("Incident created");
    await refreshAll();
  }

  async function handleCreateDeployment(event) {
    event.preventDefault();
    await api.createDeployment({
      ...deploymentForm,
      service_id: Number(deploymentForm.service_id),
    });
    setDeploymentForm(emptyDeployment);
    setNotice("Deployment registered");
    await refreshAll();
  }

  async function handleTimelineUpdate(event) {
    event.preventDefault();
    if (!selectedIncidentId) return;
    await api.addIncidentUpdate(selectedIncidentId, timelineForm);
    setTimelineForm({ message: "", status: timelineForm.status });
    setNotice("Timeline updated");
    await refreshAll();
    setIncidentDetail(await api.getIncident(selectedIncidentId));
  }

  async function handleResolveIncident() {
    if (!selectedIncidentId) return;
    await api.resolveIncident(selectedIncidentId, {
      message: "Incident resolved and service restored.",
    });
    setNotice("Incident resolved");
    await refreshAll();
    setIncidentDetail(await api.getIncident(selectedIncidentId));
  }

  const uptimePercent =
    metrics && metrics.total_services
      ? ((metrics.healthy_services / metrics.total_services) * 100).toFixed(2)
      : "0.00";

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <Activity size={22} />
          </div>
          <div>
            <strong>CloudOps</strong>
            <span>SRE Platform</span>
          </div>
        </div>
        <nav className="nav-list" aria-label="Primary">
          {views.map((view) => {
            const Icon = view.icon;
            return (
              <button
                key={view.id}
                className={activeView === view.id ? "nav-item active" : "nav-item"}
                onClick={() => setActiveView(view.id)}
                type="button"
              >
                <Icon size={18} />
                <span>{view.label}</span>
              </button>
            );
          })}
        </nav>
      </aside>

      <main className="content">
        <header className="topbar">
          <div>
            <p className="eyebrow">Reliability Operations</p>
            <h1>{views.find((view) => view.id === activeView)?.label}</h1>
          </div>
          <div className="topbar-actions">
            {metrics && (
              <span className={statusClass(metrics.current_platform_status)}>
                {metrics.current_platform_status}
              </span>
            )}
            <button className="icon-button" onClick={refreshAll} type="button" title="Refresh data">
              <RefreshCw size={18} />
            </button>
          </div>
        </header>

        {error && <div className="alert error">{error}</div>}
        {notice && <div className="alert success">{notice}</div>}
        {loading && <div className="loading">Loading platform data...</div>}

        {!loading && activeView === "dashboard" && (
          <Dashboard
            deployments={deployments}
            incidents={incidents}
            metrics={metrics}
            serviceById={serviceById}
            services={services}
            setActiveView={setActiveView}
            setSelectedIncidentId={setSelectedIncidentId}
          />
        )}

        {!loading && activeView === "services" && (
          <Services
            form={serviceForm}
            onChange={setServiceForm}
            onSubmit={handleCreateService}
            onStatusChange={handleServiceStatus}
            services={services}
          />
        )}

        {!loading && activeView === "incidents" && (
          <Incidents
            form={incidentForm}
            incidents={incidents}
            onChange={setIncidentForm}
            onSubmit={handleCreateIncident}
            serviceById={serviceById}
            services={services}
            setActiveView={setActiveView}
            setSelectedIncidentId={setSelectedIncidentId}
          />
        )}

        {!loading && activeView === "incident-detail" && (
          <IncidentDetail
            detail={selectedIncident}
            form={timelineForm}
            incidents={incidents}
            onChange={setTimelineForm}
            onResolve={handleResolveIncident}
            onSelect={setSelectedIncidentId}
            onSubmit={handleTimelineUpdate}
            serviceById={serviceById}
            selectedIncidentId={selectedIncidentId}
          />
        )}

        {!loading && activeView === "deployments" && (
          <Deployments
            deployments={deployments}
            form={deploymentForm}
            onChange={setDeploymentForm}
            onSubmit={handleCreateDeployment}
            serviceById={serviceById}
            services={services}
          />
        )}

        {!loading && activeView === "metrics" && (
          <Metrics metrics={metrics} uptimePercent={uptimePercent} />
        )}
      </main>
    </div>
  );
}

function MetricCard({ icon: Icon, label, value, tone }) {
  return (
    <section className={`metric-card ${tone || ""}`}>
      <div className="metric-icon">
        <Icon size={19} />
      </div>
      <span>{label}</span>
      <strong>{value}</strong>
    </section>
  );
}

function Dashboard({
  deployments,
  incidents,
  metrics,
  serviceById,
  services,
  setActiveView,
  setSelectedIncidentId,
}) {
  return (
    <div className="stack">
      <section className="metrics-grid">
        <MetricCard icon={Database} label="Total services" value={metrics?.total_services ?? 0} />
        <MetricCard
          icon={CheckCircle2}
          label="Healthy services"
          tone="good"
          value={metrics?.healthy_services ?? 0}
        />
        <MetricCard
          icon={AlertTriangle}
          label="Degraded/down"
          tone="warn"
          value={metrics?.degraded_down_services ?? 0}
        />
        <MetricCard
          icon={ShieldAlert}
          label="Open incidents"
          tone="bad"
          value={metrics?.open_incidents ?? 0}
        />
        <MetricCard
          icon={Clock}
          label="Average MTTR"
          value={
            metrics?.average_mttr_minutes
              ? `${metrics.average_mttr_minutes} min`
              : "No resolved"
          }
        />
        <MetricCard
          icon={GitBranch}
          label="Failed deploys"
          tone="bad"
          value={metrics?.failed_deployments ?? 0}
        />
      </section>

      <div className="split-grid">
        <section className="panel">
          <PanelHeader title="Service Health" />
          <table>
            <thead>
              <tr>
                <th>Service</th>
                <th>Owner</th>
                <th>Status</th>
                <th>SLO</th>
                <th>Version</th>
              </tr>
            </thead>
            <tbody>
              {services.map((service) => (
                <tr key={service.id}>
                  <td>{service.name}</td>
                  <td>{service.owner}</td>
                  <td>
                    <span className={statusClass(service.status)}>{service.status}</span>
                  </td>
                  <td>{service.slo_target}%</td>
                  <td>{service.current_version}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="panel">
          <PanelHeader title="Recent Incidents" />
          <div className="compact-list">
            {incidents.slice(0, 5).map((incident) => (
              <button
                className="list-row"
                key={incident.id}
                onClick={() => {
                  setSelectedIncidentId(incident.id);
                  setActiveView("incident-detail");
                }}
                type="button"
              >
                <span>
                  <strong>{incident.title}</strong>
                  <small>{serviceById[incident.service_id]?.name || "Unknown service"}</small>
                </span>
                <span className={severityClass(incident.severity)}>{incident.severity}</span>
              </button>
            ))}
          </div>
        </section>
      </div>

      <section className="panel">
        <PanelHeader title="Recent Deployments" />
        <table>
          <thead>
            <tr>
              <th>Service</th>
              <th>Version</th>
              <th>Commit</th>
              <th>Status</th>
              <th>Deployed</th>
            </tr>
          </thead>
          <tbody>
            {deployments.slice(0, 6).map((deployment) => (
              <tr key={deployment.id}>
                <td>{serviceById[deployment.service_id]?.name || "Unknown service"}</td>
                <td>{deployment.version}</td>
                <td>
                  <code>{deployment.commit_sha}</code>
                </td>
                <td>
                  <span className={statusClass(deployment.status)}>{deployment.status}</span>
                </td>
                <td>{formatDate(deployment.deployed_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

function PanelHeader({ title }) {
  return (
    <div className="panel-header">
      <h2>{title}</h2>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
    </label>
  );
}

function Services({ form, onChange, onSubmit, onStatusChange, services }) {
  return (
    <div className="stack">
      <section className="panel">
        <PanelHeader title="Create Service" />
        <form className="form-grid" onSubmit={onSubmit}>
          <Field label="Name">
            <input
              required
              value={form.name}
              onChange={(event) => onChange({ ...form, name: event.target.value })}
            />
          </Field>
          <Field label="Owner">
            <input
              required
              value={form.owner}
              onChange={(event) => onChange({ ...form, owner: event.target.value })}
            />
          </Field>
          <Field label="Environment">
            <select
              value={form.environment}
              onChange={(event) => onChange({ ...form, environment: event.target.value })}
            >
              <option>production</option>
              <option>staging</option>
              <option>development</option>
            </select>
          </Field>
          <Field label="Status">
            <select
              value={form.status}
              onChange={(event) => onChange({ ...form, status: event.target.value })}
            >
              <option>healthy</option>
              <option>degraded</option>
              <option>down</option>
              <option>maintenance</option>
            </select>
          </Field>
          <Field label="SLO target">
            <input
              max="100"
              min="0"
              step="0.01"
              type="number"
              value={form.slo_target}
              onChange={(event) => onChange({ ...form, slo_target: event.target.value })}
            />
          </Field>
          <Field label="Version">
            <input
              required
              value={form.current_version}
              onChange={(event) => onChange({ ...form, current_version: event.target.value })}
            />
          </Field>
          <Field label="Service URL">
            <input
              type="url"
              value={form.service_url}
              onChange={(event) => onChange({ ...form, service_url: event.target.value })}
            />
          </Field>
          <button className="primary-button" type="submit">
            <Plus size={17} />
            Create
          </button>
        </form>
      </section>

      <section className="panel">
        <PanelHeader title="Service Catalog" />
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Owner</th>
              <th>Environment</th>
              <th>Status</th>
              <th>SLO</th>
              <th>Version</th>
            </tr>
          </thead>
          <tbody>
            {services.map((service) => (
              <tr key={service.id}>
                <td>{service.name}</td>
                <td>{service.owner}</td>
                <td>{service.environment}</td>
                <td>
                  <select
                    className="compact-select"
                    value={service.status}
                    onChange={(event) => onStatusChange(service.id, event.target.value)}
                  >
                    <option>healthy</option>
                    <option>degraded</option>
                    <option>down</option>
                    <option>maintenance</option>
                  </select>
                </td>
                <td>{service.slo_target}%</td>
                <td>{service.current_version}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

function Incidents({
  form,
  incidents,
  onChange,
  onSubmit,
  serviceById,
  services,
  setActiveView,
  setSelectedIncidentId,
}) {
  return (
    <div className="stack">
      <section className="panel">
        <PanelHeader title="Create Incident" />
        <form className="form-grid" onSubmit={onSubmit}>
          <Field label="Service">
            <select
              required
              value={form.service_id}
              onChange={(event) => onChange({ ...form, service_id: event.target.value })}
            >
              <option value="">Select service</option>
              {services.map((service) => (
                <option key={service.id} value={service.id}>
                  {service.name}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Title">
            <input
              required
              value={form.title}
              onChange={(event) => onChange({ ...form, title: event.target.value })}
            />
          </Field>
          <Field label="Severity">
            <select
              value={form.severity}
              onChange={(event) => onChange({ ...form, severity: event.target.value })}
            >
              <option>P1</option>
              <option>P2</option>
              <option>P3</option>
              <option>P4</option>
            </select>
          </Field>
          <Field label="Status">
            <select
              value={form.status}
              onChange={(event) => onChange({ ...form, status: event.target.value })}
            >
              <option>investigating</option>
              <option>identified</option>
              <option>monitoring</option>
            </select>
          </Field>
          <button className="primary-button" type="submit">
            <Plus size={17} />
            Open
          </button>
        </form>
      </section>

      <section className="panel">
        <PanelHeader title="Incident Queue" />
        <table>
          <thead>
            <tr>
              <th>Incident</th>
              <th>Service</th>
              <th>Severity</th>
              <th>Status</th>
              <th>Started</th>
              <th>MTTR</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {incidents.map((incident) => (
              <tr key={incident.id}>
                <td>{incident.title}</td>
                <td>{serviceById[incident.service_id]?.name || "Unknown service"}</td>
                <td>
                  <span className={severityClass(incident.severity)}>{incident.severity}</span>
                </td>
                <td>
                  <span className={statusClass(incident.status)}>{incident.status}</span>
                </td>
                <td>{formatDate(incident.started_at)}</td>
                <td>{incident.mttr_minutes ? `${incident.mttr_minutes} min` : "Open"}</td>
                <td>
                  <button
                    className="table-button"
                    onClick={() => {
                      setSelectedIncidentId(incident.id);
                      setActiveView("incident-detail");
                    }}
                    type="button"
                  >
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

function IncidentDetail({
  detail,
  form,
  incidents,
  onChange,
  onResolve,
  onSelect,
  onSubmit,
  serviceById,
  selectedIncidentId,
}) {
  if (!detail) {
    return (
      <section className="panel">
        <PanelHeader title="Incident Detail" />
        <select value={selectedIncidentId || ""} onChange={(event) => onSelect(Number(event.target.value))}>
          <option value="">Select incident</option>
          {incidents.map((incident) => (
            <option key={incident.id} value={incident.id}>
              {incident.title}
            </option>
          ))}
        </select>
      </section>
    );
  }

  return (
    <div className="stack">
      <section className="panel detail-panel">
        <div className="detail-head">
          <div>
            <div className="detail-select">
              <select value={selectedIncidentId || ""} onChange={(event) => onSelect(Number(event.target.value))}>
                {incidents.map((incident) => (
                  <option key={incident.id} value={incident.id}>
                    {incident.title}
                  </option>
                ))}
              </select>
            </div>
            <h2>{detail.title}</h2>
            <p>{serviceById[detail.service_id]?.name || "Unknown service"}</p>
          </div>
          <div className="detail-badges">
            <span className={severityClass(detail.severity)}>{detail.severity}</span>
            <span className={statusClass(detail.status)}>{detail.status}</span>
          </div>
        </div>
        <div className="detail-stats">
          <MetricCard icon={Clock} label="Started" value={formatDate(detail.started_at)} />
          <MetricCard
            icon={CheckCircle2}
            label="Resolved"
            value={detail.resolved_at ? formatDate(detail.resolved_at) : "Open"}
          />
          <MetricCard
            icon={BarChart3}
            label="MTTR"
            value={detail.mttr_minutes ? `${detail.mttr_minutes} min` : "Open"}
          />
        </div>
      </section>

      <div className="split-grid">
        <section className="panel">
          <PanelHeader title="Timeline" />
          <div className="timeline">
            {(detail.updates || []).map((update) => (
              <article className="timeline-item" key={update.id}>
                <span className={statusClass(update.status)}>{update.status}</span>
                <p>{update.message}</p>
                <small>{formatDate(update.created_at)}</small>
              </article>
            ))}
          </div>
        </section>

        <section className="panel">
          <PanelHeader title="Add Update" />
          <form className="form-stack" onSubmit={onSubmit}>
            <Field label="Status">
              <select
                value={form.status}
                onChange={(event) => onChange({ ...form, status: event.target.value })}
              >
                <option>investigating</option>
                <option>identified</option>
                <option>monitoring</option>
                <option>resolved</option>
              </select>
            </Field>
            <Field label="Message">
              <textarea
                required
                rows="6"
                value={form.message}
                onChange={(event) => onChange({ ...form, message: event.target.value })}
              />
            </Field>
            <div className="button-row">
              <button className="primary-button" type="submit">
                <Plus size={17} />
                Add
              </button>
              <button
                className="secondary-button"
                disabled={detail.status === "resolved"}
                onClick={onResolve}
                type="button"
              >
                <CheckCircle2 size={17} />
                Resolve
              </button>
            </div>
          </form>
        </section>
      </div>
    </div>
  );
}

function Deployments({ deployments, form, onChange, onSubmit, serviceById, services }) {
  return (
    <div className="stack">
      <section className="panel">
        <PanelHeader title="Register Deployment" />
        <form className="form-grid" onSubmit={onSubmit}>
          <Field label="Service">
            <select
              required
              value={form.service_id}
              onChange={(event) => onChange({ ...form, service_id: event.target.value })}
            >
              <option value="">Select service</option>
              {services.map((service) => (
                <option key={service.id} value={service.id}>
                  {service.name}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Version">
            <input
              required
              value={form.version}
              onChange={(event) => onChange({ ...form, version: event.target.value })}
            />
          </Field>
          <Field label="Commit SHA">
            <input
              required
              minLength="7"
              value={form.commit_sha}
              onChange={(event) => onChange({ ...form, commit_sha: event.target.value })}
            />
          </Field>
          <Field label="Status">
            <select
              value={form.status}
              onChange={(event) => onChange({ ...form, status: event.target.value })}
            >
              <option>success</option>
              <option>failed</option>
              <option>rolled_back</option>
              <option>in_progress</option>
            </select>
          </Field>
          <button className="primary-button" type="submit">
            <Plus size={17} />
            Register
          </button>
        </form>
      </section>

      <section className="panel">
        <PanelHeader title="Deployment History" />
        <table>
          <thead>
            <tr>
              <th>Service</th>
              <th>Version</th>
              <th>Commit</th>
              <th>Status</th>
              <th>Deployed</th>
            </tr>
          </thead>
          <tbody>
            {deployments.map((deployment) => (
              <tr key={deployment.id}>
                <td>{serviceById[deployment.service_id]?.name || "Unknown service"}</td>
                <td>{deployment.version}</td>
                <td>
                  <code>{deployment.commit_sha}</code>
                </td>
                <td>
                  <span className={statusClass(deployment.status)}>{deployment.status}</span>
                </td>
                <td>{formatDate(deployment.deployed_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

function Metrics({ metrics, uptimePercent }) {
  const severities = metrics?.open_incidents_by_severity || {};
  const maxSeverity = Math.max(1, ...Object.values(severities));

  return (
    <div className="stack">
      <section className="metrics-grid">
        <MetricCard icon={CheckCircle2} label="Uptime proxy" value={`${uptimePercent}%`} />
        <MetricCard
          icon={Clock}
          label="MTTR"
          value={metrics?.average_mttr_minutes ? `${metrics.average_mttr_minutes} min` : "No data"}
        />
        <MetricCard icon={GitBranch} label="Failed deploys" value={metrics?.failed_deployments ?? 0} />
        <MetricCard icon={ShieldAlert} label="Open incidents" value={metrics?.open_incidents ?? 0} />
      </section>
      <section className="panel">
        <PanelHeader title="Open Incidents By Severity" />
        <div className="bar-list">
          {["P1", "P2", "P3", "P4"].map((severity) => (
            <div className="bar-row" key={severity}>
              <span className={severityClass(severity)}>{severity}</span>
              <div className="bar-track">
                <div
                  className="bar-fill"
                  style={{ width: `${((severities[severity] || 0) / maxSeverity) * 100}%` }}
                />
              </div>
              <strong>{severities[severity] || 0}</strong>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

export default App;
