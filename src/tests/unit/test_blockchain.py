"""Unit tests for blockchain integration components."""

import pytest
from src.blockchain.eip3009_signer import EIP3009Signer, AuthorizationParams
from src.blockchain.circle_nanopayments import CircleNanopayments, NanopaymentTx, TransactionStatus
from src.blockchain.arc_testnet import ArcTestnet
from src.protocol.x402_handler import (
    X402Server,
    X402Client,
    X402Challenge,
    PaymentMode,
    X402Authorization,
)


class TestEIP3009Signer:
    """Test EIP-3009 signature generation."""

    @pytest.fixture
    def signer(self):
        # Test private key (DO NOT USE IN PRODUCTION)
        return EIP3009Signer("0x" + "1" * 64)

    def test_signer_initialization(self, signer):
        assert signer.address is not None
        assert signer.address.startswith("0x")

    def test_create_authorization(self, signer):
        auth = signer.create_authorization(
            from_address="0x1111",
            to_address="0x2222",
            amount_usdc=0.01,
            nonce=0,
        )

        assert auth.from_address == "0x1111"
        assert auth.to_address == "0x2222"
        assert auth.amount == 10000  # 0.01 * 1e6
        assert auth.valid_before > auth.valid_after

    def test_sign_authorization(self, signer):
        auth = signer.create_authorization(
            from_address="0x1111",
            to_address="0x2222",
            amount_usdc=0.001,
        )

        signed = signer.sign_authorization(auth)
        assert signed.signature.startswith("0x")
        assert len(signed.signature) > 100
        assert signed.signer_address == signer.address


class TestCircleNanopayments:
    """Test Circle Nanopayments client."""

    @pytest.fixture
    def circle(self):
        return CircleNanopayments(api_key="test-key", is_testnet=True)

    @pytest.fixture
    def signer(self):
        return EIP3009Signer("0x" + "1" * 64)

    def test_client_initialization(self, circle):
        assert circle.is_testnet is True
        assert "testnet" in circle.base_url.lower()

    def test_submit_authorization(self, circle, signer):
        auth = signer.create_authorization(
            from_address="0x1111", to_address="0x2222", amount_usdc=0.002
        )
        signed = signer.sign_authorization(auth)

        tx = circle.submit_authorization(signed, batch_id="test_batch")

        assert tx.from_address == "0x1111"
        assert tx.to_address == "0x2222"
        assert tx.amount_usdc == 0.002
        assert tx.status == TransactionStatus.PENDING

    def test_confirm_transaction(self, circle, signer):
        auth = signer.create_authorization("0x1111", "0x2222", 0.001)
        signed = signer.sign_authorization(auth)
        tx = circle.submit_authorization(signed)

        # Confirm transaction
        result = circle.confirm_transaction(tx.tx_hash, block_number=1000)
        assert result is True
        assert circle.transactions[tx.tx_hash].status == TransactionStatus.CONFIRMED

    def test_submit_batch(self, circle, signer):
        # Add transactions to batch
        for i in range(3):
            auth = signer.create_authorization(
                f"0x{i:04x}", f"0x{i+1:04x}", amount_usdc=0.001
            )
            signed = signer.sign_authorization(auth)
            circle.submit_authorization(signed, batch_id="batch1")

        # Submit batch
        result = circle.submit_batch("batch1")
        assert result is True

        batch_stats = circle.get_batch_status("batch1")
        assert batch_stats["transaction_count"] == 3

    def test_settlement_summary(self, circle, signer):
        for i in range(5):
            auth = signer.create_authorization("0x1111", "0x2222", 0.001)
            signed = signer.sign_authorization(auth)
            tx = circle.submit_authorization(signed)
            circle.confirm_transaction(tx.tx_hash, block_number=1000 + i)

        summary = circle.get_settlement_summary()
        assert summary["total_transactions"] == 5
        assert summary["confirmed_transactions"] == 5
        assert summary["total_volume_usdc"] == pytest.approx(0.005)


