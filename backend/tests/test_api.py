"""
API tests share the single in-memory DATABASE_URL set up in conftest.py
(sqlite:///:memory: with StaticPool, so all connections see the same DB).
Every test that depends on a specific transaction count calls /seed
first, which deletes existing rows before inserting new ones — so tests
stay independent even though they share a database.
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_seed_and_list_transactions():
    resp = client.post("/seed", params={"count": 30})
    assert resp.status_code == 200
    assert resp.json()["created"] == 30

    resp = client.get("/transactions")
    assert resp.status_code == 200
    assert len(resp.json()) == 30


def test_get_single_transaction_not_found():
    resp = client.get("/transactions/DOES_NOT_EXIST")
    assert resp.status_code == 404


def test_recover_single_transaction():
    client.post("/seed", params={"count": 10})
    txns = client.get("/transactions").json()
    txn_id = txns[0]["transaction_id"]

    resp = client.post(f"/recover/{txn_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["recovery_result"] in ("RECOVERED", "FAILED", "ESCALATED", "SKIPPED")

    audit = client.get(f"/audit/{txn_id}")
    assert audit.status_code == 200
    assert len(audit.json()["steps"]) == 7


def test_batch_recovery_and_metrics():
    client.post("/seed", params={"count": 40})
    batch = client.post("/recover/batch", params={"limit": 40})
    assert batch.status_code == 200
    body = batch.json()
    assert body["processed"] == 40
    assert body["recovered"] + body["escalated"] + body["safely_stopped"] + body["failed"] == 40

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    m = metrics.json()
    assert m["total_transactions"] == 40
    assert m["processed_count"] == 40
    assert m["total_recovered"] >= 0


def test_recover_transaction_not_found():
    resp = client.post("/recover/DOES_NOT_EXIST")
    assert resp.status_code == 404


def test_search_and_filter_transactions():
    client.post("/seed", params={"count": 20})
    all_txns = client.get("/transactions").json()
    sample_id = all_txns[0]["transaction_id"]

    resp = client.get("/transactions", params={"search": sample_id})
    assert resp.status_code == 200
    assert any(t["transaction_id"] == sample_id for t in resp.json())

    resp = client.get("/transactions", params={"failure_reason": "expired_card"})
    assert resp.status_code == 200
    assert all(t["failure_reason"] == "expired_card" for t in resp.json())
