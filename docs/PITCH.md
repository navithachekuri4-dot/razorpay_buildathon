# Pitch Structures

## A. 30-second explanation

"Failed payments aren't just failed transactions — they're recoverable revenue, if
something diagnoses why they failed and acts on it fast and safely. This agent does
that: an AI diagnoses the failure and recommends a fix, but a completely separate,
deterministic safety layer decides what's actually allowed to run — so it never
retries an opted-out customer, never double-charges an ambiguous deduction, and never
retries past a limit. In this demo, ₹1,62,980 was at risk and ₹51,266 came back,
verified, not assumed."

## B. 2-minute technical explanation

"The core idea is a seven-step pipeline: detect, diagnose, decide, safety-check, act,
verify, recover. Every failed transaction goes through all seven, and every step
writes to an audit log, so any transaction's full reasoning history can be
reconstructed.

The architectural principle underneath all of it is: AI recommends, deterministic
code controls money. A risk engine scores each transaction 0-100 using a plain
weighted formula — amount, failure reason, retry history, opt-out status. Gemini (or
a rule-based fallback if it's unavailable) takes that context and recommends one of
six actions with a confidence score. That recommendation then hits a guardrail layer
that has zero dependency on the AI being right — it independently checks opt-out
status, retry limits, payment status, and idempotency, and it can override the AI's
recommendation outright. Only what survives that layer gets executed, through
Razorpay Test Mode where that's meaningful — real Order and Payment Link creation —
and simulation where synthetic data makes a real API call meaningless, always labeled
honestly via an `execution_mode` field.

Everything is tested: 40 tests cover the risk formula, every guardrail rule in
isolation and combined, the AI fallback path including malformed model output, and
the full pipeline end to end. Nothing on the dashboard is hardcoded — metrics are
computed live from the database on every request."

## C. 5-minute pitch structure

Use `docs/DEMO_SCRIPT.md` for the full walkthrough. Structure:

1. **Open with the problem** (not the tech): failed payments are recoverable revenue,
   automating recovery safely is the hard part. (30s)
2. **Show revenue at risk** before running anything. (30s)
3. **Run the batch live**, narrate the seven steps while it runs. (30s)
4. **Three contrasting transactions**, each showing WHY → AI DIAGNOSIS → SAFETY →
   ACT → VERIFY → RESULT:
   - A recovered payment (expired card → update link → captured).
   - An escalated payment (uncertain deduction → verified, unresolved → human).
   - A guardrail-blocked payment (opted-out customer → protected, not contacted).
   (3 min total, ~60s each)
5. **Return to the numbers**: recovery rate, guardrail intervention count, AI
   acceptance rate — success measured as "recovered safely," not just "recovered."
   (30s)
6. **Close**: restate the number that was at risk, the number that came back
   verified, and that the rest wasn't ignored — it was escalated or explicitly
   protected. (20s)
