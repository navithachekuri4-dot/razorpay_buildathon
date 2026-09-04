# Panel Prep — 20 Hard Questions

Answers are grounded only in what's actually implemented, with file references so you
can go straight to the code if asked to show it.

---

## AI

**1. Why use an LLM at all here? Couldn't rules alone diagnose the failure?**
Rules alone can handle the well-understood cases (expired card → send a link), which
is why `app/services/strategy.py` hard-overrides those regardless of what the AI says.
Where an LLM adds value is combining multiple weak signals — amount, retry history,
failure text, timing — into a single judgment with a confidence score, and doing it
without hand-writing a rule for every combination. The honest caveat: with only 8
failure-reason categories in this dataset, a rules table gets you most of the way
there too. The AI's real edge would show up on messier real-world failure text that
doesn't cleanly map to 8 buckets.

**2. What does the AI actually decide, concretely?**
One thing: `recommended_action`, one of six fixed strings (`retry_now`,
`retry_after_delay`, `send_update_card_link`, `escalate`, `stop_no_retry`,
`verify_then_decide`), plus a cause string, a reasoning string, and a confidence
number. It never decides amounts, never decides whether to actually execute, never
touches the database's financial fields directly — the orchestrator does that
(`app/services/orchestrator.py`), and only after the guardrail layer approves.

**3. Why not use rules only, then — why bother with the AI/fallback split at all?**
Because the fallback rules *are* the safety net, not the primary logic — Gemini is
meant to be the primary diagnoser, and it's built to be swapped for a stronger model
without touching anything downstream, since guardrails and executor only ever see the
six-action vocabulary, not the model's reasoning.

**4. What happens if Gemini gives a bad recommendation — e.g. suggests retrying an
opted-out customer?**
Two independent nets catch it. First, `ai_diagnosis.py` validates the response shape
and vocabulary before trusting it — anything outside `settings.ALLOWED_ACTIONS`, or
missing/malformed fields, is discarded and the deterministic fallback runs instead
(tested in `test_diagnosis_rejects_out_of_vocabulary_action`). Second, even a
*valid*, on-vocabulary bad recommendation (like "retry an opted-out customer") is
caught downstream by `guardrails.py`, which checks `customer_opted_out` directly from
the transaction record — it doesn't trust or even look at what the AI said for that
check. This is tested explicitly: `test_opt_out_beats_retry_limit_and_everything_else`.

