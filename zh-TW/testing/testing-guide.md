# 測試指南

此專案為後端和前端使用單獨的測試套件。

## 專案結構

```
tech-news-agent/
├── backend/
│   ├── tests/              # 後端 Python 測試
│   ├── pytest.ini          # 後端 pytest 配置
│   ├── requirements.txt    # 後端依賴
│   └── requirements-dev.txt
│
├── frontend/
│   ├── __tests__/          # 前端單元測試 (Jest)
│   ├── e2e/                # 前端 E2E 測試 (Playwright)
│   ├── jest.config.js
│   └── playwright.config.ts
│
└── .github/workflows/
    └── ci.yml              # 後端與前端的單獨 CI 作業
```

## 後端測試 (Python)

### 設定

```bash
cd backend
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 運行測試

```bash
# 運行所有測試
pytest

# 運行快速測試 (跳過基於屬性和整合測試)
pytest --ignore-glob="*property*.py" --ignore=tests/integration/

# 運行帶覆蓋率的測試
pytest --cov=app --cov-report=html

# 運行特定測試文件
pytest tests/test_auth_integration.py

# 並行運行測試
pytest -n auto
```

### 測試類別

- **單元測試**: `test_*.py` (非屬性、非整合)
- **基於屬性的測試**: `test_*_property.py` (使用 Hypothesis)
- **整合測試**: `tests/integration/`

## 前端測試 (TypeScript/JavaScript)

### 設定

```bash
cd frontend
npm install
```

### 運行測試

```bash
# 運行單元測試 (Jest)
npm test

# 在監聽模式下運行測試
npm run test:watch

# 運行帶覆蓋率的測試
npm run test:coverage

# 運行 E2E 測試 (Playwright)
npm run test:e2e

# 帶 UI 運行 E2E 測試
npm run test:e2e:ui

# 型別檢查
npm run type-check

# Linting
npm run lint
```

## CI/CD

GitHub Actions 並行運行兩個測試套件：

- **後端作業**: Python 測試與 pytest
- **前端作業**: TypeScript 檢查、Linting、單元測試和建置

### CI 配置

請參閱 `.github/workflows/ci.yml` 以了解完整的 CI 管道。

### 快速測試 (所有分支)

```bash
# 後端
pytest --ignore-glob="*property*.py" --ignore=tests/integration/

# 前端
npm test -- --passWithNoTests
```

### 完整測試 (僅主分支/PR)

```bash
# 後端
pytest  # 包括基於屬性和整合測試

# 前端
npm test && npm run build
```

## 測試的環境變數

後端測試使用虛擬值（請參閱 `.github/workflows/ci.yml`）：

```bash
SUPABASE_URL=https://dummy.supabase.co
SUPABASE_KEY=dummy_supabase_key
DISCORD_TOKEN=dummy_discord_token
DISCORD_CHANNEL_ID=123456789012345678
GROQ_API_KEY=dummy_groq_api_key
TIMEZONE=Asia/Taipei
```

所有外部呼叫均被模擬，因此從不需要真實憑證。

## 編寫測試

### 後端 (pytest)

```python
# tests/test_example.py
import pytest
from app.services.example import example_function

def test_example():
    result = example_function("input")
    assert result == "expected"

@pytest.mark.asyncio
async def test_async_example():
    result = await async_function()
    assert result is not None
```

### 前端 (Jest)

```typescript
// __tests__/example.test.tsx
import { render, screen } from '@testing-library/react'
import Component from '@/components/Component'

describe('Component', () => {
  it('renders correctly', () => {
    render(<Component />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })
})
```

## 故障排除

### 後端

**問題**: `ModuleNotFoundError: No module named 'app'`

- **解決方案**: 從 `backend/` 目錄運行測試

**問題**: `ImportPathMismatchError`

- **解決方案**: 確保您在正確的目錄 (backend/)

### 前端

**問題**: `Cannot find module '@/...'`

- **解決方案**: 檢查 `tsconfig.json` 路徑配置

**問題**: 測試超時

- **解決方案**: 增加 `jest.config.js` 或 `playwright.config.ts` 中的超時時間

## 其他資源

- [pytest 文件](https://docs.pytest.org/)
- [Jest 文件](https://jestjs.io/)
- [Playwright 文件](https://playwright.dev/)
- [Hypothesis (基於屬性的測試)](https://hypothesis.readthedocs.io/)
