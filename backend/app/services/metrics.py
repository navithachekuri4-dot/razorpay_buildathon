"""
Metrics.

Every number here is computed live from the transactions table — nothing
is hardcoded or cached. If a metric can't be computed honestly from
stored data, it isn't included.
"""
from sqlalchemy.orm import Session

from app.models import Transaction, AuditLog


def compute_metrics(db: Session) -> dict:
    all_txns = db.query(Transaction).all()
    total_transactions = len(all_txns)
    total_at_risk = sum(t.amount for t in all_txns)

    processed = [t for t in all_txns if t.processed_at is not None]
    recovered = [t for t in processed if t.recovery_result == "RECOVERED"]
    failed = [t for t in processed if t.recovery_result == "FAILED"]
    escalated = [t for t in processed if t.recovery_result == "ESCALATED"]
    stopped = [t for t in processed if t.recovery_result == "SKIPPED"]

    total_recovered = sum(t.recovered_amount or 0 for t in recovered)
    recovery_rate = round((total_recovered / total_at_risk) * 100, 2) if total_at_risk else 0.0

    guardrail_blocks = (
        db.query(AuditLog)
        .filter(AuditLog.step == "SAFETY_CHECK", AuditLog.status == "BLOCKED")
        .count()
    )

    ai_accepted = len(
        [t for t in processed if t.recovery_action == t.ai_recommended_action]
    )
    ai_acceptance_rate = round((ai_accepted / len(processed)) * 100, 2) if processed else 0.0

    by_reason: dict = {}
    by_strategy: dict = {}
    amount_by_strategy: dict = {}
    for t in processed:
        reason_bucket = by_reason.setdefault(
            t.failure_reason, {"processed": 0, "recovered": 0, "recovered_amount": 0.0}
        )
        reason_bucket["processed"] += 1
        if t.recovery_result == "RECOVERED":
            reason_bucket["recovered"] += 1
            reason_bucket["recovered_amount"] += t.recovered_amount or 0

        strat = t.recovery_action or "unknown"
        by_strategy[strat] = by_strategy.get(strat, 0) + 1
        if t.recovery_result == "RECOVERED":
            amount_by_strategy[strat] = amount_by_strategy.get(strat, 0.0) + (t.recovered_amount or 0)

    avg_recovered = round(total_recovered / len(recovered), 2) if recovered else 0.0

    return {
        "total_transactions": total_transactions,
        "total_at_risk": round(total_at_risk, 2),
        "total_recovered": round(total_recovered, 2),
        "recovery_rate": recovery_rate,
        "processed_count": len(processed),
        "unprocessed_count": total_transactions - len(processed),
        "recovered_count": len(recovered),
        "failed_count": len(failed),
        "escalated_count": len(escalated),
        "safely_stopped_count": len(stopped),
        "guardrail_intervention_count": guardrail_blocks,
        "ai_recommendation_acceptance_rate": ai_acceptance_rate,
        "recovery_by_failure_reason": by_reason,
        "recovery_by_strategy": by_strategy,
        "amount_recovered_by_strategy": {k: round(v, 2) for k, v in amount_by_strategy.items()},
        "average_recovered_amount": avg_recovered,
    }
