"""
Revenue Risk Engine.

Fully deterministic and explainable on purpose: this is a scoring formula,
not a model, so its output can be justified line by line in a panel
interview. It answers one question: "how much attention/urgency does this
piece of at-risk revenue deserve?"

Score is 0-100, built from four independently-capped components so no
single factor can dominate the score unfairly.
"""
from dataclasses import dataclass

# Points (0-25) per failure reason, reflecting how "recoverable" or urgent
# that failure category typically is.
FAILURE_REASON_POINTS = {
    "deducted_status_unclear": 25,   # highest: money may already be gone/stuck
    "insufficient_funds": 20,
    "authentication_failure": 18,
    "expired_card": 15,
    "payment_method_invalid": 15,
    "bank_timeout": 10,
    "gateway_error": 10,
    "network_error": 8,
}
DEFAULT_FAILURE_POINTS = 10

MAX_AMOUNT_POINTS = 30
AMOUNT_NORMALIZER = 3000.0  # amount at/above this contributes the full 30 pts

MAX_RETRY_POINTS = 21
RETRY_POINTS_PER_ATTEMPT = 7

OPT_OUT_POINTS = 15
UNCERTAIN_STATUS_POINTS = 9


@dataclass
class RiskAssessment:
    risk_score: float
    risk_level: str
    breakdown: dict


def _risk_level(score: float) -> str:
    if score >= 80:
        return "CRITICAL"
    if score >= 55:
        return "HIGH"
    if score >= 30:
        return "MEDIUM"
    return "LOW"


def assess_risk(
    *,
    amount: float,
    failure_reason: str,
    retry_count: int,
    payment_status: str,
    customer_opted_out: bool,
) -> RiskAssessment:
    amount_points = min(MAX_AMOUNT_POINTS, round((amount / AMOUNT_NORMALIZER) * MAX_AMOUNT_POINTS, 1))
    failure_points = FAILURE_REASON_POINTS.get(failure_reason, DEFAULT_FAILURE_POINTS)
    retry_points = min(MAX_RETRY_POINTS, retry_count * RETRY_POINTS_PER_ATTEMPT)
    opt_out_points = OPT_OUT_POINTS if customer_opted_out else 0
    uncertain_points = UNCERTAIN_STATUS_POINTS if payment_status == "uncertain" else 0

    raw_score = amount_points + failure_points + retry_points + opt_out_points + uncertain_points
    score = round(min(100.0, raw_score), 1)

    breakdown = {
        "amount_points": amount_points,
        "failure_reason_points": failure_points,
        "retry_points": retry_points,
        "opt_out_points": opt_out_points,
        "uncertain_status_points": uncertain_points,
        "total": score,
    }

    return RiskAssessment(risk_score=score, risk_level=_risk_level(score), breakdown=breakdown)
