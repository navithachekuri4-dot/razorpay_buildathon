from app.models import AuditLog
from app.services.orchestrator import process_transaction
from tests.conftest import make_txn


def test_full_pipeline_runs_all_seven_steps(db_session):
    txn = make_txn(transaction_id="TXN_PIPE_0001")
    db_session.add(txn)
    db_session.commit()

    result = process_transaction(db_session, txn)

    assert result.risk_score is not None
    assert result.ai_recommended_action is not None
    assert result.recovery_action is not None
    assert result.recovery_result in ("RECOVERED", "FAILED", "ESCALATED", "SKIPPED")
    assert result.processed_at is not None

    logs = (
        db_session.query(AuditLog)
        .filter(AuditLog.transaction_id == "TXN_PIPE_0001")
        .order_by(AuditLog.timestamp.asc())
        .all()
    )
    steps = [l.step for l in logs]
    assert steps == [
        "DETECT", "RISK_ASSESSMENT", "AI_DIAGNOSIS", "STRATEGY",
        "SAFETY_CHECK", "EXECUTION", "VERIFICATION",
    ]


def test_opted_out_customer_is_never_charged(db_session):
    txn = make_txn(transaction_id="TXN_PIPE_OPTOUT", customer_opted_out=True)
    db_session.add(txn)
    db_session.commit()

    result = process_transaction(db_session, txn)

    assert result.recovery_result == "SKIPPED"
    assert result.recovered_amount is None
    assert result.guardrail_decision == "BLOCKED"


def test_uncertain_deduction_never_blindly_retried(db_session):
    txn = make_txn(
        transaction_id="TXN_PIPE_UNCERTAIN",
        payment_status="uncertain",
        failure_reason="deducted_status_unclear",
    )
    db_session.add(txn)
    db_session.commit()

    result = process_transaction(db_session, txn)

    assert result.recovery_action == "verify_then_decide"
    assert result.recovery_result in ("RECOVERED", "ESCALATED")


def test_retry_limit_exceeded_escalates_instead_of_retrying(db_session):
    txn = make_txn(transaction_id="TXN_PIPE_RETRYLIMIT", retry_count=5, failure_reason="bank_timeout")
    db_session.add(txn)
    db_session.commit()

    result = process_transaction(db_session, txn)

    assert result.recovery_action in ("escalate", "stop_no_retry")
    assert result.recovery_result in ("ESCALATED", "SKIPPED")


def test_already_recovered_transaction_is_not_processed_again(db_session):
    txn = make_txn(transaction_id="TXN_PIPE_IDEMPOTENT")
    db_session.add(txn)
    db_session.commit()

    first = process_transaction(db_session, txn)
    first.recovery_result = "RECOVERED"
    first.recovered_amount = first.amount
    db_session.commit()

    second = process_transaction(db_session, first)
    assert second.guardrail_decision == "BLOCKED"
    assert second.recovery_action == "stop_no_retry"
