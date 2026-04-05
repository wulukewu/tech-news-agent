# 手動觸發 Scheduler 功能

## 概述

除了定時自動執行外，現在可以透過以下三種方式手動觸發 scheduler 來立即抓取新文章：

1. 前端 Dashboard 按鈕
2. Discord Bot 指令
3. REST API Endpoint

## 1. 前端 Dashboard 按鈕

在 Dashboard 頁面 (`/dashboard`) 的右上角，新增了「立即抓取新文章」按鈕。

### 使用方式

1. 登入後進入 Dashboard
2. 點擊右上角的「立即抓取新文章」按鈕
3. 系統會在背景執行抓取任務
4. 等待幾分鐘後重新整理頁面即可看到新文章

### 功能特點

- 需要登入才能使用
- 按鈕會顯示載入動畫
- 成功觸發後會顯示提示訊息
- 任務在背景執行，不會阻塞頁面

## 2. Discord Bot 指令

新增了兩個 Discord slash 指令：

### `/trigger_fetch`

手動觸發文章抓取任務。

**使用方式：**

```
/trigger_fetch
```

**回應：**

- ✅ 成功：顯示任務已觸發的確認訊息
- ❌ 失敗：顯示錯誤訊息

### `/scheduler_status`

查看 scheduler 的執行狀態。

**使用方式：**

```
/scheduler_status
```

**回應資訊：**

- 上次執行時間
- 處理文章數
- 成功率
- 健康狀態
- 問題列表（如果有）

## 3. REST API Endpoint

### POST `/api/scheduler/trigger`

手動觸發 scheduler 執行。

**認證：** 需要 JWT Token

**請求範例：**

```bash
curl -X POST https://your-domain.com/api/scheduler/trigger \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**回應範例：**

```json
{
  "status": "triggered",
  "message": "Scheduler job has been triggered manually and is running in the background."
}
```

**狀態碼：**

- `202 Accepted`: 成功觸發
- `401 Unauthorized`: 未登入或 token 無效
- `500 Internal Server Error`: 伺服器錯誤

### GET `/api/scheduler/status`

查詢 scheduler 的執行狀態。

**認證：** 需要 JWT Token

**請求範例：**

```bash
curl -X GET https://your-domain.com/api/scheduler/status \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**回應範例：**

```json
{
  "last_execution_time": "2024-01-01T12:00:00Z",
  "articles_processed": 25,
  "failed_operations": 2,
  "total_operations": 27,
  "is_healthy": true,
  "issues": []
}
```

**狀態碼：**

- `200 OK`: 成功取得狀態
- `401 Unauthorized`: 未登入或 token 無效
- `500 Internal Server Error`: 伺服器錯誤

## 技術實作細節

### 後端實作

1. **API Endpoint** (`backend/app/api/scheduler.py`)
   - 提供 `/api/scheduler/trigger` 和 `/api/scheduler/status` 兩個端點
   - 使用 `get_current_user` 進行身份驗證
   - 使用 `asyncio.create_task()` 在背景執行任務

2. **Discord Bot Command** (`backend/app/bot/cogs/admin_commands.py`)
   - 新增 `AdminCommands` Cog
   - 實作 `/trigger_fetch` 和 `/scheduler_status` 指令
   - 使用 Discord Embed 格式化回應

### 前端實作

1. **API Client** (`frontend/lib/api/scheduler.ts`)
   - 提供 `triggerScheduler()` 和 `getSchedulerStatus()` 函數
   - 使用統一的 `apiClient` 處理認證

2. **UI Component** (`frontend/components/TriggerSchedulerButton.tsx`)
   - 可重用的按鈕組件
   - 包含載入狀態和錯誤處理
   - 使用 Lucide React 圖示

3. **Dashboard Integration** (`frontend/app/dashboard/page.tsx`)
   - 在 Dashboard 頁面整合按鈕
   - 與現有的「管理訂閱」按鈕並排顯示

## 注意事項

1. **執行頻率**：建議不要過於頻繁地手動觸發，以避免對 RSS 來源造成過大負擔
2. **執行時間**：抓取任務可能需要數分鐘才能完成，取決於訂閱的 feed 數量
3. **並發執行**：多次觸發會創建多個背景任務，但不會互相干擾
4. **權限控制**：目前所有登入用戶都可以觸發，未來可考慮限制為管理員專用

## 測試

執行以下命令測試新功能：

```bash
# 測試 API endpoint
python3 -m pytest backend/tests/test_scheduler_manual_trigger.py -v

# 測試 Discord bot command
python3 -m pytest backend/tests/test_admin_commands.py -v
```

## 未來改進

1. 添加觸發頻率限制（rate limiting）
2. 添加管理員權限檢查
3. 在前端顯示即時執行進度
4. 添加執行歷史記錄
5. 支援指定特定 feed 進行抓取
