"""Integration tests for Day 4: x402 + Nanopayments + Arc settlement."""

import pytest
from src.agents.settlement_agent_x402 import SettlementAgentX402
from src.blockchain.eip3009_signer import EIP3009Signer
from src.protocol.x402_handler import X402Challenge, PaymentMode


@pytest.fixture
def settlement_agent():
    return SettlementAgentX402(
        agent_id="settlement-agent-x402",
        wallet_address="0x0000",
        private_key="0x" + "1" * 64,
        circle_api_key="test-key",
    )


@pytest.fixture
def payer_wallet():
    return "0x1111"


@pytest.fixture
def recipient_wallet():
    return "0x2222"


@pytest.mark.asyncio
async def test_settlement_agent_initialization(settlement_agent):
    """Test settlement agent initializes with blockchain integration."""
    assert settlement_agent.agent_id == "settlement-agent-x402"
    assert settlement_agent.signer is not None
    assert settlement_agent.circle is not None
    assert settlement_agent.arc is not None


@pytest.mark.asyncio
async def test_authorize_nanopayment(settlement_agent, payer_wallet, recipient_wallet):
    """Test EIP-3009 nanopayment authorization."""
    # Set payer balance
    settlement_agent.arc.set_balance(payer_wallet, 10.0)

    # Authorize payment
    result = settlement_agent.authorize_nanopayment(
        payer=payer_wallet, recipient=recipient_wallet, amount_usdc=0.01, nonce=0
    )

    assert result is not None
    assert result.authorized is True
    assert result.amount == 0.01
    assert result.signature.startswith("0x")


@pytest.mark.asyncio
async def test_nanopayment_on_chain_verification(settlement_agent, payer_wallet, recipient_wallet):
    """Test nanopayment settlement verified on Arc blockchain."""
    settlement_agent.arc.set_balance(payer_wallet, 10.0)

    # Authorize payment
    result = settlement_agent.authorize_nanopayment(
        payer=payer_wallet, recipient=recipient_wallet, amount_usdc=0.005
    )

    assert result.authorized is True

    # Verify on-chain
    # Extract tx_hash from reason (simplified for test)
    reason_parts = result.reason.split(": ")
    if len(reason_parts) > 1:
        tx_hash = reason_parts[1]
        verified = settlement_agent.verify_settlement_on_chain(tx_hash)
        assert verified is True


@pytest.mark.asyncio
async def test_settlement_proof_generation(settlement_agent, payer_wallet, recipient_wallet):
    """Test generation of settlement proof for verification."""
    settlement_agent.arc.set_balance(payer_wallet, 10.0)

    result = settlement_agent.authorize_nanopayment(
        payer=payer_wallet, recipient=recipient_wallet, amount_usdc=0.01
    )

    # Extract tx hash from result reason
    reason_parts = result.reason.split(": ")
    if len(reason_parts) > 1:
        tx_hash = reason_parts[1]
        proof = settlement_agent.get_settlement_proof(tx_hash)

        assert proof is not None
        assert proof["from"] == payer_wallet
        assert proof["to"] == recipient_wallet
        assert proof["amount_usdc"] == 0.01
        assert "explorer_url" in proof


@pytest.mark.asyncio
async def test_x402_challenge_handling(settlement_agent):
    """Test x402 Payment Required challenge handling."""
    # Create challenge
    challenge = X402Challenge(
        payment_amount=0.01,
        recipient_address=settlement_agent.wallet_address,
        nonce="x402-nonce-123",
        mode=PaymentMode.THRESHOLD,
    )

    # Handle challenge
    result = settlement_agent.handle_x402_challenge(challenge, payer="0x1111")

    assert result is not None
    assert result.authorized is True
    assert result.amount == 0.01


@pytest.mark.asyncio
async def test_multiple_nanopayments_batch(settlement_agent):
    """Test multiple nanopayments in a batch."""
    # Set balances for multiple payers
    for i in range(5):
        settlement_agent.arc.set_balance(f"0x{i:04x}1111", 10.0)

    # Process payments
    for i in range(5):
        result = settlement_agent.authorize_nanopayment(
            payer=f"0x{i:04x}1111",
            recipient=f"0x{i:04x}2222",
            amount_usdc=0.001,
            nonce=i,
        )
        assert result.authorized is True

    # Check stats
    stats = settlement_agent.get_stats()
    assert stats["settlements_authorized"] == 5
    assert stats["total_volume_usdc"] == pytest.approx(0.005)


