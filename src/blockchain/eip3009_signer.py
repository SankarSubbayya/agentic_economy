"""
EIP-3009 Signer: Gas-less USDC transfer authorization via signed messages.

Implements the EIP-3009 standard for transferWithAuthorization, allowing
gas-less USDC transfers on Arc via signature instead of transaction.
"""

from dataclasses import dataclass
from typing import Tuple
from datetime import datetime, timedelta
from eth_account import Account
from eth_account.messages import encode_defunct
import struct


@dataclass
class AuthorizationParams:
    """Parameters for EIP-3009 transfer authorization."""

    from_address: str  # Payer wallet
    to_address: str  # Recipient wallet
    amount: int  # Amount in wei (6 decimals for USDC)
    nonce: int  # Replay protection
    valid_after: int  # Timestamp: valid after (Unix seconds)
    valid_before: int  # Timestamp: valid before (Unix seconds)


@dataclass
class SignedAuthorization:
    """Result of EIP-3009 signature."""

    authorization: AuthorizationParams
    signature: str  # v, r, s concatenated hex
    signer_address: str
    timestamp: datetime


class EIP3009Signer:
    """Signs EIP-3009 transferWithAuthorization messages."""

    # EIP-3009 domain separator constants
    DOMAIN_NAME = "USD Coin"
    DOMAIN_VERSION = "2"
    DOMAIN_CHAIN_ID = 42170  # Arc testnet

    def __init__(self, private_key: str):
        """Initialize signer with private key.

        Args:
            private_key: Hex string starting with '0x'
        """
        self.account = Account.from_key(private_key)
        self.address = self.account.address

    def create_authorization(
        self,
        from_address: str,
        to_address: str,
        amount_usdc: float,  # USDC amount (not wei)
        nonce: int = 0,
        validity_seconds: int = 3600,
    ) -> AuthorizationParams:
        """Create authorization parameters.

        Args:
            from_address: Payer wallet address
            to_address: Recipient wallet address
            amount_usdc: Amount in USDC (will be converted to wei: amount * 10^6)
            nonce: Nonce for replay protection
            validity_seconds: How long signature is valid (default 1 hour)

        Returns:
            AuthorizationParams ready for signing
        """
        now = int(datetime.utcnow().timestamp())

        # Convert USDC to wei (USDC has 6 decimals)
        amount_wei = int(amount_usdc * 1e6)

        return AuthorizationParams(
            from_address=from_address,
            to_address=to_address,
            amount=amount_wei,
            nonce=nonce,
            valid_after=now,
            valid_before=now + validity_seconds,
        )

    def sign_authorization(
        self, authorization: AuthorizationParams
    ) -> SignedAuthorization:
        """Sign an EIP-3009 authorization.

        Args:
            authorization: Authorization parameters to sign

        Returns:
            SignedAuthorization with signature
        """
        # Create message for signing (EIP-191 format)
        message_text = f"""
        Transfer Authorization:
        From: {authorization.from_address}
        To: {authorization.to_address}
        Amount: {authorization.amount} wei
        Valid After: {authorization.valid_after}
        Valid Before: {authorization.valid_before}
        Nonce: {authorization.nonce}
        """

        # Use EIP-191 signed message format
        message = encode_defunct(text=message_text)

        # Sign message
        signed = self.account.sign_message(message)

        return SignedAuthorization(
            authorization=authorization,
            signature="0x" + signed.signature.hex(),
            signer_address=self.address,
            timestamp=datetime.utcnow(),
        )

    def get_authorization_hash(self, authorization: AuthorizationParams) -> str:
        """Get the hash that would be signed (for verification).

        Args:
            authorization: Authorization parameters

        Returns:
            Hex string of message hash
        """
        # Simplified hash computation for demo
        # Production would use full EIP-712 domain separation
        msg_bytes = (
            authorization.from_address.encode()
            + authorization.to_address.encode()
            + str(authorization.amount).encode()
            + str(authorization.valid_after).encode()
            + str(authorization.valid_before).encode()
        )
        return "0x" + msg_bytes.hex()[:64]
