# Design Document: Proactive Recommendation Loop

## Overview

本功能在現有基礎設施上加一層「主動觸發 + DM 送出 + 即時回饋」的閉環。不需要新的 AI 模型，主要是串接已有的元件。

## Architecture

```
RSS Fetch 完成
      ↓
proactive_recommendation_job()   ← 新增，掛在 scheduler
      ↓
對每個啟用 DM 通知的用戶：
  1. 檢查距上次 Proactive_DM 是否超過冷卻時間
  2. 用 PreferenceModel 對新文章評分 → 取 top 3-5
  3. 為每篇文章生成推薦原因（LLM 或 rule-based）
  4. 發送 Discord DM（含 Inline Feedback 按鈕）
      ↓
用戶點擊按鈕
      ↓
Discord interaction handler → PreferenceModel.update_weight()
```

## Components

### 1. `backend/app/tasks/proactive_recommendation.py` (新增)

核心 job，負責整個流程的協調：

```python
async def proactive_recommendation_job():
    # 1. 取得所有啟用 DM 通知的用戶
    # 2. 對每個用戶執行 run_for_user()

async def run_for_user(user_id, discord_id):
    # 1. 檢查冷卻時間（查 last_proactive_dm_at）
    # 2. 取得用戶最近評分歷史
    # 3. 用 WeightAdjuster.score_articles() 對新文章評分
    # 4. 取 top N 篇
    # 5. 生成推薦原因
    # 6. 發送 DM
    # 7. 更新 last_proactive_dm_at
```

### 2. `backend/app/services/recommendation_reason.py` (新增)

生成推薦原因的邏輯，優先用 rule-based（快、省 token），LLM 作為 fallback：

```python
def generate_reason(article, user_rating_history) -> str:
    # Rule-based: 找用戶評過 4+ 星的同分類文章
    # 如果找到 → "你之前給 {category} 相關文章高分，這篇主題相似"
    # 如果沒有評分歷史 → "這篇技術深度較高，符合本平台精選標準"
```

### 3. `backend/app/bot/cogs/proactive_dm.py` (新增)

Discord DM 的格式化和 Inline Feedback 的 interaction handler：

```python
async def send_proactive_dm(discord_id, articles_with_reasons):
    # 組裝 embed + View（含 👍👎 按鈕）
    # 每篇文章一個 embed，最多 5 篇

class FeedbackView(discord.ui.View):
    # 👍 按鈕 → call PreferenceModel.adjust_weight(category, +delta)
    # 👎 按鈕 → call PreferenceModel.adjust_weight(category, -delta)
    # 點擊後 disable 按鈕，回覆確認訊息
```

### 4. 資料庫變更

在 `users` 表新增兩個欄位：

```sql
ALTER TABLE users ADD COLUMN last_proactive_dm_at TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN proactive_dm_frequency_hours INTEGER DEFAULT 20;
```

### 5. Scheduler 整合

在 `backend/app/tasks/scheduler.py` 的 RSS fetch job 完成後，呼叫 `proactive_recommendation_job()`：

```python
# 現有 fetch job 結束後
await proactive_recommendation_job()
```

## Data Flow

```
新文章 (articles table)
    ↓
WeightAdjuster.score_articles(user_id, articles)
    ↓ 使用 preference_model table 的權重
top N articles
    ↓
generate_reason(article, rating_history)
    ↓
Discord DM with FeedbackView
    ↓ 用戶點擊
PreferenceModel.adjust_weight() → 更新 preference_model table
```

## Design Decisions

**為什麼用 rule-based 生成推薦原因，而不是 LLM？**
每次 fetch 可能有多個用戶，LLM 呼叫成本會累積。Rule-based 在大多數情況下已經夠用（「你喜歡 Kubernetes，這篇也是 Kubernetes」），LLM 只在規則無法覆蓋時才用。

**為什麼最多 5 篇？**
Discord embed 有數量限制，超過 5 篇用戶也不會看完，反而造成通知疲勞。

**冷卻時間為什麼是 20 小時而不是 24 小時？**
允許每天的發送時間有 4 小時的漂移，避免因 scheduler 執行時間不固定導致某天完全沒收到。