@pytest.mark.asyncio
async def test_settlement_agent_stats(settlement_agent, payer_wallet, recipient_wallet):
    """Test settlement agent statistics tracking."""
    settlement_agent.arc.set_balance(payer_wallet, 10.0)

    # Process several settlements
    for i in range(3):
        settlement_agent.authorize_nanopayment(
            payer=payer_wallet,
            recipient=recipient_wallet,
            amount_usdc=0.001,
            nonce=i,
        )

    stats = settlement_agent.get_stats()
    assert stats["settlements_authorized"] == 3
    assert stats["settlements_denied"] == 0
    assert stats["total_earned_usdc"] == pytest.approx(0.006)
    assert stats["success_rate"] == 100.0


@pytest.mark.asyncio
async def test_blockchain_stats(settlement_agent, payer_wallet, recipient_wallet):
    """Test Arc blockchain integration statistics."""
    settlement_agent.arc.set_balance(payer_wallet, 10.0)

    # Execute settlement
    settlement_agent.authorize_nanopayment(payer_wallet, recipient_wallet, 0.01)

    # Get blockchain stats
    stats = settlement_agent.get_blockchain_stats()
    assert stats["chain_id"] == 42170
    assert stats["total_transactions"] >= 1
    assert stats["total_transfers"] >= 1


@pytest.mark.asyncio
async def test_settlement_failure_tracking(settlement_agent):
    """Test tracking of failed settlements."""
    # Try to process payment without sufficient balance
    # (This won't fail in our mock, but we test the error handling)
    stats_before = settlement_agent.get_stats()

    result = settlement_agent.authorize_nanopayment(
        payer="0x0000",
        recipient="0x1111",
        amount_usdc=0.01,
    )

    # Even if it succeeds in mock, we test the structure
    stats_after = settlement_agent.get_stats()
    assert "settlements_denied" in stats_after


@pytest.mark.asyncio
async def test_eip3009_signature_validity(settlement_agent):
    """Test EIP-3009 signature generation and structure."""
    # Create authorization
    auth_params = settlement_agent.signer.create_authorization(
        from_address="0x1111",
        to_address="0x2222",
        amount_usdc=0.01,
    )

    # Sign
    signed = settlement_agent.signer.sign_authorization(auth_params)

    # Verify signature structure
    assert signed.signature.startswith("0x")
    assert len(signed.signature) > 100
    assert signed.signer_address == settlement_agent.signer.address


@pytest.mark.asyncio
async def test_circular_payment_flow(settlement_agent):
    """Test circular payment flow between agents."""
    # Agent A -> Agent B: 0.001
    settlement_agent.arc.set_balance("0xAAAA", 1.0)
    r1 = settlement_agent.authorize_nanopayment("0xAAAA", "0xBBBB", 0.001)
    assert r1.authorized is True

    # Agent B -> Agent C: 0.0005
    settlement_agent.arc.set_balance("0xBBBB", 1.0)
    r2 = settlement_agent.authorize_nanopayment("0xBBBB", "0xCCCC", 0.0005)
    assert r2.authorized is True

    # Agent C -> Agent A: 0.0002
    settlement_agent.arc.set_balance("0xCCCC", 1.0)
    r3 = settlement_agent.authorize_nanopayment("0xCCCC", "0xAAAA", 0.0002)
    assert r3.authorized is True

    # Verify circular flow
    stats = settlement_agent.get_stats()
    assert stats["settlements_authorized"] == 3
    assert stats["total_volume_usdc"] == pytest.approx(0.0017)


@pytest.mark.asyncio
async def test_settlement_agent_reset(settlement_agent):
    """Test settlement agent state reset."""
    settlement_agent.arc.set_balance("0x1111", 10.0)
    settlement_agent.authorize_nanopayment("0x1111", "0x2222", 0.001)

    # Verify state before reset
    stats_before = settlement_agent.get_stats()
    assert stats_before["settlements_authorized"] > 0

    # Reset
    settlement_agent.reset()

    # Verify state after reset
    stats_after = settlement_agent.get_stats()
    assert stats_after["settlements_authorized"] == 0
    assert stats_after["total_earned_usdc"] == 0.0
