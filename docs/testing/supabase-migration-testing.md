# Supabase Migration Phase 1 - Testing Guide

本文件說明如何測試 Supabase 遷移 Phase 1 的資料庫基礎建設。

## 測試概覽

Phase 1 包含以下測試類別：

1. **配置測試** - 驗證環境變數與配置類別
2. **SQL 初始化測試** - 驗證資料庫結構建立
3. **種子腳本測試** - 驗證 RSS 訂閱源灌入
4. **屬性測試** - 使用 Hypothesis 驗證 17 個正確性屬性
5. **測試基礎設施測試** - 驗證 fixtures 與清理機制

## 前置準備

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 設定測試環境變數

建立 `.env` 檔案並填入 Supabase 測試資料庫的連線資訊：

```bash
# Supabase 測試資料庫（建議使用獨立的測試專案）
SUPABASE_URL=https://your-test-project.supabase.co
SUPABASE_KEY=your-test-anon-key

# 其他必要變數（測試用假值即可）
DISCORD_TOKEN=test_token
DISCORD_CHANNEL_ID=123456789
GROQ_API_KEY=test_key
TIMEZONE=Asia/Taipei
```

⚠️ **重要：** 建議使用獨立的 Supabase 測試專案，避免影響開發或生產環境。

### 3. 初始化測試資料庫

在 Supabase Dashboard 的 SQL Editor 執行：

```bash
# 執行初始化腳本
cat scripts/init_supabase.sql
```

或直接在 SQL Editor 貼上 `scripts/init_supabase.sql` 的內容。

## 執行測試

### 快速開始 - 執行所有 Supabase 測試

```bash
pytest tests/test_database_properties.py tests/test_config.py tests/test_seed_feeds.py tests/test_sql_init_integration.py -v
```

### 分類執行

#### 1. 配置測試（最快，不需資料庫）

```bash
pytest tests/test_config.py -v
```

**測試內容：**

- Settings 類別包含 `supabase_url` 和 `supabase_key` 欄位
- Settings 類別不包含任何 `notion_*` 欄位
- 環境變數正確載入

**預期結果：** 12 個測試全部通過

#### 2. SQL 初始化測試（需要資料庫）

```bash
pytest tests/test_sql_init_integration.py -v
```

**測試內容：**

- SQL 腳本可以成功執行
- 所有表格都已建立（users, feeds, user_subscriptions, articles, reading_list）
- pgvector 擴充功能已啟用
- 所有索引都已建立（包含 HNSW 向量索引）

**預期結果：** 4 個測試全部通過

#### 3. 種子腳本測試（需要資料庫）

```bash
pytest tests/test_seed_feeds.py -v
```

**測試內容：**

- 缺少環境變數時拋出錯誤
- 重複 URL 處理邏輯
- 連線失敗處理
- 成功插入訂閱源

**預期結果：** 10 個測試全部通過

#### 4. 屬性測試（需要資料庫，較慢）

```bash
pytest tests/test_database_properties.py -v
```

**測試內容：** 17 個正確性屬性，每個屬性執行 20 次迭代（預設）

**屬性列表：**

1. **User Deletion Cascades** - 刪除使用者時相關訂閱與閱讀清單自動刪除
2. **Feed Deletion Cascades** - 刪除訂閱源時相關文章自動刪除
3. **Article Deletion Cascades** - 刪除文章時相關閱讀清單記錄自動刪除
4. **Discord ID Uniqueness** - discord_id 必須唯一
5. **Subscription Uniqueness** - (user_id, feed_id) 組合必須唯一
6. **Reading List Entry Uniqueness** - (user_id, article_id) 組合必須唯一
7. **Feed URL Uniqueness** - 訂閱源 URL 必須唯一
8. **Article URL Uniqueness** - 文章 URL 必須唯一
9. **Shared Feed References** - 多個使用者可訂閱同一個訂閱源
10. **Required Field Validation** - NOT NULL 欄位驗證
11. **Timestamp Auto-Population** - 時間戳記自動填入
12. **Reading List Status Validation** - status 必須為 Unread/Read/Archived
13. **Rating Range Validation** - rating 必須在 1-5 範圍內
14. **Embedding NULL Tolerance** - embedding 可以為 NULL
15. **Seed Script Active Flag** - 種子腳本插入的訂閱源 is_active 為 true
16. **Seed Script Duplicate Handling** - 種子腳本正確處理重複 URL
17. **Updated Timestamp Trigger** - updated_at 觸發器正常運作

**預期結果：** 17 個測試全部通過

### 調整測試速度

屬性測試使用 Hypothesis 框架，可透過環境變數調整迭代次數：