class TestArcTestnet:
    """Test Arc blockchain integration."""

    @pytest.fixture
    def arc(self):
        return ArcTestnet()

    def test_testnet_initialization(self, arc):
        assert arc.chain_id == 42170
        assert arc.usdc_contract == "0xA2F67F45938e3cBEc8d6D92c25b3E3E49ED69767"

    def test_set_and_get_balance(self, arc):
        arc.set_balance("0x1111", 100.0)
        balance = arc.get_balance("0x1111")
        assert balance == 100.0

    def test_record_transaction(self, arc):
        tx = arc.record_transaction(
            tx_hash="0xabc",
            from_address="0x1111",
            to_address="0x2222",
            gas_used=21000,
        )

        assert tx.from_address == "0x1111"
        assert tx.to_address == "0x2222"
        assert tx.gas_used == 21000
        assert tx.is_success() is True

    def test_record_usdc_transfer(self, arc):
        arc.set_balance("0x1111", 10.0)
        arc.set_balance("0x2222", 0.0)

        transfer = arc.record_usdc_transfer(
            tx_hash="0xdef", from_address="0x1111", to_address="0x2222", amount_usdc=5.0
        )

        assert transfer.amount_usdc == 5.0
        assert arc.get_balance("0x1111") == 5.0
        assert arc.get_balance("0x2222") == 5.0

    def test_get_transfers_for_address(self, arc):
        arc.record_usdc_transfer("0xabc", "0x1111", "0x2222", 1.0)
        arc.record_usdc_transfer("0xdef", "0x2222", "0x3333", 2.0)
        arc.record_usdc_transfer("0xghi", "0x1111", "0x3333", 0.5)

        transfers = arc.get_transfers_for_address("0x1111")
        assert len(transfers) == 2

    def test_get_explorer_url(self, arc):
        url = arc.get_explorer_url("0xabc123")
        assert "explorer.arc.testnet" in url
        assert "0xabc123" in url


class TestX402Protocol:
    """Test x402 Payment Protocol implementation."""

    @pytest.fixture
    def server(self):
        return X402Server(wallet_address="0x0000")

    @pytest.fixture
    def client(self):
        return X402Client(payer_address="0x1111")

    def test_x402_challenge_creation(self, server):
        challenge = server.create_challenge(
            amount=0.01, nonce="nonce123", mode=PaymentMode.THRESHOLD
        )

        assert challenge.payment_amount == 0.01
        assert challenge.nonce == "nonce123"
        assert challenge.mode == PaymentMode.THRESHOLD

    def test_x402_challenge_header(self, server):
        challenge = server.create_challenge(0.01, "nonce123")
        header = challenge.to_header()

        assert "Bearer" in header
        assert "0.01" in header
        assert "nonce123" in header

    def test_x402_challenge_parse(self, server):
        challenge = server.create_challenge(0.01, "nonce123")
        header = challenge.to_header()

        parsed = X402Challenge.from_header(header)
        assert parsed.payment_amount == 0.01
        assert parsed.nonce == "nonce123"

    def test_x402_authorization(self, server, client):
        challenge = server.create_challenge(0.01, "nonce123")
        auth = client.respond_to_challenge(challenge)

        assert auth.nonce == "nonce123"
        assert auth.payer_address == "0x1111"
        assert auth.signature.startswith("0x")

    def test_x402_authorization_header(self, server, client):
        challenge = server.create_challenge(0.01, "nonce123")
        auth = client.respond_to_challenge(challenge)
        header = auth.to_header()

        parsed = X402Authorization.from_header(header)
        assert parsed.nonce == "nonce123"
        assert parsed.payer_address == "0x1111"

    def test_x402_accept_payment(self, server, client):
        challenge = server.create_challenge(0.01, "nonce123")
        auth = client.respond_to_challenge(challenge)

        result = server.accept_payment("nonce123", auth)
        assert result is True

    def test_x402_server_stats(self, server, client):
        challenge = server.create_challenge(0.01, "nonce123")
        auth = client.respond_to_challenge(challenge)
        server.accept_payment("nonce123", auth)

        stats = server.get_stats()
        assert stats["challenges_created"] == 1
        assert stats["authorizations_received"] == 1
