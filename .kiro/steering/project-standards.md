---
inclusion: always
---

# 專案規範與標準

這份文件定義了本專案的基本規範和要求，所有開發工作都應遵循這些標準。

## 📁 檔案組織規範

### 🎯 核心原則

**所有專案文件必須統一放在 `docs/` 資料夾中**，根目錄只保留必要的專案說明檔案。

### 📂 標準目錄結構

```
docs/
├── README.md                    # 📋 文件索引與導航
├── api/                        # 🔌 API 相關文件
│   ├── contracts/              # API 合約與規格
│   └── examples/               # API 使用範例
├── architecture/               # 🏗️ 系統架構文件
│   ├── decisions/              # 架構決策記錄 (ADR)
│   ├── diagrams/               # 架構圖表
│   └── patterns/               # 設計模式
├── backend/                    # ⚙️ 後端相關文件
│   ├── database/               # 資料庫設計與遷移
│   ├── services/               # 服務層文件
│   └── integrations/           # 第三方整合
├── frontend/                   # 🎨 前端相關文件
│   ├── components/             # 元件設計文件
│   ├── ui-ux/                  # UI/UX 設計指南
│   └── styling/                # 樣式規範
├── ci/                         # 🔄 CI/CD 相關文件
│   ├── workflows/              # 工作流程說明
│   ├── deployment/             # 部署相關
│   └── testing/                # 測試策略
├── deployment/                 # 🚀 部署文件
│   ├── environments/           # 環境配置
│   ├── procedures/             # 部署程序
│   └── rollback/               # 回滾程序
├── development/                # 💻 開發相關文件
│   ├── setup/                  # 開發環境設置
│   ├── workflows/              # 開發工作流程
│   ├── standards/              # 編碼標準
│   └── tools/                  # 開發工具
├── features/                   # ✨ 功能相關文件
│   ├── specifications/         # 功能規格
│   ├── user-stories/           # 用戶故事
│   └── acceptance-criteria/    # 驗收標準
├── fixes/                      # 🔧 修復相關文件
│   ├── bug-reports/            # 錯誤報告
│   ├── hotfixes/               # 緊急修復
│   └── patches/                # 補丁說明
├── guides/                     # 📖 使用指南
│   ├── user/                   # 用戶指南
│   ├── admin/                  # 管理員指南
│   └── developer/              # 開發者指南
├── implementation/             # 🛠️ 實作相關文件
│   ├── tasks/                  # 任務完成記錄
│   ├── progress/               # 進度追蹤
│   └── reviews/                # 實作審查
├── improvements/               # 📈 改進相關文件
│   ├── proposals/              # 改進提案
│   ├── performance/            # 性能優化
│   └── refactoring/            # 重構計劃
├── migrations/                 # 🔄 遷移相關文件
│   ├── database/               # 資料庫遷移
│   ├── data/                   # 資料遷移
│   └── system/                 # 系統遷移
├── setup/                      # ⚡ 設置相關文件
│   ├── installation/           # 安裝指南
│   ├── configuration/          # 配置說明
│   └── environment/            # 環境變數
├── tasks/                      # ✅ 任務相關文件
│   ├── completed/              # 已完成任務
│   ├── in-progress/            # 進行中任務
│   └── planning/               # 任務規劃
├── testing/                    # 🧪 測試相關文件
│   ├── strategies/             # 測試策略
│   ├── cases/                  # 測試案例
│   ├── automation/             # 自動化測試
│   └── reports/                # 測試報告
├── troubleshooting/            # 🚨 故障排除
│   ├── common-issues/          # 常見問題
│   ├── debugging/              # 除錯指南
│   └── monitoring/             # 監控相關
└── ux-improvements/            # 🎯 UX 改進文件
    ├── research/               # 用戶研究
    ├── feedback/               # 用戶反饋
    └── iterations/             # 迭代改進
```

### 📋 檔案組織規則

#### ✅ **必須遵循 (DO)**

1. **統一存放**: 所有 `.md` 文件必須放在 `docs/` 對應的子資料夾中
2. **維護索引**: 在 `docs/README.md` 中維護完整的文件索引和導航
3. **分類明確**: 根據文件性質放入對應的子資料夾
4. **命名規範**: 使用 kebab-case 命名，如 `api-authentication.md`
5. **內容更新**: 定期檢查和更新文件內容，移除過時資訊
6. **交叉引用**: 在相關文件間建立適當的連結和引用

