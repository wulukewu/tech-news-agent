# 公開 Bot 遷移摘要

## 改動概覽

將 Tech News Agent 從私人伺服器模式改為公開 Bot + DM 推播模式。

## 主要變更

### 1. 資料庫 Schema

- ✅ 新增 `users.dm_notifications_enabled` 欄位（預設 `true`）
- ✅ 提供遷移腳本：`scripts/add_dm_notifications_column.sql`

### 2. 新增檔案

| 檔案                                              | 說明             |
| ------------------------------------------------- | ---------------- |
| `backend/app/bot/cogs/notification_settings.py`   | 通知設定指令 Cog |
| `backend/app/services/dm_notification_service.py` | DM 通知服務      |
| `scripts/add_dm_notifications_column.sql`         | 資料庫遷移腳本   |
| `docs/PUBLIC_BOT_SETUP.md`                        | 完整設定指南     |

### 3. 修改檔案

| 檔案                                       | 變更內容                                        |
| ------------------------------------------ | ----------------------------------------------- |
| `scripts/init_supabase.sql`                | 新增 `dm_notifications_enabled` 欄位到 users 表 |
| `backend/app/services/supabase_service.py` | 新增通知設定相關方法                            |
| `backend/app/bot/client.py`                | 載入 notification_settings cog                  |
| `backend/app/tasks/scheduler.py`           | 新增 DM 通知排程任務                            |
| `backend/app/core/config.py`               | 新增 DM 通知設定                                |
| `.env.example`                             | 更新環境變數說明                                |

### 4. 新增功能

#### Discord 指令

- `/notifications` - 開啟/關閉 DM 通知
- `/notification_status` - 查看通知設定狀態

#### 服務方法

- `SupabaseService.update_notification_settings()` - 更新通知設定
- `SupabaseService.get_notification_settings()` - 查詢通知設定
- `SupabaseService.get_users_with_dm_enabled()` - 查詢啟用通知的使用者
- `SupabaseService.get_user_articles()` - 查詢使用者訂閱的文章

#### 排程任務

- `send_dm_notifications()` - 發送 DM 通知給所有使用者
- 可透過 `DM_NOTIFICATION_CRON` 環境變數自訂排程

## 部署步驟

### 1. 資料庫遷移

```sql
-- 在 Supabase SQL Editor 執行
ALTER TABLE users
ADD COLUMN IF NOT EXISTS dm_notifications_enabled BOOLEAN DEFAULT true;
```

### 2. 更新環境變數

```bash
# .env
DISCORD_CHANNEL_ID=  # 改為選填
DM_NOTIFICATION_CRON=10 */6 * * *  # 新增
```

### 3. Discord Developer Portal 設定

1. 開啟 **Public Bot**
2. 確認權限：Send Messages, Embed Links, Use Slash Commands
3. 生成邀請連結

### 4. 重新部署

```bash
docker-compose down
docker-compose up -d
```

### 5. 測試

```
/notification_status
/notifications enabled:開啟通知
```

## 向後相容性

- ✅ 現有使用者自動啟用 DM 通知（預設 `true`）
- ✅ 現有指令完全相容
- ✅ 可選擇保留頻道通知功能（設定 `DISCORD_CHANNEL_ID`）

## 使用者體驗

### 之前（私人伺服器模式）

1. 使用者加入你的私人伺服器
2. Bot 在固定頻道發送通知
3. 所有人看到相同內容

### 之後（公開 Bot + DM 模式）

1. 使用者邀請 bot 到任何伺服器
2. Bot 發送個人化 DM 通知
3. 每個使用者看到自己訂閱的內容

## 技術優勢

1. **多租戶架構** - 每個使用者獨立資料
2. **個人化內容** - 基於使用者訂閱
3. **隱私保護** - DM 只有使用者看得到
4. **可擴展性** - 支援無限使用者
5. **靈活部署** - 使用者可加入任何伺服器

## 監控與日誌

DM 發送統計會記錄在日誌中：

```
DM notification job completed:
Total users: 150,
Successful: 145,
Failed: 5
```

失敗原因包括：

- 使用者關閉 DM
- 使用者封鎖 bot
- 沒有共同伺服器
- Discord API 錯誤

## 下一步

1. 閱讀 [PUBLIC_BOT_SETUP.md](./PUBLIC_BOT_SETUP.md) 完整指南
2. 執行資料庫遷移
3. 更新環境變數
4. 設定 Discord Developer Portal
5. 測試 DM 功能
6. 分享邀請連結

## 常見問題

**Q: 舊使用者需要重新註冊嗎？**
A: 不需要，現有使用者會自動啟用 DM 通知。

**Q: 可以同時保留頻道通知嗎？**
A: 可以，保留 `DISCORD_CHANNEL_ID` 設定即可。

**Q: DM 通知頻率是多少？**
A: 預設每 6 小時一次，可透過 `DM_NOTIFICATION_CRON` 自訂。

**Q: 如何停用 DM 通知？**
A: 使用者可用 `/notifications` 指令關閉，或管理員可移除 `DM_NOTIFICATION_CRON` 設定。
