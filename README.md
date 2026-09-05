# AI Revenue Recovery Agent

An AI-powered revenue recovery system that identifies payments at risk, understands why they failed, recommends the next recovery action, and executes it only when it is safe to do so.

Built for the **Razorpay AI Buildathon 2026 — AI Revenue Recovery track**.

## 🔗 Links

🌐 **Live Application:** https://razorpay-buildathon-one.vercel.app/

⚙️ **Backend API Docs:** https://razorpay-buildathon-orcx.onrender.com/docs

📂 **GitHub Repository:** https://github.com/navithachekuri4-dot/razorpay_buildathon

---

## Problem

A failed payment does not always mean lost revenue.

Different payment failures need different responses.

For example:

- An insufficient-funds failure may be worth retrying after some time.
- A temporary gateway error may be worth retrying immediately.
- An expired card may require the customer to update their payment method.
- An unclear deduction status should not be retried blindly because the customer may already have been charged.
- A customer who has opted out should not continue receiving recovery attempts.

So the problem is not simply:

> Retry every failed payment.

The system needs to answer:

**What happened? → What should we do? → Is it safe? → Did we recover the money?**

---

## What I Built

I built an **AI Revenue Recovery Agent** that follows a complete recovery workflow:

1. Detect payments that are at risk.
2. Calculate a risk score.
3. Diagnose the payment failure.
4. Use Gemini to recommend the next recovery action.
5. Validate the AI response.
6. Apply deterministic safety rules.
7. Execute the approved action using Razorpay Test Mode or simulation.
8. Verify the payment result.
9. Record the decision in an audit trail.
10. Measure the revenue recovered.

The main design decision is:

> **AI recommends the action, but deterministic code decides whether the action is allowed.**

This prevents an AI response from directly performing an unsafe financial operation.

---

## AI's Role

Gemini is used for payment failure diagnosis and recovery recommendation.

The AI receives transaction information and failure context and returns a structured response containing:

- failure diagnosis
- recommended recovery action
- confidence
- reasoning

For example:

```text
Payment amount: ₹1,999
Failure reason: insufficient_funds
Retry count: 1
Customer opted out: No
```

Gemini can recommend:

```text
Action: retry_after_delay
Confidence: 0.85
```

The recommendation is then passed through the deterministic safety layer before execution.

The AI is therefore part of the actual decision-making process instead of being used only as a chatbot or text generator.

---

## Recovery Actions

The agent works with a controlled set of recovery actions:

```text
retry_now
retry_after_delay
send_update_card_link
send_payment_link
escalate
stop_no_retry
verify_then_decide
```

The action vocabulary is restricted so the AI cannot invent arbitrary payment operations.

---

## Safety and Guardrails

Because this system deals with payment recovery, safety is handled separately from the AI recommendation.

The deterministic guardrail layer has the final authority.

### Retry Limit

A transaction cannot be retried indefinitely.

The default maximum retry count is:

```text
3 retries
```

### Customer Opt-Out

If a customer has opted out of recovery communication, the system stops instead of continuing recovery attempts.

### Already Captured Payment

If a payment has already been captured, the system does not attempt another recovery action.

### Uncertain Deduction

If money may already have been deducted but the payment status is unclear, the system does not blindly retry.

It first requires verification.

### Stop After Successful Recovery

Once a payment is successfully recovered, the workflow stops for that transaction.

### AI Cannot Bypass Guardrails

Even if Gemini recommends a retry with high confidence, the deterministic safety layer can reject it.

The basic principle is:

> **AI decides what might work. Rules decide what is allowed.**

---

## Architecture

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

#### Payment Events

Contains transaction information and payment failure status.

#### Revenue Risk Engine

Identifies at-risk revenue and calculates a risk score using information such as:

- transaction amount
- failure reason
- retry history
- customer opt-out status
- uncertain payment status

#### AI Diagnosis

Gemini analyzes the payment context and returns a structured recovery recommendation.

#### Recovery Strategy

Converts the diagnosis into one of the supported recovery actions.

#### Deterministic Safety Guardrails

Checks whether the recommended action is safe and permitted.

#### Recovery Executor

Executes the approved recovery action using Razorpay Test Mode or simulation.

#### Payment Result Verifier

Checks the result of the recovery attempt and determines whether the payment was successfully recovered.

#### Audit Trail

Records important decisions and results throughout the workflow.

#### Metrics

Calculates recovery performance from transaction data.

---

## Example Decision

Consider a payment that failed because of insufficient funds.

```text
Transaction:        TXN0002
Amount:             ₹1,999
Failure reason:     insufficient_funds
Retry count:        1
Opt-out:            No
```

The risk engine evaluates the transaction.

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

The recovery action is executed and the result is verified.

If the payment succeeds:

```text
RECOVERED
₹1,999 recovered
```

The transaction is then marked as recovered and no further retry is attempted.

---

## Dashboard

The frontend provides several views of the recovery process.

### Overview

Shows:

- total revenue at risk
- revenue recovered
- recovery rate
- transactions processed
- recovered transactions
- escalated transactions
- guardrail interventions
- recovery pipeline

### Transactions

Shows individual payment records, failure reasons and recovery actions.

### Recovery Queue

Shows transactions that are currently eligible for recovery processing.

### Analytics

Shows recovery metrics calculated from transaction data.

### Guardrails

Shows transactions where safety rules affected or blocked the proposed recovery action.

### Audit Logs

Shows the complete decision timeline:

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

This makes it possible to understand what the agent did and why.

---

## Measuring Revenue Recovery

The project measures the financial outcome of the recovery workflow.

The dashboard tracks:

