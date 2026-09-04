# Demo Script (5 minutes)

Every transaction ID and number below is a real output from running `POST /seed?count=120`
followed by `POST /recover/batch` against this codebase (seed = 42) — not invented for
the script. Your own run will match exactly, since the dataset and simulation are
seeded deterministically.

## 0. Open (30 sec) — don't start with the tech

> "Every failed payment is not just a failed transaction — it's potentially lost
> revenue. Most of it is recoverable, if something diagnoses why it failed and takes
> the right next action fast. But automating that safely is the hard part: retry
> blindly and you risk double-charging someone, or you retry a customer who told you
> to stop. This agent does both — recovers what it safely can, and proves it left the
> rest alone for a good reason."

## 1. Revenue at risk (30 sec)

Open the Command Center. Point at the hero metrics before running anything:

- **Revenue at risk**: ₹1,62,980 across 120 transactions.
- Explain: "This is every payment that failed — before the agent has done anything."

## 2. Run the recovery batch (30 sec)

Click **"Run recovery batch."** While it runs: "Each transaction is going through
seven steps — detect, assess risk, get an AI diagnosis, decide a strategy, pass a
safety check, execute, and verify. Nothing here is randomly clicked — it's the same
pipeline for all 120."

Result: **34 recovered · 19 escalated · 7 safely stopped · 60 failed · ₹51,266
recovered · 31.46% recovery rate.**

## 3. Case 1 — a payment that gets recovered (60 sec)

Open **TXN0006** (Inspect).

- **What happened:** ₹499 payment failed with `expired_card`.
- **AI diagnosis:** the deterministic fallback (or Gemini, if configured) diagnosed
  "the saved card has expired" and recommended `send_update_card_link`.
- **Safety check:** ALLOWED — no guardrail applies here (not opted out, not
  already captured, within retry limits).
- **Execution:** a Razorpay Test Mode payment link is created (`execution_mode:
  razorpay_test` when Razorpay credentials are configured; `simulation` otherwise).
- **Verification:** simulated customer completion → captured.
- **Result:** RECOVERED, ₹499.

> "This is the straightforward case: clear cause, safe action, real Razorpay Test
> Mode object created, verified outcome."

## 4. Case 2 — a payment that gets escalated (60 sec)

Open **TXN0023**.

- **What happened:** ₹4,999, `authentication_failure`, and — critically — the payment
  status is `uncertain`: it's not clear whether the deduction actually went through.
- **AI/rule diagnosis:** because status is uncertain, the recommendation is forced to
  `verify_then_decide` — never a retry.
- **Safety check:** this rule is enforced independently by the guardrail layer too,
  not just the diagnosis — even if the AI recommended something else, the guardrail
  would override it to verification.
- **Execution:** verification step runs (simulated for synthetic data — no real
  Razorpay `payment_id` exists to query).
- **Result:** verification couldn't confirm capture → ESCALATED to a human, not
  retried automatically.

> "This is the safety story: an ambiguous deduction is never blindly retried. Worst
> case here is a human looks at it — not a double charge."

## 5. Case 3 — a payment blocked by a safety guardrail (60 sec)

Open **TXN0004**.

- **What happened:** ₹4,999, `gateway_error`, retry_count already at 3 — **and the
  customer has opted out of recovery contact.**
- **AI/rule diagnosis:** recognizes the opt-out and recommends `stop_no_retry`.
- **Safety check:** BLOCKED — shown explicitly in the UI as the safety layer's own
  decision, independent of what the AI said. "Customer has opted out of recovery
  contact. This overrides any AI or strategy recommendation."
- **Execution:** none. No charge attempted, no contact made.
- **Result:** SKIPPED — ₹4,999 protected from an unwanted contact, not "recovered,"
  and the metrics don't pretend otherwise.

> "This is deliberately not a success story in the revenue sense — it's a success
> story in the trust sense. The agent knows when *not* to act, and the UI treats that
> as a first-class outcome, not a failure to hide."

## 6. Back to the numbers (30 sec)

Return to the dashboard. Point at:

- **Guardrail intervention count** (8 in this run) — "every one of these is the
  deterministic layer overriding or confirming a stop, independent of the AI."
- **AI recommendation acceptance rate** (~94%) — "most of the time the AI's call
  stood; the safety layer stepping in is the exception, and it's visible when it
  happens, not silent."
- **Recovery by failure reason / by strategy** — different failure types genuinely
  get different treatment; this isn't one strategy applied uniformly.

## 7. Close (20 sec)

> "₹1,62,980 was at risk. ₹51,266 came back — verified, not assumed. The rest wasn't
> ignored; it was either escalated to a human or explicitly protected by a rule you
> can point to. That's the product: AI does the diagnosis, deterministic code decides
> what's safe to do with someone's money."
