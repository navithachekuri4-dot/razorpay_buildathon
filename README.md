# AI Revenue Recovery Agent

An AI-powered revenue recovery system that identifies payments at risk, understands why they failed, recommends the next recovery action, and executes it only when it is safe to do so.

Built for the **Razorpay AI Buildathon 2026 — AI Revenue Recovery track**.

## 🔗 Links

🌐 **Live Application:** https://razorpay-buildathon-one.vercel.app/

⚙️ **Backend API Docs:** https://razorpay-buildathon-orcx.onrender.com/docs

📂 **GitHub Repository:** https://github.com/navithachekuri4-dot/razorpay_buildathon

---

## 🎯 Problem

A failed payment does not always mean lost revenue.

Different payment failures require different recovery strategies:

- Insufficient funds → retry later
- Temporary gateway error → retry
- Expired card → ask the customer to update the payment method
- Uncertain deduction → verify before retrying
- Customer opt-out → stop recovery attempts

The problem is therefore not simply:

> **Retry every failed payment.**

The system needs to answer:

**What happened? → What should we do? → Is it safe? → Did we recover the money?**

---

## 💡 Solution

I built an **AI Revenue Recovery Agent** that performs an end-to-end recovery workflow:

```text
Detect
  ↓
Assess Risk
  ↓
Diagnose with AI
  ↓
Select Recovery Strategy
  ↓
Apply Safety Guardrails
  ↓
Execute Recovery
  ↓
Verify Result
  ↓
Measure Revenue Recovered
```

The key design principle is:

> **AI recommends the action, but deterministic code decides whether the action is allowed.**

This prevents an AI recommendation from directly performing an unsafe financial operation.

---

## 🤖 AI Integration

Gemini is used to diagnose payment failures and recommend the next recovery action.

### Model

```text
Google Gemini 3.5 Flash Lite
```

The AI receives transaction context such as:

- payment amount
- failure reason
- retry count
- customer opt-out status
- payment status

It returns a structured response containing:

- failure diagnosis
- recommended action
- confidence
- reasoning

Example:

```text
Payment amount: ₹1,999
Failure reason: insufficient_funds
Retry count: 1
Customer opted out: No
```

Gemini may recommend:

```text
Action: retry_after_delay
Confidence: 0.85
```

The recommendation is then validated and passed through deterministic safety checks before execution.

---

## 🔄 Recovery Actions

The agent supports a controlled set of recovery actions:

```text
retry_now
retry_after_delay
send_update_card_link
send_payment_link
escalate
stop_no_retry
verify_then_decide
```

Restricting the action vocabulary prevents the AI from inventing arbitrary payment operations.

---

## 🛡️ Safety & Guardrails

Payment recovery requires strong controls, so safety decisions are handled separately from AI reasoning.

### Retry Limit

A transaction cannot be retried indefinitely.

Default maximum:

```text
3 retries
```

### Customer Opt-Out

If a customer has opted out of recovery communication, the system stops further recovery attempts.

### Already Captured Payment

If a payment is already captured, the system does not attempt another recovery action.

### Uncertain Deduction

If money may already have been deducted but the payment status is unclear, the system does not blindly retry.

It first requires verification.

### Successful Recovery

Once a payment is successfully recovered, the workflow stops for that transaction.

### AI Cannot Bypass Guardrails

Even if Gemini recommends a retry with high confidence, deterministic rules can reject it.

```text
AI decides what might work.
Rules decide what is allowed.
```

---

## 🏗️ Architecture

```text
                    Payment Events
                          |
                          v
                 Revenue Risk Engine
                          |
                          v
                   AI Diagnosis
                      (Gemini)
                          |
                          v
                 Recovery Strategy
                          |
                          v
             Deterministic Guardrails
                    /           \
                   /             \
                Block           Allow
                  |                |
                  v                v
             Stop / Log     Recovery Executor
                                  |
                                  v
                       Payment Result Verifier
                                  |
                         +--------+--------+
                         |                 |
                         v                 v
                    Audit Trail        Metrics
```

### Main Components

**Revenue Risk Engine**

Identifies at-risk payments and calculates a risk score using transaction amount, failure reason, retry history and payment state.

**AI Diagnosis**

Uses Gemini to understand the failure and recommend a recovery action.

