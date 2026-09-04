export function formatINR(value) {
  if (value === undefined || value === null) return "—";
  return `₹${Number(value).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
}

function Card({ label, value, sub, tone, icon }) {
  return (
    <div className={`metric-card metric-card--${tone}`}>
      <div className="metric-card-top">
        <span className="metric-card-label">{label}</span>
        <span className="metric-card-icon">{icon}</span>
      </div>
      <span className="metric-card-value num">{value}</span>
      <span className="metric-card-sub">{sub}</span>
    </div>
  );
}

export default function MetricCards({ metrics }) {
  if (!metrics) return null;

  return (
    <section className="metric-grid">
      <Card
        label="Recovered revenue"
        value={formatINR(metrics.total_recovered)}
        sub={`${metrics.recovered_count} of ${metrics.total_transactions} transactions`}
        tone="success"
        icon="₹"
      />
      <Card
        label="Revenue at risk"
        value={formatINR(metrics.total_at_risk)}
        sub={`${metrics.guardrail_intervention_count} guardrail interventions`}
        tone="risk"
        icon="!"
      />
      <Card
        label="Recovery rate"
        value={`${metrics.recovery_rate}%`}
        sub={`${metrics.ai_recommendation_acceptance_rate}% AI acceptance`}
        tone="accent"
        icon="↗"
      />
      <Card
        label="Total transactions"
        value={`${metrics.processed_count}/${metrics.total_transactions}`}
        sub="processed of total"
        tone="neutral"
        icon="≡"
      />
    </section>
  );
}
