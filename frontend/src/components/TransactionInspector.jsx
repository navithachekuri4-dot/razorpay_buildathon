import { formatINR } from "./MetricCards.jsx";

const STEP_LABELS = {
  DETECT: "Detect",
  RISK_ASSESSMENT: "AI Diagnosis prep · Risk",
  AI_DIAGNOSIS: "AI Diagnosis",
  STRATEGY: "Recovery Decision",
  SAFETY_CHECK: "Safety / Guardrails",
  EXECUTION: "Action",
  VERIFICATION: "Result",
};
const STEP_ORDER = [
  "DETECT",
  "RISK_ASSESSMENT",
  "AI_DIAGNOSIS",
  "STRATEGY",
  "SAFETY_CHECK",
  "EXECUTION",
  "VERIFICATION",
];

function riskTone(level) {
  if (level === "CRITICAL" || level === "HIGH") return "risk";
  if (level === "MEDIUM") return "escalate";
  return "neutral";
}

function resultTone(result) {
  switch (result) {
    case "RECOVERED":
      return "success";
    case "ESCALATED":
      return "escalate";
    case "SKIPPED":
      return "guardrail";
    case "FAILED":
      return "risk";
    default:
      return "neutral";
  }
}

export default function TransactionInspector({ transaction, audit, loading, onClose }) {
  if (!transaction) return null;

  return (
    <div className="inspector-backdrop" onClick={onClose}>
      <aside className="inspector" onClick={(e) => e.stopPropagation()}>
        <div className="inspector-header">
          <div>
            <span className="inspector-eyebrow mono">{transaction.transaction_id}</span>
            <h2 className="inspector-amount num">{formatINR(transaction.amount)}</h2>
            <div className="inspector-tags">
              <span className="inspector-tag capitalize">
                {transaction.failure_reason.replaceAll("_", " ")}
              </span>
              <span className={`inspector-tag inspector-tag--${riskTone(transaction.risk_level)}`}>
                {transaction.risk_level || "—"} risk
              </span>
            </div>
          </div>
          <button className="inspector-close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>

        {loading && <p className="inspector-loading">Loading transaction detail…</p>}

        {!loading && (
          <div className="inspector-body">
            {/* AI LAYER */}
            <div className="layer-block layer-block--ai">
              <div className="layer-block-head">
                <span className="layer-chip layer-chip--ai">AI LAYER</span>
              </div>
              <p className="layer-main">{transaction.ai_diagnosis || "No diagnosis recorded yet."}</p>
              {transaction.ai_recommended_action && (
                <div className="layer-kv">
                  <span>AI recommendation</span>
                  <span className="mono">{transaction.ai_recommended_action}</span>
                </div>
              )}
              <div className="layer-kv-row">
                <span className="layer-kv-small">
                  Confidence <strong>{transaction.ai_confidence ?? "—"}</strong>
                </span>
                <span className="layer-kv-small">
                  Source <span className="mono">{transaction.ai_source}</span>
                </span>
              </div>
            </div>

            {/* DETERMINISTIC SAFETY LAYER */}
            <div
              className={`layer-block layer-block--safety ${
                transaction.guardrail_decision === "BLOCKED" ? "layer-block--blocked" : ""
              }`}
            >
              <div className="layer-block-head">
                <span className="layer-chip layer-chip--safety">DETERMINISTIC SAFETY LAYER</span>
                <span
                  className={`safety-decision-pill ${
                    transaction.guardrail_decision === "BLOCKED"
                      ? "safety-decision-pill--blocked"
                      : "safety-decision-pill--allowed"
                  }`}
                >
                  {transaction.guardrail_decision || "—"}
                </span>
              </div>
              <div className="layer-kv">
                <span>Final action</span>
                <span className="mono">{transaction.recovery_action || "—"}</span>
              </div>
              {transaction.guardrail_reason && (
                <p className="layer-reason">{transaction.guardrail_reason}</p>
              )}
            </div>

            {/* ACTION / VERIFICATION / RESULT */}
            <div className="layer-block layer-block--neutral">
              <div className="layer-block-head">
                <span className="layer-chip layer-chip--neutral">EXECUTION</span>
              </div>
              <div className="layer-kv">
                <span>Action executed</span>
                <span className="mono">
                  {transaction.execution_mode ? transaction.recovery_action : "Not executed"}
                </span>
              </div>
              <div className="layer-kv">
                <span>Mode</span>
                <span className="mono">{transaction.execution_mode || "—"}</span>
              </div>
            </div>

            <div className={`result-block result-block--${resultTone(transaction.recovery_result)}`}>
              <span className="result-label">Verification result</span>
              <span className="result-value">{transaction.recovery_result || "PENDING"}</span>
              {transaction.recovered_amount != null && (
                <span className="result-amount num">
                  ₹ Recovered: {formatINR(transaction.recovered_amount)}
                </span>
              )}
            </div>

            {/* Timeline */}
            <div className="timeline">
              <h3 className="timeline-title">Decision timeline</h3>
              {(!audit || audit.steps.length === 0) && (
                <p className="layer-reason">This transaction has not been processed yet.</p>
              )}
              {audit &&
                STEP_ORDER.map((stepKey, i) => {
                  const step = audit.steps.find((s) => s.step === stepKey);
                  if (!step) return null;
                  return (
                    <div className="timeline-row" key={stepKey}>
                      <div className="timeline-marker">
                        <span
                          className={`timeline-dot ${
                            step.status === "BLOCKED" ? "timeline-dot--blocked" : "timeline-dot--ok"
                          }`}
                        >
                          {String(i + 1).padStart(2, "0")}
                        </span>
                        {i < STEP_ORDER.length - 1 && <span className="timeline-line" />}
                      </div>
                      <div className="timeline-content">
                        <div className="timeline-content-head">
                          <span className="timeline-step-label">{STEP_LABELS[stepKey]}</span>
                          <span
                            className={`timeline-status ${
                              step.status === "BLOCKED" ? "timeline-status--blocked" : ""
                            }`}
                          >
                            {step.status}
                          </span>
                        </div>
                        <p className="timeline-message">{step.message}</p>
                        <span className="timeline-time mono">
                          {new Date(step.timestamp).toLocaleString()}
                          {step.execution_mode ? ` · ${step.execution_mode}` : ""}
                        </span>
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>
        )}
      </aside>
    </div>
  );
}
