# 🔧 Database Migration Guide

## 問題描述

通知偏好設定功能需要兩個新的資料庫表格：

- `user_notification_preferences` - 儲存使用者的個人化通知設定
- `notification_locks` - 防止重複通知的鎖定機制

這些表格尚未在資料庫中建立，導致前端顯示「無法載入通知偏好設定」錯誤。

## 解決方案

### 步驟 1: 開啟 Supabase SQL 編輯器

1. 前往您的 Supabase Dashboard
2. 點擊左側選單的 **SQL Editor**
3. 點擊 **New query** 建立新查詢

### 步驟 2: 執行第一個遷移 (user_notification_preferences)

複製以下 SQL 並執行：

```sql
-- Migration 005: Create user_notification_preferences table
-- Task 1.1: Create database migration for user_notification_preferences table
-- Requirements: 4.1, 4.2, 4.3, 4.6, 4.7
--
-- This migration creates the user_notification_preferences table to store individual
-- user notification settings for the personalized notification frequency feature.
-- This replaces the system-wide DM_NOTIFICATION_CRON with per-user preferences.
--
-- Default values:
-- - frequency: weekly (every Friday)
-- - notification_time: 18:00 (6 PM)
-- - timezone: Asia/Taipei
-- - dm_enabled: true
-- - email_enabled: false

-- Create user_notification_preferences table
CREATE TABLE IF NOT EXISTS user_notification_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Notification frequency: daily, weekly, monthly, disabled
    frequency TEXT NOT NULL DEFAULT 'weekly'
        CHECK (frequency IN ('daily', 'weekly', 'monthly', 'disabled')),

    -- Notification time in HH:MM format (24-hour)
    notification_time TIME NOT NULL DEFAULT '18:00:00',

    -- IANA timezone identifier
    timezone TEXT NOT NULL DEFAULT 'Asia/Taipei',

    -- Channel preferences
    dm_enabled BOOLEAN NOT NULL DEFAULT true,
    email_enabled BOOLEAN NOT NULL DEFAULT false,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    -- Ensure one preference record per user
    UNIQUE(user_id)
);

-- Create indexes for optimized query performance
CREATE INDEX IF NOT EXISTS idx_user_notification_preferences_user_id
    ON user_notification_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_user_notification_preferences_frequency
    ON user_notification_preferences(frequency);

-- Create trigger to automatically update updated_at timestamp
CREATE TRIGGER update_user_notification_preferences_updated_at
    BEFORE UPDATE ON user_notification_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments to document the table and columns
COMMENT ON TABLE user_notification_preferences IS 'Stores individual user notification preferences for personalized notification scheduling';
COMMENT ON COLUMN user_notification_preferences.user_id IS 'Foreign key to users table, one preference record per user';
COMMENT ON COLUMN user_notification_preferences.frequency IS 'Notification frequency: daily, weekly, monthly, or disabled';
COMMENT ON COLUMN user_notification_preferences.notification_time IS 'Time of day to send notifications in user timezone (HH:MM format)';
COMMENT ON COLUMN user_notification_preferences.timezone IS 'IANA timezone identifier for user location';
COMMENT ON COLUMN user_notification_preferences.dm_enabled IS 'Whether Discord DM notifications are enabled';
COMMENT ON COLUMN user_notification_preferences.email_enabled IS 'Whether email notifications are enabled';
```

### 步驟 3: 執行第二個遷移 (notification_locks)

複製以下 SQL 並執行：

```sql
-- Migration 006: Create notification_locks table
-- Task 1.1: Create database migration for notification_locks table (part of user_notification_preferences feature)
-- Requirements: 4.4, 4.5, 4.7, 10.1, 10.2, 10.3, 10.4, 10.5
--
-- This migration creates the notification_locks table to prevent duplicate notifications
-- when multiple backend instances are running simultaneously. Uses atomic database
-- operations to coordinate notification delivery across instances.
--
-- Lock statuses:
-- - pending: Lock created, ready for processing
-- - processing: Lock acquired by an instance, notification in progress
-- - completed: Notification successfully sent
-- - failed: Notification failed to send

-- Create notification_locks table
CREATE TABLE IF NOT EXISTS notification_locks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Type of notification (e.g., 'weekly_digest', 'daily_summary')
    notification_type TEXT NOT NULL,

    -- When this notification was scheduled to be sent
    scheduled_time TIMESTAMPTZ NOT NULL,

    -- Lock status for coordination between instances
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed')),

    -- Instance ID that acquired the lock
    instance_id TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL,

    -- Ensure unique lock per user/type/time combination
    UNIQUE(user_id, notification_type, scheduled_time)
);

-- Create indexes for efficient lock queries and cleanup
CREATE INDEX IF NOT EXISTS idx_notification_locks_user_scheduled
    ON notification_locks(user_id, scheduled_time);
CREATE INDEX IF NOT EXISTS idx_notification_locks_status_expires
    ON notification_locks(status, expires_at);
CREATE INDEX IF NOT EXISTS idx_notification_locks_instance_status
    ON notification_locks(instance_id, status);

-- Add comments to document the table and columns
COMMENT ON TABLE notification_locks IS 'Prevents duplicate notifications across multiple backend instances using atomic locking';
COMMENT ON COLUMN notification_locks.user_id IS 'Foreign key to users table, identifies user for this notification lock';
COMMENT ON COLUMN notification_locks.notification_type IS 'Type of notification being locked (weekly_digest, daily_summary, etc.)';
COMMENT ON COLUMN notification_locks.scheduled_time IS 'When this notification was scheduled to be sent';
COMMENT ON COLUMN notification_locks.status IS 'Lock status: pending, processing, completed, or failed';
COMMENT ON COLUMN notification_locks.instance_id IS 'Identifier of the backend instance that acquired this lock';
COMMENT ON COLUMN notification_locks.expires_at IS 'When this lock expires to prevent deadlocks';
```

### 步驟 4: 驗證遷移

執行以下查詢來確認表格已正確建立：

```sql
-- Check if tables exist and show their structure
SELECT table_name, column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name IN ('user_notification_preferences', 'notification_locks')
ORDER BY table_name, ordinal_position;
```

您應該會看到兩個表格的完整欄位列表。

### 步驟 5: 測試功能

1. 重新整理前端頁面
2. 前往通知設定頁面
3. 確認不再顯示「無法載入通知偏好設定」錯誤
4. 嘗試修改通知設定並儲存

## 預期結果

遷移完成後：

- ✅ 前端可以正常載入通知偏好設定
- ✅ 使用者可以修改通知頻率、時間和時區
- ✅ 系統會自動為新使用者建立預設設定
- ✅ 通知排程系統可以正常運作

## 故障排除

### 如果遷移失敗

1. **權限錯誤**: 確認您使用的是 service_role key，不是 anon key
2. **語法錯誤**: 確認完整複製了 SQL 內容，沒有遺漏
3. **外鍵錯誤**: 確認 `users` 表格已存在且有資料

### 如果前端仍然顯示錯誤

1. 清除瀏覽器快取
2. 重新啟動後端服務
3. 檢查瀏覽器開發者工具的 Network 標籤，查看 API 請求是否成功

## 聯絡支援

如果遇到問題，請提供：

- 錯誤訊息的完整內容
- Supabase SQL 編輯器的執行結果
- 瀏覽器開發者工具的錯誤訊息
