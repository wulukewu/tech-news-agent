# Discord OAuth 設定與測試指南

## ✅ 已完成的設定

### 1. 後端 OAuth Callback

- ✅ 處理 Discord OAuth 回調
- ✅ 交換 authorization code 取得 access token
- ✅ 取得用戶資訊並註冊/登入
- ✅ 生成 JWT token
- ✅ 設定 HttpOnly Cookie
- ✅ 重定向到前端 `/auth/callback`

### 2. 前端 Callback 頁面

- ✅ 處理 OAuth 回調
- ✅ 從 Cookie 讀取 JWT token
- ✅ 更新認證狀態
- ✅ 重定向到 Dashboard
- ✅ 錯誤處理和顯示

---

## 🔧 Discord Developer Portal 設定

### 1. 前往 Discord Developer Portal

訪問：https://discord.com/developers/applications

### 2. 選擇你的應用程式

Client ID: `1482750418084823081`

### 3. 設定 OAuth2 Redirects

在 **OAuth2** > **Redirects** 中新增：

#### 開發環境

```
http://localhost:8000/api/auth/discord/callback
```

#### 正式環境（之後部署時）

```
https://api.yourdomain.com/api/auth/discord/callback
```

### 4. OAuth2 Scopes

確認已啟用以下 scopes：

- ✅ `identify` - 讀取用戶基本資訊（ID、用戶名）
- ✅ `email` - 讀取用戶 email（選填）

---

## 🚀 測試 OAuth 登入流程

### 1. 確認服務運行

```bash
# 檢查容器狀態
docker-compose ps

# 應該看到兩個容器都在運行
# tech-news-agent-backend-dev
# tech-news-agent-frontend-dev
```

### 2. 訪問前端首頁

打開瀏覽器訪問：

```
http://localhost:3000
```

### 3. 點擊「使用 Discord 登入」

應該會：

1. 重定向到 Discord 授權頁面
2. 顯示你的應用程式名稱和請求的權限
3. 要求你授權

### 4. 授權後的流程

```
用戶點擊「授權」
    ↓
Discord 重定向到: http://localhost:8000/api/auth/discord/callback?code=xxx
    ↓
後端處理:
  - 交換 code 取得 access token
  - 取得用戶資訊
  - 註冊/登入用戶
  - 生成 JWT token
  - 設定 HttpOnly Cookie
    ↓
後端重定向到: http://localhost:3000/auth/callback
    ↓
前端處理:
  - 從 Cookie 讀取 JWT token
  - 呼叫 checkAuth() 更新狀態
  - 重定向到 /dashboard
    ↓
用戶看到 Dashboard 頁面（已登入）
```

---

## 🔍 驗證登入成功

### 1. 檢查 Cookie

在瀏覽器開發者工具中：

1. 打開 **Application** > **Cookies**
2. 選擇 `http://localhost:3000`
3. 應該看到 `access_token` cookie
4. 屬性應該包含：
   - ✅ HttpOnly
   - ✅ SameSite=Lax
   - ✅ Path=/

### 2. 檢查認證狀態

在 Dashboard 頁面：

- ✅ 應該顯示你的 Discord 用戶名
- ✅ 應該顯示你的頭像
- ✅ 應該能看到導航選單

### 3. 測試 API 請求

打開瀏覽器控制台，執行：

```javascript
fetch('http://localhost:8000/api/feeds', {
  credentials: 'include',
})
  .then((r) => r.json())
  .then(console.log);
```

應該返回你的訂閱列表（而不是 401 錯誤）

---

## 🐛 常見問題排解

### 問題 1: 「無效的 OAuth2 redirect_uri」

**原因：** Discord Developer Portal 中沒有設定 redirect URI

**解決方法：**

1. 前往 Discord Developer Portal
2. OAuth2 > Redirects
3. 新增 `http://localhost:8000/api/auth/discord/callback`
4. 點擊 Save Changes

### 問題 2: 授權後顯示 JSON 而不是重定向

**原因：** 後端沒有正確重定向（已修復）

**解決方法：**

```bash
# 重啟後端容器
docker-compose restart backend
```

### 問題 3: 前端顯示「驗證失敗」

**可能原因：**

- Cookie 沒有正確設定
- CORS 設定問題
- JWT Secret 不一致

**檢查步驟：**

```bash
# 1. 檢查後端日誌
docker-compose logs backend

# 2. 檢查 .env 設定
cat .env | grep -E "JWT_SECRET|CORS_ORIGINS|NEXT_PUBLIC"

# 3. 確認 CORS_ORIGINS 包含前端 URL
# 應該是: CORS_ORIGINS=http://localhost:3000
```

### 問題 4: Cookie 沒有設定

**可能原因：**

