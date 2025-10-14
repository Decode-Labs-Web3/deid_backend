## Sync Profile to DEiD (Calldata Builder)

Endpoint: `POST /api/v1/sync/create-profile`

What it does:

- Fetches user profile from Decode (via authenticated session)
- Builds metadata JSON: `username, display_name, bio, avatar_ipfs_hash, primary_wallet, wallets, decode_user_id`
- Uploads metadata to IPFS (`settings.IPFS_URL`), returns `ipfs://<hash>` and raw `<hash>`
- Encodes calldata for `createProfile(address wallet, string username, string metadataURI)`
- Returns calldata and backend validator signature over `ipfs_hash`; frontend also signs and submits the tx

Response example:

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Calldata prepared",
  "data": {
    "method": "createProfile(address,string,string)",
    "params": {
      "wallet": "0x...",
      "username": "pasondev",
      "metadataURI": "ipfs://bafy..."
    },
    "calldata": "0xf2bd900d...",
    "metadata": { "username": "...", "display_name": "..." },
    "ipfs_hash": "bafy...",
    "validator": {
      "signature": "0x...", // signature by backend validator key over ipfs_hash
      "signer": "0xValidator...", // validator address (recoverable on-chain)
      "payload": "bafy...", // raw ipfs hash string that was signed
      "type": "personal_sign"
    }
  }
}
```

How frontend uses it:

1. Call endpoint with session cookie to get `data`.
2. Verify backend validator signature client-side if desired (recover signer == expected).
3. Ask wallet to `personal_sign` the `ipfs_hash` string (optional if contract only checks validator sig).
4. Use proxy contract to forward the returned `calldata` to DEiDProfile facet. If your facet requires validator signature as an argument, extend calldata encoding to include it and the signer.

Debugging tips:

- If metadata upload fails: verify `IPFS_URL` is reachable and returns `Hash`.
- If wallet is missing: ensure Decode `primary_wallet.address` exists.
- If calldata mismatch: confirm the function signature and argument order on-chain. If you require validator signature on-chain, tell backend the exact function signature so calldata includes `(bytes validatorSig, address validator)`.
- To preview metadata: open `settings.IPFS_GATEWAY_URL/<hash>` in a browser.

# 🧩 **DEiD Protocol — Back-End**
