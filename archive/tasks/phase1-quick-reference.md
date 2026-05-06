# Phase 1 快速參考指南

## 🚀 快速啟動

```bash
# 啟動服務
docker-compose up -d

# 驗證 Phase 1 功能
bash scripts/verify_phase1_complete.sh

# 查看後端日誌
docker logs tech-news-agent-backend-dev --tail 50

# 查看前端日誌
docker logs tech-news-agent-frontend-dev --tail 50
```

## 🔗 重要連結

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Settings Page**: http://localhost:3000/settings/notifications

## 📡 API 端點速查

### Quiet Hours (勿擾時段)

```bash
# 獲取設定 (需要認證)
GET /api/notifications/quiet-hours

# 更新設定 (需要認證)
PUT /api/notifications/quiet-hours
Body: {
  "start_time": "22:00:00",
  "end_time": "08:00:00",
  "timezone": "Asia/Taipei",
  "weekdays": [1,2,3,4,5],
  "enabled": true
}

# 檢查狀態 (需要認證)
GET /api/notifications/quiet-hours/status

# 創建預設設定 (需要認證)
POST /api/notifications/quiet-hours/default
Body: {"timezone": "Asia/Taipei"}

# 刪除設定 (需要認證)
DELETE /api/notifications/quiet-hours
```

### Technical Depth (技術深度)

```bash
# 獲取設定 (需要認證)
GET /api/notifications/tech-depth

# 更新設定 (需要認證)
PUT /api/notifications/tech-depth
Body: {
  "threshold": "intermediate",
  "enabled": true
}

# 獲取可用等級 (公開)
GET /api/notifications/tech-depth/levels

# 獲取統計 (需要認證)
GET /api/notifications/tech-depth/stats
```

### Notification History (通知歷史)

```bash
# 獲取歷史記錄 (需要認證)
GET /api/notifications/history?page=1&page_size=20

# 獲取統計 (需要認證)
GET /api/notifications/history/stats?days_back=30
```

## 🗄️ 資料庫表格

### user_quiet_hours

```sql
- id (uuid, primary key)
- user_id (uuid, foreign key)
- start_time (time)
- end_time (time)
- timezone (text)
- weekdays (integer[])
- enabled (boolean)
- created_at (timestamp)
- updated_at (timestamp)
```

### user_notification_preferences (新增欄位)

```sql
- tech_depth_threshold (text) -- 'basic', 'intermediate', 'advanced', 'expert'
- tech_depth_enabled (boolean)
```

### notification_history

```sql
- id (uuid, primary key)
- user_id (uuid, foreign key)
- sent_at (timestamp)
- channel (text) -- 'discord', 'email'
- status (text) -- 'sent', 'failed', 'queued', 'cancelled'
- content (jsonb)
- feed_source (text)
- error_message (text)
- retry_count (integer)
- created_at (timestamp)
- updated_at (timestamp)
```

## 🧪 測試指令

```bash
# 後端 API 測試
python scripts/test_phase1_apis.py

# 前端整合測試
bash scripts/test_phase1_frontend.sh

# 完整驗證測試
bash scripts/verify_phase1_complete.sh

# 檢查後端錯誤
docker logs tech-news-agent-backend-dev 2>&1 | grep -i "error\|exception"
```

## 🐛 常見問題排查

### 問題: Frontend 顯示「無法載入設定」

**檢查步驟**:

1. 確認後端正在運行: `curl http://localhost:8000/health`
2. 檢查用戶是否已登入
3. 查看瀏覽器 Console 的錯誤訊息
4. 檢查後端日誌: `docker logs tech-news-agent-backend-dev --tail 50`

**常見原因**:

- 用戶未登入 (401 錯誤)
- 後端服務未啟動
- 資料庫連接問題

### 問題: Backend 返回 500 錯誤

**檢查步驟**:

1. 查看後端日誌找到完整錯誤訊息
2. 確認資料庫表格已創建
3. 檢查環境變數設定

**常見原因**:

- 資料庫表格不存在 (需要運行遷移)
- UUID 類型錯誤 (已修復)
- 缺少必要的欄位

### 問題: Docker 容器無法啟動

**檢查步驟**:

```bash
# 查看容器狀態
docker ps -a

# 查看容器日誌
docker logs tech-news-agent-backend-dev
docker logs tech-news-agent-frontend-dev

# 重啟容器
docker-compose restart

# 重建容器
docker-compose down
docker-compose up -d --build
```

## 📝 開發筆記

### 重要提醒

1. `current_user["user_id"]` 已經是 UUID 對象，不需要再用 `UUID()` 包裝
2. 使用 `apiClient` 而非直接 `fetch()` 來調用後端 API
3. 時區處理使用 Python 內建的 `zoneinfo`，不需要 `pytz`
4. 所有 Phase 1 API 端點都需要認證 (除了 levels 和 timezones)

### 檔案位置

- **Backend Services**: `backend/app/services/`
- **Backend API**: `backend/app/api/notifications.py`
- **Frontend API Client**: `frontend/lib/api/notifications.ts`
- **Frontend Components**: `frontend/features/notifications/components/`
- **Database Migrations**: `scripts/migrations/`
- **Tests**: `scripts/test_*.py` 和 `scripts/*.sh`
- **Documentation**: `docs/phase1-*.md`

## 🔄 更新流程

### 修改後端代碼

```bash
# 1. 修改代碼
# 2. 重啟後端容器
docker restart tech-news-agent-backend-dev

# 3. 驗證
curl http://localhost:8000/health
```

### 修改前端代碼

```bash
# 1. 修改代碼
# 2. 前端會自動熱重載 (Hot Reload)
# 3. 如果沒有，重啟前端容器
docker restart tech-news-agent-frontend-dev
```

### 資料庫遷移

```bash
# 1. 創建遷移檔案在 scripts/migrations/
# 2. 在 Supabase SQL Editor 中執行
# 3. 驗證表格已創建
```

## 📊 監控指標

### 健康檢查

```bash
# Backend health
curl http://localhost:8000/health

# 預期輸出
{
  "status": "healthy",
  "services": {
    "bot": "healthy",
    "scheduler": "healthy",
    "database": "healthy",
    "oauth": "healthy",
    "jwt": "healthy"
  }
}
```

### 容器狀態

```bash
docker ps --filter "name=tech-news-agent"

# 預期看到兩個容器都是 "Up"
```

### 日誌監控

```bash
# 實時查看後端日誌
docker logs -f tech-news-agent-backend-dev

# 實時查看前端日誌
docker logs -f tech-news-agent-frontend-dev
```

## 🎯 下一步行動

1. **用戶測試**: 讓真實用戶測試 Phase 1 功能
2. **收集反饋**: 記錄用戶體驗和問題
3. **性能優化**: 監控 API 響應時間
4. **準備 Phase 2**: 開始規劃 Smart Bundling 功能

---

**最後更新**: 2026-04-21
**版本**: Phase 1 Complete
**狀態**: ✅ 生產就緒
