# 故障排除指南

本指南幫助您診斷和修復技術新聞代理中的常見問題。

## 目錄

- [快速診斷](#快速診斷)
- [常見問題](#常見問題)
- [資料庫問題](#資料庫問題)
- [Discord 機器人問題](#discord-機器人問題)
- [前端問題](#前端問題)
- [後端問題](#後端問題)
- [Docker 問題](#docker-問題)
- [錯誤參考](#錯誤參考)
- [獲取幫助](#獲取幫助)

---

## 快速診斷

```bash
# 檢查所有服務狀態
make ps

# 檢查後端健康狀態
curl http://localhost:8000/health
curl http://localhost:8000/health/scheduler

# 檢查日誌
make logs-dev       # 開發環境
make logs-prod      # 生產環境

# 檢查端口
lsof -i :3000
lsof -i :8000
```

---

## 常見問題

### 1. 資料庫表格缺失

**症狀:** `relation "X" does not exist`，API 調用時出現 500 錯誤

**解決方案:**

選項 A — 在 Supabase SQL 編輯器中運行初始化 SQL：
```
Supabase Dashboard → SQL Editor → 貼上 backend/scripts/init_supabase.sql → 運行
```

選項 B — 運行遷移腳本：
```bash
python3 backend/scripts/apply_missing_migration.py
```

要驗證資料庫狀態：
```bash
python3 backend/scripts/verify_bot_health.py
```

---

### 2. Discord 機器人沒有回應

**症狀:** 機器人線上但忽略命令，斜線命令未註冊

**檢查清單:**
- `DISCORD_TOKEN` 在 `.env` 中設定正確
- 機器人在 Discord 伺服器中擁有所需權限（發送訊息、使用斜線命令、在線程中發送訊息）
- OAuth 範圍包括 `bot` 和 `applications.commands`
- 機器人已使用正確的權限整數邀請到伺服器

```bash
# 檢查 Token 是否已加載
docker-compose exec backend env | grep DISCORD_TOKEN

# 檢查機器人日誌
docker-compose logs backend | grep -i discord
```

---

### 3. 文章無法抓取

**症狀:** 沒有新文章出現，排程器似乎閒置

**檢查清單:**
1. 檢查排程器健康狀態：`curl http://localhost:8000/health/scheduler`
2. 檢查後端日誌中是否有排程器錯誤：`make logs-dev`
3. 驗證 RSS Feed URL 是否有效且可訪問
4. 確認 `GROQ_API_KEY` 已設定且有剩餘額度

```bash
# 手動觸發抓取
curl -X POST http://localhost:8000/api/scheduler/trigger
# 或透過 Discord：/trigger_fetch
```

---

### 4. 前端無法連接後端

**症狀:** API 調用失敗，「網路錯誤」，登入後空白頁面

**解決方案:**

```bash
# 驗證環境變數是否已設定
grep NEXT_PUBLIC_API_URL .env

# 測試後端是否可訪問
curl http://localhost:8000/health
```

- 確保 `.env` 中的 `NEXT_PUBLIC_API_URL=http://localhost:8000`
- 檢查後端中的 CORS 配置是否允許前端來源
- 如果在 Docker 中運行，請使用服務名稱：`http://backend:8000`

---

### 5. 身份驗證失敗

**症狀:** 登入重定向失敗，「無效 Token」，401 錯誤

**檢查清單:**
- `DISCORD_CLIENT_ID` 和 `DISCORD_CLIENT_SECRET` 與 Discord 開發者門戶中的匹配
- `DISCORD_REDIRECT_URI` 與門戶中註冊的 URI 完全匹配（例如 `http://localhost:3000/auth/callback`）
- `JWT_SECRET_KEY` 已設定（使用 `openssl rand -hex 32` 生成）

---

### 6. 端口衝突

**症狀:** `address already in use`，服務無法啟動

```bash
# 查找正在使用端口的程式
lsof -i :3000
lsof -i :8000

# 終止衝突程式
kill -9 $(lsof -t -i:3000)
kill -9 $(lsof -t -i:8000)
```

---

## 資料庫問題

專案使用 **Supabase (雲端 PostgreSQL)**。沒有本地資料庫且沒有 Alembic。所有遷移都是 SQL 文件。

### 運行遷移

```bash
# 選項 1: Supabase SQL 編輯器 (推薦)
# 貼上 backend/scripts/init_supabase.sql 並運行

# 選項 2: 遷移腳本
python3 backend/scripts/apply_missing_migration.py
```

### 連接超時 / 身份驗證失敗

```bash
# 驗證憑證是否已設定
grep SUPABASE .env

# 手動測試連接
python3 -c "
from supabase import create_client
import os
c = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
print('連接成功:', c.table('users').select('count').execute())
"

# 檢查 Supabase 專案狀態
# Supabase Dashboard → 設定 → 一般
```

- `SUPABASE_KEY` 使用 **服務角色密鑰** (而非匿名密鑰)
- 檢查 RLS 策略是否允許服務角色存取

---

## Discord 機器人問題

### 機器人 Token 無效

```bash
grep DISCORD_TOKEN .env
# 在以下位置重新生成 Token：Discord 開發者門戶 → Bot → 重設 Token
```

### 斜線命令未顯示

斜線命令可能需要長達 1 小時才能在全球範圍內傳播。在開發期間，使用特定伺服器命令進行即時註冊。

```bash
docker-compose logs backend | grep -i "command\|sync\|slash"
```

---

## 前端問題

### 建置失敗

```bash
cd frontend
rm -rf node_modules .next
npm install
npm run build
```

### TypeScript 錯誤

```bash
cd frontend
npm run type-check
```

### Hydration 錯誤

對於任何僅限瀏覽器的程式碼（例如 `localStorage`、`Date`），請使用 `useEffect`：

```typescript
const [mounted, setMounted] = useState(false);
useEffect(() => setMounted(true), []);
if (!mounted) return null;
```

---

## 後端問題

### 導入 / 依賴錯誤

```bash
docker-compose exec backend pip list
docker-compose build backend --no-cache
```

### 排程器未運行

```bash
curl http://localhost:8000/health/scheduler
make logs-dev | grep -i scheduler
```

在 `.env` 中設定 `LOG_LEVEL=DEBUG` 以獲取詳細輸出。

---

## Docker 問題

### 服務無法啟動

```bash
# 檢查失敗服務的日誌
docker-compose logs backend
docker-compose logs frontend

# 清理並重新建置
make clean
make dev
```

### 磁碟空間不足

```bash
docker system df
docker system prune -a -f
docker volume prune -f
```

### Makefile 參考

| 命令        | 描述                  |
|-------------|-----------------------|
| `make dev`  | 啟動開發環境          |
| `make prod` | 啟動生產環境          |
| `make logs-dev` | 查看開發日誌        |
| `make logs-prod` | 查看生產日誌       |
| `make clean` | 停止並移除容器/卷     |
| `make ps`   | 顯示運行中的服務      |

---

## 錯誤參考

| 錯誤                     | 可能原因                | 修正                                         |
|--------------------------|-------------------------|----------------------------------------------|
| `relation "X" does not exist` | 缺少資料庫表格          | 運行 `init_supabase.sql` 或 `apply_missing_migration.py` |
| `401 Unauthorized`       | JWT 或 Discord Token 無效或過期 | 重新登入或檢查 `JWT_SECRET_KEY`               |
| `403 Forbidden`          | 權限不足或 RLS 策略     | 檢查 Supabase RLS、機器人權限                 |
| `404 Not Found`          | 錯誤的端點或缺失的資源  | 檢查 URL，驗證資料是否存在                     |
| `500 Internal Server Error` | 未處理的異常            | 檢查 `make logs-dev`                         |
| `Port already in use`    | 端口衝突                | `kill -9 $(lsof -t -i:PORT)`                 |
| `GROQ API error`         | 無額度或無效的 Key      | 檢查 [console.groq.com](https://console.groq.com) |

---

## 獲取幫助

### 收集調試資訊

```bash
# 服務狀態
make ps

# 最近的日誌 (分享前請清理敏感資訊)
docker-compose logs --tail=100

# 配置檢查 (隱藏敏感值)
cat .env | sed 's/=.*/=***/'

# 系統資訊
docker --version && docker-compose --version
```

### 有用的腳本

```bash
python3 backend/scripts/verify_bot_health.py      # 檢查機器人 + 資料庫健康狀態
python3 backend/scripts/apply_missing_migration.py # 應用缺失的資料庫遷移
```

### 緊急重置

```bash
make clean
docker system prune -f
cp .env.example .env   # 重新填寫憑證
make dev
```

### 文件

- [快速入門指南](../guides/quick-start.md)
- [環境設定指南](../setup/env-setup-guide.md)
- [開發人員指南](../development/developer-guide.md)
- [架構概覽](../architecture/architecture-overview.md)
