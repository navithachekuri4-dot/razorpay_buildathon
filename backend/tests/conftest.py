import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ.setdefault("GEMINI_API_KEY", "")
os.environ.setdefault("RAZORPAY_KEY_ID", "")
os.environ.setdefault("RAZORPAY_KEY_SECRET", "")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Transaction


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def make_txn(**overrides) -> Transaction:
    defaults = dict(
        transaction_id="TXN_TEST_0001",
        customer_id="CUST0001",
        subscription_id="SUB0001",
        amount=999.0,
        currency="INR",
        failure_reason="bank_timeout",
        payment_status="failed",
        customer_opted_out=False,
        retry_count=0,
        previous_attempts=0,
    )
    defaults.update(overrides)
    return Transaction(**defaults)
