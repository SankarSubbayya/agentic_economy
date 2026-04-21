from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List


@dataclass
class Token:
    """Individual token from inference stream."""

    index: int
    text: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SessionConfig:
    """Configuration for an inference session."""

    max_tokens: int = 200
    max_budget_usdc: float = 0.05
    quality_threshold: int = 75
    evaluation_interval: int = 10


class SessionStatus(str, Enum):
    """Status of an inference session."""

    ACTIVE = "active"
    COMPLETED = "completed"
    CUTOFF = "cutoff"
    ERROR = "error"


@dataclass
class SessionState:
    """State of an active inference session."""

    session_id: str
    config: SessionConfig
    tokens_generated: int = 0
    tokens_accepted: int = 0
    current_score: float = 100.0
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    total_cost: float = 0.0


@dataclass
class EvaluationResult:
    """Result of quality evaluation."""

    score: int  # 0-100
    relevant: bool
    hallucinating: bool
    on_topic: bool
    reasoning: str = ""


@dataclass
class SettlementResult:
    """Result of settlement authorization."""

    authorized: bool
    amount: float
    signature: str
    reason: str = ""


class AgentAction(str, Enum):
    """Actions an agent can take."""

    CONTINUE = "continue"
    CUTOFF = "cutoff"
    APPROVE = "approve"
    DENY = "deny"
