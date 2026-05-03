# 公開 Bot 設定指南

本指南說明如何將 Tech News Agent 設定為公開 Bot，讓任何人都可以邀請到他們的伺服器，並接收個人化的 DM 通知。

## 目錄

1. [Discord Developer Portal 設定](#discord-developer-portal-設定)
2. [資料庫遷移](#資料庫遷移)
3. [環境變數設定](#環境變數設定)
4. [測試 DM 功能](#測試-dm-功能)
5. [邀請連結生成](#邀請連結生成)
6. [常見問題](#常見問題)

---

## Discord Developer Portal 設定

### 1. 將 Bot 設為 Public

1. 前往 [Discord Developer Portal](https://discord.com/developers/applications)
2. 選擇你的應用程式
3. 進入 **Bot** 頁面
4. 找到 **Public Bot** 選項
5. **開啟** Public Bot 開關

![Public Bot Setting](https://i.imgur.com/example.png)

### 2. 設定 Bot 權限

確保 Bot 有以下權限：

#### Required Permissions (必要權限)

- `Send Messages` - 發送訊息
- `Send Messages in Threads` - 在討論串發送訊息
- `Embed Links` - 嵌入連結
- `Use Slash Commands` - 使用斜線指令

#### Optional Permissions (選填權限)

- `Read Message History` - 讀取訊息歷史（如果需要）

### 3. 設定 Privileged Gateway Intents

在 **Bot** 頁面中，確保以下 Intents 已啟用：

- ✅ **Message Content Intent** - 讀取訊息內容（如果需要）
- ⚠️ **Server Members Intent** - 不需要（除非有其他功能需求）
- ⚠️ **Presence Intent** - 不需要

> 注意：Message Content Intent 在 bot 加入超過 100 個伺服器後需要驗證。

---

## 資料庫遷移

### 新增 DM 通知欄位

如果你已經有現有的資料庫，需要執行遷移腳本：

```bash
# 在 Supabase Dashboard > SQL Editor 中執行
cat scripts/add_dm_notifications_column.sql
```

或直接執行 SQL：

```sql
-- Add dm_notifications_enabled column to users table
ALTER TABLE users
ADD COLUMN IF NOT EXISTS dm_notifications_enabled BOOLEAN DEFAULT true;

-- Add comment for documentation
COMMENT ON COLUMN users.dm_notifications_enabled IS 'Whether user wants to receive DM notifications for new articles (default: true)';
```

### 驗證遷移

```sql
-- 檢查欄位是否存在
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'users' AND column_name = 'dm_notifications_enabled';
```

---

## 環境變數設定

### 更新 .env 檔案

```bash
# Discord Bot Configuration
DISCORD_TOKEN=your_discord_bot_token_here
# DISCORD_CHANNEL_ID 現在是選填的（如果要保留頻道通知功能）
DISCORD_CHANNEL_ID=  # 可以留空

# DM Notification Configuration
# DM 通知排程（建議在文章抓取後 10 分鐘執行）
DM_NOTIFICATION_CRON=10 */6 * * *

# Scheduler Configuration
SCHEDULER_CRON=0 */6 * * *
SCHEDULER_TIMEZONE=Asia/Taipei
```

### 設定說明

| 變數                   | 說明                         | 預設值         |
| ---------------------- | ---------------------------- | -------------- |
| `DISCORD_CHANNEL_ID`   | 選填，如果要保留頻道通知功能 | None           |
| `DM_NOTIFICATION_CRON` | DM 通知排程（CRON 表達式）   | `10 */6 * * *` |
| `SCHEDULER_CRON`       | 文章抓取排程                 | `0 */6 * * *`  |

---

## 測試 DM 功能

### 1. 啟動 Bot

```bash
# 使用 Docker Compose
docker-compose up -d

# 或本地執行
python -m backend.app.main
```

### 2. 測試指令

在 Discord 中測試以下指令：

#### 查看通知設定

```
/notification_status
```

#### 開啟/關閉通知

```
/notifications enabled:開啟通知
/notifications enabled:關閉通知
```

#### 訂閱 Feed

```
/add_feed name:Hacker News url:https://news.ycombinator.com/rss category:Tech News
```

#### 查看文章

```
/news_now
```

### 3. 測試 DM 發送

確保你的 Discord 隱私設定允許接收 DM：

1. 右鍵點擊伺服器圖示
2. 選擇 **隱私設定**
3. 開啟 **允許來自伺服器成員的私人訊息**

![Discord Privacy Settings](https://i.imgur.com/example2.png)

---

## 邀請連結生成

### 1. 生成 OAuth2 URL

1. 前往 [Discord Developer Portal](https://discord.com/developers/applications)
2. 選擇你的應用程式
3. 進入 **OAuth2** > **URL Generator**
4. 選擇以下 Scopes：
   - ✅ `bot`
   - ✅ `applications.commands`

5. 選擇 Bot Permissions：
   - ✅ Send Messages
   - ✅ Send Messages in Threads
   - ✅ Embed Links
   - ✅ Use Slash Commands

6. 複製生成的 URL

### 2. 邀請連結範例

```
https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=277025508352&scope=bot%20applications.commands
```

### 3. 分享邀請連結

你可以：

- 在 README 中加入邀請連結
- 建立專屬的邀請頁面
- 在社群媒體分享

---

## 常見問題

### Q1: 為什麼我收不到 DM？

**可能原因：**

1. **Discord 隱私設定**
   - 確保你的伺服器隱私設定允許接收 DM
   - 路徑：伺服器 > 右鍵 > 隱私設定 > 允許來自伺服器成員的私人訊息

2. **通知設定未開啟**
   - 使用 `/notification_status` 檢查狀態
   - 使用 `/notifications enabled:開啟通知` 來開啟

3. **沒有訂閱任何 Feed**
   - 使用 `/add_feed` 訂閱至少一個 RSS 來源
   - 使用 `/list_feeds` 查看訂閱列表

4. **Bot 未與你共享伺服器**
   - Bot 只能 DM 與它有共同伺服器的使用者
   - 確保你和 bot 都在同一個伺服器中

### Q2: DM 通知的頻率是多少？

預設情況下，DM 通知會在文章抓取後 10 分鐘發送。

- 文章抓取：每 6 小時一次（`SCHEDULER_CRON=0 */6 * * *`）
- DM 通知：抓取後 10 分鐘（`DM_NOTIFICATION_CRON=10 */6 * * *`）

你可以在 `.env` 中自訂這些排程。

### Q3: 如何停用 DM 通知？

有兩種方式：

**方式 1：使用者自行關閉**

```
/notifications enabled:關閉通知
```

**方式 2：全域停用（管理員）**

```bash
# 在 .env 中設定
DM_NOTIFICATION_CRON=  # 留空即停用
```

### Q4: Bot 可以加入多少個伺服器？

- **未驗證 Bot**：最多 100 個伺服器
- **已驗證 Bot**：無限制（需要通過 Discord 驗證流程）

當 bot 接近 100 個伺服器時，你需要申請驗證：

1. 前往 Discord Developer Portal
2. 選擇你的應用程式
3. 進入 **Bot** > **Verification**
4. 填寫驗證表單

### Q5: 如何追蹤 DM 發送統計？

查看應用程式日誌：

```bash
# Docker Compose
docker-compose logs -f backend

# 本地執行
tail -f logs/app.log
```

日誌會顯示：

- 總使用者數
- 成功發送數
- 失敗數
- 失敗原因

### Q6: 使用者資料如何隔離？

每個使用者都有獨立的：

- 訂閱列表（`user_subscriptions` 表）
- 閱讀清單（`reading_list` 表）
- 通知設定（`users.dm_notifications_enabled` 欄位）

資料完全隔離，使用者之間互不影響。

### Q7: 如何處理 Rate Limit？

Discord API 有 Rate Limit 限制：

- 每個使用者每秒最多 5 個 DM
- 全域每秒最多 50 個請求

Bot 會自動處理 Rate Limit：

- 使用 `discord.py` 的內建 Rate Limit 處理
- 失敗的 DM 會記錄在日誌中
- 不會影響其他使用者

---

## 架構變更摘要

### 新增功能

1. **DM 通知系統**
   - 個人化文章摘要
   - 按類別分組顯示
   - 自動 Rate Limit 處理

2. **通知設定指令**
   - `/notifications` - 開啟/關閉通知
   - `/notification_status` - 查看目前設定

3. **資料庫欄位**
   - `users.dm_notifications_enabled` - 通知開關

4. **排程任務**
   - `send_dm_notifications` - DM 通知任務
   - 可透過 CRON 表達式自訂排程

### 移除/變更

1. **DISCORD_CHANNEL_ID**
   - 從必填改為選填
   - 如果要保留頻道通知功能可繼續使用

2. **通知方式**
   - 從固定頻道推播改為個人 DM
   - 每個使用者收到個人化內容

---

## 下一步

1. ✅ 完成 Discord Developer Portal 設定
2. ✅ 執行資料庫遷移
3. ✅ 更新環境變數
4. ✅ 測試 DM 功能
5. ✅ 生成並分享邀請連結
6. 📊 監控 DM 發送統計
7. 🎉 開始接受使用者！

---

## 相關文件

- [User Guide](./USER_GUIDE.md) - 使用者指南
- [Developer Guide](./DEVELOPER_GUIDE.md) - 開發者指南
- [Environment Setup](./setup/ENV_SETUP_GUIDE.md) - 環境變數設定

---

## 需要協助？

如果遇到問題，請：

1. 查看日誌檔案
2. 檢查 Discord Developer Portal 設定
3. 確認資料庫遷移已完成
4. 在 GitHub Issues 提問
