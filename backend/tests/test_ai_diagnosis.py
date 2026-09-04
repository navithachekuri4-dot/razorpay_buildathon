from app.config import settings
from app.services import ai_diagnosis


def _txn(**overrides):
    base = dict(
        amount=999,
        failure_reason="expired_card",
        payment_status="failed",
        retry_count=0,
        previous_attempts=1,
        customer_opted_out=False,
    )
    base.update(overrides)
    return base


def test_no_gemini_key_uses_fallback():
    assert settings.GEMINI_API_KEY == ""
    result = ai_diagnosis.diagnose(_txn())
    assert result.source == "FALLBACK"
    assert result.recommended_action in settings.ALLOWED_ACTIONS


def test_opted_out_customer_always_stops():
    result = ai_diagnosis.diagnose(_txn(customer_opted_out=True))
    assert result.recommended_action == "stop_no_retry"


def test_uncertain_status_always_verifies_first():
    result = ai_diagnosis.diagnose(_txn(payment_status="uncertain", failure_reason="deducted_status_unclear"))
    assert result.recommended_action == "verify_then_decide"


def test_retry_limit_reached_escalates():
    result = ai_diagnosis.diagnose(_txn(retry_count=settings.MAX_RETRY_COUNT))
    assert result.recommended_action == "escalate"


def test_expired_card_recommends_update_link():
    result = ai_diagnosis.diagnose(_txn(failure_reason="expired_card"))
    assert result.recommended_action == "send_update_card_link"


def test_diagnosis_never_raises_on_malformed_gemini_json(monkeypatch):
    monkeypatch.setattr(ai_diagnosis, "_call_gemini", lambda prompt: {"garbage": True})
    result = ai_diagnosis.diagnose(_txn())
    assert result.source == "FALLBACK"


def test_diagnosis_rejects_out_of_vocabulary_action(monkeypatch):
    monkeypatch.setattr(
        ai_diagnosis,
        "_call_gemini",
        lambda prompt: {
            "likely_cause": "x", "recommended_action": "refund_everything",
            "reasoning": "y", "confidence": 0.9,
        },
    )
    result = ai_diagnosis.diagnose(_txn())
    assert result.source == "FALLBACK"
    assert result.recommended_action in settings.ALLOWED_ACTIONS


def test_diagnosis_accepts_valid_gemini_response(monkeypatch):
    monkeypatch.setattr(
        ai_diagnosis,
        "_call_gemini",
        lambda prompt: {
            "likely_cause": "Card expired", "recommended_action": "send_update_card_link",
            "reasoning": "Card is expired", "confidence": 0.8,
        },
    )
    result = ai_diagnosis.diagnose(_txn())
    assert result.source == "GEMINI"
    assert result.recommended_action == "send_update_card_link"
