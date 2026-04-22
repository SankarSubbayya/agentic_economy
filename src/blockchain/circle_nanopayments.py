"""
Circle Nanopayments Client: Batch USDC settlement on Arc blockchain.

Submits signed EIP-3009 authorizations to Circle's nanopayments service
for gas-less USDC transfers on Arc testnet.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum
import httpx
import logging
from src.blockchain.eip3009_signer import SignedAuthorization

logger = logging.getLogger(__name__)


class TransactionStatus(str, Enum):
    """Status of a nanopayment transaction."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class NanopaymentTx:
    """Record of a nanopayment transaction."""

    tx_hash: str
    from_address: str
    to_address: str
    amount_usdc: float
    signature: str
    status: TransactionStatus = TransactionStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    confirmed_at: Optional[datetime] = None
    block_number: Optional[int] = None
    gas_used: Optional[int] = None

    def is_confirmed(self) -> bool:
        return self.status == TransactionStatus.CONFIRMED


@dataclass
class SettlementBatch:
    """Batch of nanopayments for submission."""

    batch_id: str
    transactions: List[NanopaymentTx] = field(default_factory=list)
    total_volume: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None
    status: TransactionStatus = TransactionStatus.PENDING

    def add_transaction(self, tx: NanopaymentTx) -> None:
        """Add transaction to batch."""
        self.transactions.append(tx)
        self.total_volume += tx.amount_usdc

    def get_stats(self) -> dict:
        """Get batch statistics."""
        confirmed = len([tx for tx in self.transactions if tx.is_confirmed()])
        return {
            "batch_id": self.batch_id,
            "transaction_count": len(self.transactions),
            "total_volume_usdc": round(self.total_volume, 4),
            "confirmed_count": confirmed,
            "status": self.status,
        }


