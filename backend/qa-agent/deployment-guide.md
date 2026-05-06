# QA Agent 部署指南

## 概述

本指南說明如何部署修復後的 QA Agent，確保穩定運行且無驗證錯誤。

## 前置需求

- Docker 和 Docker Compose 已安裝
- Supabase 資料庫已設定
- 環境變數已配置

## 部署步驟

### 1. 確認環境變數

檢查 `.env` 檔案包含以下必要設定：

```bash
# Supabase 設定
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Groq API (用於 LLM 回應生成)
GROQ_API_KEY=your_groq_api_key

# 其他必要設定
JWT_SECRET=your_jwt_secret
DISCORD_TOKEN=your_discord_token
```

### 2. 重新建置容器

```bash
# 停止現有容器
docker-compose down

# 重新建置（確保使用最新程式碼）
docker-compose build

# 啟動服務
docker-compose up -d
```

### 3. 驗證部署

#### 檢查容器狀態

```bash
docker-compose ps
```

應該看到所有服務都是 `Up` 狀態。

#### 檢查後端日誌

```bash
docker-compose logs -f tech-news-agent-backend-dev
```

應該看到：

```
✅ QA Agent database manager initialized successfully
✅ Scheduler started successfully
✅ Notification system integration initialized successfully
```

#### 測試健康檢查

```bash
curl http://localhost:8000/health
```

應該回傳：

```json
{
  "status": "healthy",
  "services": {
    "bot": "healthy",
    "scheduler": "healthy",
    "database": "healthy",
    "oauth": "healthy",
    "jwt": "healthy",
    "qa_agent": "healthy"
  }
}
```

### 4. 測試 QA 功能

#### 方法 1: 使用測試腳本

```bash
# 進入後端容器
docker-compose exec tech-news-agent-backend-dev bash

# 執行測試
python3 test_qa_simple.py

# 退出容器
exit
```

#### 方法 2: 使用 API 端點

首先取得認證 token（透過前端登入或使用現有 token）。

```bash
# 測試單次查詢
curl -X POST http://localhost:8000/api/qa/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "AI 技術的最新發展趨勢是什麼？"
  }'
```

預期回應：

```json
{
  "success": true,
  "data": {
    "query": "AI 技術的最新發展趨勢是什麼？",
    "articles": [...],
    "insights": [...],
    "recommendations": [...],
    "conversation_id": "...",
    "response_time": 0.5
  }
}
```

#### 方法 3: 使用前端介面

1. 開啟瀏覽器訪問 `http://localhost:3000`
2. 登入系統
3. 前往聊天頁面 `/chat`
4. 輸入測試查詢
5. 確認回應正常顯示

### 5. 監控運行狀況

#### 持續監控日誌

```bash
# 監控後端日誌
docker-compose logs -f tech-news-agent-backend-dev

# 監控前端日誌
docker-compose logs -f tech-news-agent-frontend-dev
```

#### 檢查常見錯誤

如果看到以下錯誤，表示修復未生效：

```
❌ column articles.summary does not exist
❌ ValidationError: Summary must contain at least 2 sentences
❌ Database manager not initialized
```

解決方法：

1. 確認程式碼已更新
2. 重新建置容器
3. 清除 Docker 快取：`docker-compose build --no-cache`

## 故障排除

### 問題 1: QA Agent 初始化失敗

**症狀**: 日誌顯示 "Failed to initialize QA Agent database manager"

**解決方法**:

1. 檢查 Supabase 連線設定
2. 確認 `SUPABASE_URL` 和 `SUPABASE_KEY` 正確
3. 測試 Supabase 連線：
   ```bash
   curl -H "apikey: YOUR_SUPABASE_KEY" \
        "YOUR_SUPABASE_URL/rest/v1/articles?limit=1"
   ```

### 問題 2: 資料庫欄位錯誤

**症狀**: "column articles.summary does not exist"

**解決方法**:

1. 確認已更新到最新程式碼
2. 檢查 `backend/app/qa_agent/fallback_qa.py` 使用 `ai_summary`
3. 檢查 `backend/app/qa_agent/simple_qa.py` 使用 `ai_summary`

### 問題 3: Pydantic 驗證錯誤

**症狀**: "ValidationError: Summary must contain at least 2 sentences"

**解決方法**:

1. 確認 API 端點使用 `SimpleQAAgent` 而非 `FallbackQAAgent`
2. 檢查 `backend/app/api/qa.py` 中的 import 語句
3. 重新啟動容器

### 問題 4: 前端無法連接後端

**症狀**: 前端顯示網路錯誤

**解決方法**:

1. 檢查 CORS 設定
2. 確認後端服務正在運行
3. 檢查防火牆設定
4. 驗證 API URL 配置

## 效能優化建議

### 1. 啟用快取

未來可以加入 Redis 快取常見查詢：

```python
# 範例：快取查詢結果
@cache(ttl=3600)  # 快取 1 小時
async def process_query(query: str):
    # ...
```

### 2. 資料庫索引

確保 articles 表有適當的索引：

```sql
-- 為標題和摘要建立全文搜尋索引
CREATE INDEX idx_articles_title_search ON articles USING gin(to_tsvector('english', title));
CREATE INDEX idx_articles_summary_search ON articles USING gin(to_tsvector('english', ai_summary));
```

### 3. 連線池優化

調整資料庫連線池大小（如需要）：

```python
# 在 database.py 中
pool = await asyncpg.create_pool(
    dsn=DATABASE_URL,
    min_size=5,
    max_size=20,
    command_timeout=60
)
```

## 回滾計畫

如果部署後發現問題，可以快速回滾：

```bash
# 1. 停止服務
docker-compose down

# 2. 切換到上一個版本
git checkout <previous-commit>

# 3. 重新建置和啟動
docker-compose build
docker-compose up -d
```

## 監控指標

建議監控以下指標：

1. **QA 查詢成功率**: 應該 > 95%
2. **平均回應時間**: 應該 < 2 秒
3. **錯誤率**: 應該 < 5%
4. **資料庫連線狀態**: 應該保持健康

## 支援

如遇到問題：

1. 檢查日誌檔案
2. 參考故障排除章節
3. 查看 `docs/qa-agent-fix-summary.md`
4. 聯繫技術支援

---

**版本**: 1.0.0
**最後更新**: 2026-04-22
**狀態**: ✅ 準備部署
