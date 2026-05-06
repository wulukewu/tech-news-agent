# Discord OAuth & Bot DM Setup Guide

Complete guide for configuring Discord OAuth2 login and enabling bot DM notifications for all users.

## 📖 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Step 1: Discord Developer Portal](#step-1-discord-developer-portal)
- [Step 2: Create a Discord Server](#step-2-create-a-discord-server)
- [Step 3: Add Bot to Server](#step-3-add-bot-to-server)
- [Step 4: Configure Environment Variables](#step-4-configure-environment-variables)
- [Step 5: Verify the Flow](#step-5-verify-the-flow)
- [How It Works](#how-it-works)
- [Troubleshooting](#troubleshooting)

---

## Overview

Tech News Agent uses Discord OAuth2 for authentication. When a user logs in, the backend:

1. Authenticates the user via Discord OAuth2 (`identify` + `guilds.join` scopes)
2. Automatically adds the user to your Discord server using the `guilds.join` scope
3. Issues a JWT token for the web session

Because the user and the bot are now in the same server, the bot can send DMs to the user.

> **Note:** DMs can still fail if the user has disabled "Allow direct messages from server members" in their Discord privacy settings. This is user-controlled and cannot be bypassed.

---

## Prerequisites

- A Discord account
- A Discord application with a bot created at [discord.com/developers/applications](https://discord.com/developers/applications)
- Backend running with valid `DISCORD_TOKEN`, `DISCORD_CLIENT_ID`, and `DISCORD_CLIENT_SECRET`

---

## Step 1: Discord Developer Portal

### 1.1 OAuth2 Scopes

No manual scope configuration is needed in the portal — scopes are set in code. The backend requests:

| Scope | Purpose |
|-------|---------|
| `identify` | Read user's username, avatar, and ID |
| `guilds.join` | Add the user to your server automatically |

### 1.2 Redirect URIs

In your application → **OAuth2** → **Redirects**, add:

```
# Development
http://localhost:8000/api/auth/discord/callback

# Production
https://your-api-domain.com/api/auth/discord/callback
```

Click **Save Changes**.

### 1.3 Bot Permissions

In your application → **Bot**:

- Enable **Server Members Intent** under Privileged Gateway Intents
- Ensure the bot token is copied to `DISCORD_TOKEN` in your `.env`

---

## Step 2: Create a Discord Server

The bot needs to share a server with users to send them DMs.

1. Open Discord
2. Click **+** in the left sidebar → **Create My Own** → **For me and my friends**
3. Give it a name (e.g., `Tech News Agent`)
4. Click **Create**

### Get the Server ID

1. Go to Discord **Settings** → **Advanced** → enable **Developer Mode**
2. Right-click your server icon → **Copy Server ID**
3. Save this ID — you'll need it for `DISCORD_GUILD_ID`

---

## Step 3: Add Bot to Server

1. Go to [discord.com/developers/applications](https://discord.com/developers/applications) → your app
2. Navigate to **OAuth2** → **URL Generator**
3. Under **Scopes**, check `bot`
4. Under **Bot Permissions**, check:
   - `Send Messages`
   - `Create Instant Invite` ← required for `guilds.join` to work
5. Copy the generated URL, open it in a browser
6. Select your server → **Authorize**

Verify the bot appears in your server's member list.

---

## Step 4: Configure Environment Variables

Add the following to your `.env`:

```bash
# Required for auto-join and DM support
DISCORD_GUILD_ID=your_server_id_here
```

Full Discord-related variables:

```bash
# Bot
DISCORD_TOKEN=your_discord_bot_token_here

# OAuth2
DISCORD_CLIENT_ID=your_discord_client_id_here
DISCORD_CLIENT_SECRET=your_discord_client_secret_here
DISCORD_REDIRECT_URI=http://localhost:8000/api/auth/discord/callback

# Guild (server) for auto-join
DISCORD_GUILD_ID=your_server_id_here
```

---

## Step 5: Verify the Flow

1. Start the backend and frontend
2. Visit `http://localhost:3000` and click **Login with Discord**
3. The Discord authorization page should show:
   - ✅ Access your username, avatar, and banner (`identify`)
   - ✅ Join servers for you (`guilds.join`)
4. After authorizing, you should be redirected to the dashboard
5. Check your Discord server — the user should now appear as a member
6. The bot can now send DMs to that user

---

## How It Works

### OAuth Login Flow

```
User clicks "Login with Discord"
    ↓
Backend redirects to Discord OAuth
(scope: identify guilds.join)
    ↓
User authorizes on Discord
    ↓
Discord redirects to /api/auth/discord/callback?code=xxx
    ↓
Backend:
  1. Exchanges code for access_token
  2. Fetches user info (/users/@me)
  3. Calls PUT /guilds/{guild_id}/members/{user_id}
     → Adds user to your server (201 = joined, 204 = already in)
  4. Creates/fetches user in database
  5. Issues JWT token
    ↓
Frontend receives JWT → redirects to dashboard
```

### Why guilds.join Is Needed for DMs

Discord bots can only DM users who share at least one server with the bot. The `guilds.join` scope + the `PUT /guilds/{id}/members/{id}` API call ensures every user who logs in is automatically added to your server, satisfying this requirement.

### DM Delivery Conditions

| Condition | Required |
|-----------|----------|
| Bot and user share a server | ✅ Yes |
| User has DMs from server members enabled | ✅ Yes (user-controlled) |
| `DISCORD_GUILD_ID` is set | ✅ Yes |
| `DISCORD_TOKEN` is set | ✅ Yes |

If `DISCORD_GUILD_ID` is not set, the auto-join step is skipped silently and DMs may fail for new users.

---

## Troubleshooting

### "驗證失敗 / errors.server-error" on callback page

**Cause:** The OAuth scope contained invalid values (e.g., `dm_channels.messages.*`), causing Discord to return an error before the callback.

**Fix:** Ensure the scope in `backend/app/api/auth.py` → `discord_login` is exactly:
```python
"scope": "identify guilds.join",
```

### Bot cannot DM user

Check in order:

1. `DISCORD_GUILD_ID` is set in `.env`
2. Bot is in the server specified by `DISCORD_GUILD_ID`
3. Bot has `Send Messages` permission in the server
4. User's Discord privacy settings allow DMs from server members
5. Check backend logs for `403 Cannot send messages to this user`

### User not added to server after login

1. Verify `DISCORD_GUILD_ID` is correct (numeric server ID)
2. Verify the bot has `Create Instant Invite` permission in the server
3. Verify **Server Members Intent** is enabled in Developer Portal → Bot
4. Check backend logs for errors during the `PUT /guilds/.../members/...` call

### "Invalid OAuth2 redirect_uri"

The `DISCORD_REDIRECT_URI` in `.env` must exactly match one of the URIs registered in Developer Portal → OAuth2 → Redirects.

### User already in server (204 response)

This is expected and handled correctly — the backend ignores 204 responses. No action needed.

---

## Security Notes

- `guilds.join` only allows adding users to servers where the bot is already a member. It cannot add users to arbitrary servers.
- The `access_token` from OAuth is used only for the guild join call and is never stored.
- JWT tokens are issued separately and are independent of the Discord access token.
- Users can leave the server at any time; this does not affect their web session or JWT.
