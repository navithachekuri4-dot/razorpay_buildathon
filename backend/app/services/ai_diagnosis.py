"""
AI Diagnosis.

This is the ONLY component allowed to call an LLM. It produces a
*recommendation* — never an executed action. Everything downstream
(app/services/guardrails.py) is free to override it, and frequently does.

Contract this module guarantees to the rest of the pipeline, no matter
what happens with Gemini:
  - Always returns a Diagnosis object.
  - `action` is always one of settings.ALLOWED_ACTIONS.
  - `source` is either "GEMINI" or "FALLBACK", so the UI/audit trail can
    always say honestly where a recommendation came from.
  - Never raises: network errors, timeouts, malformed JSON, missing API
    key, or an out-of-vocabulary action from the model are all caught and
    routed to the deterministic fallback below.
"""
import json
from dataclasses import dataclass
from typing import Optional

import httpx

from app.config import settings

GEMINI_URL_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)


@dataclass
class Diagnosis:
    likely_cause: str
    recommended_action: str
    reasoning: str
    confidence: float  # 0.0 - 1.0
    source: str  # "GEMINI" | "FALLBACK"


def _fallback_diagnosis(
    *, failure_reason: str, retry_count: int, payment_status: str, customer_opted_out: bool
) -> Diagnosis:
    """
    Deterministic rule-based diagnosis used whenever Gemini is unavailable,
    unconfigured, or returns something we can't trust. This is what keeps
    the product working with zero AI credentials, and it is judged by the
    exact same downstream guardrails as a Gemini recommendation.
    """
    if customer_opted_out:
        return Diagnosis(
            likely_cause="Customer has opted out of recovery contact.",
            recommended_action="stop_no_retry",
            reasoning="Rule: opted-out customers are never contacted, regardless of amount.",
            confidence=1.0,
            source="FALLBACK",
        )

    if payment_status == "uncertain":
        return Diagnosis(
            likely_cause="Payment status is ambiguous; funds may already be deducted.",
            recommended_action="verify_then_decide",
            reasoning="Rule: an unclear deduction must be verified before any retry to avoid a double charge.",
            confidence=0.9,
            source="FALLBACK",
        )

    if retry_count >= settings.MAX_RETRY_COUNT:
        return Diagnosis(
            likely_cause="Prior automated retries have already been exhausted.",
            recommended_action="escalate",
            reasoning=f"Rule: retry_count >= {settings.MAX_RETRY_COUNT} is handled by a human, not another retry.",
            confidence=0.85,
            source="FALLBACK",
        )

    reason_map = {
        "expired_card": ("The saved card has expired.", "send_update_card_link", 0.85),
        "payment_method_invalid": ("The saved payment method is invalid.", "send_update_card_link", 0.8),
        "insufficient_funds": ("The account likely had insufficient funds at charge time.", "retry_after_delay", 0.7),
        "bank_timeout": ("A transient timeout on the bank/issuer side.", "retry_now", 0.75),
        "gateway_error": ("A transient error at the payment gateway.", "retry_now", 0.7),
        "network_error": ("A transient network failure during the charge.", "retry_now", 0.7),
        "authentication_failure": ("3-D Secure / OTP authentication was not completed.", "send_update_card_link", 0.65),
    }
    cause, action, confidence = reason_map.get(
        failure_reason,
        ("Cause not confidently classified from the failure reason.", "escalate", 0.4),
    )
    return Diagnosis(
        likely_cause=cause,
        recommended_action=action,
        reasoning=f"Rule-based mapping for failure_reason='{failure_reason}'.",
        confidence=confidence,
        source="FALLBACK",
    )


