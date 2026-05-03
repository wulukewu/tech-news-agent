# 通知格式對比

## 📊 改進前後對比

### ❌ 改進前的格式

```
📰 本週技術文章精選
為你精選了 20 篇技術文章

📂 AI 應用
⭐⭐⭐ [Elephant-alpha is Chinese? Don't make me laugh...](url)
⭐⭐⭐⭐ [Q8 Cache We benchmarked TranslateGemma-12b against 5 frontier LLMs on subtitle translatio...](url)
⭐⭐⭐⭐⭐ [1000 token/s, it's blazing fast!!! Fairl](url)

📂 自架服務
⭐⭐⭐ [If it works - don't touch it: COMPETITION](url)
⭐⭐⭐ [自架服務About Karakeep, cookie banner and Youtube videos](url)

💡 使用 /news_now 查看完整列表 | 使用 /notifications 管理通知設定
```

**問題**：

- ❌ 標題被截斷（80 字元限制）
- ❌ 只有連結，沒有摘要
- ❌ 不知道文章何時發布
- ❌ 不知道文章內容是什麼
- ❌ 需要點開才能了解
- ❌ 每次都會重複發送相同文章

---

### ✅ 改進後的格式

```
📰 本週技術文章精選
為你精選了 5 篇新技術文章

📂 AI 應用 (2 篇)

⭐⭐⭐⭐ Elephant-alpha is Chinese? Don't make me laugh
🔗 https://example.com/article1
📝 深入探討 Elephant-alpha 模型在中文處理上的實際表現，與其他主流模型進行對比測試...
🗓️ 2 天前

⭐⭐⭐⭐⭐ Q8 Cache: 1000 token/s Benchmark Results
🔗 https://example.com/article2
📝 TranslateGemma-12b 的性能測試結果驚人，在字幕翻譯任務上超越了 5 個前沿 LLM 模型...
🗓️ 1 天前

📂 自架服務 (3 篇)

⭐⭐⭐ If it works - don't touch it: COMPETITION
🔗 https://example.com/article3
📝 探討軟體開發中的「不要動能用的東西」原則，以及何時應該打破這個規則...
🗓️ 3 天前

⭐⭐⭐ Karakeep: Cookie Banner and Youtube Videos
🔗 https://example.com/article4
📝 介紹 Karakeep 如何處理 cookie 橫幅和 Youtube 影片嵌入的最佳實踐...
🗓️ 5 小時前

⭐⭐⭐⭐ Erugo Connection Help and Setup Guide
🔗 https://example.com/article5
📝 完整的 Erugo 連接設定指南，包含常見問題排解和最佳配置建議...
🗓️ 12 小時前

💡 使用 /news_now 查看完整列表 | 使用 /notifications 管理通知設定
```

**改進**：

- ✅ 完整標題（不截斷）
- ✅ 文章摘要（前 100 字）
- ✅ 發布時間（相對時間）
- ✅ 分類顯示文章數量
- ✅ 清晰的視覺層次
- ✅ 不用點開就能了解內容
- ✅ 只發送新文章，不重複

---

## 🎯 核心改進點

### 1. 完整標題

**之前**：

```
⭐⭐⭐⭐ [Q8 Cache We benchmarked TranslateGemma-12b against 5 frontier LLMs on subtitle translatio...](url)
```

**現在**：

```
⭐⭐⭐⭐ Q8 Cache: 1000 token/s Benchmark Results
🔗 https://example.com/article2
```

### 2. 文章摘要

**之前**：無摘要

**現在**：

```
📝 TranslateGemma-12b 的性能測試結果驚人，在字幕翻譯任務上超越了 5 個前沿 LLM 模型...
```

### 3. 發布時間

**之前**：無時間資訊

**現在**：

```
🗓️ 1 天前
🗓️ 5 小時前
🗓️ 12 分鐘前
```

### 4. 分類資訊

**之前**：

```
📂 AI 應用
```

**現在**：

```
📂 AI 應用 (2 篇)
```

### 5. 視覺層次

**之前**：所有資訊擠在一行

**現在**：

- 第一行：星星評分 + 標題
- 第二行：連結
- 第三行：摘要
- 第四行：時間
- 空行分隔

---

## 📱 實際效果預覽

### 使用者體驗改進

#### 改進前的使用者流程：

1. 收到通知
2. 看到標題被截斷
3. 不知道文章內容
4. 必須點開連結
5. 發現是已經看過的文章 😞

#### 改進後的使用者流程：

1. 收到通知
2. 看到完整標題
3. 閱讀摘要了解內容
4. 看到發布時間判斷新舊
5. 決定是否點開
6. 都是新文章，沒有重複 😊

---

## 🔧 技術實現

### 重複檢測機制

```python
# 查詢已發送的文章
sent_articles = db.query("dm_sent_articles")
    .filter(user_id=user_id)
    .select("article_id")

# 排除已發送的文章
articles = db.query("articles")
    .filter(feed_id IN user_feeds)
    .filter(published_at >= cutoff_date)
    .filter(id NOT IN sent_articles)  # 關鍵：排除已發送
    .order_by(tinkering_index DESC)
    .limit(20)
```

### 時間範圍調整

```python
# 根據頻率調整時間範圍
if frequency == "daily":
    days = 1  # 只查詢最近 24 小時
elif frequency == "weekly":
    days = 7  # 查詢最近 7 天
elif frequency == "monthly":
    days = 30  # 查詢最近 30 天
```

### 格式化邏輯

```python
# 完整標題（不截斷）
title = article.title

# 摘要（前 100 字）
summary = article.ai_summary[:100] + "..." if len(article.ai_summary) > 100 else article.ai_summary

# 相對時間
delta = now - article.published_at
if delta.days > 0:
    time_ago = f"🗓️ {delta.days} 天前"
elif delta.seconds >= 3600:
    hours = delta.seconds // 3600
    time_ago = f"🗓️ {hours} 小時前"
else:
    minutes = delta.seconds // 60
    time_ago = f"🗓️ {minutes} 分鐘前"
```

---

## 📊 預期效果

### 重複率降低

- **改進前**：每次通知可能有 80-90% 重複
- **改進後**：0% 重複（完全避免）

### 點擊率提升

- **改進前**：使用者不知道內容，點擊率低
- **改進後**：有摘要和時間，使用者可以判斷是否感興趣

### 使用者滿意度

- **改進前**：「只有連結，還會重複」
- **改進後**：「有摘要，不重複，很清楚」

---

## 🚀 下一步

執行以下步驟來啟用改進：

1. **執行資料庫遷移**

   ```bash
   # 在 Supabase SQL Editor 中執行
   scripts/migrations/011_create_dm_sent_articles_table.sql
   ```

2. **重啟後端服務**

   ```bash
   docker-compose restart backend
   ```

3. **測試通知**
   - 設定一個測試時間
   - 等待通知發送
   - 檢查格式是否改進
   - 再次發送確認無重複

---

**文件創建時間**: 2026-04-21
