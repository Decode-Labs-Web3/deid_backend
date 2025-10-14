"""
Custom exceptions for the DEID Backend application.
Provides structured error handling for decentralized identity management.
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class DEIDException(Exception):
    """Base exception for DEID Backend application."""

    def __init__(
        self,
        message: str,
        error_code: str = "DEID_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


# Authentication & Authorization
class AuthenticationError(DEIDException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AUTH_ERROR", details)


class AuthorizationError(DEIDException):
    """Raised when authorization fails."""

    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AUTHZ_ERROR", details)


class SSOError(DEIDException):
    """Raised when SSO authentication fails."""

    def __init__(self, message: str = "SSO authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "SSO_ERROR", details)


class SessionExpiredError(DEIDException):
    """Raised when user session has expired."""

    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__("Session has expired", "SESSION_EXPIRED", details)


# Identity Management
class IdentityNotFoundError(DEIDException):
    """Raised when a DEID identity is not found."""

    def __init__(self, identity_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"Identity not found: {identity_id}"
        super().__init__(message, "IDENTITY_NOT_FOUND", details)


class UsernameAlreadyTakenError(DEIDException):
    """Raised when trying to register a username that's already taken."""

    def __init__(self, username: str, details: Optional[Dict[str, Any]] = None):
        message = f"Username already taken: {username}"
        super().__init__(message, "USERNAME_TAKEN", details)


class InvalidUsernameError(DEIDException):
    """Raised when username format is invalid."""

    def __init__(self, username: str, details: Optional[Dict[str, Any]] = None):
        message = f"Invalid username format: {username}"
        super().__init__(message, "INVALID_USERNAME", details)


# Wallet Management
class WalletAlreadyLinkedError(DEIDException):
    """Raised when trying to link a wallet that's already linked."""

    def __init__(self, wallet_address: str, details: Optional[Dict[str, Any]] = None):
        message = f"Wallet already linked: {wallet_address}"
        super().__init__(message, "WALLET_ALREADY_LINKED", details)


class InvalidWalletAddressError(DEIDException):
    """Raised when an invalid wallet address is provided."""

    def __init__(self, wallet_address: str, details: Optional[Dict[str, Any]] = None):
        message = f"Invalid wallet address: {wallet_address}"
        super().__init__(message, "INVALID_WALLET_ADDRESS", details)


class UnsupportedChainError(DEIDException):
    """Raised when an unsupported blockchain chain is specified."""

    def __init__(self, chain_id: int, details: Optional[Dict[str, Any]] = None):
        message = f"Unsupported blockchain chain: {chain_id}"
        super().__init__(message, "UNSUPPORTED_CHAIN", details)


class WalletLimitExceededError(DEIDException):
    """Raised when user tries to link more wallets than allowed."""

    def __init__(self, max_wallets: int, details: Optional[Dict[str, Any]] = None):
        message = f"Maximum wallet limit exceeded: {max_wallets}"
        super().__init__(message, "WALLET_LIMIT_EXCEEDED", details)