#### ❌ **嚴格禁止 (DON'T)**

1. **散落文件**: 不可在專案根目錄或其他資料夾散落 `.md` 文件
2. **臨時文件**: 不可創建臨時文件而不整理到 `docs/` 中
3. **重複文件**: 避免在不同位置創建內容重複的文件
4. **無分類**: 不可將文件直接放在 `docs/` 根目錄下
5. **空白資料夾**: 不可創建空的子資料夾
6. **混亂命名**: 避免使用空格、特殊字符或不明確的檔名

### 🏠 根目錄例外情況

**只有以下文件可以放在專案根目錄：**

- `README.md` - 專案主要說明（英文版）
- `README_zh.md` - 專案主要說明（中文版）
- `CHANGELOG.md` - 版本變更記錄
- `CONTRIBUTING.md` - 貢獻指南
- `LICENSE` - 授權文件
- `CODE_OF_CONDUCT.md` - 行為準則
- `.gitignore` - Git 忽略規則
- 配置文件（如 `package.json`, `requirements.txt`, `Dockerfile` 等）

**⚠️ 重要提醒**: 更新 README 時，必須同時更新 `README.md` 和 `README_zh.md` 兩個檔案，保持內容同步。

## 📝 命名規範

### 檔案命名標準

#### ✅ **正確做法**

- 使用 **kebab-case**: `project-standards.md`, `api-authentication.md`
- 使用有意義的名稱: `user-authentication-guide.md` 而非 `doc1.md`
- 包含版本資訊（如需要）: `api-v2-migration-guide.md`
- 使用英文命名: `database-schema.md` 而非 `資料庫架構.md`

#### ❌ **錯誤做法**

- 使用空格: `project standards.md`
- 使用特殊字符: `project@standards.md`, `project#1.md`
- 使用中文檔名: `專案標準.md`
- 使用無意義名稱: `temp.md`, `doc1.md`, `新文件.md`

### 資料夾命名標準

#### ✅ **正確做法**

- 使用小寫 kebab-case: `user-guides/`, `api-documentation/`
- 使用複數形式: `guides/` 而非 `guide/`, `components/` 而非 `component/`
- 使用描述性名稱: `troubleshooting/` 而非 `issues/`

#### ❌ **錯誤做法**

- 使用大寫: `API/`, `GUIDES/`
- 使用底線: `user_guides/`, `api_docs/`
- 使用中文: `指南/`, `文件/`

### 內容標題規範

#### Markdown 標題層級

```markdown
# H1 - 文件主標題（每個文件只能有一個）

## H2 - 主要章節

### H3 - 子章節

#### H4 - 詳細說明

##### H5 - 細節補充

###### H6 - 最小層級（盡量避免使用）
```

#### 標題命名原則

- 使用清晰、描述性的標題
- 避免使用過長的標題（建議 50 字元以內）
- 使用一致的大小寫風格
- 在標題中使用適當的 emoji 提升可讀性（但不要過度使用）

## 🔧 程式碼規範

### Python 規範

#### 基本要求

- 嚴格遵循 **PEP 8** 編碼風格
- 使用 **type hints** 進行型別標註
- 使用 **ruff** 進行程式碼檢查和格式化
- 使用 **mypy** 進行靜態型別檢查
- 使用 **pytest** 進行單元測試

#### 程式碼品質標準

```python
# ✅ 正確範例
from typing import List, Optional

def process_user_data(
    user_ids: List[int],
    include_inactive: bool = False
) -> Optional[List[dict]]:
    """處理用戶資料並返回結果。

    Args:
        user_ids: 用戶 ID 列表
        include_inactive: 是否包含非活躍用戶

    Returns:
        處理後的用戶資料列表，如果沒有資料則返回 None
    """
    if not user_ids:
        return None

    # 實作邏輯...
    return processed_data
```

### TypeScript/JavaScript 規範

#### 基本要求

- 使用 **ESLint + Prettier** 進行程式碼檢查和格式化
- **優先使用 TypeScript** 而非純 JavaScript
- 使用 **functional components** (React)
- 遵循 **React Hooks** 最佳實踐
- 使用 **strict mode** TypeScript 配置

#### 程式碼品質標準

