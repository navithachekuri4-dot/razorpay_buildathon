from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Transaction(Base):
    """
    A single failed/at-risk payment. This is the unit the agent reasons
    about end to end: detect -> diagnose -> decide -> safety -> act ->
    verify -> recover.
    """

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, unique=True, index=True, nullable=False)
    customer_id = Column(String, nullable=False)
    subscription_id = Column(String, nullable=True)

    amount = Column(Float, nullable=False)
    currency = Column(String, default="INR")

    failure_reason = Column(String, nullable=False)
    payment_status = Column(String, default="failed")  # failed | uncertain | captured
    customer_opted_out = Column(Boolean, default=False)

    retry_count = Column(Integer, default=0)
    previous_attempts = Column(Integer, default=0)

    created_at = Column(DateTime, default=utcnow)

    # --- Risk assessment (Revenue Risk Engine output) ---
    risk_score = Column(Float, nullable=True)
    risk_level = Column(String, nullable=True)  # LOW | MEDIUM | HIGH | CRITICAL

    # --- AI diagnosis output ---
    ai_diagnosis = Column(Text, nullable=True)
    ai_recommended_action = Column(String, nullable=True)
    ai_confidence = Column(Float, nullable=True)
    ai_source = Column(String, nullable=True)  # GEMINI | FALLBACK

    # --- Strategy + safety output ---
    recovery_action = Column(String, nullable=True)  # final action after guardrails
    guardrail_decision = Column(String, nullable=True)  # ALLOWED | BLOCKED
    guardrail_reason = Column(Text, nullable=True)

    # --- Execution + verification output ---
    execution_mode = Column(String, nullable=True)  # razorpay_test | simulation
    recovery_result = Column(String, nullable=True)  # RECOVERED|FAILED|ESCALATED|SKIPPED
    recovered_amount = Column(Float, nullable=True)

    processed_at = Column(DateTime, nullable=True)

    audit_logs = relationship(
        "AuditLog", back_populates="transaction", cascade="all, delete-orphan"
    )


class AuditLog(Base):
    """
    One row per pipeline step per transaction. This is what lets us answer,
    for any transaction: what did the agent do, why, what safety checks
    ran, and what happened afterward.
    """

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(
        String, ForeignKey("transactions.transaction_id"), index=True, nullable=False
    )
    step = Column(String, nullable=False)
    # DETECT | RISK_ASSESSMENT | AI_DIAGNOSIS | STRATEGY | SAFETY_CHECK |
    # EXECUTION | VERIFICATION
    status = Column(String, nullable=False)  # e.g. OK | BLOCKED | ERROR
    message = Column(Text, nullable=False)
    execution_mode = Column(String, nullable=True)
    timestamp = Column(DateTime, default=utcnow)

    transaction = relationship("Transaction", back_populates="audit_logs")
