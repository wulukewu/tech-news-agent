# 🧪 DM 對話記憶系統 - 測試指南

## ✅ 測試清單

### 測試 1: 驗證資料庫 Schema (2 分鐘)

**在 Supabase Dashboard 執行:**

```sql
-- 1. 檢查 dm_conversations 表格
SELECT COUNT(*) FROM dm_conversations;
-- 預期: 返回 0 (空表格)

-- 2. 檢查 preference_model 欄位
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'preference_model'
  AND column_name IN ('preference_summary', 'summary_updated_at');
-- 預期: 返回 2 行

-- 3. 檢查索引
SELECT indexname
FROM pg_indexes
WHERE tablename = 'dm_conversations';
-- 預期: 至少有 idx_dm_conversations_user_created
```

**✓ 通過條件**: 所有查詢都成功執行

---

### 測試 2: Discord DM 測試 (5 分鐘)

#### 步驟 1: 發送測試 DM

在 Discord 發送 DM 給你的 bot:

```
我喜歡 Rust 和系統程式設計
```

**預期回應**:
```
✅ 已記錄你的偏好！偏好摘要將自動更新 🎯

💡 你可以：
• 直接問我問題，例如「最近有什麼 Rust 文章？」
• 告訴我偏好，例如「我喜歡系統設計，不喜歡入門教學」
• /update_profile 更新偏好摘要
• /recommend_now 立即獲取個人化推薦
• /my_profile 查看你的偏好檔案
```

#### 步驟 2: 發送更多 DM

```
想看更多關於記憶體管理和效能優化的文章
```

```
不太喜歡入門教學，偏好深入的技術分析
```

**✓ 通過條件**: Bot 每次都回覆 "✅ 已記錄你的偏好！"

---

#### 步驟 3: 驗證資料庫儲存

**在 Supabase Dashboard 執行:**

```sql
-- 查看最近的 DM 對話
SELECT
  content,
  created_at
FROM dm_conversations
ORDER BY created_at DESC
LIMIT 5;
```

**預期結果**: 看到你剛才發送的 3 則訊息

**✓ 通過條件**: 所有 DM 都被正確儲存

---

### 測試 3: 生成偏好摘要 (2 分鐘)

#### 步驟 1: 執行 Discord 指令

在 Discord 執行:
```
/update_profile
```

**預期回應**:
```
✅ 偏好摘要已更新！

> 喜歡 Rust、系統程式設計、記憶體管理、效能優化等深入技術分析，
> 不喜歡入門教學。
```

**✓ 通過條件**: 看到生成的偏好摘要

---

#### 步驟 2: 驗證資料庫

**在 Supabase Dashboard 執行:**

```sql
-- 查看偏好摘要
SELECT
  preference_summary,
  summary_updated_at,
  LENGTH(preference_summary) as summary_length
FROM preference_model
WHERE preference_summary IS NOT NULL
ORDER BY summary_updated_at DESC
LIMIT 1;
```

**預期結果**:
- `preference_summary` 有內容（約 50-150 字）
- `summary_updated_at` 是剛才的時間
- `summary_length` > 0

**✓ 通過條件**: 摘要已儲存到資料庫

---

### 測試 4: 查看偏好檔案 (1 分鐘)

在 Discord 執行:
```
/my_profile
```

**預期回應**: 一個 Embed 訊息包含:
- 💬 偏好摘要（你的偏好描述）
- 📊 分類權重（如果有評分過文章）
- 摘要更新時間

**✓ 通過條件**: 看到完整的偏好檔案

---

### 測試 5: 推薦系統整合 (10 分鐘)

#### 方法 A: 等待自動推薦

如果你的系統有設定自動推薦（每 6-20 小時），等待下次推薦 DM。

#### 方法 B: 手動觸發

如果有 `/trigger_fetch` 指令，執行它來觸發新文章抓取和推薦。

**預期結果**:
推薦 DM 中的推薦原因應該提到你的偏好，例如:
```
📰 為你推薦 5 篇文章

1. Rust 記憶體管理深入解析
   🎯 根據你的偏好描述，這篇 Rust 文章符合你的興趣方向
   🔗 https://...
```

**✓ 通過條件**: 推薦原因提到 "根據你的偏好描述"

---

### 測試 6: 前端介面 (3 分鐘)

#### 步驟 1: 訪問偏好頁面

打開瀏覽器訪問:
```
http://localhost:3000/preferences
```
或你的部署網址

**預期顯示**:
- 偏好摘要（如果有）
- 分類權重視覺化（條狀圖）
- 學習設定開關
- 待回答的學習對話（如果有）

**✓ 通過條件**: 頁面正常顯示，沒有錯誤

---

#### 步驟 2: 編輯偏好摘要

1. 前往 `http://localhost:3000/settings/preferences`
2. 找到偏好摘要的 textarea
3. 編輯內容，例如加上 "也對 WebAssembly 感興趣"
4. 點擊儲存