```typescript
// ✅ 正確範例
interface UserData {
  id: number;
  name: string;
  email: string;
  isActive?: boolean;
}

const UserProfile: React.FC<{ userId: number }> = ({ userId }) => {
  const [userData, setUserData] = useState<UserData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchUserData = async (): Promise<void> => {
      try {
        const data = await getUserById(userId);
        setUserData(data);
      } catch (error) {
        console.error('Failed to fetch user data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, [userId]);

  if (loading) return <div>Loading...</div>;
  if (!userData) return <div>User not found</div>;

  return (
    <div className="user-profile">
      <h2>{userData.name}</h2>
      <p>{userData.email}</p>
    </div>
  );
};
```

### 通用程式碼規範

#### 註解與文件

- 使用英文撰寫註解和文件字串
- 為複雜邏輯添加解釋性註解
- 為所有公開函數/方法添加文件字串
- 避免無意義的註解（如 `// 增加 1`）

#### 錯誤處理

- 使用適當的例外處理機制
- 提供有意義的錯誤訊息
- 記錄重要的錯誤資訊
- 避免忽略例外情況

#### 效能考量

- 避免不必要的重複計算
- 使用適當的資料結構
- 考慮記憶體使用效率
- 進行適當的快取策略

## 📚 文件撰寫規範

### Markdown 格式標準

#### 結構要求

- 使用清晰的標題層級 (H1 → H2 → H3 → H4)
- 為長文件（超過 10 個章節）添加目錄 (TOC)
- 使用程式碼區塊並標註正確的語言
- 添加適當的 emoji 提升可讀性（但不要過度使用）
- 使用表格整理結構化資訊
- 添加適當的連結和交叉引用

#### 格式範例

````markdown
# 📋 文件標題

## 📖 目錄

