"""
Contract Client for smart contract interactions.
Handles Web3 contract calls and transactions.
"""

from typing import Any, Dict, List, Optional

from web3 import Web3
from web3.contract import Contract

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ContractClient:
    """Client for interacting with smart contracts."""

    def __init__(self, contract_address: str, abi: List[Dict]):
        """
        Initialize contract client.

        Args:
            contract_address: Contract address
            abi: Contract ABI
        """
        self.contract_address = Web3.to_checksum_address(contract_address)
        self.abi = abi

        # Initialize Web3 (use TESTNET_RPC_URL if available, otherwise EVM_RPC_URL)
        rpc_url = settings.TESTNET_RPC_URL or settings.EVM_RPC_URL
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        logger.info(f"Connecting to RPC: {rpc_url}")

        if not self.w3.is_connected():
            logger.error("Failed to connect to Web3 provider")
            raise ConnectionError("Cannot connect to blockchain RPC")

        # Load contract
        self.contract: Contract = self.w3.eth.contract(
            address=self.contract_address, abi=self.abi
        )

        logger.info(f"Contract client initialized for {self.contract_address}")

    async def send_transaction(
        self,
        function_name: str,
        args: List[Any],
        from_address: Optional[str] = None,
        gas_limit: Optional[int] = None,
    ) -> Optional[Dict]:
        """
        Send a transaction to the contract.

        Args:
            function_name: Name of the contract function to call
            args: List of arguments for the function
            from_address: Sender address (uses EVM_PRIVATE_KEY if None)
            gas_limit: Gas limit for the transaction

        Returns:
            Transaction receipt or None if failed
        """
        try:
            # Get the contract function
            contract_function = getattr(self.contract.functions, function_name)

            # Get account from private key
            if not settings.EVM_PRIVATE_KEY:
                raise ValueError("EVM_PRIVATE_KEY not configured")

            account = self.w3.eth.account.from_key(settings.EVM_PRIVATE_KEY)
            from_address = from_address or account.address

            logger.info(
                f"Sending transaction: {function_name}({args}) from {from_address}"
            )

            # Build transaction
            nonce = self.w3.eth.get_transaction_count(from_address)

            # Estimate gas if not provided
            if not gas_limit:
                try:
                    gas_limit = contract_function(*args).estimate_gas(
                        {"from": from_address}
                    )
                    # Add 20% buffer
                    gas_limit = int(gas_limit * 1.2)
                except Exception as e:
                    logger.warning(f"Gas estimation failed: {e}, using default")
                    gas_limit = 500000

            # Build transaction
            transaction = contract_function(*args).build_transaction(
                {
                    "from": from_address,
                    "nonce": nonce,
                    "gas": gas_limit,
                    "gasPrice": self.w3.eth.gas_price,
                }
            )

            # Sign transaction
            signed_txn = self.w3.eth.account.sign_transaction(
                transaction, settings.EVM_PRIVATE_KEY
            )

            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)

            logger.info(f"Transaction sent: {tx_hash.hex()}")

            # Wait for receipt
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            logger.info(f"Transaction confirmed: {tx_receipt['transactionHash'].hex()}")

            return dict(tx_receipt)

        except Exception as e:
            logger.error(f"Error sending transaction: {e}", exc_info=True)
            return None

    async def call_function(
        self, function_name: str, args: List[Any], from_address: Optional[str] = None
    ) -> Any:
        """
        Call a read-only contract function.

        Args:
            function_name: Name of the contract function to call
            args: List of arguments for the function
            from_address: Caller address (optional)

        Returns:
            Function return value
        """
        try:
            contract_function = getattr(self.contract.functions, function_name)

            if from_address:
                result = contract_function(*args).call({"from": from_address})
            else:
                result = contract_function(*args).call()

            logger.info(f"Called function: {function_name}({args}) = {result}")

            return result

        except Exception as e:
            logger.error(f"Error calling function: {e}", exc_info=True)
            return None
