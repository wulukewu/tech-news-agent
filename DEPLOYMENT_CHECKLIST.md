# 通知頻率增強功能 - 部署檢查清單

## 📋 部署前檢查

### ✅ 資料庫層

- [x] Migration 009 已建立
- [x] Migration 已在 Supabase 執行
- [x] 欄位驗證通過
- [x] 索引已建立
- [x] 現有記錄已更新預設值

**驗證命令**:

```bash
python3 scripts/verify_migration_009.py
```

**預期輸出**:

```
✅ Migration verified successfully!
   notification_day_of_week: 5
   notification_day_of_month: 1
```

### ✅ 後端層

- [x] Repository 層已更新
- [x] Schema 層已更新
- [x] 排程邏輯已更新
- [x] 驗證邏輯已實作
- [x] 測試已通過

**測試命令**:

```bash
python3 scripts/test_notification_scheduling.py
```

**預期輸出**:

```
✅ All tests completed!
```

### ✅ 前端層

- [x] API 類型定義已更新
- [x] UI 組件已更新
- [x] 條件式顯示已實作
- [x] 預覽功能已實作

**檢查命令**:

```bash
cd frontend
npm run type-check
npm run lint
npm run build
```

## 🚀 部署步驟

### 步驟 1: 資料庫遷移（已完成 ✅）

```bash
# 在 Supabase Dashboard > SQL Editor 執行
# scripts/migrations/009_add_notification_day_fields.sql
```

### 步驟 2: 後端部署

```bash
# 1. 確認測試通過
python3 scripts/test_notification_scheduling.py

# 2. 提交程式碼
git add backend/
git commit -m "feat: add notification day fields support"

# 3. 部署到測試環境
# (根據你的部署流程)

# 4. 驗證測試環境
curl https://test-api.yourdomain.com/api/notifications/preferences

# 5. 部署到正式環境
# (根據你的部署流程)
```

### 步驟 3: 前端部署

```bash
# 1. 確認建置成功
cd frontend
npm run type-check
npm run lint
npm run build

# 2. 提交程式碼
git add frontend/
git commit -m "feat: add day selectors for weekly and monthly notifications"

# 3. 部署到測試環境
# (根據你的部署流程)

# 4. 驗證測試環境
# 開啟 https://test.yourdomain.com/settings/notifications
# 測試星期和日期選擇器

# 5. 部署到正式環境
# (根據你的部署流程)
```

## 🧪 部署後驗證

### 1. 資料庫驗證

```bash
# 連線到資料庫
psql $DATABASE_URL

# 檢查欄位
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'user_notification_preferences'
AND column_name IN ('notification_day_of_week', 'notification_day_of_month');

# 預期結果：
# notification_day_of_week | integer | 5
# notification_day_of_month | integer | 1

# 檢查現有記錄
SELECT id, notification_day_of_week, notification_day_of_month
FROM user_notification_preferences
LIMIT 5;

# 預期：所有記錄都有值（5 和 1）
```

### 2. API 驗證

```bash
# 測試 GET 端點
curl -X GET https://api.yourdomain.com/api/notifications/preferences \
  -H "Authorization: Bearer YOUR_TOKEN"

# 預期回應包含：
# {
#   "notificationDayOfWeek": 5,
#   "notificationDayOfMonth": 1,
#   ...
# }

# 測試 PUT 端點（每週一）
curl -X PUT https://api.yourdomain.com/api/notifications/preferences \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "frequency": "weekly",
    "notificationDayOfWeek": 1,
    "notificationTime": "09:00"
  }'

# 預期：成功更新

# 測試 PUT 端點（每月 15 號）
curl -X PUT https://api.yourdomain.com/api/notifications/preferences \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "frequency": "monthly",
    "notificationDayOfMonth": 15,
    "notificationTime": "18:00"
  }'

# 預期：成功更新

# 測試預覽端點
curl -X GET "https://api.yourdomain.com/api/notifications/preferences/preview?frequency=weekly&notification_time=09:00&timezone=Asia/Taipei&notification_day_of_week=1" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 預期：返回下次通知時間（星期一 09:00）
```

### 3. 前端驗證

**手動測試清單**:

- [ ] 開啟通知設定頁面
- [ ] 選擇「每週」頻率
  - [ ] 確認顯示星期選擇器
  - [ ] 測試選擇不同星期
  - [ ] 確認預覽正確更新
- [ ] 選擇「每月」頻率
  - [ ] 確認顯示日期選擇器
  - [ ] 測試選擇不同日期
  - [ ] 確認預覽正確更新
- [ ] 選擇「每日」頻率
  - [ ] 確認不顯示星期/日期選擇器
