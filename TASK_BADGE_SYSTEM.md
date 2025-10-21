# Task & Badge Management System Documentation

## Overview

The Task & Badge Management System allows administrators to create on-chain verification tasks that users can complete to earn NFT badges. The system integrates MongoDB for data storage, IPFS for metadata hosting, and Ethereum smart contracts for on-chain badge minting.

### Access Control

- **Task Creation**: Admin role required (enforced via `get_admin_user()` dependency)
- **Task Viewing**: Public access (no authentication required)
- **Task Types Supported**: ERC20 balance verification, ERC721 balance verification

### Filtering Capabilities

Users can filter tasks with **multi-select** support:

- **Type**: `token` (ERC20) and/or `nft` (ERC721) - can select one or both
- **Network**: `ethereum`, `bsc`, `base` - can select one, two, or all three
- **Default**: If no filters specified, shows tasks from ALL types and ALL networks

Examples:

- All tasks: `GET /api/v1/task/list`
- Only Ethereum and BSC: `GET /api/v1/task/list?network=ethereum&network=bsc`
- Token tasks on all networks: `GET /api/v1/task/list?type=token`

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Data Flow](#data-flow)
3. [API Endpoints](#api-endpoints)
4. [Task Filtering](#task-filtering)
5. [Code Structure](#code-structure)
6. [Configuration](#configuration)
7. [Usage Examples](#usage-examples)

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
- `type` (array of strings, optional) - Filter by task types (multi-select)
  - `token` - ERC20 token balance verification tasks
  - `nft` - ERC721 NFT ownership verification tasks
  - Can pass multiple values: `type=token&type=nft` (shows both)
  - Default: Shows all types if not specified
- `network` (array of strings, optional) - Filter by blockchain networks (multi-select)
  - `ethereum` - Ethereum mainnet/testnet
  - `bsc` - Binance Smart Chain
  - `base` - Base network
  - Can pass multiple values: `network=ethereum&network=bsc` (shows both)
  - Default: Shows all networks if not specified

**Example Requests**:

```
# Get all tasks (all types, all networks)
GET /api/v1/task/list?page=1&page_size=10

# Filter by single task type (token tasks only)
GET /api/v1/task/list?page=1&page_size=10&type=token

# Filter by multiple task types (both token and nft)
GET /api/v1/task/list?page=1&page_size=10&type=token&type=nft

# Filter by single network (Ethereum only)
GET /api/v1/task/list?page=1&page_size=10&network=ethereum

# Filter by multiple networks (Ethereum and BSC, exclude Base)
GET /api/v1/task/list?page=1&page_size=10&network=ethereum&network=bsc

# Combine filters: Token tasks on Ethereum and Base (exclude BSC)
GET /api/v1/task/list?page=1&page_size=10&type=token&network=ethereum&network=base

# Show all types but only on Ethereum
GET /api/v1/task/list?page=1&page_size=10&network=ethereum
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

**Error Response (Invalid Filter)**:

```json
{
  "success": false,
  "message": "Invalid type filter. Allowed values: 'token', 'nft'",
  "data": [],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_count": 0,
    "total_pages": 0
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

## Task Filtering

The task list endpoint supports **multi-select filtering** capabilities to help users find relevant tasks quickly. Users can select multiple values for each filter category.

### Filter Behavior

- **Default (No Filters)**: Shows ALL tasks from ALL types and ALL networks
- **Multi-Select**: Users can select multiple values for each filter
- **Flexible**: Can select any combination (e.g., Ethereum + BSC only, exclude Base)

### Available Filters

#### 1. Type Filter (`type`) - Multi-Select

Filter tasks by their validation type. Can select one or both:

| Value   | Description                             | Internal Mapping       |
| ------- | --------------------------------------- | ---------------------- |
| `token` | ERC20 token balance verification tasks  | `erc20_balance_check`  |
| `nft`   | ERC721 NFT ownership verification tasks | `erc721_balance_check` |

**Examples**:

```
# Only token tasks
GET /api/v1/task/list?type=token

# Only NFT tasks
GET /api/v1/task/list?type=nft

# Both token AND nft tasks (explicitly select both)
GET /api/v1/task/list?type=token&type=nft
```

**Use Cases**:

- Show only token tasks for DeFi-focused users
- Show only NFT tasks for collectors
- Allow users to toggle between task types
- Let users select which types they want to see

---

#### 2. Network Filter (`network`) - Multi-Select

Filter tasks by blockchain network. Can select one, two, or all three:

| Value      | Description              | Use Case                    |
| ---------- | ------------------------ | --------------------------- |
| `ethereum` | Ethereum mainnet/testnet | Tasks on Ethereum ecosystem |
| `bsc`      | Binance Smart Chain      | Tasks on BSC ecosystem      |
| `base`     | Base network             | Tasks on Base L2            |

**Examples**:

```
# Only Ethereum tasks
GET /api/v1/task/list?network=ethereum

# Ethereum AND BSC (exclude Base)
GET /api/v1/task/list?network=ethereum&network=bsc

# Only Base tasks (exclude Ethereum and BSC)
GET /api/v1/task/list?network=base

# All three networks (explicit, same as no filter)
GET /api/v1/task/list?network=ethereum&network=bsc&network=base
```

**Use Cases**:

- Show tasks for user's connected wallet network
- Filter by gas cost preferences (L2 vs mainnet)
- Allow users to uncheck networks they're not interested in
- Users can select "Ethereum + Base" only

---

#### 3. Combined Multi-Select Filters

Combine both filters with multi-select for precise queries:

**Examples**:

```
# Token tasks on Ethereum AND BSC (no Base, no NFT)
GET /api/v1/task/list?type=token&network=ethereum&network=bsc

# NFT tasks on Base only
GET /api/v1/task/list?type=nft&network=base

# Both types (token + nft) but only on Ethereum
GET /api/v1/task/list?type=token&type=nft&network=ethereum

# Token tasks on all networks (default networks)
GET /api/v1/task/list?type=token
```

---

### Filter Validation

The API validates filter parameters and returns helpful error messages:

**Invalid Type Filter**:

```json
{
  "success": false,
  "message": "Invalid type filter. Allowed values: 'token', 'nft'",
  "data": [],
  "pagination": {...}
}
```

**Invalid Network Filter**:

```json
{
  "success": false,
  "message": "Invalid network filter. Allowed values: ethereum, bsc, base",
  "data": [],
  "pagination": {...}
}
```

---

### Frontend Implementation Example

```typescript
interface TaskFilters {
  page?: number;
  pageSize?: number;
  types?: Array<"token" | "nft">; // Multi-select
  networks?: Array<"ethereum" | "bsc" | "base">; // Multi-select
}

const fetchTasks = async (filters: TaskFilters) => {
  const params = new URLSearchParams();

  if (filters.page) params.append("page", filters.page.toString());
  if (filters.pageSize) params.append("page_size", filters.pageSize.toString());

  // Add multiple type filters
  if (filters.types) {
    filters.types.forEach((type) => params.append("type", type));
  }

  // Add multiple network filters
  if (filters.networks) {
    filters.networks.forEach((network) => params.append("network", network));
  }

  const response = await fetch(
    `http://localhost:8000/api/v1/task/list?${params.toString()}`
  );

  return response.json();
};

// Usage examples

// All tasks (no filters)
await fetchTasks({});

// Only token tasks (all networks)
await fetchTasks({ types: ["token"] });

// Only NFT tasks (all networks)
await fetchTasks({ types: ["nft"] });

// Both types (all networks)
await fetchTasks({ types: ["token", "nft"] });

// Only Ethereum tasks (all types)
await fetchTasks({ networks: ["ethereum"] });

// Ethereum AND BSC only (exclude Base, all types)
await fetchTasks({ networks: ["ethereum", "bsc"] });

// Token tasks on Ethereum AND Base (no BSC, no NFT)
await fetchTasks({
  types: ["token"],
  networks: ["ethereum", "base"],
});

// All types but only on BSC
await fetchTasks({ networks: ["bsc"] });
```

### React Component Example (Checkboxes)

```tsx
import React, { useState, useEffect } from "react";

const TaskFilterComponent = () => {
  const [selectedTypes, setSelectedTypes] = useState<string[]>([
    "token",
    "nft",
  ]);
  const [selectedNetworks, setSelectedNetworks] = useState<string[]>([
    "ethereum",
    "bsc",
    "base",
  ]);
  const [tasks, setTasks] = useState([]);

  // Fetch tasks when filters change
  useEffect(() => {
    const loadTasks = async () => {
      const result = await fetchTasks({
        types: selectedTypes.length > 0 ? selectedTypes : undefined,
        networks: selectedNetworks.length > 0 ? selectedNetworks : undefined,
      });
      if (result.success) {
        setTasks(result.data);
      }
    };
    loadTasks();
  }, [selectedTypes, selectedNetworks]);

  const toggleType = (type: string) => {
    setSelectedTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  const toggleNetwork = (network: string) => {
    setSelectedNetworks((prev) =>
      prev.includes(network)
        ? prev.filter((n) => n !== network)
        : [...prev, network]
    );
  };

  return (
    <div>
      <div>
        <h3>Task Type</h3>
        <label>
          <input
            type="checkbox"
            checked={selectedTypes.includes("token")}
            onChange={() => toggleType("token")}
          />
          Token (ERC20)
        </label>
        <label>
          <input
            type="checkbox"
            checked={selectedTypes.includes("nft")}
            onChange={() => toggleType("nft")}
          />
          NFT (ERC721)
        </label>
      </div>

      <div>
        <h3>Network</h3>
        <label>
          <input
            type="checkbox"
            checked={selectedNetworks.includes("ethereum")}
            onChange={() => toggleNetwork("ethereum")}
          />
          Ethereum
        </label>
        <label>
          <input
            type="checkbox"
            checked={selectedNetworks.includes("bsc")}
            onChange={() => toggleNetwork("bsc")}
          />
          BSC
        </label>
        <label>
          <input
            type="checkbox"
            checked={selectedNetworks.includes("base")}
            onChange={() => toggleNetwork("base")}
          />
          Base
        </label>
      </div>

      <div>
        <h3>Tasks</h3>
        {tasks.map((task) => (
          <div key={task.id}>{task.task_title}</div>
        ))}
      </div>
    </div>
  );
};
```

---

### Database Indexing Recommendations

For optimal query performance with filters, create these MongoDB indexes:

```javascript
// Compound index for filtering and sorting
db.tasks.createIndex({
  validation_type: 1,
  blockchain_network: 1,
  created_at: -1,
});

// Individual indexes for each filter
db.tasks.createIndex({ validation_type: 1 });
db.tasks.createIndex({ blockchain_network: 1 });
db.tasks.createIndex({ created_at: -1 });
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
    async def get_tasks_paginated(skip, limit, validation_types, blockchain_networks) -> tuple[List[dict], int]
    async def update_task_contract_data(task_id, tx_hash, block_number) -> bool
```

**Key Features**:

- Async MongoDB operations using Motor
- Automatic timestamps (created_at, updated_at)
- Pagination support with total count
- **Multi-select filtering** by validation types (ERC20/ERC721) - accepts list of types
- **Multi-select filtering** by blockchain networks (ethereum/bsc/base) - accepts list of networks
- Uses MongoDB `$in` operator for efficient multi-value queries
- Supports combined filters for precise queries (e.g., token tasks on Ethereum + BSC only)

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
    async def get_tasks_paginated(page, page_size, validation_types, blockchain_networks)
    async def get_task_by_id(task_id)
```

**Key Updates**:

- Accepts lists for `validation_types` and `blockchain_networks` parameters
- Enables multi-select filtering at service layer

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

#### 2. List Tasks (Multi-Select Filters)

```typescript
// Get all tasks (no filters - shows all types and networks)
const getAllTasks = async (page = 1) => {
  const response = await fetch(
    `http://localhost:8000/api/v1/task/list?page=${page}&page_size=10`
  );

  const result = await response.json();

  if (result.success) {
    console.log("All Tasks:", result.data);
    console.log("Total pages:", result.pagination.total_pages);
  }
};

// Get token tasks only (all networks)
const getTokenTasks = async (page = 1) => {
  const response = await fetch(
    `http://localhost:8000/api/v1/task/list?page=${page}&page_size=10&type=token`
  );

  const result = await response.json();

  if (result.success) {
    console.log("Token Tasks:", result.data);
  }
};

// Get both token AND nft tasks (all networks)
const getBothTypesTasks = async (page = 1) => {
  const response = await fetch(
    `http://localhost:8000/api/v1/task/list?page=${page}&page_size=10&type=token&type=nft`
  );

  const result = await response.json();

  if (result.success) {
    console.log("Token + NFT Tasks:", result.data);
  }
};

// Get Ethereum tasks only (all types)
const getEthereumTasks = async (page = 1) => {
  const response = await fetch(
    `http://localhost:8000/api/v1/task/list?page=${page}&page_size=10&network=ethereum`
  );

  const result = await response.json();

  if (result.success) {
    console.log("Ethereum Tasks:", result.data);
  }
};

// Get Ethereum AND BSC tasks (exclude Base, all types)
const getEthAndBscTasks = async (page = 1) => {
  const response = await fetch(
    `http://localhost:8000/api/v1/task/list?page=${page}&page_size=10&network=ethereum&network=bsc`
  );

  const result = await response.json();

  if (result.success) {
    console.log("Ethereum + BSC Tasks:", result.data);
  }
};

// Token tasks on Ethereum AND Base (exclude BSC and NFT tasks)
const getTokenOnEthAndBase = async (page = 1) => {
  const response = await fetch(
    `http://localhost:8000/api/v1/task/list?page=${page}&page_size=10&type=token&network=ethereum&network=base`
  );

  const result = await response.json();

  if (result.success) {
    console.log("Token Tasks on Ethereum + Base:", result.data);
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

**Indexes** (Recommended):

- `_id` - Primary key (automatic)
- `validation_type` - For type filtering (token/nft)
- `blockchain_network` - For network filtering (ethereum/bsc/base)
- `created_at` - For sorting (descending)
- Compound index: `(validation_type, blockchain_network, created_at)` - For optimal combined filter queries

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

# 2. List all tasks (no filters - shows all types and networks)
curl http://localhost:8000/api/v1/task/list?page=1&page_size=10

# 3. List token tasks only (all networks)
curl http://localhost:8000/api/v1/task/list?page=1&page_size=10&type=token

# 4. List NFT tasks only (all networks)
curl http://localhost:8000/api/v1/task/list?page=1&page_size=10&type=nft

# 5. List both token AND nft tasks (all networks)
curl "http://localhost:8000/api/v1/task/list?page=1&page_size=10&type=token&type=nft"

# 6. List Ethereum tasks only (all types)
curl http://localhost:8000/api/v1/task/list?page=1&page_size=10&network=ethereum

# 7. List Ethereum AND BSC tasks (exclude Base, all types)
curl "http://localhost:8000/api/v1/task/list?page=1&page_size=10&network=ethereum&network=bsc"

# 8. List Base network tasks only (all types)
curl http://localhost:8000/api/v1/task/list?page=1&page_size=10&network=base

# 9. Token tasks on Ethereum only
curl http://localhost:8000/api/v1/task/list?page=1&page_size=10&type=token&network=ethereum

# 10. Token tasks on Ethereum AND Base (exclude BSC)
curl "http://localhost:8000/api/v1/task/list?page=1&page_size=10&type=token&network=ethereum&network=base"

# 11. NFT tasks on all three networks (explicit)
curl "http://localhost:8000/api/v1/task/list?page=1&page_size=10&type=nft&network=ethereum&network=bsc&network=base"

# 12. Get task by ID
curl http://localhost:8000/api/v1/task/507f1f77bcf86cd799439011

# 13. Test non-admin access (should return 403 Forbidden)
curl -X POST http://localhost:8000/api/v1/task/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_NON_ADMIN_JWT_TOKEN" \
  -d '{...}'
# Response: {"detail": {"message": "Access denied. Required roles: admin. Your role: user", "error": "INSUFFICIENT_PERMISSIONS"}}

# 14. Test invalid type filter (should return error)
curl http://localhost:8000/api/v1/task/list?page=1&page_size=10&type=invalid
# Response: {"success": false, "message": "Invalid type filter 'invalid'. Allowed values: 'token', 'nft'", ...}

# 15. Test invalid network filter (should return error)
curl http://localhost:8000/api/v1/task/list?page=1&page_size=10&network=polygon
# Response: {"success": false, "message": "Invalid network filter 'polygon'. Allowed values: ethereum, bsc, base", ...}
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
**Last Updated**: October 21, 2025
**Status**: Production Ready ✅

**Recent Updates**:

- ✅ Added **multi-select** task filtering by type (token/nft)
- ✅ Added **multi-select** task filtering by network (ethereum/bsc/base)
- ✅ Support for combined filters with multiple selections
- ✅ Users can select any combination (e.g., Ethereum + BSC only, exclude Base)
- ✅ Input validation for filter parameters
- ✅ MongoDB `$in` operator for efficient multi-value queries

For questions or issues, refer to this documentation or contact the development team.
