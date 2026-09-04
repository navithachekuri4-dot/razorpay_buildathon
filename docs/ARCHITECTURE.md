# Architecture

## The 30-60 second version

"Failed payments go through seven steps. A deterministic risk engine scores how
urgent each one is. An AI model — Gemini, with a rule-based fallback when it's
unavailable — diagnoses why the payment failed and recommends an action. That
recommendation then passes through a **separate, deterministic safety layer** that
has the actual authority to decide what runs: it enforces opt-outs, retry limits,
double-charge protection, and forces verification before ever retrying an ambiguous
deduction. Only after that layer approves does an executor act — through Razorpay
Test Mode where that's meaningful, simulated where it isn't, always labeled honestly.
Every step is logged to an audit trail, and every metric on the dashboard is computed
live from that trail, not hardcoded."

## Why each technology choice

**Why FastAPI?** Type-checked request/response models via Pydantic, automatic Swagger
docs, and async-ready if this needed to scale later — without adding framework
overhead for what is fundamentally a handful of REST endpoints.

**Why SQLite?** The whole point of the demo is to show reasoning and safety behavior on
~120 transactions, not to prove database scalability. SQLite needs zero setup, which
matters for a judge who wants to clone and run this in five minutes. `DATABASE_URL` is
the only thing that would change to point at Postgres in production.

**Why Gemini?** Chosen as the diagnosis model because it supports structured JSON
output cheaply and quickly, which is what a *recommendation* step needs — not
creativity, just a fast, structured judgment call with a confidence score.

**Why synthetic data?** No real customer or payment data should ever sit in a
buildathon repo. Synthetic data, seeded deterministically, gives a reproducible demo
without that risk — and lets us deliberately include the hard cases (opt-outs, retry
exhaustion, ambiguous deductions) that a purely organic sample might not surface
consistently.

**Why Razorpay Test Mode specifically where it's used, and not everywhere?** Real
Razorpay API calls happen where they represent a genuine artifact — a real test-mode
Order for a retry, a real test-mode Payment Link for a card update. They don't happen
for the "did this synthetic transaction actually get captured" question, because no
real card is behind it — faking that as a live API round-trip would be integration
for appearance's sake, not substance. The honest answer — "this part is simulated,
here's why, here's what changes in production" — is worth more in a technical panel
than a hidden fake call.

**Why a separate deterministic guardrail layer instead of asking the AI to "be
careful"?** Because instructing a model to be careful is not a control — it's a
suggestion with no floor. A financial safety property (never double-charge, always
respect opt-out, never exceed a retry limit) needs to be true 100% of the time, which
only a rule that runs outside the model can guarantee. This is also why the guardrail
module has zero dependencies on `ai_diagnosis.py` — it takes plain transaction fields
as input, not the AI's output, so it can be reasoned about (and tested) completely
independently of whether the AI is even working.

**Why an Executor *and* a Verifier as separate steps, instead of one "do it" step?**
Because "I attempted an action" and "the action actually resulted in recovered money"
are different claims, and conflating them is exactly how systems end up over-claiming
revenue recovered. The Verifier is the only place `recovery_result` and
`recovered_amount` get set, and `recovered_amount` is always read from the
transaction's own `amount` field — never computed or estimated.

**Why an audit log per step instead of just a final status?** Because "the agent
recovered ₹999" is not an explainable answer on its own. The audit trail lets you
answer, for any transaction: what did the agent think was wrong, what did it want to
do, what did the safety layer allow or block and why, what actually got executed, and
how was the result verified. That's the difference between a black box and something
you can defend line by line in an interview.

## Scaling and concurrency (asked, not built)

The current design processes transactions one at a time inside a single request
(`/recover/batch` loops sequentially). For real merchant volume this would move to:

- A queue (e.g. Celery/RQ over Redis) so batches process in parallel across workers.
- Postgres instead of SQLite, with a unique constraint on `(transaction_id,
  attempt_number)` to make the executor idempotent under retries or concurrent
  workers picking up the same row.
- Real Razorpay webhooks (`payment.captured`, `payment.failed`) feeding the Verifier
  asynchronously, instead of the Verifier resolving synchronously in the same request
  as the Executor — because in production, "did the retry succeed" is not known the
  instant you fire it.
