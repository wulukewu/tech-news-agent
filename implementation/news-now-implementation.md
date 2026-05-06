# News Now 功能實作文檔

## 📋 概述

本文檔說明 `/news_now` 指令的完整實作，包括文章抓取、AI 分析、資料庫儲存和 Discord 互動。

---

## 🔄 完整流程

### 執行流程圖

```
/news_now 指令
  ↓
┌─────────────────────────────────────────────────────────┐
│ 1. 抓取新文章（去重）                                    │
│    - 從 RSS 抓取最近 7 天的文章                          │
│    - 時間過濾：只保留 7 天內的文章                       │
│    - 資料庫去重：檢查 URL 是否已存在                     │
│    - 返回新文章列表                                      │
└─────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────┐
│ 2. AI 批次分析（並發處理）                               │
│    - 評估技術深度（tinkering_index 1-5）                │
│    - 生成繁體中文摘要（ai_summary）                      │
│    - 並發數：2，延遲：4 秒                               │
│    - 使用 asyncio.gather() 並發處理                     │
└─────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────┐
│ 3. 批次插入資料庫                                        │
│    - 等待所有文章處理完成                                │
│    - 使用 UPSERT 邏輯（避免重複）                        │
│    - 批次插入（每批最多 100 筆）                         │
└─────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────┐
│ 4. Discord 顯示結果                                      │
│    - 顯示統計資訊                                        │
│    - 按分類顯示文章列表                                  │
│    - 提供互動元件（篩選、Deep Dive）                    │
└─────────────────────────────────────────────────────────┘
```

---

## 🔍 詳細說明

### 1. 文章抓取與過濾

#### 時間過濾

**位置：** `app/services/rss_service.py` → `_process_single_feed()`

**邏輯：**

```python
cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)

for entry in feed.entries:
    published_date = self._parse_date(entry)

    # 過濾舊文章
    if published_date < cutoff_date:
        continue

    articles.append(ArticleSchema(...))
```

**效果：**

- 只保留最近 7 天的文章
- 可透過 `RSS_FETCH_DAYS` 環境變數配置

#### 資料庫去重

**位置：** `app/services/rss_service.py` → `fetch_new_articles()`

**邏輯：**

```python
for article in all_articles:
    exists = await supabase_service.check_article_exists(str(article.url))

    if not exists:
        new_articles.append(article)

return new_articles
```

**效果：**

- 避免重複處理已存在的文章
- 節省 API 配額和處理時間
- 使用 URL 作為唯一識別碼

#### Feed ID 映射

**位置：** `app/services/rss_service.py` → `fetch_new_articles()`

**邏輯：**

```python
# 從資料庫查詢 feed_id
response = supabase_service.client.table('feeds')\
    .select('id, url')\
    .eq('is_active', True)\
    .execute()

feed_id_map = {}
for feed in response.data:
    feed_id_map[feed['url']] = feed['id']
```

**效果：**

- 將 RSS URL 映射到資料庫的 feed_id
- 確保文章能正確關聯到訂閱源

---

### 2. AI 分析

#### 使用的模型

| 用途 | 模型                    | RPM 限制 | 特點         |
| ---- | ----------------------- | -------- | ------------ |
| 評估 | Llama 3.1 8B Instant    | 30       | 快速、輕量   |
| 摘要 | Llama 3.3 70B Versatile | 30       | 高品質、詳細 |

**注意：** 兩個模型共用同一個帳號的 30 RPM 限制。

#### 並發處理

**位置：** `app/services/llm_service.py` → `evaluate_batch()`

**邏輯：**

```python
semaphore = asyncio.Semaphore(2)  # 並發限制

async def process_article(article):
    async with semaphore:
        await asyncio.sleep(4)  # 速率控制

        # 評估 tinkering_index
        article.ai_analysis = await self.evaluate_article(article)

        # 生成摘要
        article.ai_summary = await self.generate_summary(article)

        return article

# 並發處理所有文章
evaluated = await asyncio.gather(*(process_article(a) for a in articles))
```

**配置：**

- 並發數：2
- 延遲：4 秒/請求
- 速率：30 RPM（符合 Groq 限制）

#### 錯誤處理

**邏輯：**

```python
try:
    article.ai_analysis = await self.evaluate_article(article)
except Exception as e:
    logger.error(f"Failed to evaluate: {e}")
    article.tinkering_index = None
    article.ai_analysis = None
```

**效果：**

- 個別文章失敗不影響其他文章
- 失敗的文章設為 NULL
- 記錄詳細錯誤日誌

---

### 3. 資料庫操作

#### 批次插入

**位置：** `app/services/supabase_service.py` → `insert_articles()`

**邏輯：**

```python
# 分批處理（每批 100 筆）
batch_size = 100
for i in range(0, len(articles), batch_size):
    batch = articles[i:i + batch_size]

    for article in batch:
        # 使用 UPSERT 邏輯
        self.client.table('articles').upsert(
            article_data,
            on_conflict='url'
        ).execute()
```

**UPSERT 邏輯：**

- 新 URL：插入新記錄
- 已存在 URL：更新現有記錄
- 避免重複插入

#### 統計資訊

**返回：**

