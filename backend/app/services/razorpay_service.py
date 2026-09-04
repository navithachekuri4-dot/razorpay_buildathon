"""
Razorpay Test Mode service layer.

Single place in the codebase that is allowed to talk to Razorpay. Two
honesty notes that matter for explaining this in a panel:

1. Live keys are hard-blocked. Any key starting with "rzp_live_" is
   rejected at client-construction time — the app physically cannot use
   live mode, even by accident.

2. What is "real" vs "simulated": creating a Razorpay Order or a Payment
   Link is a genuine network call to Razorpay's test environment and
   returns a genuine test-mode id/URL. But because this project's
   transactions are synthetic (there is no real card behind them), the
   actual capture/failure of that order is not something Razorpay can
   tell us — no card was ever entered. So the "did the retry succeed"
   outcome is produced by a *seeded deterministic simulation*, not
   invented from Razorpay's response. execution_mode on every transaction
   records honestly which path was used: "razorpay_test" (a real API
   call happened) or "simulation" (no credentials / API error / the step
   has no real-world equivalent for synthetic data).
"""
import hashlib
from dataclasses import dataclass
from typing import Optional

from app.config import settings

try:
    import razorpay
except ImportError:  # pragma: no cover - dependency always installed via requirements.txt
    razorpay = None


@dataclass
class ExecutionOutcome:
    success: bool
    execution_mode: str  # "razorpay_test" | "simulation"
    reference_id: Optional[str]
    detail: str


class RazorpayService:
    def __init__(self):
        self.client = None
        self.configured = False
        self._init_client()

    def _init_client(self):
        key_id = settings.RAZORPAY_KEY_ID
        key_secret = settings.RAZORPAY_KEY_SECRET

        if not key_id or not key_secret:
            return  # no credentials -> simulation mode, by design

        if key_id.startswith("rzp_live_"):
            # Hard safety block. This must never be bypassable by config.
            raise RuntimeError(
                "Refusing to start: RAZORPAY_KEY_ID begins with 'rzp_live_'. "
                "This project only ever runs in Razorpay Test Mode."
            )

        if razorpay is None:
            return

        try:
            self.client = razorpay.Client(auth=(key_id, key_secret))
            self.configured = True
        except Exception:
            self.client = None
            self.configured = False

    # --- deterministic simulated outcome, seeded per-transaction so the
    # demo is reproducible run to run ---
    @staticmethod
    def _seeded_success(transaction_id: str, salt: str, success_rate: float) -> bool:
        digest = hashlib.sha256(f"{transaction_id}:{salt}".encode()).hexdigest()
        bucket = int(digest[:8], 16) % 1000
        return bucket < int(success_rate * 1000)

    def create_recovery_order(self, *, transaction_id: str, amount: float) -> ExecutionOutcome:
        """Represents a retry attempt: create a test-mode Order for the amount."""
        if self.configured:
            try:
                order = self.client.order.create(
                    {
                        "amount": int(amount * 100),  # paise
                        "currency": "INR",
                        "receipt": f"recovery-{transaction_id}",
                        "notes": {"transaction_id": transaction_id, "purpose": "revenue_recovery_retry"},
                    }
                )
                success = self._seeded_success(transaction_id, "retry", 0.55)
                return ExecutionOutcome(
                    success=success,
                    execution_mode="razorpay_test",
                    reference_id=order.get("id"),
                    detail="Razorpay Test Mode order created; capture outcome simulated "
                           "(no real card is attached to synthetic data).",
                )
            except Exception as exc:
                return ExecutionOutcome(
                    success=self._seeded_success(transaction_id, "retry", 0.55),
                    execution_mode="simulation",
                    reference_id=None,
                    detail=f"Razorpay API error, fell back to simulation: {exc}",
                )

        success = self._seeded_success(transaction_id, "retry", 0.55)
        return ExecutionOutcome(
            success=success,
            execution_mode="simulation",
            reference_id=None,
            detail="No Razorpay credentials configured; simulated retry outcome.",
        )

    def create_payment_link(self, *, transaction_id: str, amount: float, customer_id: str) -> ExecutionOutcome:
        """Represents 'send update-card link': create a real test-mode Payment Link."""
        if self.configured:
            try:
                link = self.client.payment_link.create(
                    {
                        "amount": int(amount * 100),
                        "currency": "INR",
                        "description": f"Update payment method - recovery for {transaction_id}",
                        "notes": {"transaction_id": transaction_id, "customer_id": customer_id},
                    }
                )
                completed = self._seeded_success(transaction_id, "link", 0.35)
                return ExecutionOutcome(
                    success=completed,
                    execution_mode="razorpay_test",
                    reference_id=link.get("id"),
                    detail="Razorpay Test Mode payment link created "
                           f"({link.get('short_url', 'n/a')}); customer completion simulated.",
                )
            except Exception as exc:
                return ExecutionOutcome(
                    success=self._seeded_success(transaction_id, "link", 0.35),
                    execution_mode="simulation",
                    reference_id=None,
                    detail=f"Razorpay API error, fell back to simulation: {exc}",
                )

        completed = self._seeded_success(transaction_id, "link", 0.35)
        return ExecutionOutcome(
            success=completed,
            execution_mode="simulation",
            reference_id=None,
            detail="No Razorpay credentials configured; simulated payment-link completion.",
        )

    def verify_payment_status(self, *, transaction_id: str) -> ExecutionOutcome:
        """
        Represents checking whether an uncertain deduction actually landed.
        Synthetic transactions have no real Razorpay payment_id to fetch, so
        this step is always a deterministic simulation — documented
        honestly rather than faked as a real API call.
        """
        captured = self._seeded_success(transaction_id, "verify", 0.40)
        return ExecutionOutcome(
            success=captured,
            execution_mode="simulation",
            reference_id=None,
            detail=(
                "Verification simulated: synthetic transactions have no real Razorpay "
                "payment_id to query. In production this calls client.payment.fetch(id)."
            ),
        )


razorpay_service = RazorpayService()
