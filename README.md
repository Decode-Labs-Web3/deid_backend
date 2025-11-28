# DEiD Backend

A FastAPI-based backend service for decentralized identity management, integrating with EVM smart contracts, IPFS, and the Decode Portal SSO system.

## Overview

DEiD Backend is the server-side component of the DEiD (Decentralized Identity) system, part of The Decode Network. It provides RESTful APIs for profile management, social account verification, task and badge management, score computation, and integration with blockchain smart contracts.

## Features

- **SSO Integration**: Seamless integration with Decode Portal for user authentication
- **Profile Synchronization**: Sync user profiles between Decode Portal and on-chain smart contracts
- **Social Link Verification**: OAuth2 flows for Discord, Twitter, GitHub, Telegram with EIP-712 signature verification
- **Task & Badge Management**: Create verification tasks, validate completions, and manage NFT badge minting
- **Score Computation**: Calculate user reputation scores and generate Merkle tree snapshots
- **IPFS Integration**: Upload and manage metadata on IPFS for badges and profiles
- **Blockchain Integration**: Interact with EVM smart contracts (Ethereum, BSC, Base, Monad)
- **MongoDB Storage**: Persistent storage for tasks, social links, and user data
- **Redis Caching**: Session management and caching layer

## Technology Stack

- **Framework**: FastAPI 0.118.0
- **Python**: 3.13
- **Database**: MongoDB (Motor async driver)
- **Cache**: Redis 5.2.1
- **Blockchain**: Web3.py 7.4.0
- **IPFS**: ipfshttpclient 0.8.0a2
- **Authentication**: python-jose 3.3.0 (JWT)
- **Validation**: Pydantic 2.11.10
- **HTTP Client**: httpx 0.28.1, aiohttp 3.12.15
- **Testing**: pytest 8.3.4, pytest-asyncio 0.23.8

## Prerequisites

- Python 3.13 or higher
- MongoDB 4.4 or higher (local or cloud instance)
- Redis 6.0 or higher (optional, for caching)
- Access to Ethereum RPC endpoint (Sepolia testnet recommended)
- IPFS node or gateway access
- Decode Portal credentials (for SSO integration)

## Installation

1. Clone the repository and navigate to the backend directory:

```bash
cd deid_backend
```