- [ ] 選擇「停用」
  - [ ] 確認隱藏所有時間設定
- [ ] 測試儲存功能
  - [ ] 更改設定後自動儲存
  - [ ] 重新整理頁面，確認設定保留
- [ ] 測試預覽功能
  - [ ] 更改任何設定後預覽自動更新
  - [ ] 預覽顯示正確的日期和時間

### 4. 排程驗證

```bash
# 檢查排程器狀態
curl -X GET https://api.yourdomain.com/api/notifications/preferences/status \
  -H "Authorization: Bearer YOUR_TOKEN"

# 預期回應：
# {
#   "scheduled": true,
#   "nextRunTime": "2026-04-28T01:00:00Z",
#   "message": "Notification scheduled successfully"
# }

# 手動觸發重新排程
curl -X POST https://api.yourdomain.com/api/notifications/preferences/reschedule \
  -H "Authorization: Bearer YOUR_TOKEN"

# 預期：成功重新排程
```

### 5. 邊界情況驗證

```bash
# 測試 2 月 31 號
curl -X PUT https://api.yourdomain.com/api/notifications/preferences \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "frequency": "monthly",
    "notificationDayOfMonth": 31,
    "notificationTime": "18:00"
  }'

# 檢查預覽
curl -X GET "https://api.yourdomain.com/api/notifications/preferences/preview?frequency=monthly&notification_time=18:00&timezone=Asia/Taipei&notification_day_of_month=31" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 預期：如果當前是 1 月，下次通知應該在 1 月 31 號
#       如果當前是 2 月，下次通知應該在 2 月 28/29 號
```

## 🔍 監控指標

### 部署後 24 小時內監控

1. **錯誤率**
   - API 錯誤率應 < 1%
   - 前端錯誤率應 < 0.5%

2. **效能指標**
   - API 回應時間應 < 200ms
   - 前端載入時間應 < 2s

3. **使用者行為**
   - 監控有多少使用者更新設定
   - 監控選擇的頻率分佈
   - 監控選擇的星期/日期分佈

4. **排程狀態**
   - 確認所有使用者的通知都正確排程
   - 監控排程失敗率

## 🚨 回滾計畫

如果發現嚴重問題，按以下步驟回滾：

### 前端回滾

```bash
# 1. 回滾到上一個版本
git revert <commit-hash>
git push

# 2. 重新部署
# (根據你的部署流程)
```

**影響**: 使用者將看不到星期/日期選擇器，但不影響現有功能

### 後端回滾

```bash
# 1. 回滾程式碼
git revert <commit-hash>
git push

# 2. 重新部署
# (根據你的部署流程)
```

**影響**: API 將忽略新欄位，使用預設值（星期五、每月 1 號）

### 資料庫回滾（不建議）

```sql
-- 只有在必要時才執行
-- 注意：這會刪除使用者的自訂設定

ALTER TABLE user_notification_preferences
DROP COLUMN IF EXISTS notification_day_of_week;

ALTER TABLE user_notification_preferences
DROP COLUMN IF EXISTS notification_day_of_month;
```

**影響**: 所有使用者的星期/日期設定將遺失

## ✅ 部署完成確認

- [ ] 資料庫遷移成功
- [ ] 後端部署成功
- [ ] 前端部署成功
- [ ] API 驗證通過
- [ ] 前端驗證通過
- [ ] 排程驗證通過
- [ ] 邊界情況驗證通過
- [ ] 監控指標正常
- [ ] 使用者回饋正面
- [ ] 文件已更新

## 📞 支援資訊

### 問題回報

如果發現問題，請提供以下資訊：

1. **問題描述**
2. **重現步驟**
3. **預期行為**
4. **實際行為**
5. **截圖或錯誤訊息**
6. **瀏覽器/環境資訊**

### 聯絡方式

- GitHub Issues: [專案 Issues 頁面]
- Email: [支援信箱]
- Discord: [Discord 頻道]

## 📚 相關文件

- [完整實作總結](./docs/COMPLETE_IMPLEMENTATION_SUMMARY.md)
- [快速開始指南](./docs/QUICK_START.md)
- [前端更新報告](./docs/FRONTEND_UPDATE_COMPLETE.md)
- [後端完成報告](./docs/IMPLEMENTATION_COMPLETE.md)
- [遷移指南](./docs/MIGRATION_009_GUIDE.md)

---

**部署日期**: ****\_\_\_****
**部署人員**: ****\_\_\_****
**驗證人員**: ****\_\_\_****
**狀態**: ⬜ 待部署 / ⬜ 部署中 / ⬜ 已完成
