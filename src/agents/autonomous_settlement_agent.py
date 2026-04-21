from dataclasses import dataclass
from typing import Optional
import google.generativeai as genai
from src.config import settings
from src.types import SettlementResult


@dataclass
class SettlementStats:
    settlements_authorized: int = 0
    settlements_denied: int = 0
    total_volume_usdc: float = 0.0
    total_earned_usdc: float = 0.0
    reputation_score: float = 100.0
    errors: int = 0


class AutonomousSettlementAgent:
    """Settlement authorization agent with independent wallet and earnings."""

    SETTLEMENT_PRICE = 0.002  # $0.002 per settlement authorization

    def __init__(self, agent_id: str = "settlement-agent-001"):
        self.agent_id = agent_id
        self.wallet_address = settings.SETTLEMENT_AGENT_WALLET
        self.stats = SettlementStats()
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    async def authorize_settlement(
        self, amount_usdc: float, remaining_budget: float
    ) -> Optional[SettlementResult]:
        """Autonomously decide whether to authorize settlement."""
        try:
            tools = [
                {
                    "name": "verify_budget",
                    "description": "Verify if payment exceeds remaining budget",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "within_budget": {"type": "boolean"},
                            "available": {"type": "number"},
                            "requested": {"type": "number"},
                        },
                        "required": ["within_budget", "available", "requested"],
                    },
                },
                {
                    "name": "authorize_payment",
                    "description": "Authorize payment with signature",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "authorized": {"type": "boolean"},
                            "signature": {"type": "string"},
                            "reason": {"type": "string"},
                        },
                        "required": ["authorized", "signature", "reason"],
                    },
                },
            ]

            prompt = f"""Autonomously authorize this payment:
            Amount: ${amount_usdc}
            Remaining Budget: ${remaining_budget}

            Use tools to verify budget and authorize payment if valid."""

            response = self.model.generate_content(prompt, tools=tools)

            authorized = remaining_budget >= amount_usdc
            reason = "Settlement authorized" if authorized else "Budget exceeded"

            # Generate mock signature (Day 4: replace with real EIP-3009)
            mock_sig = f"0x{'a' * 130}"

            if authorized:
                self.stats.settlements_authorized += 1
                self.stats.total_volume_usdc += amount_usdc
                self.stats.total_earned_usdc += self.SETTLEMENT_PRICE
            else:
                self.stats.settlements_denied += 1

            return SettlementResult(
                authorized=authorized, amount=amount_usdc, signature=mock_sig, reason=reason
            )

        except Exception as e:
            self.stats.errors += 1
            self.stats.reputation_score *= 0.95
            return SettlementResult(
                authorized=False,
                amount=0.0,
                signature="",
                reason=f"Settlement error: {str(e)}",
            )

    def get_stats(self) -> dict:
        """Return agent statistics."""
        return {
            "agent_id": self.agent_id,
            "wallet": self.wallet_address,
            "settlements_authorized": self.stats.settlements_authorized,
            "settlements_denied": self.stats.settlements_denied,
            "total_volume_usdc": round(self.stats.total_volume_usdc, 4),
            "total_earned_usdc": round(self.stats.total_earned_usdc, 4),
            "reputation_score": round(self.stats.reputation_score, 2),
            "errors": self.stats.errors,
        }

    def reset_stats(self):
        """Reset agent statistics."""
        self.stats = SettlementStats()
