from app.config import settings
from app.services import guardrails


def test_opt_out_blocks_any_action():
    result = guardrails.apply_guardrails(
        proposed_action="retry_now", payment_status="failed",
        customer_opted_out=True, retry_count=0, already_recovered=False,
    )
    assert result.decision == "BLOCKED"
    assert result.final_action == "stop_no_retry"


def test_already_captured_blocks_action():
    result = guardrails.apply_guardrails(
        proposed_action="retry_now", payment_status="captured",
        customer_opted_out=False, retry_count=0, already_recovered=False,
    )
    assert result.decision == "BLOCKED"
    assert result.final_action == "stop_no_retry"


def test_uncertain_status_forces_verification():
    result = guardrails.apply_guardrails(
        proposed_action="retry_now", payment_status="uncertain",
        customer_opted_out=False, retry_count=0, already_recovered=False,
    )
    assert result.decision == "BLOCKED"
    assert result.final_action == "verify_then_decide"


def test_uncertain_status_allows_verification_action_through():
    result = guardrails.apply_guardrails(
        proposed_action="verify_then_decide", payment_status="uncertain",
        customer_opted_out=False, retry_count=0, already_recovered=False,
    )
    assert result.decision == "ALLOWED"
    assert result.final_action == "verify_then_decide"


def test_retry_limit_blocks_further_retries():
    result = guardrails.apply_guardrails(
        proposed_action="retry_now", payment_status="failed",
        customer_opted_out=False, retry_count=settings.MAX_RETRY_COUNT, already_recovered=False,
    )
    assert result.decision == "BLOCKED"
    assert result.final_action == "escalate"


def test_already_recovered_blocks_double_charge():
    result = guardrails.apply_guardrails(
        proposed_action="retry_now", payment_status="failed",
        customer_opted_out=False, retry_count=0, already_recovered=True,
    )
    assert result.decision == "BLOCKED"
    assert result.final_action == "stop_no_retry"


def test_normal_case_is_allowed():
    result = guardrails.apply_guardrails(
        proposed_action="retry_after_delay", payment_status="failed",
        customer_opted_out=False, retry_count=1, already_recovered=False,
    )
    assert result.decision == "ALLOWED"
    assert result.final_action == "retry_after_delay"


def test_opt_out_beats_retry_limit_and_everything_else():
    """Opt-out must win even when other rules could also fire."""
    result = guardrails.apply_guardrails(
        proposed_action="retry_now", payment_status="uncertain",
        customer_opted_out=True, retry_count=99, already_recovered=False,
    )
    assert result.final_action == "stop_no_retry"
