# Implementation Tasks: Proactive Recommendation Loop

## Overview

串接現有基礎設施，補上「主動觸發 → DM 送出 → 即時回饋」的閉環。

## Tasks

- [x] 1. 資料庫變更
  - [x] 1.1 新增 migration SQL
    - `backend/scripts/migrations/016_add_proactive_dm_fields.sql`
    - 在 `users` 表新增 `last_proactive_dm_at TIMESTAMPTZ` 和 `proactive_dm_frequency_hours INTEGER DEFAULT 20`
    - _Requirements: 4.2, 4.3_

- [x] 2. 推薦原因生成服務
  - [x] 2.1 實作 `RecommendationReasonService`
    - `backend/app/services/recommendation_reason.py`
    - rule-based 邏輯：找用戶評過 4+ 星的同分類文章 → 生成原因句
    - fallback：無評分歷史時回傳預設說明
    - _Requirements: 2.1, 2.2, 2.3_

- [x] 3. Discord DM 元件
  - [x] 3.1 實作 `FeedbackView` (discord.ui.View)
    - `backend/app/bot/cogs/proactive_dm.py`
    - 👍 / 👎 按鈕，點擊後呼叫 PreferenceModel 更新權重
    - 點擊後 disable 按鈕並回覆確認訊息
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  - [x] 3.2 實作 `send_proactive_dm()`
    - 組裝每篇文章的 embed（標題、推薦原因、連結、FeedbackView）
    - 最多 5 篇
    - _Requirements: 2.4, 1.4_

- [x] 4. 核心 Job
  - [x] 4.1 實作 `proactive_recommendation_job()`
    - `backend/app/tasks/proactive_recommendation.py`
    - 取得所有啟用 DM 通知的用戶
    - 對每個用戶：檢查冷卻時間 → 評分新文章 → 取 top N → 生成原因 → 發 DM → 更新 `last_proactive_dm_at`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 4.1, 4.2, 4.3_

- [x] 5. Scheduler 整合
  - [x] 5.1 在 RSS fetch job 完成後呼叫 `proactive_recommendation_job()`
    - `backend/app/tasks/scheduler.py`
    - _Requirements: 1.1_

- [x] 6. 前端設定頁面
  - [x] 6.1 在設定頁面新增推薦頻率選項
    - `frontend/features/notifications/components/ProactiveFrequencySettings.tsx`
    - `frontend/lib/api/notifications.ts` (新增 API 函數)
    - `backend/app/api/notifications.py` (新增 PATCH/GET /proactive-frequency)
    - 選項：每天 / 每兩天 / 每週
    - _Requirements: 4.4_