**Recovery Strategy**

Maps the diagnosis to a supported recovery action.

**Deterministic Guardrails**

Checks whether the proposed action is safe and permitted.

**Recovery Executor**

Executes the approved action using Razorpay Test Mode or simulation.

**Payment Result Verifier**

Determines whether the recovery attempt actually succeeded.

**Audit Trail**

Records the important decisions and results throughout the workflow.

**Metrics**

Calculates recovery performance from transaction data.

---

## 📊 Example Decision

Consider:

```text
Transaction:        TXN0002
Amount:             ₹1,999
Failure reason:     insufficient_funds
Retry count:        1
Opt-out:            No
```

Gemini recommends:

```text
Action: retry_after_delay
Confidence: 0.85
```

The safety layer checks:

```text
Already captured?        No
Customer opted out?      No
Retry limit reached?     No
Payment status unclear?  No
```

The action is allowed.

If the recovery succeeds:

```text
RECOVERED
₹1,999 recovered
```

The transaction is then marked as recovered and no further retry is attempted.

---

## 📈 Revenue Recovery Metrics

The dashboard tracks actual application data, including:

- Total revenue at risk
- Total revenue recovered
- Recovery rate
- Transactions processed
- Transactions recovered
- Transactions escalated
- Guardrail interventions
- Failed recovery attempts

The recovery rate is based on the application's processed transaction data.

```text
Revenue at Risk
       ↓
Recovery Attempts
       ↓
Successful Recoveries
       ↓
Revenue Recovered
       ↓
Recovery Rate
```

The demo uses synthetic transactions, so displayed recovery numbers are demonstration results and not production performance claims.

---

## 🖥️ Dashboard

The frontend provides multiple views:

### Overview

Displays:

- revenue at risk
- recovered revenue
- recovery rate
- processed transactions
- recovered transactions
- escalations
- guardrail interventions
- recovery pipeline

### Transactions

Displays individual payment records, failure reasons and recovery actions.

### Recovery Queue

Shows transactions currently eligible for recovery.

### Analytics

Displays recovery performance metrics.

### Guardrails

Shows transactions where safety rules affected or blocked a proposed action.

### Audit Logs

Shows the decision timeline:

```text
Detect
  ↓
Risk Assessment
  ↓
AI Diagnosis
  ↓
Recovery Decision
  ↓
Safety Check
  ↓
Execution
  ↓
Verification
```

---

## 🧪 Dynamic Demo Batches

The application supports generating additional synthetic payment batches.

The initial dataset contains:

```text
120 transactions
```

Clicking **Generate New Demo Batch** appends another 120 transactions without deleting existing data.

Example:

```text
Initial Batch
120 transactions

        +

New Batch
120 transactions

        =

240 transactions
```

Previously processed transactions are not processed again.

The `/seed` endpoint can be used when a clean reset is required.

---

## 🔁 AI Failure Handling

The system does not completely depend on Gemini being available.

If Gemini:

- times out
- cannot be reached
- returns malformed JSON
- returns an unsupported action
- returns invalid confidence data
- fails validation

the application uses a deterministic rule-based fallback.

The fallback goes through the same safety and recovery workflow.

Audit logs identify whether the diagnosis came from:

```text
GEMINI
```

or:

```text
FALLBACK
```

This allows the recovery pipeline to remain functional even when the AI service is unavailable.

---

## 💳 Razorpay Integration

The project is designed for **Razorpay Test Mode**.

For the buildathon demonstration, recovery execution can also use simulation.

No real customer payments are processed.

This allows the complete recovery workflow to be demonstrated without putting real customer money at risk.

---

## 🧰 Technology Stack

### Frontend

- React
- Vite
- JavaScript
- CSS

### Backend

- Python
- FastAPI
- SQLAlchemy
- SQLite

### AI

- Google Gemini API
- Structured JSON responses
- AI response validation
- Deterministic fallback

### Payments

- Razorpay Test Mode
- Simulation

### Testing

- Pytest

---

## 🔌 API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Check backend health |
| POST | `/seed` | Reset and seed demo transactions |
| POST | `/seed/batch` | Append a new demo batch |
| GET | `/transactions` | List transactions |
| GET | `/transactions/{transaction_id}` | Get one transaction |
| POST | `/recover/batch` | Process the recovery queue |
| POST | `/recover/{transaction_id}` | Recover one transaction |
| GET | `/audit/{transaction_id}` | Get transaction audit logs |

