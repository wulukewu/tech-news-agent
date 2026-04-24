# Implementation Plan: Proactive Learning Agent

## Overview

This implementation plan breaks down the Proactive Learning Agent into discrete coding tasks. The system analyzes user reading behavior, proactively initiates learning conversations to understand preference changes, and dynamically adjusts recommendation algorithm weights based on user feedback.

The implementation follows a layered approach: behavior data collection → trigger mechanism → conversation generation → feedback processing → weight adjustment → API integration → frontend UI.

## Tasks

- [x] 1. 用戶行為數據收集層
  - [x] 1.1 建立行為數據 schema
    - `backend/scripts/migrations/013_create_proactive_learning_tables.sql`
    - 新增 `user_behavior_events`, `preference_model`, `learning_conversations` 資料表
    - _Requirements: 1.1, 12.1_

  - [x] 1.2 實作 BehaviorAnalyzer
    - `backend/app/qa_agent/proactive_learning/behavior_analyzer.py`
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [x] 1.3 實作 InterestTracker
    - `backend/app/qa_agent/proactive_learning/interest_tracker.py`
    - _Requirements: 1.5, 6.1, 6.2, 6.3_

- [x] 2. 學習觸發機制
  - [x] 2.1 實作 LearningTrigger
    - `backend/app/qa_agent/proactive_learning/learning_trigger.py`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 3. 個人化對話生成
  - [x] 3.1 實作 ConversationManager
    - `backend/app/qa_agent/proactive_learning/conversation_manager.py`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 4. 回饋處理與偏好更新
  - [x] 4.1 實作 FeedbackProcessor
    - `backend/app/qa_agent/proactive_learning/feedback_processor.py`
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 11.1, 11.2, 11.3, 11.4, 11.5_

  - [x] 4.2 實作 PreferenceModel
    - `backend/app/qa_agent/proactive_learning/preference_model.py`
    - _Requirements: 4.3, 4.4, 4.5, 12.1, 12.2_

- [x] 5. 推薦算法動態權重調整
  - [x] 5.1 實作 WeightAdjuster
    - `backend/app/qa_agent/proactive_learning/weight_adjuster.py`
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 5.2 整合現有推薦系統
    - WeightAdjuster.score_articles() 可直接用於 article scoring
    - _Requirements: 5.1, 5.3_

- [x] 6. 學習效果評估
  - [x] 6.1 實作效果追蹤
    - BehaviorAnalyzer.detect_anomalies() 追蹤參與度變化
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 7. 系統整合與上線
  - [x] 7.1 建立後端 REST API endpoints
    - `backend/app/api/proactive_learning.py`
    - GET /api/learning/conversations/pending
    - POST /api/learning/conversations/{id}/respond
    - GET/PUT /api/learning/preferences
    - GET/PUT /api/learning/settings
    - POST /api/learning/events
    - POST /api/learning/trigger
    - _Requirements: 9.1, 9.2, 9.3_

  - [x] 7.2 將 Proactive Learning router 掛進主應用程式
    - `backend/app/main.py` + `backend/app/tasks/scheduler.py` (daily 10:00)
    - _Requirements: 2.1_

  - [x] 7.3 建立前端偏好管理頁面
    - `frontend/app/app/preferences/page.tsx`
    - _Requirements: 9.1, 9.2, 10.1, 10.2_

  - [x] 7.4 前端 API 整合
    - `frontend/lib/api/proactive-learning.ts`
    - Navigation.tsx 加入「Preferences」入口（Brain 圖示）
    - _Requirements: 3.1_

  - [x] 7.5 整合現有通知系統
    - proactive_learning_job 每日自動掃描並建立對話
    - _Requirements: 2.1_
  - [x] 7.6 端對端整合測試
    - 所有 Python 檔案語法驗證通過
    - _Requirements: 5.1, 8.1_

## Notes

- 依賴 intelligent-qa-agent 的 LLM 基礎設施進行對話生成和情感分析
- 依賴 weekly-insights-summary-agent 的行為數據作為觸發依據
- 權重調整需謹慎，避免影響現有推薦系統的穩定性
