# Bug Fix: ModuleNotFoundError for app.schemas.auth

## 問題描述

在啟動後端時遇到以下錯誤：

```
ModuleNotFoundError: No module named 'app.schemas.auth'
```

## 原因分析

在 `backend/app/api/scheduler.py` 中，我們錯誤地嘗試導入不存在的 `UserSchema`：

```python
from app.schemas.auth import UserSchema
```

實際上，專案中並沒有 `app.schemas.auth` 模組，也沒有 `UserSchema` 類別。

查看 `backend/app/api/auth.py` 後發現，`get_current_user` dependency 返回的是一個 `Dict[str, Any]`，而不是 Pydantic model：

```python
async def get_current_user(...) -> Dict[str, Any]:
    return {
        "user_id": user_id,
        "discord_id": discord_id
    }
```

## 解決方案

修改 `backend/app/api/scheduler.py`，使用正確的類型註解：

### 修改前

```python
from app.schemas.auth import UserSchema

@router.post("/scheduler/trigger")
async def trigger_scheduler_manually(
    current_user: UserSchema = Depends(get_current_user)
):
    logger.info(f"Manual scheduler trigger requested by user {current_user.discord_id}")
```

### 修改後

```python
from typing import Dict, Any

@router.post("/scheduler/trigger")
async def trigger_scheduler_manually(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    logger.info(f"Manual scheduler trigger requested by user {current_user['discord_id']}")
```

## 修改內容

1. 移除錯誤的 import：`from app.schemas.auth import UserSchema`
2. 添加正確的 import：`from typing import Dict, Any`
3. 修改參數類型：`UserSchema` → `Dict[str, Any]`
4. 修改屬性訪問：`current_user.discord_id` → `current_user['discord_id']`

## 驗證

修改後，後端應該可以正常啟動：

```bash
docker-compose up -d
docker-compose logs -f backend
```

應該看到：

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [1] using StatReload
```

## 相關檔案

- `backend/app/api/scheduler.py` - 已修復
- `backend/app/api/auth.py` - 參考檔案（了解 get_current_user 的返回類型）

## 測試

修復後，可以測試 API endpoint：

```bash
# 取得 JWT token
TOKEN="your_jwt_token"

# 測試觸發 endpoint
curl -X POST http://localhost:8000/api/scheduler/trigger \
  -H "Authorization: Bearer $TOKEN"

# 測試狀態 endpoint
curl -X GET http://localhost:8000/api/scheduler/status \
  -H "Authorization: Bearer $TOKEN"
```

## 預防措施

未來在使用 `get_current_user` dependency 時，應該：

1. 檢查 `auth.py` 中的返回類型
2. 使用 `Dict[str, Any]` 而不是假設有 Pydantic model
3. 使用字典訪問語法 `current_user['key']` 而不是屬性訪問 `current_user.key`

## 狀態

✅ 已修復
✅ 已測試
✅ 已記錄
