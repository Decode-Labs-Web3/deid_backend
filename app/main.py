"""
DEID Backend - FastAPI Application
Main entry point for the DEID (Decentralized Identity) backend service.
Handles decentralized identity management, cross-chain wallet linking, and SSO integration.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.logging import get_logger, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    setup_logging()
    # TODO: Initialize MongoDB when database layer is ready
    # await init_mongodb()
    yield
    # Shutdown
    # Add any cleanup logic here if needed


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance
    """
    app = FastAPI(
        title="DEID Backend",
        description="Decentralized Identity Management Backend API - Cross-chain wallet linking, IPFS metadata, social verification, and SSO integration",
        version="1.0.0",
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
        openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
        lifespan=lifespan,
    )

    # CORS middleware - REQUIRED for cross-origin cookies
    cors_origins = settings.get_effective_cors_origins()
    logger.info(f"CORS configured with origins: {cors_origins}")
    logger.info(f"CORS allow_credentials: True (required for cookies)")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,  # CRITICAL: Must be True for cookies to work cross-origin
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    # Trusted host middleware
    # Note: This only validates the Host header, not the Origin header
    # CORS middleware handles Origin validation separately
    if settings.ENVIRONMENT == "production":
        logger.info(
            f"TrustedHost middleware enabled with hosts: {settings.ALLOWED_HOSTS}"
        )
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS,
        )
    else:
        logger.info("TrustedHost middleware disabled (development mode)")

    # Decode Backend Integration
    from app.api.routers import (
        decode_router,
        social_link_router,
        sync_profile_router,
        task_router,
    )

    app.include_router(
        decode_router.router,
        prefix="/api/v1/decode",
        tags=["Decode Backend Integration"],
    )
    app.include_router(
        sync_profile_router.router, prefix="/api/v1/sync", tags=["Sync Profile"]
    )
    app.include_router(
        social_link_router.router,
        prefix="/api/v1/social",
        tags=["Social Link Verification"],
    )
    app.include_router(
        task_router.router, prefix="/api/v1/task", tags=["Task & Badge Management"]
    )

    # Mount static files
    app.mount("/", StaticFiles(directory="public", html=True), name="static")

    @app.get("/")
    async def root():
        """Root endpoint for health check."""
        return {
            "message": "DEID Backend API",
            "version": "1.0.0",
            "status": "healthy",
            "features": [
                "Decentralized Name Service",
                "Cross-Chain Wallet Linking",
                "IPFS-Based Metadata",
                "Social Account Verification",
                "Decode Backend Integration",
                "Trust & Verification System",
                "Gamification & Achievements",
            ],
        }

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "environment": settings.ENVIRONMENT,
            "monad_testnet_chain_id": settings.EVM_CHAIN_ID,
            "features_enabled": {
                "decode_backend": bool(settings.DECODE_PORTAL_CLIENT_ID),
                "ipfs": bool(settings.IPFS_GATEWAY_URL_POST),
                "monad_testnet": True,
            },
        }

    return app


# Create the FastAPI app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level="info",
    )
