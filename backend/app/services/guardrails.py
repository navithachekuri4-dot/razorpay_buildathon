"""
Deterministic Safety Guardrails.

THIS IS THE MOST IMPORTANT FILE IN THE PROJECT.

No AI model output reaches money without passing through here first, and
every rule in this file is plain Python — no prompts, no model calls,
nothing probabilistic. Guardrails run in a fixed priority order and the
first one that fires wins; they can only ever make the action *safer*
(stop/escalate/verify), never riskier.

Priority order and why:
  1. Already recovered  -> stop.        (idempotency / no double-charge)
  2. Opted out           -> stop.        (consent, not negotiable)
  3. Already captured    -> stop.        (don't touch a successful payment)
  4. Uncertain deduction -> verify.      (never blindly retry a possible
                                           double charge)
  5. Retry limit reached -> escalate/stop, EVEN IF the AI said retry.
  6. Otherwise           -> allow the strategy's action through.
"""
from dataclasses import dataclass

from app.config import settings


@dataclass
class GuardrailResult:
    decision: str  # "ALLOWED" | "BLOCKED"
    final_action: str
    reason: str


def apply_guardrails(
    *,
    proposed_action: str,
    payment_status: str,
    customer_opted_out: bool,
    retry_count: int,
    already_recovered: bool,
) -> GuardrailResult:
    if already_recovered:
        return GuardrailResult(
            decision="BLOCKED",
            final_action="stop_no_retry",
            reason="Transaction is already marked RECOVERED — refusing to act again "
                   "to prevent a double charge.",
        )

    if customer_opted_out:
        return GuardrailResult(
            decision="BLOCKED",
            final_action="stop_no_retry",
            reason="Customer has opted out of recovery contact. This overrides any "
                   "AI or strategy recommendation.",
        )

    if payment_status == "captured":
        return GuardrailResult(
            decision="BLOCKED",
            final_action="stop_no_retry",
            reason="Payment is already captured/successful. No action needed or allowed.",
        )

    if payment_status == "uncertain" and proposed_action != "verify_then_decide":
        return GuardrailResult(
            decision="BLOCKED",
            final_action="verify_then_decide",
            reason="Deduction status is unclear. A retry could cause a double charge, "
                   "so the action is forced to verification first.",
        )

    if retry_count >= settings.MAX_RETRY_COUNT and proposed_action in (
        "retry_now",
        "retry_after_delay",
    ):
        return GuardrailResult(
            decision="BLOCKED",
            final_action="escalate",
            reason=f"retry_count ({retry_count}) has reached the maximum allowed "
                   f"({settings.MAX_RETRY_COUNT}). Automated retries are disabled; "
                   f"escalating to a human instead.",
        )

    return GuardrailResult(
        decision="ALLOWED",
        final_action=proposed_action,
        reason="No safety rule blocked this action.",
    )
