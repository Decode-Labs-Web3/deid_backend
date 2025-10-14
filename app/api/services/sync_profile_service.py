"""
Sync Profile Service.
Builds calldata for DEiDProfile.createProfile via proxy after uploading metadata to IPFS.
"""

from typing import Dict, Any, Optional
import json
import httpx

from eth_abi import encode as abi_encode
from eth_utils import to_checksum_address
from app.infrastructure.blockchain.selectors import selector_for

from app.core.config import settings
from app.core.logging import get_logger
from app.api.services.decode_service import DecodeService
from app.infrastructure.blockchain.signature_utils import sign_message_with_private_key

logger = get_logger(__name__)


class SyncProfileService:
    """Service to prepare on-chain profile creation calldata."""

    def __init__(self) -> None:
        self.decode_service = DecodeService()

    async def upload_metadata_to_ipfs(self, metadata: Dict[str, Any]) -> Dict[str, str]:
        """Upload JSON metadata to Pinata if configured, else to self-hosted IPFS node."""
        jsonable_metadata = json.loads(json.dumps(metadata, default=str))

        ipfs_url = settings.IPFS_GATEWAY_URL_POST
        files = {
            "file": (
                "metadata.json",
                json.dumps(jsonable_metadata, default=str),
                "application/json",
            )
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(ipfs_url, files=files)
            resp.raise_for_status()
            data = resp.json()
            ipfs_hash = data.get("Hash")
            return {"uri": f"ipfs://{ipfs_hash}", "hash": ipfs_hash}

    async def build_create_profile_calldata(
        self,
        session_user_id: str,
        user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build calldata for createProfile(string username, string metadataURI, bytes validatorSignature).

        Args:
            session_user_id: The current authenticated user id (Decode ID)
            user_profile: The fetched user profile payload from Decode

        Returns:
            Dict containing method, params, calldata (bytes hex), and metadataURI
        """
        data = user_profile.get("data") or {}
        username: str = data.get("username")
        display_name: Optional[str] = data.get("display_name")
        bio: Optional[str] = data.get("bio")
        avatar_ipfs_hash: Optional[str] = data.get("avatar_ipfs_hash")
        primary_wallet = (data.get("primary_wallet") or {})
        wallet_address: str = primary_wallet.get("address")
        wallets = data.get("wallets") or []

        if not username:
            raise ValueError("username missing from Decode profile")
        if not wallet_address:
            raise ValueError("primary wallet address missing from Decode profile")

        # Build metadata JSON
        metadata: Dict[str, Any] = {
            "username": username,
            "display_name": display_name,
            "bio": bio,
            "avatar_ipfs_hash": avatar_ipfs_hash,
            "primary_wallet": primary_wallet,
            "wallets": wallets,
            "decode_user_id": session_user_id,
        }

        # Upload to IPFS and form URI
        print(f"Uploading metadata to IPFS")
        ipfs_res = await self.upload_metadata_to_ipfs(metadata)
        metadata_uri = ipfs_res["uri"]
        ipfs_hash = ipfs_res["hash"]
        print(f"Metadata URI: {metadata_uri}")

        # Backend validator signature (server signs ipfs_hash to attest validation)
        validator_signature = None
        validator_address = None
        validator_message_hash = None

        print(f"EVM_PRIVATE_KEY configured: {(settings.EVM_PRIVATE_KEY)}")
        if settings.EVM_PRIVATE_KEY:
            try:
                print(f"Signing IPFS hash: {ipfs_hash}")
                validator_signature, validator_address, validator_message_hash = sign_message_with_private_key(
                    metadata_uri,
                    settings.EVM_PRIVATE_KEY,
                )
                print(f"Signature created successfully: {validator_signature[:20]}...")
                print(f"Signer address: {validator_address}")
            except Exception as e:
                logger.error(f"Validator signing failed: {e}")
                print(f"Signature error details: {e}")
        else:
            print("EVM_PRIVATE_KEY not configured - skipping signature")

        # Prepare calldata for createProfile(string,string,bytes)
        checksum_wallet = to_checksum_address(wallet_address)
        method_selector = bytes.fromhex(selector_for("createProfile(string,string,bytes)")[2:])
        signature_bytes = bytes.fromhex(validator_signature[2:]) if validator_signature else b""
        args_encoded = abi_encode([
            "string",
            "string",
            "bytes",
        ], [
            username,
            metadata_uri,
            signature_bytes,
        ])
        calldata = "0x" + (method_selector + args_encoded).hex()

        return {
            "method": "createProfile(string,string,bytes)",
            "params": {
                "wallet": checksum_wallet,
                "username": username,
                "metadataURI": metadata_uri,
            },
            "calldata": calldata,
            "metadata": metadata,
            "ipfs_hash": ipfs_hash,
            "validator": {
                "signature": validator_signature,
                "signer": validator_address,
                "payload": ipfs_hash,
                "message_hash": validator_message_hash,
                "type": "personal_sign",
            },
        }

    async def create_profile_prepare(self, user_id: str) -> Dict[str, Any]:
        """Fetch user data from Decode and return calldata + metadata URI."""
        # Reuse decode service to fetch profile by user id
        resp = await self.decode_service.get_my_profile(user_id)
        print(f"Profile response")
        if not resp or not resp.success or not resp.data:
            raise ValueError("Failed to fetch user profile from Decode")

        # Convert DTO-like response to dict for uniform processing
        if hasattr(resp, "model_dump"):
            profile_dict = resp.model_dump()
        else:
            profile_dict = dict(resp)

        print(f"Profile dictionary")

        return await self.build_create_profile_calldata(user_id, profile_dict)

    async def build_update_profile_calldata(
        self,
        session_user_id: str,
        user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build calldata for updateProfile(string metadataURI, bytes validatorSignature).

        Args:
            session_user_id: The current authenticated user id (Decode ID)
            user_profile: The fetched user profile payload from Decode

        Returns:
            Dict containing method, params, calldata (bytes hex), and metadataURI
        """
        data = user_profile.get("data") or {}
        username: str = data.get("username")
        display_name: Optional[str] = data.get("display_name")
        bio: Optional[str] = data.get("bio")
        avatar_ipfs_hash: Optional[str] = data.get("avatar_ipfs_hash")
        primary_wallet = (data.get("primary_wallet") or {})
        wallet_address: str = primary_wallet.get("address")
        wallets = data.get("wallets") or []

        if not username:
            raise ValueError("username missing from Decode profile")
        if not wallet_address:
            raise ValueError("primary wallet address missing from Decode profile")

        # Build metadata JSON
        metadata: Dict[str, Any] = {
            "username": username,
            "display_name": display_name,
            "bio": bio,
            "avatar_ipfs_hash": avatar_ipfs_hash,
            "primary_wallet": primary_wallet,
            "wallets": wallets,
            "decode_user_id": session_user_id,
        }

        # Upload to IPFS and form URI
        print(f"Uploading updated metadata to IPFS")
        ipfs_res = await self.upload_metadata_to_ipfs(metadata)
        metadata_uri = ipfs_res["uri"]
        ipfs_hash = ipfs_res["hash"]
        print(f"Updated metadata URI: {metadata_uri}")

        # Backend validator signature (server signs ipfs_hash to attest validation)
        validator_signature = None
        validator_address = None
        validator_message_hash = None
        if settings.EVM_PRIVATE_KEY:
            try:
                validator_signature, validator_address, validator_message_hash = sign_message_with_private_key(
                    metadata_uri,
                    settings.EVM_PRIVATE_KEY,
                )
            except Exception as e:
                logger.error(f"Validator signing failed: {e}")

        # Prepare calldata for updateProfile(string,bytes)
        method_selector = bytes.fromhex(selector_for("updateProfile(string,bytes)")[2:])
        signature_bytes = bytes.fromhex(validator_signature[2:]) if validator_signature else b""
        args_encoded = abi_encode([
            "string",
            "bytes",
        ], [
            metadata_uri,
            signature_bytes,
        ])
        calldata = "0x" + (method_selector + args_encoded).hex()

        return {
            "method": "updateProfile(string,bytes)",
            "params": {
                "metadataURI": metadata_uri,
            },
            "calldata": calldata,
            "metadata": metadata,
            "ipfs_hash": ipfs_hash,
            "validator": {
                "signature": validator_signature,
                "signer": validator_address,
                "payload": ipfs_hash,
                "message_hash": validator_message_hash,
                "type": "personal_sign",
            },
        }

    async def update_profile_prepare(self, user_id: str) -> Dict[str, Any]:
        """Fetch user data from Decode and return update calldata + metadata URI."""
        # Reuse decode service to fetch profile by user id
        resp = await self.decode_service.get_my_profile(user_id)
        print(f"Update profile response")
        if not resp or not resp.success or not resp.data:
            raise ValueError("Failed to fetch user profile from Decode")

        # Convert DTO-like response to dict for uniform processing
        if hasattr(resp, "model_dump"):
            profile_dict = resp.model_dump()
        else:
            profile_dict = dict(resp)

        print(f"Update profile dictionary")

        return await self.build_update_profile_calldata(user_id, profile_dict)
