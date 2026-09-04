export default function SafetyControls({ compact }) {
  const controls = [
    { label: "Max retries", value: "3" },
    { label: "Opt-out protection", value: "Active" },
    { label: "Double-charge protection", value: "Active" },
    { label: "Payment mode", value: "Razorpay Test Mode + Simulation" },
  ];

  return (
    <section className={`panel safety-panel ${compact ? "safety-panel--compact" : ""}`}>
      <div className="safety-panel-head">
        <h2 className="panel-title">Safety controls</h2>
        <span className="safety-shield" aria-hidden="true">🛡</span>
      </div>
      <p className="safety-note">
        Deterministic rules that decide what actually touches money — no exceptions.
      </p>
      <ul className="safety-list">
        {controls.map((c) => (
          <li className="safety-row" key={c.label}>
            <span className="safety-check">✓</span>
            <span className="safety-label">{c.label}</span>
            <span className="safety-value mono">{c.value}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