- Total revenue at risk
- Total revenue recovered
- Recovery rate
- Transactions processed
- Transactions recovered
- Transactions escalated
- Guardrail interventions
- Failed recovery attempts

The metrics are calculated from the application's transaction data rather than being hard-coded into the dashboard.

The recovery flow is:

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

The demo uses synthetic transactions, so these numbers are demonstration results and are **not production performance claims**.

---

## Dynamic Demo Batches

The application supports generating additional demo batches.

The initial demo dataset contains:

```text
120 synthetic transactions
```

The **Generate New Demo Batch** feature adds another 120 synthetic transactions without deleting previously processed transactions.

For example:

```text
Initial batch
120 transactions

        +

New demo batch
120 transactions

        =

240 transactions
```

The application processes only transactions that have not already been processed.

The `/seed` endpoint can still be used when a clean reset of the demo data is needed.

---

## AI Failure Handling

The application does not completely depend on Gemini being available.

If Gemini:

- times out
- cannot be reached
- returns malformed JSON
- returns an unsupported action
- returns invalid confidence data
- or otherwise fails validation

the application uses a deterministic rule-based fallback.

The fallback recommendation is also passed through the same recovery and safety workflow.

This means an AI service failure does not cause the entire recovery pipeline to fail.

The audit log records whether the diagnosis came from:

```text
GEMINI
```

or:

```text
FALLBACK
```

---

## Razorpay Integration

The project is designed to work with **Razorpay Test Mode**.

For the buildathon demonstration, payment execution can also use simulation.

No real customer payments are processed.

This allows the complete recovery workflow to be demonstrated without putting real customer money at risk.

---

## Technology Stack

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
- Simulation mode

### Testing

- Pytest

---

## API Endpoints

The backend exposes REST APIs for the main recovery operations.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Check backend health |
| POST | `/seed` | Reset and seed demo transactions |
| POST | `/seed/batch` | Append a new demo batch |
| GET | `/transactions` | List transactions |
| GET | `/transactions/{transaction_id}` | Get one transaction |
| POST | `/recover/batch` | Process the recovery queue |
| POST | `/recover/{transaction_id}` | Recover one transaction |
| GET | `/audit/{transaction_id}` | Get the transaction audit trail |

The backend also provides automatically generated API documentation through FastAPI Swagger.

---

## Project Structure

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
│
├── .gitignore
└── README.md
```

---

## Running the Project Locally

### Backend

Go to the backend directory:

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

Create a `.env` file using `.env.example`.

Example:

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
```

Install dependencies:

```bash
npm install
```

Start the frontend:

```bash
npm run dev
```

Open the local URL provided by Vite.

---

## Testing

The backend contains automated tests for important parts of the recovery workflow, including:

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

Run the test suite with:

```bash
python -m pytest -q
```

Current test result:

```text
50 passed
```

---

## Demo Flow

A typical demonstration can be run as follows:

1. Open the Revenue Recovery dashboard.
2. Generate a new demo batch if required.
3. Open the Recovery Queue.
4. Start the recovery process.
5. Open Audit Logs.
6. Select a transaction.
7. Show the Gemini diagnosis.
8. Show the recommended recovery action.
9. Show the deterministic safety decision.
10. Show the execution result.
11. Show the verification result.
12. Return to Overview.
13. Show the updated recovered revenue.
14. Open Guardrails and demonstrate a transaction where an unsafe action was blocked.

A useful example is an insufficient-funds transaction where Gemini recommends `retry_after_delay`, followed by successful recovery and verification.

---

## What Makes the Approach Different

I did not want the project to simply classify payment failures using AI.

The goal was to build the complete recovery loop:

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

The important design choice is the separation between AI reasoning and financial execution.

The AI can recommend an action, but it cannot override:

- retry limits
- customer opt-out
- captured payment checks
- uncertain deduction checks
- deterministic safety rules

This makes the system easier to test, explain and control.

---

## Security Considerations

API keys are stored as environment variables and are not committed to the repository.

The project uses synthetic transaction data.

Razorpay Test Mode and simulation are used for the demonstration rather than real customer payments.

Recovery actions are restricted by deterministic safety rules.

Secrets should never be included in:

- source code
- README files
- GitHub commits
- screenshots
- frontend code
- public logs

---

## Limitations

This is a buildathon prototype and not a production payment recovery system.

Current limitations include:

- Demo transactions are synthetic.
- Payment execution uses Razorpay Test Mode and simulation.
- Recovery policies are simplified for the prototype.
- AI diagnosis depends on Gemini availability and API limits.
- Production deployment would require additional authentication, monitoring, access controls, fraud prevention and compliance reviews.
- The current recovery strategy is rule-guided rather than learned from a large historical payment dataset.

---

## Future Improvements

Possible improvements include:

- Learning recovery policies from historical recovery outcomes.
- Personalizing recovery timing for different customer segments.
- Adding more payment failure patterns.
- Adding human approval for high-value recoveries.
- Adding email or SMS recovery notifications.
- Adding stronger duplicate-payment detection.
- Adding fraud-risk checks.
- Building offline evaluation datasets for recovery strategies.
- Tracking recovery performance over longer periods.

---

## Buildathon Track

This project was built for:

**Razorpay AI Buildathon 2026**

Track:

**AI Revenue Recovery**

The project focuses on:

- detecting revenue at risk
- diagnosing payment failures
- selecting the appropriate intervention
- executing bounded recovery actions
- measuring recovered revenue
- handling escalation and stopping conditions
- maintaining an audit trail
- applying deterministic safety controls around AI decisions

---

## Disclaimer

This is a student buildathon prototype using synthetic data and Razorpay Test Mode/simulation.

It does not process real customer payments, and the demonstrated recovery numbers should not be interpreted as production performance.
