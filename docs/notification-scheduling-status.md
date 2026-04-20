# 通知排程狀態報告

**日期**: 2026-04-21
**問題**: DM 通知排程功能檢查

## 問題 1: 時間輸入 UI/UX ✅ 已修復

### 問題描述

用戶在輸入時間時，每輸入一個數字就會立即保存到資料庫，導致無法輸入完整的時間（例如想輸入 13:00 但只能輸入到 1）。

### 解決方案

修改 `PersonalizedNotificationSettings.tsx` 組件：

- 使用本地狀態 (`localTime`) 來存儲用戶輸入
- `onChange` 事件只更新本地狀態，不觸發 API 調用
- `onBlur` 事件（失去焦點時）才保存到資料庫
- 添加提示文字：「輸入完成後點擊其他地方即可儲存」

### 修改的檔案

- `frontend/features/notifications/components/PersonalizedNotificationSettings.tsx`

### 測試方法

1. 登入前端 http://localhost:3000
2. 進入 Settings > Notifications
3. 嘗試輸入時間（例如 13:30）
4. 確認可以完整輸入而不會中斷
5. 點擊其他地方後確認時間已保存

## 問題 2: 排程功能狀態 🔍 需要驗證

### 當前狀態

根據後端日誌分析：

#### ✅ 排程器正在運行

```
- Scheduler is active
- Jobs are being scheduled
- User notification jobs exist
```

#### ✅ 用戶排程已設定

從日誌中可以看到：

```json
{
  "user_id": "bc627dfa-7101-4e98-8e92-bbc02f97e7cd",
  "job_id": "user_notification_bc627dfa-7101-4e98-8e92-bbc02f97e7cd",
  "next_run_time": "2026-04-21T22:00:00+00:00"
}
```

這表示：

- 用戶的通知已排程
- 下次執行時間：2026-04-21 22:00 UTC（台北時間 2026-04-22 06:00）
- 頻率：每日 (daily)

#### ✅ 排程邏輯完整

代碼檢查顯示：

1. `DynamicScheduler._send_user_notification()` 函數存在且邏輯正確
2. 包含勿擾時段檢查
3. 包含技術深度過濾
4. 包含通知歷史記錄
5. 使用 LockManager 防止重複發送

### 可能的問題

#### 1. 時間設定問題

- 用戶設定的時間可能是未來時間
- 需要等到排程時間才會執行

#### 2. Bot 狀態問題

代碼中有檢查：

```python
if not bot.is_ready():
    self.logger.warning("Bot is not ready, skipping notification")
    return
```

如果 Discord Bot 未就緒，通知會被跳過。

#### 3. 通知管道未啟用

如果用戶的 `dm_enabled` 為 `false`，通知不會發送。

### 驗證步驟

#### 方法 1: 使用前端測試按鈕

1. 登入 http://localhost:3000
2. 進入 Settings > Notifications
3. 確認 Discord 私訊已啟用
4. 點擊「發送測試通知」按鈕
5. 檢查 Discord 是否收到測試通知

#### 方法 2: 檢查排程狀態

1. 在前端查看「排程狀態」卡片
2. 確認顯示「已排程」狀態
3. 查看「下次執行」時間

#### 方法 3: 查看後端日誌

```bash
# 實時監控通知發送
docker logs -f tech-news-agent-backend-dev | grep -i "sending scheduled notification\|successfully sent notification"

# 檢查排程任務
docker logs tech-news-agent-backend-dev 2>&1 | grep "user_notification" | tail -20
```

#### 方法 4: 手動觸發排程（開發用）

如果需要立即測試，可以：

1. 修改用戶的 `notification_time` 為當前時間後 2 分鐘
2. 點擊「重新排程」按鈕
3. 等待 2 分鐘後檢查是否收到通知

### 排程執行流程

```
1. APScheduler 在指定時間觸發
   ↓
2. DynamicScheduler._send_user_notification() 被調用
   ↓
3. 檢查勿擾時段
   ├─ 是 → 重新排程到勿擾時段結束後
   └─ 否 → 繼續
   ↓
4. 獲取通知鎖（防止重複）
   ↓
5. 檢查 Bot 是否就緒
   ↓
6. DMNotificationService.send_personalized_digest()
   ├─ 獲取用戶偏好的 feeds
   ├─ 根據技術深度過濾文章
   ├─ 發送 Discord DM
   └─ 記錄到 notification_history
   ↓
7. 釋放鎖
   ↓
8. 重新排程下次通知
```

### 檢查清單

- [ ] Discord Bot 已連接並就緒
- [ ] 用戶的 `dm_enabled` 為 `true`
- [ ] 用戶的 `frequency` 不是 `disabled`
- [ ] 排程時間已設定且為未來時間
- [ ] 資料庫中有可發送的文章
- [ ] 用戶已訂閱至少一個 feed
- [ ] 不在勿擾時段內

### 建議的測試計劃

1. **立即測試**（使用測試按鈕）
   - 驗證 Bot 連接正常
   - 驗證 DM 發送功能正常
   - 驗證技術深度過濾正常

2. **短期測試**（設定 2-5 分鐘後的時間）
   - 修改通知時間為當前時間 + 2 分鐘
   - 重新排程
   - 等待並觀察日誌

3. **長期測試**（保持原設定）
   - 等待原定的排程時間
   - 檢查是否收到通知
   - 驗證是否自動重新排程下次通知

## 後續行動

### 如果測試通知成功

✅ 表示系統正常，只需等待排程時間到達

### 如果測試通知失敗

需要檢查：

1. Discord Bot token 是否正確
2. Bot 是否有發送 DM 的權限
3. 用戶是否已與 Bot 建立過對話
4. 後端日誌中的具體錯誤訊息

### 如果排程時間到了但沒收到通知

需要檢查：

1. 後端日誌中是否有「Sending scheduled notification」
2. 是否有錯誤訊息
3. Bot 狀態是否為 ready
4. 是否在勿擾時段內

## 相關檔案

### Backend

- `backend/app/services/dynamic_scheduler.py` - 排程器主邏輯
- `backend/app/services/dm_notification_service.py` - DM 發送服務
- `backend/app/services/notification_system_integration.py` - 通知系統整合
- `backend/app/services/quiet_hours_service.py` - 勿擾時段檢查
- `backend/app/services/technical_depth_service.py` - 技術深度過濾

### Frontend

- `frontend/features/notifications/components/PersonalizedNotificationSettings.tsx` - 設定介面

### Database

- `user_notification_preferences` - 用戶通知偏好
- `notification_history` - 通知歷史記錄
- `user_quiet_hours` - 勿擾時段設定

---

**狀態**: 問題 1 已修復，問題 2 需要用戶測試驗證
**下一步**: 使用前端「發送測試通知」按鈕驗證功能
