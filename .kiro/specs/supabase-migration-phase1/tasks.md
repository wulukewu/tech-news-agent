# Implementation Plan: Supabase Migration Phase 1

## Overview

本實作計畫將 Tech News Agent 從 Notion 遷移至 Supabase，建立支援多租戶架構的 PostgreSQL 資料庫基礎建設。實作包括清理舊有依賴、更新配置、建立資料庫結構、灌入種子資料，以及完整的測試覆蓋。

## Tasks

- [x] 1. 清理 Notion 依賴與配置
  - [x] 1.1 更新 requirements.txt 移除 notion-client 並新增 supabase
    - 從 requirements.txt 移除 `notion-client==2.2.1`
    - 新增 `supabase>=2.0.0` 到 requirements.txt
    - _Requirements: 2.1, 2.2_

  - [x] 1.2 更新 .env.example 移除 Notion 變數並新增 Supabase 變數
    - 移除所有 NOTION\_\* 環境變數（NOTION_TOKEN, NOTION_FEEDS_DB_ID, NOTION_READ_LATER_DB_ID, NOTION_WEEKLY_DIGESTS_DB_ID）
    - 新增 SUPABASE_URL 環境變數範例
    - 新增 SUPABASE_KEY 環境變數範例
    - 新增註解說明如何從 Supabase Dashboard 取得這些值
    - _Requirements: 1.5, 1.6_

  - [x] 1.3 更新 app/core/config.py 移除 Notion 欄位並新增 Supabase 欄位
    - 從 Settings 類別移除所有 notion\_\* 欄位（notion_token, notion_feeds_db_id, notion_read_later_db_id, notion_weekly_digests_db_id）
    - 新增 supabase_url: str 欄位
    - 新增 supabase_key: str 欄位
    - 保持其他配置欄位不變（discord_token, discord_channel_id, groq_api_key, timezone）
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [x] 1.4 撰寫配置模組的單元測試
    - 測試 Settings 類別包含 supabase_url 和 supabase_key 欄位
    - 測試 Settings 類別不包含任何 notion\_\* 欄位
    - 測試環境變數載入功能
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. 建立資料庫初始化 SQL 腳本
  - [x] 2.1 建立 scripts/init_supabase.sql 並啟用 pgvector 擴充功能
    - 建立 scripts 目錄（如果不存在）
    - 建立 init_supabase.sql 檔案
    - 新增 SQL 指令啟用 pgvector 擴充功能：`CREATE EXTENSION IF NOT EXISTS vector;`
    - _Requirements: 3.1, 3.2, 5.1_

  - [x] 2.2 建立 users 資料表
    - 新增 CREATE TABLE users 語句
    - 定義欄位：id (UUID PRIMARY KEY DEFAULT gen_random_uuid()), discord_id (TEXT UNIQUE NOT NULL), created_at (TIMESTAMPTZ DEFAULT now())
    - _Requirements: 3.3, 6.1, 8.1, 9.3_

  - [x] 2.3 建立 feeds 資料表
    - 新增 CREATE TABLE feeds 語句
    - 定義欄位：id (UUID PRIMARY KEY DEFAULT gen_random_uuid()), name (TEXT NOT NULL), url (TEXT UNIQUE NOT NULL), category (TEXT NOT NULL), is_active (BOOLEAN DEFAULT true), created_at (TIMESTAMPTZ DEFAULT now())
    - _Requirements: 3.4, 7.3, 8.2, 9.4, 9.5, 9.6_

  - [x] 2.4 建立 user_subscriptions 資料表
    - 新增 CREATE TABLE user_subscriptions 語句
    - 定義欄位：id (UUID PRIMARY KEY DEFAULT gen_random_uuid()), user_id (UUID REFERENCES users(id) ON DELETE CASCADE), feed_id (UUID REFERENCES feeds(id) ON DELETE CASCADE), subscribed_at (TIMESTAMPTZ DEFAULT now())
    - 新增 UNIQUE 約束於 (user_id, feed_id)
    - _Requirements: 3.5, 3.9, 6.2, 6.4, 8.3_

  - [x] 2.5 建立 articles 資料表
    - 新增 CREATE TABLE articles 語句
    - 定義欄位：id (UUID PRIMARY KEY DEFAULT gen_random_uuid()), feed_id (UUID REFERENCES feeds(id) ON DELETE CASCADE), title (TEXT NOT NULL), url (TEXT UNIQUE NOT NULL), published_at (TIMESTAMPTZ), tinkering_index (INTEGER), ai_summary (TEXT), embedding (VECTOR(1536)), created_at (TIMESTAMPTZ DEFAULT now())
    - _Requirements: 3.6, 3.10, 5.2, 5.4, 7.4, 8.4, 8.5, 9.7, 9.8_

  - [x] 2.6 建立 reading_list 資料表
    - 新增 CREATE TABLE reading_list 語句
    - 定義欄位：id (UUID PRIMARY KEY DEFAULT gen_random_uuid()), user_id (UUID REFERENCES users(id) ON DELETE CASCADE), article_id (UUID REFERENCES articles(id) ON DELETE CASCADE), status (TEXT CHECK (status IN ('Unread', 'Read', 'Archived'))), rating (INTEGER CHECK (rating >= 1 AND rating <= 5)), added_at (TIMESTAMPTZ DEFAULT now()), updated_at (TIMESTAMPTZ DEFAULT now())
    - 新增 UNIQUE 約束於 (user_id, article_id)
    - _Requirements: 3.7, 3.9, 3.11, 6.3, 6.5, 8.6, 8.7, 9.1, 9.2_

  - [x] 2.7 建立資料庫索引
    - 在 feeds 表建立索引：CREATE INDEX idx_feeds_is_active ON feeds(is_active);
    - 在 feeds 表建立索引：CREATE INDEX idx_feeds_category ON feeds(category);
    - 在 user_subscriptions 表建立索引：CREATE INDEX idx_user_subscriptions_user_id ON user_subscriptions(user_id);
    - 在 user_subscriptions 表建立索引：CREATE INDEX idx_user_subscriptions_feed_id ON user_subscriptions(feed_id);
    - 在 articles 表建立索引：CREATE INDEX idx_articles_feed_id ON articles(feed_id);
    - 在 articles 表建立索引：CREATE INDEX idx_articles_published_at ON articles(published_at);
    - 在 articles 表建立向量索引：CREATE INDEX idx_articles_embedding ON articles USING hnsw (embedding vector_cosine_ops);
    - 在 reading_list 表建立索引：CREATE INDEX idx_reading_list_user_id ON reading_list(user_id);
    - 在 reading_list 表建立索引：CREATE INDEX idx_reading_list_status ON reading_list(status);
    - 在 reading_list 表建立索引：CREATE INDEX idx_reading_list_rating ON reading_list(rating);
    - _Requirements: 3.8, 5.3_

  - [x] 2.8 建立 updated_at 自動更新觸發器
    - 建立 update_updated_at_column() 函數
    - 建立觸發器 update_reading_list_updated_at 於 reading_list 表
    - _Requirements: 8.8_

  - [x] 2.9 撰寫 SQL 腳本的整合測試
    - 測試 SQL 腳本可以成功執行
    - 測試所有表格都已建立
    - 測試 pgvector 擴充功能已啟用
    - 測試所有索引都已建立
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8_

