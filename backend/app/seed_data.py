"""
Generates a realistic, reproducible synthetic dataset of failed payments.

This is NOT real customer data and NOT real money. Every field is invented
by a seeded random generator so that (a) the demo is reproducible run to
run, and (b) the mix of outcomes is realistic: not every failure is
recoverable, some customers have opted out, some transactions have an
unclear deduction status, and some have already hit the retry limit.
"""
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import Transaction

SEED = 42

FAILURE_REASONS = [
    "expired_card",
    "insufficient_funds",
    "bank_timeout",
    "gateway_error",
    "authentication_failure",
    "payment_method_invalid",
    "network_error",
    "deducted_status_unclear",
]

# Realistic-ish relative frequency of each failure reason in a subscription
# / e-commerce payment base.
FAILURE_WEIGHTS = [18, 20, 12, 12, 10, 10, 10, 8]

CUSTOMER_FIRST = [
    "Aarav", "Vivaan", "Aditi", "Diya", "Kabir", "Meera", "Rohan", "Ananya",
    "Ishaan", "Priya", "Arjun", "Neha", "Kunal", "Sanya", "Dev", "Riya",
    "Karan", "Pooja", "Nikhil", "Tanvi",
]
CUSTOMER_LAST = [
    "Sharma", "Verma", "Reddy", "Nair", "Iyer", "Gupta", "Khan", "Bose",
    "Menon", "Rao", "Chatterjee", "Joshi", "Kapoor", "Pillai", "Das",
]

# Plausible subscription price points (INR) for a mid-market SaaS / D2C
# subscription business.
AMOUNT_BUCKETS = [199, 299, 399, 499, 599, 799, 999, 1499, 1999, 2499, 4999]


def _make_customer(rng: random.Random, idx: int) -> tuple[str, str]:
    name = f"{rng.choice(CUSTOMER_FIRST)} {rng.choice(CUSTOMER_LAST)}"
    return f"CUST{idx:04d}", name


def generate_transactions(count: int = 120) -> list[dict]:
    rng = random.Random(SEED)
    now = datetime.now(timezone.utc)
    rows = []

    for i in range(1, count + 1):
        txn_id = f"TXN{i:04d}"
        customer_id, _name = _make_customer(rng, rng.randint(1, count))
        has_subscription = rng.random() < 0.7
        subscription_id = f"SUB{rng.randint(1, count // 2):04d}" if has_subscription else None

        amount = float(rng.choice(AMOUNT_BUCKETS))
        failure_reason = rng.choices(FAILURE_REASONS, weights=FAILURE_WEIGHTS, k=1)[0]

        # Retry history: most transactions have been attempted a few times
        # already by the merchant's normal (pre-agent) dunning flow.
        previous_attempts = rng.choices([0, 1, 2, 3], weights=[35, 30, 20, 15], k=1)[0]
        retry_count = min(previous_attempts, rng.choice([0, 1, 2, 3, 3, 4]))
        # A handful of transactions have already exceeded the retry limit
        # before the agent ever looks at them, so the demo can show the
        # "guardrail blocks a retry" case honestly.
        if rng.random() < 0.12:
            retry_count = rng.choice([3, 4, 5])

        # Opt-outs: customers who explicitly asked not to be re-charged.
        customer_opted_out = rng.random() < 0.10

        # Payment status: usually "failed" cleanly, but some are genuinely
        # ambiguous (bank says failed, ledger suggests otherwise).
        if failure_reason == "deducted_status_unclear":
            payment_status = "uncertain"
        else:
            payment_status = rng.choices(
                ["failed", "uncertain"], weights=[92, 8], k=1
            )[0]

        days_ago = rng.randint(0, 21)
        created_at = now - timedelta(days=days_ago, hours=rng.randint(0, 23))

        rows.append(
            {
                "transaction_id": txn_id,
                "customer_id": customer_id,
                "subscription_id": subscription_id,
                "amount": amount,
                "currency": "INR",
                "failure_reason": failure_reason,
                "payment_status": payment_status,
                "customer_opted_out": customer_opted_out,
                "retry_count": retry_count,
                "previous_attempts": previous_attempts,
                "created_at": created_at,
            }
        )

    return rows


def seed_database(db: Session, count: int = 120, reset: bool = True) -> int:
    if reset:
        db.query(Transaction).delete()
        db.commit()

    rows = generate_transactions(count)
    objects = [Transaction(**row) for row in rows]
    db.bulk_save_objects(objects)
    db.commit()
    return len(objects)
