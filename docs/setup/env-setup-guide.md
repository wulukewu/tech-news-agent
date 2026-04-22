# 環境變數設定指南

## 📁 檔案結構

```
tech-news-agent/
├── .env.example    # 環境變數範本（包含前後端所有變數）
└── .env            # 實際環境變數（需自行建立，不提交到 Git）
```

## 🚀 快速設定

### 方法 1: 使用自動化腳本（推薦）

```bash
./setup-env.sh
nano .env  # 編輯並填入實際值
```

### 方法 2: 手動設定

```bash
# 複製範本
cp .env.example .env

# 編輯檔案
nano .env  # 或使用你喜歡的編輯器
```

---

## 📋 環境變數說明

`.env` 檔案分為兩大區塊：

### 🔧 Backend 變數（後端使用）

這些變數只在後端使用，不會暴露到前端：

#### 必填項目

| 變數                    | 說明                      | 範例                                              |
| ----------------------- | ------------------------- | ------------------------------------------------- |
| `SUPABASE_URL`          | Supabase 專案 URL         | `https://xxx.supabase.co`                         |
| `SUPABASE_KEY`          | Supabase service_role key | `eyJ...`                                          |
| `DISCORD_TOKEN`         | Discord bot token         | `MTQ...`                                          |
| `DISCORD_CHANNEL_ID`    | Discord 頻道 ID           | `1234567890`                                      |
| `DISCORD_CLIENT_ID`     | Discord OAuth2 Client ID  | `1234567890`                                      |
| `DISCORD_CLIENT_SECRET` | Discord OAuth2 Secret     | `abc123...`                                       |
| `DISCORD_REDIRECT_URI`  | OAuth2 redirect URI       | `http://localhost:8000/api/auth/discord/callback` |
| `GROQ_API_KEY`          | Groq API key              | `gsk_...`                                         |
| `JWT_SECRET`            | JWT 密鑰（至少 32 字元）  | 使用 `openssl rand -hex 32` 產生                  |
| `CORS_ORIGINS`          | CORS 允許來源             | `http://localhost:3000`                           |
| `COOKIE_SECURE`         | Cookie 安全標記           | `false` (開發) / `true` (正式)                    |

#### 選填項目（有預設值）

| 變數                           | 預設值        | 說明               |
| ------------------------------ | ------------- | ------------------ |
| `LLM_CONCURRENT_LIMIT`         | `2`           | LLM 並發請求數     |
| `LLM_REQUEST_DELAY`            | `4`           | 請求延遲（秒）     |
| `LLM_MAX_RETRIES`              | `2`           | 最大重試次數       |
| `LLM_TIMEOUT`                  | `30`          | 請求超時（秒）     |
| `RSS_FETCH_DAYS`               | `7`           | RSS 抓取天數       |
| `SCHEDULER_CRON`               | `0 */6 * * *` | 排程器 CRON 表達式 |
| `SCHEDULER_TIMEZONE`           | `Asia/Taipei` | 時區               |
| `BATCH_SIZE`                   | `50`          | 批次大小           |
| `BATCH_SPLIT_THRESHOLD`        | `100`         | 批次分割閾值       |
| `JWT_ALGORITHM`                | `HS256`       | JWT 演算法         |
| `JWT_EXPIRATION_DAYS`          | `7`           | JWT 過期天數       |
| `RATE_LIMIT_PER_MINUTE_UNAUTH` | `100`         | 未認證速率限制     |
| `RATE_LIMIT_PER_MINUTE_AUTH`   | `300`         | 已認證速率限制     |

### 🎨 Frontend 變數（前端使用）

這些變數以 `NEXT_PUBLIC_` 開頭，會暴露到前端瀏覽器：

| 變數                       | 說明            | 範例                    |
| -------------------------- | --------------- | ----------------------- |
| `NEXT_PUBLIC_API_BASE_URL` | Backend API URL | `http://localhost:8000` |
| `NEXT_PUBLIC_APP_NAME`     | 應用程式名稱    | `Tech News Agent`       |
| `NEXT_PUBLIC_APP_URL`      | 應用程式 URL    | `http://localhost:3000` |

---

## 🔑 如何取得 API Keys

### Supabase

