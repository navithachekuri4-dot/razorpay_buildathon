from app.services import strategy


def test_expired_card_overridden_to_update_link():
    result = strategy.decide_strategy(failure_reason="expired_card", ai_action="retry_now")
    assert result.action == "send_update_card_link"
    assert result.source == "RULE_OVERRIDE"


def test_ai_recommendation_kept_when_no_strong_rule():
    result = strategy.decide_strategy(failure_reason="bank_timeout", ai_action="retry_now")
    assert result.action == "retry_now"
    assert result.source == "AI"


def test_no_override_when_ai_already_matches_rule():
    result = strategy.decide_strategy(failure_reason="expired_card", ai_action="send_update_card_link")
    assert result.action == "send_update_card_link"
    assert result.source == "AI"
