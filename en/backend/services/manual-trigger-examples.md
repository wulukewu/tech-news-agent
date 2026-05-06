# 手動觸發 Scheduler 使用範例

本文件提供手動觸發 scheduler 的實際使用範例。

## 使用場景

### 場景 1: 剛訂閱新的 RSS Feed

當你剛使用 `/add_feed` 訂閱了新的 RSS feed，想立即看到新文章：

1. 在 Discord 執行 `/trigger_fetch`
2. 等待 2-5 分鐘讓系統抓取和分析文章
3. 執行 `/news_now` 查看新文章

### 場景 2: 定期檢查更新

如果你想在非排程時間檢查是否有新文章：

1. 在前端 Dashboard 點擊「立即抓取新文章」按鈕
2. 系統會在背景執行抓取任務
3. 重新整理頁面查看新文章

### 場景 3: 系統維護後驗證

在系統維護或更新後，驗證 scheduler 是否正常運作：

1. 執行 `/scheduler_status` 查看當前狀態
2. 如果狀態異常，執行 `/trigger_fetch` 手動觸發
3. 再次執行 `/scheduler_status` 確認執行成功

### 場景 4: API 整合

如果你正在開發自動化工具，可以透過 API 觸發：

```bash
# 取得 JWT token (假設已登入)
TOKEN="your_jwt_token_here"

# 觸發 scheduler
curl -X POST https://your-domain.com/api/scheduler/trigger \
  -H "Authorization: Bearer $TOKEN"

# 查詢狀態
curl -X GET https://your-domain.com/api/scheduler/status \
  -H "Authorization: Bearer $TOKEN"
```

## Discord 指令範例

### 基本使用流程

```
# 1. 訂閱新的 feed
/add_feed name:TechCrunch url:https://techcrunch.com/feed/ category:Tech News

# 2. 立即觸發抓取
/trigger_fetch

# 3. 等待幾分鐘後查看狀態
/scheduler_status

# 4. 查看新文章
/news_now
```

### 檢查 Scheduler 健康狀態

```
# 查看詳細狀態
/scheduler_status
```

**正常狀態回應範例：**

```
✅ Scheduler 狀態正常

上次執行時間: 5 分鐘前
處理文章數: 25
成功率: 92.6%
```

**異常狀態回應範例：**

```
⚠️ Scheduler 狀態異常

問題:
• Scheduler has not run in 13.5 hours (threshold: 12 hours)

上次執行時間: 13 小時前
處理文章數: 0
成功率: N/A
```

## 前端 UI 範例

### Dashboard 按鈕使用

1. 登入後進入 Dashboard (`/dashboard`)
2. 在右上角找到「立即抓取新文章」按鈕（旁邊有旋轉圖示）
3. 點擊按鈕
4. 看到成功提示：「已觸發文章抓取任務，請稍後重新整理頁面查看新文章」
5. 等待 2-5 分鐘
6. 重新整理頁面查看新文章

### 按鈕狀態

- **正常狀態**: 顯示「立即抓取新文章」
- **執行中**: 顯示「抓取中...」並且按鈕被禁用
- **成功**: 顯示綠色提示訊息
- **失敗**: 顯示紅色錯誤訊息

## API 使用範例

### 使用 curl

```bash
# 設定變數
API_URL="http://localhost:8000"
TOKEN="your_jwt_token"

# 觸發 scheduler
curl -X POST "${API_URL}/api/scheduler/trigger" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json"

# 預期回應 (202 Accepted)
{
  "status": "triggered",
  "message": "Scheduler job has been triggered manually and is running in the background."
}

# 查詢狀態
curl -X GET "${API_URL}/api/scheduler/status" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json"

# 預期回應 (200 OK)
{
  "last_execution_time": "2024-01-01T12:00:00Z",
  "articles_processed": 25,
  "failed_operations": 2,
  "total_operations": 27,
  "is_healthy": true,
  "issues": []
}
```

### 使用 Python

```python
import requests

API_URL = "http://localhost:8000"
TOKEN = "your_jwt_token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# 觸發 scheduler
response = requests.post(f"{API_URL}/api/scheduler/trigger", headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# 查詢狀態
response = requests.get(f"{API_URL}/api/scheduler/status", headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

### 使用 JavaScript/TypeScript

```typescript
const API_URL = 'http://localhost:8000';
const TOKEN = 'your_jwt_token';

