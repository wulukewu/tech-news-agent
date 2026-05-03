# 提交指南

## 🚀 推送前檢查清單

在每次推送前，請執行以下步驟：

### 1. 自動修復格式問題

```bash
./scripts/ci-fix.sh
```

這會自動修復：

- ✅ Black 格式化（Python）
- ✅ Ruff linting（Python）
- ✅ Prettier 格式化（TypeScript/JavaScript）
- ✅ ESLint 問題（TypeScript/JavaScript）

### 2. 執行完整 CI 檢查

```bash
./scripts/ci-local-test.sh
```

這會執行所有 CI 檢查：

- ✅ 程式碼格式化
- ✅ Linting
- ✅ 類型檢查
- ✅ 測試 + 覆蓋率
- ✅ 建置驗證

### 3. 查看變更

```bash
git status
git diff
```

確認所有變更都是預期的。

### 4. 提交並推送

```bash
git add .
git commit -m "feat: your feature description"
git push
```

## 📝 Commit Message 格式

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type

- `feat`: 新功能
- `fix`: 錯誤修復
- `docs`: 文件變更
- `style`: 格式化（不影響程式碼運行）
- `refactor`: 重構
- `test`: 測試相關
- `chore`: 建置過程或輔助工具變更

### 範例

```bash
# 新功能
git commit -m "feat(api): add user profile endpoint"

# 錯誤修復
git commit -m "fix(auth): resolve token expiration issue"

# 文件更新
git commit -m "docs(readme): update installation instructions"

# 重構
git commit -m "refactor(services): simplify article fetching logic"
```

## 🔍 如果 CI 失敗

### 1. 查看錯誤

在 GitHub Actions 查看詳細錯誤訊息。

### 2. 本地重現

```bash
./scripts/ci-local-test.sh
```

### 3. 修復問題

```bash
# 自動修復
./scripts/ci-fix.sh

# 或手動修復
```

### 4. 重新測試

```bash
./scripts/ci-local-test.sh
```

### 5. 推送修復

```bash
git add .
git commit -m "fix(ci): resolve formatting issues"
git push
```

## 📚 更多資訊

- [CI 快速開始](./docs/ci/QUICK_START.md)
- [CI 完整指南](./docs/ci/CI_GUIDE.md)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

**記住**: 永遠在推送前執行 `./scripts/ci-local-test.sh`！