**預期結果**:
- 顯示 "✓ 偏好已儲存" 或類似訊息
- 重新整理頁面，看到更新後的內容

**✓ 通過條件**: 編輯成功儲存

---

### 測試 7: 自動觸發機制 (可選)

這個測試需要等待時間，可以跳過。

#### 測試條件

發送 3 則新的 DM 訊息（不執行 /update_profile）:

```
我也對 WebAssembly 感興趣
```

```
想了解更多關於並發程式設計的內容
```

```
對分散式系統也很有興趣
```

**預期行為**:
- 系統會在背景自動觸發偏好摘要更新
- 不需要手動執行 /update_profile

**驗證方式**:
```sql
-- 檢查 summary_updated_at 是否在最近更新
SELECT
  summary_updated_at,
  NOW() - summary_updated_at as age
FROM preference_model
WHERE preference_summary IS NOT NULL
ORDER BY summary_updated_at DESC
LIMIT 1;
```

**✓ 通過條件**: `age` < 10 分鐘

---

### 測試 8: 排程器 (可選)

這個測試需要等到每天 11:00，可以跳過。

#### 驗證方式

**檢查 backend logs**:

```bash
# Docker
docker-compose logs -f backend | grep "preference_summary_job"

# PM2
pm2 logs backend | grep "preference_summary_job"
```

**預期 log** (每天 11:00):
```
INFO: Starting preference summary job...
INFO: Updated preference summary for user abc123...
INFO: Preference summary job complete: 5 summaries updated
```

**✓ 通過條件**: 每天 11:00 看到 log

---

## 📊 測試結果總結

### 必做測試 (1-6)

- [ ] 測試 1: 資料庫 Schema ✓
- [ ] 測試 2: Discord DM 儲存 ✓
- [ ] 測試 3: 生成偏好摘要 ✓
- [ ] 測試 4: 查看偏好檔案 ✓
- [ ] 測試 5: 推薦系統整合 ✓
- [ ] 測試 6: 前端介面 ✓

### 可選測試 (7-8)

- [ ] 測試 7: 自動觸發機制
- [ ] 測試 8: 排程器

---

## ✅ 成功標準

**系統正常運作的條件**:

1. ✅ 所有 DM 訊息都被儲存到資料庫
2. ✅ `/update_profile` 能生成偏好摘要
3. ✅ `/my_profile` 能顯示偏好檔案
4. ✅ 推薦原因提到用戶偏好
5. ✅ 前端頁面正常顯示和編輯

**如果以上 5 點都通過，系統就完全正常！** 🎉

---

## 🐛 常見問題

### Q1: Bot 沒有回應 DM

**檢查**:
```bash
# 1. 確認 ENABLE_DM_LISTENER=true
grep ENABLE_DM_LISTENER .env

# 2. 檢查 bot logs
docker-compose logs -f backend | grep "DM conversation listener"
```

**預期**: 看到 "DM conversation listener enabled"

---

### Q2: /update_profile 說 "沒有足夠的 DM 對話"

**原因**: 資料庫中沒有 DM 對話記錄

**解決**:
1. 發送 2-3 則 DM 給 bot
2. 檢查資料庫: `SELECT COUNT(*) FROM dm_conversations;`
3. 如果還是 0，檢查 bot logs 是否有錯誤

---

### Q3: 偏好摘要是空的

**檢查**:
```sql
SELECT * FROM dm_conversations WHERE user_id = 'YOUR_USER_ID';
```

如果是空的，DM 沒有被儲存。檢查:
1. Bot 是否正在運行
2. ENABLE_DM_LISTENER 是否為 true
3. Bot logs 是否有錯誤

---

### Q4: 推薦沒有提到偏好

**可能原因**:
1. 偏好摘要還沒生成（執行 /update_profile）
2. 文章標題/分類與偏好關鍵字不匹配
3. 這是正常的 fallback 行為

**驗證**:
```sql
SELECT preference_summary FROM preference_model WHERE user_id = 'YOUR_USER_ID';
```

如果有摘要但推薦沒用到，這是正常的（不是每篇文章都會匹配）

---

## 📝 測試記錄

**測試日期**: ___________
**測試人員**: ___________

| 測試項目 | 結果 | 備註 |
|---------|------|------|
| 1. 資料庫 Schema | ☐ 通過 ☐ 失敗 | |
| 2. Discord DM | ☐ 通過 ☐ 失敗 | |
| 3. 生成摘要 | ☐ 通過 ☐ 失敗 | |
| 4. 查看檔案 | ☐ 通過 ☐ 失敗 | |
| 5. 推薦整合 | ☐ 通過 ☐ 失敗 | |
| 6. 前端介面 | ☐ 通過 ☐ 失敗 | |

**總體評價**: ☐ 完全正常 ☐ 基本可用 ☐ 需要修復

---

**預估測試時間**: 15-20 分鐘
**難度**: 簡單
**需要工具**: Discord, 瀏覽器, Supabase Dashboard

🎉 祝測試順利！