1. 前往 [Supabase Dashboard](https://supabase.com/dashboard)
2. 選擇你的專案
3. Settings > API
4. 複製 Project URL 到 `SUPABASE_URL`
5. 複製 service_role key（不是 anon key）到 `SUPABASE_KEY`

### Discord Bot

1. 前往 [Discord Developer Portal](https://discord.com/developers/applications)
2. 建立新應用程式或選擇現有的
3. Bot > Copy Token 到 `DISCORD_TOKEN`
4. OAuth2 > Copy Client ID 和 Client Secret
5. 在 Discord 中右鍵點擊頻道 > 複製 ID 到 `DISCORD_CHANNEL_ID`
6. 在 OAuth2 Redirects 中新增:
   - 開發: `http://localhost:8000/api/auth/discord/callback`
   - 正式: `https://api.yourdomain.com/api/auth/discord/callback`

### Groq API

1. 前往 [Groq Console](https://console.groq.com/keys)
2. 建立新的 API Key
3. 複製到 `GROQ_API_KEY`

### JWT Secret

```bash
# 使用 openssl 產生隨機密鑰（至少 32 字元）
openssl rand -hex 32
```

---

## 🌍 開發環境 vs 正式環境

### 開發環境 (.env)

```bash
# Backend
DISCORD_REDIRECT_URI=http://localhost:8000/api/auth/discord/callback
CORS_ORIGINS=http://localhost:3000
COOKIE_SECURE=false

# Frontend
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### 正式環境 (.env)

```bash
# Backend
DISCORD_REDIRECT_URI=https://api.yourdomain.com/api/auth/discord/callback
CORS_ORIGINS=https://yourdomain.com
COOKIE_SECURE=true

# Frontend
NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com
NEXT_PUBLIC_APP_URL=https://yourdomain.com
```

---

## 🔒 安全性注意事項

### ⚠️ 絕對不要提交

- `.env` （包含真實的密鑰和 tokens）

### ✅ 可以提交

- `.env.example` （只有範本和說明）

### 🛡️ 最佳實踐

1. **使用強密碼**
   - JWT_SECRET 至少 32 字元
   - 使用隨機產生的密鑰

2. **分離環境**
   - 開發環境和正式環境使用不同的密鑰
   - 不要在正式環境使用開發環境的設定

3. **限制權限**
   - Supabase 使用 service_role key（後端）
   - Discord bot 只給必要的權限

4. **HTTPS**
   - 正式環境必須使用 HTTPS
   - 設定 `COOKIE_SECURE=true`

5. **NEXT*PUBLIC*\* 變數**
   - 這些變數會暴露在前端
   - 不要放敏感資訊（API keys, secrets）

---

## 🔄 環境變數更新流程

### 新增環境變數

1. 在 `.env.example` 中新增變數和說明
2. 在實際的 `.env` 中新增值
3. 更新此文件說明
4. 提交 `.env.example` 的變更

### 修改環境變數

1. 修改 `.env` 中的值
2. 如果是預設值變更，同步更新 `.env.example`
3. 重啟應用程式使變更生效: `make restart-dev`

---

## 🐛 疑難排解

### 問題: 應用程式無法連接到 Supabase

**檢查:**

- `SUPABASE_URL` 格式正確 (https://xxx.supabase.co)
- `SUPABASE_KEY` 使用 service_role key
- Supabase 專案狀態正常

### 問題: Discord bot 無法啟動

**檢查:**

- `DISCORD_TOKEN` 正確且未過期
- Bot 已被邀請到伺服器
- Bot 有必要的權限

### 問題: JWT 驗證失敗

**檢查:**

- `JWT_SECRET` 至少 32 字元
- 前後端使用相同的 JWT_SECRET（都從 .env 讀取）
- JWT_ALGORITHM 設定正確

### 問題: CORS 錯誤

**檢查:**

- `CORS_ORIGINS` 包含前端 URL
- 前端的 `NEXT_PUBLIC_API_BASE_URL` 正確
- 沒有多餘的斜線 (/)

### 問題: 前端無法讀取環境變數

**檢查:**

- 前端變數必須以 `NEXT_PUBLIC_` 開頭
- 修改 `.env` 後需要重啟: `make restart-dev`
- Docker 容器需要重新建置: `make up-dev`

---

## ✅ 設定檢查清單

### 必填項目

- [ ] SUPABASE_URL
- [ ] SUPABASE_KEY
- [ ] DISCORD_TOKEN
- [ ] DISCORD_CHANNEL_ID
- [ ] DISCORD_CLIENT_ID
- [ ] DISCORD_CLIENT_SECRET
- [ ] DISCORD_REDIRECT_URI
- [ ] GROQ_API_KEY
- [ ] JWT_SECRET (至少 32 字元)
- [ ] CORS_ORIGINS (包含前端 URL)
- [ ] NEXT_PUBLIC_API_BASE_URL
- [ ] NEXT_PUBLIC_APP_NAME
- [ ] NEXT_PUBLIC_APP_URL

### 驗證設定

```bash
# 啟動開發環境
make dev

# 檢查日誌
make logs-dev

# 測試 API
curl http://localhost:8000/health

# 測試前端
curl http://localhost:3000
```

---

## 🎯 快速參考

### 一鍵設定（首次使用）

```bash
# 1. 複製環境變數範本
./setup-env.sh

# 2. 編輯環境變數
nano .env

# 3. 啟動應用程式
make dev

# 4. 查看日誌確認啟動成功
make logs-dev
```

### 產生 JWT Secret

```bash
openssl rand -hex 32
```

### 檢查環境變數（不顯示敏感資訊）

```bash
grep -v "KEY\|SECRET\|TOKEN" .env
```

---

## 📚 相關文件

- [QUICKSTART.md](./QUICKSTART.md) - 快速開始指南
- [DOCKER_GUIDE.md](./DOCKER_GUIDE.md) - Docker 使用指南
- [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md) - 部署檢查清單