- [x] 3. Checkpoint - 驗證資料庫結構
  - 在 Supabase Dashboard 執行 init_supabase.sql
  - 確認所有表格、索引、約束都已正確建立
  - 如有問題請詢問使用者

- [x] 4. 建立種子資料 Python 腳本
  - [x] 4.1 建立 scripts/seed_feeds.py 基礎結構
    - 建立 seed_feeds.py 檔案
    - 匯入必要套件：supabase, os, dotenv
    - 載入環境變數並驗證 SUPABASE_URL 和 SUPABASE_KEY 存在
    - 建立 Supabase 客戶端連線
    - _Requirements: 4.1, 4.2, 4.3, 10.1, 10.2, 10.3_

  - [x] 4.2 定義預設 RSS 訂閱源資料
    - 建立包含 14 個訂閱源的資料結構（list of dicts）
    - 前端開發類別：Vue.js News, Nuxt, VitePress, Express, Vue.js Developers
    - 自架服務類別：Reddit r/selfhosted, Reddit r/docker, Home Assistant, Awesome-Selfhosted
    - AI 應用類別：Simon Willison's Weblog, Reddit r/LocalLLaMA, Vue.js Community Newsletters
    - 每個訂閱源包含：name, url, category, is_active (設為 true)
    - _Requirements: 4.4, 4.5, 4.6, 4.7_

  - [x] 4.3 實作資料插入邏輯與錯誤處理
    - 使用 try-except 包裹插入邏輯
    - 對每個訂閱源執行 supabase.table('feeds').insert().execute()
    - 捕獲重複 URL 錯誤並跳過該訂閱源
    - 捕獲連線錯誤並顯示清晰的錯誤訊息
    - 記錄成功插入的訂閱源數量
    - _Requirements: 4.8, 4.9, 4.10, 10.4, 10.5_

  - [x] 4.4 撰寫種子腳本的單元測試
    - 測試缺少環境變數時拋出錯誤
    - 測試重複 URL 處理邏輯
    - 測試連線失敗處理
    - _Requirements: 4.8, 4.9, 10.3, 10.5_

