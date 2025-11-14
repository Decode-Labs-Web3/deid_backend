# Social Link Service - Discord OAuth with MongoDB Integration

This document describes the Social Link Service implementation for DEID Backend, featuring Discord OAuth verification with persistent MongoDB storage.

## Overview

The Social Link Service enables users to verify their social media accounts (Discord, Twitter, GitHub, Telegram) and link them to their decentralized identity. The service implements a secure OAuth2 flow with EIP-712 signature verification and persistent MongoDB storage for tracking verification status.

## Architecture

### Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Discord
    participant Backend
    participant MongoDB
    participant SmartContract as "Smart Contract"

    User->>Frontend: Click "Verify with Discord"
    Frontend->>Backend: GET /api/social/discord/oauth-url?user_id=0x1234
    Backend->>Frontend: Return Discord OAuth URL
    Frontend->>Discord: Redirect to OAuth2 Authorize URL
    Discord->>User: Shows consent page
    User->>Discord: Click "Authorize"
    Discord->>Backend: Redirect to /api/social/discord/callback?code=XYZ&state=deid_0x1234
    Backend->>Discord: POST /oauth2/token (exchange code → access_token)
    Discord->>Backend: Returns access_token
    Backend->>Discord: GET /users/@me (using access_token)
    Discord->>Backend: Returns user info {id, username, email}
    Backend->>Backend: Sign verification EIP-712(hash(user_id, "discord", discord_id))
    Backend->>MongoDB: Store social link record
    Backend->>Frontend: Return {platform, account_id, signature}
    Frontend->>SmartContract: call linkSocialAccount(signature, "discord", account_id)
    SmartContract-->>Frontend: emit Linked(user, "discord")
    Frontend->>Backend: POST /social/onchain-confirm {tx_hash, platform, account_id}
    Backend->>MongoDB: Update record status="onchain"
    Note over Backend,SmartContract: ✅ Discord account verified<br/>Off-chain (OAuth) + On-chain (Smart Contract) + Database (MongoDB)
```

## Components

### 1. MongoDB Models (`app/domain/models/social_link.py`)

- **SocialLinkModel**: Main MongoDB document model
- **SocialPlatform**: Enum for supported platforms
- **VerificationStatus**: Enum for verification states
- **SocialLinkCreateModel**: Model for creating new social links
- **SocialLinkUpdateModel**: Model for updating existing social links
- **SocialLinkQueryModel**: Model for querying social links

### 2. Repository Layer (`app/domain/repositories/social_link_repository.py`)

- **SocialLinkRepository**: MongoDB repository with full CRUD operations
- **create_social_link()**: Create new social link with unique constraints
- **get_social_link()**: Get social link by user_id and platform
- **get_user_social_links()**: Get all social links for a user
- **update_social_link()**: Update social link status and metadata
- **delete_social_link()**: Remove social link
- **get_social_link_stats()**: Get verification statistics for a user

### 3. Service Layer (`app/api/services/social_link_service.py`)

- **SocialLinkService**: Main service class handling business logic
- **get_discord_oauth_url()**: Generates Discord OAuth authorization URL
- **handle_discord_oauth_callback()**: Processes OAuth callback and stores in MongoDB
- **confirm_onchain_verification_with_user_id()**: Updates status after smart contract confirmation
- **get_user_social_links()**: Retrieves all social links for a user
- **get_user_social_link_stats()**: Gets verification statistics

### 4. API Layer (`app/api/routers/social_link_router.py`)

- **GET /discord/oauth-url**: Get Discord OAuth authorization URL
- **GET /discord/callback**: Handle Discord OAuth callback
- **POST /onchain-confirm**: Confirm onchain verification
- **GET /links/{user_id}**: Get user's social links (with optional status filter)
- **GET /stats/{user_id}**: Get user's social link statistics
- **GET /health**: Health check endpoint

### 5. DTOs (`app/api/dto/social_dto.py`)

- **SocialLinkDataDTO**: Complete social link data structure
- **SocialVerificationResponseDTO**: Standardized response format
- **SocialLinksListResponseDTO**: Response for multiple social links
- **SocialLinkStatsDTO**: Statistics data structure
- **SocialLinkStatsResponseDTO**: Statistics response format

## Database Schema

### Social Links Collection

```javascript
{
  "_id": ObjectId,
  "user_id": "0x1234567890abcdef",           // User's wallet address
  "platform": "discord",                     // Social platform
  "account_id": "123456789012345678",        // Social account ID
  "username": "username#1234",               // Social username
  "email": "user@example.com",               // Social email (optional)
  "display_name": "Username#1234",           // Display name
  "avatar_url": "https://cdn.discordapp.com/...", // Avatar URL
  "signature": "0x...",                      // EIP-712 signature
  "verification_hash": "0x...",              // Verification hash
  "status": "verified",                      // Status: pending, verified, onchain, failed
  "tx_hash": "0x...",                        // Transaction hash (when onchain)
  "block_number": 12345,                     // Block number (when onchain)
  "created_at": ISODate,                     // Creation timestamp
  "updated_at": ISODate                      // Last update timestamp
}
```

### Indexes

- **Compound Index**: `(user_id, platform)` - Unique constraint
- **User Index**: `user_id` - For user queries
- **Platform Index**: `platform` - For platform queries
- **Status Index**: `status` - For status filtering
- **Created At Index**: `created_at` - For chronological ordering

## API Endpoints

### 1. Get Discord OAuth URL

```http
GET /api/v1/social/discord/oauth-url?user_id=0x1234567890abcdef
```

**Response:**

```json
{
  "success": true,
  "oauth_url": "https://discord.com/oauth2/authorize?client_id=...",
  "message": "Discord OAuth URL generated successfully"
}
```

### 2. Discord OAuth Callback

```http
GET /api/v1/social/discord/callback?code=XYZ&state=deid_0x1234567890abcdef
```

**Response:**

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Discord account verified successfully",
  "data": {
    "id": "mongodb_document_id",
    "user_id": "0x1234567890abcdef",
    "platform": "discord",
    "account_id": "123456789012345678",
    "username": "username#1234",
    "email": "user@example.com",
    "display_name": "Username#1234",
    "avatar_url": "https://cdn.discordapp.com/...",
    "signature": "0x...",
    "verification_hash": "0x...",
    "status": "verified",
    "tx_hash": null,
    "block_number": null,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  },
  "requestId": "uuid-here"
}
```