const headers = {
  Authorization: `Bearer ${TOKEN}`,
  'Content-Type': 'application/json',
};

// 觸發 scheduler
const triggerResponse = await fetch(`${API_URL}/api/scheduler/trigger`, {
  method: 'POST',
  headers,
});
const triggerData = await triggerResponse.json();
console.log('Trigger:', triggerData);

// 查詢狀態
const statusResponse = await fetch(`${API_URL}/api/scheduler/status`, {
  method: 'GET',
  headers,
});
const statusData = await statusResponse.json();
console.log('Status:', statusData);
```

## 測試腳本

專案提供了測試腳本來快速驗證 API：

```bash
# 不帶 token 測試（會得到 401）
./scripts/test_manual_trigger.sh

# 帶 token 測試
./scripts/test_manual_trigger.sh http://localhost:8000 your_jwt_token

# 測試生產環境
./scripts/test_manual_trigger.sh https://your-domain.com your_jwt_token
```

## 常見問題

### Q: 觸發後多久可以看到新文章？

A: 通常需要 2-5 分鐘，取決於：

- 訂閱的 feed 數量
- 每個 feed 的文章數量
- LLM API 的回應速度
- 網路連線品質

### Q: 可以連續多次觸發嗎？

A: 可以，但不建議。每次觸發都會創建一個新的背景任務，多次觸發可能會：

- 增加伺服器負擔
- 對 RSS 來源造成過多請求
- 消耗更多 LLM API quota

建議至少間隔 5 分鐘再次觸發。

### Q: 觸發失敗怎麼辦？

A: 檢查以下項目：

1. 確認已登入（有有效的 JWT token）
2. 檢查網路連線
3. 查看伺服器日誌是否有錯誤
4. 使用 `/scheduler_status` 查看詳細狀態
5. 如果持續失敗，聯繫系統管理員

### Q: 如何知道任務是否完成？

A: 有幾種方式：

1. 使用 `/scheduler_status` 查看「上次執行時間」
2. 查看「處理文章數」是否增加
3. 執行 `/news_now` 看是否有新文章
4. 在前端 Dashboard 重新整理頁面

### Q: 手動觸發會影響定時排程嗎？

A: 不會。手動觸發和定時排程是獨立的：

- 手動觸發立即執行一次
- 定時排程繼續按照設定的時間執行
- 兩者不會互相干擾

## 最佳實踐

1. **適度使用**: 不要過於頻繁地手動觸發
2. **監控狀態**: 定期使用 `/scheduler_status` 檢查健康狀態
3. **錯誤處理**: 如果觸發失敗，等待幾分鐘後再試
4. **日誌記錄**: 在生產環境中記錄所有手動觸發操作
5. **權限控制**: 考慮限制手動觸發權限給管理員

## 進階使用

### 自動化腳本

創建一個定期檢查並觸發的腳本：

```bash
#!/bin/bash

# 每小時檢查一次，如果超過 12 小時沒執行就觸發

API_URL="http://localhost:8000"
TOKEN="your_jwt_token"

# 查詢狀態
STATUS=$(curl -s -X GET "${API_URL}/api/scheduler/status" \
  -H "Authorization: Bearer ${TOKEN}")

IS_HEALTHY=$(echo $STATUS | jq -r '.is_healthy')

if [ "$IS_HEALTHY" = "false" ]; then
  echo "Scheduler is unhealthy, triggering manually..."
  curl -X POST "${API_URL}/api/scheduler/trigger" \
    -H "Authorization: Bearer ${TOKEN}"
fi
```

### 監控整合

整合到監控系統（如 Prometheus）：

```python
from prometheus_client import Gauge
import requests

scheduler_health = Gauge('scheduler_health', 'Scheduler health status')
articles_processed = Gauge('scheduler_articles_processed', 'Articles processed in last run')

def check_scheduler_health():
    response = requests.get(
        f"{API_URL}/api/scheduler/status",
        headers={"Authorization": f"Bearer {TOKEN}"}
    )
    data = response.json()

    scheduler_health.set(1 if data['is_healthy'] else 0)
    articles_processed.set(data['articles_processed'])
```
