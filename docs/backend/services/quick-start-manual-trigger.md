# 快速開始：手動觸發 Scheduler

這是一個 5 分鐘快速指南，教你如何使用新的手動觸發功能。

## 前置條件

- 已部署並運行的 Tech News Agent
- Discord bot 已連線
- 前端應用已啟動
- 至少訂閱了一個 RSS feed

## 方法 1: Discord Bot (最簡單)

### 步驟 1: 觸發抓取

在 Discord 輸入：

```
/trigger_fetch
```

你會看到：

```
✅ 文章抓取已觸發

已手動觸發文章抓取任務，正在背景執行中...

說明
系統將立即開始抓取新文章並進行分析。
完成後可使用 /news_now 查看最新文章。
```

### 步驟 2: 等待完成

等待 2-5 分鐘（取決於訂閱的 feed 數量）

### 步驟 3: 查看狀態

```
/scheduler_status
```

你會看到：

```
✅ Scheduler 狀態正常

上次執行時間: 2 分鐘前
處理文章數: 25
成功率: 92.6%
```

### 步驟 4: 查看新文章

```
/news_now
```

## 方法 2: 前端 Dashboard

### 步驟 1: 登入 Dashboard

1. 開啟瀏覽器
2. 前往 `http://localhost:3000/dashboard` (或你的部署網址)
3. 使用 Discord OAuth 登入

### 步驟 2: 點擊按鈕

在 Dashboard 右上角找到「立即抓取新文章」按鈕（有旋轉圖示），點擊它。

### 步驟 3: 等待提示

你會看到綠色提示訊息：

```
已觸發文章抓取任務，請稍後重新整理頁面查看新文章
```

### 步驟 4: 重新整理頁面

等待 2-5 分鐘後，重新整理頁面查看新文章。

## 方法 3: REST API

### 步驟 1: 取得 JWT Token

登入前端後，從瀏覽器的 localStorage 取得 token：

```javascript
// 在瀏覽器 Console 執行
localStorage.getItem('access_token');
```

### 步驟 2: 呼叫 API

```bash
# 設定變數
TOKEN="your_jwt_token_here"
API_URL="http://localhost:8000"

# 觸發 scheduler
curl -X POST "${API_URL}/api/scheduler/trigger" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json"
```

### 步驟 3: 查看回應

```json
{
  "status": "triggered",
  "message": "Scheduler job has been triggered manually and is running in the background."
}
```

### 步驟 4: 查詢狀態

```bash
curl -X GET "${API_URL}/api/scheduler/status" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json"
```

## 常見問題

### Q: 按鈕點擊後沒反應？

A: 檢查：

1. 是否已登入？
2. 瀏覽器 Console 是否有錯誤？
3. 後端服務是否正常運行？

### Q: Discord 指令沒回應？

A: 檢查：

1. Bot 是否在線？
2. 指令是否正確輸入？
3. 是否有權限執行指令？

### Q: 觸發後看不到新文章？

A: 請：

1. 等待 2-5 分鐘
2. 使用 `/scheduler_status` 確認執行完成
3. 重新整理頁面或執行 `/news_now`

## 下一步

- 閱讀 [完整文件](./MANUAL_SCHEDULER_TRIGGER.md)
- 查看 [使用範例](./MANUAL_TRIGGER_EXAMPLES.md)
- 了解 [技術實作](../IMPLEMENTATION_SUMMARY.md)

## 需要幫助？

如果遇到問題：

1. 查看後端日誌：`docker-compose logs -f backend`
2. 查看前端日誌：`docker-compose logs -f frontend`
3. 執行測試腳本：`./scripts/test_manual_trigger.sh`
4. 查看 [故障排除指南](./MANUAL_SCHEDULER_TRIGGER.md#注意事項)