```bash
# 快速測試（每個屬性 10 次迭代）- 適合開發時快速驗證
HYPOTHESIS_PROFILE=dev pytest tests/test_database_properties.py -v

# 預設測試（每個屬性 20 次迭代）- 平衡速度與覆蓋率
pytest tests/test_database_properties.py -v

# 完整測試（每個屬性 100 次迭代）- CI/生產環境使用
HYPOTHESIS_PROFILE=ci pytest tests/test_database_properties.py -v

# 除錯模式（每個屬性 5 次迭代，詳細輸出）
HYPOTHESIS_PROFILE=debug pytest tests/test_database_properties.py -v
```

## 測試基礎設施

### Fixtures

測試使用以下 fixtures（定義於 `tests/conftest.py`）：

- **test_supabase_client** - Supabase 客戶端連線
- **test_user** - 測試用使用者（自動清理）
- **test_feed** - 測試用訂閱源（自動清理）
- **test_article** - 測試用文章（自動清理）
- **test_subscription** - 測試用訂閱關係（自動清理）
- **test_reading_list_entry** - 測試用閱讀清單記錄（自動清理）
- **cleanup_test_data** - 手動清理機制

所有 fixtures 都會在測試結束後自動清理資料，確保測試獨立性。

詳細說明請參考 [Test Fixtures 文件](./test-fixtures.md)。

### 清理機制

測試使用兩種清理機制：

1. **自動清理（Fixture）** - 每個 fixture 在 yield 後自動刪除建立的資料
2. **手動清理（cleanup_test_data）** - 提供追蹤字典，可手動追蹤需要清理的資料

詳細說明請參考 [Cleanup Mechanism 文件](./cleanup-mechanism.md)。

## 常見問題

### Q: 測試失敗：SUPABASE_URL not set

**A:** 請確認 `.env` 檔案存在且包含 `SUPABASE_URL` 和 `SUPABASE_KEY`。

### Q: 測試失敗：relation "users" does not exist

**A:** 請先在 Supabase Dashboard 執行 `scripts/init_supabase.sql` 初始化資料庫結構。

### Q: 屬性測試太慢

**A:** 使用 `HYPOTHESIS_PROFILE=dev` 減少迭代次數：

```bash
HYPOTHESIS_PROFILE=dev pytest tests/test_database_properties.py -v
```

### Q: 測試失敗：duplicate key value violates unique constraint

**A:** 這可能是測試清理不完全導致。請手動清理測試資料庫：

```sql
-- 在 Supabase SQL Editor 執行
TRUNCATE users, feeds, user_subscriptions, articles, reading_list CASCADE;
```

### Q: 如何只執行特定的屬性測試？

**A:** 使用 pytest 的 `-k` 參數：

```bash
# 只執行 CASCADE DELETE 相關測試
pytest tests/test_database_properties.py -k "cascade" -v

# 只執行 uniqueness 相關測試
pytest tests/test_database_properties.py -k "uniqueness" -v

# 只執行特定編號的測試
pytest tests/test_database_properties.py -k "property_1" -v
```

## 測試覆蓋率

查看測試覆蓋率：

```bash
pytest tests/test_database_properties.py tests/test_config.py tests/test_seed_feeds.py --cov=app --cov-report=html
```

覆蓋率報告會生成在 `htmlcov/index.html`。

## CI/CD 整合

在 CI 環境中執行測試：

```bash
# 設定環境變數
export SUPABASE_URL=your-ci-test-db-url
export SUPABASE_KEY=your-ci-test-db-key
export DISCORD_TOKEN=test_token
export DISCORD_CHANNEL_ID=123456789
export GROQ_API_KEY=test_key

# 執行完整測試（100 次迭代）
HYPOTHESIS_PROFILE=ci pytest tests/test_database_properties.py tests/test_config.py tests/test_seed_feeds.py tests/test_sql_init_integration.py -v --tb=short
```

## 下一步

Phase 1 測試完成後，可以開始 Phase 2 的服務遷移：

1. 遷移 RSS Service 至 Supabase
2. 遷移 Notion Service 至 Supabase
3. 更新 Discord Bot 指令
4. 更新排程任務

每個階段都應該有對應的測試覆蓋。

## 參考文件

- [Hypothesis 文件](https://hypothesis.readthedocs.io/)
- [Supabase Python 客戶端](https://supabase.com/docs/reference/python/introduction)
- [pytest 文件](https://docs.pytest.org/)
- [Test Fixtures 說明](./test-fixtures.md)
- [Cleanup Mechanism 說明](./cleanup-mechanism.md)
- [SQL Integration Tests 說明](./sql-integration-tests.md)