```python
BatchResult(
    inserted_count=82,   # 新增數量
    updated_count=0,     # 更新數量
    failed_count=30      # 失敗數量
)
```

---

### 4. Discord 互動

#### 顯示格式

```
📰 **本週科技新聞精選**

📊 本週統計：
  • 總共抓取：112 篇文章
  • 精選推薦：112 篇
  • 新增資料庫：82 篇
  • 更新資料庫：0 篇

🔥 **推薦文章：**

**AI**
  🔥🔥🔥🔥 Article Title 1
    🔗 https://example.com/1
  🔥🔥🔥 Article Title 2
    🔗 https://example.com/2

**Backend**
  🔥🔥🔥🔥🔥 Article Title 3
    🔗 https://example.com/3
```

#### 互動元件

**FilterView（分類篩選）：**

- 下拉選單顯示所有分類
- 選擇分類後顯示該分類的文章
- 回應為 ephemeral（只有自己看得到）

**DeepDiveView（深度分析）：**

- 最多 5 個按鈕
- 點擊後生成詳細技術分析
- 使用 Llama 3.3 70B 生成

**ReadLaterView（稍後閱讀）：**

- 最多 10 個按鈕
- 功能尚未完全實作

---

## 📊 效能分析

### 處理時間

**50 篇新文章：**

```
抓取文章：~10 秒
AI 分析：50 × 2 ÷ 2 × 4 = 200 秒 = 3.3 分鐘
插入資料庫：~0.5 秒
顯示結果：~1 秒

總計：約 3.5 分鐘
```

**100 篇新文章：**

```
抓取文章：~15 秒
AI 分析：100 × 2 ÷ 2 × 4 = 400 秒 = 6.7 分鐘
插入資料庫：~1 秒
顯示結果：~1 秒

總計：約 7 分鐘
```

### API 使用量

**第一次執行（所有文章都是新的）：**

```
100 篇文章 × 2 API 調用 = 200 API 調用
時間：~7 分鐘
```

**第二次執行（只有 5 篇新文章）：**

```
5 篇文章 × 2 API 調用 = 10 API 調用
時間：~20 秒

節省：190 API 調用（95%）
節省：6.7 分鐘（96%）
```

### 記憶體使用

**單篇文章：**

```
title: ~100 bytes
url: ~100 bytes
feed_id: 36 bytes
ai_summary: ~500 bytes
embedding: ~3KB

總計：約 4KB/篇
```

**不同數量：**

```
50 篇：200KB
100 篇：400KB
500 篇：2MB
1000 篇：4MB
```

---

## 🐛 已知問題與修復

### 問題 1: Feed ID 映射缺失 ✅ 已修復

**問題：** RSS Service 使用臨時 UUID，無法正確插入資料庫。

**修復：** 從資料庫查詢真實的 feed_id 並建立映射。

### 問題 2: 文章未插入資料庫 ✅ 已修復

**問題：** 只顯示文章，沒有存入資料庫。

**修復：** 實作文章插入邏輯，使用 UPSERT 避免重複。

### 問題 3: 欄位名稱不一致 ✅ 已修復

**問題：** `interactions.py` 使用舊欄位名稱 `source_category`。

**修復：** 統一使用新欄位名稱 `category`。

### 問題 4: Rate Limit 觸發 ✅ 已修復

**問題：** 並發數過高，頻繁觸發 Groq API 的 rate limit。

**修復：** 降低並發數到 2，增加延遲到 4 秒。

### 問題 5: 重複處理文章 ✅ 已修復

**問題：** 每次執行都會重新處理所有文章。

**修復：** 實作資料庫去重，只處理新文章。

---

## 🎯 最佳實踐

### 測試建議

1. **第一次執行**
   - 會處理所有新文章
   - 預期時間：5-7 分鐘
   - 正常現象

2. **後續執行**
   - 只處理新文章
   - 預期時間：20 秒 - 2 分鐘
   - 取決於新文章數量

3. **測試間隔**
   - 建議間隔 15 分鐘以上
   - 避免觸發 rate limit
   - 給 API 配額時間恢復

### 生產環境建議

1. **使用背景排程器**
   - 每 6 小時執行一次
   - 自動處理新文章
   - 推播到 Discord

2. **監控 API 使用**
   - 追蹤每日 API 調用數
   - 設定告警閾值
   - 考慮升級方案

3. **錯誤處理**
   - 記錄失敗的文章
   - 實作重試機制
   - 定期檢查日誌

---

## 🔗 相關文件

- [Rate Limit 指南](./RATE_LIMIT_GUIDE.md)
- [測試文件](./testing/)
- [資料庫 Schema](../scripts/init_supabase.sql)
- [API 文件](../README.md)

---

## 📝 更新日誌

### 2026-04-04

- ✅ 實作 feed_id 映射機制
- ✅ 實作文章批次插入
- ✅ 修復欄位名稱不一致
- ✅ 實作資料庫去重
- ✅ 優化 rate limit 處理
- ✅ 降低並發數和增加延遲

### 未來改進

- [ ] 實作 Read Later 功能
- [ ] 實作進度顯示
- [ ] 實作分批處理和插入
- [ ] 實作失敗文章重試
- [ ] 完成 Phase 3 背景排程器
