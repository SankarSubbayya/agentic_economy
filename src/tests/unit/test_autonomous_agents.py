import pytest
from src.agents.autonomous_quality_agent import AutonomousQualityAgent, AgentStats
from src.agents.autonomous_settlement_agent import AutonomousSettlementAgent, SettlementStats
from src.payment.a2a_router import A2ARouter, Payment, AgentAccount


class TestAutonomousQualityAgent:
    """Test autonomous quality agent functionality."""

    @pytest.fixture
    def quality_agent(self):
        return AutonomousQualityAgent("test-quality-001")

    def test_agent_initialization(self, quality_agent):
        assert quality_agent.agent_id == "test-quality-001"
        assert quality_agent.wallet_address is not None
        assert quality_agent.EVALUATION_PRICE == 0.001

    def test_initial_stats(self, quality_agent):
        stats = quality_agent.get_stats()
        assert stats["evaluations_completed"] == 0
        assert stats["total_earned_usdc"] == 0.0
        assert stats["avg_quality_score"] == 0.0
        assert stats["reputation_score"] == 100.0
        assert stats["errors"] == 0

    def test_stats_reset(self, quality_agent):
        quality_agent.stats.evaluations_completed = 10
        quality_agent.stats.total_earned_usdc = 0.01
        quality_agent.reset_stats()
        assert quality_agent.stats.evaluations_completed == 0
        assert quality_agent.stats.total_earned_usdc == 0.0

    def test_agent_reputation_decay_on_error(self, quality_agent):
        initial_reputation = quality_agent.stats.reputation_score
        quality_agent.stats.errors = 5
        quality_agent.stats.reputation_score *= (0.95 ** 5)
        final_reputation = quality_agent.stats.reputation_score
        assert final_reputation < initial_reputation

    def test_agent_stats_contain_wallet(self, quality_agent):
        stats = quality_agent.get_stats()
        assert "wallet" in stats
        assert stats["wallet"] == quality_agent.wallet_address


class TestAutonomousSettlementAgent:
    """Test autonomous settlement agent functionality."""

    @pytest.fixture
    def settlement_agent(self):
        return AutonomousSettlementAgent("test-settlement-001")

    def test_agent_initialization(self, settlement_agent):
        assert settlement_agent.agent_id == "test-settlement-001"
        assert settlement_agent.wallet_address is not None
        assert settlement_agent.SETTLEMENT_PRICE == 0.002

    def test_initial_stats(self, settlement_agent):
        stats = settlement_agent.get_stats()
        assert stats["settlements_authorized"] == 0
        assert stats["settlements_denied"] == 0
        assert stats["total_volume_usdc"] == 0.0
        assert stats["total_earned_usdc"] == 0.0
        assert stats["reputation_score"] == 100.0

    def test_stats_reset(self, settlement_agent):
        settlement_agent.stats.settlements_authorized = 5
        settlement_agent.stats.total_volume_usdc = 0.05
        settlement_agent.reset_stats()
        assert settlement_agent.stats.settlements_authorized == 0
        assert settlement_agent.stats.total_volume_usdc == 0.0

    def test_settlement_stats_contain_wallet(self, settlement_agent):
        stats = settlement_agent.get_stats()
        assert "wallet" in stats
        assert stats["wallet"] == settlement_agent.wallet_address


