import pytest

from app.services.razorpay_service import RazorpayService


def test_live_key_is_rejected(monkeypatch):
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_live_abc123")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "secret")
    from app import config
    monkeypatch.setattr(config.settings, "RAZORPAY_KEY_ID", "rzp_live_abc123")
    monkeypatch.setattr(config.settings, "RAZORPAY_KEY_SECRET", "secret")
    with pytest.raises(RuntimeError):
        RazorpayService()


def test_missing_credentials_falls_back_to_simulation(monkeypatch):
    from app import config
    monkeypatch.setattr(config.settings, "RAZORPAY_KEY_ID", "")
    monkeypatch.setattr(config.settings, "RAZORPAY_KEY_SECRET", "")
    service = RazorpayService()
    assert service.configured is False
    outcome = service.create_recovery_order(transaction_id="TXN0001", amount=500)
    assert outcome.execution_mode == "simulation"


def test_simulated_outcome_is_deterministic_for_same_transaction():
    from app import config
    service = RazorpayService()
    a = service.create_recovery_order(transaction_id="TXN_DETERMINISM_TEST", amount=500)
    b = service.create_recovery_order(transaction_id="TXN_DETERMINISM_TEST", amount=500)
    assert a.success == b.success


def test_verification_is_always_simulated_for_synthetic_data():
    service = RazorpayService()
    outcome = service.verify_payment_status(transaction_id="TXN0002")
    assert outcome.execution_mode == "simulation"