def _build_prompt(txn: dict) -> str:
    return f"""You are a payment-recovery diagnosis assistant for an Indian fintech.
You NEVER execute anything — you only recommend. A separate deterministic
safety system decides what is actually allowed to run.

Analyze this failed payment and respond with ONLY a JSON object, no prose,
no markdown fences, matching exactly this shape:
{{
  "likely_cause": "<one sentence, plain language>",
  "recommended_action": "<one of: retry_now, retry_after_delay, send_update_card_link, escalate, stop_no_retry, verify_then_decide>",
  "reasoning": "<one or two sentences explaining the recommendation>",
  "confidence": <number between 0 and 1>
}}

Transaction:
- amount_inr: {txn['amount']}
- failure_reason: {txn['failure_reason']}
- payment_status: {txn['payment_status']}
- retry_count: {txn['retry_count']}
- previous_attempts: {txn['previous_attempts']}
- customer_opted_out: {txn['customer_opted_out']}
"""


def _call_gemini(prompt: str) -> Optional[dict]:
    if not settings.GEMINI_API_KEY:
        return None

    url = GEMINI_URL_TEMPLATE.format(model=settings.GEMINI_MODEL)
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "response_mime_type": "application/json",
        },
    }
    try:
        response = httpx.post(
        url,
        headers={"x-goog-api-key": settings.GEMINI_API_KEY},
        json=payload,
        timeout=settings.GEMINI_TIMEOUT_SECONDS,
)

        response.raise_for_status()
        data = response.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)

    except (httpx.HTTPError, KeyError, IndexError, json.JSONDecodeError, ValueError, TypeError) as exc:
        print(f"Gemini API error: {type(exc).__name__}: {exc}")
        return None
    except Exception:
        # Defense in depth: no matter what goes wrong talking to an external
        # API, diagnosis must never crash the recovery pipeline. Anything
        # not anticipated above still routes to the deterministic fallback.
        return None


def _validate_gemini_response(raw: dict) -> bool:
    """
    Structural + vocabulary validation only — this function does not (and
    cannot) judge whether the AI's reasoning is good. That's exactly why
    guardrails.py exists downstream and re-checks the final action on its
    own terms regardless of what passes here.
    """
    if not isinstance(raw, dict):
        return False

    action = raw.get("recommended_action")
    confidence = raw.get("confidence")
    likely_cause = raw.get("likely_cause")
    reasoning = raw.get("reasoning")

    if not (isinstance(action, str) and action in settings.ALLOWED_ACTIONS):
        return False
    if not (isinstance(likely_cause, str) and likely_cause.strip()):
        return False
    if not (isinstance(reasoning, str) and reasoning.strip()):
        return False
    # bool is a subclass of int in Python — exclude it explicitly so
    # confidence=true isn't silently accepted as confidence=1.0.
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        return False
    if not (0 <= confidence <= 1):
        return False
    return True


def diagnose(txn: dict) -> Diagnosis:
    """
    txn: dict with keys amount, failure_reason, payment_status, retry_count,
    previous_attempts, customer_opted_out.

    Contract (unconditional, regardless of Gemini's availability or output):
      - GEMINI_API_KEY configured + Gemini reachable + response passes
        validation -> source="GEMINI".
      - GEMINI_API_KEY missing, Gemini unreachable/errored/timed out, or its
        response fails validation (bad JSON, out-of-vocabulary action,
        missing/malformed fields) -> source="FALLBACK", same deterministic
        rules either way.
      - This function never raises.
    """
    raw = _call_gemini(_build_prompt(txn))

    if raw is not None and _validate_gemini_response(raw):
        return Diagnosis(
            likely_cause=raw["likely_cause"],
            recommended_action=raw["recommended_action"],
            reasoning=raw["reasoning"],
            confidence=float(raw["confidence"]),
            source="GEMINI",
        )
    # Either Gemini was never called (no key / call failed), or it responded
    # but didn't match our contract. We do not trust a non-conforming
    # response — fall through to the deterministic path either way.

    return _fallback_diagnosis(
        failure_reason=txn["failure_reason"],
        retry_count=txn["retry_count"],
        payment_status=txn["payment_status"],
        customer_opted_out=txn["customer_opted_out"],
    )
