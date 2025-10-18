# Task & Badge Management System Documentation

## Overview

The Task & Badge Management System allows administrators to create on-chain verification tasks that users can complete to earn NFT badges. The system integrates MongoDB for data storage, IPFS for metadata hosting, and Ethereum smart contracts for on-chain badge minting.

### Access Control

- **Task Creation**: Admin role required (enforced via `get_admin_user()` dependency)
- **Task Viewing**: Public access (no authentication required)
- **Task Types Supported**: ERC20 balance verification, ERC721 balance verification

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Data Flow](#data-flow)
3. [API Endpoints](#api-endpoints)
4. [Code Structure](#code-structure)
5. [Configuration](#configuration)
6. [Usage Examples](#usage-examples)

---

## System Architecture

### Components

```
┌─────────────┐
│  Frontend   │
│  (React)    │
└──────┬──────┘
       │
       │ HTTP Request
       ▼
┌─────────────────────────────────────────┐
│         FastAPI Backend                 │
│  ┌───────────────────────────────────┐ │
│  │   Task Router                     │ │
│  │   - POST /task/create             │ │
│  │   - GET  /task/list               │ │
│  │   - GET  /task/{id}               │ │
│  └───────────┬───────────────────────┘ │
│              │                           │
│  ┌───────────▼───────────────────────┐ │
│  │   Task Service                    │ │
│  │   - Business Logic                │ │
│  │   - Orchestration                 │ │
│  └───┬───────────────┬───────────┬───┘ │
│      │               │           │     │
└──────┼───────────────┼───────────┼─────┘
       │               │           │
       ▼               ▼           ▼
┌─────────────┐ ┌──────────┐ ┌─────────────┐
│   MongoDB   │ │   IPFS   │ │  Ethereum   │
│  (Storage)  │ │(Metadata)│ │ (BadgeNFT)  │
└─────────────┘ └──────────┘ └─────────────┘
```

### Technology Stack

- **Backend Framework**: FastAPI (Python 3.13)
- **Database**: MongoDB (Motor async driver)
- **Blockchain**: Ethereum Sepolia Testnet
- **Web3 Library**: Web3.py
- **Storage**: IPFS Gateway
- **Authentication**: JWT-based (DecodeGuard)

---

## Data Flow

### 1. Task Creation Flow

```
┌──────────┐
│ Frontend │
└────┬─────┘
     │
     │ 1. POST /api/v1/task/create
     │    {
     │      task_title, task_description,
     │      validation_type, blockchain_network,
     │      token_contract_address, minimum_balance,
     │      badge_details {name, description, image, attributes}
     │    }
     ▼
┌────────────────┐
│  Task Router   │ Authenticates admin via get_admin_user()
└────┬───────────┘
     │
     │ 2. Calls task_service.create_task()
     ▼
┌────────────────────────────────────────────────┐
│            Task Service                        │
│                                                │
│  Step 1: Prepare Badge Metadata               │
│  ┌─────────────────────────────────────────┐  │
│  │ {                                       │  │
│  │   "name": "Badge Name",                 │  │
│  │   "description": "Badge Description",   │  │
│  │   "image": "ipfs://Qm...",             │  │
│  │   "attributes": [...]                   │  │
│  │ }                                       │  │
│  └─────────────────────────────────────────┘  │
│           │                                    │
│           │ 3. Upload to IPFS                  │
│           ▼                                    │
│  ┌─────────────────────────────────────────┐  │
│  │  IPFS Service                           │  │
│  │  POST http://35.247.142.76:5001/api/   │  │
│  │       v0/add                            │  │
│  │  Returns: IPFS Hash (Qm...)             │  │
│  └─────────────────────────────────────────┘  │
│           │                                    │
│           │ 4. Save to MongoDB                 │
│           ▼                                    │
│  ┌─────────────────────────────────────────┐  │
│  │  Task Repository                        │  │
│  │  - Inserts task document                │  │
│  │  - Returns task_id (MongoDB ObjectId)  │  │
│  └─────────────────────────────────────────┘  │
│           │                                    │
│           │ 5. Create Badge On-Chain          │
│           ▼                                    │
│  ┌─────────────────────────────────────────┐  │
│  │  Contract Client                        │  │
│  │  - Connects to Sepolia via Web3        │  │
│  │  - Calls: createBadge(task_id, ipfs_url)│  │
│  │  - Signs tx with EVM_PRIVATE_KEY        │  │
│  │  - Waits for confirmation               │  │
│  │  Returns: tx_hash, block_number         │  │
│  └─────────────────────────────────────────┘  │
│           │                                    │
│           │ 6. Update Task with TX Info        │
│           ▼                                    │
│  ┌─────────────────────────────────────────┐  │
│  │  Task Repository                        │  │
│  │  - Updates task with tx_hash            │  │
│  │  - Updates task with block_number       │  │
│  └─────────────────────────────────────────┘  │
└────────────────────────────────────────────────┘
     │
     │ 7. Return Success Response
     ▼
┌──────────┐
│ Frontend │ Displays created task with on-chain confirmation
└──────────┘
```

### 2. Task Listing Flow

```
┌──────────┐
│ Frontend │
└────┬─────┘
     │
     │ GET /api/v1/task/list?page=1&page_size=10&validation_type=erc20_balance_check
     ▼
┌────────────────┐
│  Task Router   │ No authentication required
└────┬───────────┘
     │
     │ Calls task_service.get_tasks_paginated()
     ▼
┌────────────────────────────────────────────┐
│         Task Service                       │
│                                            │
│  1. Calculate skip = (page - 1) * page_size│
│                                            │
│  2. Query MongoDB                          │
│     ┌────────────────────────────────┐    │
│     │  Task Repository               │    │
│     │  - Filters by validation_type  │    │
│     │  - Sorts by created_at DESC    │    │
│     │  - Applies skip & limit        │    │
│     │  Returns: (tasks[], total_count)│   │
│     └────────────────────────────────┘    │
│                                            │
│  3. Calculate total_pages                  │
│     total_pages = ceil(total_count / page_size)│
│                                            │
│  4. Serialize tasks                        │
│     - Convert ObjectId to string           │
│     - Format datetime to ISO string        │
└────────────────────────────────────────────┘
     │
     │ Return paginated response
     ▼
┌──────────┐
│ Frontend │ Displays task list with pagination
└──────────┘
```

---

## API Endpoints

### 1. Create Task (POST /api/v1/task/create)

**Authentication**: Required (Admin Role Only)

**Request Body**:

```json
{
  "task_title": "Hold 100 USDC",
  "task_description": "Hold at least 100 USDC tokens in your wallet",
  "validation_type": "erc20_balance_check",
  "blockchain_network": "ethereum",
  "token_contract_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
  "minimum_balance": 100,
  "badge_details": {
    "badge_name": "USDC Holder",
    "badge_description": "Awarded for holding 100+ USDC",
    "badge_image": "QmXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "attributes": [
      {
        "trait_type": "Token",
        "value": "USDC"
      },
      {
        "trait_type": "Minimum Amount",
        "value": "100"
      },
      {
        "trait_type": "Network",
        "value": "Ethereum"
      }
    ]
  }
}
```

**Response (Success)**:

```json
{
  "success": true,
  "message": "Task and badge created successfully",
  "data": {
    "id": "507f1f77bcf86cd799439011",
    "task_title": "Hold 100 USDC",
    "task_description": "Hold at least 100 USDC tokens in your wallet",
    "validation_type": "erc20_balance_check",
    "blockchain_network": "ethereum",
    "token_contract_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "minimum_balance": 100,
    "badge_details": {
      "badge_name": "USDC Holder",
      "badge_description": "Awarded for holding 100+ USDC",
      "badge_image": "QmXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
      "attributes": [...]
    },
    "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
    "block_number": 4567890,
    "created_at": "2025-10-18T10:30:00.000Z",
    "updated_at": "2025-10-18T10:30:15.000Z"
  }
}
```

**Response (Failure)**:

```json
{
  "success": false,
  "message": "Failed to upload badge metadata to IPFS",
  "data": null
}
```

---

### 2. List Tasks (GET /api/v1/task/list)

**Authentication**: Not required

**Query Parameters**:

- `page` (integer, default: 1) - Page number (1-indexed)
- `page_size` (integer, default: 10, max: 100) - Items per page
- `validation_type` (string, optional) - Filter by validation type
  - `erc20_balance_check` - ERC20 token balance verification
  - `erc721_balance_check` - ERC721 NFT ownership verification

**Example Request**:

```
GET /api/v1/task/list?page=1&page_size=10&validation_type=erc20_balance_check
```

**Response**:

```json
{
  "success": true,
  "message": "Tasks retrieved successfully",
  "data": [
    {
      "id": "507f1f77bcf86cd799439011",
      "task_title": "Hold 100 USDC",
      "task_description": "Hold at least 100 USDC tokens in your wallet",
      "validation_type": "erc20_balance_check",
      "blockchain_network": "ethereum",
      "token_contract_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
      "minimum_balance": 100,
      "badge_details": {...},
      "tx_hash": "0xabc...",
      "block_number": 4567890,
      "created_at": "2025-10-18T10:30:00.000Z",
      "updated_at": "2025-10-18T10:30:15.000Z"
    },
    // ... more tasks
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_count": 25,
    "total_pages": 3
  }
}
```

---

### 3. Get Task by ID (GET /api/v1/task/{task_id})

**Authentication**: Not required

**Path Parameters**:

- `task_id` (string) - MongoDB ObjectId of the task

**Example Request**:

```
GET /api/v1/task/507f1f77bcf86cd799439011
```

**Response (Found)**:

```json
{
  "success": true,
  "message": "Task retrieved successfully",
  "data": {
    "id": "507f1f77bcf86cd799439011",
    "task_title": "Hold 100 USDC"
    // ... full task data
  }
}
```

**Response (Not Found)**:

```json
{
  "success": false,
  "message": "Task not found",
  "data": null
}
```

---

## Code Structure

### 1. **Data Models** (`app/domain/models/task.py`)

Defines the MongoDB schema for tasks:

```python
class ValidationType(str, Enum):
    ERC20_BALANCE_CHECK = "erc20_balance_check"  # Check ERC20 token balance
    ERC721_BALANCE_CHECK = "erc721_balance_check"  # Check NFT ownership

class BlockchainNetwork(str, Enum):
    ETHEREUM = "ethereum"
    BINANCE_SMART_CHAIN = "bsc"
    BASE = "base"

class TaskModel(BaseModel):
    task_title: str
    task_description: str
    validation_type: ValidationType
    blockchain_network: BlockchainNetwork
    token_contract_address: str
    minimum_balance: int
    badge_details: BadgeDetail
```

**Purpose**: Type-safe data models for MongoDB documents

---

### 2. **DTOs** (`app/api/dto/task_dto.py`)

Data Transfer Objects for API request/response:

- `OriginTaskCreateRequestDTO` - Request body for task creation
- `TaskResponseDTO` - Task data in API responses
- `TaskCreateResponseDTO` - Response wrapper for single task
- `TaskListResponseDTO` - Response wrapper for paginated list

**Purpose**: Separates internal models from API contracts, enables validation

---

### 3. **Repository Layer** (`app/domain/repositories/task_repository.py`)

Handles all MongoDB operations:

```python
class TaskRepository:
    async def create_task(task_data: TaskModel) -> dict
    async def get_task_by_id(task_id: str) -> Optional[dict]
    async def get_tasks_paginated(skip, limit, validation_type) -> tuple[List[dict], int]
    async def update_task_contract_data(task_id, tx_hash, block_number) -> bool
```

**Key Features**:

- Async MongoDB operations using Motor
- Automatic timestamps (created_at, updated_at)
- Pagination support with total count
- Optional filtering by validation type

**Purpose**: Database abstraction layer, makes testing easier

---

### 4. **IPFS Service** (`app/infrastructure/ipfs/ipfs_service.py`)

Handles badge metadata upload to IPFS:

```python
class IPFSService:
    async def upload_badge_metadata(badge_data: Dict) -> Optional[str]
    def get_ipfs_url(ipfs_hash: str) -> str
```

**Upload Process**:

1. Converts badge data to JSON
2. Creates multipart form data
3. POSTs to IPFS gateway (http://35.247.142.76:5001/api/v0/add)
4. Returns IPFS hash (CID)

**Purpose**: Decentralized metadata storage for NFT badges

---

### 5. **Contract Client** (`app/infrastructure/blockchain/contract_client.py`)

Web3 integration for smart contract interactions:

```python
class ContractClient:
    async def send_transaction(function_name, args, from_address, gas_limit)
    async def call_function(function_name, args, from_address)
```

**Key Features**:

- Web3.py integration with Sepolia testnet
- Automatic gas estimation (+ 20% buffer)
- Transaction signing with private key
- Wait for transaction confirmation (120s timeout)
- Error handling and logging

**Smart Contract Function Called**:

```solidity
function createBadge(string taskId, string metadataURI) public
```

**Purpose**: Blockchain interaction layer

---

### 6. **Task Service** (`app/api/services/task_service.py`)

Business logic orchestration:

```python
class TaskService:
    async def create_task(request) -> Tuple[bool, str, Optional[Dict]]
    async def get_tasks_paginated(page, page_size, validation_type)
    async def get_task_by_id(task_id)
```

**Create Task Logic**:

1. Prepare badge metadata JSON
2. Upload to IPFS → get hash
3. Save task to MongoDB → get task_id
4. Load BadgeSystem ABI from JSON
5. Initialize ContractClient with PROXY_ADDRESS
6. Call `createBadge(task_id, ipfs_url)` on-chain
7. Wait for transaction confirmation
8. Update task with tx_hash and block_number
9. Return serialized task data

**Error Handling**:

- If IPFS fails → return error immediately
- If MongoDB fails → return error with partial data
- If contract call fails → task exists in DB but not on-chain

**Purpose**: Coordinates between repository, IPFS, and blockchain

---

### 7. **Task Router** (`app/api/routers/task_router.py`)

FastAPI endpoints:

```python
@router.post("/create")  # Requires authentication
@router.get("/list")     # Public
@router.get("/{task_id}") # Public
```

**Authentication**:

- `/create` requires admin role (get_admin_user dependency)
- List and get endpoints are public

**Purpose**: HTTP API layer

---

## Configuration

### Environment Variables (.env)

```bash
# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=deid

# Ethereum Sepolia Testnet
TESTNET_RPC_URL=https://eth-sepolia.public.blastapi.io
EVM_RPC_URL=https://eth-sepolia.public.blastapi.io
EVM_PRIVATE_KEY=0xyour_private_key_here
EVM_CHAIN_ID=11155111

# IPFS Gateway
IPFS_GATEWAY_URL_POST=http://35.247.142.76:5001/api/v0/add
IPFS_GATEWAY_URL_GET=http://35.247.142.76:8080/ipfs

# Smart Contract (BadgeSystem via Proxy)
PROXY_ADDRESS=0xYourProxyContractAddress

# Authentication
JWT_SECRET_KEY=your-secret-key-here
```

### Config Class (`app/core/config.py`)

```python
class Settings(BaseSettings):
    # MongoDB
    MONGODB_URL: str
    MONGODB_DB_NAME: str

    # Blockchain
    TESTNET_RPC_URL: str
    EVM_PRIVATE_KEY: str
    EVM_CHAIN_ID: int = 11155111  # Sepolia

    # IPFS
    IPFS_GATEWAY_URL_POST: str
    IPFS_GATEWAY_URL_GET: str

    # Smart Contract
    PROXY_ADDRESS: Optional[str]
```

---

## Usage Examples

### Frontend Integration

#### 1. Create Task (Admin Only)

```typescript
// Create task with admin authentication
const createTask = async () => {
  const response = await fetch("http://localhost:8000/api/v1/task/create", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${adminJwtToken}`,
    },
    body: JSON.stringify({
      task_title: "Hold 100 USDC",
      task_description: "Hold at least 100 USDC in your wallet",
      validation_type: "erc20_balance_check",
      blockchain_network: "ethereum",
      token_contract_address: "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
      minimum_balance: 100,
      badge_details: {
        badge_name: "USDC Holder",
        badge_description: "Awarded for holding 100+ USDC",
        badge_image: "QmXxxxxx", // Pre-uploaded to IPFS
        attributes: [
          { trait_type: "Token", value: "USDC" },
          { trait_type: "Amount", value: "100" },
        ],
      },
    }),
  });

  const result = await response.json();

  if (response.status === 403) {
    console.error("Access denied: Admin role required");
    return;
  }

  if (result.success) {
    console.log("Task created:", result.data.id);
    console.log("TX Hash:", result.data.tx_hash);
  } else {
    console.error("Failed to create task:", result.message);
  }
};
```

#### 2. List Tasks

```typescript
// Get paginated task list
const getTasks = async (page = 1) => {
  const response = await fetch(
    `http://localhost:8000/api/v1/task/list?page=${page}&page_size=10&validation_type=erc20_balance_check`
  );

  const result = await response.json();

  if (result.success) {
    console.log("Tasks:", result.data);
    console.log("Total pages:", result.pagination.total_pages);
  }
};
```

#### 3. Display Task Details

```typescript
// Get single task
const getTaskById = async (taskId: string) => {
  const response = await fetch(`http://localhost:8000/api/v1/task/${taskId}`);

  const result = await response.json();

  if (result.success) {
    return result.data;
  }
};
```

---

## Smart Contract Integration

### BadgeSystem Contract

The system interacts with a BadgeSystem smart contract deployed behind a proxy:

**Contract Functions Used**:

```solidity
// Create a new badge type
function createBadge(string memory taskId, string memory metadataURI) external;

// Check if badge exists
function badgeExists(string memory taskId) external view returns (bool);

// Get badge metadata URI
function getBadgeMetadataURI(string memory taskId) external view returns (string memory);

// Mint badge to user (called by user after validation)
function mintBadge(string memory taskId, bytes memory signature) external;
```

**How It Works**:

1. Backend calls `createBadge(task_id, ipfs_url)` when task is created
2. Contract stores mapping: `taskId => metadataURI`
3. Users can later mint badges by calling `mintBadge(taskId, signature)`
4. Backend validates user meets requirements and signs approval

---

## Database Schema

### Tasks Collection (MongoDB)

```javascript
{
  _id: ObjectId("507f1f77bcf86cd799439011"),
  task_title: "Hold 100 USDC",
  task_description: "Hold at least 100 USDC tokens in your wallet",
  validation_type: "erc20_balance_check",
  blockchain_network: "ethereum",
  token_contract_address: "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
  minimum_balance: 100,
  badge_details: {
    badge_name: "USDC Holder",
    badge_description: "Awarded for holding 100+ USDC",
    badge_image: "QmXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    attributes: [
      {
        trait_type: "Token",
        value: "USDC"
      },
      {
        trait_type: "Minimum Amount",
        value: "100"
      }
    ]
  },
  tx_hash: "0xabcdef1234567890...",
  block_number: 4567890,
  created_at: ISODate("2025-10-18T10:30:00.000Z"),
  updated_at: ISODate("2025-10-18T10:30:15.000Z")
}
```

**Indexes**:

- `_id` - Primary key (automatic)
- `validation_type` - For filtering
- `created_at` - For sorting (descending)

---

## Error Handling

### Service Layer Errors

```python
# IPFS Upload Failure
if not ipfs_hash:
    return False, "Failed to upload badge metadata to IPFS", None

# MongoDB Failure
except Exception as e:
    return False, f"Failed to create task: {str(e)}", None

# Contract Call Failure
except Exception as contract_error:
    # Task exists in DB but not on-chain
    return False, f"Task created but contract deployment failed: {str(contract_error)}", task_data
```

### Router Layer Errors

```python
# Authentication failure (handled by get_admin_user)
# Returns 401 Unauthorized if not authenticated
# Returns 403 Forbidden if user is not admin

# Internal errors
try:
    success, message, task_data = await task_service.create_task(request)
except Exception as e:
    return TaskCreateResponseDTO(
        success=False,
        message=f"Internal server error: {str(e)}",
        data=None
    )
```

---

## Testing

### Manual Testing with cURL

```bash
# 1. Create task (requires admin auth token)
curl -X POST http://localhost:8000/api/v1/task/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_JWT_TOKEN" \
  -d '{
    "task_title": "Hold 100 USDC",
    "task_description": "Hold at least 100 USDC",
    "validation_type": "erc20_balance_check",
    "blockchain_network": "ethereum",
    "token_contract_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "minimum_balance": 100,
    "badge_details": {
      "badge_name": "USDC Holder",
      "badge_description": "Hold 100+ USDC",
      "badge_image": "QmXxx",
      "attributes": [
        {"trait_type": "Token", "value": "USDC"}
      ]
    }
  }'

