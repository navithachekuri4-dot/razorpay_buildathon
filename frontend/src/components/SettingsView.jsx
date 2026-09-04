export default function SettingsView() {
  const rows = [
    { label: "Max retry count", value: "3", source: "MAX_RETRY_COUNT" },
    { label: "AI diagnosis model", value: "Gemini (rule-based fallback if unavailable)", source: "GEMINI_API_KEY / GEMINI_MODEL" },
    { label: "Payment integration", value: "Razorpay Test Mode + Simulation", source: "RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET" },
    { label: "Live key protection", value: "rzp_live_ keys are rejected at startup", source: "razorpay_service.py" },
    { label: "Database", value: "SQLite (demo) — swappable via DATABASE_URL", source: "DATABASE_URL" },
  ];

  return (
    <div className="view-stack">
      <section className="panel">
        <h2 className="panel-title">Configuration</h2>
        <p className="panel-subtext">
          This project's safety configuration is intentionally not editable from the UI —
          it lives in backend environment variables so it can't be loosened accidentally
          from the browser. This page reflects the current values for transparency.
        </p>
        <table className="settings-table">
          <thead>
            <tr>
              <th>Setting</th>
              <th>Current value</th>
              <th>Configured via</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.label}>
                <td>{r.label}</td>
                <td className="mono">{r.value}</td>
                <td className="mono settings-source">{r.source}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
