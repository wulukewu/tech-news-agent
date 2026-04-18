# CI/CD 文件索引

本目錄包含專案的 CI/CD 相關文件。

## 📚 文件列表

### 快速開始

- **[QUICK_START.md](./QUICK_START.md)** - CI 快速開始指南（推薦新手閱讀）
  - 推送前檢查清單
  - 常見問題快速修復
  - 基本工作流程

### 完整指南

- **[CI_GUIDE.md](./CI_GUIDE.md)** - 完整 CI/CD 指南
  - CI 流程詳解
  - 所有檢查項目說明
  - 詳細故障排除
  - 最佳實踐

## 🚀 快速命令

```bash
# 自動修復格式問題
./scripts/ci-fix.sh

# 執行完整 CI 檢查
./scripts/ci-local-test.sh
```

## 📊 CI 架構

```
GitHub Actions CI
├── Backend Job (並行)
│   ├── Black 格式化
│   ├── Ruff linting
│   ├── mypy 類型檢查
│   └── pytest 測試 + 覆蓋率
│
├── Frontend Job (並行)
│   ├── Prettier 格式化
│   ├── ESLint linting
│   ├── TypeScript 類型檢查
│   ├── Vitest 測試 + 覆蓋率
│   └── Next.js 建置
│
└── Quality Gate
    └── 確保所有檢查通過
```

## 🎯 設計原則

1. **快速反饋** - 並行執行，5 分鐘內完成
2. **本地優先** - 推送前在本地驗證
3. **自動修復** - 提供自動修復腳本
4. **清晰錯誤** - 詳細的錯誤訊息和修復建議

## 🔗 相關資源

- [GitHub Actions 配置](../../.github/workflows/ci.yml)
- [本地測試腳本](../../scripts/ci-local-test.sh)
- [自動修復腳本](../../scripts/ci-fix.sh)

## 📞 需要幫助？

1. 查看 [QUICK_START.md](./QUICK_START.md) 快速解決常見問題
2. 查看 [CI_GUIDE.md](./CI_GUIDE.md) 了解詳細資訊
3. 在 GitHub Issues 搜尋類似問題
4. 建立新的 Issue 並附上錯誤訊息

---

**最後更新**: 2026-04-18