# 2. List tasks (no auth)
curl http://localhost:8000/api/v1/task/list?page=1&page_size=10

# 3. Get task by ID
curl http://localhost:8000/api/v1/task/507f1f77bcf86cd799439011

# 4. Test non-admin access (should return 403 Forbidden)
curl -X POST http://localhost:8000/api/v1/task/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_NON_ADMIN_JWT_TOKEN" \
  -d '{...}'
# Response: {"detail": {"message": "Access denied. Required roles: admin. Your role: user", "error": "INSUFFICIENT_PERMISSIONS"}}
```

### Swagger UI

Access interactive API documentation:

```
http://localhost:8000/docs
```

---

## Deployment Checklist

- [ ] MongoDB is running and accessible
- [ ] IPFS gateway is accessible
- [ ] Sepolia RPC URL is working
- [ ] Private key has ETH for gas fees
- [ ] Proxy contract is deployed on Sepolia
- [ ] BadgeSystem ABI JSON is in `app/contracts/verification/BadgeSystem.sol/BadgeSystem.json`
- [ ] All environment variables are set
- [ ] JWT authentication is configured
- [ ] CORS origins are properly configured

---

## Security Considerations

1. **Private Key Management**

   - Store `EVM_PRIVATE_KEY` in environment variables
   - Never commit to version control
   - Use separate key for development/production

2. **Authentication & Authorization**

   - **Role-Based Access Control (RBAC)**: Task creation requires admin role only
   - **Admin Users**: Can create, view, and manage tasks
   - **Regular Users**: Can only view task list and task details (read-only)
   - **Error Responses**:
     - `401 Unauthorized`: Missing or invalid authentication token
     - `403 Forbidden`: Authenticated user without admin role
   - **Implementation**: Uses `get_admin_user()` dependency in FastAPI
   - Implement rate limiting for API endpoints to prevent abuse

3. **Input Validation**

   - Pydantic validates all input data
   - Contract addresses are checksummed
   - MongoDB queries are parameterized

4. **Gas Management**

   - Automatic gas estimation with 20% buffer
   - Monitor gas prices on Sepolia
   - Set reasonable gas limits

5. **IPFS Content**
   - Validate badge_image is a valid IPFS hash
   - Consider content moderation for user-submitted images

---

## Monitoring & Logging

All operations are logged with structured logging:

```python
logger.info(f"Task created in MongoDB with ID: {task_id}")
logger.info(f"Badge metadata uploaded to IPFS: {ipfs_hash}")
logger.info(f"Badge created on-chain: tx_hash={tx_hash}, block={block_number}")
logger.error(f"Error creating task: {e}", exc_info=True)
```

**Key Metrics to Monitor**:

- Task creation success rate
- IPFS upload failures
- Contract transaction failures
- Average transaction confirmation time
- Gas costs per task creation

---

## Future Enhancements

1. **Task Validation**

   - Implement actual ERC20/ERC721 balance checking
   - Add webhook for real-time validation
   - Support more validation types

2. **Badge Minting**

   - Add endpoint for users to claim badges
   - Implement signature-based minting approval
   - Track which users have earned which badges

3. **Analytics**

   - Task completion statistics
   - Popular badges dashboard
   - User leaderboards

4. **Multi-chain Support**

   - Add support for Base, BSC networks
   - Configurable RPC URLs per network
   - Cross-chain badge verification

5. **Caching**
   - Cache task list with Redis
   - Invalidate on new task creation
   - Cache IPFS metadata

---

## Troubleshooting

### Common Issues

**Issue**: `ImportError: cannot import name 'ContractClient'`

- **Solution**: Ensure `contract_client.py` contains the ContractClient class

**Issue**: `Failed to connect to Web3 provider`

- **Solution**: Check TESTNET_RPC_URL is accessible and correct

**Issue**: `PROXY_ADDRESS not configured`

- **Solution**: Add PROXY_ADDRESS to .env file

**Issue**: `Failed to upload to IPFS`

- **Solution**: Verify IPFS gateway is running at http://35.247.142.76:5001

**Issue**: `Transaction failed with status 0`

- **Solution**: Check contract function parameters and ensure wallet has ETH for gas

**Issue**: `MongoDB connection failed`

- **Solution**: Verify MongoDB is running and MONGODB_URL is correct

---

## API Versioning

Current version: **v1**

All endpoints are prefixed with `/api/v1/task/`

Future versions will use `/api/v2/task/` etc.

---

## Support & Maintenance

**Created**: October 18, 2025
**Last Updated**: October 18, 2025
**Status**: Production Ready ✅

For questions or issues, refer to this documentation or contact the development team.
