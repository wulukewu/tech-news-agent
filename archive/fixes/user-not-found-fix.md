# User Not Found Error Fix

## 問題描述

當呼叫 `POST /api/notifications/test` 端點時，收到 400 錯誤：

```json
{
  "success": false,
  "error": "RESOURCE_NOT_FOUND: User not found | Details: {'user_id': 'bc627dfa-7101-4e98-8e92-bbc02f97e7cd'}",
  "error_code": "INTERNAL_ERROR"
}
```

## 根本原因

所有通知相關的 API 端點都有相同的問題：

1. `get_current_user()` 從 JWT token 中提取 `user_id` 和 `discord_id`
2. 端點接著呼叫 `supabase.get_or_create_user(current_user["discord_id"])`
3. `get_or_create_user()` 可能返回與 JWT token 中不同的 UUID
4. 當使用這個不同的 UUID 查詢資料庫時，找不到對應的使用者記錄

**問題核心**：不應該在已經通過身份驗證的情況下再次呼叫 `get_or_create_user()`，應該直接使用 `current_user["user_id"]`。

## 修復方案

### 已修復的檔案

#### 1. `backend/app/api/notifications.py` ✅

修復了以下端點：

- `GET /api/notifications/settings` - 獲取通知設定
- `PATCH /api/notifications/settings` - 更新通知設定
- `POST /api/notifications/test` - 發送測試通知
- `GET /api/notifications/preferences` - 獲取通知偏好
- `PATCH /api/notifications/preferences` - 更新通知偏好
- `GET /api/notifications/status` - 獲取通知狀態
- `POST /api/notifications/reschedule` - 重新排程通知

#### 2. `backend/app/api/analytics.py` ✅

修復了以下端點：

- `POST /api/analytics/event` - 記錄分析事件

#### 3. `backend/app/api/recommendations.py` ✅

修復了以下端點：

- `GET /api/recommendations/feeds` - 獲取推薦的 feeds
- `GET /api/recommendations/articles` - 獲取推薦文章
- `POST /api/recommendations/refresh` - 重新載入推薦
- `POST /api/recommendations/dismiss` - 忽略推薦
- `POST /api/recommendations/track` - 追蹤互動

#### 4. `backend/app/api/feeds.py` ✅

修復了以下端點：

- `POST /api/feeds/batch-subscribe` - 批次訂閱 feeds

#### 5. `backend/app/api/onboarding.py` ✅

修復了以下端點：

- `GET /api/onboarding/status` - 獲取引導狀態
- `POST /api/onboarding/progress` - 更新引導進度
- `POST /api/onboarding/complete` - 完成引導
- `POST /api/onboarding/skip` - 跳過引導
- `POST /api/onboarding/reset` - 重置引導

**修改前**：

```python
user_uuid = await supabase.get_or_create_user(current_user["discord_id"])
```

**修改後**：

```python
user_uuid = current_user["user_id"]
```

## 測試驗證

修復後，請執行以下測試：

```bash
# 1. 重啟後端服務
cd backend
python -m uvicorn app.main:app --reload

# 2. 測試通知端點
curl -X POST http://localhost:8000/api/notifications/test \
  -H "Authorization: Bearer YOUR_TOKEN"
```

預期結果：

```json
{
  "success": true,
  "data": {
    "message": "測試通知已發送"
  }
}
```

## 影響範圍

- **修復的檔案數**：5 個
- **修復的端點數**：19 個
- **向後相容性**：✅ 完全相容，不影響現有功能

## 建議

1. **立即修復**：所有使用 `get_or_create_user()` 配合 `get_current_user()` 的端點
2. **程式碼審查**：檢查是否有其他類似的模式
3. **單元測試**：為這些端點添加測試，確保使用正確的 user_id

## 相關文件

- JWT 認證流程：`backend/app/api/auth.py` 中的 `get_current_user()`
- 使用者服務：`backend/app/services/supabase_service.py` 中的 `get_or_create_user()`
