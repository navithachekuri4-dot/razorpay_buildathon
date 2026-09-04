import { useState } from "react";
import { api } from "../api.js";

const STEP_LABELS = {
  DETECT: "Detect",
  RISK_ASSESSMENT: "Risk assessment",
  AI_DIAGNOSIS: "AI diagnosis",
  STRATEGY: "Strategy",
  SAFETY_CHECK: "Safety check",
  EXECUTION: "Execution",
  VERIFICATION: "Verification",
};

export default function AuditLogsView({ transactions }) {
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState(null);
  const [audit, setAudit] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const processed = transactions.filter((t) => t.processed_at);
  const suggestions = processed
    .filter((t) =>
      query ? t.transaction_id.toLowerCase().includes(query.toLowerCase()) : true
    )
    .slice(0, 8);

  const load = async (id) => {
    setSelectedId(id);
    setLoading(true);
    setError(null);
    try {
      const result = await api.getAudit(id);
      setAudit(result);
    } catch {
      setError("Could not load audit trail for this transaction.");
      setAudit(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="view-stack">
      <div className="row-split">
        <section className="panel">
          <h2 className="panel-title">Find a transaction</h2>
          <input
            className="queue-search audit-search"
            type="text"
            placeholder="Search processed transaction IDs…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <div className="audit-suggestion-list">
            {suggestions.length === 0 && (
              <p className="empty-hint">
                {processed.length === 0
                  ? "No processed transactions yet — run a recovery batch first."
                  : "No matches."}
              </p>
            )}
            {suggestions.map((t) => (
              <button
                key={t.transaction_id}
                className={`audit-suggestion ${
                  selectedId === t.transaction_id ? "audit-suggestion--active" : ""
                }`}
                onClick={() => load(t.transaction_id)}
              >
                <span className="mono">{t.transaction_id}</span>
                <span className="capitalize audit-suggestion-reason">
                  {t.failure_reason.replaceAll("_", " ")}
                </span>
                <span className={`badge badge--${(t.recovery_result || "pending").toLowerCase() === "recovered" ? "success" : "pending"}`}>
                  {t.recovery_result || "PENDING"}
                </span>
              </button>
            ))}
          </div>
        </section>

        <section className="panel">
          <h2 className="panel-title">Audit trail</h2>
          {!selectedId && <p className="empty-hint">Select a transaction to view its audit trail.</p>}
          {loading && <p className="empty-hint">Loading…</p>}
          {error && <p className="empty-hint">{error}</p>}
          {audit && !loading && (
            <div className="audit-trail-table-wrap">
              <table className="audit-trail-table">
                <thead>
                  <tr>
                    <th>Step</th>
                    <th>Status</th>
                    <th>Message</th>
                    <th>Mode</th>
                    <th>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {audit.steps.map((step, i) => (
                    <tr key={i}>
                      <td>{STEP_LABELS[step.step] || step.step}</td>
                      <td>
                        <span
                          className={
                            step.status === "BLOCKED" ? "timeline-status timeline-status--blocked" : "timeline-status"
                          }
                        >
                          {step.status}
                        </span>
                      </td>
                      <td className="audit-message-cell">{step.message}</td>
                      <td className="mono">{step.execution_mode || "—"}</td>
                      <td className="mono">{new Date(step.timestamp).toLocaleTimeString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
