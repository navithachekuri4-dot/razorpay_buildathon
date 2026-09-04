import { formatINR } from "./MetricCards.jsx";

function BarRow({ label, value, max, sub, tone = "accent" }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0;
  return (
    <div className="bar-row">
      <div className="bar-row-labels">
        <span className="bar-row-label capitalize">{label.replaceAll("_", " ")}</span>
        <span className="bar-row-value num">{sub}</span>
      </div>
      <div className="bar-track">
        <div className={`bar-fill bar-fill--${tone}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function AnalyticsView({ metrics }) {
  if (!metrics) return null;

  const byReason = Object.entries(metrics.recovery_by_failure_reason || {});
  const maxProcessed = Math.max(1, ...byReason.map(([, v]) => v.processed));

  const byStrategy = Object.entries(metrics.recovery_by_strategy || {});
  const maxStrategyCount = Math.max(1, ...byStrategy.map(([, v]) => v));

  const amountByStrategy = Object.entries(metrics.amount_recovered_by_strategy || {});
  const maxAmount = Math.max(1, ...amountByStrategy.map(([, v]) => v));

  return (
    <div className="view-stack">
      <section className="panel">
        <h2 className="panel-title">Recovery by failure reason</h2>
        <p className="panel-subtext">
          How many transactions were processed per failure reason, and what share was
          recovered — computed live from {metrics.processed_count} processed transactions.
        </p>
        <div className="bar-list">
          {byReason.length === 0 && <p className="empty-hint">No processed transactions yet.</p>}
          {byReason.map(([reason, v]) => (
            <BarRow
              key={reason}
              label={reason}
              value={v.processed}
              max={maxProcessed}
              sub={`${v.recovered}/${v.processed} recovered · ${formatINR(v.recovered_amount)}`}
              tone="accent"
            />
          ))}
        </div>
      </section>

      <div className="row-split">
        <section className="panel">
          <h2 className="panel-title">Transactions by strategy</h2>
          <div className="bar-list">
            {byStrategy.length === 0 && <p className="empty-hint">No processed transactions yet.</p>}
            {byStrategy.map(([strategy, count]) => (
              <BarRow
                key={strategy}
                label={strategy}
                value={count}
                max={maxStrategyCount}
                sub={String(count)}
                tone="guardrail"
              />
            ))}
          </div>
        </section>

        <section className="panel">
          <h2 className="panel-title">Amount recovered by strategy</h2>
          <div className="bar-list">
            {amountByStrategy.length === 0 && (
              <p className="empty-hint">Nothing recovered yet — run a batch first.</p>
            )}
            {amountByStrategy.map(([strategy, amount]) => (
              <BarRow
                key={strategy}
                label={strategy}
                value={amount}
                max={maxAmount}
                sub={formatINR(amount)}
                tone="success"
              />
            ))}
          </div>
        </section>
      </div>

      <section className="panel">
        <h2 className="panel-title">Summary</h2>
        <div className="summary-grid">
          <div>
            <span className="summary-label">Average recovered amount</span>
            <span className="summary-value num">{formatINR(metrics.average_recovered_amount)}</span>
          </div>
          <div>
            <span className="summary-label">AI recommendation acceptance</span>
            <span className="summary-value num">{metrics.ai_recommendation_acceptance_rate}%</span>
          </div>
          <div>
            <span className="summary-label">Guardrail interventions</span>
            <span className="summary-value num">{metrics.guardrail_intervention_count}</span>
          </div>
        </div>
      </section>
    </div>
  );
}