- `COOKIE_SECURE=true` 但使用 HTTP（開發環境應該是 false）
- SameSite 設定問題

**解決方法：**

```bash
# 檢查 .env
grep COOKIE_SECURE .env

# 開發環境應該是:
# COOKIE_SECURE=false
```

### 問題 5: 「Failed to authenticate with Discord」

**可能原因：**

- Discord Client ID 或 Secret 錯誤
- Redirect URI 不匹配

**解決方法：**

```bash
# 檢查 .env 設定
cat .env | grep DISCORD

# 確認:
# - DISCORD_CLIENT_ID 正確
# - DISCORD_CLIENT_SECRET 正確
# - DISCORD_REDIRECT_URI=http://localhost:8000/api/auth/discord/callback
```

---

## 🔐 安全性說明

### OAuth 和 Bot 的關係

#### Discord Bot（你現在的設定）

- Bot 在你的私人 Discord 頻道運作
- 只有你能看到 bot 發送的通知
- Bot Token: `DISCORD_TOKEN`

#### Discord OAuth（Web 登入）

- 用於網站的身份驗證
- **任何人都可以用 Discord 登入你的網站**
- **不需要**在你的 Discord 伺服器裡
- **不需要**能看到 bot 的頻道
- OAuth Credentials: `DISCORD_CLIENT_ID` + `DISCORD_CLIENT_SECRET`

### 開放給其他人使用

你的 OAuth 設定**完全可以開放給其他人使用**：

✅ **可以做的：**

- 任何人用 Discord 登入你的網站
- 每個用戶管理自己的 RSS 訂閱
- 每個用戶在網站上看自己的文章

⚠️ **目前的限制：**

- Bot 通知只發給你（在你的私人頻道）
- 其他用戶不會收到 Discord 通知
- 其他用戶只能在網站上看文章

💡 **如果要給其他用戶 Discord 通知：**
需要修改程式碼，讓 Bot 發送 DM 給用戶

---

## 📊 OAuth 流程圖

```
┌─────────────────────────────────────────────────────────────┐
│                    OAuth 登入完整流程                        │
└─────────────────────────────────────────────────────────────┘

1. 用戶訪問前端
   http://localhost:3000

2. 點擊「使用 Discord 登入」
   ↓
   前端重定向到後端 OAuth 端點
   http://localhost:8000/api/auth/discord/login

3. 後端重定向到 Discord
   ↓
   https://discord.com/oauth2/authorize?
     client_id=xxx&
     redirect_uri=http://localhost:8000/api/auth/discord/callback&
     response_type=code&
     scope=identify

4. Discord 顯示授權頁面
   ↓
   用戶點擊「授權」

5. Discord 重定向回後端
   ↓
   http://localhost:8000/api/auth/discord/callback?code=xxx

6. 後端處理 callback
   ├─ 交換 code → access token
   ├─ 取得用戶資訊
   ├─ 註冊/登入用戶
   ├─ 生成 JWT token
   ├─ 設定 HttpOnly Cookie
   └─ 重定向到前端

7. 前端 callback 頁面
   ↓
   http://localhost:3000/auth/callback
   ├─ 從 Cookie 讀取 JWT
   ├─ 呼叫 checkAuth()
   ├─ 更新認證狀態
   └─ 重定向到 Dashboard

8. 用戶看到 Dashboard
   ✅ 登入成功！
```

---

## ✅ 測試檢查清單

完整測試 OAuth 登入流程：

- [ ] Discord Developer Portal 已設定 redirect URI
- [ ] `.env` 中所有 Discord 變數已填入
- [ ] 前後端容器都在運行
- [ ] 訪問 `http://localhost:3000` 看到登入頁面
- [ ] 點擊「使用 Discord 登入」
- [ ] 重定向到 Discord 授權頁面
- [ ] 授權後重定向回前端
- [ ] 前端顯示 Dashboard（不是錯誤頁面）
- [ ] 瀏覽器 Cookie 中有 `access_token`
- [ ] Dashboard 顯示用戶名和頭像
- [ ] 可以訪問其他需要認證的頁面
- [ ] 登出功能正常運作

---

## 🎉 完成！

如果所有測試都通過，你的 OAuth 登入系統就完全正常運作了！

### 下一步

1. **測試其他功能**
   - 訂閱管理
   - 文章列表
   - 閱讀清單

2. **準備部署**
   - 在 Discord Developer Portal 新增正式環境的 redirect URI
   - 更新 `.env` 為正式環境設定
   - 參考 `DEPLOYMENT_CHECKLIST.md`

3. **開放給其他用戶**
   - OAuth 已經可以開放使用
   - 任何人都可以用 Discord 登入
   - 不需要在你的 Discord 伺服器裡
