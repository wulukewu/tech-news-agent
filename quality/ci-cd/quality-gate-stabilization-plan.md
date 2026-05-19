# Quality Gate Stabilization Plan

## 背景

目前專案的主要風險不是單一功能，而是「品質閘門本身不穩」：lint/test 入口不一致、測試流程受執行環境影響、前端測試失敗數量高。這會直接降低 CI 結果可信度，讓「綠燈」與「可發布」無法等價。

## 目前已觀察到的核心問題

1. `make lint-backend` / `make lint` 失敗
   根目錄 `Makefile` 會呼叫 `cd backend && make lint`，但 `backend/` 缺少對應 target。
2. `make test-backend` 在 Docker 環境容易誤判
   `scripts/dev-test.sh` 只要偵測到 `backend` 容器在跑，就切到 `docker-compose exec backend`。在容器缺少測試檔或掛載不一致時，會出現 `collected 0 items` 的假失敗。
3. 前端測試現況失敗量高
   測試一次跑完時會出現大量失敗（integration/property 混跑下尤為明顯），目前不適合作為穩定 gate。

## 改善目標

- 統一本地與 CI 的執行入口（同一套命令、同一判定標準）。
- 讓 lint/test 的失敗訊息可定位、可重現。
- 把前端測試拆成「穩定 gate」與「擴展驗證」兩層，先恢復可持續交付。

## 改善方案（分階段）

### Phase 1: 修復命令入口與執行一致性（最高優先）

#### 1. 修正 backend lint 入口（擇一，建議 A）

- A. 在 `backend/Makefile` 補齊標準 target：`lint`、`format`、`type-check`、`test`
- B. 或改根目錄 `Makefile`，不要依賴 `backend make lint`，改為直接呼叫明確命令

建議 target 定義（示意）：

```makefile
lint:
	black --check app/ tests/
	ruff check app/ tests/
	mypy app/ --ignore-missing-imports --no-strict-optional --python-version=3.11

test:
	pytest -v --tb=short -n auto
```

#### 2. 修正 `scripts/dev-test.sh` 的 Docker 偵測策略

目前「自動偵測容器即走 Docker」太脆弱，改為：

- 預設永遠跑本機（local venv / local node_modules）
- 使用 `--docker` 才走 `docker compose exec`
- 執行前加 preflight：
  - local 模式：檢查 `pytest` / `npm` 是否存在
  - docker 模式：檢查容器內是否有 `/app/tests`

建議調整：

```bash
# 預設
RUN_MODE="local"

# 參數
# --docker => RUN_MODE="docker"

if [ "$RUN_MODE" = "docker" ]; then
  docker-compose exec backend test -d /app/tests || {
    echo "❌ /app/tests not found in backend container"
    exit 1
  }
fi
```

#### 3. 將 CI 與本地入口對齊

- `scripts/ci-local-test.sh` 與 `.github/workflows/ci.yml` 使用同一組命令順序
- 不要在本地腳本使用一套、CI workflow 再另外拼一套

最低要求：

1. Backend: black → ruff → mypy → pytest
2. Frontend: prettier check → eslint → type-check → vitest → build

---

### Phase 2: 恢復可用的前端測試 gate

#### 1. 測試分層（必要）

把前端測試拆成：

- **Gate 套件（阻擋合併）**：穩定 unit + 穩定 integration 子集
- **Extended 套件（非阻擋）**：property、高波動 integration、e2e

建議 `package.json` 新增：

```json
{
  "scripts": {
    "test:gate": "vitest run __tests__/unit __tests__/integration --exclude **/*.property.test.*",
    "test:extended": "vitest run __tests__/property"
  }
}
```

#### 2. 修復已知高頻失敗型態

- 測試查詢選擇器衝突（例如重複 `data-testid`）
- 非決定性資料造成 assertion 漂移（時間、隨機值、locale）
- property test shrink 後 counterexample 對應不到實際渲染輸出

技術原則：

- 對時間使用固定 clock
- 對隨機數注入 deterministic seed
- 對 i18n 測試使用穩定 fixture，而非共用 mutable 狀態

---

### Phase 3: 讓品質閘門可維運

#### 1. 報告格式標準化

- pytest 輸出 JUnit XML
- vitest 輸出 JSON/JUnit（擇一）
- CI job summary 統一附上失敗案例連結與修復提示

#### 2. 覆蓋率策略

- 不一次拉高閾值，先固定最低可接受線
- 僅在穩定套件上設 gate（例如 `test:gate`）
- 每次提升閾值時，先補對應測試再調門檻

#### 3. 建立「失敗分流規則」

- 命令入口錯誤（腳本/Makefile）→ build tooling 負責
- 測試資料或 fixture 問題 → 測試所有者修復
- 真實功能 regression → 功能模組 owner 修復

## 建議實作清單（可直接開工）

1. 新增 `backend/Makefile` 並補齊 `lint/test/type-check/format`。
2. 修改根目錄 `Makefile`，確保 `lint-backend` 不再依賴不存在的 target。
3. 重構 `scripts/dev-test.sh`：預設 local，新增 `--docker` 顯式模式。
4. 修改 frontend scripts：加入 `test:gate` 與 `test:extended`。
5. 更新 `.github/workflows/ci.yml`：PR 先跑 gate，extended 改為非阻擋或排程。
6. 更新 `docs/quality/ci-cd/quick-ci-guide.md`（若存在）與對應 README 連結。

## 驗收標準

- `make lint` 可完整執行，不再因 backend target 缺失中止。
- `make test-backend` 在 local 模式可穩定發現並執行測試（非 `0 items`）。
- PR 的 CI 在同一 commit 上重跑結果一致，不因執行環境差異忽紅忽綠。
- 前端 gate 測試能作為合併阻擋條件；extended 測試不影響主幹交付節奏。
