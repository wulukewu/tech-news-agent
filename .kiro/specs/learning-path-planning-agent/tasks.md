# Implementation Plan: Learning Path Planning Agent

## Overview

This implementation plan breaks down the Learning Path Planning Agent into discrete coding tasks. The system allows users to set learning goals, automatically generates structured multi-stage learning paths, recommends relevant articles for each stage, and tracks learning progress with dynamic plan adjustment.

The implementation follows a layered approach: skill tree modeling → goal parsing → path generation → article recommendation → progress tracking → dynamic adjustment → API integration → frontend UI.

## Tasks

- [x] 1. 資料層與技能樹建模
  - [x] 1.1 建立資料庫 schema
    - `backend/scripts/migrations/017_create_learning_path_tables.sql`
    - 新增 `learning_goals`, `learning_paths`, `learning_stages`, `learning_progress`, `skill_tree` 資料表
    - _Requirements: 10.1, 10.2_

  - [x] 1.2 實作 SkillTree 模型
    - `backend/app/qa_agent/learning_path/skill_tree.py`
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 2. 學習目標解析
  - [x] 2.1 實作目標解析器
    - `backend/app/qa_agent/learning_path/goal_parser.py`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 3. 學習路徑生成
  - [x] 3.1 實作 LearningPathGenerator
    - `backend/app/qa_agent/learning_path/path_generator.py`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 4. 智能文章推薦
  - [x] 4.1 實作 ArticleRecommender
    - `backend/app/qa_agent/learning_path/article_recommender.py`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 5. 學習進度追蹤
  - [x] 5.1 實作 ProgressTracker
    - `backend/app/qa_agent/learning_path/progress_tracker.py`
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 6. 動態計劃調整
  - [x] 6.1 實作 DynamicAdjuster
    - `backend/app/qa_agent/learning_path/dynamic_adjuster.py`
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 7. 學習成效評估
  - [x] 7.1 實作成效評估模組
    - `backend/app/qa_agent/learning_path/effectiveness_evaluator.py`
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 8. 系統整合與上線
  - [x] 8.1 建立後端 REST API endpoints
    - `backend/app/api/learning_path.py`
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [x] 8.2 將 Learning Path router 掛進主應用程式
    - `backend/app/main.py`
    - _Requirements: 6.1_

  - [x] 8.3 建立前端學習路徑頁面
    - `frontend/app/app/learning/page.tsx`
    - `frontend/app/app/learning/[id]/page.tsx`
    - _Requirements: 2.5, 4.2, 6.5_

  - [x] 8.4 前端 API 整合
    - `frontend/lib/api/learning-path.ts`
    - Navigation.tsx 已加入學習路徑入口
    - _Requirements: 6.1_

  - [x] 8.5 端對端整合測試
    - _Requirements: 2.1, 4.1, 5.1_

## Notes

- 依賴 intelligent-qa-agent 的 LLM 基礎設施進行目標解析和路徑生成
- 依賴 proactive-learning-agent 的用戶偏好數據優化文章推薦
- SkillTree 初始資料需要預先建立常見技術領域的依賴關係
