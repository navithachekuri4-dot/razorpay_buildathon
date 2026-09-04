"""
Recovery Strategy Decision.

Takes the AI's recommended action and reconciles it against simple,
explainable business rules tied to the failure reason. The AI is good at
picking up nuance across the whole context; these rules are a sanity net
that catches the common, well-understood cases even if the AI (or its
fallback) picked something less on-the-nose.

This layer can *adjust* the action toward a better-fitting one, but it
still is not the safety layer — app/services/guardrails.py runs after this
and has the final, deterministic say over what is actually allowed to
execute.
"""
from dataclasses import dataclass

# Failure reasons with an unambiguous best-fit action. If the AI recommended
# something else for one of these, we prefer the rule — these mappings are
# well-established dunning-management practice, not guesswork.
STRONG_RULE_OVERRIDES = {
    "expired_card": "send_update_card_link",
    "payment_method_invalid": "send_update_card_link",
}


@dataclass
class StrategyDecision:
    action: str
    source: str  # "AI" | "RULE_OVERRIDE"
    note: str


def decide_strategy(*, failure_reason: str, ai_action: str) -> StrategyDecision:
    override = STRONG_RULE_OVERRIDES.get(failure_reason)
    if override and override != ai_action:
        return StrategyDecision(
            action=override,
            source="RULE_OVERRIDE",
            note=(
                f"Business rule for failure_reason='{failure_reason}' prefers "
                f"'{override}' over the AI's '{ai_action}'."
            ),
        )
    return StrategyDecision(
        action=ai_action,
        source="AI",
        note="AI recommendation accepted as the working strategy.",
    )
