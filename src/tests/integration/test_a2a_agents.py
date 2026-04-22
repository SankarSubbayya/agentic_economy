import pytest
from src.agents.autonomous_quality_agent import AutonomousQualityAgent
from src.agents.autonomous_settlement_agent import AutonomousSettlementAgent
from src.agents.hallucination_agent import HallucinationAgent
from src.agents.task_creator_agent import TaskCreatorAgent
from src.payment.a2a_router import A2ARouter


@pytest.fixture
def quality_agent():
    return AutonomousQualityAgent("test-quality-agent")


@pytest.fixture
def settlement_agent():
    return AutonomousSettlementAgent("test-settlement-agent")


@pytest.fixture
def hallucination_agent():
    return HallucinationAgent("test-hallucination-agent")


@pytest.fixture
def a2a_router():
    router = A2ARouter()
    # Initialize with task creator as primary agent
    router.register_agent("task-creator-001", "0x0000", initial_balance=10.0)
    router.register_agent("test-quality-agent", "0x1111", initial_balance=0.0)
    router.register_agent("test-settlement-agent", "0x2222", initial_balance=0.0)
    router.register_agent("test-hallucination-agent", "0x3333", initial_balance=0.0)
    return router


@pytest.fixture
def task_creator(quality_agent, settlement_agent, hallucination_agent, a2a_router):
    return TaskCreatorAgent(
        quality_agent,
        settlement_agent,
        hallucination_agent,
        a2a_router,
        agent_id="task-creator-001",
    )


@pytest.mark.asyncio
async def test_task_creator_initialization(task_creator):
    """Test task creator agent initializes properly."""
    assert task_creator.agent_id == "task-creator-001"
    assert task_creator.quality_agent is not None
    assert task_creator.settlement_agent is not None
    assert task_creator.hallucination_agent is not None
    assert task_creator.router is not None


@pytest.mark.asyncio
async def test_quality_task_payment(task_creator, a2a_router):
    """Test quality agent is paid after task execution."""
    initial_balance = a2a_router.get_agent_balance("test-quality-agent")
    # Mock evaluation result by setting stats directly (avoids actual API calls in test)
    task_creator.quality_agent.stats.evaluations_completed = 1

    # Simulate task payment
    a2a_router.authorize_payment(
        "task-creator-001", "test-quality-agent", 0.001, "quality_evaluation_task"
    )

    final_balance = a2a_router.get_agent_balance("test-quality-agent")
    assert final_balance == initial_balance + 0.001


@pytest.mark.asyncio
async def test_settlement_task_payment(task_creator, a2a_router):
    """Test settlement agent is paid after task execution."""
    initial_balance = a2a_router.get_agent_balance("test-settlement-agent")

    # Simulate task payment
    a2a_router.authorize_payment(
        "task-creator-001", "test-settlement-agent", 0.002, "settlement_authorization_task"
    )

    final_balance = a2a_router.get_agent_balance("test-settlement-agent")
    assert final_balance == initial_balance + 0.002


@pytest.mark.asyncio
async def test_agent_payment_flow(task_creator, a2a_router):
    """Test complete A2A payment flow with multiple tasks."""
    creator_initial = a2a_router.get_agent_balance("task-creator-001")
    quality_initial = a2a_router.get_agent_balance("test-quality-agent")
    settlement_initial = a2a_router.get_agent_balance("test-settlement-agent")

    # Quality tasks
    a2a_router.authorize_payment("task-creator-001", "test-quality-agent", 0.001, "task1")
    a2a_router.authorize_payment("task-creator-001", "test-quality-agent", 0.001, "task2")

    # Settlement tasks
    a2a_router.authorize_payment("task-creator-001", "test-settlement-agent", 0.002, "task1")
    a2a_router.authorize_payment("task-creator-001", "test-settlement-agent", 0.002, "task2")

    # Verify balances
    assert a2a_router.get_agent_balance("task-creator-001") == creator_initial - 0.006
    assert a2a_router.get_agent_balance("test-quality-agent") == quality_initial + 0.002
    assert a2a_router.get_agent_balance("test-settlement-agent") == settlement_initial + 0.004


@pytest.mark.asyncio
async def test_orchestrator_stats(task_creator, a2a_router):
    """Test orchestrator collects stats from all agents."""
    # Execute some payments
    a2a_router.authorize_payment("task-creator-001", "test-quality-agent", 0.001, "test")
    a2a_router.authorize_payment("task-creator-001", "test-settlement-agent", 0.002, "test")

    stats = task_creator.get_orchestrator_stats()

    assert "task_creator_id" in stats
    assert "quality_agent" in stats
    assert "settlement_agent" in stats
    assert "hallucination_agent" in stats
    assert "payment_flow" in stats
    assert "agent_accounts" in stats

    # Verify payment flow summary
    assert stats["payment_flow"]["successful_payments"] == 2
    assert stats["payment_flow"]["total_volume_usdc"] == pytest.approx(0.003)


@pytest.mark.asyncio
async def test_insufficient_funds_prevents_payment(a2a_router):
    """Test that payments fail when creator runs out of funds."""
    # Drain creator account
    a2a_router.authorize_payment("task-creator-001", "test-quality-agent", 10.0, "drain")

    # Try to pay more
    result = a2a_router.authorize_payment(
        "task-creator-001", "test-settlement-agent", 0.001, "should_fail"
    )
    assert result is False


@pytest.mark.asyncio
async def test_a2a_ecosystem_simulation(task_creator, a2a_router):
    """Simulate realistic A2A payment ecosystem."""
    # 10 quality evaluations
    for i in range(10):
        a2a_router.authorize_payment(
            "task-creator-001",
            "test-quality-agent",
            0.001,
            f"quality_eval_{i}",
        )

    # 5 settlement authorizations
    for i in range(5):
        a2a_router.authorize_payment(
            "task-creator-001",
            "test-settlement-agent",
            0.002,
            f"settlement_{i}",
        )

    # Verify final state
    summary = a2a_router.get_payment_flow_summary()
    assert summary["successful_payments"] == 15
    assert summary["total_volume_usdc"] == pytest.approx(0.020)

    quality_stats = a2a_router.get_agent_stats("test-quality-agent")
    settlement_stats = a2a_router.get_agent_stats("test-settlement-agent")

    assert quality_stats["balance_usdc"] == pytest.approx(0.010)
    assert settlement_stats["balance_usdc"] == pytest.approx(0.010)


@pytest.mark.asyncio
async def test_task_creator_reset(task_creator, a2a_router):
    """Test that reset clears all state."""
    # Create some payments
    a2a_router.authorize_payment("task-creator-001", "test-quality-agent", 0.001, "test")
    a2a_router.authorize_payment("task-creator-001", "test-settlement-agent", 0.002, "test")

    assert len(a2a_router.get_all_payments()) == 2

    # Reset
    task_creator.reset()

    # Verify state is cleared
    assert len(a2a_router.get_all_payments()) == 0
    assert a2a_router.get_agent_balance("test-quality-agent") == 0.0
    assert a2a_router.get_agent_balance("test-settlement-agent") == 0.0
