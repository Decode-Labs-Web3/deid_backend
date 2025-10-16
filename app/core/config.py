"""
Configuration management for the DEID Backend application.
Handles environment variables and application settings for decentralized identity management.
"""

import os
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "DEID Backend"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-change-in-production"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]

    # Database - MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "deid_backend"
    MONGODB_USERNAME: Optional[str] = None
    MONGODB_PASSWORD: Optional[str] = None

    # MongoDB Environment Variables (from .env)
    MONGO_URI: Optional[str] = None
    MONGO_DB_NAME: Optional[str] = None
    MONGO_USER: Optional[str] = None
    MONGO_PASSWORD: Optional[str] = None

    # Redis for session management and caching
    REDIS_URI: str = "redis://localhost:6379"
    REDIS_DB: int = 0
    SESSION_EXPIRE_DAYS: int = 30

    # JWT for internal API tokens
    JWT_SECRET_KEY: str = "your-jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Monad Testnet Support
    EVM_RPC_URL: str = "https://testnet-rpc.monad.xyz"
    EVM_CHAIN_ID: int = 41434  # Monad testnet chain ID
    EVM_CONTRACT_ADDRESS: Optional[str] = None
    EVM_CONTRACT_ABI_PATH: str = "contracts/DeID.json"

    # Private key for signing (from .env)
    EVM_PRIVATE_KEY: Optional[str] = None

    # IPFS Configuration
    IPFS_URL: str = "http://localhost:5001"
    IPFS_GATEWAY_URL_POST: str = "https://ipfs.de-id.xyz/add"
    # Pinata credentials (preferred names)
    IPFS_PINATA_API_KEY: Optional[str] = None
    IPFS_PINATA_SECRET: Optional[str] = None
    IPFS_ACCESS_TOKEN: Optional[str] = None  # Pinata JWT (preferred when present)
    # Alternate env names support (to avoid extra inputs error)
    IPFS_API_KEY: Optional[str] = None
    IPFS_API_SECRET: Optional[str] = None

    # Decode Portal SSO Integration
    DECODE_PORTAL_BASE_URL: str = "https://portal.decode.com"
    DECODE_PORTAL_CLIENT_ID: str = "your-decode-client-id"
    DECODE_PORTAL_CLIENT_SECRET: str = "your-decode-client-secret"
    DECODE_PORTAL_REDIRECT_URI: str = (
        "http://localhost:8000/api/v1/auth/decode/callback"
    )

    # Decode Backend URL
    DECODE_BACKEND_URL: str = "http://localhost:8001"

    # Decode Auth Service
    DECODE_AUTH_HOST: str = "localhost"
    DECODE_AUTH_PORT: int = 4001

    # Simple Identity Management
    DEID_DOMAIN_SUFFIX: str = ".deid"
    PROFILE_METADATA_MAX_SIZE: int = 1024 * 1024  # 1MB

    # Security
    BCRYPT_ROUNDS: int = 12
    SIGNATURE_MESSAGE_PREFIX: str = "DEID Identity Management"
    NONCE_EXPIRE_MINUTES: int = 10

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Sentry (optional)
    SENTRY_DSN: Optional[str] = None

    # Social Link OAuth Configuration
    # Discord OAuth
    DISCORD_CLIENT_ID: Optional[str] = None
    DISCORD_CLIENT_SECRET: Optional[str] = None
    DISCORD_REDIRECT_URI: str = "http://localhost:8000/api/v1/social/discord/callback"

    # Github OAuth
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    GITHUB_REDIRECT_URI: str = "http://localhost:8000/api/v1/social/github/callback"

    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/social/google/callback"

    # Facebook OAuth
    FACEBOOK_CLIENT_ID: Optional[str] = None
    FACEBOOK_CLIENT_SECRET: Optional[str] = None
    FACEBOOK_REDIRECT_URI: str = "http://localhost:8000/api/v1/social/facebook/callback"

    # Twitter OAuth
    X_CLIENT_ID: Optional[str] = None
    X_CLIENT_SECRET: Optional[str] = None
    X_REDIRECT_URI: str = "http://localhost:8000/api/v1/social/x/callback"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v):
        """Parse allowed hosts from string or list."""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment setting."""
        allowed_envs = ["development", "staging", "production"]
        if v not in allowed_envs:
            raise ValueError(f"Environment must be one of {allowed_envs}")
        return v

    def get_evm_config(self) -> Dict[str, Any]:
        """Get Monad testnet configuration."""
        return {
            "name": "Monad Testnet",
            "rpc_url": self.EVM_RPC_URL,
            "chain_id": self.EVM_CHAIN_ID,
            "contract_address": self.EVM_CONTRACT_ADDRESS,
            "private_key": self.EVM_PRIVATE_KEY,
            "explorer": "https://testnet-explorer.monad.xyz",
        }

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def model_post_init(self, __context: Any) -> None:  # type: ignore[override]
        """Normalize alternate env var names to pinata fields."""
        if not self.IPFS_PINATA_API_KEY and self.IPFS_API_KEY:
            self.IPFS_PINATA_API_KEY = self.IPFS_API_KEY
        if not self.IPFS_PINATA_SECRET and self.IPFS_API_SECRET:
            self.IPFS_PINATA_SECRET = self.IPFS_API_SECRET


# Create global settings instance
settings = Settings()


def get_mongodb_url() -> str:
    """
    Get MongoDB connection URL with authentication if credentials are provided.

    Returns:
        str: MongoDB connection URL
    """
    # Use MONGO_URI from environment if available
    if settings.MONGO_URI:
        return settings.MONGO_URI

    # Fallback to MONGODB_URL with authentication
    if settings.MONGODB_USERNAME and settings.MONGODB_PASSWORD:
        # Parse the base URL to add authentication
        base_url = settings.MONGODB_URL.replace("mongodb://", "")
        if "@" not in base_url:  # No existing auth in URL
            return f"mongodb://{settings.MONGODB_USERNAME}:{settings.MONGODB_PASSWORD}@{base_url}"

    return settings.MONGODB_URL


def get_mongodb_database_name() -> str:
    """
    Get MongoDB database name.

    Returns:
        str: MongoDB database name
    """
    # Use MONGO_DB_NAME from environment if available
    if settings.MONGO_DB_NAME:
        return settings.MONGO_DB_NAME

    return settings.MONGODB_DATABASE


def is_production() -> bool:
    """Check if running in production environment."""
    return settings.ENVIRONMENT == "production"


def is_development() -> bool:
    """Check if running in development environment."""
    return settings.ENVIRONMENT == "development"


def get_evm_chain_id() -> int:
    """Get the EVM chain ID."""
    return settings.EVM_CHAIN_ID
