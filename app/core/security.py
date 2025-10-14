"""
Security utilities for the DEID Backend application.
Handles JWT tokens, signature verification, and SSO integration for decentralized identity management.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from eth_account import Account
from eth_account.messages import encode_defunct
import hashlib
import secrets
import redis
import json

from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import (
    SignatureVerificationError,
    InvalidSignatureError,
    NonceExpiredError,
    SSOError,
    SessionExpiredError
)

logger = get_logger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Redis client for session management
redis_client = redis.from_url(settings.REDIS_URL, db=settings.REDIS_DB, decode_responses=True)
class WalletSignatureManager:
    """Manages wallet signature verification for multi-chain support."""

    def __init__(self):
        self.message_prefix = settings.SIGNATURE_MESSAGE_PREFIX

    def verify_wallet_signature(
        self,
        message: str,
        signature: str,
        wallet_address: str,
        chain_id: int = 1
    ) -> bool:
        """
        Verify a wallet signature against a message for any supported chain.

        Args:
            message: Original message that was signed
            signature: Hex signature from wallet
            wallet_address: Wallet address that should have signed
            chain_id: Blockchain chain ID

        Returns:
            bool: True if signature is valid, False otherwise
        """
        try:
            # Validate signature format
            if not self._validate_signature_format(signature):
                raise InvalidSignatureError()

            # Create message hash
            message_hash = encode_defunct(text=message)

            # Recover address from signature
            recovered_address = Account.recover_message(message_hash, signature=signature)

            # Normalize addresses for comparison
            recovered_address = recovered_address.lower()
            wallet_address = wallet_address.lower()

            is_valid = recovered_address == wallet_address

            if is_valid:
                logger.info("Wallet signature verified",
                           wallet_address=wallet_address,
                           chain_id=chain_id)
            else:
                logger.warning("Wallet signature verification failed",
                              expected=wallet_address,
                              recovered=recovered_address,
                              chain_id=chain_id)

            return is_valid

        except Exception as e:
            logger.error("Error verifying wallet signature", error=str(e))
            raise SignatureVerificationError(f"Signature verification failed: {str(e)}")

    def _validate_signature_format(self, signature: str) -> bool:
        """Validate signature format."""
        if not signature or not signature.startswith('0x'):
            return False
        if len(signature) != 132:  # 0x + 130 hex chars
            return False
        return True

    def create_auth_message(self, wallet_address: str, nonce: str, action: str = "login") -> str:
        """
        Create an authentication message for wallet signing.

        Args:
            wallet_address: User's wallet address
            nonce: Random nonce for replay protection
            action: Action being performed (login, register, update_profile, etc.)

        Returns:
            str: Message to be signed by the wallet
        """
        message = f"{self.message_prefix}\n\nAction: {action}\nWallet: {wallet_address}\nNonce: {nonce}\nTimestamp: {int(datetime.utcnow().timestamp())}"
        return message

    def create_profile_message(self, wallet_address: str, nonce: str, profile_hash: str) -> str:
        """
        Create a message for profile registration/update.

        Args:
            wallet_address: User's wallet address
            nonce: Random nonce for replay protection
            profile_hash: IPFS hash of profile metadata

        Returns:
            str: Message to be signed by the wallet
        """
        message = f"{self.message_prefix}\n\nAction: update_profile\nWallet: {wallet_address}\nProfileHash: {profile_hash}\nNonce: {nonce}\nTimestamp: {int(datetime.utcnow().timestamp())}"
        return message

    def create_social_verification_message(
        self,
        wallet_address: str,
        nonce: str,
        platform: str,
        account_id: str
    ) -> str:
        """
        Create a message for social account verification.

        Args:
            wallet_address: User's wallet address
            nonce: Random nonce for replay protection
            platform: Social platform (twitter, discord, github, telegram)
            account_id: Social account identifier

        Returns:
            str: Message to be signed by the wallet
        """
        message = f"{self.message_prefix}\n\nAction: verify_social\nWallet: {wallet_address}\nPlatform: {platform}\nAccount: {account_id}\nNonce: {nonce}\nTimestamp: {int(datetime.utcnow().timestamp())}"
        return message

    def generate_nonce(self) -> str:
        """Generate a random nonce for signature verification."""
        return secrets.token_hex(16)


class NonceManager:
    """Manages nonces for signature verification with expiration."""

    def __init__(self):
        self.expire_minutes = settings.NONCE_EXPIRE_MINUTES

    def generate_and_store_nonce(self, wallet_address: str, action: str = "login") -> str:
        """
        Generate and store a nonce for a wallet address.

        Args:
            wallet_address: Wallet address
            action: Action being performed

        Returns:
            str: Generated nonce
        """
        nonce = secrets.token_hex(16)
        key = f"nonce:{wallet_address}:{action}"

        # Store nonce with expiration
        redis_client.setex(key, self.expire_minutes * 60, nonce)

        logger.info("Nonce generated and stored", wallet_address=wallet_address, action=action)
        return nonce

    def verify_and_consume_nonce(self, wallet_address: str, nonce: str, action: str = "login") -> bool:
        """
        Verify and consume a nonce.

        Args:
            wallet_address: Wallet address
            nonce: Nonce to verify
            action: Action being performed

        Returns:
            bool: True if nonce is valid and consumed
        """
        key = f"nonce:{wallet_address}:{action}"
        stored_nonce = redis_client.get(key)

        if not stored_nonce:
            logger.warning("Nonce not found or expired", wallet_address=wallet_address, action=action)
            raise NonceExpiredError()

        if stored_nonce != nonce:
            logger.warning("Nonce mismatch", wallet_address=wallet_address, action=action)
            return False

        # Consume the nonce
        redis_client.delete(key)
        logger.info("Nonce verified and consumed", wallet_address=wallet_address, action=action)
        return True


class ChainValidator:
    """Validates blockchain addresses and chain IDs."""

    @staticmethod
    def validate_ethereum_address(address: str) -> bool:
        """Validate Ethereum address format."""
        if not address or not address.startswith('0x'):
            return False
        if len(address) != 42:
            return False
        try:
            int(address[2:], 16)
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_solana_address(address: str) -> bool:
        """Validate Solana address format."""
        if not address:
            return False
        # Solana addresses are base58 encoded and typically 32-44 characters
        if len(address) < 32 or len(address) > 44:
            return False
        # Basic base58 check (simplified)
        try:
            import base58
            base58.b58decode(address)
            return True
        except:
            return False

    @staticmethod
    def validate_chain_id(chain_id: int) -> bool:
        """Validate if chain ID is supported."""
        supported_chains = [1, 56, 137]  # Ethereum, BSC, Polygon
        return chain_id in supported_chains

    @staticmethod
    def get_address_type(address: str) -> str:
        """Determine address type based on format."""
        if ChainValidator.validate_ethereum_address(address):
            return "ethereum"
        elif ChainValidator.validate_solana_address(address):
            return "solana"
        else:
            return "unknown"


# Global instances
security_manager = SecurityManager()
wallet_signature_manager = WalletSignatureManager()
nonce_manager = NonceManager()
sso_manager = SSOManager()
chain_validator = ChainValidator()
