export default function BatchRecoveryButton({ onRun, status, lastResult }) {
  return (
    <div className="batch-bar">
      <div className="batch-bar-text">
        {status === "done" && lastResult ? (
          <span className="batch-result">
            <span className="batch-result-check">✓</span>
            Batch complete · <strong>{lastResult.recovered} recovered</strong> ·{" "}
            {lastResult.escalated} escalated · {lastResult.safely_stopped} safely stopped ·{" "}
            {lastResult.failed} failed
          </span>
        ) : status === "error" ? (
          <span className="batch-result batch-result--error">
            Batch failed to run. Check that the backend is reachable.
          </span>
        ) : (
          <span className="batch-result batch-result--muted">
            Processes every unprocessed transaction through the full 7-step pipeline.
          </span>
        )}
      </div>
      <button className="batch-button" onClick={onRun} disabled={status === "running"}>
        {status === "running" && <span className="spinner" aria-hidden="true" />}
        {status === "running" ? "Recovering payments…" : "▶ Run Recovery Batch"}
      </button>
    </div>
  );
}
