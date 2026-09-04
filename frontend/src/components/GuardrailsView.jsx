import SafetyControls from "./SafetyControls.jsx";
import { formatINR } from "./MetricCards.jsx";

export default function GuardrailsView({ transactions, onInspect }) {
  const blocked = transactions.filter((t) => t.guardrail_decision === "BLOCKED");

  return (
    <div className="view-stack">
      <div className="row-split">
        <section className="panel">
          <h2 className="panel-title">Guardrail interventions</h2>
          <p className="panel-subtext">
            Every row below is a transaction where the deterministic safety layer
            overrode or confirmed a stop — independent of what the AI recommended.
            {" "}{blocked.length} of {transactions.length} loaded transactions.
          </p>
          <div className="guardrail-list">
            {blocked.length === 0 && (
              <p className="empty-hint">No guardrail interventions in the current dataset.</p>
            )}
            {blocked.map((t) => (
              <button
                key={t.transaction_id}
                className="guardrail-row"
                onClick={() => onInspect(t.transaction_id)}
              >
                <div className="guardrail-row-top">
                  <span className="mono guardrail-row-id">{t.transaction_id}</span>
                  <span className="num guardrail-row-amount">{formatINR(t.amount)}</span>
                </div>
                <p className="guardrail-row-reason">{t.guardrail_reason}</p>
                <span className="guardrail-row-action mono">
                  final action: {t.recovery_action}
                </span>
              </button>
            ))}
          </div>
        </section>

        <SafetyControls />
      </div>
    </div>
  );
}
