export default function OperationsBreakdown({ metrics }) {
  if (!metrics) return null;
  const total = metrics.processed_count || 1;

  const tiles = [
    { label: "Recovered", value: metrics.recovered_count, tone: "success" },
    { label: "Escalated", value: metrics.escalated_count, tone: "escalate" },
    { label: "Guardrail blocked", value: metrics.safely_stopped_count, tone: "guardrail" },
    { label: "Failed", value: metrics.failed_count, tone: "risk" },
  ];

  return (
    <section className="panel">
      <h2 className="panel-title">Recovery operations</h2>
      <div className="ops-grid">
        {tiles.map((tile) => (
          <div className={`ops-tile ops-tile--${tile.tone}`} key={tile.label}>
            <span className="ops-value num">{tile.value}</span>
            <span className="ops-label">{tile.label}</span>
            <span className="ops-pct num">
              {total ? Math.round((tile.value / total) * 100) : 0}% of total
            </span>
          </div>
        ))}
      </div>
      <p className="ops-footnote">
        "Guardrail blocked" means the agent chose not to act — protecting customers from
        unnecessary retries.
      </p>
    </section>
  );
}
