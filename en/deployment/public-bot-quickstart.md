# 公開 Bot 快速開始

5 分鐘內將你的 Tech News Agent 改為公開 Bot！

## 步驟 1：資料庫遷移（1 分鐘）

在 Supabase SQL Editor 執行：

```sql
ALTER TABLE users
ADD COLUMN IF NOT EXISTS dm_notifications_enabled BOOLEAN DEFAULT true;
```

## 步驟 2：更新 .env（1 分鐘）

```bash
# 將 DISCORD_CHANNEL_ID 改為選填
DISCORD_CHANNEL_ID=  # 留空或移除

# 新增 DM 通知排程
DM_NOTIFICATION_CRON=10 */6 * * *
```

## 步驟 3：Discord 設定（2 分鐘）

1. 前往 [Discord Developer Portal](https://discord.com/developers/applications)
2. 選擇你的應用程式 > Bot
3. 開啟 **Public Bot** 開關
4. 複製邀請連結：
   ```
   https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=277025508352&scope=bot%20applications.commands
   ```

## 步驟 4：重新部署（1 分鐘）

```bash
docker-compose down
docker-compose up -d
```

## 步驟 5：測試（30 秒）

在 Discord 中執行：

```
/notification_status
/notifications enabled:開啟通知
```

## 完成！🎉

現在你的 bot 是公開的，任何人都可以：

1. 使用邀請連結加入 bot
2. 訂閱自己的 RSS feeds
3. 接收個人化的 DM 通知

## 新增指令

- `/notifications` - 開啟/關閉 DM 通知
- `/notification_status` - 查看通知設定

## 邀請連結範例

```
https://discord.com/api/oauth2/authorize?client_id=1234567890&permissions=277025508352&scope=bot%20applications.commands
```

將 `1234567890` 替換為你的 Client ID。

## 需要詳細說明？

查看完整文件：

- [PUBLIC_BOT_SETUP.md](./PUBLIC_BOT_SETUP.md) - 完整設定指南
- [PUBLIC_BOT_MIGRATION_SUMMARY.md](./PUBLIC_BOT_MIGRATION_SUMMARY.md) - 技術細節

## 常見問題

**Q: 我的使用者需要做什麼？**
A: 什麼都不用！現有使用者會自動啟用 DM 通知。

**Q: 如何分享 bot？**
A: 分享邀請連結即可，使用者點擊後可將 bot 加入他們的伺服器。

**Q: DM 通知何時發送？**
A: 預設在文章抓取後 10 分鐘（每 6 小時一次）。
