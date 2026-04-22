# 環境變數結構總結

## 📁 新的檔案結構

```
tech-news-agent/
├── backend/
│   ├── .env.example    ✅ 範本檔案 (可提交到 Git)
│   └── .env            ❌ 實際環境變數 (不可提交，需自行建立)
│
├── frontend/
│   ├── .env.example    ✅ 範本檔案 (可提交到 Git)
│   └── .env.local      ❌ 實際環境變數 (不可提交，需自行建立)
│
├── ENV_SETUP_GUIDE.md  📚 環境變數完整設定指南
├── setup-env.sh        🔧 自動設定腳本
└── .gitignore          🔒 確保 .env 不被提交
```

## ✅ 已完成的變更

### 1. 刪除根目錄的環境變數檔案

- ❌ 刪除 `.env`
- ❌ 刪除 `.env.example`

### 2. 建立/更新環境變數範本

- ✅ `backend/.env.example` - 完整的後端環境變數範本
- ✅ `frontend/.env.example` - 前端環境變數範本

### 3. 更新 .gitignore

```gitignore
# 環境變數
.env
.env.local
.env.*.local
backend/.env
frontend/.env.local
!backend/.env.example
!frontend/.env.example
```

### 4. 建立文件

- ✅ `ENV_SETUP_GUIDE.md` - 詳細的環境變數設定指南
- ✅ `setup-env.sh` - 自動化設定腳本

### 5. 更新現有文件

- ✅ `README.md` - 加入環境變數指南連結
- ✅ `QUICKSTART.md` - 更新設定步驟
- ✅ `DEPLOYMENT_CHECKLIST.md` - 更新環境變數檢查項目

---

## 🚀 使用方式

### 方法 1: 使用自動化腳本 (推薦)

```bash
# 執行設定腳本
./setup-env.sh

# 編輯環境變數
nano backend/.env
nano frontend/.env.local

# 啟動開發環境
make dev
```

### 方法 2: 手動設定

```bash
# 複製範本
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# 編輯環境變數
nano backend/.env
nano frontend/.env.local

# 啟動開發環境
make dev
```

---

## 📋 環境變數清單

### Backend (.env)

#### 必填項目

- `SUPABASE_URL` - Supabase 專案 URL
- `SUPABASE_KEY` - Supabase service_role key
- `DISCORD_TOKEN` - Discord bot token
- `DISCORD_CHANNEL_ID` - Discord 頻道 ID
- `DISCORD_CLIENT_ID` - Discord OAuth2 Client ID
- `DISCORD_CLIENT_SECRET` - Discord OAuth2 Client Secret
- `DISCORD_REDIRECT_URI` - OAuth2 redirect URI
- `GROQ_API_KEY` - Groq API key
- `JWT_SECRET` - JWT 密鑰 (至少 32 字元)

#### 選填項目 (有預設值)

