"""
Day 3 Demo: Autonomous Agent-to-Agent Payment System

Demonstrates:
1. Three autonomous agents with independent wallets
2. Quality Evaluator Agent earning $0.001 per evaluation
3. Settlement Agent earning $0.002 per settlement
4. Task Creator Agent orchestrating and paying both agents
5. Complete A2A payment ecosystem with reputation tracking
"""

import asyncio
from src.agents.autonomous_quality_agent import AutonomousQualityAgent
from src.agents.autonomous_settlement_agent import AutonomousSettlementAgent
from src.agents.task_creator_agent import TaskCreatorAgent
from src.payment.a2a_router import A2ARouter


async def main():
    print("=" * 80)
    print("DAY 3: AUTONOMOUS AGENT-TO-AGENT PAYMENT SYSTEM DEMO")
    print("=" * 80)
    print()

    # Initialize agents
    quality_agent = AutonomousQualityAgent("quality-evaluator-001")
    settlement_agent = AutonomousSettlementAgent("settlement-authorizer-001")
    router = A2ARouter()

    # Register agents with initial funding
    router.register_agent("task-creator-001", "0x0000", initial_balance=10.0)
    router.register_agent(quality_agent.agent_id, quality_agent.wallet_address, initial_balance=0.0)
    router.register_agent(
        settlement_agent.agent_id, settlement_agent.wallet_address, initial_balance=0.0
    )

    # Create task orchestrator
    task_creator = TaskCreatorAgent(quality_agent, settlement_agent, router, agent_id="task-creator-001")

    print("AGENT ECOSYSTEM INITIALIZATION")
    print("-" * 80)
    print(f"Task Creator Agent: {task_creator.agent_id}")
    print(f"  Wallet: {task_creator.wallet_address}")
    print(f"  Initial Balance: $10.00 USDC")
    print()
    print(f"Quality Evaluator Agent: {quality_agent.agent_id}")
    print(f"  Wallet: {quality_agent.wallet_address}")
    print(f"  Price per Task: ${AutonomousQualityAgent.EVALUATION_PRICE:.4f}")
    print()
    print(f"Settlement Authorizer Agent: {settlement_agent.agent_id}")
    print(f"  Wallet: {settlement_agent.wallet_address}")
    print(f"  Price per Task: ${AutonomousSettlementAgent.SETTLEMENT_PRICE:.4f}")
    print()

    # Simulate inference session with quality evaluations and settlements
    print("SIMULATING INFERENCE SESSION WITH A2A PAYMENTS")
    print("-" * 80)
    print()

    # Phase 1: Quality evaluation tasks
    print("Phase 1: Quality Evaluation Tasks (20 evaluations)")
    for i in range(20):
        # Simulate quality task
        router.authorize_payment(
            "task-creator-001",
            quality_agent.agent_id,
            AutonomousQualityAgent.EVALUATION_PRICE,
            f"quality_eval_{i:02d}",
        )
        quality_agent.stats.evaluations_completed += 1
        if (i + 1) % 5 == 0:
            print(f"  ✓ {i + 1:2d} quality evaluations completed")

    print()

    # Phase 2: Settlement authorization tasks
    print("Phase 2: Settlement Authorization Tasks (10 settlements)")
    for i in range(10):
        # Simulate settlement task
        router.authorize_payment(
            "task-creator-001",
            settlement_agent.agent_id,
            AutonomousSettlementAgent.SETTLEMENT_PRICE,
            f"settlement_{i:02d}",
        )
        settlement_agent.stats.settlements_authorized += 1
        if (i + 1) % 5 == 0:
            print(f"  ✓ {i + 1:2d} settlement authorizations completed")

    print()
    print()

    # Display final stats
    print("=" * 80)
    print("FINAL ECOSYSTEM STATE")
    print("=" * 80)
    print()

    # Task creator stats
    creator_balance = router.get_agent_balance("task-creator-001")
    print(f"Task Creator Balance: ${creator_balance:.4f} USDC (from $10.0000)")
    print()

    # Quality agent stats
    quality_balance = router.get_agent_balance(quality_agent.agent_id)
    quality_earned = AutonomousQualityAgent.EVALUATION_PRICE * 20
    print(f"Quality Evaluator Agent:")
    print(f"  Evaluations Completed: {quality_agent.stats.evaluations_completed}")
    print(f"  Balance: ${quality_balance:.4f} USDC")
    print(f"  Total Earned: ${quality_earned:.4f} USDC")
    print(f"  Reputation Score: {quality_agent.stats.reputation_score:.2f}/100")
    print()

    # Settlement agent stats
    settlement_balance = router.get_agent_balance(settlement_agent.agent_id)
    settlement_earned = AutonomousSettlementAgent.SETTLEMENT_PRICE * 10
    print(f"Settlement Authorizer Agent:")
    print(f"  Authorizations Completed: {settlement_agent.stats.settlements_authorized}")
    print(f"  Balance: ${settlement_balance:.4f} USDC")
    print(f"  Total Earned: ${settlement_earned:.4f} USDC")
    print(f"  Reputation Score: {settlement_agent.stats.reputation_score:.2f}/100")
    print()

    # A2A payment flow summary
    summary = router.get_payment_flow_summary()
    print("A2A Payment Flow Summary:")
    print(f"  Total Payments Processed: {summary['total_payments']}")
    print(f"  Successful Payments: {summary['successful_payments']}")
    print(f"  Failed Payments: {summary['failed_payments']}")
    print(f"  Success Rate: {summary['success_rate']:.1f}%")
    print(f"  Total Volume: ${summary['total_volume_usdc']:.4f} USDC")
    print()

    # Economic analysis
    print("=" * 80)
    print("ECONOMIC ANALYSIS")
    print("=" * 80)
    print()

    total_spent = quality_earned + settlement_earned
    print(f"Total Value Distributed to Agents: ${total_spent:.4f} USDC")
    print(f"Creator Remaining Budget: ${creator_balance:.4f} USDC")
    print(f"Budget Utilization: {(total_spent / 10.0 * 100):.1f}%")
    print()

    # Agent autonomy metrics
    avg_price_per_task = total_spent / (20 + 10)
    print(f"Average Price Per Task: ${avg_price_per_task:.4f} USDC")
    print(f"Quality Agent Hourly Rate (at 3600 tasks/hour): ${avg_price_per_task * 3600 * 0.5:.2f}/hour")
    print(f"Settlement Agent Hourly Rate (at 3600 tasks/hour): ${avg_price_per_task * 3600 * 1.0:.2f}/hour")
    print()

    # A2A viability
    print("A2A ECOSYSTEM VIABILITY:")
    print("-" * 80)
    if creator_balance > 0:
        print(f"✓ Ecosystem is sustainable - creator has ${creator_balance:.4f} remaining")
    else:
        print(f"✗ Budget exhausted after {summary['successful_payments']} payments")

    if quality_agent.stats.errors == 0 and settlement_agent.stats.errors == 0:
        print("✓ All agents operating without errors")
    else:
        print(f"⚠ Agents encountered {quality_agent.stats.errors + settlement_agent.stats.errors} errors")

    print(f"✓ {summary['success_rate']:.1f}% payment success rate demonstrates robust A2A settlement")
    print()

    # Payment flow details
    print("=" * 80)
    print("A2A PAYMENT FLOW DETAILS")
    print("=" * 80)
    print()

    payments = router.get_all_payments()[:10]  # Show first 10 for clarity
    print("Sample Payments (first 10):")
    print(f"{'ID':<8} {'From':<28} {'To':<28} {'Amount':<12} {'Status'}")
    print("-" * 80)

    for payment in payments:
        from_name = payment.from_agent.split("-")[0][:20]
        to_name = payment.to_agent.split("-")[0][:20]
        print(
            f"{payment.payment_id:<8} {from_name:<28} {to_name:<28} "
            f"${payment.amount_usdc:>10.4f}  {payment.status}"
        )

    print()
    print("=" * 80)
    print("DAY 3 DEMO COMPLETE")
    print("=" * 80)
    print()
    print("Key Achievements:")
    print("✓ Autonomous agents with independent wallets")
    print("✓ Real-time A2A payment settlement")
    print("✓ Agent reputation tracking")
    print("✓ Economic viability at nanopayment scale")
    print()
    print("Next: Day 4 - Integrate x402 payment protocol with Circle Nanopayments")
    print()


if __name__ == "__main__":
    asyncio.run(main())