### 3. Onchain Confirmation

```http
POST /api/v1/social/onchain-confirm?user_id=0x1234567890abcdef
Content-Type: application/json

{
  "tx_hash": "0xabcdef1234567890...",
  "platform": "discord",
  "account_id": "123456789012345678"
}
```

**Response:**

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Onchain verification confirmed successfully",
  "data": {
    "id": "mongodb_document_id",
    "user_id": "0x1234567890abcdef",
    "platform": "discord",
    "account_id": "123456789012345678",
    "username": "username#1234",
    "email": "user@example.com",
    "display_name": "Username#1234",
    "avatar_url": "https://cdn.discordapp.com/...",
    "signature": "0x...",
    "verification_hash": "0x...",
    "status": "onchain",
    "tx_hash": "0xabcdef1234567890...",
    "block_number": null,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:01:00Z"
  },
  "requestId": "uuid-here"
}
```

### 4. Get User Social Links

```http
GET /api/v1/social/links/0x1234567890abcdef
GET /api/v1/social/links/0x1234567890abcdef?status=verified
GET /api/v1/social/links/0x1234567890abcdef?status=onchain
```

**Response:**

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Social links retrieved successfully",
  "data": [
    {
      "id": "mongodb_document_id",
      "user_id": "0x1234567890abcdef",
      "platform": "discord",
      "account_id": "123456789012345678",
      "username": "username#1234",
      "email": "user@example.com",
      "display_name": "Username#1234",
      "avatar_url": "https://cdn.discordapp.com/...",
      "signature": "0x...",
      "verification_hash": "0x...",
      "status": "onchain",
      "tx_hash": "0xabcdef1234567890...",
      "block_number": null,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:01:00Z"
    }
  ],
  "requestId": "uuid-here"
}
```

### 5. Get User Social Link Statistics

```http
GET /api/v1/social/stats/0x1234567890abcdef
```

**Response:**

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Social link statistics retrieved successfully",
  "data": {
    "total": 3,
    "verified": 2,
    "onchain": 1,
    "pending": 0,
    "failed": 0
  },
  "requestId": "uuid-here"
}
```

## Setup Instructions

### 1. Environment Configuration

Add the following to your `.env` file:

```env
# MongoDB Configuration
MONGO_URI=mongodb+srv://decodenetworkweb3:decodenetworkweb3@cluster0.nyqsoth.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
MONGO_DB_NAME=deid
MONGO_USER=decodenetworkweb3
MONGO_PASSWORD=decodenetworkweb3

