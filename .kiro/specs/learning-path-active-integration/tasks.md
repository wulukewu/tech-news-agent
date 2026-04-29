# Tasks: Learning Path Active Integration

## Tasks

- [x] 1. 閱讀行為自動同步進度
  - [x] 1.1 在 `supabase_service.py` 的 `update_article_rating` 加入 side effect
    - 新增 `_sync_learning_progress(user_id, article_id)` private method
    - 查詢用戶進行中的學習目標（status = 'active'）
    - 比對文章 category 與各學習階段的 skills（字串包含比對）
    - 相關時呼叫 learning_progress upsert 更新進度
    - 避免重複標記（先檢查 learning_progress 是否已有該 article_id）
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Proactive DM 混合學習路徑推薦
  - [x] 2.1 修改 `proactive_recommendation.py` 的 `_build_recommendations()`
    - 新增 `_get_learning_path_articles(supabase, user_id, new_articles)` helper
    - 有學習目標時：學習路徑文章 3 篇 + 一般偏好 2 篇
    - 無學習目標時：維持現有邏輯不變
    - 學習路徑文章的推薦原因加上「符合你的 [目標名稱] - [階段名稱] 階段」
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 3. 學習停滯偵測與提醒
  - [x] 3.1 新增 `backend/app/tasks/learning_stagnation.py`
    - `learning_stagnation_check_job()` — 主入口
    - 查詢所有 active 學習目標，取各目標最後一筆進度記錄時間
    - 超過 3 天無進度 且 本週提醒次數 < 2 → 觸發提醒
    - 提醒 DM 內容：目標名稱、當前進度 %、下一篇推薦文章連結
    - 記錄提醒發送時間（存入 learning_goals 表的 last_stagnation_reminder_at 欄位）
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 3.2 DB migration：在 `learning_goals` 表新增追蹤欄位
    - `backend/scripts/migrations/018_add_learning_stagnation_fields.sql`
    - 新增 `last_stagnation_reminder_at TIMESTAMPTZ`
    - 新增 `stagnation_reminder_count_this_week INTEGER DEFAULT 0`
    - _Requirements: 3.5_

  - [x] 3.3 在 `scheduler.py` 掛上 `learning_stagnation_check_job`
    - 每天 10:05 執行
    - _Requirements: 3.1_
