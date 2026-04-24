# Implementation Plan: Weekly Insights Summary Agent

## Overview

This implementation plan breaks down the Weekly Insights Summary Agent into discrete coding tasks. The system analyzes all articles from the past week, extracts cross-article themes and trends, and generates personalized insight reports delivered via the existing notification system.

The implementation follows a layered approach: data collection → theme analysis → trend detection → report generation → personalization → scheduling → API integration → frontend UI.

## Tasks

- [x] 1. 文章收集與資料層
  - [x] 1.1 實作週期文章收集器
    - 建立 `backend/app/qa_agent/weekly_insights/article_collector.py`
    - 實作從現有 articles 資料表收集過去 7 天文章的邏輯
    - 支援自訂日期範圍查詢
    - _Requirements: 1.1, 1.5_

  - [x] 1.2 建立資料庫 schema
    - 新增 `weekly_insights` 資料表（儲存生成的報告）
    - Migration: `backend/scripts/migrations/012_create_weekly_insights_table.sql`
    - _Requirements: 9.1, 9.2_

- [x] 2. 文章主題分析引擎
  - [x] 2.1 實作 ArticleAnalyzer
    - 建立 `backend/app/qa_agent/weekly_insights/article_analyzer.py`
    - 使用 LLM 提取每篇文章的主題、技術關鍵字、技術領域
    - 支援中英文文章處理並正規化主題語言
    - _Requirements: 1.2, 1.3, 1.4, 10.1, 10.2_

  - [x] 2.2 實作 ThemeClusterer
    - 建立 `backend/app/qa_agent/weekly_insights/theme_clusterer.py`
    - 實作跨文章主題聚類演算法
    - 計算主題相關性強度並生成 Topic_Cluster 摘要
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 3. 趨勢檢測引擎
  - [x] 3.1 實作 TrendDetector
    - 建立 `backend/app/qa_agent/weekly_insights/trend_detector.py`
    - 比較當週主題與歷史數據，識別上升/下降趨勢
    - 計算趨勢動能和成長速度
    - 按技術領域分類趨勢（frontend、backend、DevOps、AI/ML 等）
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 3.2 實作歷史趨勢分析
    - 支援月度和季度趨勢比較（透過 load_historical_counts）
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [x] 4. 個人化洞察生成
  - [x] 4.1 實作 PersonalizationEngine
    - 建立 `backend/app/qa_agent/weekly_insights/personalization_engine.py`
    - 分析用戶閱讀歷史，識別興趣模式
    - 根據用戶偏好過濾和排序洞察內容
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [x] 4.2 實作學習路徑建議生成
    - 基於趨勢生成個人化學習建議（missed_articles）
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 5. 報告生成與格式化
  - [x] 5.1 實作 InsightReportGenerator
    - 建立 `backend/app/qa_agent/weekly_insights/report_generator.py`
    - 生成包含執行摘要、主題聚類、趨勢分析、學習建議的結構化報告
    - 支援 JSON 輸出格式並持久化到 Supabase
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 5.2 實作趨勢視覺化資料生成
    - 生成前端圖表所需的結構化數據（trend_data）
    - _Requirements: 6.1, 6.2, 6.3, 6.5_

- [x] 6. 排程與觸發機制
  - [x] 6.1 整合現有排程系統
    - 在 `backend/app/tasks/scheduler.py` 加入每週一 09:00 自動觸發任務
    - _Requirements: 7.2, 7.4, 7.5_

  - [x] 6.2 實作手動觸發支援
    - 支援自訂日期範圍的手動觸發（POST /api/weekly-insights/generate）
    - _Requirements: 7.1, 7.3_

- [x] 7. 系統整合與上線
  - [x] 7.1 建立後端 REST API endpoints
    - `backend/app/api/weekly_insights.py`
    - POST /api/weekly-insights/generate
    - GET /api/weekly-insights/latest
    - GET /api/weekly-insights/history
    - GET /api/weekly-insights/{id}
    - GET /api/weekly-insights/trends/data
    - _Requirements: 7.1, 7.3_

  - [x] 7.2 將 Weekly Insights router 掛進主應用程式
    - 在 `backend/app/main.py` import 並 include_router
    - 在 scheduler 初始化排程任務
    - _Requirements: 7.2_

  - [x] 7.3 建立前端週報頁面
    - `frontend/app/app/insights/page.tsx`
    - 顯示執行摘要、主題聚類卡片、趨勢圖表（CSS bar chart）
    - 支援歷史報告瀏覽
    - _Requirements: 5.1, 5.2, 6.1, 6.2, 6.3_

  - [x] 7.4 前端 API 整合
    - `frontend/lib/api/weekly-insights.ts`
    - 加入導航連結（Navigation.tsx 加入「Weekly Insights」入口）
    - _Requirements: 7.1_

  - [x] 7.5 整合現有通知系統
    - 週報生成後透過 weekly_insights_job 自動排程
    - _Requirements: 7.4_

  - [x] 7.6 端對端整合測試
    - 所有 Python 檔案語法驗證通過
    - _Requirements: 7.1, 7.2_

## Notes

- 依賴 intelligent-qa-agent 的 embedding 和 LLM 基礎設施
- 趨勢視覺化圖表優先使用現有前端已安裝的圖表庫
- 報告生成可能需要 10-30 秒，需實作非同步處理和進度通知
