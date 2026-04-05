# 手動觸發 Scheduler 功能實作總結

## 功能概述

成功實作了手動觸發 scheduler 的功能，讓使用者可以透過三種方式立即抓取新文章：

1. **前端 Dashboard 按鈕**
2. **Discord Bot 指令**
3. **REST API Endpoint**

## 實作內容

### 1. 後端 API (Backend)

#### 新增檔案

- `backend/app/api/scheduler.py`
  - `POST /api/scheduler/trigger` - 手動觸發 scheduler
  - `GET /api/scheduler/status` - 查詢 scheduler 狀態
  - 需要 JWT 認證
  - 使用 `asyncio.create_task()` 在背景執行任務

#### 修改檔案

- `backend/app/main.py`
  - 註冊新的 scheduler API router
  - 添加 `/api` prefix 和 `scheduler` tag

### 2. Discord Bot

#### 新增檔案

- `backend/app/bot/cogs/admin_commands.py`
  - `/trigger_fetch` - 手動觸發文章抓取
  - `/scheduler_status` - 查看 scheduler 狀態
  - 使用 Discord Embed 格式化回應
  - 包含中文提示訊息

#### 修改檔案

- `backend/app/bot/client.py`
  - 載入新的 `admin_commands` cog

### 3. 前端 (Frontend)

#### 新增檔案

- `frontend/lib/api/scheduler.ts`
  - `triggerScheduler()` - 呼叫 API 觸發 scheduler
  - `getSchedulerStatus()` - 查詢 scheduler 狀態
  - 使用統一的 `apiClient` 處理認證

- `frontend/components/TriggerSchedulerButton.tsx`
  - 可重用的按鈕組件
  - 包含載入狀態和錯誤處理
  - 使用 Lucide React 的 RefreshCw 圖示
  - 顯示中文提示訊息

#### 修改檔案

- `frontend/app/dashboard/page.tsx`
  - 在 Dashboard 頁面整合 `TriggerSchedulerButton`
  - 與「管理訂閱」按鈕並排顯示

### 4. 測試

#### 新增檔案

- `backend/tests/test_scheduler_manual_trigger.py`
  - 測試 API endpoint 的認證和回應
  - 測試成功和失敗的情況

- `backend/tests/test_admin_commands.py`
  - 測試 Discord bot 指令
  - 測試健康和異常狀態的回應

- `scripts/test_manual_trigger.sh`
  - 快速測試 API endpoint 的 bash 腳本
  - 支援自訂 API URL 和 JWT token

### 5. 文件

#### 新增檔案

- `docs/MANUAL_SCHEDULER_TRIGGER.md`
  - 完整的功能說明文件
  - 包含使用方式、技術實作、注意事項

- `docs/MANUAL_TRIGGER_EXAMPLES.md`
  - 實際使用範例
  - 包含各種場景和程式語言的範例

- `CHANGELOG.md`
  - 記錄新功能的變更

- `IMPLEMENTATION_SUMMARY.md` (本檔案)
  - 實作總結

#### 修改檔案

- `README.md`
  - 在 Core Features 添加新功能
  - 在 Discord Commands 添加新指令說明
  - 在 Feature Highlights 添加新功能亮點

## 技術細節

### 認證機制

- 前端和 API 都使用 JWT token 認證
- Discord bot 指令不需要額外認證（Discord 本身已認證）
- 使用 `get_current_user` dependency 進行身份驗證

### 背景任務執行

- 使用 `asyncio.create_task()` 在背景執行 `background_fetch_job()`
- 任務立即返回 202 Accepted 狀態碼
- 不會阻塞 API 請求或 Discord 指令回應

### 錯誤處理

- API endpoint 包含完整的錯誤處理和日誌記錄
- Discord bot 使用 Embed 顯示友善的錯誤訊息
- 前端按鈕包含載入狀態和錯誤提示

### 狀態監控

