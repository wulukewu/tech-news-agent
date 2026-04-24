# Implementation Plan: Learning Path Planning Agent

## Overview

This implementation plan breaks down the Learning Path Planning Agent into discrete coding tasks. The system allows users to set learning goals, automatically generates structured multi-stage learning paths, recommends relevant articles for each stage, and tracks learning progress with dynamic plan adjustment.

The implementation follows a layered approach: skill tree modeling → goal parsing → path generation → article recommendation → progress tracking → dynamic adjustment → API integration → frontend UI.

## Tasks

- [ ] 1. 資料層與技能樹建模
  - [ ] 1.1 建立資料庫 schema
    - 新增 `learning_goals` 資料表（用戶學習目標）
    - 新增 `learning_paths` 資料表（生成的學習路徑）
    - 新增 `learning_stages` 資料表（路徑中的各階段）
    - 新增 `learning_progress` 資料表（用戶進度記錄）
    - 新增 `skill_tree` 資料表（技能依賴關係）
    - _Requirements: 10.1, 10.2_

  - [ ] 1.2 實作 SkillTree 模型
    - 建立 `backend/app/qa_agent/learning_path/skill_tree.py`
    - 定義技能節點和前置依賴關係
    - 支援多層級技能結構（基礎→中級→高級）
    - 包含技能難度評級和預估學習時間
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 2. 學習目標解析
  - [ ] 2.1 實作目標解析器
    - 建立 `backend/app/qa_agent/learning_path/goal_parser.py`
    - 使用 LLM 解析自然語言學習目標（如「我想學習 Kubernetes」）
    - 驗證目標有效性，對模糊目標要求澄清
    - 估算學習時間
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 3. 學習路徑生成
  - [ ] 3.1 實作 LearningPathGenerator
    - 建立 `backend/app/qa_agent/learning_path/path_generator.py`
    - 基於 SkillTree 生成包含基礎、進階、實戰三階段的學習路徑
    - 建立階段間依賴關係，確保學習順序邏輯性
    - 為每個階段設定預估完成時間
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 4. 智能文章推薦
  - [ ] 4.1 實作 ArticleRecommender
    - 建立 `backend/app/qa_agent/learning_path/article_recommender.py`
    - 根據當前學習階段推薦相關文章
    - 按學習順序排序，考慮文章難度與用戶水平匹配度
    - 避免推薦重複或已讀文章
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 5. 學習進度追蹤
  - [ ] 5.1 實作 ProgressTracker
    - 建立 `backend/app/qa_agent/learning_path/progress_tracker.py`
    - 記錄文章閱讀狀態（已讀、未讀、進行中）
    - 計算各階段完成百分比
    - 追蹤學習時間和頻率
    - 識別學習瓶頸和停滯點
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 6. 動態計劃調整
  - [ ] 6.1 實作 DynamicAdjuster
    - 建立 `backend/app/qa_agent/learning_path/dynamic_adjuster.py`
    - 進度超前時提前推薦進階內容
    - 進度落後時調整時程
    - 遇到困難時增加基礎內容推薦
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 7. 學習成效評估
  - [ ] 7.1 實作成效評估模組
    - 計算學習效率指標（實際 vs 預估時間）
    - 識別學習強項和弱項
    - 生成階段性成效報告
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 8. 系統整合與上線
  - [ ] 8.1 建立後端 REST API endpoints
    - 在 `backend/app/api/learning_path.py` 建立 FastAPI router
    - 實作 `POST /api/learning-path/goals` — 設定學習目標
    - 實作 `GET /api/learning-path/goals` — 取得所有學習目標
    - 實作 `GET /api/learning-path/goals/{id}` — 取得特定目標的學習路徑
    - 實作 `GET /api/learning-path/goals/{id}/progress` — 取得學習進度
    - 實作 `POST /api/learning-path/goals/{id}/articles/{article_id}/complete` — 標記文章完成
    - 實作 `GET /api/learning-path/goals/{id}/recommendations` — 取得當前推薦文章
    - 實作 `PUT /api/learning-path/goals/{id}/adjust` — 手動調整計劃
    - 加入 JWT 認證和 rate limiting
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [ ] 8.2 將 Learning Path router 掛進主應用程式
    - 在 `backend/app/main.py` import 並 `include_router`
    - _Requirements: 6.1_

  - [ ] 8.3 建立前端學習路徑頁面
    - 在 `frontend/app/learning/page.tsx` 建立學習路徑主頁
    - 顯示所有學習目標和整體進度
    - 在 `frontend/app/learning/[id]/page.tsx` 建立單一路徑詳情頁
    - 顯示三階段學習路徑（基礎/進階/實戰）和各階段文章列表
    - 顯示進度條和完成百分比
    - 顯示當前推薦文章
    - _Requirements: 2.5, 4.2, 6.5_

  - [ ] 8.4 前端 API 整合
    - 在 `frontend/lib/api/learning-path.ts` 建立 API client
    - 加入導航連結（navbar 加入「學習路徑」入口）
    - _Requirements: 6.1_

  - [ ] 8.5 端對端整合測試
    - 測試設定目標 → 生成路徑 → 標記完成 → 進度更新完整流程
    - 測試動態調整機制
    - _Requirements: 2.1, 4.1, 5.1_

## Notes

- 依賴 intelligent-qa-agent 的 LLM 基礎設施進行目標解析和路徑生成
- 依賴 proactive-learning-agent 的用戶偏好數據優化文章推薦
- SkillTree 初始資料需要預先建立常見技術領域的依賴關係
