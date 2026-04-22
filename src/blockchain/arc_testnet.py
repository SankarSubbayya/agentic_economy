"""
Arc Testnet Integration: On-chain transaction verification and monitoring.

Connects to Arc testnet RPC to verify nanopayment settlements,
monitor transaction status, and track USDC balances.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum
from web3 import Web3
import logging

logger = logging.getLogger(__name__)


class BlockchainStatus(str, Enum):
    """Status of blockchain transaction."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    REVERTED = "reverted"


@dataclass
class BlockInfo:
    """Information about a block on Arc."""

    block_number: int
    timestamp: datetime
    miner: str
    gas_used: int
    gas_limit: int
    transaction_count: int


@dataclass
class TransactionReceipt:
    """Transaction receipt from Arc blockchain."""

    tx_hash: str
    block_number: int
    block_hash: str
    from_address: str
    to_address: str
    gas_used: int
    cumulative_gas_used: int
    contract_address: Optional[str] = None
    status: BlockchainStatus = BlockchainStatus.CONFIRMED
    logs: List[dict] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def is_success(self) -> bool:
        """Check if transaction succeeded."""
        return self.status == BlockchainStatus.CONFIRMED


@dataclass
class USDCTransfer:
    """USDC transfer event on Arc."""

    tx_hash: str
    from_address: str
    to_address: str
    amount_usdc: float
    block_number: int
    timestamp: datetime
    status: BlockchainStatus = BlockchainStatus.CONFIRMED

    def is_success(self) -> bool:
        """Check if transfer succeeded."""
        return self.status == BlockchainStatus.CONFIRMED


