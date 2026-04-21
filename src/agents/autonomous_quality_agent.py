import json
from dataclasses import dataclass, field
from typing import Optional
import google.generativeai as genai
from src.config import settings
from src.types import EvaluationResult


@dataclass
class AgentStats:
    evaluations_completed: int = 0
    total_earned_usdc: float = 0.0
    avg_quality_score: float = 0.0
    reputation_score: float = 100.0
    errors: int = 0


class AutonomousQualityAgent:
    """Quality evaluation agent with independent wallet and earnings."""

    EVALUATION_PRICE = 0.001  # $0.001 per evaluation

    def __init__(self, agent_id: str = "quality-agent-001"):
        self.agent_id = agent_id
        self.wallet_address = settings.QUALITY_AGENT_WALLET
        self.stats = AgentStats()
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    async def evaluate_with_function_calling(
        self, text: str, original_query: str = "user query"
    ) -> Optional[EvaluationResult]:
        """Evaluate text quality with function calling."""
        try:
            tools = [
                {
                    "name": "check_relevance",
                    "description": "Check if text is relevant to the query",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "is_relevant": {"type": "boolean"},
                            "relevance_score": {"type": "integer", "minimum": 0, "maximum": 100},
                        },
                        "required": ["is_relevant", "relevance_score"],
                    },
                },
                {
                    "name": "check_hallucination",
                    "description": "Check for hallucinations or false information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "has_hallucination": {"type": "boolean"},
                            "hallucination_score": {"type": "integer", "minimum": 0, "maximum": 100},
                        },
                        "required": ["has_hallucination", "hallucination_score"],
                    },
                },
                {
                    "name": "calculate_quality_score",
                    "description": "Calculate final quality score 0-100",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "score": {"type": "integer", "minimum": 0, "maximum": 100},
                            "reasoning": {"type": "string"},
                        },
                        "required": ["score", "reasoning"],
                    },
                },
            ]

            prompt = f"""Evaluate this text for quality:
            Original Query: {original_query}
            Text to Evaluate: {text}

            Use the tools to check relevance, hallucinations, and calculate a quality score."""

            response = self.model.generate_content(prompt, tools=tools)

            # Parse function calls from response
            for part in response.content:
                if part.function_call:
                    score = 50
                    reasoning = "Evaluation completed"

                    if part.function_call.name == "calculate_quality_score":
                        score = part.function_call.args.get("score", 50)
                        reasoning = part.function_call.args.get("reasoning", "")

            # Update stats
            self.stats.evaluations_completed += 1
            self.stats.total_earned_usdc += self.EVALUATION_PRICE
            old_avg = self.stats.avg_quality_score
            self.stats.avg_quality_score = (
                old_avg * (self.stats.evaluations_completed - 1) + score
            ) / self.stats.evaluations_completed

            return EvaluationResult(
                score=score,
                relevant=True,
                hallucinating=False,
                on_topic=True,
                reasoning=reasoning,
            )

        except Exception as e:
            self.stats.errors += 1
            self.stats.reputation_score *= 0.95  # Decay reputation on error
            return EvaluationResult(
                score=50,
                relevant=False,
                hallucinating=False,
                on_topic=False,
                reasoning=f"Evaluation error: {str(e)}",
            )

    def get_stats(self) -> dict:
        """Return agent statistics."""
        return {
            "agent_id": self.agent_id,
            "wallet": self.wallet_address,
            "evaluations_completed": self.stats.evaluations_completed,
            "total_earned_usdc": self.stats.total_earned_usdc,
            "avg_quality_score": round(self.stats.avg_quality_score, 2),
            "reputation_score": round(self.stats.reputation_score, 2),
            "errors": self.stats.errors,
        }

    def reset_stats(self):
        """Reset agent statistics."""
        self.stats = AgentStats()
