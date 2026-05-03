# 通知改進計劃

## 🎯 目標

讓排程通知更人性化、更有價值，避免重複發送，提供更清晰的資訊。

## 📋 當前問題

### 1. 格式問題

- ❌ 只顯示標題和連結
- ❌ 沒有摘要或描述
- ❌ 標題被截斷（80 字元）
- ❌ 只有星星評分，不清楚代表什麼

### 2. 重複發送問題

- ❌ 每次都發送最近 7 天的文章
- ❌ 沒有追蹤已發送的文章
- ❌ 每天發送會有大量重複

### 3. 內容問題

- ❌ 沒有文章摘要
- ❌ 沒有發布時間
- ❌ 沒有閱讀時間估計
- ❌ 分類不夠清晰

## 💡 改進方案

### 方案 1: 追蹤已發送文章（推薦）

**目標**: 只發送新文章，避免重複

**實現**:

1. 創建 `dm_sent_articles` 表（已在日誌中看到缺失）
2. 記錄每次發送的文章 ID
3. 查詢時排除已發送的文章

**優點**:

- ✅ 完全避免重複
- ✅ 用戶只收到新內容
- ✅ 適合每日通知

**缺點**:

- ⚠️ 需要額外的資料庫表
- ⚠️ 需要清理舊記錄

### 方案 2: 基於時間範圍（簡單）

**目標**: 根據通知頻率調整時間範圍

**實現**:

- Daily: 只發送最近 24 小時的文章
- Weekly: 只發送最近 7 天的文章
- Monthly: 只發送最近 30 天的文章

**優點**:

- ✅ 實現簡單
- ✅ 不需要額外表格
- ✅ 自動適應頻率

**缺點**:

- ⚠️ 可能還是會有重複（如果文章在時間範圍內）
- ⚠️ 如果某天沒有新文章，通知會是空的

### 方案 3: 混合方案（最佳）

**結合方案 1 和 2**:

1. 根據頻率設定時間範圍
2. 同時追蹤已發送文章
3. 查詢時同時過濾時間和已發送狀態

## 🎨 格式改進

### 當前格式

```
📰 本週技術文章精選
為你精選了 20 篇技術文章

📂 AI 應用
⭐⭐⭐ [Elephant-alpha is Chinese? Don't make me laugh...](url)
⭐⭐⭐⭐ [Q8 Cache We benchmarked TranslateGemma-12b...](url)
```

### 改進後格式

```
📰 本週技術文章精選
為你精選了 5 篇新文章（自上次通知後）

📂 AI 應用 (2 篇)

⭐⭐⭐⭐ Elephant-alpha is Chinese? Don't make me laugh
🔗 https://example.com/article1
📝 深入探討 Elephant-alpha 模型的實際表現...
⏱️ 5 分鐘閱讀 | 🗓️ 2 天前

⭐⭐⭐⭐⭐ Q8 Cache: 1000 token/s Benchmark
🔗 https://example.com/article2
📝 TranslateGemma-12b 的性能測試結果驚人...
⏱️ 8 分鐘閱讀 | 🗓️ 1 天前

📂 自架服務 (3 篇)
...

💡 提示
• 使用 /news_now 查看完整列表
• 使用 /notifications 管理通知設定
• 已為你過濾 15 篇已讀文章
```

### 改進點

1. ✅ 顯示「新文章」數量
2. ✅ 完整標題（不截斷）
3. ✅ 文章摘要（前 50 字）
4. ✅ 閱讀時間估計
5. ✅ 發布時間（相對時間）
6. ✅ 顯示過濾了多少已讀文章
7. ✅ 每個分類顯示文章數量

## 🗄️ 資料庫設計

### dm_sent_articles 表

```sql
CREATE TABLE IF NOT EXISTS dm_sent_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    notification_type TEXT NOT NULL, -- 'daily', 'weekly', 'monthly'

    -- 防止重複記錄
    UNIQUE(user_id, article_id),

    -- 索引
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_dm_sent_articles_user_sent
    ON dm_sent_articles(user_id, sent_at DESC);

CREATE INDEX IF NOT EXISTS idx_dm_sent_articles_article
    ON dm_sent_articles(article_id);

-- 自動清理 90 天前的記錄（可選）
CREATE INDEX IF NOT EXISTS idx_dm_sent_articles_cleanup
    ON dm_sent_articles(sent_at)
    WHERE sent_at < now() - interval '90 days';
```

## 📝 實現步驟

### Phase 1: 資料庫準備

1. 創建 `dm_sent_articles` 表
2. 添加清理舊記錄的功能

### Phase 2: 查詢邏輯改進

1. 修改 `get_user_articles` 查詢
2. 根據頻率調整時間範圍
3. 排除已發送的文章

### Phase 3: 格式改進

1. 修改 `_create_digest_embed` 函數
2. 添加文章摘要
3. 添加閱讀時間和發布時間
4. 改進分類顯示

### Phase 4: 記錄已發送

1. 發送成功後記錄到 `dm_sent_articles`
2. 批量插入提高效率

## 🎯 優先級

### 高優先級（立即實現）

1. ✅ 創建 `dm_sent_articles` 表
2. ✅ 根據頻率調整時間範圍
3. ✅ 排除已發送文章

### 中優先級（本週實現）

4. ✅ 添加文章摘要
5. ✅ 添加發布時間
6. ✅ 改進分類顯示

### 低優先級（未來優化）

7. ⏳ 添加閱讀時間估計
8. ⏳ 添加文章標籤
9. ⏳ 個性化推薦排序

## 💬 用戶反饋

當前用戶反饋：

> "只有連結的話變成是使用者還要自己點開來看，然後也會重複"

改進後預期：

- ✅ 有摘要，不用點開就能了解內容
- ✅ 不會重複，只收到新文章
- ✅ 格式清晰，易於閱讀

## 🚀 下一步

你想先實現哪個部分？

1. **快速修復**（30 分鐘）
   - 創建 `dm_sent_articles` 表
   - 根據頻率調整時間範圍
   - 排除已發送文章

2. **格式改進**（1 小時）
   - 添加文章摘要
   - 改進 embed 格式
   - 添加更多資訊

3. **完整實現**（2 小時）
   - 所有改進一次完成
   - 包含測試和驗證

建議從「快速修復」開始，這樣明天的通知就不會重複了！
