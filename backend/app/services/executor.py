"""
Recovery Executor.

Takes the single final_action that survived the safety guardrails and
performs it. This module has no opinion about whether the action is a
good idea — that judgment already happened upstream. Its only job is to
carry it out through the Razorpay service layer (or simulation) and
report a raw outcome for the Verifier to interpret.
"""
from dataclasses import dataclass
from typing import Optional

from app.services.razorpay_service import razorpay_service


@dataclass
class ExecutionRecord:
    action_taken: str
    execution_mode: Optional[str]
    raw_success: Optional[bool]
    reference_id: Optional[str]
    detail: str


def execute(*, action: str, transaction_id: str, amount: float, customer_id: str) -> ExecutionRecord:
    if action in ("retry_now", "retry_after_delay"):
        outcome = razorpay_service.create_recovery_order(
            transaction_id=transaction_id, amount=amount
        )
        return ExecutionRecord(
            action_taken=action,
            execution_mode=outcome.execution_mode,
            raw_success=outcome.success,
            reference_id=outcome.reference_id,
            detail=outcome.detail,
        )

    if action == "send_update_card_link":
        outcome = razorpay_service.create_payment_link(
            transaction_id=transaction_id, amount=amount, customer_id=customer_id
        )
        return ExecutionRecord(
            action_taken=action,
            execution_mode=outcome.execution_mode,
            raw_success=outcome.success,
            reference_id=outcome.reference_id,
            detail=outcome.detail,
        )

    if action == "verify_then_decide":
        outcome = razorpay_service.verify_payment_status(transaction_id=transaction_id)
        return ExecutionRecord(
            action_taken=action,
            execution_mode=outcome.execution_mode,
            raw_success=outcome.success,
            reference_id=outcome.reference_id,
            detail=outcome.detail,
        )

    if action == "escalate":
        return ExecutionRecord(
            action_taken=action,
            execution_mode=None,
            raw_success=None,
            reference_id=None,
            detail="No automated action taken. Routed to a human operator for review.",
        )

    # stop_no_retry (and any unexpected value, defensively)
    return ExecutionRecord(
        action_taken="stop_no_retry",
        execution_mode=None,
        raw_success=None,
        reference_id=None,
        detail="No action taken. A safety guardrail prevented automated recovery.",
    )
