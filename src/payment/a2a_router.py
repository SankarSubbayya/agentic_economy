from dataclasses import dataclass, field
from typing import Dict, Optional, List
from datetime import datetime


@dataclass
class Payment:
    """Agent-to-agent payment record."""

    payment_id: str
    from_agent: str
    to_agent: str
    amount_usdc: float
    reason: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    status: str = "pending"  # pending, completed, failed


@dataclass
class AgentAccount:
    """Agent account with balance and transaction history."""

    agent_id: str
    wallet_address: str
    balance_usdc: float = 0.0
    payments_sent: List[Payment] = field(default_factory=list)
    payments_received: List[Payment] = field(default_factory=list)

    def add_earnings(self, amount: float, reason: str = "task_completion"):
        """Add earnings to agent account."""
        self.balance_usdc += amount

    def deduct_payment(self, payment: Payment) -> bool:
        """Deduct payment from balance if sufficient funds."""
        if self.balance_usdc >= payment.amount_usdc:
            self.balance_usdc -= payment.amount_usdc
            self.payments_sent.append(payment)
            return True
        return False

    def receive_payment(self, payment: Payment):
        """Receive payment into account."""
        self.balance_usdc += payment.amount_usdc
        self.payments_received.append(payment)

    def get_balance(self) -> float:
        return self.balance_usdc

    def get_stats(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "wallet": self.wallet_address,
            "balance_usdc": round(self.balance_usdc, 4),
            "total_sent": round(sum(p.amount_usdc for p in self.payments_sent), 4),
            "total_received": round(sum(p.amount_usdc for p in self.payments_received), 4),
            "payment_count": len(self.payments_sent) + len(self.payments_received),
        }


class A2ARouter:
    """Routes autonomous agent-to-agent payments."""

    def __init__(self):
        self.accounts: Dict[str, AgentAccount] = {}
        self.all_payments: List[Payment] = []

    def register_agent(self, agent_id: str, wallet_address: str, initial_balance: float = 0.0):
        """Register agent with account."""
        self.accounts[agent_id] = AgentAccount(
            agent_id=agent_id, wallet_address=wallet_address, balance_usdc=initial_balance
        )

    def authorize_payment(self, from_agent: str, to_agent: str, amount: float, reason: str) -> bool:
        """Authorize and execute A2A payment."""
        if from_agent not in self.accounts or to_agent not in self.accounts:
            return False

        payment = Payment(
            payment_id=f"p_{len(self.all_payments) + 1:06d}",
            from_agent=from_agent,
            to_agent=to_agent,
            amount_usdc=amount,
            reason=reason,
        )

        # Check if sender has sufficient balance
        if not self.accounts[from_agent].deduct_payment(payment):
            payment.status = "failed"
            self.all_payments.append(payment)
            return False

        # Receive payment
        self.accounts[to_agent].receive_payment(payment)
        payment.status = "completed"
        self.all_payments.append(payment)
        return True

    def fund_agent(self, agent_id: str, amount: float, reason: str = "initial_funding"):
        """Fund agent account from external source."""
        if agent_id in self.accounts:
            self.accounts[agent_id].add_earnings(amount, reason)
            return True
        return False

    def get_agent_balance(self, agent_id: str) -> Optional[float]:
        """Get agent current balance."""
        return self.accounts.get(agent_id, AgentAccount("", "")).get_balance()

    def get_agent_stats(self, agent_id: str) -> Optional[dict]:
        """Get agent account statistics."""
        if agent_id in self.accounts:
            return self.accounts[agent_id].get_stats()
        return None

    def get_all_payments(self) -> List[Payment]:
        """Get all payments processed."""
        return self.all_payments

    def get_payment_flow_summary(self) -> dict:
        """Get summary of all A2A payment flows."""
        total_volume = sum(p.amount_usdc for p in self.all_payments if p.status == "completed")
        successful = len([p for p in self.all_payments if p.status == "completed"])
        failed = len([p for p in self.all_payments if p.status == "failed"])

        return {
            "total_volume_usdc": round(total_volume, 4),
            "successful_payments": successful,
            "failed_payments": failed,
            "total_payments": len(self.all_payments),
            "success_rate": round(
                (successful / len(self.all_payments) * 100) if self.all_payments else 0, 2
            ),
        }

    def reset(self):
        """Reset router state."""
        self.accounts.clear()
        self.all_payments.clear()