# Discord OAuth Configuration
DISCORD_CLIENT_ID=your_discord_client_id
DISCORD_CLIENT_SECRET=your_discord_client_secret
DISCORD_REDIRECT_URI=https://api.de-id.xyz/api/v1/social/discord/callback

# Social Link Backend Signing
SOCIAL_LINK_PRIVATE_KEY=your_private_key_for_signing
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Discord Application Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to OAuth2 settings
4. Add redirect URI: `https://api.de-id.xyz/api/v1/social/discord/callback`
5. Copy Client ID and Client Secret to your `.env` file

### 4. Run the Application

```bash
python -m uvicorn app.main:app --reload
```

## Testing

### 1. Run Test Script

```bash
python test_social_link_service.py
```

### 2. Manual Testing

1. **Get OAuth URL:**

   ```bash
   curl "https://api.de-id.xyz/api/v1/social/discord/oauth-url?user_id=0x1234567890abcdef"
   ```

2. **Health Check:**

   ```bash
   curl "https://api.de-id.xyz/api/v1/social/health"
   ```

3. **Get Social Links:**

   ```bash
   curl "https://api.de-id.xyz/api/v1/social/links/0x1234567890abcdef"
   curl "https://api.de-id.xyz/api/v1/social/links/0x1234567890abcdef?status=verified"
   ```

4. **Get Statistics:**
   ```bash
   curl "https://api.de-id.xyz/api/v1/social/stats/0x1234567890abcdef"
   ```

## Database Operations

### Query Examples

```javascript
// Get all social links for a user
db.social_links.find({ user_id: "0x1234567890abcdef" });

// Get verified social links only
db.social_links.find({ user_id: "0x1234567890abcdef", status: "verified" });

// Get onchain social links
db.social_links.find({ user_id: "0x1234567890abcdef", status: "onchain" });

// Get Discord links specifically
db.social_links.find({ user_id: "0x1234567890abcdef", platform: "discord" });

// Get statistics
db.social_links.aggregate([
  { $match: { user_id: "0x1234567890abcdef" } },
  { $group: { _id: "$status", count: { $sum: 1 } } },
]);
```

## Security Features

### 1. CSRF Protection

- State parameter includes user ID for CSRF protection
- Format: `deid_{user_id}`

### 2. EIP-712 Signature

- Uses existing `signature_utils.py` for consistent signing
- Creates deterministic hash from user_id, platform, and account_id
- Signature can be verified on-chain

### 3. Database Security

- Unique constraints prevent duplicate social links
- Proper indexing for performance and data integrity
- Automatic timestamps for audit trails

### 4. Token Management

- Access tokens are used immediately and not stored
- Verification data stored persistently in MongoDB
- Automatic status tracking and updates

## Integration with Smart Contract

The service generates EIP-712 compatible signatures that can be used with smart contracts:

```solidity
function linkSocialAccount(
    bytes memory signature,
    string memory platform,
    string memory accountId
) external {
    // Verify signature
    bytes32 messageHash = keccak256(abi.encodePacked(msg.sender, platform, accountId));
    address signer = ECDSA.recover(messageHash, signature);
    require(signer == authorizedSigner, "Invalid signature");

    // Link account
    socialLinks[msg.sender][platform] = accountId;
    emit Linked(msg.sender, platform, accountId);
}
```

## Future Enhancements

1. **Additional Platforms**: Twitter, GitHub, Telegram OAuth integration
2. **Advanced Filtering**: Date ranges, platform combinations
3. **Batch Operations**: Multiple social account verification
4. **Webhook Support**: Real-time updates from social platforms
5. **Analytics**: Detailed verification statistics and trends
6. **Caching**: Redis caching for frequently accessed data
7. **Rate Limiting**: API rate limiting for OAuth endpoints

## Error Handling

The service includes comprehensive error handling:

- **OAuth Errors**: Invalid codes, expired tokens, network issues
- **Database Errors**: Connection issues, constraint violations, data corruption
- **Signature Errors**: Invalid private keys, signing failures
- **Validation Errors**: Invalid input parameters, malformed requests

All errors are logged and return standardized error responses with appropriate HTTP status codes.

## Monitoring and Logging

- **Structured Logging**: JSON-formatted logs for easy parsing
- **Error Tracking**: Comprehensive error logging with context
- **Performance Monitoring**: Database query performance tracking
- **Health Checks**: Service health monitoring endpoints
