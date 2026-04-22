# QA Agent 架構分析與建議

## 執行摘要

經過測試驗證，**HuggingFace 免費 Inference API 已經無法使用**（返回 404 錯誤）。
建議**完全移除 embedding 功能**，改用**純關鍵字搜尋**，這樣更簡單、穩定且完全免費。

---

## 🔍 當前架構問題

### 1. HuggingFace Embedding 不可用 ❌

**測試結果**:

```bash
$ python3 test_hf_embedding.py

狀態碼: 404
錯誤: Cannot POST /models/sentence-transformers/all-MiniLM-L6-v2
```

**原因分析**:

- HuggingFace 已經停止提供無 API key 的免費 Inference API
- 即使有 API key，免費額度也非常有限
- 無法追蹤用量，不適合生產環境

### 2. 前端顯示問題 ❌

**症狀**: 前端聊天頁面沒有顯示任何 QA 回應

**可能原因**:

1. API 回應格式不符合前端預期
2. 前端 JavaScript 錯誤
3. 認證問題

---

## 📊 Embedding vs 關鍵字搜尋比較

| 特性         | Embedding 搜尋      | 關鍵字搜尋     |
| ------------ | ------------------- | -------------- |
| **準確度**   | 高（語義理解）      | 中（字面匹配） |
| **成本**     | 高（需 API 或自架） | 免費           |
| **速度**     | 慢（需計算向量）    | 快（直接 SQL） |
| **維護**     | 複雜                | 簡單           |
| **穩定性**   | 依賴外部服務        | 完全自主       |
| **適合場景** | 大規模語義搜尋      | 中小型專案     |

---

## 💡 建議的架構

### 方案 A: 純關鍵字搜尋（推薦）✅

**優點**:

- ✅ 完全免費
- ✅ 簡單穩定
- ✅ 無外部依賴
- ✅ 易於維護

**實作**:

```python
# 使用 PostgreSQL 全文搜尋
SELECT id, title, ai_summary, url
FROM articles
WHERE
  to_tsvector('english', title || ' ' || ai_summary)
  @@ to_tsquery('english', 'AI & technology')
ORDER BY ts_rank(
  to_tsvector('english', title || ' ' || ai_summary),
  to_tsquery('english', 'AI & technology')
) DESC
LIMIT 10;
```

**改進方向**:

1. 使用 PostgreSQL 全文搜尋索引
2. 改進關鍵字提取演算法
3. 加入同義詞擴展
4. 實作查詢快取

### 方案 B: 自架 Embedding 服務

**優點**:

- ✅ 完全免費
- ✅ 完全控制
- ✅ 無用量限制

**缺點**:

- ❌ 需要額外伺服器資源
- ❌ 維護成本高
- ❌ 技術門檻高

**實作**:

```python
# 使用 sentence-transformers 本地模型
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(texts)
```

**資源需求**:

- CPU: 2 核心
- RAM: 4GB
- 儲存: 500MB（模型大小）

### 方案 C: 付費 Embedding API

**選項**:

1. **OpenAI** - $0.0001/1K tokens
2. **HuggingFace Pro** - $9/月
3. **Cohere** - $1/1M tokens

**不推薦原因**:

- ❌ 需要付費
- ❌ 有用量限制
- ❌ 依賴外部服務

---

## 🏗️ 推薦的最終架構

```
用戶查詢
    ↓
API 端點 (/api/qa/query)
    ↓
SimpleQAAgent
    ↓
關鍵字提取
    ↓
PostgreSQL 全文搜尋
    ↓
相關性排序
    ↓
回應生成（使用 Groq LLM）
    ↓
返回結果
```

### 核心元件

1. **關鍵字提取器**
   - 中文：使用 jieba 分詞
   - 英文：使用 NLTK 或簡單的 split
   - 過濾停用詞
   - 提取重要詞彙

2. **全文搜尋**
   - PostgreSQL `tsvector` 和 `tsquery`
   - 建立 GIN 索引加速
   - 支援中英文搜尋

3. **相關性評分**
   - TF-IDF 評分
   - 標題權重加成
   - 時間衰減（新文章優先）

4. **回應生成**
   - 使用 Groq LLM 生成洞察
   - 基於搜尋結果生成建議
   - 保持回應簡潔有用

---

## 🔧 實作步驟

### 步驟 1: 移除 Embedding 相關程式碼

```bash
# 刪除或註解掉以下檔案
backend/app/qa_agent/huggingface_embeddings.py
backend/app/qa_agent/vector_store.py (embedding 相關部分)
```

### 步驟 2: 改進關鍵字搜尋

