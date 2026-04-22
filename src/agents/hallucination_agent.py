"""Autonomous Hallucination Detection Agent for AI-generated content verification."""

import google.generativeai as genai
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

from src.config import settings
from src.types import EvaluationResult


@dataclass
class HallucinationStats:
    """Statistics for hallucination detection agent."""

    detections_completed: int = 0
    hallucinations_found: int = 0
    total_earned_usdc: float = 0.0
    reputation_score: float = 100.0
    errors: int = 0


class HallucinationAgent:
    """Autonomous agent for detecting hallucinations in AI-generated text."""

    DETECTION_PRICE = 0.0015  # $0.0015 per hallucination detection

    def __init__(self, agent_id: str = "hallucination-agent-001"):
        """Initialize hallucination detection agent."""
        self.agent_id = agent_id
        self.wallet_address = settings.HALLUCINATION_AGENT_WALLET
        self.stats = HallucinationStats()
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    async def detect_hallucinations(
        self, text: str, context: str = ""
    ) -> Optional[EvaluationResult]:
        """
        Detect hallucinations in generated text using Gemini function calling.

        Args:
            text: The generated text to check for hallucinations
            context: The original context or query the text was generated from

        Returns:
            EvaluationResult with hallucination flag and score, or None on error
        """
        try:
            tools = [
                {
                    "name": "check_factual_accuracy",
                    "description": "Check if claims in the text are factually accurate",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "accurate": {
                                "type": "boolean",
                                "description": "Whether the text contains accurate information",
                            },
                            "suspicious_claims": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of claims that are suspicious or potentially fabricated",
                            },
                        },
                        "required": ["accurate", "suspicious_claims"],
                    },
                },
                {
                    "name": "identify_unsupported_claims",
                    "description": "Identify claims not grounded in the provided context",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "unsupported": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Claims that are not supported by the context",
                            },
                            "confidence": {
                                "type": "number",
                                "description": "Confidence score 0-1 that claims are grounded in context",
                            },
                        },
                        "required": ["unsupported", "confidence"],
                    },
                },
                {
                    "name": "calculate_hallucination_score",
                    "description": "Calculate overall hallucination score for the text",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "score": {
                                "type": "integer",
                                "description": "Score 0-100, where 100 means no hallucinations detected",
                            },
                            "hallucinating": {
                                "type": "boolean",
                                "description": "Whether the text contains hallucinations",
                            },
                        },
                        "required": ["score", "hallucinating"],
                    },
                },
            ]

            prompt = f"""Analyze the following generated text for hallucinations and factual accuracy.

Original Context/Query: {context if context else "(No context provided)"}

Generated Text: {text}

Use the provided tools to:
1. Check factual accuracy
2. Identify claims not grounded in the context
3. Calculate overall hallucination score

A hallucination is detected if:
- There are 2 or more unsupported claims, OR
- Confidence in context-grounding is < 0.5, OR
- Any suspicious claims are found

Score: 100 = no hallucinations, 50 = moderate hallucinations, 0 = severe hallucinations"""

            response = self.model.generate_content(
                prompt,
                tools=tools,
                tool_config={"function_calling_config": "ANY"},
            )

            accuracy_result = {"accurate": True, "suspicious_claims": []}
            unsupported_result = {"unsupported": [], "confidence": 1.0}
            score_result = {"score": 85, "hallucinating": False}

            if response.tool_calls:
                for tool_call in response.tool_calls:
                    if tool_call.function_name == "check_factual_accuracy":
                        accuracy_result = dict(tool_call.args)
                    elif tool_call.function_name == "identify_unsupported_claims":
                        unsupported_result = dict(tool_call.args)
                    elif tool_call.function_name == "calculate_hallucination_score":
                        score_result = dict(tool_call.args)

            hallucinating = (
                len(unsupported_result.get("unsupported", [])) >= 2
                or unsupported_result.get("confidence", 1.0) < 0.5
                or len(accuracy_result.get("suspicious_claims", [])) > 0
            )

            if hallucinating:
                score = max(0, min(50, score_result.get("score", 25)))
            else:
                score = max(70, score_result.get("score", 85))

            reasoning = f"Suspicious claims: {len(accuracy_result.get('suspicious_claims', []))}, "
            reasoning += f"Unsupported claims: {len(unsupported_result.get('unsupported', []))}, "
            reasoning += f"Context confidence: {unsupported_result.get('confidence', 1.0):.2f}"

            result = EvaluationResult(
                score=score,
                relevant=True,
                hallucinating=hallucinating,
                on_topic=True,
                reasoning=reasoning,
            )

            self.stats.detections_completed += 1
            if hallucinating:
                self.stats.hallucinations_found += 1
            self.stats.total_earned_usdc += self.DETECTION_PRICE

            return result

        except Exception as e:
            self.stats.errors += 1
            self.stats.reputation_score *= 0.95

            return EvaluationResult(
                score=50,
                relevant=True,
                hallucinating=False,
                on_topic=True,
                reasoning=f"Detection error: {str(e)}",
            )

    def get_stats(self) -> dict:
        """Get agent statistics."""
        return {
            "agent_id": self.agent_id,
            "wallet": self.wallet_address,
            "detections_completed": self.stats.detections_completed,
            "hallucinations_found": self.stats.hallucinations_found,
            "total_earned_usdc": self.stats.total_earned_usdc,
            "reputation_score": self.stats.reputation_score,
            "errors": self.stats.errors,
            "detection_rate": (
                self.stats.hallucinations_found / self.stats.detections_completed
                if self.stats.detections_completed > 0
                else 0.0
            ),
        }

    def reset_stats(self) -> None:
        """Reset agent statistics."""
        self.stats = HallucinationStats()
