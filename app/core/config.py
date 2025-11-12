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
    # TODO: Dev Config for Testing
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "https://app.de-id.xyz",
        "https://www.de-id.xyz",
        "http://localhost:8000",
    ]
    ALLOWED_HOSTS: List[str] = [
        "localhost",
        "app.de-id.xyz",
        "api.de-id.xyz",
        "www.de-id.xyz",
    ]

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

    # Blockchain Configuration
    # Supports both Monad and Ethereum Sepolia
    TESTNET_RPC_URL: Optional[str] = (
        None  # Sepolia: https://eth-sepolia.public.blastapi.io
    )
    EVM_RPC_URL: str = "https://testnet-rpc.monad.xyz"  # Default: Monad testnet
    EVM_CHAIN_ID: int = 41434  # Monad: 41434, Sepolia: 11155111
    EVM_CONTRACT_ADDRESS: Optional[str] = None
    EVM_CONTRACT_ABI_PATH: str = "contracts/DeID.json"

    # Private key for signing (from .env)
    EVM_PRIVATE_KEY: Optional[str] = None

    # Blockchain Validation RPC URLs
    ETHEREUM_RPC_URL: str = "https://eth-mainnet.public.blastapi.io"
    BSC_RPC_URL: str = "https://bsc-mainnet.public.blastapi.io"
    BASE_RPC_URL: str = "https://base-mainnet.public.blastapi.io"

    @property
    def ACTIVE_RPC_URL(self) -> str:
        """Get active RPC URL (TESTNET_RPC_URL takes priority over EVM_RPC_URL)."""
        return self.TESTNET_RPC_URL or self.EVM_RPC_URL

    # IPFS Configuration
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

    # IPFS Configuration
    IPFS_GATEWAY_URL_POST: str = "http://35.247.142.76:5001/api/v0/add"
    IPFS_GATEWAY_URL_GET: str = "http://35.247.142.76:8080/ipfs"

    # Smart Contract Configuration
    PROXY_ADDRESS: Optional[str] = None

    # BLOCKCHAIN RPC
    ETHEREUM_RPC_URL: str = "https://eth-mainnet.public.blastapi.io"
    BSC_RPC_URL: str = "https://bsc-mainnet.public.blastapi.io"
    BASE_RPC_URL: str = "https://base-mainnet.public.blastapi.io"

    # Cookie Configuration
    COOKIE_DOMAIN: Optional[str] = (
        None  # None = host-only cookie, or set to ".de-id.xyz" for subdomain sharing
    )
    COOKIE_SAMESITE: str = "lax"  # "none", "lax", or "strict"
    COOKIE_SECURE: bool = True  # Must be True when samesite="none"
    COOKIE_HTTPONLY: bool = True
    COOKIE_PATH: str = "/"

    def get_cookie_domain(self) -> Optional[str]:
        """
        Get cookie domain based on environment.
        For cross-origin cookies (localhost -> api.de-id.xyz), domain should be None.
        For same-domain cookies (app.de-id.xyz -> api.de-id.xyz), use ".de-id.xyz".
        """
        # If explicitly set, use it
        if self.COOKIE_DOMAIN:
            return self.COOKIE_DOMAIN

        # For production with subdomain sharing, use domain cookie
        if self.ENVIRONMENT == "production":
            # Check if frontend is on a subdomain of de-id.xyz
            frontend_origins = [
                origin for origin in self.ALLOWED_ORIGINS if "de-id.xyz" in origin
            ]
            if frontend_origins:
                return ".de-id.xyz"

        # For development or cross-origin scenarios, don't set domain
        return None

    def get_effective_cors_origins(self) -> List[str]:
        """
        Get effective CORS origins based on environment.
        Ensures all necessary origins are included for cookie support.
        """
        origins = list(self.ALLOWED_ORIGINS)

        # Add common localhost ports if not already present
        common_ports = [3000, 5173, 8080, 8000]
        for port in common_ports:
            origin = f"http://localhost:{port}"
            if origin not in origins:
                origins.append(origin)

        return origins

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