2. Create a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file (see [Environment Variables](#environment-variables))

5. Start MongoDB and Redis (if running locally):

```bash
# MongoDB
mongod

# Redis
redis-server
```

6. Run the development server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`

## Environment Variables

Create a `.env` file in the `deid_backend` directory:

```bash
# Application
APP_NAME=DEID Backend
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=your-secret-key-change-in-production

# Server
HOST=0.0.0.0
PORT=8000

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,https://app.de-id.xyz
ALLOWED_HOSTS=localhost,api.de-id.xyz

# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=deid_backend
# Or use connection string:
MONGO_URI=mongodb+srv://user:password@cluster.mongodb.net/
MONGO_DB_NAME=deid

# Redis
REDIS_URI=redis://localhost:6379
REDIS_DB=0
SESSION_EXPIRE_DAYS=30

# JWT
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Blockchain - Ethereum Sepolia
TESTNET_RPC_URL=https://eth-sepolia.public.blastapi.io
EVM_RPC_URL=https://eth-sepolia.public.blastapi.io
EVM_CHAIN_ID=11155111
EVM_PRIVATE_KEY=0xYourPrivateKeyForSigning

# Blockchain - Monad Testnet (alternative)
# EVM_RPC_URL=https://testnet-rpc.monad.xyz
# EVM_CHAIN_ID=41434

# Smart Contract
EVM_CONTRACT_ADDRESS=0xYourContractAddress
PROXY_ADDRESS=0xYourProxyAddress

# Blockchain Validation RPCs
ETHEREUM_RPC_URL=https://eth-mainnet.public.blastapi.io
BSC_RPC_URL=https://bsc-mainnet.public.blastapi.io
BASE_RPC_URL=https://base-mainnet.public.blastapi.io

# IPFS
IPFS_GATEWAY_URL_POST=http://35.247.142.76:5001/api/v0/add
IPFS_GATEWAY_URL_GET=http://35.247.142.76:8080/ipfs
# Or use Pinata:
IPFS_ACCESS_TOKEN=your-pinata-jwt-token
IPFS_PINATA_API_KEY=your-pinata-api-key
IPFS_PINATA_SECRET=your-pinata-secret

# Decode Portal SSO
DECODE_PORTAL_BASE_URL=https://portal.decode.com
DECODE_PORTAL_CLIENT_ID=your-decode-client-id
DECODE_PORTAL_CLIENT_SECRET=your-decode-client-secret

# Social Link Verification
DISCORD_CLIENT_ID=your-discord-client-id
DISCORD_CLIENT_SECRET=your-discord-client-secret
DISCORD_REDIRECT_URI=https://api.de-id.xyz/api/v1/social/discord/callback
SOCIAL_LINK_PRIVATE_KEY=0xYourPrivateKeyForSigning
```

### Environment Variable Descriptions

| Variable | Description | Required |
|----------|-------------|----------|
| `MONGODB_URL` | MongoDB connection string | Yes |
| `EVM_RPC_URL` | Ethereum RPC endpoint | Yes |
| `EVM_PRIVATE_KEY` | Private key for signing transactions | Yes |
| `DECODE_PORTAL_CLIENT_ID` | Decode Portal OAuth client ID | Yes |
| `DECODE_PORTAL_CLIENT_SECRET` | Decode Portal OAuth secret | Yes |
| `IPFS_GATEWAY_URL_POST` | IPFS node for uploading | Yes |
| `JWT_SECRET_KEY` | Secret for JWT tokens | Yes |
| `PROXY_ADDRESS` | Smart contract proxy address | Yes |

## API Endpoints

### Decode Integration (`/api/v1/decode`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/my-profile` | Get current user profile | Cookie |
| POST | `/fetch-user-data` | Fetch user data from Decode | SSO Token |
| POST | `/sync-to-evm` | Sync profile to blockchain | SSO Token |

### Profile Synchronization (`/api/v1/sync`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/profile` | Sync user profile to smart contract | Cookie |

### Social Link Verification (`/api/v1/social`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/discord/oauth-url` | Get Discord OAuth URL | Query param |
| GET | `/discord/callback` | Handle Discord OAuth callback | OAuth |
| POST | `/onchain-confirm` | Confirm on-chain verification | Query param |
| GET | `/links/{user_id}` | Get user's social links | Public |
| GET | `/stats/{user_id}` | Get social link statistics | Public |
| GET | `/health` | Health check | Public |

See [SOCIAL_LINK_README.md](./SOCIAL_LINK_README.md) for detailed documentation.

### Task & Badge Management (`/api/v1/task`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/create` | Create verification task | Admin |
| GET | `/list` | List tasks with filters | Public |
| GET | `/{task_id}` | Get task details | Public |
| POST | `/validate` | Validate task completion | Cookie |

See [TASK_BADGE_SYSTEM.md](./TASK_BADGE_SYSTEM.md) for detailed documentation.

### Health & Status

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint with feature list |
| GET | `/health` | Health check with service status |

## Project Structure

```
deid_backend/
├── app/
│   ├── api/
│   │   ├── routers/          # FastAPI route handlers
│   │   │   ├── decode_router.py
│   │   │   ├── social_link_router.py
│   │   │   ├── sync_profile_router.py
│   │   │   └── task_router.py
│   │   ├── services/         # Business logic layer
│   │   │   ├── social_link_service.py
│   │   │   ├── task_service.py
│   │   │   └── ...
│   │   ├── dto/             # Data Transfer Objects
│   │   │   ├── social_dto.py
│   │   │   └── task_dto.py
│   │   └── deps/            # FastAPI dependencies
│   ├── core/
│   │   ├── config.py        # Configuration management
│   │   ├── security.py     # Authentication & authorization
│   │   ├── logging.py       # Logging setup
│   │   └── exceptions.py   # Custom exceptions
│   ├── domain/
│   │   ├── models/         # Domain models (Pydantic)
│   │   │   ├── task.py
│   │   │   └── social_link.py
│   │   └── repositories/   # Data access layer
│   │       ├── task_repository.py
│   │       └── social_link_repository.py
│   ├── infrastructure/
│   │   ├── blockchain/     # Web3 integration
│   │   │   ├── contract_client.py
│   │   │   └── signature_utils.py
│   │   ├── ipfs/           # IPFS integration
│   │   │   └── ipfs_service.py
│   │   ├── db/             # Database connections
│   │   └── cache/         # Redis integration
│   ├── contracts/          # Smart contract ABIs
│   │   ├── core/
│   │   ├── verification/
│   │   └── ...
│   └── main.py             # FastAPI application entry point
├── tests/                  # Test files
├── requirements.txt        # Python dependencies
├── pytest.ini            # Pytest configuration
└── .env                   # Environment variables (not in git)
```

## Architecture

The backend follows a **layered architecture** pattern:

1. **API Layer** (`routers/`): FastAPI route handlers, request validation
2. **Service Layer** (`services/`): Business logic, orchestration
3. **Repository Layer** (`repositories/`): Data access, MongoDB operations
4. **Domain Layer** (`models/`): Domain models, business entities
5. **Infrastructure Layer** (`infrastructure/`): External services (blockchain, IPFS, cache)

### Data Flow Example: Task Creation

```
Frontend → Router → Service → Repository → MongoDB
                    ↓
                 IPFS Service → IPFS Node
                    ↓
              Contract Client → Smart Contract
```

## Database Setup

### MongoDB Collections

#### Tasks Collection

```javascript
{
  _id: ObjectId,
  task_title: String,
  task_description: String,
  validation_type: "erc20_balance_check" | "erc721_balance_check",
  blockchain_network: "ethereum" | "bsc" | "base",
  token_contract_address: String,
  minimum_balance: Number,
  badge_details: {
    badge_name: String,
    badge_description: String,
    badge_image: String, // IPFS hash
    attributes: Array
  },
  tx_hash: String,
  block_number: Number,
  created_at: ISODate,
  updated_at: ISODate
}
```

#### Social Links Collection

```javascript
{
  _id: ObjectId,
  user_id: String, // Wallet address
  platform: "discord" | "twitter" | "github" | "telegram",
  account_id: String,
  username: String,
  email: String,
  display_name: String,
  avatar_url: String,
  signature: String, // EIP-712 signature
  verification_hash: String,
  status: "pending" | "verified" | "onchain" | "failed",
  tx_hash: String,
  block_number: Number,
  created_at: ISODate,
  updated_at: ISODate
}
```

### Recommended Indexes

```javascript
// Tasks
db.tasks.createIndex({ validation_type: 1, blockchain_network: 1, created_at: -1 });
db.tasks.createIndex({ created_at: -1 });

// Social Links
db.social_links.createIndex({ user_id: 1, platform: 1 }, { unique: true });
db.social_links.createIndex({ user_id: 1 });
db.social_links.createIndex({ status: 1 });
```

## Running the Server

### Development Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Gunicorn (Production)

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Testing

Run tests with pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_social_pkce.py

# Run with verbose output
pytest -v
```

Test files are located in the `tests/` directory and use pytest fixtures defined in `conftest.py`.

## API Documentation

Interactive API documentation is available at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## Security Considerations

1. **Private Keys**: Never commit private keys to version control. Use environment variables.
2. **JWT Secrets**: Use strong, random secrets for JWT signing.
3. **CORS**: Configure allowed origins properly for production.
4. **Rate Limiting**: Implement rate limiting for public endpoints.
5. **Input Validation**: All inputs are validated using Pydantic models.
6. **SQL Injection**: Not applicable (MongoDB), but use parameterized queries.
7. **Signature Verification**: All blockchain signatures are verified using EIP-712 standard.

## Monitoring & Logging

The application uses structured logging:

```python
from app.core.logging import get_logger

logger = get_logger(__name__)
logger.info("Task created", extra={"task_id": task_id})
```

Logs are formatted as JSON for easy parsing by log aggregation services.

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment-Specific Configuration

- **Development**: Debug mode enabled, detailed error messages
- **Production**: Debug disabled, error messages sanitized, CORS restricted

## Related Documentation

- [Setup Guide](./SETUP.md) - Detailed setup instructions
- [Social Link Service](./SOCIAL_LINK_README.md) - Social verification documentation
- [Task & Badge System](./TASK_BADGE_SYSTEM.md) - Task management documentation
- [Insomnia Testing Guide](./INSOMNIA_TESTING_GUIDE.md) - API testing examples

## Troubleshooting

### MongoDB Connection Issues

```bash
# Check MongoDB is running
mongosh --eval "db.adminCommand('ping')"

# Verify connection string
echo $MONGODB_URL
```

### Blockchain Connection Issues

```bash
# Test RPC endpoint
curl -X POST $EVM_RPC_URL \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
```

### IPFS Upload Failures

- Verify IPFS node is accessible
- Check IPFS gateway URL is correct
- Ensure IPFS node has CORS enabled for your domain

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Ensure all tests pass
6. Submit a Pull Request

## License

MIT License - see LICENSE file for details

## Support

For issues or questions:

- Open an issue on GitHub
- Check existing documentation
- Review the [REPORT.md](../REPORT.md) for architecture details

---

**Built with ❤️ for The Decode Network**
