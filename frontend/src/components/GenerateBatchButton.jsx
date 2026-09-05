export default function GenerateBatchButton({ onRun, status, lastResult }) {
  return (
    <div className="batch-bar">
      <div className="batch-bar-text">
        {status === "done" && lastResult ? (
          <span className="batch-result">
            <span className="batch-result-check">✓</span>
            {lastResult.message}
          </span>
        ) : status === "error" ? (
          <span className="batch-result batch-result--error">
            Could not generate a new batch. Check that the backend is reachable.
          </span>
        ) : (
          <span className="batch-result batch-result--muted">
            Appends 120 new synthetic transactions without touching existing data.
          </span>
        )}
      </div>
      <button className="batch-button batch-button--secondary" onClick={onRun} disabled={status === "running"}>
        {status === "running" && <span className="spinner spinner--dark" aria-hidden="true" />}
        {status === "running" ? "Generating…" : "+ Generate New Demo Batch"}
      </button>
    </div>
  );
}
