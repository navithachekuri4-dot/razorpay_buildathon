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


def _generate_rows(rng: random.Random, start_index: int, count: int) -> list[dict]:
    """
    Shared row generator. `start_index` is the transaction number the first
    row in this batch should get (TXN{start_index:04d}), so a second/third/
    Nth batch can be appended after existing data without ever reusing a
    transaction_id. The customer/subscription ID pool grows with
    `start_index + count` too, so later batches draw from a wider pool
    rather than only ever recreating the first batch's customers — some
    overlap with earlier batches is still expected and realistic (the same
    customer failing more than once over time), just not the *only* thing
    that can happen.
    """
    now = datetime.now(timezone.utc)
    customer_pool_size = max(1, start_index + count - 1)
    subscription_pool_size = max(1, customer_pool_size // 2)
    rows = []

    for offset in range(count):
        i = start_index + offset
        txn_id = f"TXN{i:04d}"
        customer_id, _name = _make_customer(rng, rng.randint(1, customer_pool_size))
        has_subscription = rng.random() < 0.7
        subscription_id = f"SUB{rng.randint(1, subscription_pool_size):04d}" if has_subscription else None

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


def generate_transactions(count: int = 120) -> list[dict]:
    """
    The original, fully deterministic dataset used by POST /seed (full
    reset). Fixed SEED, always starts at TXN0001 — unchanged behavior.
    """
    rng = random.Random(SEED)
    return _generate_rows(rng, start_index=1, count=count)


def seed_database(db: Session, count: int = 120, reset: bool = True) -> int:
    """POST /seed — unchanged: wipes the table (when reset=True) and
    creates the original deterministic dataset starting at TXN0001."""
    if reset:
        db.query(Transaction).delete()
        db.commit()

    rows = generate_transactions(count)
    objects = [Transaction(**row) for row in rows]
    db.bulk_save_objects(objects)
    db.commit()
    return len(objects)


def next_start_index(db: Session) -> int:
    """
    The transaction number the next appended batch should start at:
    one past the highest existing TXN#### in the table, or 1 if the table
    is empty. Reading this from the DB (rather than tracking a counter in
    memory) means it's correct even after a server restart.
    """
    existing_ids = [row[0] for row in db.query(Transaction.transaction_id).all()]
    max_n = 0
    for tid in existing_ids:
        if tid.startswith("TXN"):
            try:
                max_n = max(max_n, int(tid[3:]))
            except ValueError:
                continue
    return max_n + 1


def append_batch(db: Session, count: int = 120) -> dict:
    """
    POST /seed/batch — ADDS `count` new transactions after whatever already
    exists. Never deletes, never overwrites, never reused a transaction_id
    (enforced both by next_start_index() and, as a hard backstop, by the
    unique constraint on Transaction.transaction_id at the DB level — a
    bug here would raise an IntegrityError rather than silently collide).

    Each call uses a different random seed (the batch's own start_index),
    so batch 2 (starting at TXN0121) is guaranteed to differ from batch 1
    (TXN0001-0120) while still being reproducible if you needed to inspect
    "batch starting at TXN0121" again.
    """
    start_index = next_start_index(db)
    rng = random.Random(start_index)
    rows = _generate_rows(rng, start_index=start_index, count=count)
    objects = [Transaction(**row) for row in rows]
    db.bulk_save_objects(objects)
    db.commit()

    return {
        "created": len(objects),
        "start_id": f"TXN{start_index:04d}",
        "end_id": f"TXN{start_index + count - 1:04d}",
    }