class TestAgentAccount:
    """Test agent account management."""

    @pytest.fixture
    def account(self):
        return AgentAccount(agent_id="agent-001", wallet_address="0xABC123", balance_usdc=1.0)

    def test_account_initialization(self, account):
        assert account.agent_id == "agent-001"
        assert account.wallet_address == "0xABC123"
        assert account.balance_usdc == 1.0

    def test_add_earnings(self, account):
        account.add_earnings(0.5)
        assert account.balance_usdc == 1.5

    def test_deduct_payment_success(self, account):
        payment = Payment(
            payment_id="p_001", from_agent="agent-001", to_agent="agent-002", amount_usdc=0.3, reason="test"
        )
        result = account.deduct_payment(payment)
        assert result is True
        assert account.balance_usdc == 0.7

    def test_deduct_payment_insufficient_funds(self, account):
        payment = Payment(
            payment_id="p_001", from_agent="agent-001", to_agent="agent-002", amount_usdc=1.5, reason="test"
        )
        result = account.deduct_payment(payment)
        assert result is False
        assert account.balance_usdc == 1.0

    def test_receive_payment(self, account):
        payment = Payment(
            payment_id="p_001", from_agent="agent-002", to_agent="agent-001", amount_usdc=0.5, reason="test"
        )
        account.receive_payment(payment)
        assert account.balance_usdc == 1.5

    def test_get_stats(self, account):
        account.add_earnings(0.5)
        stats = account.get_stats()
        assert stats["agent_id"] == "agent-001"
        assert stats["balance_usdc"] == 1.5


class TestA2ARouter:
    """Test A2A payment router."""

    @pytest.fixture
    def router(self):
        r = A2ARouter()
        r.register_agent("agent-001", "0x1111", initial_balance=1.0)
        r.register_agent("agent-002", "0x2222", initial_balance=0.5)
        r.register_agent("agent-003", "0x3333", initial_balance=0.0)
        return r

    def test_router_initialization(self, router):
        assert len(router.accounts) == 3
        assert router.get_agent_balance("agent-001") == 1.0

    def test_successful_payment(self, router):
        result = router.authorize_payment("agent-001", "agent-002", 0.2, "test payment")
        assert result is True
        assert router.get_agent_balance("agent-001") == 0.8
        assert router.get_agent_balance("agent-002") == 0.7

    def test_payment_exceeds_balance(self, router):
        result = router.authorize_payment("agent-002", "agent-001", 1.0, "test payment")
        assert result is False
        assert router.get_agent_balance("agent-002") == 0.5

    def test_payment_creates_record(self, router):
        router.authorize_payment("agent-001", "agent-002", 0.1, "test")
        payments = router.get_all_payments()
        assert len(payments) == 1
        assert payments[0].from_agent == "agent-001"
        assert payments[0].to_agent == "agent-002"
        assert payments[0].amount_usdc == 0.1

    def test_fund_agent(self, router):
        router.fund_agent("agent-003", 1.0)
        assert router.get_agent_balance("agent-003") == 1.0

    def test_payment_flow_summary(self, router):
        router.authorize_payment("agent-001", "agent-002", 0.1, "test1")
        router.authorize_payment("agent-001", "agent-003", 0.2, "test2")
        router.authorize_payment("agent-002", "agent-001", 0.5, "test3")

        summary = router.get_payment_flow_summary()
        assert summary["total_payments"] == 3
        assert summary["successful_payments"] == 3
        assert summary["total_volume_usdc"] == pytest.approx(0.8)

    def test_payment_with_invalid_agent(self, router):
        result = router.authorize_payment("agent-999", "agent-001", 0.1, "test")
        assert result is False

    def test_get_agent_stats(self, router):
        stats = router.get_agent_stats("agent-001")
        assert stats["agent_id"] == "agent-001"
        assert stats["balance_usdc"] == 1.0

    def test_router_reset(self, router):
        router.authorize_payment("agent-001", "agent-002", 0.1, "test")
        router.reset()
        assert len(router.accounts) == 0
        assert len(router.all_payments) == 0

    def test_multiple_payments_flow(self, router):
        # Simulate quality agent getting paid for work
        router.authorize_payment("agent-001", "agent-002", 0.001, "quality_task")
        # Simulate settlement agent getting paid
        router.authorize_payment("agent-001", "agent-003", 0.002, "settlement_task")
        # Agents do more work
        router.authorize_payment("agent-001", "agent-002", 0.001, "quality_task")

        summary = router.get_payment_flow_summary()
        assert summary["successful_payments"] == 3
        assert summary["total_volume_usdc"] == pytest.approx(0.004)
