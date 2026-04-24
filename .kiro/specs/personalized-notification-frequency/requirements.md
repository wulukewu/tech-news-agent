# 需求文件

## 簡介

個人化通知頻率功能允許每個使用者自訂通知偏好，取代現有的系統級固定 DM_NOTIFICATION_CRON 排程。使用者可以設定通知頻率、時間和時區，並透過 Discord 和 UI 界面進行設定同步。

## 詞彙表

- **Notification_System**: 負責管理和發送通知的系統
- **User_Preferences**: 儲存個別使用者通知設定的資料結構
- **Dynamic_Scheduler**: 根據使用者偏好動態排程通知的排程器
- **Discord_Interface**: Discord 機器人命令界面
- **Web_Interface**: 網頁使用者界面
- **Notification_Job**: 個別的通知任務
- **Time_Zone**: 使用者所在的時區設定
- **Notification_Lock**: 防止重複通知的鎖定機制
- **Atomic_Operation**: 原子性資料庫操作，確保資料一致性
- **Notification_Log**: 通知發送的詳細記錄

## 需求

### 需求 1: 移除系統級固定排程

**使用者故事:** 作為系統管理員，我希望移除固定的 DM_NOTIFICATION_CRON 設定，以便實現個人化通知排程。

#### 驗收標準

1. THE Notification_System SHALL 移除現有的 DM_NOTIFICATION_CRON 環境變數依賴
2. THE Notification_System SHALL 停用所有基於固定 CRON 的通知排程
3. WHEN 系統啟動時，THE Notification_System SHALL 不再使用系統級 CRON 設定

### 需求 2: 預設通知設定

**使用者故事:** 作為新使用者，我希望系統提供合理的預設通知設定，以便在我自訂設定前仍能收到通知。

#### 驗收標準

1. THE User_Preferences SHALL 為新使用者設定預設通知時間為每週五台灣時間晚上六點
2. THE User_Preferences SHALL 設定預設時區為 Asia/Taipei
3. THE User_Preferences SHALL 設定預設通知頻率為每週
4. WHEN 使用者首次註冊時，THE Notification_System SHALL 自動建立預設通知偏好

### 需求 3: 個人化通知偏好設定

**使用者故事:** 作為使用者，我希望能夠自訂我的通知頻率、時間和時區，以便按照我的需求接收通知。

#### 驗收標準

1. THE User_Preferences SHALL 允許使用者設定通知頻率（每日、每週、每月、關閉）
2. THE User_Preferences SHALL 允許使用者設定通知時間（小時和分鐘）
3. THE User_Preferences SHALL 允許使用者選擇時區
4. THE User_Preferences SHALL 驗證時間設定的有效性（0-23小時，0-59分鐘）
5. THE User_Preferences SHALL 支援所有標準時區識別碼

### 需求 4: 資料庫架構擴展

**使用者故事:** 作為開發者，我需要資料庫架構來儲存個人通知偏好和防重複機制，以便系統能夠管理每個使用者的設定並防止重複通知。

#### 驗收標準

1. THE Database_Schema SHALL 建立 user_notification_preferences 資料表
2. THE user_notification_preferences 資料表 SHALL 包含 user_id、frequency、notification_time、timezone、enabled 欄位
3. THE user_notification_preferences 資料表 SHALL 與現有使用者資料表建立外鍵關聯
4. THE Database_Schema SHALL 建立 notification_locks 資料表用於防重複機制
5. THE notification_locks 資料表 SHALL 包含 user_id、notification_type、scheduled_time、status、created_at、expires_at 欄位
6. THE Database_Schema SHALL 支援資料遷移以保持現有資料完整性
7. THE 資料表 SHALL 設定適當的索引以優化查詢效能和鎖定機制

### 需求 5: 動態排程系統

**使用者故事:** 作為系統，我需要根據每個使用者的偏好動態排程通知，以便在正確的時間發送個人化通知。

#### 驗收標準

1. THE Dynamic_Scheduler SHALL 根據使用者偏好建立個別的 Notification_Job
2. WHEN 使用者更新通知偏好時，THE Dynamic_Scheduler SHALL 重新排程該使用者的通知
3. THE Dynamic_Scheduler SHALL 處理時區轉換以確保在使用者本地時間發送通知
4. THE Dynamic_Scheduler SHALL 支援不同頻率的通知排程（每日、每週、每月）
5. IF 使用者停用通知，THEN THE Dynamic_Scheduler SHALL 取消該使用者的所有排程通知