- [x] 5. Checkpoint - 執行種子資料腳本
  - 執行 `python scripts/seed_feeds.py`
  - 確認 14 個訂閱源已成功插入
  - 在 Supabase Dashboard 驗證資料
  - 如有問題請詢問使用者

- [x] 6. 撰寫屬性測試（Property-Based Tests）
  - [x] 6.1 撰寫 Property 1: User Deletion Cascades 測試
    - **Property 1: User Deletion Cascades**
    - **Validates: Requirements 3.9**
    - 使用 Hypothesis 生成隨機 discord_id
    - 建立使用者、訂閱、閱讀清單記錄
    - 刪除使用者後驗證相關記錄已被刪除

  - [x] 6.2 撰寫 Property 2: Feed Deletion Cascades 測試
    - **Property 2: Feed Deletion Cascades**
    - **Validates: Requirements 3.10**
    - 使用 Hypothesis 生成隨機 feed URL
    - 建立訂閱源與文章記錄
    - 刪除訂閱源後驗證相關文章已被刪除

  - [x] 6.3 撰寫 Property 3: Article Deletion Cascades 測試
    - **Property 3: Article Deletion Cascades**
    - **Validates: Requirements 3.11**
    - 使用 Hypothesis 生成隨機文章資料
    - 建立文章與閱讀清單記錄
    - 刪除文章後驗證相關閱讀清單記錄已被刪除

  - [x] 6.4 撰寫 Property 4: Discord ID Uniqueness 測試
    - **Property 4: Discord ID Uniqueness**
    - **Validates: Requirements 6.1**
    - 使用 Hypothesis 生成隨機 discord_id
    - 插入第一個使用者成功
    - 嘗試插入相同 discord_id 的第二個使用者應失敗

  - [x] 6.5 撰寫 Property 5: Subscription Uniqueness 測試
    - **Property 5: Subscription Uniqueness**
    - **Validates: Requirements 6.4**
    - 使用 Hypothesis 生成隨機使用者與訂閱源
    - 建立第一個訂閱成功
    - 嘗試建立重複訂閱應失敗

  - [x] 6.6 撰寫 Property 6: Reading List Entry Uniqueness 測試
    - **Property 6: Reading List Entry Uniqueness**
    - **Validates: Requirements 6.5**
    - 使用 Hypothesis 生成隨機使用者與文章
    - 建立第一個閱讀清單記錄成功
    - 嘗試建立重複記錄應失敗

  - [x] 6.7 撰寫 Property 7: Feed URL Uniqueness 測試
    - **Property 7: Feed URL Uniqueness**
    - **Validates: Requirements 7.3**
    - 使用 Hypothesis 生成隨機 feed URL
    - 插入第一個訂閱源成功
    - 嘗試插入相同 URL 的第二個訂閱源應失敗

  - [x] 6.8 撰寫 Property 8: Article URL Uniqueness 測試
    - **Property 8: Article URL Uniqueness**
    - **Validates: Requirements 7.4**
    - 使用 Hypothesis 生成隨機文章 URL
    - 插入第一個文章成功
    - 嘗試插入相同 URL 的第二個文章應失敗

  - [x] 6.9 撰寫 Property 9: Shared Feed References 測試
    - **Property 9: Shared Feed References**
    - **Validates: Requirements 7.5**
    - 使用 Hypothesis 生成多個使用者
    - 建立一個訂閱源
    - 多個使用者訂閱同一個訂閱源
    - 驗證所有訂閱記錄都參照相同的 feed_id

  - [x] 6.10 撰寫 Property 10: Required Field Validation 測試
    - **Property 10: Required Field Validation**
    - **Validates: Requirements 9.3, 9.4, 9.5, 9.6, 9.7, 9.8**
    - 測試 users 表的 discord_id 為 NULL 時插入失敗
    - 測試 feeds 表的 name, url, category 為 NULL 時插入失敗
    - 測試 articles 表的 title, url 為 NULL 時插入失敗

  - [x] 6.11 撰寫 Property 11: Timestamp Auto-Population 測試
    - **Property 11: Timestamp Auto-Population**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.6, 8.7**
    - 插入記錄時不提供時間戳記欄位
    - 驗證 created_at, subscribed_at, added_at, updated_at 自動填入當前時間

  - [x] 6.12 撰寫 Property 12: Reading List Status Validation 測試
    - **Property 12: Reading List Status Validation**
    - **Validates: Requirements 9.1**
    - 使用 Hypothesis 生成不在 {'Unread', 'Read', 'Archived'} 的 status 值
    - 嘗試插入應失敗並拋出 CHECK constraint 錯誤

  - [x] 6.13 撰寫 Property 13: Rating Range Validation 測試
    - **Property 13: Rating Range Validation**
    - **Validates: Requirements 9.2**
    - 使用 Hypothesis 生成不在 [1, 5] 範圍的 rating 值
    - 嘗試插入應失敗並拋出 CHECK constraint 錯誤

  - [x] 6.14 撰寫 Property 14: Embedding NULL Tolerance 測試
    - **Property 14: Embedding NULL Tolerance**
    - **Validates: Requirements 5.4**
    - 插入文章時不提供 embedding 值（NULL）
    - 驗證插入成功

  - [x] 6.15 撰寫 Property 15: Seed Script Active Flag 測試
    - **Property 15: Seed Script Active Flag**
    - **Validates: Requirements 4.7**
    - 執行種子腳本
    - 驗證所有插入的訂閱源 is_active 欄位為 true

  - [x] 6.16 撰寫 Property 16: Seed Script Duplicate Handling 測試
    - **Property 16: Seed Script Duplicate Handling**
    - **Validates: Requirements 4.8**
    - 預先插入一個訂閱源
    - 執行種子腳本
    - 驗證腳本跳過重複的訂閱源並繼續執行

  - [x] 6.17 撰寫 Property 17: Updated Timestamp Trigger 測試
    - **Property 17: Updated Timestamp Trigger**
    - **Validates: Requirements 8.8**
    - 建立閱讀清單記錄
    - 記錄初始 updated_at 時間
    - 更新記錄的 status 欄位
    - 驗證 updated_at 已自動更新為新的時間

- [x] 7. 建立測試基礎設施
  - [x] 7.1 建立測試配置與 fixtures
    - 建立 tests/conftest.py
    - 定義 test_supabase_client fixture（連接測試資料庫）
    - 定義 test_user, test_feed, test_article fixtures（可重用的測試資料）
    - 配置 Hypothesis 設定（最少 100 次迭代）

  - [x] 7.2 建立測試資料庫清理機制
    - 實作 cleanup_test_data fixture
    - 在每個測試後清理建立的資料
    - 確保測試獨立性

- [x] 8. Final Checkpoint - 執行所有測試
  - 執行 `pytest tests/ -v` 確認所有測試通過
  - 檢查測試覆蓋率
  - 如有失敗測試請詢問使用者

## Notes

- 任務標記 `*` 為可選測試任務，可跳過以加快 MVP 開發
- 每個任務都明確參照需求編號以確保可追溯性
- Checkpoint 任務確保階段性驗證
- 屬性測試使用 Hypothesis 框架，每個測試至少執行 100 次迭代
- 測試任務包含完整的 17 個 correctness properties
- 建議在測試環境使用獨立的 Supabase 專案，避免影響開發環境
