"""
Pipeline Orchestrator.

Runs the full DETECT -> DIAGNOSE -> DECIDE -> SAFETY -> ACT -> VERIFY ->
RECOVER pipeline for one transaction, writing an AuditLog row at every
step. This is the only module that mutates a Transaction's outcome
fields, and it is the one place you can read top-to-bottom to see the
entire agent behavior for a single piece of at-risk revenue.
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Transaction, AuditLog
from app.services import risk_engine, ai_diagnosis, strategy, guardrails, executor, verifier


def _log(db: Session, transaction_id: str, step: str, status: str, message: str, execution_mode=None):
    entry = AuditLog(
        transaction_id=transaction_id,
        step=step,
        status=status,
        message=message,
        execution_mode=execution_mode,
    )
    db.add(entry)


def process_transaction(db: Session, txn: Transaction) -> Transaction:
    # --- 1. DETECT ---
    _log(
        db, txn.transaction_id, "DETECT", "OK",
        f"Detected at-risk revenue: ₹{txn.amount:,.2f} ({txn.failure_reason}).",
    )

    # --- 2. RISK ASSESSMENT ---
    risk = risk_engine.assess_risk(
        amount=txn.amount,
        failure_reason=txn.failure_reason,
        retry_count=txn.retry_count,
        payment_status=txn.payment_status,
        customer_opted_out=txn.customer_opted_out,
    )
    txn.risk_score = risk.risk_score
    txn.risk_level = risk.risk_level
    _log(
        db, txn.transaction_id, "RISK_ASSESSMENT", "OK",
        f"Risk score {risk.risk_score}/100 ({risk.risk_level}). Breakdown: {risk.breakdown}.",
    )

    # --- 3. AI DIAGNOSIS ---
    diagnosis = ai_diagnosis.diagnose(
        {
            "amount": txn.amount,
            "failure_reason": txn.failure_reason,
            "payment_status": txn.payment_status,
            "retry_count": txn.retry_count,
            "previous_attempts": txn.previous_attempts,
            "customer_opted_out": txn.customer_opted_out,
        }
    )
    txn.ai_diagnosis = diagnosis.likely_cause
    txn.ai_recommended_action = diagnosis.recommended_action
    txn.ai_confidence = diagnosis.confidence
    txn.ai_source = diagnosis.source
    _log(
        db, txn.transaction_id, "AI_DIAGNOSIS", "OK",
        f"[{diagnosis.source}] Cause: {diagnosis.likely_cause} | "
        f"Recommended: {diagnosis.recommended_action} (confidence {diagnosis.confidence}) | "
        f"Reasoning: {diagnosis.reasoning}",
    )

    # --- 4. STRATEGY ---
    strat = strategy.decide_strategy(
        failure_reason=txn.failure_reason, ai_action=diagnosis.recommended_action
    )
    _log(
        db, txn.transaction_id, "STRATEGY", "OK",
        f"Proposed action: {strat.action} (source: {strat.source}). {strat.note}",
    )

    # --- 5. SAFETY CHECK (deterministic guardrails) ---
    already_recovered = txn.recovery_result == "RECOVERED"
    guard = guardrails.apply_guardrails(
        proposed_action=strat.action,
        payment_status=txn.payment_status,
        customer_opted_out=txn.customer_opted_out,
        retry_count=txn.retry_count,
        already_recovered=already_recovered,
    )
    txn.recovery_action = guard.final_action
    txn.guardrail_decision = guard.decision
    txn.guardrail_reason = guard.reason
    _log(
        db, txn.transaction_id, "SAFETY_CHECK",
        "BLOCKED" if guard.decision == "BLOCKED" else "OK",
        f"Decision: {guard.decision}. Final action: {guard.final_action}. Reason: {guard.reason}",
    )

    # --- 6. EXECUTION ---
    if guard.final_action in ("retry_now", "retry_after_delay"):
        txn.retry_count += 1

    exec_record = executor.execute(
        action=guard.final_action,
        transaction_id=txn.transaction_id,
        amount=txn.amount,
        customer_id=txn.customer_id,
    )
    txn.execution_mode = exec_record.execution_mode
    _log(
        db, txn.transaction_id, "EXECUTION", "OK",
        f"Action taken: {exec_record.action_taken}. {exec_record.detail}"
        + (f" Reference: {exec_record.reference_id}." if exec_record.reference_id else ""),
        execution_mode=exec_record.execution_mode,
    )

    # --- 7. VERIFICATION ---
    verification = verifier.verify(execution=exec_record, amount=txn.amount)
    txn.recovery_result = verification.result
    txn.recovered_amount = verification.recovered_amount
    if verification.result == "RECOVERED":
        txn.payment_status = "captured"
    txn.processed_at = datetime.now(timezone.utc)
    _log(
        db, txn.transaction_id, "VERIFICATION", "OK",
        f"Final result: {verification.result}. {verification.message}"
        + (f" Recovered ₹{verification.recovered_amount:,.2f}." if verification.recovered_amount else ""),
    )

    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn
