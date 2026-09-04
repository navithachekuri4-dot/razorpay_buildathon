# AI Revenue Recovery Agent

**Razorpay AI Buildathon 2026 — Track: AI Revenue Recovery**

> Every failed payment is not just a failed transaction. It is potentially lost revenue.
> This agent decides, safely, whether it can be won back.

---

## 1. Problem

Subscription and e-commerce businesses lose real revenue to failed payments — expired
cards, bank timeouts, insufficient funds, gateway errors. Most of that revenue is not
actually gone; it is *recoverable*, if someone (or something) diagnoses why the payment
failed and takes the right next action quickly and safely.

Doing this by hand doesn't scale. Doing it with a bot that blindly retries everything is
dangerous — it can double-charge customers, retry people who asked to be left alone, or
keep hammering a payment that will never succeed.

## 2. Solution

An agent that runs every at-risk transaction through seven explicit steps:

```
DETECT → DIAGNOSE → DECIDE → SAFETY → ACT → VERIFY → RECOVER
```

An AI model diagnoses *why* a payment failed and *recommends* a next action. A completely
separate, deterministic safety layer decides whether that action is actually allowed to
run. Every step is written to an audit trail, so any transaction's full history —
diagnosis, decision, safety check, execution, result — can be reconstructed after the
fact.

## 3. Why this matters (to a merchant / Razorpay)

- Recovering even 20-30% of failed-payment revenue is a direct, measurable line to
  the bottom line — no new customer acquisition required.
- Doing recovery automation *unsafely* (retrying blindly, ignoring opt-outs, retrying an
  already-successful payment) creates real financial and compliance risk. Trust in the
  recovery system matters as much as its recovery rate.
- This project treats both halves as first-class: how much revenue comes back, and how
  provably safe the process was to get it there.

## 4. Core architectural principle

> **AI recommends. Deterministic code controls money.**

The LLM (Gemini) never touches a payment. It only produces a diagnosis and a
recommended action. A pure-Python guardrail layer — no model calls, no probabilities —
has the final and only say over what actually executes. This separation is enforced in
code (`app/services/guardrails.py` runs after and independently of `app/services/ai_diagnosis.py`)
and made visible in the UI (the Transaction Inspector shows the AI's recommendation and
the safety layer's decision as two distinct blocks).

```
Payment Events
      │
      ▼
Revenue Risk Engine          (deterministic 0-100 score)
      │
      ▼
AI Diagnosis                 (Gemini, or rule-based fallback — recommends only)
      │
      ▼
Recovery Strategy             (reconciles AI + simple business rules)
      │
      ▼
Deterministic Safety Guardrails   ← the only layer allowed to authorize execution
      │
      ▼
Recovery Executor             (Razorpay Test Mode / simulation)
      │
      ▼
Payment Result Verifier
      │
      ▼
Audit Trail  +  Revenue Metrics
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full breakdown, and
[`docs/PANEL_PREP.md`](docs/PANEL_PREP.md) for 20 hard questions with honest answers.

## 5. Safety guardrails (deterministic, non-negotiable)

Implemented in `backend/app/services/guardrails.py`, run in this priority order — the
first rule that matches wins:

1. **Already recovered** → stop. Never act on a transaction twice (no double charge).
2. **Customer opted out** → stop. Overrides every other signal, including the AI.
3. **Payment already captured** → stop. Never touch a successful payment.
4. **Deduction status uncertain** → force verification before any retry. Never blindly
   retry a payment that might already have gone through.
5. **Retry limit reached** (default 3) → escalate to a human instead of retrying again,
   even if the AI recommended a retry.
6. Otherwise, the strategy's proposed action is allowed through.

## 6. AI role

Gemini receives structured transaction context (amount, failure reason, payment status,
retry history, opt-out flag) and returns structured JSON: likely cause, recommended
action, reasoning, confidence. If Gemini is unavailable — no API key, network failure,
timeout, or a response that doesn't match the expected shape/vocabulary — the app falls
back to a deterministic rule-based diagnoser that covers the same cases. Every diagnosis
records its `ai_source` as `GEMINI` or `FALLBACK` so nothing is hidden. **The app works
fully with zero AI credentials configured.**

## 7. Razorpay Test Mode

`backend/app/services/razorpay_service.py` is the only file that talks to Razorpay.

- Live keys (`rzp_live_...`) are hard-blocked at startup — the app cannot run in live
  mode even by accident.
- **Real Razorpay Test Mode API calls** happen for the two actions that map to genuine
  Razorpay objects: creating a recovery **Order** (for retry actions) and creating a
  **Payment Link** (for "update your card" actions). These return real test-mode
  IDs/URLs.
- Because this project's transactions are synthetic (no real card is attached to them),
  whether that order/link actually gets "paid" is decided by a **seeded, deterministic
  simulation** — not invented from a real capture event. This is recorded honestly on
  every transaction via `execution_mode: "razorpay_test" | "simulation"`.
- Missing credentials, network errors, or API failures all fall back to simulation
  automatically. The app never crashes on Razorpay unavailability.

## 8. Synthetic data

120 synthetic failed-payment transactions, seeded deterministically (`SEED = 42` in
`backend/app/seed_data.py`) so every demo run starts from the same dataset. Includes a
realistic mix of failure reasons, some customers who've opted out, some transactions
with an ambiguous deduction status, and some that have already exhausted their retry
budget — so the demo can honestly show recovery, escalation, *and* guardrail blocking.

**This is not real customer data and no real money moves at any point.**

## 9. Metrics

Computed live from the database on every request (`backend/app/services/metrics.py`) —
nothing is hardcoded:

- Total revenue at risk / recovered, recovery rate
- Recovered / failed / escalated / safely-stopped counts
- Guardrail intervention count
- AI recommendation acceptance rate (how often the safety layer left the AI's
  recommendation unchanged)
- Recovery broken down by failure reason and by strategy, with amount recovered per
  strategy

Numbers shown anywhere in this README or the UI are from a synthetic demo run and are
**not** a claim about real-world merchant performance.

## 10. Project structure

```
revenue-recovery-agent/
├── backend/
│   ├── app/
│   │   ├── main.py              FastAPI app + all endpoints
│   │   ├── config.py            env-driven settings
│   │   ├── database.py          SQLAlchemy engine/session
│   │   ├── models.py            Transaction, AuditLog
│   │   ├── schemas.py           Pydantic response models
│   │   ├── seed_data.py         synthetic dataset generator
│   │   └── services/
│   │       ├── risk_engine.py       Revenue Risk Engine
│   │       ├── ai_diagnosis.py      Gemini + deterministic fallback
│   │       ├── strategy.py          strategy decision
│   │       ├── guardrails.py        deterministic safety layer
│   │       ├── executor.py          recovery executor
│   │       ├── verifier.py          payment result verifier
│   │       ├── razorpay_service.py  Razorpay Test Mode + simulation
│   │       ├── orchestrator.py      runs the full 7-step pipeline
│   │       └── metrics.py           live metrics computation
│   ├── tests/                   40 tests across every module above
│   ├── requirements.txt
│   └── .env.example
├── frontend/                    React + Vite Revenue Recovery Command Center
│   └── src/
│       ├── App.jsx
│       ├── api.js
│       └── components/
└── docs/
    ├── ARCHITECTURE.md
    ├── DEMO_SCRIPT.md
    └── PANEL_PREP.md
```

## 11. Running locally

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt
cp .env.example .env       # fill in GEMINI_API_KEY / RAZORPAY_* only if you have them —
                            # the app works fully without them
uvicorn app.main:app --reload --port 8000
```

Swagger docs: http://127.0.0.1:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173. The Vite dev server proxies `/api/*` to the backend on
port 8000 (see `frontend/vite.config.js`).

### First run

The UI will show an empty state with a **"Seed demo data"** button (calls `POST
/seed`). After seeding, click **"Run recovery batch"** to process all transactions
through the full pipeline.

## 12. Environment variables

| Variable | Required? | Purpose |
|---|---|---|
| `DATABASE_URL` | No | Defaults to a local SQLite file |
| `GEMINI_API_KEY` | No | If unset, the deterministic fallback diagnoser is used |
| `GEMINI_MODEL` | No | Defaults to `gemini-2.0-flash` |
| `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` | No | Must be **Test Mode** keys (`rzp_test_...`). If unset, everything runs in simulation. `rzp_live_...` keys are rejected outright. |
| `MAX_RETRY_COUNT` | No | Defaults to 3 |

Never commit a real `.env` file. `.env.example` documents the shape; `.env` is
git-ignored.

## 13. Testing

```bash
cd backend
python -m pytest tests/ -v
```

40 tests, covering: risk scoring, AI diagnosis (including malformed/out-of-vocabulary
Gemini responses and the no-credentials fallback path), every guardrail rule in
isolation and in combination, strategy overrides, Razorpay live-key blocking and
simulation fallback, the full 7-step pipeline end-to-end, and every API endpoint.
All 40 currently pass.

## 14. Demo flow

See [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) for the full 5-minute walkthrough,
including three contrasting transactions (recovered / escalated / guardrail-blocked).

## 15. Limitations (stated honestly)

- **Synthetic data, not production traffic.** All 120 transactions are generated by a
  seeded random process; there is no real merchant, customer, or card behind any of
  them.
- **No real capture events.** Razorpay Test Mode Orders and Payment Links created by
  this app are real API objects, but whether they'd be "paid" is simulated, because no
  real card is ever entered. In production, this step would be driven by real Razorpay
  webhooks (`payment.captured`, `payment.failed`) rather than a seeded coin flip.
  See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for how that would change.
- **Verification of an "uncertain" deduction is simulated**, since synthetic
  transactions have no real Razorpay `payment_id` to query. In production this calls
  `client.payment.fetch(id)`.
- **Single-process SQLite.** Fine for a demo; a production system would need a
  concurrency-safe database and idempotency keys per recovery attempt (see
  `docs/ARCHITECTURE.md` for the scaling discussion).
- **No authentication on the API.** Out of scope for a buildathon demo; a real
  deployment would need it.

## 16. Future improvements

- Real Razorpay webhook integration to replace simulated capture/verification outcomes.
- Idempotency keys per recovery attempt for true exactly-once execution under retries/
  concurrent requests.
- A/B testing different recovery strategies per failure reason and measuring actual
  lift.
- Configurable guardrail thresholds per merchant (still deterministic, just
  parameterized).
- Postgres + a task queue (e.g. Celery/RQ) for concurrent batch processing at scale.
