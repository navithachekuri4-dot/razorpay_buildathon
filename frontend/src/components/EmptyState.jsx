export default function EmptyState({ onSeed, seeding }) {
  return (
    <section className="empty-state panel">
      <div className="empty-state-icon">₹</div>
      <h2>No transactions yet</h2>
      <p>
        Seed the demo dataset to load 120 synthetic failed payments and start the recovery
        pipeline. Nothing here is real customer data or real money.
      </p>
      <button className="batch-button" onClick={onSeed} disabled={seeding}>
        {seeding ? "Seeding…" : "Seed demo data"}
      </button>
    </section>
  );
}