class CircleNanopayments:
    """Circle Nanopayments API client."""

    # API endpoints
    API_BASE_URL = "https://api.circle.com/v1"
    TESTNET_BASE_URL = "https://testnet-api.circle.com/v1"

    def __init__(self, api_key: str, is_testnet: bool = True, use_real_api: bool = False):
        """Initialize Circle Nanopayments client.

        Args:
            api_key: Circle API key from developer console
            is_testnet: Use testnet (default) or production
            use_real_api: If True, submit to real Circle API; if False, simulate locally
        """
        self.api_key = api_key
        self.is_testnet = is_testnet
        self.base_url = self.TESTNET_BASE_URL if is_testnet else self.API_BASE_URL
        self.use_real_api = use_real_api and api_key and not api_key.startswith("sk_test_demo")

        # Local simulation state
        self.batches: dict[str, SettlementBatch] = {}
        self.transactions: dict[str, NanopaymentTx] = {}

        if self.use_real_api:
            logger.info(f"Initialized Circle Nanopayments client (REAL API) at {self.base_url}")
        else:
            logger.info("Initialized Circle Nanopayments client (SIMULATION MODE)")

    def submit_authorization(
        self, signed_auth: SignedAuthorization, batch_id: str = "default"
    ) -> NanopaymentTx:
        """Submit signed EIP-3009 authorization for settlement.

        Args:
            signed_auth: Signed authorization from EIP3009Signer
            batch_id: Batch identifier for grouping payments

        Returns:
            NanopaymentTx record
        """
        # Create unique tx hash based on transaction data
        import hashlib
        tx_data = f"{signed_auth.authorization.from_address}{signed_auth.authorization.to_address}{signed_auth.authorization.amount}{len(self.transactions)}".encode()
        tx_hash = "0x" + hashlib.sha256(tx_data).hexdigest()[:64]

        # Create transaction record
        tx = NanopaymentTx(
            tx_hash=tx_hash,
            from_address=signed_auth.authorization.from_address,
            to_address=signed_auth.authorization.to_address,
            amount_usdc=signed_auth.authorization.amount / 1e6,
            signature=signed_auth.signature,
        )

        # Track transaction
        self.transactions[tx.tx_hash] = tx

        # Add to batch
        if batch_id not in self.batches:
            self.batches[batch_id] = SettlementBatch(batch_id=batch_id)

        self.batches[batch_id].add_transaction(tx)

        return tx

    def get_batch(self, batch_id: str) -> Optional[SettlementBatch]:
        """Get batch by ID."""
        return self.batches.get(batch_id)

    def confirm_transaction(
        self, tx_hash: str, block_number: int, gas_used: int = 0
    ) -> bool:
        """Mark transaction as confirmed (simulated).

        Args:
            tx_hash: Transaction hash
            block_number: Block number where confirmed
            gas_used: Gas used (USDC on Arc, so minimal)

        Returns:
            True if confirmed successfully
        """
        if tx_hash not in self.transactions:
            return False

        tx = self.transactions[tx_hash]
        tx.status = TransactionStatus.CONFIRMED
        tx.block_number = block_number
        tx.gas_used = gas_used
        tx.confirmed_at = datetime.utcnow()

        return True

    def submit_batch(self, batch_id: str) -> bool:
        """Submit batch for settlement.

        Args:
            batch_id: Batch identifier

        Returns:
            True if submitted successfully
        """
        if batch_id not in self.batches:
            return False

        batch = self.batches[batch_id]
        batch.submitted_at = datetime.utcnow()
        batch.status = TransactionStatus.PENDING

        return True

    def get_transaction_status(self, tx_hash: str) -> Optional[TransactionStatus]:
        """Get transaction status.

        Args:
            tx_hash: Transaction hash

        Returns:
            TransactionStatus or None if not found
        """
        tx = self.transactions.get(tx_hash)
        return tx.status if tx else None

    def get_batch_status(self, batch_id: str) -> Optional[dict]:
        """Get batch status and statistics.

        Args:
            batch_id: Batch identifier

        Returns:
            Stats dict or None if not found
        """
        batch = self.batches.get(batch_id)
        return batch.get_stats() if batch else None

    def get_all_batches(self) -> List[dict]:
        """Get all batch statistics."""
        return [batch.get_stats() for batch in self.batches.values()]

    async def submit_to_circle_api(self, tx_hash: str) -> bool:
        """Submit transaction to real Circle Nanopayments API.

        Args:
            tx_hash: Transaction hash to submit

        Returns:
            True if submitted successfully
        """
        if not self.use_real_api or tx_hash not in self.transactions:
            return False

        tx = self.transactions[tx_hash]

        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }

                payload = {
                    "idempotencyKey": tx_hash,
                    "transfersPayload": {
                        "rawSignature": tx.signature,
                        "amount": int(tx.amount_usdc * 1e6),
                        "from": tx.from_address,
                        "to": tx.to_address,
                    },
                }

                url = f"{self.base_url}/eip3009/submitTransfers"
                response = await client.post(url, json=payload, headers=headers)

                if response.status_code in [200, 201]:
                    tx.status = TransactionStatus.PENDING
                    logger.info(f"Submitted {tx_hash} to Circle API")
                    return True
                else:
                    logger.warning(
                        f"Circle API returned {response.status_code}: {response.text}"
                    )
                    return False

        except Exception as e:
            logger.error(f"Failed to submit to Circle API: {e}")
            return False

    def get_settlement_summary(self) -> dict:
        """Get summary of all settlements processed."""
        total_confirmed = len([tx for tx in self.transactions.values() if tx.is_confirmed()])
        total_volume = sum(tx.amount_usdc for tx in self.transactions.values())
        total_pending = len([tx for tx in self.transactions.values() if tx.status == TransactionStatus.PENDING])

        return {
            "total_transactions": len(self.transactions),
            "confirmed_transactions": total_confirmed,
            "pending_transactions": total_pending,
            "total_volume_usdc": round(total_volume, 4),
            "average_tx_size": round(
                total_volume / len(self.transactions) if self.transactions else 0, 6
            ),
            "batches_created": len(self.batches),
        }
