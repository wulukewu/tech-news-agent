# CI 測試優化說明

## 問題診斷

### 原始問題

- CI 執行時間：1 小時以上
- 測試總數：811 個測試案例
- 大量使用 Hypothesis property-based testing

### 時間分析

```
Property tests 分佈：
- 107 個測試 × 5 examples = 535 次執行
- 42 個測試 × 20 examples = 840 次執行
- 42 個測試 × 100 examples = 4200 次執行 ⚠️
- 5 個測試 × 50 examples = 250 次執行

總計：約 6000+ 次測試執行
```

## 優化方案

### 1. 平行化測試執行 (`pytest-xdist`)

```yaml
pytest -n auto # 自動使用所有 CPU 核心
```

**預期效果**：在 2-4 核心的 GitHub Actions runner 上，速度提升 2-3 倍

### 2. 減少 CI 的 Hypothesis examples

```python
# conftest.py
settings.register_profile("ci", max_examples=5)  # 從 10 降到 5
```

**預期效果**：Property-based tests 執行時間減少 50%

### 3. 快取 Hypothesis 資料庫

```yaml
- name: Cache Hypothesis database
  uses: actions/cache@v4
  with:
    path: .hypothesis
```

**預期效果**：Hypothesis 會記住已經測試過的案例，避免重複測試

### 4. 超時保護

```yaml
timeout-minutes: 30
```

**預期效果**：如果測試卡住，30 分鐘後自動失敗，不會浪費 CI 時間

## 預期改善

| 項目                   | 優化前   | 優化後     | 改善      |
| ---------------------- | -------- | ---------- | --------- |
| 執行時間               | 60+ 分鐘 | 10-15 分鐘 | **75% ↓** |
| Property examples (CI) | 10       | 5          | 50% ↓     |
| 平行化                 | 無       | 2-4 核心   | 2-3x ↑    |
| 超時保護               | 無       | 30 分鐘    | ✓         |

## 本地開發不受影響

本地測試仍然使用 `default` profile（max_examples=10）：

```bash
pytest  # 使用 default profile
HYPOTHESIS_PROFILE=dev pytest  # 明確指定 dev profile
```

## 進一步優化建議

如果 CI 還是太慢，可以考慮：

### 選項 A：分層測試策略

```yaml
# 快速測試（每次 push）
pytest -m "not slow"

# 完整測試（只在 PR 或 main branch）
pytest
```

### 選項 B：減少個別測試的 max_examples

某些測試用 `max_examples=100` 可能過多，可以降到 20-50：

```python
# 找出最慢的測試
pytest --durations=10

# 針對性調整
@settings(max_examples=20)  # 從 100 降到 20
```

### 選項 C：使用 GitHub Actions matrix

```yaml
strategy:
  matrix:
    test-group: [unit, integration, property]
```

將測試分成多個 job 平行執行

## 監控建議

追蹤以下指標來確認優化效果：

1. CI 執行時間（目標：< 15 分鐘）
2. 測試通過率（應該維持不變）
3. Hypothesis 快取命中率
4. 最慢的 10 個測試（`pytest --durations=10`）