FastAPI Swagger documentation is available through the backend API link above.

---

## 📁 Project Structure

```text
razorpay_buildathon/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── seed_data.py
│   │   └── services/
│   │       ├── ai_diagnosis.py
│   │       ├── razorpay_service.py
│   │       └── ...
│   │
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── api.js
│   └── package.json
│
├── docs/
├── .gitignore
└── README.md
```

---

## 🚀 Running Locally

### Backend

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv .venv
```

On Windows:

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```text
DATABASE_URL=sqlite:///./revenue_recovery.db
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
MAX_RETRY_COUNT=3
```

Start the backend:

```bash
uvicorn app.main:app --reload
```

### Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL provided by Vite.

---

## ✅ Testing

The project includes automated tests covering:

- API behaviour
- seed data generation
- dynamic batch generation
- recovery orchestration
- AI response validation
- safety guardrails
- retry limits
- opt-out protection
- payment verification
- fallback behaviour

Run:

```bash
python -m pytest -q
```

Current test result:

```text
50 passed
```

---

## 🎬 Demo Flow

A typical demonstration:

1. Open the Revenue Recovery dashboard.
2. Generate a new demo batch.
3. Open the Recovery Queue.
4. Start batch recovery.
5. Open Audit Logs.
6. Select a transaction.
7. Show the Gemini diagnosis.
8. Show the recommended recovery action.
9. Show the deterministic safety decision.
10. Show execution.
11. Show verification.
12. Return to Overview.
13. Show recovered revenue.
14. Open Guardrails and demonstrate an unsafe action being blocked.

The strongest demo is one where you show both:

```text
AI recommendation → Recovery succeeds
```

and:

```text
AI recommendation → Guardrail blocks unsafe action
```

---

## ⭐ What Makes This Approach Different

The project is not just an AI classifier for payment failures.

It builds the complete recovery loop:

```text
Detect
  ↓
Diagnose
  ↓
Decide
  ↓
Protect
  ↓
Act
  ↓
Verify
  ↓
Measure
```

The key separation is between **AI reasoning** and **financial execution**.

Gemini can recommend:

```text
retry_now
retry_after_delay
send_update_card_link
send_payment_link
escalate
```

But deterministic code controls whether the action is actually allowed.

This makes the system easier to:

- test
- audit
- explain
- control
- demonstrate safely

---

## 🔐 Security Considerations

- API keys are stored as environment variables.
- Secrets are not committed to the repository.
- Synthetic transaction data is used.
- Razorpay Test Mode/simulation is used.
- Recovery actions are restricted by deterministic rules.
- Secrets should never be included in source code, screenshots, commits or public logs.

---

## ⚠️ Limitations

This is a buildathon prototype, not a production payment recovery system.

Current limitations include:

- Synthetic demo transactions
- Razorpay Test Mode/simulation
- Simplified recovery policies
- Gemini API availability and quota limitations
- No production-grade authentication or access control
- No large historical dataset for learning recovery policies
- Additional fraud, compliance and monitoring controls would be required for production

---

## 🔮 Future Improvements

- Learn recovery policies from historical outcomes
- Personalize recovery timing
- Add more payment failure patterns
- Add human approval for high-value recoveries
- Add email/SMS recovery workflows
- Improve duplicate-payment detection
- Add fraud-risk checks
- Build offline evaluation datasets
- Track long-term recovery performance

---

## 🏆 Buildathon Track

Built for:

**Razorpay AI Buildathon 2026**

Track:

**AI Revenue Recovery**

The project focuses on:

- detecting revenue at risk
- diagnosing payment failures
- selecting the appropriate intervention
- executing bounded recovery actions
- measuring recovered revenue
- applying stopping rules
- handling escalation
- maintaining an audit trail
- applying deterministic safety controls around AI decisions

---

## 📌 Disclaimer

This is a student buildathon prototype using synthetic data and Razorpay Test Mode/simulation.

It does not process real customer payments.

Demonstrated recovery numbers are prototype results and should not be interpreted as production performance.
