"""
Blockchain Balance Validator.
Validates ERC20 and ERC721 token balances for task validation.
"""

from typing import Optional, Tuple

from web3 import Web3

from app.core.logging import get_logger

logger = get_logger(__name__)

# Standard ERC20 ABI (balanceOf function)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    }
]

# Standard ERC721 ABI (balanceOf function)
ERC721_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function",
    }
]


class BlockchainBalanceValidator:
    """Validator for checking token and NFT balances on blockchain."""

    def __init__(self):
        """Initialize balance validator."""
        pass

    async def check_erc20_balance(
        self,
        wallet_address: str,
        token_contract_address: str,
        minimum_balance: int,
        rpc_url: str,
    ) -> Tuple[bool, int]:
        """
        Check if wallet has minimum ERC20 token balance.

        Args:
            wallet_address: User's wallet address
            token_contract_address: ERC20 token contract address
            minimum_balance: Minimum required balance
            rpc_url: Blockchain RPC URL

        Returns:
            Tuple of (is_valid, actual_balance)
        """
        try:
            # Connect to blockchain
            w3 = Web3(Web3.HTTPProvider(rpc_url))

            if not w3.is_connected():
                logger.error(f"Failed to connect to blockchain RPC: {rpc_url}")
                return False, 0

            # Convert addresses to checksum format
            wallet_checksum = Web3.to_checksum_address(wallet_address)
            token_checksum = Web3.to_checksum_address(token_contract_address)

            # Create contract instance
            contract = w3.eth.contract(address=token_checksum, abi=ERC20_ABI)

            # Call balanceOf function
            balance = contract.functions.balanceOf(wallet_checksum).call()

            logger.info(
                f"ERC20 balance check: wallet={wallet_address}, token={token_contract_address}, balance={balance}, minimum={minimum_balance}"
            )

            # Check if balance meets minimum requirement
            is_valid = balance >= minimum_balance

            return is_valid, balance

        except Exception as e:
            logger.error(f"Error checking ERC20 balance: {e}", exc_info=True)
            return False, 0

    async def check_erc721_balance(
        self,
        wallet_address: str,
        nft_contract_address: str,
        minimum_balance: int,
        rpc_url: str,
    ) -> Tuple[bool, int]:
        """
        Check if wallet has minimum ERC721 NFT balance.

        Args:
            wallet_address: User's wallet address
            nft_contract_address: ERC721 NFT contract address
            minimum_balance: Minimum required balance
            rpc_url: Blockchain RPC URL

        Returns:
            Tuple of (is_valid, actual_balance)
        """
        try:
            # Connect to blockchain
            w3 = Web3(Web3.HTTPProvider(rpc_url))

            if not w3.is_connected():
                logger.error(f"Failed to connect to blockchain RPC: {rpc_url}")
                return False, 0

            # Convert addresses to checksum format
            wallet_checksum = Web3.to_checksum_address(wallet_address)
            nft_checksum = Web3.to_checksum_address(nft_contract_address)

            # Create contract instance
            contract = w3.eth.contract(address=nft_checksum, abi=ERC721_ABI)

            # Call balanceOf function
            balance = contract.functions.balanceOf(wallet_checksum).call()

            logger.info(
                f"ERC721 balance check: wallet={wallet_address}, nft={nft_contract_address}, balance={balance}, minimum={minimum_balance}"
            )

            # Check if balance meets minimum requirement
            is_valid = balance >= minimum_balance

            return is_valid, balance

        except Exception as e:
            logger.error(f"Error checking ERC721 balance: {e}", exc_info=True)
            return False, 0


# Global validator instance
balance_validator = BlockchainBalanceValidator()
