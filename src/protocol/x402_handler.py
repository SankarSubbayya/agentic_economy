"""
x402 Payment Protocol Handler: HTTP 402-based web-native payments.

Implements x402 standard for Payment Required HTTP 402 responses,
enabling payment negotiation directly in HTTP headers.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict
import json
from datetime import datetime


class PaymentMode(str, Enum):
    """Payment modes supported by x402."""

    THRESHOLD = "threshold"  # Single payment required
    STREAMING = "streaming"  # Payment per byte/token
    SUBSCRIPTION = "subscription"  # Periodic payment


@dataclass
class X402Challenge:
    """x402 Payment Required challenge."""

    payment_amount: float  # USDC amount
    recipient_address: str  # Wallet address
    nonce: str  # Challenge nonce for replay protection
    mode: PaymentMode = PaymentMode.THRESHOLD
    resource: str = "api"
    required_by: Optional[int] = None  # Unix timestamp

    def to_header(self) -> str:
        """Serialize to x402 Payment header format."""
        header_parts = [
            f"amount={self.payment_amount}",
            f"recipient={self.recipient_address}",
            f"nonce={self.nonce}",
            f"mode={self.mode.value}",
            f"resource={self.resource}",
        ]
        if self.required_by:
            header_parts.append(f"required_by={self.required_by}")
        return "Bearer " + ",".join(header_parts)

    @staticmethod
    def from_header(header_value: str) -> Optional["X402Challenge"]:
        """Parse x402 Payment header."""
        if not header_value.startswith("Bearer "):
            return None

        try:
            parts = header_value[7:].split(",")
            params = {}
            for part in parts:
                key, value = part.split("=", 1)
                params[key.strip()] = value.strip()

            return X402Challenge(
                payment_amount=float(params.get("amount", 0)),
                recipient_address=params.get("recipient", ""),
                nonce=params.get("nonce", ""),
                mode=PaymentMode(params.get("mode", "threshold")),
                resource=params.get("resource", "api"),
                required_by=int(params.get("required_by")) if "required_by" in params else None,
            )
        except (ValueError, KeyError):
            return None


@dataclass
class X402Authorization:
    """x402 Payment authorization response."""

    signature: str  # Signed proof of payment
    nonce: str  # Challenge nonce
    payer_address: str  # Payer wallet address
    tx_hash: Optional[str] = None  # Settlement transaction hash
    timestamp: datetime = None  # When authorized

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_header(self) -> str:
        """Serialize to x402 Authorization header format."""
        return f"Bearer {self.signature},nonce={self.nonce},payer={self.payer_address}"

    @staticmethod
    def from_header(header_value: str) -> Optional["X402Authorization"]:
        """Parse x402 Authorization header."""
        if not header_value.startswith("Bearer "):
            return None

        try:
            parts = header_value[7:].split(",")
            signature = parts[0]

            params = {}
            for part in parts[1:]:
                key, value = part.split("=", 1)
                params[key.strip()] = value.strip()

            return X402Authorization(
                signature=signature,
                nonce=params.get("nonce", ""),
                payer_address=params.get("payer", ""),
                tx_hash=params.get("tx_hash"),
            )
        except (ValueError, IndexError, KeyError):
            return None


class X402Server:
    """Server-side x402 payment handler."""

    def __init__(self, wallet_address: str):
        """Initialize x402 server.

        Args:
            wallet_address: Server's wallet for receiving payments
        """
        self.wallet_address = wallet_address
        self.challenges: Dict[str, X402Challenge] = {}
        self.authorizations: Dict[str, X402Authorization] = {}

    def create_challenge(
        self,
        amount: float,
        nonce: str,
        mode: PaymentMode = PaymentMode.THRESHOLD,
        resource: str = "api",
    ) -> X402Challenge:
        """Create payment challenge.

        Args:
            amount: USDC amount required
            nonce: Challenge nonce
            mode: Payment mode
            resource: Resource being protected

        Returns:
            X402Challenge
        """
        challenge = X402Challenge(
            payment_amount=amount,
            recipient_address=self.wallet_address,
            nonce=nonce,
            mode=mode,
            resource=resource,
            required_by=int(datetime.utcnow().timestamp()) + 3600,  # 1 hour validity
        )

        self.challenges[nonce] = challenge
        return challenge

    def verify_authorization(
        self, authorization: X402Authorization, challenge: X402Challenge
    ) -> bool:
        """Verify x402 authorization.

        Args:
            authorization: x402 authorization
            challenge: Original challenge

        Returns:
            True if authorization is valid
        """
        # Verify nonce matches
        if authorization.nonce != challenge.nonce:
            return False

        # Verify signature is not empty (real verification in Day 5)
        if not authorization.signature or authorization.signature == "0x":
            return False

        # Verify payer is not zero address
        if not authorization.payer_address or authorization.payer_address == "0x0":
            return False

        return True

    def accept_payment(self, nonce: str, authorization: X402Authorization) -> bool:
        """Accept payment for completed transaction.

        Args:
            nonce: Challenge nonce
            authorization: x402 authorization

        Returns:
            True if accepted
        """
        if nonce not in self.challenges:
            return False

        challenge = self.challenges[nonce]

        if not self.verify_authorization(authorization, challenge):
            return False

        self.authorizations[nonce] = authorization
        return True

    def get_challenge(self, nonce: str) -> Optional[X402Challenge]:
        """Get challenge by nonce."""
        return self.challenges.get(nonce)

    def get_authorization(self, nonce: str) -> Optional[X402Authorization]:
        """Get authorization by nonce."""
        return self.authorizations.get(nonce)

    def get_stats(self) -> dict:
        """Get x402 server statistics."""
        total_authorized = len(self.authorizations)
        total_amount = sum(
            self.challenges[nonce].payment_amount
            for nonce in self.authorizations.keys()
            if nonce in self.challenges
        )

        return {
            "challenges_created": len(self.challenges),
            "authorizations_received": total_authorized,
            "total_payment_volume": round(total_amount, 4),
            "server_wallet": self.wallet_address,
        }


class X402Client:
    """Client-side x402 payment handler."""

    def __init__(self, payer_address: str, signer_func=None):
        """Initialize x402 client.

        Args:
            payer_address: Payer's wallet address
            signer_func: Function to sign payments (optional for testing)
        """
        self.payer_address = payer_address
        self.signer_func = signer_func or self._default_signer
        self.completed_payments: Dict[str, X402Authorization] = {}

    def respond_to_challenge(self, challenge: X402Challenge) -> X402Authorization:
        """Create authorization response to challenge.

        Args:
            challenge: x402 challenge

        Returns:
            X402Authorization
        """
        # Sign payment (simplified - real signing uses EIP-3009)
        signature = self.signer_func(challenge)

        authorization = X402Authorization(
            signature=signature,
            nonce=challenge.nonce,
            payer_address=self.payer_address,
            timestamp=datetime.utcnow(),
        )

        self.completed_payments[challenge.nonce] = authorization
        return authorization

    def _default_signer(self, challenge: X402Challenge) -> str:
        """Default mock signer."""
        return f"0x{'b' * 130}"  # Mock signature

    def get_stats(self) -> dict:
        """Get client statistics."""
        return {
            "payer_address": self.payer_address,
            "payments_completed": len(self.completed_payments),
            "total_amount_paid": round(
                sum(
                    float(auth.signature.count("b")) / 100
                    for auth in self.completed_payments.values()
                ),
                4,
            ),
        }
