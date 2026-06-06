const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method || "GET",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    let message = `API request failed with ${response.status}`;
    try {
      const payload = await response.json();
      message = payload.detail || message;
    } catch {
      message = response.statusText || message;
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export const api = {
  getHealth: () => request("/health"),
  getMetrics: () => request("/metrics"),
  getServices: () => request("/services"),
  createService: (body) => request("/services", { method: "POST", body }),
  updateServiceStatus: (id, status) =>
    request(`/services/${id}/status`, { method: "PATCH", body: { status } }),
  getIncidents: () => request("/incidents"),
  createIncident: (body) => request("/incidents", { method: "POST", body }),
  getIncident: (id) => request(`/incidents/${id}`),
  addIncidentUpdate: (id, body) =>
    request(`/incidents/${id}/updates`, { method: "POST", body }),
  resolveIncident: (id, body) =>
    request(`/incidents/${id}/resolve`, { method: "PATCH", body }),
  getDeployments: () => request("/deployments"),
  createDeployment: (body) => request("/deployments", { method: "POST", body }),
};
