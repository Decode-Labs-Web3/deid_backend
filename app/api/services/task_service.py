"""
Task Service Layer.
Contains business logic for task management and smart contract integration.
"""

import json
from typing import Dict, List, Optional, Tuple

from app.api.dto.task_dto import (
    BadgeDetail,
    OriginTaskCreateRequestDTO,
    TaskValidationDataDTO,
    TaskValidationResponseDTO,
)
from app.core.config import settings
from app.core.decode_external_service import get_decode_profile_external
from app.core.logging import get_logger
from app.domain.models.task import (
    BlockchainNetwork,
    TaskModel,
    TaskValidationModel,
    ValidationType,
)
from app.domain.repositories.task_repository import task_repository
from app.infrastructure.blockchain.balance_validator import balance_validator
from app.infrastructure.blockchain.contract_client import ContractClient
from app.infrastructure.blockchain.signature_utils import (
    sign_message_with_private_key,
    sign_user_task_message,
)
from app.infrastructure.ipfs.ipfs_service import ipfs_service

logger = get_logger(__name__)


class TaskService:
    """Service class for task management."""

    def __init__(self):
        """Initialize task service."""
        self.contract_client = None

    async def _get_contract_client(self) -> ContractClient:
        """Get or create contract client instance."""
        if not self.contract_client:
            # Load BadgeSystem ABI
            with open(
                "app/contracts/verification/BadgeSystem.sol/BadgeSystem.json", "r"
            ) as f:
                badge_system_abi = json.load(f)["abi"]

            if not settings.PROXY_ADDRESS:
                raise ValueError("PROXY_ADDRESS not configured in environment")

            self.contract_client = ContractClient(
                contract_address=settings.PROXY_ADDRESS, abi=badge_system_abi
            )

        return self.contract_client

    async def create_task(
        self, task_request: OriginTaskCreateRequestDTO
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Create a new task and badge on smart contract.

        Steps:
        1. Upload badge metadata to IPFS
        2. Save task to MongoDB
        3. Create badge on smart contract
        4. Update task with transaction info

        Args:
            task_request: Task creation request data

        Returns:
            Tuple of (success, message, task_data)
        """
        try:
            # Step 1: Prepare badge metadata for IPFS
            badge_metadata = self._prepare_badge_metadata(task_request.badge_details)

            # Upload to IPFS
            ipfs_hash = await ipfs_service.upload_badge_metadata(badge_metadata)
            if not ipfs_hash:
                return False, "Failed to upload badge metadata to IPFS", None

            metadata_uri = ipfs_service.get_ipfs_url(ipfs_hash)
            logger.info(f"Badge metadata uploaded to IPFS: {ipfs_hash}")

            # Step 2: Save task to MongoDB
            task_model = TaskModel(
                task_title=task_request.task_title,
                task_description=task_request.task_description,
                validation_type=task_request.validation_type,
                blockchain_network=task_request.blockchain_network,
                token_contract_address=task_request.token_contract_address,
                minimum_balance=task_request.minimum_balance,
                badge_details=task_request.badge_details.model_dump(),
            )

            created_task = await task_repository.create_task(task_model)
            task_id = str(created_task["_id"])
            logger.info(f"Task created in MongoDB with ID: {task_id}")

            # Step 3: Create badge on smart contract
            try:
                contract_client = await self._get_contract_client()

                # Call createBadge function
                tx_receipt = await contract_client.send_transaction(
                    function_name="createBadge",
                    args=[task_id, metadata_uri],
                    from_address=None,  # Will use default from contract_client
                )

                if tx_receipt and tx_receipt.get("status") == 1:
                    tx_hash = tx_receipt["transactionHash"].hex()
                    block_number = tx_receipt["blockNumber"]

                    # Step 4: Update task with transaction info
                    await task_repository.update_task_contract_data(
                        task_id, tx_hash, block_number
                    )

                    logger.info(
                        f"Badge created on-chain: tx_hash={tx_hash}, block={block_number}"
                    )

                    # Retrieve updated task
                    updated_task = await task_repository.get_task_by_id(task_id)

                    return (
                        True,
                        "Task and badge created successfully",
                        self._serialize_task(updated_task),
                    )
                else:
                    logger.error("Smart contract transaction failed")
                    return (
                        False,
                        "Failed to create badge on smart contract",
                        self._serialize_task(created_task),
                    )

            except Exception as contract_error:
                logger.error(f"Smart contract error: {contract_error}")
                # Task is created in DB but contract failed
                return (
                    False,
                    f"Task created but contract deployment failed: {str(contract_error)}",
                    self._serialize_task(created_task),
                )

        except Exception as e:
            logger.error(f"Error creating task: {e}", exc_info=True)
            return False, f"Failed to create task: {str(e)}", None

    async def get_tasks_paginated(
        self,
        page: int = 1,
        page_size: int = 10,
        validation_types: Optional[List[str]] = None,
        blockchain_networks: Optional[List[str]] = None,
    ) -> Tuple[List[Dict], int, int]:
        """
        Get paginated list of tasks.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            validation_types: Optional filter by validation types (list of erc20_balance_check, erc721_balance_check)
            blockchain_networks: Optional filter by blockchain networks (list of ethereum, bsc, base)

        Returns:
            Tuple of (tasks list, total count, total pages)
        """
        try:
            # Calculate skip
            skip = (page - 1) * page_size

            # Get tasks and total count
            tasks, total_count = await task_repository.get_tasks_paginated(
                skip=skip,
                limit=page_size,
                validation_types=validation_types,
                blockchain_networks=blockchain_networks,
            )

            # Calculate total pages
            total_pages = (total_count + page_size - 1) // page_size

            # Serialize tasks
            serialized_tasks = [self._serialize_task(task) for task in tasks]

            return serialized_tasks, total_count, total_pages

        except Exception as e:
            logger.error(f"Error getting tasks: {e}")
            return [], 0, 0

    async def get_task_by_id(self, task_id: str) -> Optional[Dict]:
        """
        Get task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task data or None if not found
        """
        try:
            task = await task_repository.get_task_by_id(task_id)
            if task:
                return self._serialize_task(task)
            return None
        except Exception as e:
            logger.error(f"Error getting task by ID: {e}")
            return None

    def _prepare_badge_metadata(self, badge_details: BadgeDetail) -> Dict:
        """
        Prepare badge metadata for IPFS upload.

        Args:
            badge_details: Badge details from request

        Returns:
            Badge metadata dictionary
        """
        return {
            "name": badge_details.badge_name,
            "description": badge_details.badge_description,
            "image": f"ipfs://{badge_details.badge_image}",
            "attributes": [
                {"trait_type": attr.trait_type, "value": attr.value}
                for attr in badge_details.attributes
            ],
        }

    def _serialize_task(self, task: Dict) -> Dict:
        """
        Serialize task document for API response.

        Args:
            task: Task document from MongoDB

        Returns:
            Serialized task data
        """
        if not task:
            return None

        # Convert ObjectId to string
        task_data = {
            "id": str(task["_id"]),
            "task_title": task.get("task_title"),
            "task_description": task.get("task_description"),
            "validation_type": task.get("validation_type"),
            "blockchain_network": task.get("blockchain_network"),
            "token_contract_address": task.get("token_contract_address"),
            "minimum_balance": task.get("minimum_balance"),
            "badge_details": task.get("badge_details"),
            "tx_hash": task.get("tx_hash"),
            "block_number": task.get("block_number"),
            "created_at": (
                task.get("created_at").isoformat() if task.get("created_at") else None
            ),
            "updated_at": (
                task.get("updated_at").isoformat() if task.get("updated_at") else None
            ),
        }

        return task_data

    async def validate_task_for_user(
        self, task_id: str, user_id: str
    ) -> TaskValidationResponseDTO:
        """
        Validate if user meets task requirements and generate signature for badge minting.

        Steps:
        1. Fetch user profile from Decode
        2. Extract primary wallet address
        3. Get task details
        4. Check if user already validated this task
        5. Validate balance on blockchain
        6. Sign task_id if validation succeeds
        7. Store successful validation

        Args:
            task_id: Task ID (MongoDB ObjectId)
            user_id: User ID from Decode

        Returns:
            TaskValidationResponseDTO with validation result and signature
        """
        try:
            # Step 1: Fetch user profile from Decode
            logger.info(f"Validating task {task_id} for user {user_id}")
            user_profile = await get_decode_profile_external(user_id)

            if not user_profile or not user_profile.get("success"):
                return TaskValidationResponseDTO(
                    success=False,
                    message="Failed to fetch user profile from Decode",
                    data=None,
                )

            # Step 2: Extract primary wallet address
            user_data = user_profile.get("data")
            if not user_data:
                return TaskValidationResponseDTO(
                    success=False, message="User data not found", data=None
                )

            primary_wallet = user_data.get("primary_wallet")
            if not primary_wallet or not primary_wallet.get("address"):
                return TaskValidationResponseDTO(
                    success=False,
                    message="User does not have a primary wallet",
                    data=None,
                )

            wallet_address = primary_wallet["address"]
            logger.info(f"User {user_id} primary wallet: {wallet_address}")

            # Step 3: Get task details
            task_data = await task_repository.get_task_by_id(task_id)
            if not task_data:
                return TaskValidationResponseDTO(
                    success=False, message="Task not found", data=None
                )

            # Step 4: Check if user already validated this task
            # existing_validation = await task_repository.get_user_task_validation(
            #     user_id, task_id
            # )

            # if existing_validation:
            #     logger.info(
            #         f"User {user_id} already validated task {task_id}, returning existing validation"
            #     )
            #     return TaskValidationResponseDTO(
            #         success=True,
            #         message="Task already validated for this user",
            #         data=TaskValidationDataDTO(
            #             task_id=task_id,
            #             user_wallet=wallet_address,
            #             actual_balance=str(
            #                 existing_validation.get("actual_balance", "0")
            #             ),
            #             required_balance=str(task_data.get("minimum_balance", 0)),
            #             signature=existing_validation.get("signature", ""),
            #             verification_hash=existing_validation.get(
            #                 "verification_hash", ""
            #             ),
            #             task_details=self._serialize_task(task_data),
            #         ),
            #     )

            # Step 5: Get RPC URL based on blockchain network
            blockchain_network = task_data.get("blockchain_network")
            rpc_url = self._get_rpc_url_for_network(blockchain_network)

            if not rpc_url:
                return TaskValidationResponseDTO(
                    success=False,
                    message=f"Unsupported blockchain network: {blockchain_network}",
                    data=None,
                )

            # Step 6: Validate balance based on validation type
            validation_type = task_data.get("validation_type")
            token_contract_address = task_data.get("token_contract_address")
            minimum_balance = task_data.get("minimum_balance", 0)

            is_valid = False
            actual_balance = 0
            logger.info(
                f"Validating balance for user {user_id} on network {blockchain_network}"
            )

            if validation_type == ValidationType.ERC20_BALANCE_CHECK.value:
                is_valid, actual_balance = await balance_validator.check_erc20_balance(
                    wallet_address=wallet_address,
                    token_contract_address=token_contract_address,
                    minimum_balance=minimum_balance,
                    rpc_url=rpc_url,
                )
            elif validation_type == ValidationType.ERC721_BALANCE_CHECK.value:
                is_valid, actual_balance = await balance_validator.check_erc721_balance(
                    wallet_address=wallet_address,
                    nft_contract_address=token_contract_address,
                    minimum_balance=minimum_balance,
                    rpc_url=rpc_url,
                )
            else:
                return TaskValidationResponseDTO(
                    success=False,
                    message=f"Unsupported validation type: {validation_type}",
                    data=None,
                )

            if not is_valid:
                return TaskValidationResponseDTO(
                    success=False,
                    message=f"Insufficient balance. Required: {minimum_balance}, Actual: {actual_balance}",
                    data=None,
                )

            # Step 7: Sign user_address + task_id using EVM_PRIVATE_KEY
            # This prevents signature reuse attacks by binding the signature to the specific user
            if not settings.EVM_PRIVATE_KEY:
                return TaskValidationResponseDTO(
                    success=False, message="EVM private key not configured", data=None
                )

            signature, signer_address, verification_hash = sign_user_task_message(
                user_address=wallet_address,
                task_id=task_id,
                private_key=settings.EVM_PRIVATE_KEY,
            )

            logger.info(
                f"Generated signature for task {task_id}: {signature[:20]}... (signer: {signer_address})"
            )

            # Step 8: Store successful validation
            validation_model = TaskValidationModel(
                user_id=user_id,
                task_id=task_id,
                wallet_address=wallet_address,
                actual_balance=str(actual_balance),
                signature=signature,
                verification_hash=verification_hash,
            )

            await task_repository.create_task_validation(validation_model)

            # Step 9: Return validation response
            return TaskValidationResponseDTO(
                success=True,
                message="Task validated successfully",
                data=TaskValidationDataDTO(
                    task_id=task_id,
                    user_wallet=wallet_address,
                    actual_balance=str(actual_balance),
                    required_balance=str(minimum_balance),
                    signature=signature,
                    verification_hash=verification_hash,
                    task_details=self._serialize_task(task_data),
                ),
            )

        except Exception as e:
            logger.error(f"Error validating task: {e}", exc_info=True)
            return TaskValidationResponseDTO(
                success=False, message=f"Internal server error: {str(e)}", data=None
            )

    def _get_rpc_url_for_network(self, blockchain_network: str) -> Optional[str]:
        """
        Get RPC URL for blockchain network.

        Args:
            blockchain_network: Blockchain network name

        Returns:
            RPC URL or None if unsupported
        """
        network_mapping = {
            BlockchainNetwork.ETHEREUM.value: settings.ETHEREUM_RPC_URL,
            BlockchainNetwork.BINANCE_SMART_CHAIN.value: settings.BSC_RPC_URL,
            BlockchainNetwork.BASE.value: settings.BASE_RPC_URL,
        }

        return network_mapping.get(blockchain_network)


# Global service instance
task_service = TaskService()
