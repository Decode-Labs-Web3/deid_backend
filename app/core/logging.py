"""
Logging configuration for the DEID Backend application.
Provides structured logging for decentralized identity management operations.
"""

import logging
import sys
from typing import Any, Dict
import structlog
from structlog.stdlib import LoggerFactory

from app.core.config import settings


def setup_logging() -> None:
    """
    Configure structured logging for the application.
    Sets up different log formats for development and production environments.
    """

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            _get_processor(),
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )

    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("motor").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def _get_processor():
    """
    Get the appropriate processor based on environment.

    Returns:
        Processor function for structlog
    """
    if settings.ENVIRONMENT == "production":
        return structlog.processors.JSONRenderer()
    else:
        return structlog.dev.ConsoleRenderer(colors=True)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        structlog.stdlib.BoundLogger: Configured logger instance
    """
    return structlog.get_logger(name)


class LoggerMixin:
    """Mixin class to add logging capabilities to any class."""

    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """Get logger instance for this class."""
        return get_logger(self.__class__.__module__ + "." + self.__class__.__name__)


# Specialized logging functions for DEID operations

def log_identity_operation(
    operation: str,
    identity_id: str = None,
    username: str = None,
    wallet_address: str = None,
    **kwargs
) -> None:
    """
    Log identity management operations.

    Args:
        operation: Operation type (register, update, delete, link_wallet, etc.)
        identity_id: DEID identity ID
        username: DEID username
        wallet_address: Wallet address involved
        **kwargs: Additional context
    """
    logger = get_logger("identity.operation")
    logger.info(
        "Identity operation",
        operation=operation,
        identity_id=identity_id,
        username=username,
        wallet_address=wallet_address,
        **kwargs
    )


def log_wallet_operation(
    operation: str,
    wallet_address: str,
    chain_id: int = None,
    user_id: str = None,
    **kwargs
) -> None:
    """
    Log wallet-related operations.

    Args:
        operation: Operation type (link, unlink, verify, sign)
        wallet_address: Wallet address
        chain_id: Blockchain chain ID
        user_id: User ID
        **kwargs: Additional context
    """
    logger = get_logger("wallet.operation")
    logger.info(
        "Wallet operation",
        operation=operation,
        wallet_address=wallet_address,
        chain_id=chain_id,
        user_id=user_id,
        **kwargs
    )


def log_social_verification(
    platform: str,
    account_id: str,
    user_id: str = None,
    wallet_address: str = None,
    status: str = "success",
    **kwargs
) -> None:
    """
    Log social account verification operations.

    Args:
        platform: Social platform (twitter, discord, github, telegram)
        account_id: Social account identifier
        user_id: User ID
        wallet_address: Wallet address
        status: Verification status
        **kwargs: Additional context
    """
    logger = get_logger("social.verification")
    logger.info(
        "Social verification",
        platform=platform,
        account_id=account_id,
        user_id=user_id,
        wallet_address=wallet_address,
        status=status,
        **kwargs
    )


def log_blockchain_transaction(
    tx_hash: str,
    chain_id: int,
    contract_address: str = None,
    method: str = None,
    user_id: str = None,
    **kwargs
) -> None:
    """
    Log blockchain transaction details.

    Args:
        tx_hash: Transaction hash
        chain_id: Blockchain chain ID
        contract_address: Smart contract address
        method: Contract method called
        user_id: User ID
        **kwargs: Additional transaction context
    """
    logger = get_logger("blockchain.transaction")
    logger.info(
        "Blockchain transaction",
        tx_hash=tx_hash,
        chain_id=chain_id,
        contract_address=contract_address,
        method=method,
        user_id=user_id,
        **kwargs
    )


def log_ipfs_operation(
    operation: str,
    ipfs_hash: str = None,
    file_size: int = None,
    user_id: str = None,
    **kwargs
) -> None:
    """
    Log IPFS operations.

    Args:
        operation: Operation type (upload, pin, unpin, retrieve)
        ipfs_hash: IPFS hash
        file_size: File size in bytes
        user_id: User ID
        **kwargs: Additional context
    """
    logger = get_logger("ipfs.operation")
    logger.info(
        "IPFS operation",
        operation=operation,
        ipfs_hash=ipfs_hash,
        file_size=file_size,
        user_id=user_id,
        **kwargs
    )


def log_sso_operation(
    operation: str,
    user_id: str = None,
    session_id: str = None,
    status: str = "success",
    **kwargs
) -> None:
    """
    Log SSO operations.

    Args:
        operation: Operation type (login, logout, validate, create_session)
        user_id: User ID
        session_id: Session ID
        status: Operation status
        **kwargs: Additional context
    """
    logger = get_logger("sso.operation")
    logger.info(
        "SSO operation",
        operation=operation,
        user_id=user_id,
        session_id=session_id,
        status=status,
        **kwargs
    )


def log_achievement_event(
    achievement_id: str,
    user_id: str,
    achievement_type: str = None,
    points_earned: int = None,
    **kwargs
) -> None:
    """
    Log achievement and gamification events.

    Args:
        achievement_id: Achievement identifier
        user_id: User ID
        achievement_type: Type of achievement
        points_earned: Points earned
        **kwargs: Additional context
    """
    logger = get_logger("achievement.event")
    logger.info(
        "Achievement event",
        achievement_id=achievement_id,
        user_id=user_id,
        achievement_type=achievement_type,
        points_earned=points_earned,
        **kwargs
    )


def log_task_completion(
    task_id: str,
    user_id: str,
    reward_amount: int = None,
    task_type: str = None,
    **kwargs
) -> None:
    """
    Log task completion events.

    Args:
        task_id: Task identifier
        user_id: User ID
        reward_amount: Reward amount earned
        task_type: Type of task
        **kwargs: Additional context
    """
    logger = get_logger("task.completion")
    logger.info(
        "Task completion",
        task_id=task_id,
        user_id=user_id,
        reward_amount=reward_amount,
        task_type=task_type,
        **kwargs
    )


def log_reputation_change(
    user_id: str,
    old_score: float,
    new_score: float,
    reason: str = None,
    **kwargs
) -> None:
    """
    Log reputation score changes.

    Args:
        user_id: User ID
        old_score: Previous reputation score
        new_score: New reputation score
        reason: Reason for change
        **kwargs: Additional context
    """
    logger = get_logger("reputation.change")
    logger.info(
        "Reputation change",
        user_id=user_id,
        old_score=old_score,
        new_score=new_score,
        reason=reason,
        **kwargs
    )


def log_claim_verification(
    claim_id: str,
    verifier_id: str,
    user_id: str,
    claim_type: str,
    status: str,
    **kwargs
) -> None:
    """
    Log claim verification events.

    Args:
        claim_id: Claim identifier
        verifier_id: Verifier identifier
        user_id: User ID
        claim_type: Type of claim
        status: Verification status
        **kwargs: Additional context
    """
    logger = get_logger("claim.verification")
    logger.info(
        "Claim verification",
        claim_id=claim_id,
        verifier_id=verifier_id,
        user_id=user_id,
        claim_type=claim_type,
        status=status,
        **kwargs
    )


def log_error(error: Exception, context: Dict[str, Any] = None) -> None:
    """
    Log an error with context.

    Args:
        error: Exception instance
        context: Additional context information
    """
    logger = get_logger("error")
    logger.error(
        "An error occurred",
        error=str(error),
        error_type=type(error).__name__,
        context=context or {},
        exc_info=True
    )


def log_request(method: str, url: str, status_code: int, duration: float, **kwargs) -> None:
    """
    Log HTTP request details.

    Args:
        method: HTTP method
        url: Request URL
        status_code: Response status code
        duration: Request duration in seconds
        **kwargs: Additional context to log
    """
    logger = get_logger("http.request")
    logger.info(
        "HTTP request completed",
        method=method,
        url=url,
        status_code=status_code,
        duration=duration,
        **kwargs
    )
