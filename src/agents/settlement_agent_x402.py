"""
Day 4: Settlement Agent with x402 Protocol + Circle Nanopayments.

Enhanced settlement agent that:
- Signs real EIP-3009 authorizations
- Submits to Circle Nanopayments for gas-less USDC transfer
- Verifies settlement on Arc blockchain
- Handles x402 payment protocol negotiation
"""

from typing import Optional
from src.blockchain.eip3009_signer import EIP3009Signer, SignedAuthorization
from src.blockchain.circle_nanopayments import CircleNanopayments, NanopaymentTx
from src.blockchain.arc_testnet import ArcTestnet
from src.protocol.x402_handler import X402Server, X402Client, X402Challenge, PaymentMode
from src.types import SettlementResult


class SettlementAgentX402:
    """Settlement agent with x402 protocol and on-chain verification."""

    SETTLEMENT_PRICE = 0.002  # $0.002 per settlement

    def __init__(
        self,
        agent_id: str,
        wallet_address: str,
        private_key: str,
        circle_api_key: str,
        agent_name: str = "settlement-agent",
    ):
        """Initialize settlement agent with blockchain integration.

        Args:
            agent_id: Unique agent identifier
            wallet_address: Agent's wallet on Arc
            private_key: Private key for signing (hex string with 0x prefix)
            circle_api_key: Circle API key for nanopayments
            agent_name: Human-readable agent name
        """
        self.agent_id = agent_id
        self.wallet_address = wallet_address
        self.agent_name = agent_name

        # EIP-3009 signer for gas-less authorizations
        self.signer = EIP3009Signer(private_key)

        # Circle Nanopayments for submission
        self.circle = CircleNanopayments(circle_api_key, is_testnet=True)

        # Arc blockchain for verification
        self.arc = ArcTestnet()

        # x402 protocol handler
        self.x402_server = X402Server(wallet_address)

        # Track settlements
        self.settlements_authorized = 0
        self.settlements_denied = 0
        self.settlements_confirmed = 0
        self.total_volume = 0.0
        self.total_earned = 0.0

    def authorize_nanopayment(
        self, payer: str, recipient: str, amount_usdc: float, nonce: int = 0
    ) -> Optional[SettlementResult]:
        """Authorize a gas-less USDC transfer via EIP-3009.

        Args:
            payer: Payer wallet address
            recipient: Recipient wallet address
            amount_usdc: Amount in USDC
            nonce: Nonce for replay protection

        Returns:
            SettlementResult with signature and settlement details
        """
        try:
            # Create EIP-3009 authorization
            auth_params = self.signer.create_authorization(
                from_address=payer, to_address=recipient, amount_usdc=amount_usdc, nonce=nonce
            )

            # Sign authorization
            signed_auth = self.signer.sign_authorization(auth_params)

            # Submit to Circle Nanopayments
            tx = self.circle.submit_authorization(signed_auth, batch_id=f"{payer}_{nonce}")

            # Record transaction on Arc testnet
            self.arc.record_transaction(
                tx_hash=tx.tx_hash,
                from_address=payer,
                to_address=recipient,
            )

            # Record USDC transfer on Arc testnet
            arc_tx = self.arc.record_usdc_transfer(
                tx_hash=tx.tx_hash,
                from_address=payer,
                to_address=recipient,
                amount_usdc=amount_usdc,
            )

            # Confirm settlement
            if arc_tx.is_success():
                self.circle.confirm_transaction(tx.tx_hash, arc_tx.block_number)
                self.settlements_authorized += 1
                self.total_volume += amount_usdc
                self.total_earned += self.SETTLEMENT_PRICE

                return SettlementResult(
                    authorized=True,
                    amount=amount_usdc,
                    signature=signed_auth.signature,
                    reason=f"Settled via nanopayment: {tx.tx_hash}",
                )
            else:
                self.settlements_denied += 1
                return SettlementResult(
                    authorized=False,
                    amount=0.0,
                    signature="",
                    reason="Settlement confirmation failed on Arc",
                )

        except Exception as e:
            self.settlements_denied += 1
            return SettlementResult(
                authorized=False, amount=0.0, signature="", reason=f"Settlement error: {str(e)}"
            )

    def handle_x402_challenge(
        self, challenge: X402Challenge, payer: str
    ) -> Optional[SettlementResult]:
        """Handle x402 Payment Required challenge.

        Args:
            challenge: x402 challenge from server
            payer: Payer wallet address

        Returns:
            SettlementResult with payment authorization
        """
        try:
            # Create x402 client
            x402_client = X402Client(payer_address=payer)

            # Generate authorization response
            auth = x402_client.respond_to_challenge(challenge)

            # Accept payment on server side
            self.x402_server.accept_payment(challenge.nonce, auth)

            self.settlements_authorized += 1
            self.total_earned += self.SETTLEMENT_PRICE

            return SettlementResult(
                authorized=True,
                amount=challenge.payment_amount,
                signature=auth.signature,
                reason=f"x402 payment authorized: {challenge.nonce}",
            )

        except Exception as e:
            self.settlements_denied += 1
            return SettlementResult(
                authorized=False,
                amount=0.0,
                signature="",
                reason=f"x402 challenge failed: {str(e)}",
            )

    def verify_settlement_on_chain(self, tx_hash: str) -> bool:
        """Verify settlement was recorded on Arc blockchain.

        Args:
            tx_hash: Settlement transaction hash

        Returns:
            True if settlement confirmed on-chain
        """
        tx = self.arc.get_transaction(tx_hash)
        if not tx:
            return False

        self.settlements_confirmed += 1
        return tx.is_success()

    def get_settlement_proof(self, tx_hash: str) -> Optional[dict]:
        """Get proof of settlement for verification.

        Args:
            tx_hash: Settlement transaction hash

        Returns:
            Settlement proof with block explorer link
        """
        transfer = self.arc.get_transfer(tx_hash)
        if not transfer:
            return None

        return {
            "tx_hash": tx_hash,
            "from": transfer.from_address,
            "to": transfer.to_address,
            "amount_usdc": transfer.amount_usdc,
            "block_number": transfer.block_number,
            "confirmed": transfer.is_success(),
            "explorer_url": self.arc.get_explorer_url(tx_hash),
            "timestamp": transfer.timestamp.isoformat(),
        }

    def get_stats(self) -> dict:
        """Get settlement agent statistics.

        Returns:
            Stats dict with settlement metrics
        """
        return {
            "agent_id": self.agent_id,
            "wallet": self.wallet_address,
            "settlements_authorized": self.settlements_authorized,
            "settlements_denied": self.settlements_denied,
            "settlements_confirmed": self.settlements_confirmed,
            "total_volume_usdc": round(self.total_volume, 4),
            "total_earned_usdc": round(self.total_earned, 4),
            "success_rate": round(
                (
                    self.settlements_authorized
                    / (self.settlements_authorized + self.settlements_denied)
                    * 100
                )
                if (self.settlements_authorized + self.settlements_denied) > 0
                else 0,
                1,
            ),
        }

    def get_blockchain_stats(self) -> dict:
        """Get Arc blockchain integration statistics.

        Returns:
            Arc network stats
        """
        return self.arc.get_network_stats()

    def reset(self) -> None:
        """Reset agent state (for testing)."""
        self.settlements_authorized = 0
        self.settlements_denied = 0
        self.settlements_confirmed = 0
        self.total_volume = 0.0
        self.total_earned = 0.0
        self.arc.reset()
