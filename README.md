# AI Revenue Recovery Agent

### Razorpay AI Buildathon 2026 · AI Revenue Recovery

> **Find revenue that's slipping away and win it back — safely.**

An AI-assisted revenue recovery system that identifies potentially recoverable payments, diagnoses failure reasons, recommends the next-best recovery action, applies deterministic safety controls, executes approved actions in Razorpay Test Mode or simulation, verifies the outcome, and measures recovered revenue.

---

## Table of Contents

- [Overview](#overview)
- [Problem](#problem)
- [Solution](#solution)
- [Architecture](#architecture)
- [Core Design Principle](#core-design-principle)
- [AI Decision Layer](#ai-decision-layer)
- [Safety Guardrails](#safety-guardrails)
- [Razorpay Test Mode](#razorpay-test-mode)
- [Demo Results](#demo-results)
- [Revenue Recovery Dashboard](#revenue-recovery-dashboard)
- [Synthetic Dataset](#synthetic-dataset)
- [Metrics](#metrics)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Running Locally](#running-locally)
- [Environment Variables](#environment-variables)
- [API](#api)
- [Testing](#testing)
- [Demo Flow](#demo-flow)
- [Limitations](#limitations)
- [Future Improvements](#future-improvements)
- [Documentation](#documentation)

---

# Overview

Payment failures do not always mean that revenue is permanently lost.

A failed transaction may be recoverable through the right intervention — such as retrying after a delay, requesting a payment-method update, generating a payment link, or escalating the case.

The challenge is deciding:

- **Which payments should be recovered?**
- **Why did the payment fail?**
- **What should happen next?**
- **Is the proposed action safe?**
- **Did the recovery actually succeed?**
- **When should the system stop?**

The AI Revenue Recovery Agent addresses this through an end-to-end recovery pipeline:

```text
DETECT
   ↓
DIAGNOSE
   ↓
DECIDE
   ↓
SAFETY
   ↓
ACT
   ↓
VERIFY
   ↓
RECOVER
```

---

# Problem

Subscription and e-commerce businesses can lose revenue because of:

- 💳 Insufficient funds
- ⏰ Expired cards
- ❌ Invalid payment methods
- 🌐 Bank or network failures
- ⚠️ Gateway errors
- 🚫 Customer opt-outs
- 🔄 Repeated unsuccessful retries
- ❓ Uncertain payment states

Manual recovery does not scale.

Blind automation creates another problem:

```text
Payment Failed
      ↓
Retry
      ↓
Retry Again
      ↓
Retry Again
```

This can result in:

- unnecessary retries
- potential duplicate charges
- ignoring customer opt-outs
- repeated attempts against unrecoverable payments
- poor customer experience

The problem is therefore not simply **retrying failed payments**.

The problem is:

> **Recover the right revenue while knowing when it is safe to act and when to stop.**

---

# Solution

The AI Revenue Recovery Agent combines:

```text
AI Reasoning
      +
Deterministic Business Logic
      +
Financial Safety Guardrails
      +
Payment Execution
      +
Outcome Verification
      +
Auditability
```

For every transaction, the system moves through seven stages.

### 1. Detect

Identify failed and potentially recoverable transactions using transaction state and risk signals.

### 2. Diagnose

Determine the likely reason for the payment failure.

Gemini can be used for structured diagnosis, with a deterministic fallback when AI is unavailable.

### 3. Decide

Select the next-best recovery action based on the diagnosis and transaction context.

### 4. Safety

Apply deterministic guardrails before any payment-related action is executed.

### 5. Act

Execute the approved action through Razorpay Test Mode or simulation.

### 6. Verify

Check the resulting payment state.

### 7. Recover

Record the outcome and update recovery metrics.

---

# Architecture

```text
┌───────────────────────────────┐
│       Payment Events          │
│   Razorpay Test / Simulation  │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│       Revenue Risk Engine     │
│       Deterministic Score     │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│         AI Diagnosis          │
│    Gemini / Rule Fallback     │
│        Recommendation         │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│       Recovery Strategy       │
│   AI + Business Rule Logic    │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│      Safety Guardrails        │
│       Deterministic           │
│    Final Execution Authority  │
└───────────────┬───────────────┘
                │
         ┌──────┴──────┐
         │             │
       ALLOW       BLOCK / ESCALATE
         │
         ▼
┌───────────────────────────────┐
│      Recovery Executor        │
│   Razorpay Test / Simulation  │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│      Payment Verifier         │
│       Confirm Outcome         │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│      Audit Trail + Metrics    │
│   Revenue + Operational Data  │
└───────────────────────────────┘
```

---

# Core Design Principle

> ## **AI recommends. Deterministic code controls money.**

The AI model does **not** directly execute payments.

Its responsibility is limited to:

```text
Transaction Context
       ↓
AI Diagnosis
       ↓
Recommended Action
```

A separate deterministic safety layer then evaluates whether that recommendation is allowed.

```text
AI Recommendation
       ↓
Deterministic Guardrails
       ↓
┌──────┴───────┐
│              │
ALLOW       BLOCK / ESCALATE
│
↓
Execute
↓
Verify
```

This separation makes financial decisions predictable, testable, and auditable.

---

# AI Decision Layer

Gemini receives structured transaction context such as:

- transaction amount
- failure reason
- payment status
- retry history
- customer opt-out status
- relevant transaction metadata

The model returns structured information including:

- likely cause
- recommended action
- reasoning
- confidence

Example:

```json
{
  "reason": "insufficient_funds",
  "recommended_action": "retry_after_delay",
  "confidence": 0.7
}
```

## Supported Recovery Actions

```text
retry_now
retry_after_delay
send_update_card_link
send_payment_link
escalate
stop_no_retry
verify_then_decide
```

---

# AI Fallback

The application does not depend on Gemini being continuously available.

If Gemini is unavailable because of:

- missing API key
- network failure
- timeout
- API error
- malformed response
- unsupported action
- invalid response structure

the system falls back to deterministic rule-based diagnosis.

Every diagnosis records its source:

```text
GEMINI
```

or:

```text
FALLBACK
```

This provides graceful degradation and keeps the recovery pipeline operational without requiring AI credentials.

> **The application works fully with zero AI credentials configured.**

---

# Safety Guardrails

Financial safety is enforced independently of the AI model.

The guardrail system is deterministic and follows a defined priority order.

## Guardrail Priority

### 1. Already Recovered

```text
Already Recovered
       ↓
STOP
```

A transaction cannot be recovered twice.

### 2. Customer Opted Out

```text
Customer Opted Out
       ↓
STOP
```

The opt-out condition overrides the AI recommendation.

### 3. Payment Already Captured

```text
Already Captured
       ↓
STOP
```

The system does not attempt recovery against an already successful payment.

### 4. Deduction Status Uncertain

```text
Deduction Uncertain
       ↓
VERIFY FIRST
       ↓
DECIDE
```

The system does not blindly retry a transaction that may already have resulted in a deduction.

### 5. Retry Limit Reached

Default:

```text
MAX_RETRY_COUNT = 3
```

Once the retry limit is reached:

```text
Retry Limit Reached
       ↓
ESCALATE / STOP
```

### 6. Otherwise

If none of the blocking conditions apply, the proposed recovery action can proceed.

---

# Razorpay Test Mode

Razorpay interaction is isolated in:

```text
backend/app/services/razorpay_service.py
```

This keeps payment-provider integration separate from the recovery decision logic.

## Execution Modes

```text
Razorpay Test Mode
        +
Simulation Fallback
```

### Test Mode

The application can create supported Razorpay Test Mode objects for recovery actions such as:

- Test Mode Orders
- Test Mode Payment Links

### Simulation

Because the project's transactions are synthetic and do not have real customer cards attached, the final payment outcome is simulated deterministically.

Each transaction records its execution mode:

```text
razorpay_test
```

or:

```text
simulation
```

### Live Payment Protection

Live Razorpay keys are rejected.

The application is designed so that:

```text
rzp_live_...
      ↓
BLOCKED
```

Only Test Mode credentials are accepted.

> **No real customer money is processed by this project.**

---

# Demo Results

The current demo uses **120 deterministic synthetic transactions**.

| Metric | Result |
|---|---:|
| Transactions processed | **120** |
| Revenue potentially at risk | **₹1,62,980** |
| Revenue recovered | **₹51,266** |
| Recovery rate | **31.46%** |
| Transactions recovered | **34** |
| Transactions escalated | **19** |
| Safely stopped / guardrail-blocked | **7** |
| Transactions remaining failed | **60** |

### Important

These numbers are from a controlled synthetic demo run.

They are **not production performance claims**.

---

# Revenue Recovery Dashboard

The frontend provides a **Revenue Recovery Command Center** for observing the complete recovery lifecycle.

## Dashboard Sections

- Overview
- Transactions
- Recovery Queue
- Analytics
- Guardrails
- Audit Logs
- Settings

## Transaction Inspector

A transaction can be inspected through:

```text
Transaction
     ↓
Failure Reason
     ↓
Risk Level
     ↓
AI Recommendation
     ↓
Safety Decision
     ↓
Execution
     ↓
Verification
     ↓
Recovered Amount
```

This makes the distinction between **AI recommendation** and **deterministic safety decision** visible to the user.

---

# Synthetic Dataset

The demo uses deterministic synthetic data.

```text
Transactions = 120
SEED = 42
```

The dataset contains a mixture of:

- insufficient funds
- expired cards
- invalid payment methods
- network failures
- customer opt-outs
- uncertain deduction states
- exhausted retry budgets
- previously captured payments

The fixed seed ensures that every demo run begins with the same dataset.

> **No real customer data or real payment money is used.**

---

# Metrics

Metrics are calculated from the application database rather than being hardcoded.

The system tracks:

- Revenue potentially at risk
- Revenue recovered
- Recovery rate
- Recovered transactions
- Failed transactions
- Escalated transactions
- Safely stopped transactions
- Guardrail interventions
- AI recommendation source
- AI recommendation acceptance
- Recovery by failure reason
- Recovery by strategy
- Amount recovered per strategy

## Recovery Rate

```text
Recovery Rate =
Recovered Revenue
----------------------------- × 100
Revenue Potentially at Risk
```

Metrics are updated as recovery operations are processed and verified.

---

# Audit Trail

Every recovery decision is recorded.

An audit record can contain:

- Transaction ID
- Previous payment state
- Failure reason
- AI recommendation
- AI confidence
- AI source
- Safety decision
- Guardrail reason
- Executed action
- Execution mode
- Verification result
- Recovered amount
- Timestamp

This allows the complete lifecycle of a recovery decision to be reconstructed.

```text
Diagnosis
    ↓
Decision
    ↓
Safety
    ↓
Execution
    ↓
Verification
    ↓
Outcome
```

---

# Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite |
| Backend | Python + FastAPI |
| Database | SQLite + SQLAlchemy |
| Validation | Pydantic |
| AI | Gemini + Deterministic Fallback |
| Payments | Razorpay Test Mode + Simulation |
| Testing | Pytest |
| API Testing | FastAPI TestClient |

---

# Project Structure

```text
razorpay_payment_app/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── seed_data.py
│   │   │
│   │   └── services/
│   │       ├── risk_engine.py
│   │       ├── ai_diagnosis.py
│   │       ├── strategy.py
│   │       ├── guardrails.py
│   │       ├── executor.py
│   │       ├── verifier.py
│   │       ├── razorpay_service.py
│   │       ├── orchestrator.py
│   │       └── metrics.py
│   │
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   └── components/
│   │
│   └── package.json
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DEMO_SCRIPT.md
│   └── PANEL_PREP.md
│
├── .gitignore
├── README.md
└── ...
```

---

# Running Locally

## Prerequisites

- Python 3.x
- Node.js
- npm
- Git

---

## 1. Clone the Repository

```bash
git clone https://github.com/navithachekuri4-dot/razorpay_buildathon.git
cd razorpay_buildathon
```

---

## 2. Start the Backend

```bash
cd backend
```

### Create Virtual Environment

#### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

#### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Create Environment File

#### Windows

```bash
copy .env.example .env
```

#### macOS / Linux

```bash
cp .env.example .env
```

### Start FastAPI

```bash
uvicorn app.main:app --reload --port 8000
```

Backend:

```text
http://127.0.0.1:8000
```

---

# API

## Swagger Documentation

Once the backend is running:

```text
http://127.0.0.1:8000/docs
```

> This is a local development URL and is not a public deployment.

FastAPI Swagger provides an interactive interface for inspecting and testing the API.

---

# Frontend

Open a second terminal:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start Vite:

```bash
npm run dev
```

The frontend will usually run at:

```text
http://127.0.0.1:5173
```

> This is a local development URL and is accessible only when the application is running locally.

The Vite development server proxies:

```text
/api/*
```

to the FastAPI backend.

---

# First Run

When the frontend starts with an empty database:

1. Click **Seed Demo Data**
2. The application creates the synthetic transaction dataset
3. Click **Run Recovery Batch**
4. Transactions move through the complete recovery pipeline
5. Dashboard metrics update automatically

```text
Seed
 ↓
Detect
 ↓
Diagnose
 ↓
Decide
 ↓
Safety
 ↓
Act
 ↓
Verify
 ↓
Metrics
```

---

# Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `DATABASE_URL` | No | Database connection; defaults to local SQLite |
| `GEMINI_API_KEY` | No | Enables Gemini diagnosis |
| `GEMINI_MODEL` | No | Gemini model configuration |
| `RAZORPAY_KEY_ID` | No | Razorpay Test Mode key |
| `RAZORPAY_KEY_SECRET` | No | Razorpay Test Mode secret |
| `MAX_RETRY_COUNT` | No | Maximum retry count; defaults to 3 |

Example:

```env
DATABASE_URL=
GEMINI_API_KEY=
GEMINI_MODEL=
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
MAX_RETRY_COUNT=3
```

If Gemini credentials are not provided, the deterministic fallback diagnoser is used.

If Razorpay Test Mode credentials are not provided, the application runs using simulation.

> ⚠️ Never commit real secrets or `.env` files to GitHub.

---

# Testing

The project includes automated tests covering the major recovery components.

### Test Coverage Includes

- Risk scoring
- AI diagnosis
- Gemini fallback behavior
- Malformed AI responses
- Unsupported AI actions
- Strategy selection
- Strategy overrides
- Customer opt-out
- Already recovered transactions
- Already captured payments
- Uncertain deduction handling
- Retry limits
- Razorpay live-key blocking
- Simulation fallback
- Recovery execution
- Payment verification
- Full recovery pipeline
- API endpoints
- Metrics
- Audit logging

### Current Test Suite

```text
40 tests
40 passed
```

Run:

```bash
cd backend
python -m pytest tests/ -v
```

---

# Demo Flow

The five-minute demo focuses on three important outcomes:

```text
RECOVERED
    +
ESCALATED
    +
GUARDRAIL-BLOCKED
```

## 1. Introduce the Problem

> Failed payments represent potentially recoverable revenue, but blindly retrying every payment is unsafe.

## 2. Show the Dashboard

Start with:

```text
120 transactions
₹1,62,980 potentially at risk
```

## 3. Run Recovery

Trigger the recovery batch.

## 4. Show the Results

Highlight:

```text
₹51,266 recovered
31.46% recovery rate
34 recovered
19 escalated
7 safely stopped
```

## 5. Show an AI Recommendation

Demonstrate:

```text
Failure Reason
      ↓
AI Diagnosis
      ↓
Recommended Action
```

## 6. Show the Safety Layer

Demonstrate:

```text
AI Recommendation
      ↓
Deterministic Guardrail
      ↓
ALLOW / BLOCK / ESCALATE
```

## 7. Show Verification

Demonstrate:

```text
Execution
    ↓
Verification
    ↓
Recovered Amount
```

## 8. Show Auditability

Show how the transaction's complete decision history is recorded.

### Closing Message

> **The goal is not to retry every failed payment.**
>
> **The goal is to recover the right revenue while knowing exactly when to stop.**

---

# Why This Architecture?

The system intentionally separates **reasoning** from **financial authority**.

```text
┌────────────────────────────┐
│            AI              │
│ Diagnose + Recommend       │
└─────────────┬──────────────┘
              │
              ▼
┌────────────────────────────┐
│     Deterministic Logic    │
│ Strategy + Guardrails      │
└─────────────┬──────────────┘
              │
              ▼
┌────────────────────────────┐
│        Execution           │
│ Test Mode / Simulation     │
└─────────────┬──────────────┘
              │
              ▼
┌────────────────────────────┐
│        Verification        │
└─────────────┬──────────────┘
              │
              ▼
┌────────────────────────────┐
│     Metrics + Audit        │
└────────────────────────────┘
```

This provides:

- AI-assisted decision making
- predictable financial controls
- explicit stopping conditions
- verifiable outcomes
- auditability
- graceful AI failure handling

---

# Limitations

This is a **buildathon prototype**, not a production financial system.

## Synthetic Data

All 120 transactions are generated deterministically.

There is no real merchant, customer, or card behind the dataset.

## Simulated Payment Outcomes

Razorpay Test Mode Orders and Payment Links can be created, but final payment outcomes for synthetic transactions are simulated because no real customer card is used.

A production implementation would use real Razorpay payment events and webhooks.

## Simulated Verification

Uncertain deduction verification is simulated for the synthetic dataset.

A production implementation would query the actual payment state.

## SQLite

SQLite is suitable for this prototype.

A production system would require a concurrency-safe database and stronger transaction/idempotency controls.

## Authentication

The demo API does not currently implement authentication.

A production deployment would require authentication, authorization, rate limiting, and secure secrets management.

---

# Future Improvements

### 1. Real Razorpay Webhooks

Replace simulated payment outcomes with real webhook-driven events such as:

```text
payment.captured
payment.failed
```

### 2. Idempotency

Introduce idempotency keys for recovery attempts to provide stronger protection against duplicate execution.

### 3. Recovery Experiments

Run controlled experiments across different recovery strategies and measure incremental recovery.

### 4. Merchant-Specific Policies

Allow configurable recovery thresholds while keeping the actual safety logic deterministic.

### 5. Scalable Infrastructure

Potential production architecture:

```text
FastAPI
   +
PostgreSQL
   +
Redis / Queue
   +
Background Workers
   +
Observability
```

### 6. Human-in-the-Loop

Route high-value or ambiguous transactions to human review before execution.

### 7. Improved AI Policies

Use historical recovery outcomes to improve recommendations across:

- failure reasons
- payment methods
- transaction amounts
- customer segments
- previous recovery outcomes

---

# Documentation

Additional technical documentation is available in:

### Architecture

[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

Detailed system architecture and production considerations.

### Demo Script

[`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md)

Five-minute walkthrough covering recovered, escalated, and guardrail-blocked transactions.

### Panel Preparation

[`docs/PANEL_PREP.md`](docs/PANEL_PREP.md)

Technical questions and explanations for discussing the system during evaluation.

---

# Buildathon Focus

## Razorpay AI Buildathon 2026

### Track: AI Revenue Recovery

This project focuses on:

| Capability | Implementation |
|---|---|
| Revenue-at-risk detection | Deterministic risk engine |
| Payment diagnosis | Gemini + deterministic fallback |
| Recovery decisions | Strategy layer |
| Financial safety | Deterministic guardrails |
| Payment execution | Razorpay Test Mode / simulation |
| Outcome verification | Payment verifier |
| Revenue measurement | Live database metrics |
| Traceability | Audit trail |

---

# Key Takeaway

```text
        🤖 AI
         │
         │ Diagnose
         │ Recommend
         ▼
   🛡️ Guardrails
         │
         │ Allow / Block
         ▼
      ⚡ Execute
         │
         ▼
      ✅ Verify
         │
         ▼
      💰 Recover
         │
         ▼
      📊 Measure
```

> ## **AI for reasoning.**
> ## **Code for safety.**
> ## **Verification for trust.**
> ## **Metrics for accountability.**

---

### Built for the Razorpay AI Revenue Recovery Challenge.