- 使用現有的 `get_scheduler_health()` 函數
- 提供詳細的執行資訊：
  - 上次執行時間
  - 處理文章數
  - 失敗操作數
  - 健康狀態
  - 問題列表

## 使用方式

### Discord Bot

```
/trigger_fetch
/scheduler_status
```

### 前端 Dashboard

1. 登入後進入 Dashboard
2. 點擊右上角的「立即抓取新文章」按鈕
3. 等待幾分鐘後重新整理頁面

### REST API

```bash
# 觸發 scheduler
curl -X POST https://your-domain.com/api/scheduler/trigger \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 查詢狀態
curl -X GET https://your-domain.com/api/scheduler/status \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 測試方式

### 單元測試

```bash
# 測試 API endpoint
python3 -m pytest backend/tests/test_scheduler_manual_trigger.py -v

# 測試 Discord bot command
python3 -m pytest backend/tests/test_admin_commands.py -v
```

### 整合測試

```bash
# 使用測試腳本
./scripts/test_manual_trigger.sh http://localhost:8000 YOUR_JWT_TOKEN
```

### 手動測試

1. 啟動後端服務
2. 在 Discord 執行 `/trigger_fetch`
3. 查看日誌確認任務執行
4. 執行 `/scheduler_status` 查看狀態
5. 在前端 Dashboard 測試按鈕

## 檔案清單

### 新增檔案 (12 個)

```
backend/app/api/scheduler.py
backend/app/bot/cogs/admin_commands.py
backend/tests/test_scheduler_manual_trigger.py
backend/tests/test_admin_commands.py
frontend/lib/api/scheduler.ts
frontend/components/TriggerSchedulerButton.tsx
scripts/test_manual_trigger.sh
docs/MANUAL_SCHEDULER_TRIGGER.md
docs/MANUAL_TRIGGER_EXAMPLES.md
CHANGELOG.md
IMPLEMENTATION_SUMMARY.md
```

### 修改檔案 (4 個)

```
backend/app/main.py
backend/app/bot/client.py
frontend/app/dashboard/page.tsx
README.md
```

## 未來改進建議

1. **頻率限制**: 添加 rate limiting 防止過度觸發
2. **權限控制**: 限制手動觸發權限給管理員
3. **即時進度**: 在前端顯示即時執行進度
4. **執行歷史**: 記錄所有手動觸發的歷史
5. **指定 Feed**: 支援只抓取特定 feed 的文章
6. **通知機制**: 任務完成後發送通知
7. **批次觸發**: 支援批次觸發多個任務
8. **排程管理**: 允許動態修改排程時間

## 相容性

- ✅ 與現有功能完全相容
- ✅ 不影響定時排程
- ✅ 支援多次並發觸發
- ✅ 向後相容（不破壞現有 API）

## 效能考量

- 背景任務不會阻塞 API 回應
- 多次觸發會創建多個背景任務（建議添加限制）
- 使用現有的 scheduler 邏輯，無額外效能開銷

## 安全性

- ✅ 需要 JWT 認證
- ✅ 使用現有的認證機制
- ✅ 日誌記錄所有觸發操作
- ⚠️ 建議添加 rate limiting
- ⚠️ 建議添加權限檢查

## 已知問題與修復

### Issue 1: ModuleNotFoundError for app.schemas.auth

**問題**: 初始實作中錯誤地嘗試導入不存在的 `UserSchema`

**修復**: 使用 `Dict[str, Any]` 作為 `get_current_user` 的返回類型

**詳細說明**: 參見 `BUGFIX_AUTH_SCHEMA.md`

## 總結

成功實作了完整的手動觸發 scheduler 功能，包含：

- ✅ 三種觸發方式（Discord、Web UI、API）
- ✅ 完整的錯誤處理和日誌記錄
- ✅ 友善的使用者介面
- ✅ 詳細的文件和範例
- ✅ 單元測試和整合測試
- ✅ 與現有功能完全相容

使用者現在可以隨時手動觸發文章抓取，不需要等待定時排程，大幅提升了系統的靈活性和使用體驗。
