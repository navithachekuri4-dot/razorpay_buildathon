import { useState, useMemo, useEffect } from "react";
import { formatINR } from "./MetricCards.jsx";

const FAILURE_REASONS = [
  "expired_card",
  "insufficient_funds",
  "bank_timeout",
  "gateway_error",
  "authentication_failure",
  "payment_method_invalid",
  "network_error",
  "deducted_status_unclear",
];

const STATUSES = ["RECOVERED", "FAILED", "ESCALATED", "SKIPPED"];
const PAGE_SIZE = 8;

function StatusBadge({ result }) {
  if (!result) return <span className="badge badge--pending">PENDING</span>;
  const toneMap = {
    RECOVERED: "success",
    ESCALATED: "escalate",
    SKIPPED: "guardrail",
    FAILED: "risk",
  };
  return <span className={`badge badge--${toneMap[result]}`}>{result}</span>;
}

export default function RecoveryQueue({
  title = "Recovery queue",
  transactions,
  filters,
  onFilterChange,
  onInspect,
  onRecoverOne,
  onRefresh,
  refreshing,
  recoveringId,
}) {
  const [page, setPage] = useState(1);

  useEffect(() => {
    setPage(1);
  }, [filters, transactions.length]);

  const totalPages = Math.max(1, Math.ceil(transactions.length / PAGE_SIZE));
  const pageRows = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE;
    return transactions.slice(start, start + PAGE_SIZE);
  }, [transactions, page]);

  const pageNumbers = useMemo(() => {
    const nums = [];
    for (let i = 1; i <= Math.min(totalPages, 3); i++) nums.push(i);
    return nums;
  }, [totalPages]);

  return (
    <section className="panel queue-panel">
      <div className="queue-header">
        <h2 className="panel-title">
          {title}
          <span className="queue-count-badge">{transactions.length}</span>
        </h2>
        <div className="queue-controls">
          <div className="queue-search-wrap">
            <span className="queue-search-icon">⌕</span>
            <input
              className="queue-search"
              type="text"
              placeholder="Search transaction or customer ID"
              value={filters.search}
              onChange={(e) => onFilterChange({ ...filters, search: e.target.value })}
            />
          </div>
          <select
            className="queue-select"
            value={filters.status}
            onChange={(e) => onFilterChange({ ...filters, status: e.target.value })}
          >
            <option value="">All statuses</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s.charAt(0) + s.slice(1).toLowerCase()}
              </option>
            ))}
          </select>
          <select
            className="queue-select"
            value={filters.failure_reason}
            onChange={(e) => onFilterChange({ ...filters, failure_reason: e.target.value })}
          >
            <option value="">All failure reasons</option>
            {FAILURE_REASONS.map((r) => (
              <option key={r} value={r}>
                {r.replaceAll("_", " ")}
              </option>
            ))}
          </select>
          {onRefresh && (
            <button
              className="queue-refresh"
              onClick={onRefresh}
              disabled={refreshing}
              aria-label="Refresh"
              title="Refresh"
            >
              <span className={refreshing ? "spin-icon" : ""}>⟳</span>
            </button>
          )}
        </div>
      </div>

      <div className="queue-table-wrap">
        <table className="queue-table">
          <thead>
            <tr>
              <th>Txn ID</th>
              <th>Customer</th>
              <th className="num-col">Amount</th>
              <th>Failure reason</th>
              <th>AI action</th>
              <th>Status</th>
              <th>Decision</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {pageRows.length === 0 && (
              <tr>
                <td colSpan={8} className="queue-empty">
                  No transactions match the current filters.
                </td>
              </tr>
            )}
            {pageRows.map((t) => (
              <tr key={t.transaction_id}>
                <td className="mono">{t.transaction_id}</td>
                <td className="mono">{t.customer_id}</td>
                <td className="num-col num">{formatINR(t.amount)}</td>
                <td className="capitalize">{t.failure_reason.replaceAll("_", " ")}</td>
                <td className="mono">{t.ai_recommended_action || "—"}</td>
                <td>
                  <StatusBadge result={t.recovery_result} />
                </td>
                <td>
                  {t.guardrail_decision === "BLOCKED" ? (
                    <span className="decision decision--blocked">Guardrail blocked</span>
                  ) : t.guardrail_decision === "ALLOWED" ? (
                    <span className="decision decision--allowed">Allowed</span>
                  ) : (
                    <span className="decision decision--none">—</span>
                  )}
                </td>
                <td className="queue-actions">
                  <button className="link-button" onClick={() => onInspect(t.transaction_id)}>
                    Inspect
                  </button>
                  {!t.processed_at && (
                    <button
                      className="link-button link-button--muted"
                      onClick={() => onRecoverOne(t.transaction_id)}
                      disabled={recoveringId === t.transaction_id}
                    >
                      {recoveringId === t.transaction_id ? "Running…" : "Recover"}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="queue-footer">
        <span className="queue-footer-text">
          Showing {transactions.length === 0 ? 0 : (page - 1) * PAGE_SIZE + 1}–
          {Math.min(page * PAGE_SIZE, transactions.length)} of {transactions.length} transactions
        </span>
        <div className="pagination">
          <button
            className="page-btn"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            ‹
          </button>
          {pageNumbers.map((n) => (
            <button
              key={n}
              className={`page-btn ${n === page ? "page-btn--active" : ""}`}
              onClick={() => setPage(n)}
            >
              {n}
            </button>
          ))}
          {totalPages > 3 && <span className="page-ellipsis">…</span>}
          {totalPages > 3 && (
            <button
              className={`page-btn ${page === totalPages ? "page-btn--active" : ""}`}
              onClick={() => setPage(totalPages)}
            >
              {totalPages}
            </button>
          )}
          <button
            className="page-btn"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
          >
            ›
          </button>
        </div>
      </div>
    </section>
  );
}