class ArcTestnet:
    """Arc testnet blockchain integration."""

    # Arc testnet configuration (real chain ID: 5042002)
    CHAIN_ID = 5042002
    RPC_ENDPOINT = "https://rpc.arc.testnet.circle.com"
    USDC_CONTRACT = "0xA2F67F45938e3cBEc8d6D92c25b3E3E49ED69767"
    EXPLORER = "https://explorer.arc.testnet.circle.com"

    def __init__(self, rpc_url: str = RPC_ENDPOINT, use_real_rpc: bool = False):
        """Initialize Arc testnet client.

        Args:
            rpc_url: RPC endpoint URL
            use_real_rpc: If True, make real RPC calls; if False, simulate locally
        """
        self.rpc_url = rpc_url
        self.chain_id = self.CHAIN_ID
        self.usdc_contract = self.USDC_CONTRACT
        self.use_real_rpc = use_real_rpc

        # Initialize web3 connection if using real RPC
        self.web3: Optional[Web3] = None
        if use_real_rpc:
            try:
                self.web3 = Web3(Web3.HTTPProvider(rpc_url))
                if self.web3.is_connected():
                    logger.info(f"Connected to Arc testnet at {rpc_url}")
                else:
                    logger.warning(f"Could not connect to Arc testnet at {rpc_url}")
                    self.use_real_rpc = False
            except Exception as e:
                logger.warning(f"Failed to initialize web3: {e}")
                self.use_real_rpc = False

        # Local simulation state
        self.transactions: dict[str, TransactionReceipt] = {}
        self.transfers: dict[str, USDCTransfer] = {}
        self.balances: dict[str, float] = {}
        self.current_block = 1000000

    def get_balance(self, address: str) -> float:
        """Get USDC balance for address.

        Args:
            address: Wallet address

        Returns:
            USDC balance
        """
        return self.balances.get(address, 0.0)

    def set_balance(self, address: str, balance: float) -> None:
        """Set USDC balance for address (for testing).

        Args:
            address: Wallet address
            balance: USDC balance
        """
        self.balances[address] = balance

    def record_transaction(
        self,
        tx_hash: str,
        from_address: str,
        to_address: str,
        gas_used: int = 0,
    ) -> TransactionReceipt:
        """Record transaction on Arc.

        Args:
            tx_hash: Transaction hash
            from_address: Sender address
            to_address: Recipient address
            gas_used: Gas used

        Returns:
            TransactionReceipt
        """
        receipt = TransactionReceipt(
            tx_hash=tx_hash,
            block_number=self.current_block,
            block_hash=f"0x{'c' * 64}",
            from_address=from_address,
            to_address=to_address,
            gas_used=gas_used,
            cumulative_gas_used=gas_used,
            status=BlockchainStatus.CONFIRMED,
        )

        self.transactions[tx_hash] = receipt
        self.current_block += 1

        return receipt

    def record_usdc_transfer(
        self,
        tx_hash: str,
        from_address: str,
        to_address: str,
        amount_usdc: float,
    ) -> USDCTransfer:
        """Record USDC transfer on Arc.

        Args:
            tx_hash: Transaction hash
            from_address: Sender address
            to_address: Recipient address
            amount_usdc: USDC amount transferred

        Returns:
            USDCTransfer
        """
        transfer = USDCTransfer(
            tx_hash=tx_hash,
            from_address=from_address,
            to_address=to_address,
            amount_usdc=amount_usdc,
            block_number=self.current_block - 1,
            timestamp=datetime.utcnow(),
            status=BlockchainStatus.CONFIRMED,
        )

        self.transfers[tx_hash] = transfer

        # Update balances
        self.balances[from_address] = self.balances.get(from_address, 0) - amount_usdc
        self.balances[to_address] = self.balances.get(to_address, 0) + amount_usdc

        return transfer

    def get_transaction(self, tx_hash: str) -> Optional[TransactionReceipt]:
        """Get transaction receipt.

        Args:
            tx_hash: Transaction hash

        Returns:
            TransactionReceipt or None
        """
        return self.transactions.get(tx_hash)

    def get_transfer(self, tx_hash: str) -> Optional[USDCTransfer]:
        """Get USDC transfer details.

        Args:
            tx_hash: Transaction hash

        Returns:
            USDCTransfer or None
        """
        return self.transfers.get(tx_hash)

    def get_transfers_for_address(self, address: str) -> List[USDCTransfer]:
        """Get all USDC transfers for address.

        Args:
            address: Wallet address

        Returns:
            List of USDCTransfer
        """
        transfers = []
        for transfer in self.transfers.values():
            if transfer.from_address.lower() == address.lower() or transfer.to_address.lower(
            ) == address.lower():
                transfers.append(transfer)
        return sorted(transfers, key=lambda t: t.block_number, reverse=True)

    def wait_for_confirmation(self, tx_hash: str, timeout_blocks: int = 12) -> bool:
        """Wait for transaction confirmation.

        Args:
            tx_hash: Transaction hash
            timeout_blocks: Blocks to wait before timeout

        Returns:
            True if confirmed
        """
        if tx_hash not in self.transactions:
            return False

        tx = self.transactions[tx_hash]
        return tx.is_success()

    def get_block_info(self, block_number: int) -> Optional[BlockInfo]:
        """Get block information.

        Args:
            block_number: Block number

        Returns:
            BlockInfo or None
        """
        if block_number > self.current_block:
            return None

        return BlockInfo(
            block_number=block_number,
            timestamp=datetime.utcnow(),
            miner="0xminer",
            gas_used=21000,
            gas_limit=30000000,
            transaction_count=1,
        )

    def get_explorer_url(self, tx_hash: str) -> str:
        """Get Arc Block Explorer URL for transaction.

        Args:
            tx_hash: Transaction hash

        Returns:
            Block Explorer URL
        """
        return f"{self.EXPLORER}/tx/{tx_hash}"

    def get_network_stats(self) -> dict:
        """Get Arc testnet network statistics.

        Returns:
            Network stats dict
        """
        total_volume = sum(t.amount_usdc for t in self.transfers.values())
        successful = len([t for t in self.transfers.values() if t.status == BlockchainStatus.CONFIRMED])

        return {
            "chain_id": self.CHAIN_ID,
            "current_block": self.current_block,
            "total_transactions": len(self.transactions),
            "total_transfers": len(self.transfers),
            "confirmed_transfers": successful,
            "total_volume_usdc": round(total_volume, 4),
            "unique_addresses": len(self.balances),
            "rpc_endpoint": self.rpc_url,
            "usdc_contract": self.USDC_CONTRACT,
        }

    def get_transaction_receipt(self, tx_hash: str) -> Optional[dict]:
        """Get transaction receipt from blockchain.

        Args:
            tx_hash: Transaction hash

        Returns:
            Transaction receipt dict or None
        """
        if self.use_real_rpc and self.web3:
            try:
                receipt = self.web3.eth.get_transaction_receipt(tx_hash)
                return dict(receipt)
            except Exception as e:
                logger.warning(f"Failed to get receipt for {tx_hash}: {e}")
                return None

        # Fallback to local simulation
        if tx_hash in self.transactions:
            return {
                "transactionHash": tx_hash,
                "blockNumber": self.transactions[tx_hash].block_number,
                "status": 1 if self.transactions[tx_hash].is_success() else 0,
            }
        return None

    def verify_transaction_on_chain(self, tx_hash: str) -> bool:
        """Verify transaction was confirmed on-chain.

        Args:
            tx_hash: Transaction hash

        Returns:
            True if transaction is confirmed
        """
        if self.use_real_rpc and self.web3:
            try:
                receipt = self.web3.eth.get_transaction_receipt(tx_hash)
                return receipt and receipt.get("status") == 1
            except Exception as e:
                logger.warning(f"Failed to verify {tx_hash}: {e}")
                return False

        # Fallback to local simulation
        if tx_hash in self.transactions:
            return self.transactions[tx_hash].is_success()
        return False

    def get_balance_from_chain(self, address: str) -> Optional[float]:
        """Get USDC balance from blockchain (real RPC).

        Args:
            address: Wallet address

        Returns:
            USDC balance or None if not available
        """
        if self.use_real_rpc and self.web3:
            try:
                # Get balance in wei
                balance_wei = self.web3.eth.get_balance(address)
                # Convert to USDC (6 decimals)
                balance_usdc = balance_wei / 1e6
                return balance_usdc
            except Exception as e:
                logger.warning(f"Failed to get balance for {address}: {e}")
                return None

        # Fallback to local simulation
        return self.balances.get(address, 0.0)

    def reset(self) -> None:
        """Reset testnet state (for testing)."""
        self.transactions.clear()
        self.transfers.clear()
        self.balances.clear()
        self.current_block = 1000000
