# CI 快速開始指南

## 🚀 推送前檢查（必讀）

在推送程式碼前，**務必**執行以下命令：

```bash
# 1. 自動修復格式問題
./scripts/ci-fix.sh

# 2. 執行完整 CI 檢查
./scripts/ci-local-test.sh
```

如果所有檢查都通過，就可以安全推送了！

## 📋 CI 檢查項目

### Backend

- ✅ Black 格式化
- ✅ Ruff linting
- ✅ mypy 類型檢查
- ✅ pytest 測試 + 覆蓋率 ≥ 70%

### Frontend

- ✅ Prettier 格式化
- ✅ ESLint linting
- ✅ TypeScript 類型檢查
- ✅ Vitest 測試 + 覆蓋率 ≥ 70%
- ✅ Next.js 建置

## 🔧 常見問題快速修復

### Black 格式錯誤

```bash
cd backend && black app/ tests/
```

### Ruff linting 錯誤

```bash
cd backend && ruff check --fix app/ tests/
```

### Prettier 格式錯誤

```bash
cd frontend && npm run format
```

### ESLint 錯誤

```bash
cd frontend && npm run lint:fix
```

### TypeScript 錯誤

```bash
cd frontend && rm -rf .next && npm run type-check
```

## 📚 詳細文件

需要更多資訊？查看 [完整 CI 指南](./CI_GUIDE.md)

## ⚡ 工作流程

```bash
# 1. 開發功能
git checkout -b feature/my-feature

# 2. 自動修復
./scripts/ci-fix.sh

# 3. 本地測試
./scripts/ci-local-test.sh

# 4. 提交推送
git add .
git commit -m "feat: add my feature"
git push origin feature/my-feature
```

## 🎯 CI 執行時間

- Backend: ~2-3 分鐘
- Frontend: ~3-4 分鐘
- 總計: ~5 分鐘

## 💡 小技巧

1. **使用 pre-commit hooks** - 自動在提交前執行檢查
2. **並行開發** - Backend 和 Frontend 可以分開測試
3. **快取依賴** - CI 使用快取加速執行
4. **監控 CI** - 在 GitHub Actions 查看詳細日誌

---

**有問題？** 查看 [CI 指南](./CI_GUIDE.md) 或建立 Issue
