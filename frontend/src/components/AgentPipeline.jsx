export default function AgentPipeline({ metrics }) {
  if (!metrics) return null;

  const detected = metrics.total_transactions;
  const diagnosed = metrics.processed_count;
  const blocked = metrics.guardrail_intervention_count;
  const acted = metrics.processed_count;
  const recovered = metrics.recovered_count;

  const stages = [
    { n: "01", label: "Detect", value: detected, done: detected > 0 },
    { n: "02", label: "Diagnose", value: diagnosed, done: diagnosed > 0 },
    { n: "03", label: "Decide", value: diagnosed, done: diagnosed > 0 },
    { n: "04", label: "Safety", value: blocked, done: diagnosed > 0, note: true },
    { n: "05", label: "Act", value: acted, done: acted > 0 },
    { n: "06", label: "Verify", value: acted, done: acted > 0 },
    { n: "07", label: "Recovered", value: recovered, done: recovered > 0, highlight: true },
  ];

  return (
    <section className="panel pipeline-panel">
      <h2 className="panel-title">Agent pipeline</h2>
      <div className="pipeline-track">
        {stages.map((stage, i) => (
          <div className="pipeline-item" key={stage.label}>
            <div
              className={`pipeline-card ${stage.highlight ? "pipeline-card--highlight" : ""}`}
            >
              <span className="pipeline-num mono">{stage.n}</span>
              <span className="pipeline-value num">{stage.value}</span>
              <span className="pipeline-label">{stage.label}</span>
              <span
                className={`pipeline-check ${stage.done ? "pipeline-check--on" : ""} ${
                  stage.highlight ? "pipeline-check--highlight" : ""
                }`}
              >
                {stage.done ? "✓" : "·"}
              </span>
            </div>
            {i < stages.length - 1 && <span className="pipeline-arrow">→</span>}
          </div>
        ))}
      </div>
    </section>
  );
}