- `LLM_CONCURRENT_LIMIT` - LLM 並發請求數 (預設: 2)
- `LLM_REQUEST_DELAY` - 請求延遲秒數 (預設: 4)
- `LLM_MAX_RETRIES` - 最大重試次數 (預設: 2)
- `LLM_TIMEOUT` - 請求超時秒數 (預設: 30)
- `RSS_FETCH_DAYS` - RSS 抓取天數 (預設: 7)
- `SCHEDULER_CRON` - 排程器 CRON 表達式 (預設: "0 _/6 _ \* \*")
- `SCHEDULER_TIMEZONE` - 時區 (預設: Asia/Taipei)
- `BATCH_SIZE` - 批次大小 (預設: 50)
- `BATCH_SPLIT_THRESHOLD` - 批次分割閾值 (預設: 100)
- `JWT_ALGORITHM` - JWT 演算法 (預設: HS256)
- `JWT_EXPIRATION_DAYS` - JWT 過期天數 (預設: 7)
- `CORS_ORIGINS` - CORS 允許來源 (預設: http://localhost:3000)
- `RATE_LIMIT_PER_MINUTE_UNAUTH` - 未認證速率限制 (預設: 100)
- `RATE_LIMIT_PER_MINUTE_AUTH` - 已認證速率限制 (預設: 300)
- `COOKIE_SECURE` - Cookie 安全標記 (預設: false)

### Frontend (.env.local)

#### 必填項目

- `NEXT_PUBLIC_API_BASE_URL` - Backend API URL
- `NEXT_PUBLIC_APP_NAME` - 應用程式名稱
- `NEXT_PUBLIC_APP_URL` - 應用程式 URL

---

## 🔒 安全性

### 不可提交的檔案 (已加入 .gitignore)

- `backend/.env`
- `frontend/.env.local`

### 可以提交的檔案

- `backend/.env.example`
- `frontend/.env.example`

### 最佳實踐

1. ✅ 永遠不要提交包含真實密鑰的 .env 檔案
2. ✅ 使用強隨機密鑰 (JWT_SECRET)
3. ✅ 開發和正式環境使用不同的密鑰
4. ✅ 定期更新 API keys
5. ✅ 正式環境設定 `COOKIE_SECURE=true`

---

## 🔄 環境變數更新流程

### 新增環境變數

1. 在 `.env.example` 中新增變數和註解
2. 在實際的 `.env` 或 `.env.local` 中新增值
3. 更新 `ENV_SETUP_GUIDE.md`
4. 提交 `.env.example` 的變更

### 修改環境變數

1. 修改 `.env` 或 `.env.local` 中的值
2. 重啟應用程式: `make restart-dev`

---

## 📚 相關文件

| 文件                      | 說明                 |
| ------------------------- | -------------------- |
| `ENV_SETUP_GUIDE.md`      | 環境變數完整設定指南 |
| `QUICKSTART.md`           | 快速開始指南         |
| `DOCKER_GUIDE.md`         | Docker 使用指南      |
| `DEPLOYMENT_CHECKLIST.md` | 部署檢查清單         |

---

## 🎯 快速參考

### 首次設定

```bash
./setup-env.sh
nano backend/.env
nano frontend/.env.local
make dev
```

### 檢查設定

```bash
# 查看 backend 環境變數 (不顯示敏感資訊)
grep -v "KEY\|SECRET\|TOKEN" backend/.env

# 查看 frontend 環境變數
cat frontend/.env.local

# 測試連線
make dev
make logs-dev
```

### 產生 JWT Secret

```bash
openssl rand -hex 32
```

---

## ✅ 驗證清單

設定完成後，確認以下項目：

- [ ] `backend/.env` 已建立並填入所有必填項目
- [ ] `frontend/.env.local` 已建立並填入所有必填項目
- [ ] JWT_SECRET 至少 32 字元
- [ ] CORS_ORIGINS 包含前端 URL
- [ ] DISCORD_REDIRECT_URI 正確設定
- [ ] 所有 API keys 有效
- [ ] 執行 `make dev` 成功啟動
- [ ] 執行 `make logs-dev` 無錯誤訊息
- [ ] 可以訪問 http://localhost:3000 (前端)
- [ ] 可以訪問 http://localhost:8000/docs (後端 API)

---

## 🐛 常見問題

### Q: 為什麼要分開 backend 和 frontend 的環境變數？

A:

- Backend 需要敏感的 API keys (Supabase service_role, Discord token)
- Frontend 只需要公開的設定 (API URL)
- 分開管理更安全，也更清晰

### Q: .env 和 .env.local 有什麼區別？

A:

- `.env` - 通常用於 Node.js/Python 後端
- `.env.local` - Next.js 的慣例，用於本地開發
- 兩者都不應該提交到 Git

### Q: 如何在正式環境設定環境變數？

A:

1. 在伺服器上複製 `.env.example`
2. 填入正式環境的值
3. 確保 `COOKIE_SECURE=true`
4. 使用 HTTPS 網域
5. 參考 `DEPLOYMENT_CHECKLIST.md`

### Q: 忘記設定某個環境變數會怎樣？

A:

- 應用程式可能無法啟動
- 查看日誌: `make logs-dev`
- 參考 `ENV_SETUP_GUIDE.md` 補充缺少的變數

---

## 📞 需要幫助？

1. 查看 `ENV_SETUP_GUIDE.md` 詳細說明
2. 執行 `./setup-env.sh` 自動設定
3. 檢查 `.env.example` 中的註解
4. 查看應用程式日誌找出問題