### 需求 6: Web 界面通知偏好設定

**使用者故事:** 作為使用者，我希望透過網頁界面管理我的通知偏好，以便方便地調整設定。

#### 驗收標準

1. THE Web_Interface SHALL 提供通知偏好設定頁面
2. THE Web_Interface SHALL 顯示目前的通知設定狀態
3. THE Web_Interface SHALL 允許使用者修改通知頻率、時間和時區
4. THE Web_Interface SHALL 提供即時預覽下次通知時間
5. WHEN 使用者儲存設定時，THE Web_Interface SHALL 驗證輸入並顯示確認訊息
6. THE Web_Interface SHALL 正確顯示 DM 通知的開啟/關閉狀態

### 需求 7: Discord 界面通知偏好設定

**使用者故事:** 作為 Discord 使用者，我希望透過 Discord 命令管理我的通知偏好，以便在 Discord 內直接調整設定。

#### 驗收標準

1. THE Discord_Interface SHALL 提供 `/notification-settings` 命令查看目前設定
2. THE Discord_Interface SHALL 提供 `/set-notification-frequency` 命令設定通知頻率
3. THE Discord_Interface SHALL 提供 `/set-notification-time` 命令設定通知時間
4. THE Discord_Interface SHALL 提供 `/set-timezone` 命令設定時區
5. THE Discord_Interface SHALL 提供 `/toggle-notifications` 命令開啟/關閉通知
6. WHEN 使用者透過 Discord 更新設定時，THE Discord_Interface SHALL 同步更新資料庫

### 需求 8: 設定同步機制

**使用者故事:** 作為使用者，我希望我在 Discord 和網頁界面的通知設定保持同步，以便無論在哪個平台都能看到一致的設定。

#### 驗收標準

1. WHEN 使用者在 Web_Interface 更新設定時，THE Notification_System SHALL 立即同步到所有界面
2. WHEN 使用者在 Discord_Interface 更新設定時，THE Notification_System SHALL 立即同步到所有界面
3. THE Notification_System SHALL 確保所有界面顯示相同的設定狀態
4. THE Notification_System SHALL 在設定更新後觸發 Dynamic_Scheduler 重新排程

### 需求 9: Email 通知功能實現

**使用者故事:** 作為使用者，我希望能夠接收 Email 通知，以便在不使用 Discord 時也能收到重要訊息。

#### 驗收標準

1. THE Notification_System SHALL 實現 Email 通知發送功能
2. THE User_Preferences SHALL 包含 Email 通知的開啟/關閉設定
3. THE Email_Notifier SHALL 使用使用者註冊的 Email 地址發送通知
4. THE Email_Notifier SHALL 提供 HTML 和純文字兩種格式的通知
5. WHEN Email 發送失敗時，THE Notification_System SHALL 記錄錯誤並重試

### 需求 10: 防重複通知機制

**使用者故事:** 作為系統管理員，我希望在多個後端實例同時運行時，系統能防止使用者收到重複的通知，以確保良好的使用者體驗。

#### 驗收標準

1. THE Notification_System SHALL 在發送通知前先在資料庫中建立通知鎖定記錄
2. THE Notification_System SHALL 使用原子性操作檢查並設定通知狀態，防止競爭條件
3. WHEN 通知發送完成時，THE Notification_System SHALL 更新通知狀態為已完成
4. IF 另一個後端實例嘗試發送相同通知，THEN THE Notification_System SHALL 檢測到已存在的鎖定並跳過發送
5. THE Notification_System SHALL 設定通知鎖定的過期時間，防止死鎖情況
6. THE Notification_System SHALL 記錄通知發送日誌以便追蹤和除錯

### 需求 11: 通知狀態修正

**使用者故事:** 作為使用者，我希望系統正確顯示我的 DM 通知狀態，以便我能準確了解我的設定。

#### 驗收標準

1. THE Web_Interface SHALL 正確讀取並顯示使用者的 DM 通知開啟/關閉狀態
2. THE Discord_Interface SHALL 正確讀取並顯示使用者的 DM 通知開啟/關閉狀態
3. WHEN 使用者切換 DM 通知狀態時，THE Notification_System SHALL 立即更新顯示
4. THE Notification_System SHALL 修正任何導致狀態顯示不正確的現有錯誤