```python
# backend/app/qa_agent/keyword_search.py

import re
from typing import List

class KeywordExtractor:
    """改進的關鍵字提取器"""

    def __init__(self):
        self.stop_words_en = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
            'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were',
            'what', 'how', 'when', 'where', 'why', 'who'
        }
        self.stop_words_zh = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人',
            '都', '一', '一個', '上', '也', '很', '到', '說', '要', '去'
        }

    def extract(self, text: str, language: str = 'auto') -> List[str]:
        """提取關鍵字"""

        # 自動檢測語言
        if language == 'auto':
            chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
            language = 'zh' if chinese_chars > len(text) * 0.3 else 'en'

        if language == 'zh':
            return self._extract_chinese(text)
        else:
            return self._extract_english(text)

    def _extract_chinese(self, text: str) -> List[str]:
        """提取中文關鍵字"""
        # 提取中文詞彙和英文單詞
        words = re.findall(r'[A-Za-z]+|[一-龯]{2,}', text)

        # 過濾停用詞和短詞
        keywords = [
            word for word in words
            if len(word) > 1 and word not in self.stop_words_zh
        ]

        return keywords[:10]  # 最多10個關鍵字

    def _extract_english(self, text: str) -> List[str]:
        """提取英文關鍵字"""
        # 轉小寫並分詞
        words = text.lower().split()

        # 過濾停用詞和短詞
        keywords = [
            word.strip('.,!?;:') for word in words
            if len(word) > 2 and word not in self.stop_words_en
        ]

        return keywords[:10]  # 最多10個關鍵字
```

### 步驟 3: 實作全文搜尋

```python
# backend/app/qa_agent/fulltext_search.py

from typing import List, Dict, Any
from app.services.supabase_service import SupabaseService

class FullTextSearch:
    """PostgreSQL 全文搜尋"""

    def __init__(self):
        self.supabase = SupabaseService()

    async def search(
        self,
        keywords: List[str],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """使用關鍵字搜尋文章"""

        if not keywords:
            return []

        # 建立搜尋條件
        conditions = []
        for keyword in keywords:
            conditions.append(f"title.ilike.%{keyword}%")
            conditions.append(f"ai_summary.ilike.%{keyword}%")

        # 執行搜尋
        result = self.supabase.client.table("articles").select(
            "id, title, ai_summary, url, published_at"
        ).or_(",".join(conditions)).limit(limit).execute()

        return result.data
```

### 步驟 4: 建立資料庫索引

```sql
-- 為全文搜尋建立索引
CREATE INDEX IF NOT EXISTS idx_articles_title_gin
ON articles USING gin(to_tsvector('english', title));

CREATE INDEX IF NOT EXISTS idx_articles_summary_gin
ON articles USING gin(to_tsvector('english', ai_summary));

-- 複合索引
CREATE INDEX IF NOT EXISTS idx_articles_fulltext_gin
ON articles USING gin(to_tsvector('english', title || ' ' || COALESCE(ai_summary, '')));
```

---

## 📈 預期效果

### 效能指標

| 指標         | 目標  | 說明                 |
| ------------ | ----- | -------------------- |
| 查詢回應時間 | < 1s  | 關鍵字搜尋非常快     |
| 搜尋準確率   | > 70% | 對於明確關鍵字很準確 |
| 系統穩定性   | 99.9% | 無外部依賴           |
| 成本         | $0    | 完全免費             |

### 使用者體驗

- ✅ 快速回應
- ✅ 相關結果
- ✅ 穩定可靠
- ⚠️ 語義理解較弱（可接受）

---

## 🎯 結論

### 當前狀況

1. ❌ HuggingFace 免費 API 不可用
2. ❌ Embedding 功能無法運作
3. ✅ Simple QA Agent 基本功能正常
4. ⚠️ 前端顯示有問題（需要修復）

### 建議行動

1. **立即**: 移除 embedding 相關程式碼
2. **短期**: 改進關鍵字搜尋演算法
3. **中期**: 實作 PostgreSQL 全文搜尋
4. **長期**: 如有需要，考慮自架 embedding 服務

### 最終建議

**對於你的專案，純關鍵字搜尋就足夠了！**

理由：

- ✅ 完全免費
- ✅ 簡單穩定
- ✅ 易於維護
- ✅ 效果足夠好（對於中小型專案）

Embedding 只有在以下情況才值得：

- 大規模文章庫（> 10萬篇）
- 需要精確的語義理解
- 有預算和資源維護

---

**下一步**: 我可以幫你實作改進的關鍵字搜尋系統，並修復前端顯示問題。要繼續嗎？