# Signature & Verification
class SignatureVerificationError(DEIDException):
    """Raised when wallet signature verification fails."""

    def __init__(self, message: str = "Signature verification failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "SIGNATURE_ERROR", details)


class InvalidSignatureError(DEIDException):
    """Raised when signature format is invalid."""

    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__("Invalid signature format", "INVALID_SIGNATURE", details)


class NonceExpiredError(DEIDException):
    """Raised when nonce has expired."""

    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__("Nonce has expired", "NONCE_EXPIRED", details)


# Social Account Verification
class SocialAccountAlreadyLinkedError(DEIDException):
    """Raised when trying to link a social account that's already linked."""

    def __init__(self, platform: str, account_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"Social account already linked: {platform}:{account_id}"
        super().__init__(message, "SOCIAL_ACCOUNT_LINKED", details)


class SocialVerificationFailedError(DEIDException):
    """Raised when social account verification fails."""

    def __init__(self, platform: str, details: Optional[Dict[str, Any]] = None):
        message = f"Social account verification failed: {platform}"
        super().__init__(message, "SOCIAL_VERIFICATION_FAILED", details)


class SocialAccountLimitExceededError(DEIDException):
    """Raised when user tries to link more social accounts than allowed."""

    def __init__(self, max_accounts: int, details: Optional[Dict[str, Any]] = None):
        message = f"Maximum social account limit exceeded: {max_accounts}"
        super().__init__(message, "SOCIAL_ACCOUNT_LIMIT_EXCEEDED", details)


# IPFS & Metadata
class IPFSError(DEIDException):
    """Raised when IPFS operations fail."""

    def __init__(self, message: str = "IPFS operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "IPFS_ERROR", details)


class MetadataTooLargeError(DEIDException):
    """Raised when metadata exceeds size limit."""

    def __init__(self, size: int, max_size: int, details: Optional[Dict[str, Any]] = None):
        message = f"Metadata too large: {size} bytes (max: {max_size})"
        super().__init__(message, "METADATA_TOO_LARGE", details)


class InvalidMetadataFormatError(DEIDException):
    """Raised when metadata format is invalid."""

    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__("Invalid metadata format", "INVALID_METADATA", details)


# Blockchain Operations
class BlockchainError(DEIDException):
    """Raised when blockchain operations fail."""

    def __init__(self, message: str = "Blockchain operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "BLOCKCHAIN_ERROR", details)


class ContractCallFailedError(DEIDException):
    """Raised when smart contract call fails."""

    def __init__(self, contract_address: str, method: str, details: Optional[Dict[str, Any]] = None):
        message = f"Contract call failed: {contract_address}.{method}"
        super().__init__(message, "CONTRACT_CALL_FAILED", details)


class TransactionFailedError(DEIDException):
    """Raised when blockchain transaction fails."""

    def __init__(self, tx_hash: str, details: Optional[Dict[str, Any]] = None):
        message = f"Transaction failed: {tx_hash}"
        super().__init__(message, "TRANSACTION_FAILED", details)


# Database Operations
class DatabaseError(DEIDException):
    """Raised when database operations fail."""

    def __init__(self, message: str = "Database operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DATABASE_ERROR", details)


class CacheError(DEIDException):
    """Raised when cache operations fail."""

    def __init__(self, message: str = "Cache operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CACHE_ERROR", details)


# Validation
class ValidationError(DEIDException):
    """Raised when input validation fails."""

    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", details)


# Rate Limiting
class RateLimitExceededError(DEIDException):
    """Raised when rate limit is exceeded."""

    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__("Rate limit exceeded", "RATE_LIMIT_EXCEEDED", details)


# Token Management
class TokenExpiredError(DEIDException):
    """Raised when a JWT token has expired."""

    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__("Token has expired", "TOKEN_EXPIRED", details)


class InvalidTokenError(DEIDException):
    """Raised when a JWT token is invalid."""

    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__("Invalid token", "INVALID_TOKEN", details)


# Gamification
class AchievementNotFoundError(DEIDException):
    """Raised when an achievement is not found."""

    def __init__(self, achievement_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"Achievement not found: {achievement_id}"
        super().__init__(message, "ACHIEVEMENT_NOT_FOUND", details)


class TaskNotFoundError(DEIDException):
    """Raised when a task is not found."""

    def __init__(self, task_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"Task not found: {task_id}"
        super().__init__(message, "TASK_NOT_FOUND", details)


def create_http_exception(
    exc: DEIDException,
    status_code: int = status.HTTP_400_BAD_REQUEST
) -> HTTPException:
    """
    Convert a DEIDException to an HTTPException.

    Args:
        exc: DEIDException instance
        status_code: HTTP status code

    Returns:
        HTTPException: FastAPI HTTP exception
    """
    return HTTPException(
        status_code=status_code,
        detail={
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    )


def get_exception_status_code(exc: DEIDException) -> int:
    """
    Get the appropriate HTTP status code for a DEIDException.

    Args:
        exc: DEIDException instance

    Returns:
        int: HTTP status code
    """
    status_mapping = {
        # Authentication & Authorization
        "AUTH_ERROR": status.HTTP_401_UNAUTHORIZED,
        "AUTHZ_ERROR": status.HTTP_403_FORBIDDEN,
        "SSO_ERROR": status.HTTP_401_UNAUTHORIZED,
        "SESSION_EXPIRED": status.HTTP_401_UNAUTHORIZED,

        # Identity Management
        "IDENTITY_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "USERNAME_TAKEN": status.HTTP_409_CONFLICT,
        "INVALID_USERNAME": status.HTTP_400_BAD_REQUEST,

        # Wallet Management
        "WALLET_ALREADY_LINKED": status.HTTP_409_CONFLICT,
        "INVALID_WALLET_ADDRESS": status.HTTP_400_BAD_REQUEST,
        "UNSUPPORTED_CHAIN": status.HTTP_400_BAD_REQUEST,
        "WALLET_LIMIT_EXCEEDED": status.HTTP_400_BAD_REQUEST,

        # Signature & Verification
        "SIGNATURE_ERROR": status.HTTP_400_BAD_REQUEST,
        "INVALID_SIGNATURE": status.HTTP_400_BAD_REQUEST,
        "NONCE_EXPIRED": status.HTTP_400_BAD_REQUEST,

        # Social Account Verification
        "SOCIAL_ACCOUNT_LINKED": status.HTTP_409_CONFLICT,
        "SOCIAL_VERIFICATION_FAILED": status.HTTP_400_BAD_REQUEST,
        "SOCIAL_ACCOUNT_LIMIT_EXCEEDED": status.HTTP_400_BAD_REQUEST,

        # IPFS & Metadata
        "IPFS_ERROR": status.HTTP_502_BAD_GATEWAY,
        "METADATA_TOO_LARGE": status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        "INVALID_METADATA": status.HTTP_400_BAD_REQUEST,

        # Blockchain Operations
        "BLOCKCHAIN_ERROR": status.HTTP_502_BAD_GATEWAY,
        "CONTRACT_CALL_FAILED": status.HTTP_502_BAD_GATEWAY,
        "TRANSACTION_FAILED": status.HTTP_502_BAD_GATEWAY,

        # Database Operations
        "DATABASE_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "CACHE_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,

        # Validation
        "VALIDATION_ERROR": status.HTTP_422_UNPROCESSABLE_ENTITY,

        # Rate Limiting
        "RATE_LIMIT_EXCEEDED": status.HTTP_429_TOO_MANY_REQUESTS,

        # Token Management
        "TOKEN_EXPIRED": status.HTTP_401_UNAUTHORIZED,
        "INVALID_TOKEN": status.HTTP_401_UNAUTHORIZED,

        # Gamification
        "ACHIEVEMENT_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "TASK_NOT_FOUND": status.HTTP_404_NOT_FOUND,
    }

    return status_mapping.get(exc.error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
