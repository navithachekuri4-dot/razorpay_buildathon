import { useEffect, useState, useCallback, useMemo } from "react";
import { api } from "./api.js";
import "./App.css";

import Sidebar from "./components/Sidebar.jsx";
import Header from "./components/Header.jsx";
import MetricCards from "./components/MetricCards.jsx";
import AgentPipeline from "./components/AgentPipeline.jsx";
import OperationsBreakdown from "./components/OperationsBreakdown.jsx";
import SafetyControls from "./components/SafetyControls.jsx";
import BatchRecoveryButton from "./components/BatchRecoveryButton.jsx";
import RecoveryQueue from "./components/RecoveryQueue.jsx";
import TransactionInspector from "./components/TransactionInspector.jsx";
import EmptyState from "./components/EmptyState.jsx";
import AnalyticsView from "./components/AnalyticsView.jsx";
import GuardrailsView from "./components/GuardrailsView.jsx";
import AuditLogsView from "./components/AuditLogsView.jsx";
import SettingsView from "./components/SettingsView.jsx";

const VIEW_META = {
  overview: {
    title: "Revenue Recovery Command Center",
    subtitle: "AI Revenue Recovery Agent — Razorpay Test Mode",
  },
  transactions: { title: "Transactions", subtitle: "Every transaction the agent has seen" },
  queue: { title: "Recovery Queue", subtitle: "Transactions still needing action or escalated" },
  analytics: { title: "Analytics", subtitle: "Recovery performance by reason and strategy" },
  guardrails: { title: "Guardrails", subtitle: "Where deterministic safety overrode or confirmed a stop" },
  audit: { title: "Audit Logs", subtitle: "Full step-by-step trail for any processed transaction" },
  settings: { title: "Settings", subtitle: "Safety configuration (read-only, set via backend env vars)" },
};

export default function App() {
  const [activeView, setActiveView] = useState("overview");

  const [health, setHealth] = useState(false);
  const [metrics, setMetrics] = useState(null);
  const [allTransactions, setAllTransactions] = useState([]);
  const [filters, setFilters] = useState({ search: "", status: "", failure_reason: "" });
  const [seeding, setSeeding] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [batchStatus, setBatchStatus] = useState("idle");
  const [batchResult, setBatchResult] = useState(null);
  const [recoveringId, setRecoveringId] = useState(null);

  const [selectedId, setSelectedId] = useState(null);
  const [selectedTxn, setSelectedTxn] = useState(null);
  const [selectedAudit, setSelectedAudit] = useState(null);
  const [inspectorLoading, setInspectorLoading] = useState(false);

  const refresh = useCallback(async () => {
    setRefreshing(true);
    try {
      const [m, t] = await Promise.all([api.getMetrics(), api.listTransactions({})]);
      setMetrics(m);
      setAllTransactions(t);
      setHealth(true);
    } catch {
      setHealth(false);
    } finally {
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const filteredTransactions = useMemo(() => {
    return allTransactions.filter((t) => {
      if (filters.status && t.recovery_result !== filters.status) return false;
      if (filters.failure_reason && t.failure_reason !== filters.failure_reason) return false;
      if (filters.search) {
        const q = filters.search.toLowerCase();
        if (
          !t.transaction_id.toLowerCase().includes(q) &&
          !t.customer_id.toLowerCase().includes(q)
        ) {
          return false;
        }
      }
      return true;
    });
  }, [allTransactions, filters]);

  const queueTransactions = useMemo(
    () => filteredTransactions.filter((t) => !t.processed_at || t.recovery_result === "ESCALATED"),
    [filteredTransactions]
  );

  const handleSeed = async () => {
    setSeeding(true);
    try {
      await api.seed(120);
      await refresh();
    } finally {
      setSeeding(false);
    }
  };

  const handleRunBatch = async () => {
    setBatchStatus("running");
    try {
      const result = await api.recoverBatch(200);
      setBatchResult(result);
      setBatchStatus("done");
      await refresh();
    } catch {
      setBatchStatus("error");
    }
  };

  const handleRecoverOne = async (id) => {
    setRecoveringId(id);
    try {
      await api.recoverOne(id);
      await refresh();
      if (selectedId === id) openInspector(id);
    } finally {
      setRecoveringId(null);
    }
  };

  const openInspector = async (id) => {
    setSelectedId(id);
    setInspectorLoading(true);
    try {
      const [txn, audit] = await Promise.all([api.getTransaction(id), api.getAudit(id)]);
      setSelectedTxn(txn);
      setSelectedAudit(audit);
    } finally {
      setInspectorLoading(false);
    }
  };

  const closeInspector = () => {
    setSelectedId(null);
    setSelectedTxn(null);
    setSelectedAudit(null);
  };

  const noData = health && metrics && metrics.total_transactions === 0;
  const meta = VIEW_META[activeView];

  return (
    <div className="app-shell">
      <Sidebar active={activeView} onNavigate={setActiveView} />

      <div className="app-main-col">
        <Header health={health} viewTitle={meta.title} viewSubtitle={meta.subtitle} />

        <main className="main">
          {noData ? (
            <EmptyState onSeed={handleSeed} seeding={seeding} />
          ) : (
            <>
              {activeView === "overview" && (
                <>
                  <MetricCards metrics={metrics} />
                  <div className="row-split">
                    <AgentPipeline metrics={metrics} />
                    <SafetyControls compact />
                  </div>
                  <OperationsBreakdown metrics={metrics} />
                  <BatchRecoveryButton
                    onRun={handleRunBatch}
                    status={batchStatus}
                    lastResult={batchResult}
                  />
                  <RecoveryQueue
                    title="Recovery queue"
                    transactions={filteredTransactions}
                    filters={filters}
                    onFilterChange={setFilters}
                    onInspect={openInspector}
                    onRecoverOne={handleRecoverOne}
                    onRefresh={refresh}
                    refreshing={refreshing}
                    recoveringId={recoveringId}
                  />
                </>
              )}

              {activeView === "transactions" && (
                <RecoveryQueue
                  title="Transactions"
                  transactions={filteredTransactions}
                  filters={filters}
                  onFilterChange={setFilters}
                  onInspect={openInspector}
                  onRecoverOne={handleRecoverOne}
                  onRefresh={refresh}
                  refreshing={refreshing}
                  recoveringId={recoveringId}
                />
              )}

              {activeView === "queue" && (
                <RecoveryQueue
                  title="Needs action / escalated"
                  transactions={queueTransactions}
                  filters={filters}
                  onFilterChange={setFilters}
                  onInspect={openInspector}
                  onRecoverOne={handleRecoverOne}
                  onRefresh={refresh}
                  refreshing={refreshing}
                  recoveringId={recoveringId}
                />
              )}

              {activeView === "analytics" && <AnalyticsView metrics={metrics} />}

              {activeView === "guardrails" && (
                <GuardrailsView transactions={allTransactions} onInspect={openInspector} />
              )}

              {activeView === "audit" && <AuditLogsView transactions={allTransactions} />}

              {activeView === "settings" && <SettingsView />}
            </>
          )}
        </main>
      </div>

      {selectedId && (
        <TransactionInspector
          transaction={selectedTxn}
          audit={selectedAudit}
          loading={inspectorLoading}
          onClose={closeInspector}
        />
      )}
    </div>
  );
}
