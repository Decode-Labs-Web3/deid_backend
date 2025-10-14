# Insomnia Testing Guide for Social Link Service

This guide will help you set up and test the Social Link Service using Insomnia.

## 🔧 **Setup Instructions**

### 1. **Get Discord OAuth Credentials**

1. **Go to Discord Developer Portal**

   - Visit: https://discord.com/developers/applications
   - Click "New Application"
   - Name it: "DEID Social Verification"

2. **Get Client ID**

   - In the "General Information" tab
   - Copy the **Application ID** (this is your `DISCORD_CLIENT_ID`)

3. **Get Client Secret**

   - Go to "OAuth2" → "General"
   - Click "Reset Secret"
   - Copy the **Client Secret** (this is your `DISCORD_CLIENT_SECRET`)

4. **Set Redirect URI**
   - In "OAuth2" → "General"
   - Add redirect URI: `http://localhost:8000/api/v1/social/discord/callback`

### 2. **Generate Private Key**

Run this command to generate a private key:

```bash
python -c "import secrets; print('0x' + secrets.token_hex(32))"
```

**Example output:** `0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef`

### 3. **Update .env File**

Add these lines to your `.env` file:

```env
# Discord OAuth Configuration
DISCORD_CLIENT_ID=your_actual_discord_client_id_here
DISCORD_CLIENT_SECRET=your_actual_discord_client_secret_here
DISCORD_REDIRECT_URI=http://localhost:8000/api/v1/social/discord/callback

# Social Link Backend Signing
SOCIAL_LINK_PRIVATE_KEY=0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
```

### 4. **Start the Application**

```bash
python -m uvicorn app.main:app --reload
```

## 📋 **Import Insomnia Collection**

1. **Open Insomnia**
2. **Import Collections**

### **Step 1: Health Check**

- **Request:** `Health Check`
- **Expected:** Status 200, service healthy
- **Purpose:** Verify the service is running

### **Step 2: Get Discord OAuth URL**

- **Request:** `Get Discord OAuth URL`
- **Expected:** Status 200, OAuth URL returned
- **Purpose:** Generate Discord authorization URL

### **Step 3: Get User Social Links (Initial)**

- **Request:** `Get User Social Links`
- **Expected:** Status 200, empty array
- **Purpose:** Check initial state (no social links)

### **Step 4: Get User Social Link Stats (Initial)**

- **Request:** `Get User Social Link Stats`
- **Expected:** Status 200, all counts = 0
- **Purpose:** Check initial statistics

### **Step 5: Discord OAuth Callback (Simulated)**

- **Request:** `Discord OAuth Callback`
- **Expected:** Status 500 (expected - requires real OAuth flow)
- **Purpose:** Test callback endpoint structure

### **Step 6: Confirm Onchain Verification (Simulated)**

- **Request:** `Confirm Onchain Verification`
- **Expected:** Status 404 (expected - no social link exists yet)
- **Purpose:** Test onchain confirmation endpoint

### **Step 7: Test Status Filtering**

- **Request:** `Get User Social Links (Verified Only)`
- **Request:** `Get User Social Links (Onchain Only)`
- **Expected:** Status 200, empty arrays
- **Purpose:** Test filtering functionality

## 🔍 **Expected Responses**

### **Health Check Response**

```json
{
  "status": "healthy",
  "service": "social_link",
  "functions": [
    "discord_oauth_verification",
    "onchain_confirmation",
    "social_links_management"
  ],
  "supported_platforms": ["discord", "twitter", "github", "telegram"]
}
```

### **Get Discord OAuth URL Response**

```json
{
  "success": true,
  "oauth_url": "https://discord.com/oauth2/authorize?client_id=...",
  "message": "Discord OAuth URL generated successfully"
}
```

### **Get User Social Links Response**

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Social links retrieved successfully",
  "data": [],
  "requestId": null
}
```

### **Get User Social Link Stats Response**

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Social link statistics retrieved successfully",
  "data": {
    "total": 0,
    "verified": 0,
    "onchain": 0,
    "pending": 0,
    "failed": 0
  },
  "requestId": null
}
```

## 🚨 **Common Issues & Solutions**

### **Issue: "Discord client ID not configured"**

**Solution:** Make sure you've added `DISCORD_CLIENT_ID` to your `.env` file

### **Issue: "Social link private key not configured"**

**Solution:** Make sure you've added `SOCIAL_LINK_PRIVATE_KEY` to your `.env` file

### **Issue: MongoDB connection errors**

**Solution:** Check your `MONGO_URI` in `.env` file

### **Issue: Discord OAuth callback fails**

**Expected:** This is normal without real OAuth flow. The endpoint structure is tested.

## 🔄 **Real OAuth Flow Testing**

To test the complete OAuth flow:

1. **Get OAuth URL** from the API
2. **Visit the URL** in your browser
3. **Authorize** the Discord application
4. **Copy the code** from the redirect URL
5. **Update** the `discord_auth_code` environment variable
6. **Test** the callback endpoint

## 📊 **Environment Variables**

The Insomnia collection uses these environment variables:

- `base_url`: `http://localhost:8000`
- `test_user_id`: `0x1234567890abcdef1234567890abcdef12345678`
- `test_discord_account_id`: `123456789012345678`
- `test_tx_hash`: `0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890`
- `discord_auth_code`: `simulated_auth_code_xyz123`

You can modify these values in the Insomnia environment to test with different data.

## 🎯 **Success Criteria**

✅ **All tests pass** when:

- Health check returns 200
- OAuth URL generation works
- Social links endpoints return proper JSON
- Statistics endpoint works
- Error handling works for invalid requests

## 📝 **Next Steps**

After successful testing:

1. **Set up real Discord application** with proper redirect URIs
2. **Test complete OAuth flow** with real Discord authorization
3. **Integrate with smart contract** for onchain verification
4. **Add more social platforms** (Twitter, GitHub, Telegram)
