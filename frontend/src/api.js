const BASE = "/api";

async function request(path, options = {}) {
  const resp = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!resp.ok) {
    let detail = resp.statusText;
    try {
      const body = await resp.json();
      detail = body.detail || detail;
    } catch {
      // ignore parse failure, keep statusText
    }
    throw new Error(detail);
  }
  return resp.json();
}

export const api = {
  health: () => request("/health"),
  seed: (count = 120) => request(`/seed?count=${count}`, { method: "POST" }),
  listTransactions: (params = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== "")
    ).toString();
    return request(`/transactions${qs ? `?${qs}` : ""}`);
  },
  getTransaction: (id) => request(`/transactions/${id}`),
  recoverOne: (id) => request(`/recover/${id}`, { method: "POST" }),
  recoverBatch: (limit = 200) =>
    request(`/recover/batch?limit=${limit}`, { method: "POST" }),
  getAudit: (id) => request(`/audit/${id}`),
  getMetrics: () => request("/metrics"),
};
