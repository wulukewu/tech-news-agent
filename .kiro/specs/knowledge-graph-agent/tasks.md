# Implementation Plan: Knowledge Graph Agent

## Overview

This implementation plan breaks down the Knowledge Graph Agent into discrete coding tasks. The system uses LLM to automatically extract dependency relationships between technical articles, builds structured knowledge graphs, provides interactive D3.js visualization, and tracks personalized learning progress.

The implementation follows a layered approach: graph database → LLM dependency extraction → graph building → progress tracking → recommendation engine → API integration → interactive frontend visualization.

## Tasks

- [ ] 1. 圖形資料層建立
  - [ ] 1.1 建立資料庫 schema
    - 新增 `knowledge_nodes` 資料表（知識節點：技術概念/技能點）
    - 新增 `node_dependencies` 資料表（節點間依賴關係和信心分數）
    - 新增 `technical_domains` 資料表（技術領域定義）
    - 新增 `user_node_progress` 資料表（用戶各節點學習狀態）
    - 新增 `user_achievements` 資料表（成就徽章記錄）
    - _Requirements: 7.1, 7.5_

  - [ ] 1.2 實作 GraphDatabase 存取層
    - 建立 `backend/app/qa_agent/knowledge_graph/graph_database.py`
    - 實作節點和依賴關係的 CRUD 操作
    - 支援圖形遍歷查詢（找出前置節點、後續節點）
    - 實作快取機制減少重複查詢
    - _Requirements: 7.4, 8.5_

- [ ] 2. LLM 依賴關係提取
  - [ ] 2.1 實作 DependencyExtractor
    - 建立 `backend/app/qa_agent/knowledge_graph/dependency_extractor.py`
    - 使用結構化提示模板分析技術文章
    - 識別前置知識、核心概念、後續主題
    - 提取依賴關係的信心分數
    - 處理中英文技術文章
    - 識別並標記循環依賴關係
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

  - [ ] 2.2 實作衝突解決機制
    - 使用 LLM 解決依賴關係衝突
    - 記錄衝突解決決策過程
    - _Requirements: 1.5_

- [ ] 3. 知識圖譜建立與管理
  - [ ] 3.1 實作 KnowledgeGraphBuilder
    - 建立 `backend/app/qa_agent/knowledge_graph/graph_builder.py`
    - 整合 DependencyExtractor 建立完整 Skill_Tree
    - 支援至少 10 個技術領域（Kubernetes、React、Python、ML、DevOps 等）
    - 支援增量更新，避免完整重建
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 5.1, 5.2, 5.3, 8.6_

  - [ ] 3.2 支援自訂技術領域
    - 允許用戶新增自訂 Technical_Domain
    - 提供技術領域間的跨領域關聯
    - _Requirements: 5.5, 5.6_

- [ ] 4. 學習進度追蹤
  - [ ] 4.1 實作 ProgressTracker
    - 建立 `backend/app/qa_agent/knowledge_graph/progress_tracker.py`
    - 記錄用戶各節點的 Learning_Status（未開始/進行中/已完成）
    - 計算整體學習進度百分比
    - 完成前置節點後自動解鎖後續節點
    - 追蹤學習時間和頻率
    - 實作成就徽章系統
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [ ] 5. 智能學習推薦
  - [ ] 5.1 實作 RecommendationEngine
    - 建立 `backend/app/qa_agent/knowledge_graph/recommendation_engine.py`
    - 基於用戶進度分析可學習的節點
    - 提供 3-5 個優先推薦學習目標
    - 考慮節點難度、用戶偏好和時間限制
    - 提供推薦理由和預估學習時間
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [ ] 6. 資料匯出與持久化
  - [ ] 6.1 實作資料匯出功能
    - 支援匯出為 JSON 和 GraphML 格式
    - 提供資料備份和還原功能
    - 實作資料完整性驗證
    - _Requirements: 7.2, 7.3, 7.6_

- [ ] 7. 系統整合與上線
  - [ ] 7.1 建立後端 REST API endpoints
    - 在 `backend/app/api/knowledge_graph.py` 建立 FastAPI router
    - 實作 `GET /api/knowledge-graph/domains` — 取得所有技術領域列表
    - 實作 `POST /api/knowledge-graph/domains` — 建立新技術領域圖譜
    - 實作 `GET /api/knowledge-graph/domains/{domain}` — 取得特定領域的完整圖譜數據
    - 實作 `GET /api/knowledge-graph/domains/{domain}/progress` — 取得用戶在該領域的進度
    - 實作 `POST /api/knowledge-graph/nodes/{id}/complete` — 標記節點完成
    - 實作 `GET /api/knowledge-graph/domains/{domain}/recommendations` — 取得推薦節點
    - 實作 `GET /api/knowledge-graph/export/{domain}` — 匯出圖譜數據
    - 加入 JWT 認證和 rate limiting
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

  - [ ] 7.2 將 Knowledge Graph router 掛進主應用程式
    - 在 `backend/app/main.py` import 並 `include_router`
    - _Requirements: 6.1_

  - [ ] 7.3 建立前端知識圖譜視覺化頁面
    - 在 `frontend/app/knowledge-graph/page.tsx` 建立主頁（技術領域選擇）
    - 在 `frontend/app/knowledge-graph/[domain]/page.tsx` 建立圖譜視覺化頁面
    - 使用 D3.js 或 react-force-graph 實作互動式知識圖譜
    - 用不同顏色區分未開始/進行中/已完成節點
    - 支援縮放、拖拽、篩選功能
    - 點擊節點顯示詳細資訊和相關文章
    - 顯示整體進度百分比和成就徽章
    - 支援行動裝置觸控操作
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 10.1, 10.2, 10.4, 10.5_

  - [ ] 7.4 前端 API 整合
    - 在 `frontend/lib/api/knowledge-graph.ts` 建立 API client
    - 加入導航連結（navbar 加入「知識圖譜」入口）
    - 實作圖譜數據的前端快取（避免重複載入）
    - _Requirements: 8.2_

  - [ ] 7.5 效能優化
    - 確保 1000 節點圖譜在 2 秒內載入
    - 確保 100 節點圖形在 500ms 內渲染
    - 實作 LLM 分析的進度指示器
    - _Requirements: 8.1, 8.2, 8.4_

  - [ ] 7.6 端對端整合測試
    - 測試建立領域圖譜 → 視覺化顯示 → 標記完成 → 進度更新完整流程
    - 測試推薦引擎準確性
    - 測試大規模圖譜效能
    - _Requirements: 1.1, 3.2, 4.2, 8.1_

## Notes

- 這是技術複雜度最高的功能，依賴所有前面功能的數據
- D3.js 圖形渲染需要特別注意效能，建議使用 WebGL 加速（如 react-force-graph）
- LLM 依賴提取可能需要較長時間，需實作非同步處理和進度通知
- 初始技術領域的知識圖譜可以預先建立，避免用戶等待
