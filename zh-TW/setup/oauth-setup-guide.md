# Discord OAuth & 機器人私訊設定指南

本指南詳細說明如何配置 Discord OAuth2 登入並為所有用戶啟用機器人私訊通知。

## 📖 目錄

- [概覽](#概覽)
- [先決條件](#先決條件)
- [步驟 1: Discord 開發者入口網站](#步驟-1-discord-開發者入口網站)
- [步驟 2: 建立 Discord 伺服器](#步驟-2-建立-discord-伺服器)
- [步驟 3: 將機器人加入伺服器](#步驟-3-將機器人加入伺服器)
- [步驟 4: 配置環境變數](#步驟-4-配置環境變數)
- [步驟 5: 驗證流程](#步驟-5-驗證流程)
- [運作原理](#運作原理)
- [故障排除](#故障排除)

---

## 概覽

技術新聞代理使用 Discord OAuth2 進行身份驗證。當用戶登入時，後端會：

1. 透過 Discord OAuth2 驗證用戶身份 (`identify` + `guilds.join` 範圍)
2. 使用 `guilds.join` 範圍自動將用戶加入您的 Discord 伺服器
3. 為網頁會話發出 JWT Token

由於用戶和機器人現在在同一個伺服器中，機器人可以向用戶發送私訊。

> **注意：** 如果用戶在 Discord 隱私設定中禁用了「允許來自伺服器成員的私訊」，則私訊仍可能失敗。這是用戶控制的，無法繞過。

---

## 先決條件

- Discord 帳戶
- 在 [discord.com/developers/applications](https://discord.com/developers/applications) 建立的帶有機器人的 Discord 應用程式
- 後端正在運行，並帶有有效的 `DISCORD_TOKEN`、`DISCORD_CLIENT_ID` 和 `DISCORD_CLIENT_SECRET`

---

## 步驟 1: Discord 開發者入口網站

### 1.1 OAuth2 範圍 (Scopes)

在入口網站中無需手動配置範圍——範圍是在程式碼中設定的。後端請求：

| 範圍       | 目的                                   |
|------------|----------------------------------------|
| `identify` | 讀取用戶的用戶名、頭像和 ID           |
| `guilds.join` | 自動將用戶加入您的伺服器           |

### 1.2 重定向 URI (Redirect URIs)

在您的應用程式 → **OAuth2** → **Redirects** 中，添加：

```
# 開發環境
http://localhost:8000/api/auth/discord/callback

# 生產環境
https://your-api-domain.com/api/auth/discord/callback
```

點擊 **Save Changes**。

### 1.3 機器人權限

在您的應用程式 → **Bot**：

- 在「特權網關意圖 (Privileged Gateway Intents)」下啟用 **伺服器成員意圖 (Server Members Intent)**
- 確保機器人 Token 已複製到您的 `.env` 中的 `DISCORD_TOKEN`

---

## 步驟 2: 建立 Discord 伺服器

機器人需要與用戶共享一個伺服器才能向他們發送私訊。

1. 打開 Discord
2. 點擊左側側邊欄中的 **+** → **建立我的** → **為我與朋友建立**
3. 給它一個名稱（例如 `技術新聞代理`）
4. 點擊 **建立**

### 獲取伺服器 ID

1. 前往 Discord **設定** → **進階** → 啟用 **開發者模式 (Developer Mode)**
2. 右鍵點擊您的伺服器圖示 → **複製伺服器 ID**
3. 保存此 ID — 您將需要它來設定 `DISCORD_GUILD_ID`

---

## 步驟 3: 將機器人加入伺服器

1. 前往 [discord.com/developers/applications](https://discord.com/developers/applications) → 您的應用程式
2. 導航到 **OAuth2** → **URL 產生器**
3. 在 **Scopes** 下，勾選 `bot`
4. 在 **Bot Permissions** 下，勾選：
   - `發送訊息 (Send Messages)`
   - `建立即時邀請 (Create Instant Invite)` ← `guilds.join` 運作所需
5. 複製生成的 URL，在瀏覽器中打開
6. 選擇您的伺服器 → **授權**

驗證機器人是否出現在您的伺服器成員列表中。

---

## 步驟 4: 配置環境變數

將以下內容添加到您的 `.env`：

```bash
# 自動加入和支援私訊所需
DISCORD_GUILD_ID=your_server_id_here
```

完整的 Discord 相關變數：

```bash
# 機器人
DISCORD_TOKEN=your_discord_bot_token_here

# OAuth2
DISCORD_CLIENT_ID=your_discord_client_id_here
DISCORD_CLIENT_SECRET=your_discord_client_secret_here
DISCORD_REDIRECT_URI=http://localhost:8000/api/auth/discord/callback

# 用於自動加入的公會 (伺服器)
DISCORD_GUILD_ID=your_server_id_here
```

---

## 步驟 5: 驗證流程

1. 啟動後端和前端
2. 訪問 `http://localhost:3000` 並點擊 **使用 Discord 登入**
3. Discord 授權頁面應顯示：
   - ✅ 存取您的用戶名、頭像和橫幅 (`identify`)
   - ✅ 為您加入伺服器 (`guilds.join`)
4. 授權後，您應該被重定向到儀表板
5. 檢查您的 Discord 伺服器 — 用戶現在應該作為成員出現
6. 機器人現在可以向該用戶發送私訊

---

## 運作原理

### OAuth 登入流程

```
用戶點擊「使用 Discord 登入」
    ↓
後端重定向到 Discord OAuth
(範圍：identify guilds.join)
    ↓
用戶在 Discord 上授權
    ↓
Discord 重定向到 /api/auth/discord/callback?code=xxx
    ↓
後端：
  1. 將 code 換取 access_token
  2. 獲取用戶資訊 (/users/@me)
  3. 調用 PUT /guilds/{guild_id}/members/{user_id}
     → 將用戶加入您的伺服器 (201 = 加入成功, 204 = 已在伺服器中)
  4. 在資料庫中建立/獲取用戶
  5. 發出 JWT Token
    ↓
前端接收 JWT → 重定向到儀表板
```

### 為何私訊需要 `guilds.join`

Discord 機器人只能向與機器人共享至少一個伺服器的用戶發送私訊。`guilds.join` 範圍 + `PUT /guilds/{id}/members/{id}` API 調用確保每個登入的用戶都會自動加入您的伺服器，滿足此要求。

### 私訊傳遞條件

| 條件                 | 必需   |
|----------------------|--------|
| 機器人與用戶共享一個伺服器 | ✅ 是   |
| 用戶已啟用來自伺服器成員的私訊 | ✅ 是 (用戶控制) |
| `DISCORD_GUILD_ID` 已設定 | ✅ 是   |
| `DISCORD_TOKEN` 已設定 | ✅ 是   |

如果未設定 `DISCORD_GUILD_ID`，則自動加入步驟將靜默跳過，新用戶的私訊可能失敗。

---

## 故障排除

### 回調頁面出現「驗證失敗 / errors.server-error」

**原因：** OAuth 範圍包含無效值（例如 `dm_channels.messages.*`），導致 Discord 在回調之前返回錯誤。

**修正：** 確保 `backend/app/api/auth.py` → `discord_login` 中的範圍為：
```python
"scope": "identify guilds.join",
```

### 機器人無法私訊用戶

依序檢查：

1. `DISCORD_GUILD_ID` 已在 `.env` 中設定
2. 機器人位於 `DISCORD_GUILD_ID` 指定的伺服器中
3. 機器人在伺服器中具有「發送訊息」權限
4. 用戶的 Discord 隱私設定允許來自伺服器成員的私訊
5. 檢查後端日誌中是否有 `403 無法向此用戶發送訊息` 錯誤

### 登入後用戶未加入伺服器

1. 驗證 `DISCORD_GUILD_ID` 是否正確（數字伺服器 ID）
2. 驗證機器人在伺服器中具有「建立即時邀請」權限
3. 驗證「伺服器成員意圖」在開發者入口網站 → Bot 中已啟用
4. 檢查後端日誌中是否有 `PUT /guilds/.../members/...` 調用期間的錯誤

### 「無效的 OAuth2 redirect_uri」

`.env` 中的 `DISCORD_REDIRECT_URI` 必須與開發者入口網站 → OAuth2 → 重定向中註冊的 URI 完全匹配。

### 用戶已在伺服器中 (204 回應)

這是預期的，並已正確處理——後端會忽略 204 回應。無需採取行動。

---

## 安全性注意事項

- `guilds.join` 只允許將用戶添加到機器人已是成員的伺服器。它不能將用戶添加到任意伺服器。
- OAuth 的 `access_token` 僅用於公會加入調用，且永不儲存。
- JWT Token 獨立發出，與 Discord access Token 無關。
- 用戶可以隨時離開伺服器；這不會影響他們的網頁會話或 JWT。
