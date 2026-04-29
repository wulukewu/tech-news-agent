# Design: Learning Path Active Integration

## Architecture

三個改動點，全部是串接現有系統，不新增獨立服務：

```
[改動 1] 評分事件 → 自動同步進度
update_article_rating() (supabase_service.py)
    → 新增: _sync_learning_progress(user_id, article_id, rating)
    → 查詢用戶進行中的學習目標
    → 比對文章 category vs 學習階段 skills
    → 呼叫 ArticleRecommender.mark_article_completed()

[改動 2] Proactive DM → 優先推學習路徑文章
proactive_recommendation_job() (proactive_recommendation.py)
    → 新增: _get_learning_path_articles(user_id, n)
    → 從 ArticleRecommender.get_next_recommendations() 取文章
    → 混入一般推薦（6:4 比例）

[改動 3] 每日排程 → 停滯偵測
scheduler.py 新增每日任務
    → learning_stagnation_check_job()
    → 查詢所有 active 學習目標，找出 > 3 天無進度的
    → 發送 Discord DM 提醒（含下一篇推薦）
```

## Key Implementation Details

### 改動 1：評分觸發點

`supabase_service.update_article_rating()` 已有評分更新邏輯，在其中加入 side effect：

```python
# 在 update_article_rating 成功後
if rating >= 3:
    await self._sync_learning_progress(discord_id, article_id)
```

相關度判斷用簡單的 category 比對（不用 LLM）：
- 取文章的 `category` 欄位
- 取學習階段的 `skills` 列表
- 如果 category 包含在任一 skill 關鍵字中 → 視為相關

### 改動 2：Proactive DM 混合推薦

在 `proactive_recommendation.py` 的 `_build_recommendations()` 中：

```python
# 現有邏輯：純偏好推薦
# 新邏輯：
learning_articles = await _get_learning_path_articles(user_id, n=3)
preference_articles = existing_logic(n=2)
combined = learning_articles + preference_articles  # 最多 5 篇
```

### 改動 3：停滯偵測 Job

新增 `backend/app/tasks/learning_stagnation.py`：

```python
async def learning_stagnation_check_job():
    # 查詢所有 active 學習目標
    # 對每個目標：取最後一筆 learning_progress 記錄的時間
    # 如果 now - last_progress > 3 天 且 本週提醒次數 < 2
    # → 發 DM（用現有 proactive_dm.py 的 send_proactive_dm 格式）
```

掛在 scheduler 每天 10:00 執行（與 proactive_recommendation_job 同時段）。

## Files to Modify / Create

| 檔案 | 動作 | 說明 |
|------|------|------|
| `backend/app/services/supabase_service.py` | 修改 | `update_article_rating` 加入 `_sync_learning_progress` |
| `backend/app/tasks/proactive_recommendation.py` | 修改 | `_build_recommendations` 加入學習路徑文章混合 |
| `backend/app/tasks/learning_stagnation.py` | 新增 | 停滯偵測 job |
| `backend/app/tasks/scheduler.py` | 修改 | 掛上 `learning_stagnation_check_job` |