**5. How do you validate AI output?**
Structural validation, not semantic. The code checks the response is valid JSON,
`recommended_action` is a string in the fixed allowed set, `confidence` is a number
in [0,1], and `likely_cause`/`reasoning` are non-empty strings. It does not (and
can't, deterministically) validate whether the *reasoning* is good — that's exactly
why the guardrail layer exists: it doesn't need to trust the AI's reasoning, only its
final action, and even that is re-checked against hard rules.

---

## Payments

**6. How do you prevent double charging?**
Three layers: (a) the guardrail's first check is "already recovered → stop," so a
transaction that's already been marked RECOVERED is never processed again
(`test_already_recovered_blocks_double_charge`); (b) an "uncertain" deduction status
is never retried — it's forced to `verify_then_decide` first, and only marked
recovered if verification confirms capture, never by attempting a fresh charge; (c) in
production, real idempotency keys per attempt would be the actual mechanism at the
Razorpay API level — the current code documents this as a known gap for scale (see
`docs/ARCHITECTURE.md`).

**7. What if payment status is uncertain?**
It never gets retried. `guardrails.py` forces the action to `verify_then_decide`
regardless of what the AI/strategy proposed. The verifier then either confirms capture
(→ RECOVERED, no new charge attempted) or can't confirm it (→ ESCALATED to a human).
This path is tested in `test_uncertain_deduction_never_blindly_retried`.

**8. What happens after multiple retries fail?**
`MAX_RETRY_COUNT` (default 3, in `app/config.py`) is enforced in the guardrail layer,
not just as a suggestion to the AI. Once `retry_count >= MAX_RETRY_COUNT`, any
proposed retry action is overridden to `escalate` — tested in
`test_retry_limit_blocks_further_retries` and
`test_retry_limit_exceeded_escalates_instead_of_retrying`.

**9. How would this work with real payment events, not synthetic data?**
The pipeline itself doesn't change — `orchestrator.py` takes a `Transaction` row and
doesn't care whether it came from a seed script or a real webhook. What would change:
(a) transactions would be created by Razorpay webhooks (`payment.failed`) instead of
`seed_data.py`; (b) the Verifier would resolve asynchronously from a webhook
(`payment.captured`) instead of synchronously in the same request, since real capture
takes time; (c) `razorpay_service.py`'s simulated outcomes would be replaced by real
`client.payment.fetch(id)` calls against a real `payment_id`.

**10. How would you handle Razorpay webhooks?**
Not implemented in this version — flagged honestly as a limitation. The design is
compatible with it: a webhook handler would look up the `Transaction` by a Razorpay
reference (already stored as `reference_id` in execution records), update
`payment_status`/`recovery_result`, and write an `AuditLog` row the same way
`orchestrator.py` does now, just triggered by an inbound webhook instead of the batch
loop.

---

## Engineering

**11. Why this architecture — seven separate steps instead of one function?**
Because each step answers a different question and needs to be independently
testable and independently explainable: how risky is this (risk_engine), why did it
fail (ai_diagnosis), what should we do (strategy), is that safe (guardrails), do it
(executor), did it work (verifier). Splitting them means `guardrails.py` can be
tested with zero dependency on whether Gemini is even configured — which is exactly
what the test suite does.

**12. What happens if the Razorpay API is unavailable?**
`razorpay_service.py` wraps every real API call in a try/except; any exception falls
back to the same seeded simulation used when there are no credentials at all, and
`execution_mode` is set to `"simulation"` with the actual error recorded in the audit
detail message. The app never crashes or halts a batch because Razorpay is down —
tested in `test_missing_credentials_falls_back_to_simulation`.

**13. How would you scale this from SQLite?**
Swap `DATABASE_URL` to Postgres — the code has no SQLite-specific logic (SQLAlchemy
abstracts it), the only SQLite-specific line is the `StaticPool`/`check_same_thread`
handling in `database.py`, gated behind `if "sqlite" in DATABASE_URL`. Beyond the
swap: move `/recover/batch` off a single sequential loop and onto a task queue
(Celery/RQ) so workers can process transactions in parallel.

**14. How would you handle concurrency — two workers processing the same
transaction?**
Currently not handled — this is a real gap, stated in the README's limitations. The
fix is a unique constraint on something like `(transaction_id, attempt_number)` at
the database level, or a `SELECT ... FOR UPDATE` / row-level lock when a worker picks
up a transaction, so two workers can't both execute a recovery on the same row.

**15. How would you make recovery idempotent?**
Two parts: application-level (already partially done — "already recovered" is the
first guardrail check) and infrastructure-level (not done — a real idempotency key
per attempt passed to Razorpay's API, so even a duplicate request from a retried HTTP
call doesn't create two charges). The current code protects against re-processing a
transaction that's already been marked RECOVERED in the DB, but doesn't yet protect
against two concurrent in-flight requests for the same not-yet-recovered transaction.

**16. How would you secure API credentials?**
Environment variables only, never committed (`.env` is git-ignored, `.env.example`
documents the shape with empty values). `RAZORPAY_KEY_ID` is checked against the
`rzp_live_` prefix at service construction time and raises immediately if matched —
this is a hard block, not a warning, so the app physically cannot start in live mode
with a live key present.

---

## Product

**17. How does this actually recover money?**
By taking one of three genuinely different actions depending on diagnosis: retrying
the charge (for transient failures), sending a payment-method update link (for
expired/invalid cards), or verifying an ambiguous deduction before deciding. "Recover"
only ever means a verified captured payment — never an assumption.

**18. How do you measure success?**
Recovery rate (`total_recovered / total_at_risk`), but deliberately alongside
guardrail intervention count and AI acceptance rate — a system that recovers 90% of
transactions by ignoring opt-outs and retrying blindly would be a worse product, not a
better one, and this dashboard is built to make that visible rather than hide it
behind one headline number.

**19. How would a merchant actually use this?**
As a scheduled job (e.g. hourly) that pulls newly-failed payments, runs them through
`/recover/batch`, and surfaces the escalated/guardrail-blocked queue to a human
operator — the "Recovery Queue" table with filters is built with exactly that
triage workflow in mind.

**20. What would you build next?**
In priority order: (1) real Razorpay webhook integration to replace simulated
capture/verification — the single biggest gap between demo and production; (2)
idempotency keys for true concurrency safety; (3) per-merchant configurable guardrail
thresholds (still deterministic, just parameterized instead of hardcoded); (4) A/B
testing recovery strategies per failure reason to measure actual incremental lift
rather than a single fixed mapping.
