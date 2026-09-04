from app.services import risk_engine


def test_low_risk_small_amount_transient_reason():
    r = risk_engine.assess_risk(
        amount=199,
        failure_reason="network_error",
        retry_count=0,
        payment_status="failed",
        customer_opted_out=False,
    )
    assert r.risk_level == "LOW"
    assert 0 <= r.risk_score <= 100


def test_uncertain_deduction_pushes_risk_up():
    base = risk_engine.assess_risk(
        amount=999, failure_reason="gateway_error", retry_count=0,
        payment_status="failed", customer_opted_out=False,
    )
    uncertain = risk_engine.assess_risk(
        amount=999, failure_reason="gateway_error", retry_count=0,
        payment_status="uncertain", customer_opted_out=False,
    )
    assert uncertain.risk_score > base.risk_score


def test_opt_out_increases_score():
    base = risk_engine.assess_risk(
        amount=999, failure_reason="expired_card", retry_count=0,
        payment_status="failed", customer_opted_out=False,
    )
    opted_out = risk_engine.assess_risk(
        amount=999, failure_reason="expired_card", retry_count=0,
        payment_status="failed", customer_opted_out=True,
    )
    assert opted_out.risk_score > base.risk_score


def test_score_never_exceeds_100():
    r = risk_engine.assess_risk(
        amount=999999, failure_reason="deducted_status_unclear", retry_count=10,
        payment_status="uncertain", customer_opted_out=True,
    )
    assert r.risk_score <= 100
    assert r.risk_level == "CRITICAL"


def test_high_amount_increases_risk_score():
    small = risk_engine.assess_risk(
        amount=199, failure_reason="bank_timeout", retry_count=0,
        payment_status="failed", customer_opted_out=False,
    )
    large = risk_engine.assess_risk(
        amount=4999, failure_reason="bank_timeout", retry_count=0,
        payment_status="failed", customer_opted_out=False,
    )
    assert large.risk_score > small.risk_score
