# CI/CD 指南

本文件說明專案的 CI/CD 流程、如何在本地測試，以及如何修復常見問題。

## 📋 目錄

- [CI 流程概覽](#ci-流程概覽)
- [本地測試](#本地測試)
- [自動修復](#自動修復)
- [CI 檢查項目](#ci-檢查項目)
- [常見問題](#常見問題)
- [最佳實踐](#最佳實踐)

## CI 流程概覽

### 觸發條件

CI 會在以下情況自動執行：

- Push 到 `main` 或 `develop` 分支
- 對 `main` 或 `develop` 分支發起 Pull Request

### 執行流程

```
┌─────────────┐     ┌──────────────┐
│   Backend   │     │   Frontend   │
│   Checks    │     │    Checks    │
└──────┬──────┘     └──────┬───────┘
       │                   │
       └────────┬──────────┘
                │
         ┌──────▼──────┐
         │ Quality Gate│
         └─────────────┘
```

### 並行執行

- Backend 和 Frontend 檢查**並行執行**，節省時間
- 只有兩者都通過，Quality Gate 才會通過

## 本地測試

### 快速測試（推薦）

在推送前執行完整的 CI 檢查：

```bash
./scripts/ci-local-test.sh
```

這個腳本會：

- ✅ 執行所有 CI 檢查（格式、linting、類型檢查、測試）
- ✅ 顯示詳細的錯誤訊息
- ✅ 提供修復建議
- ✅ 完全模擬 GitHub Actions 環境

### 分別測試

#### Backend 測試

```bash
cd backend

# 格式檢查
black --check app/ tests/

# Linting
ruff check app/ tests/

# 類型檢查
mypy app/ --ignore-missing-imports --no-strict-optional --python-version=3.11

# 測試
pytest -v --cov=app
```

#### Frontend 測試

```bash
cd frontend

# 格式檢查
npm run format:check

# Linting
npm run lint

# 類型檢查
npm run type-check

# 測試
npm run test:coverage

# 建置
npm run build
```

## 自動修復

### 一鍵修復

自動修復常見的格式和 linting 問題：

```bash
./scripts/ci-fix.sh
```

這個腳本會：

- 🔧 自動格式化 Python 程式碼（Black）
- 🔧 自動修復 Ruff 問題
- 🔧 自動格式化 TypeScript/JavaScript 程式碼（Prettier）
- 🔧 自動修復 ESLint 問題

### 手動修復

#### Backend

```bash
cd backend

# 格式化
black app/ tests/

# 修復 Ruff 問題
ruff check --fix app/ tests/
```

#### Frontend

```bash
cd frontend

# 格式化
npm run format

# 修復 ESLint 問題
npm run lint:fix
```

## CI 檢查項目

### Backend 檢查

| 檢查項目   | 工具       | 說明                          |
| ---------- | ---------- | ----------------------------- |
| 程式碼格式 | Black      | 確保程式碼符合 PEP 8 格式規範 |
| Linting    | Ruff       | 檢查程式碼品質和潛在問題      |
| 類型檢查   | mypy       | 驗證類型註解的正確性          |
| 單元測試   | pytest     | 執行所有測試並生成覆蓋率報告  |
| 覆蓋率     | pytest-cov | 確保測試覆蓋率 ≥ 70%          |

### Frontend 檢查

| 檢查項目   | 工具       | 說明                         |
| ---------- | ---------- | ---------------------------- |
| 程式碼格式 | Prettier   | 確保程式碼格式一致           |
| Linting    | ESLint     | 檢查程式碼品質和潛在問題     |
| 類型檢查   | TypeScript | 驗證類型的正確性             |
| 單元測試   | Vitest     | 執行所有測試並生成覆蓋率報告 |
| 覆蓋率     | Vitest     | 確保測試覆蓋率 ≥ 70%         |
| 建置       | Next.js    | 確保應用程式可以成功建置     |

## 常見問題

### 1. Black 格式檢查失敗

**錯誤訊息：**

```
would reformat app/main.py
```

**解決方法：**

```bash
cd backend
black app/ tests/
```

### 2. Ruff Linting 失敗

**錯誤訊息：**

```
app/main.py:10:1: F401 [*] `os` imported but unused
```

**解決方法：**

```bash
cd backend
ruff check --fix app/ tests/
```

### 3. mypy 類型檢查失敗

**錯誤訊息：**

```
app/main.py:10: error: Incompatible return value type
```

**解決方法：**

- 檢查函數的返回類型註解
- 確保返回值與註解一致
- 如果是第三方套件問題，可能需要安裝 type stubs

### 4. Prettier 格式檢查失敗

**錯誤訊息：**

```
Code style issues found in the above file(s).
```

**解決方法：**

```bash
cd frontend
npm run format
```

### 5. ESLint 失敗

**錯誤訊息：**

```
'React' is defined but never used
```

**解決方法：**

```bash
cd frontend
npm run lint:fix
```

### 6. TypeScript 類型檢查失敗

**錯誤訊息：**

```
Property 'email' does not exist on type 'User'
```

**解決方法：**

- 檢查類型定義
- 確保所有必要的屬性都已定義
- 清除 Next.js 快取：`rm -rf .next`

### 7. 測試失敗

**解決方法：**

```bash
# Backend
cd backend
pytest -v  # 查看詳細錯誤訊息

# Frontend
cd frontend
npm test  # 查看詳細錯誤訊息
```

### 8. 覆蓋率不足

**錯誤訊息：**

```
Coverage: 65.5% (threshold: 70%)
```

**解決方法：**

- 為未覆蓋的程式碼添加測試
- 或者調整覆蓋率閾值（不推薦）

### 9. 建置失敗

**錯誤訊息：**

```
Error: Failed to compile
```

**解決方法：**

```bash
cd frontend
rm -rf .next node_modules
npm install
npm run build
```

## 最佳實踐

### 推送前檢查清單

在推送程式碼前，請確保：

- [ ] 執行 `./scripts/ci-local-test.sh` 並通過所有檢查
- [ ] 所有測試都通過
- [ ] 程式碼已格式化
- [ ] 沒有 linting 錯誤
- [ ] 沒有類型錯誤
- [ ] 測試覆蓋率達標

### 開發工作流程

1. **開發功能**

   ```bash
   # 正常開發...
   ```

2. **自動修復格式問題**

   ```bash
   ./scripts/ci-fix.sh
   ```

3. **本地測試**

   ```bash
   ./scripts/ci-local-test.sh
   ```

4. **提交並推送**

   ```bash
   git add .
   git commit -m "feat: add new feature"
   git push
   ```

5. **監控 CI**
   - 前往 GitHub Actions 查看 CI 執行狀態
   - 如果失敗，查看錯誤訊息並修復

### 加速 CI 執行

CI 已經優化為：

- ✅ 使用快取（pip、npm）
- ✅ 並行執行 Backend 和 Frontend 檢查
- ✅ 使用 `pytest -n auto` 並行執行測試
- ✅ 取消進行中的重複執行（concurrency）

### 環境變數

CI 使用 dummy 環境變數執行測試，因為所有外部呼叫都已 mock：

```yaml
SUPABASE_URL: https://dummy.supabase.co
SUPABASE_KEY: dummy_supabase_key
DISCORD_TOKEN: dummy_discord_token
GROQ_API_KEY: dummy_groq_api_key
```

這些值不需要是真實的，因為測試不會實際呼叫外部服務。

## 故障排除

### CI 通過但本地失敗

可能原因：

- 本地環境與 CI 環境不同
- 快取問題

解決方法：

```bash
# Backend
cd backend
rm -rf .pytest_cache .mypy_cache .ruff_cache
pip install -r requirements.txt -r requirements-dev.txt

# Frontend
cd frontend
rm -rf .next node_modules
npm install
```

### 本地通過但 CI 失敗

可能原因：

- 未提交所有變更
- Git 忽略了某些檔案

解決方法：

```bash
git status  # 檢查未提交的變更
git add .   # 添加所有變更
```

### CI 執行時間過長

正常執行時間：

- Backend: 2-3 分鐘
- Frontend: 3-4 分鐘
- 總計: 約 5 分鐘

如果超過 10 分鐘，可能是：

- GitHub Actions runner 負載過高
- 網路問題
- 測試卡住

解決方法：

- 取消並重新執行
- 檢查測試是否有無限迴圈

## 相關資源

- [GitHub Actions 文件](https://docs.github.com/en/actions)
- [Black 文件](https://black.readthedocs.io/)
- [Ruff 文件](https://docs.astral.sh/ruff/)
- [mypy 文件](https://mypy.readthedocs.io/)
- [Prettier 文件](https://prettier.io/)
- [ESLint 文件](https://eslint.org/)
- [pytest 文件](https://docs.pytest.org/)
- [Vitest 文件](https://vitest.dev/)

## 需要幫助？

如果遇到問題：

1. 查看本文件的[常見問題](#常見問題)章節
2. 執行 `./scripts/ci-local-test.sh` 查看詳細錯誤
3. 查看 GitHub Actions 的詳細日誌
4. 在專案 Issues 中搜尋類似問題
5. 建立新的 Issue 並附上錯誤訊息

---

**最後更新**: 2026-04-18
