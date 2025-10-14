# DEID Backend Setup

## Overview

Simple SSO backend for DEID with 2 main functions:

1. **Fetch user data from Decode** - Get user profile data using SSO token
2. **Sync to Monad testnet** - Sync user data to blockchain profile with signature

## Environment Variables

Create a `.env` file with these variables:

```bash
# Monad Testnet Configuration
EVM_RPC_URL=https://testnet-rpc.monad.xyz
EVM_CHAIN_ID=41434
EVM_PRIVATE_KEY=your-private-key-here

# Decode Portal SSO
DECODE_PORTAL_BASE_URL=https://portal.decode.com
DECODE_PORTAL_CLIENT_ID=your-decode-client-id
DECODE_PORTAL_CLIENT_SECRET=your-decode-client-secret

# Database
MONGODB_URL=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET_KEY=your-jwt-secret-key
```

## API Endpoints

### SSO Endpoints

| Method | Endpoint                      | Description                     |
| ------ | ----------------------------- | ------------------------------- |
| POST   | `/api/v1/sso/fetch-user-data` | Fetch user data from Decode     |
| POST   | `/api/v1/sso/sync-to-evm`     | Sync user data to Monad testnet |
| GET    | `/api/v1/sso/health`          | SSO service health check        |

### Request Examples

#### Fetch User Data

```json
POST /api/v1/sso/fetch-user-data
{
  "sso_token": "your-sso-token"
}
```

#### Sync to Monad Testnet

```json
POST /api/v1/sso/sync-to-evm
{
  "sso_token": "your-sso-token",
  "wallet_address": "0x..."
}
```

## Features

- ✅ SSO token validation with Decode Portal
- ✅ User data fetching from Decode
- ✅ IPFS metadata upload (mock)
- ✅ Message signing with private key
- ✅ Monad testnet integration
- ✅ MongoDB user storage
- ✅ Redis session management

## Running the Server

```bash
# Install dependencies
pip install -r requirements.txt

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Monad Testnet Details

- **Chain ID**: 41434
- **RPC URL**: https://testnet-rpc.monad.xyz
- **Explorer**: https://testnet-explorer.monad.xyz

The backend signs messages using the private key from `.env` for smart contract validation.
