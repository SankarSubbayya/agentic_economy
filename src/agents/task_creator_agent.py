from typing import Optional
import google.generativeai as genai
from src.config import settings
from src.agents.autonomous_quality_agent import AutonomousQualityAgent
from src.agents.autonomous_settlement_agent import AutonomousSettlementAgent
from src.payment.a2a_router import A2ARouter
from src.types import EvaluationResult, SessionState, AgentAction


class TaskCreatorAgent:
    """Orchestrates quality and settlement agents with autonomous payments."""

    def __init__(
        self,
        quality_agent: AutonomousQualityAgent,
        settlement_agent: AutonomousSettlementAgent,
        router: A2ARouter,
        agent_id: str = "task-creator-001",
    ):
        self.agent_id = agent_id
        self.wallet_address = settings.USER_WALLET
        self.quality_agent = quality_agent
        self.settlement_agent = settlement_agent
        self.router = router
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    async def execute_quality_task(
        self, text: str, original_query: str = "user query"
    ) -> Optional[EvaluationResult]:
        """
        Execute quality evaluation task via quality agent.
        Pay quality agent upon completion.
        """
        evaluation = await self.quality_agent.evaluate_with_function_calling(text, original_query)

        if evaluation:
            # Pay quality agent for work completed
            self.router.authorize_payment(
                from_agent=self.agent_id,
                to_agent=self.quality_agent.agent_id,
                amount=AutonomousQualityAgent.EVALUATION_PRICE,
                reason="quality_evaluation_task",
            )

        return evaluation

    async def execute_settlement_task(
        self, amount_usdc: float, remaining_budget: float, session_state: Optional[SessionState] = None
    ) -> bool:
        """
        Execute settlement authorization task via settlement agent.
        Pay settlement agent upon completion.
        """
        settlement_result = await self.settlement_agent.authorize_settlement(amount_usdc, remaining_budget)

        if settlement_result and settlement_result.authorized:
            # Pay settlement agent for work completed
            self.router.authorize_payment(
                from_agent=self.agent_id,
                to_agent=self.settlement_agent.agent_id,
                amount=AutonomousSettlementAgent.SETTLEMENT_PRICE,
                reason="settlement_authorization_task",
            )
            return True

        return False

    def get_orchestrator_stats(self) -> dict:
        """Get orchestrator statistics including all agents."""
        return {
            "task_creator_id": self.agent_id,
            "wallet": self.wallet_address,
            "quality_agent": self.quality_agent.get_stats(),
            "settlement_agent": self.settlement_agent.get_stats(),
            "payment_flow": self.router.get_payment_flow_summary(),
            "agent_accounts": {
                agent_id: self.router.get_agent_stats(agent_id)
                for agent_id in [self.quality_agent.agent_id, self.settlement_agent.agent_id, self.agent_id]
            },
        }

    def reset(self):
        """Reset all agents and payment router."""
        self.quality_agent.reset_stats()
        self.settlement_agent.reset_stats()
        self.router.reset()
