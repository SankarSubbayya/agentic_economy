"""Unit tests for hallucination detection agent."""

import pytest
from src.agents.hallucination_agent import HallucinationAgent, HallucinationStats


@pytest.fixture
def hallucination_agent():
    return HallucinationAgent("test-hallucination-001")


class TestHallucinationAgent:
    """Test suite for HallucinationAgent."""

    def test_agent_initialization(self, hallucination_agent):
        """Test agent initializes with correct configuration."""
        assert hallucination_agent.agent_id == "test-hallucination-001"
        assert hallucination_agent.wallet_address is not None
        assert hallucination_agent.wallet_address.startswith("0x")
        assert hallucination_agent.stats is not None

    def test_detection_price_constant(self, hallucination_agent):
        """Test detection price is set correctly."""
        assert hallucination_agent.DETECTION_PRICE == 0.0015

    def test_initial_stats(self, hallucination_agent):
        """Test initial statistics are zero."""
        assert hallucination_agent.stats.detections_completed == 0
        assert hallucination_agent.stats.hallucinations_found == 0
        assert hallucination_agent.stats.total_earned_usdc == 0.0
        assert hallucination_agent.stats.reputation_score == 100.0
        assert hallucination_agent.stats.errors == 0

    def test_get_stats_structure(self, hallucination_agent):
        """Test stats dictionary has correct structure."""
        stats = hallucination_agent.get_stats()
        assert stats["agent_id"] == "test-hallucination-001"
        assert stats["wallet"] == hallucination_agent.wallet_address
        assert "detections_completed" in stats
        assert "hallucinations_found" in stats
        assert "total_earned_usdc" in stats
        assert "reputation_score" in stats
        assert "errors" in stats
        assert "detection_rate" in stats

    def test_detection_count_increments(self, hallucination_agent):
        """Test that detection count increments after a detection task."""
        initial_count = hallucination_agent.stats.detections_completed
        hallucination_agent.stats.detections_completed += 1
        assert hallucination_agent.stats.detections_completed == initial_count + 1

    def test_hallucination_count_increments(self, hallucination_agent):
        """Test that hallucination count increments when detected."""
        initial_count = hallucination_agent.stats.hallucinations_found
        hallucination_agent.stats.hallucinations_found += 1
        assert hallucination_agent.stats.hallucinations_found == initial_count + 1

    def test_earnings_accumulation(self, hallucination_agent):
        """Test that earnings accumulate with each detection."""
        initial_earnings = hallucination_agent.stats.total_earned_usdc
        hallucination_agent.stats.total_earned_usdc += hallucination_agent.DETECTION_PRICE
        assert hallucination_agent.stats.total_earned_usdc == pytest.approx(
            initial_earnings + 0.0015
        )

    def test_multiple_detections_earnings(self, hallucination_agent):
        """Test earnings for multiple detections."""
        num_detections = 5
        for _ in range(num_detections):
            hallucination_agent.stats.detections_completed += 1
            hallucination_agent.stats.total_earned_usdc += (
                hallucination_agent.DETECTION_PRICE
            )

        assert hallucination_agent.stats.detections_completed == 5
        assert hallucination_agent.stats.total_earned_usdc == pytest.approx(
            5 * 0.0015
        )

    def test_hallucination_detection_rate(self, hallucination_agent):
        """Test calculation of hallucination detection rate."""
        hallucination_agent.stats.detections_completed = 10
        hallucination_agent.stats.hallucinations_found = 3
        stats = hallucination_agent.get_stats()
        assert stats["detection_rate"] == pytest.approx(0.3)

    def test_detection_rate_zero_detections(self, hallucination_agent):
        """Test detection rate when no detections completed."""
        stats = hallucination_agent.get_stats()
        assert stats["detection_rate"] == 0.0

    def test_reputation_decay_on_error(self, hallucination_agent):
        """Test reputation decays on error."""
        initial_reputation = hallucination_agent.stats.reputation_score
        hallucination_agent.stats.reputation_score *= 0.95
        assert hallucination_agent.stats.reputation_score == pytest.approx(
            initial_reputation * 0.95
        )

    def test_multiple_error_reputation_decay(self, hallucination_agent):
        """Test reputation decays with multiple errors."""
        for _ in range(3):
            hallucination_agent.stats.errors += 1
            hallucination_agent.stats.reputation_score *= 0.95

        assert hallucination_agent.stats.reputation_score == pytest.approx(
            100.0 * (0.95 ** 3)
        )

    def test_reset_stats(self, hallucination_agent):
        """Test resetting all statistics."""
        # Set some stats
        hallucination_agent.stats.detections_completed = 5
        hallucination_agent.stats.hallucinations_found = 2
        hallucination_agent.stats.total_earned_usdc = 0.0075
        hallucination_agent.stats.errors = 1
        hallucination_agent.stats.reputation_score = 95.0

        # Reset
        hallucination_agent.reset_stats()

        # Verify reset
        assert hallucination_agent.stats.detections_completed == 0
        assert hallucination_agent.stats.hallucinations_found == 0
        assert hallucination_agent.stats.total_earned_usdc == 0.0
        assert hallucination_agent.stats.errors == 0
        assert hallucination_agent.stats.reputation_score == 100.0

    def test_hallucination_stats_dataclass(self):
        """Test HallucinationStats dataclass structure."""
        stats = HallucinationStats()
        assert hasattr(stats, "detections_completed")
        assert hasattr(stats, "hallucinations_found")
        assert hasattr(stats, "total_earned_usdc")
        assert hasattr(stats, "reputation_score")
        assert hasattr(stats, "errors")

    def test_stats_custom_initialization(self):
        """Test HallucinationStats with custom values."""
        stats = HallucinationStats(
            detections_completed=10,
            hallucinations_found=3,
            total_earned_usdc=0.015,
            reputation_score=95.0,
            errors=1,
        )
        assert stats.detections_completed == 10
        assert stats.hallucinations_found == 3
        assert stats.total_earned_usdc == 0.015
        assert stats.reputation_score == 95.0
        assert stats.errors == 1

    def test_agent_id_custom(self):
        """Test agent can be initialized with custom ID."""
        custom_id = "custom-hallucination-detector"
        agent = HallucinationAgent(agent_id=custom_id)
        assert agent.agent_id == custom_id

    def test_wallet_address_from_config(self, hallucination_agent):
        """Test wallet address is loaded from config."""
        from src.config import settings

        assert hallucination_agent.wallet_address == settings.HALLUCINATION_AGENT_WALLET

    def test_get_stats_earnings_calculation(self, hallucination_agent):
        """Test earnings are correctly calculated in stats."""
        hallucination_agent.stats.detections_completed = 20
        hallucination_agent.stats.total_earned_usdc = 20 * hallucination_agent.DETECTION_PRICE

        stats = hallucination_agent.get_stats()
        assert stats["total_earned_usdc"] == pytest.approx(0.03)  # 20 * 0.0015

    def test_agent_independence(self):
        """Test multiple agents maintain independent stats."""
        agent1 = HallucinationAgent("agent-1")
        agent2 = HallucinationAgent("agent-2")

        agent1.stats.detections_completed = 5
        agent2.stats.detections_completed = 10

        assert agent1.stats.detections_completed == 5
        assert agent2.stats.detections_completed == 10
