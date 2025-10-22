"""
IPFS Service for uploading badge metadata.
Handles uploading JSON metadata to IPFS gateway.
"""

import json
from typing import Dict, Optional

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class IPFSService:
    """Service for IPFS operations."""

    def __init__(self):
        """Initialize IPFS service."""
        self.ipfs_add_url = settings.IPFS_GATEWAY_URL_POST
        self.ipfs_gateway = settings.IPFS_GATEWAY_URL_GET

    async def upload_badge_metadata(self, badge_data: Dict) -> Optional[str]:
        """
        Upload badge metadata to IPFS.

        Args:
            badge_data: Badge metadata dictionary

        Returns:
            IPFS hash (CID) or None if failed
        """
        try:
            # Convert badge data to JSON string
            json_data = json.dumps(badge_data, indent=2)

            # Prepare multipart form data
            files = {
                "file": (
                    "metadata.json",
                    json_data.encode("utf-8"),
                    "application/json",
                )
            }

            logger.info(f"Uploading to IPFS: {self.ipfs_add_url}")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.ipfs_add_url, files=files)

                if response.status_code == 200:
                    result = response.json()
                    ipfs_hash = result.get("Hash")
                    logger.info(f"Uploaded to IPFS: {ipfs_hash}")
                    return ipfs_hash
                else:
                    logger.error(
                        f"Failed to upload to IPFS: {response.status_code} - {response.text}"
                    )
                    return None

        except Exception as e:
            logger.error(f"Error uploading to IPFS: {e}", exc_info=True)
            return None

    def get_ipfs_url(self, ipfs_hash: str) -> str:
        """
        Get the full IPFS URL for a hash.

        Args:
            ipfs_hash: IPFS hash (CID)

        Returns:
            Full IPFS URL
        """
        return f"ipfs://{ipfs_hash}"


# Global IPFS service instance
ipfs_service = IPFSService()
