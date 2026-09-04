"""
Payment Result Verifier.

Converts the raw output of the Executor into exactly one of four final
states: RECOVERED, FAILED, ESCALATED, SKIPPED. Recovered amount is always
read from the transaction's own amount field — never invented.
"""
from dataclasses import dataclass
from typing import Optional

from app.services.executor import ExecutionRecord


@dataclass
class VerificationResult:
    result: str  # RECOVERED | FAILED | ESCALATED | SKIPPED
    recovered_amount: Optional[float]
    message: str


def verify(*, execution: ExecutionRecord, amount: float) -> VerificationResult:
    action = execution.action_taken

    if action == "stop_no_retry":
        return VerificationResult(
            result="SKIPPED",
            recovered_amount=None,
            message="Safely stopped by a guardrail. No money moved, no charge attempted.",
        )

    if action == "escalate":
        return VerificationResult(
            result="ESCALATED",
            recovered_amount=None,
            message="Escalated for human review. No automated charge attempted.",
        )

    if action == "verify_then_decide":
        if execution.raw_success:
            return VerificationResult(
                result="RECOVERED",
                recovered_amount=amount,
                message="Verification found the payment was captured. Marked recovered "
                        "without attempting a new charge (avoids double charge).",
            )
        return VerificationResult(
            result="ESCALATED",
            recovered_amount=None,
            message="Verification could not confirm capture. Escalated to a human rather "
                    "than retrying automatically.",
        )

    # retry_now / retry_after_delay / send_update_card_link
    if execution.raw_success:
        return VerificationResult(
            result="RECOVERED",
            recovered_amount=amount,
            message=f"{action.replace('_', ' ').title()} succeeded and payment was confirmed captured.",
        )

    return VerificationResult(
        result="FAILED",
        recovered_amount=None,
        message=f"{action.replace('_', ' ').title()} did not result in a captured payment.",
    )
