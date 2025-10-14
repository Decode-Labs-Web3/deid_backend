"""
Function selector registry for DEiD contracts.

Central place to manage 4-byte selectors to avoid mismatches.
Update when facets/functions change.
"""

from typing import Dict


FUNCTION_SELECTORS: Dict[str, str] = {
    # Core
    "init()": "0x19ab453c",
    "createProfile(string,string,bytes)": "0x412738c8",
    "updateProfile(string,bytes)": "0x6eeb9b10",
    "getProfile(...)": "0x0f53a470",
    "resolveUsername(...)": "0x7d1febd4",
    "resolveAddress(...)": "0xf81e8775",
    "linkSocialAccount(...)": "0x54d58bd8",
    "unlinkSocialAccount(...)": "0x3d840a23",
    "getSocialAccounts(...)": "0x07029f91",
    "withdraw(...)": "0x3ccfd60b",
    # Validator admin
    "addValidator(address)": "0x4d238c8e",
    "isValidator(address)": "0xfacd743b",
    "getValidators()": "0xb7ab4db5",
}


def selector_for(signature: str) -> str:
    """Return 0x-prefixed selector hex for a function signature.

    Raises KeyError if not found.
    """
    return FUNCTION_SELECTORS[signature]