- [概述](#概述)
- [安裝指南](#安裝指南)
- [使用方法](#使用方法)
- [故障排除](#故障排除)

## 🎯 概述

簡潔明瞭的概述內容...

## ⚡ 安裝指南

### 前置需求

- Node.js >= 18.0.0
- Python >= 3.9

### 安裝步驟

```bash
npm install
pip install -r requirements.txt
```
````

## 🚀 使用方法

詳細的使用說明...

## 🔧 故障排除

| 問題     | 原因     | 解決方案     |
| -------- | -------- | ------------ |
| 連線失敗 | 網路問題 | 檢查網路設定 |

```

### 內容撰寫標準

#### ✅ **優質內容特徵**
- **簡潔明瞭**: 避免冗長的句子和段落
- **實用導向**: 提供實際可操作的範例和步驟
- **邏輯清晰**: 按照邏輯順序組織內容
- **完整性**: 涵蓋所有必要的資訊
- **時效性**: 定期更新過時內容
- **可搜尋**: 使用適當的關鍵字和標籤

#### 📝 **撰寫原則**
1. **說明「為什麼」而不只是「怎麼做」**: 解釋背後的原理和動機
2. **提供完整範例**: 包含輸入、處理過程和預期輸出
3. **考慮不同層級的讀者**: 提供基礎和進階兩種說明
4. **使用一致的術語**: 建立並維護術語表
5. **添加視覺輔助**: 適當使用圖表、截圖和流程圖

### 文件類型規範

#### 📖 **使用者指南 (User Guides)**
- 面向終端使用者
- 重點在於功能使用和操作流程
- 包含截圖和步驟說明
- 提供常見問題解答

#### 🛠️ **開發者文件 (Developer Documentation)**
- 面向開發人員
- 包含 API 文件、程式碼範例
- 說明架構設計和技術決策
- 提供開發環境設置指南

#### 🏗️ **架構文件 (Architecture Documentation)**
- 描述系統整體架構
- 包含架構圖和元件關係
- 說明設計原則和約束條件
- 記錄重要的技術決策 (ADR)

#### 🔧 **操作手冊 (Operation Manuals)**
- 面向系統管理員
- 包含部署、監控、維護程序
- 提供故障排除指南
- 記錄緊急處理程序

## 🎯 開發流程規範

### 新功能開發流程

#### 1. 📋 需求分析階段
- 在 `.kiro/specs/` 創建功能規格文件
- 定義用戶故事和驗收標準
- 進行技術可行性評估
- 估算開發時間和資源需求

#### 2. 🏗️ 設計階段
- 創建架構設計文件
- 設計 API 介面和資料模型
- 制定測試策略
- 進行設計審查

#### 3. 💻 實作階段
- 遵循編碼規範進行開發
- 編寫單元測試和整合測試
- 進行程式碼審查 (Code Review)
- 更新相關文件

#### 4. 📚 文件更新階段
- 在 `docs/` 添加功能相關文件
- 更新 `docs/README.md` 索引
- 更新 API 文件和使用指南
- 記錄重要的技術決策

#### 5. ✅ 驗證階段
- 執行完整的測試套件
- 進行用戶驗收測試
- 檢查文件完整性
- 準備部署計劃

### 重構流程

#### 📝 **重構前準備**
1. **記錄重構原因和目標**
   - 在 `docs/improvements/refactoring/` 創建重構計劃
   - 說明現有問題和預期改善
   - 評估重構風險和影響範圍

2. **建立基準測試**
   - 確保現有功能的測試覆蓋率
   - 記錄效能基準數據
   - 建立回滾計劃

#### 🔄 **重構執行**
1. **小步驟迭代**
   - 將大型重構分解為小步驟
   - 每個步驟都要保持系統可運行
   - 頻繁提交和測試

2. **文件同步更新**
   - 在 `docs/architecture/decisions/` 添加 ADR
   - 更新相關的技術文件
   - 記錄重構過程中的重要發現

#### ✅ **重構後驗證**
- 執行完整的回歸測試
- 驗證效能改善
- 更新部署文件
- 進行團隊知識分享

### 版本控制規範

#### Git 提交訊息格式
```

<type>(<scope>): <subject>

<body>

<footer>
```

#### 提交類型 (type)

- `feat`: 新功能
- `fix`: 錯誤修復
- `docs`: 文件更新
- `style`: 程式碼格式調整
- `refactor`: 重構
- `test`: 測試相關
- `chore`: 建置或輔助工具變動

#### 範例

```
feat(auth): add OAuth2 authentication support

- Implement OAuth2 flow for Google and GitHub
- Add user profile synchronization
- Update authentication middleware

Closes #123
```

### 程式碼審查規範

#### 審查重點

- **功能正確性**: 程式碼是否實現預期功能
- **程式碼品質**: 是否遵循編碼規範
- **效能考量**: 是否存在效能問題
- **安全性**: 是否存在安全漏洞
- **可維護性**: 程式碼是否易於理解和維護
- **測試覆蓋**: 是否有足夠的測試

#### 審查流程

1. 自我審查：提交前先自行檢查
2. 同儕審查：至少一位同事進行審查
3. 技術領導審查：重要變更需要技術領導確認
4. 自動化檢查：通過所有 CI/CD 檢查

## ⚠️ 常見錯誤與最佳實踐

### 📁 檔案組織常見錯誤

#### ❌ **錯誤做法範例**

**散落的文件結構:**

```
project/
├── backend/some-doc.md          # ❌ 後端文件散落
├── frontend/notes.md            # ❌ 前端筆記散落
├── random-file.md               # ❌ 隨意放置的文件
├── temp-notes.md                # ❌ 臨時文件未整理
├── 新功能說明.md                # ❌ 中文檔名
├── API DOC.md                   # ❌ 檔名有空格
└── fix@urgent.md                # ❌ 特殊字符
```

#### ✅ **正確做法範例**

**整齊的文件結構:**

```
project/
├── docs/
│   ├── README.md                # ✅ 文件索引
│   ├── backend/
│   │   └── api-documentation.md # ✅ 分類清楚
│   ├── frontend/
│   │   └── component-guide.md   # ✅ 命名規範
│   ├── features/
│   │   └── new-feature-spec.md  # ✅ 英文檔名
│   ├── fixes/
│   │   └── urgent-bug-fix.md    # ✅ 描述性檔名
│   └── guides/
│       └── api-usage-guide.md   # ✅ 有意義的名稱
├── README.md                    # ✅ 專案說明
└── README_zh.md                 # ✅ 中文版說明
```

### 📝 文件撰寫常見錯誤

#### ❌ **內容品質問題**

- 缺乏目錄和導航
- 沒有實際可用的範例
- 過時的資訊未更新
- 只說「怎麼做」不說「為什麼」
- 術語不一致
- 缺乏錯誤處理說明

#### ✅ **高品質文件特徵**

- 有清晰的目錄結構
- 提供完整的程式碼範例
- 定期檢查和更新內容
- 解釋設計決策的原因
- 建立並維護術語表
- 包含故障排除章節

### 🔧 開發流程常見問題

#### ❌ **流程問題**

- 直接修改程式碼不寫文件
- 重構後不更新相關文件
- 新功能沒有對應的使用說明
- 修復問題後不記錄解決方案
- 缺乏程式碼審查流程

#### ✅ **最佳實踐**

- 程式碼和文件同步更新
- 重要變更都有對應的 ADR
- 每個功能都有使用指南
- 建立知識庫記錄解決方案
- 建立完整的審查機制

### 🚨 緊急情況處理

#### 緊急修復流程

1. **立即修復**: 優先解決緊急問題
2. **臨時文件**: 可暫時在根目錄創建緊急文件
3. **後續整理**: 問題解決後 24 小時內整理文件到 `docs/`
4. **經驗記錄**: 在 `docs/troubleshooting/` 記錄問題和解決方案

#### 緊急文件命名

- 使用 `URGENT_` 前綴: `URGENT_DATABASE_FIX.md`
- 包含日期: `URGENT_20241222_API_DOWN.md`
- 問題解決後重新命名並移動到適當位置

### 📋 文件索引維護

#### ✅ **索引最佳實踐**

- 在 `docs/README.md` 維護完整的文件索引
- 按照邏輯分類組織連結
- 為每個文件添加簡短描述
- 定期檢查連結的有效性
- 使用表格或清單格式提升可讀性

#### 📊 **索引範例格式**

```markdown
# 📚 文件索引

## 🚀 快速開始

- [安裝指南](setup/installation-guide.md) - 完整的環境設置步驟
- [快速開始](guides/quick-start.md) - 5 分鐘快速上手指南

## 🏗️ 架構文件

- [系統架構](architecture/system-overview.md) - 整體架構設計
- [資料庫設計](architecture/database-schema.md) - 資料模型說明

## 📖 開發指南

- [編碼規範](development/coding-standards.md) - 程式碼風格指南
- [API 文件](api/api-reference.md) - 完整的 API 參考
```

## 🔄 定期維護與檢查

### 📅 **每週檢查項目**

- [ ] 檢查是否有新的散落文件需要整理
- [ ] 驗證 `docs/README.md` 索引的完整性
- [ ] 檢查最近更新的文件是否分類正確

### 📅 **每月檢查項目**

- [ ] 全面檢查 `docs/` 資料夾結構
- [ ] 移除過時文件或標記為 deprecated
- [ ] 更新文件索引和交叉引用
- [ ] 確保所有文件都在正確位置
- [ ] 檢查檔案命名是否符合規範

### 📅 **每季檢查項目**

- [ ] 評估文件結構是否需要調整
- [ ] 檢查文件內容的時效性
- [ ] 更新專案規範文件
- [ ] 進行文件品質審查

### 🛠️ **維護工具與腳本**

建議創建以下維護腳本：

```bash
# 檢查散落文件的腳本
find . -name "*.md" -not -path "./docs/*" -not -name "README*.md" -not -name "CHANGELOG.md" -not -name "CONTRIBUTING.md"

# 檢查空資料夾的腳本
find docs/ -type d -empty

# 檢查檔名規範的腳本
find docs/ -name "*.md" | grep -E "[ @#]"
```

---

**🎯 記住**: 良好的文件組織是專案可維護性的關鍵！定期維護和檢查能確保專案文件始終保持整潔和有用。

```

project/
├── backend/some-doc.md
├── frontend/notes.md
└── random-file.md

```

✅ **正確做法**:

```

project/
├── docs/
│ ├── backend/some-doc.md
│ ├── frontend/notes.md
│ └── notes/random-file.md
└── README.md

```

### 缺乏索引

- 在 `docs/README.md` 維護完整的文件索引
- 讓團隊成員能快速找到需要的文件

## 🔄 定期維護

- 每月檢查 `docs/` 資料夾
- 移除過時文件或標記為 deprecated
- 更新文件索引
- 確保所有文件都在正確位置

---

**記住**: 良好的文件組織是專案可維護性的關鍵！

```

```
