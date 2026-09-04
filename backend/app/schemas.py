from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    transaction_id: str
    customer_id: str
    subscription_id: Optional[str]
    amount: float
    currency: str
    failure_reason: str
    payment_status: str
    customer_opted_out: bool
    retry_count: int
    previous_attempts: int
    created_at: datetime

    risk_score: Optional[float]
    risk_level: Optional[str]

    ai_diagnosis: Optional[str]
    ai_recommended_action: Optional[str]
    ai_confidence: Optional[float]
    ai_source: Optional[str]

    recovery_action: Optional[str]
    guardrail_decision: Optional[str]
    guardrail_reason: Optional[str]

    execution_mode: Optional[str]
    recovery_result: Optional[str]
    recovered_amount: Optional[float]

    processed_at: Optional[datetime]


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    step: str
    status: str
    message: str
    execution_mode: Optional[str]
    timestamp: datetime


class AuditTrailOut(BaseModel):
    transaction_id: str
    steps: List[AuditLogOut]


class RecoverResponse(BaseModel):
    transaction_id: str
    ai_diagnosis: Optional[str]
    ai_recommended_action: Optional[str]
    ai_source: Optional[str]
    recovery_action: Optional[str]
    guardrail_decision: Optional[str]
    guardrail_reason: Optional[str]
    execution_mode: Optional[str]
    recovery_result: Optional[str]
    recovered_amount: Optional[float]


class BatchRecoverResponse(BaseModel):
    processed: int
    recovered: int
    escalated: int
    safely_stopped: int
    failed: int
    total_recovered_amount: float


class MetricsOut(BaseModel):
    total_transactions: int
    total_at_risk: float
    total_recovered: float
    recovery_rate: float
    processed_count: int
    unprocessed_count: int
    recovered_count: int
    failed_count: int
    escalated_count: int
    safely_stopped_count: int
    guardrail_intervention_count: int
    ai_recommendation_acceptance_rate: float
    recovery_by_failure_reason: dict
    recovery_by_strategy: dict
    amount_recovered_by_strategy: dict
    average_recovered_amount: float


class SeedResponse(BaseModel):
    created: int
    message: str
