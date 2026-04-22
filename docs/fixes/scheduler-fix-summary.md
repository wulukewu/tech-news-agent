# 排程器修復總結

**日期**: 2026-04-21
**問題**: 排程器執行但通知發送失敗

## 🎯 核心發現

排程器**本身工作正常**，在設定的時間正確觸發了任務。但通知發送失敗是因為以下問題：

## 🐛 發現並修復的問題

### 問題 1: 傳遞錯誤的 ID 類型 ✅ 已修復

**問題描述**:

- `_send_user_notification` 傳遞 `user_id`（UUID）給 `send_personalized_digest`
- 但 `send_personalized_digest` 需要 `discord_id`（字串）

**錯誤日誌**:

```
Invalid discord_id format: bc627dfa-7101-4e98-8e92-bbc02f97e7cd, skipping
```

**解決方案**:

1. 在 `SupabaseService` 中添加新函數 `get_user_by_id(user_id: UUID)`
2. 在 `_send_user_notification` 中先獲取用戶的 `discord_id`
3. 然後傳遞正確的 `discord_id` 給 `send_personalized_digest`

**修改的檔案**:

- `backend/app/services/supabase_service.py` - 添加 `get_user_by_id()` 函數
- `backend/app/services/dynamic_scheduler.py` - 修改調用邏輯

### 問題 2: notification_locks 表缺少 updated_at 欄位 ⚠️ 需要運行遷移

**問題描述**:

- 代碼嘗試更新 `notification_locks.updated_at` 欄位
- 但表定義中沒有這個欄位

**錯誤日誌**:

```
Could not find the 'updated_at' column of 'notification_locks' in the schema cache
```

**解決方案**:
創建遷移腳本 `010_add_updated_at_to_notification_locks.sql`

**需要執行的 SQL**:

```sql
-- 在 Supabase SQL Editor 中執行
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'notification_locks'
        AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE notification_locks
        ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

        COMMENT ON COLUMN notification_locks.updated_at IS 'When this lock was last updated';

        RAISE NOTICE 'Added updated_at column to notification_locks table';
    ELSE
        RAISE NOTICE 'updated_at column already exists in notification_locks table';
    END IF;
END $$;
```

## 📊 測試結果

### 第一次測試 (09:55)

- ✅ 排程器在 09:55 正確觸發
- ❌ 通知發送失敗（問題 1 和 2）

### 第二次測試 (10:05)

- ✅ 排程器在 10:05 正確觸發
- ❌ 通知發送失敗（問題 1 - 函數調用錯誤）

### 第三次測試 (待執行)

- 修復問題 1 後重新測試
- 需要先運行遷移修復問題 2

## 🔧 修復後的流程

```
1. APScheduler 在設定時間觸發
   ↓
2. DynamicScheduler._send_user_notification() 被調用
   ↓
3. 檢查勿擾時段 ✅
   ↓
4. 獲取通知鎖 ✅
   ↓
5. 檢查 Bot 是否就緒 ✅
   ↓
6. 從資料庫獲取用戶的 discord_id ✅ (新增)
   ↓
7. 調用 DMNotificationService.send_personalized_digest(discord_id) ✅ (修復)
   ↓
8. 發送 Discord DM
   ↓
9. 記錄到 notification_history
   ↓
10. 釋放鎖 (需要 updated_at 欄位)
   ↓
11. 重新排程下次通知
```

## 📝 下一步行動

### 立即執行

1. **運行資料庫遷移**（在 Supabase SQL Editor）:

   ```sql
   ALTER TABLE notification_locks
   ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
   ```

2. **確認後端已重啟**:

   ```bash
   curl http://localhost:8000/health
   ```

3. **設定新的測試時間**:
   - 在前端設定「當前時間 + 2 分鐘」
   - 等待並觀察

4. **監控日誌**:
   ```bash
   docker logs -f tech-news-agent-backend-dev | grep -i "sending scheduled\|successfully sent\|failed"
   ```

### 預期結果

修復後，應該看到：

```
✅ Sending scheduled notification to user
✅ User not in quiet hours, proceeding with notification
✅ Successfully acquired notification lock
✅ Successfully sent notification to user
✅ Successfully rescheduled user notification
```

## 🎉 總結

排程系統的核心邏輯是正確的：

- ✅ 時間計算正確
- ✅ 排程觸發正確
- ✅ 勿擾時段檢查正確
- ✅ 鎖機制正確

只是有兩個小問題：

1. ID 類型轉換問題（已修復）
2. 資料庫欄位缺失（需要運行遷移）

修復這兩個問題後，排程通知應該就能正常工作了！

---

**修改的檔案**:

- `backend/app/services/supabase_service.py` - 添加 `get_user_by_id()` 函數
- `backend/app/services/dynamic_scheduler.py` - 修改獲取 discord_id 的邏輯
- `scripts/migrations/010_add_updated_at_to_notification_locks.sql` - 新增遷移腳本

**需要運行的遷移**:

- `010_add_updated_at_to_notification_locks.sql`
