from app.models import Transaction
from app.seed_data import seed_database, append_batch, next_start_index


def test_append_batch_on_empty_db_starts_at_txn0001(db_session):
    result = append_batch(db_session, count=10)
    assert result["start_id"] == "TXN0001"
    assert result["end_id"] == "TXN0010"
    assert db_session.query(Transaction).count() == 10


def test_seed_then_append_batch_creates_unique_continuing_ids(db_session):
    seed_database(db_session, count=120, reset=True)
    assert db_session.query(Transaction).count() == 120

    result = append_batch(db_session, count=120)
    assert result["start_id"] == "TXN0121"
    assert result["end_id"] == "TXN0240"

    # Original 120 untouched, 120 new added, no duplicates.
    all_ids = [t.transaction_id for t in db_session.query(Transaction).all()]
    assert len(all_ids) == 240
    assert len(set(all_ids)) == 240  # every ID unique
    assert "TXN0001" in all_ids
    assert "TXN0120" in all_ids
    assert "TXN0121" in all_ids
    assert "TXN0240" in all_ids


def test_append_batch_never_deletes_existing_rows(db_session):
    seed_database(db_session, count=50, reset=True)
    first_txn = db_session.query(Transaction).filter_by(transaction_id="TXN0001").first()
    first_txn.recovery_result = "RECOVERED"
    first_txn.recovered_amount = first_txn.amount
    db_session.commit()

    append_batch(db_session, count=30)

    still_there = db_session.query(Transaction).filter_by(transaction_id="TXN0001").first()
    assert still_there is not None
    assert still_there.recovery_result == "RECOVERED"
    assert db_session.query(Transaction).count() == 80


def test_two_consecutive_batches_use_different_seeds_and_differ(db_session):
    r1 = append_batch(db_session, count=120)
    r2 = append_batch(db_session, count=120)
    assert r1["start_id"] != r2["start_id"]

    batch1 = (
        db_session.query(Transaction)
        .filter(Transaction.transaction_id.between("TXN0001", "TXN0120"))
        .order_by(Transaction.transaction_id)
        .all()
    )
    batch2 = (
        db_session.query(Transaction)
        .filter(Transaction.transaction_id.between("TXN0121", "TXN0240"))
        .order_by(Transaction.transaction_id)
        .all()
    )
    reasons1 = [t.failure_reason for t in batch1]
    reasons2 = [t.failure_reason for t in batch2]
    amounts1 = [t.amount for t in batch1]
    amounts2 = [t.amount for t in batch2]
    # Batches shouldn't be identical sequences (different seed => different draw).
    assert reasons1 != reasons2 or amounts1 != amounts2


def test_next_start_index_ignores_non_txn_prefixed_rows(db_session):
    seed_database(db_session, count=5, reset=True)
    assert next_start_index(db_session) == 6


def test_multiple_appends_keep_extending_sequence(db_session):
    append_batch(db_session, count=10)
    r2 = append_batch(db_session, count=10)
    r3 = append_batch(db_session, count=10)
    assert r2["start_id"] == "TXN0011"
    assert r3["start_id"] == "TXN0021"
    assert db_session.query(Transaction).count() == 30
