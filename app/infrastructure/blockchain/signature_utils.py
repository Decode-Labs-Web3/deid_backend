"""
Signature utilities for backend validator signing.
"""

from typing import Tuple

from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3

from app.core.config import settings


def sign_message_with_private_key(
    message: str, private_key: str = settings.EVM_PRIVATE_KEY
) -> Tuple[str, str, str]:
    """
    Sign a message matching this ethers.js logic:

      const message = metadataURI;
      const messageHash = ethers.keccak256(ethers.toUtf8Bytes(message));
      const signature = await deployer.signMessage(ethers.getBytes(messageHash));

    This means:
    - Compute messageHash = keccak256(utf8(message))
    - Sign the messageHash bytes using personal_sign (EIP-191)

    Returns (signature_hex, signer_address, message_hash_hex)
    """

    # Step 1: Compute message hash (ethers.keccak256(ethers.toUtf8Bytes(message)))
    message_bytes = message.encode("utf-8")
    message_hash_bytes = Web3.keccak(message_bytes)  # 32-byte hash as bytes
    message_hash_hex = "0x" + message_hash_bytes.hex()

    # Step 2: Convert hash to bytes for signing (ethers.getBytes(messageHash))
    # message_hash_bytes is already bytes from Web3.keccak()

    # Step 3: EIP-191 personal_sign using encode_defunct
    eth_message = encode_defunct(message_hash_bytes)

    # Step 4: Sign with eth_account
    signed = Account.sign_message(eth_message, private_key=private_key)

    # Get the signer address from the private key
    signer_address = Account.from_key(private_key).address

    signature_hex = signed.signature.hex()

    return (signature_hex, signer_address, message_hash_hex)


def sign_user_task_message(
    user_address: str, task_id: str, private_key: str = settings.EVM_PRIVATE_KEY
) -> Tuple[str, str, str]:
    """
    Sign a message that binds a task to a specific user address.

    This prevents signature reuse attacks where a signature for one user
    could be used by another user.

    The message format matches the smart contract expectation:
    keccak256(abi.encodePacked(userAddress, taskId))

    Smart Contract Flow:
    1. expectedMessageHash = keccak256(abi.encodePacked(userAddress, taskId))
    2. ethSignedMessageHash = getEthSignedMessageHash(expectedMessageHash)
    3. signer = recoverSigner(ethSignedMessageHash, signature)

    Args:
        user_address: The user's wallet address
        task_id: The task ID
        private_key: The validator's private key

    Returns:
        Tuple of (signature_hex, signer_address, message_hash_hex)
    """

    # Create the message that includes both user address and task ID
    # This matches the smart contract's keccak256(abi.encodePacked(userAddress, taskId))
    # abi.encodePacked concatenates raw bytes, not strings
    user_address_bytes = bytes.fromhex(user_address[2:])  # Remove 0x prefix
    task_id_bytes = task_id.encode("utf-8")
    combined_message_bytes = user_address_bytes + task_id_bytes

    # Step 1: Compute the message hash (keccak256(abi.encodePacked(userAddress, taskId)))
    message_hash = Web3.keccak(combined_message_bytes)  # 32-byte hash as bytes
    message_hash_hex = "0x" + message_hash.hex()

    # Step 2: Create EIP-191 signed message hash
    # This is equivalent to getEthSignedMessageHash(messageHash) in Solidity
    eth_message = encode_defunct(message_hash)

    # Step 3: Sign the EIP-191 message hash
    signed = Account.sign_message(eth_message, private_key=private_key)

    # Get the signer address from the private key
    signer_address = Account.from_key(private_key).address

    signature_hex = signed.signature.hex()

    return (signature_hex, signer_address, message_hash_hex)
