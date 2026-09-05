from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import Base, engine, get_db
from app.models import Transaction, AuditLog
from app.schemas import (
    TransactionOut,
    AuditTrailOut,
    RecoverResponse,
    BatchRecoverResponse,
    MetricsOut,
    SeedResponse,
    SeedBatchResponse,
)
from app.seed_data import seed_database, append_batch
from app.services.orchestrator import process_transaction
from app.services.metrics import compute_metrics

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Revenue Recovery Agent",
    description="Detects at-risk payment revenue, diagnoses failures with AI, "
                 "and executes a safety-guardrailed recovery workflow.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/seed", response_model=SeedResponse)
def seed(count: int = 120, db: Session = Depends(get_db)):
    created = seed_database(db, count=count, reset=True)
    return SeedResponse(created=created, message=f"Seeded {created} synthetic failed-payment transactions.")


@app.post("/seed/batch", response_model=SeedBatchResponse)
def seed_batch(count: int = 120, db: Session = Depends(get_db)):
    """
    Appends `count` new synthetic transactions after whatever already
    exists — never resets, never overwrites. Unlike /seed, safe to call
    repeatedly; each call continues the transaction_id sequence
    (TXN0121-0240, TXN0241-0360, ...) with a different random seed per
    batch so the new data isn't a repeat of the previous batch.
    """
    result = append_batch(db, count=count)
    return SeedBatchResponse(
        created=result["created"],
        start_id=result["start_id"],
        end_id=result["end_id"],
        message=f"Added {result['created']} new demo transactions "
                f"({result['start_id']}\u2013{result['end_id']}).",
    )


@app.get("/transactions", response_model=list[TransactionOut])
def list_transactions(
    status_filter: str | None = Query(None, alias="status"),
    failure_reason: str | None = None,
    search: str | None = None,
    limit: int = 500,
    db: Session = Depends(get_db),
):
    q = db.query(Transaction)
    if status_filter:
        q = q.filter(Transaction.recovery_result == status_filter)
    if failure_reason:
        q = q.filter(Transaction.failure_reason == failure_reason)
    if search:
        like = f"%{search}%"
        q = q.filter(
            (Transaction.transaction_id.ilike(like)) | (Transaction.customer_id.ilike(like))
        )
    return q.order_by(Transaction.created_at.desc()).limit(limit).all()


@app.get("/transactions/{transaction_id}", response_model=TransactionOut)
def get_transaction(transaction_id: str, db: Session = Depends(get_db)):
    txn = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return txn


@app.post("/recover/batch", response_model=BatchRecoverResponse)
def recover_batch(
    limit: int = 200,
    only_unprocessed: bool = True,
    db: Session = Depends(get_db),
):
    q = db.query(Transaction)
    if only_unprocessed:
        q = q.filter(Transaction.processed_at.is_(None))
    txns = q.limit(limit).all()

    recovered = escalated = stopped = failed = 0
    total_recovered_amount = 0.0

    for txn in txns:
        txn = process_transaction(db, txn)
        if txn.recovery_result == "RECOVERED":
            recovered += 1
            total_recovered_amount += txn.recovered_amount or 0
        elif txn.recovery_result == "ESCALATED":
            escalated += 1
        elif txn.recovery_result == "SKIPPED":
            stopped += 1
        elif txn.recovery_result == "FAILED":
            failed += 1

    return BatchRecoverResponse(
        processed=len(txns),
        recovered=recovered,
        escalated=escalated,
        safely_stopped=stopped,
        failed=failed,
        total_recovered_amount=round(total_recovered_amount, 2),
    )


@app.post("/recover/{transaction_id}", response_model=RecoverResponse)
def recover_one(transaction_id: str, db: Session = Depends(get_db)):
    txn = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    txn = process_transaction(db, txn)
    return RecoverResponse(
        transaction_id=txn.transaction_id,
        ai_diagnosis=txn.ai_diagnosis,
        ai_recommended_action=txn.ai_recommended_action,
        ai_source=txn.ai_source,
        recovery_action=txn.recovery_action,
        guardrail_decision=txn.guardrail_decision,
        guardrail_reason=txn.guardrail_reason,
        execution_mode=txn.execution_mode,
        recovery_result=txn.recovery_result,
        recovered_amount=txn.recovered_amount,
    )


@app.get("/audit/{transaction_id}", response_model=AuditTrailOut)
def get_audit_trail(transaction_id: str, db: Session = Depends(get_db)):
    txn = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    logs = (
        db.query(AuditLog)
        .filter(AuditLog.transaction_id == transaction_id)
        .order_by(AuditLog.timestamp.asc())
        .all()
    )
    return AuditTrailOut(transaction_id=transaction_id, steps=logs)


@app.get("/metrics", response_model=MetricsOut)
def get_metrics(db: Session = Depends(get_db)):
    return compute_metrics(db)
