.PHONY: help dev prod build-dev build-prod up-dev up-prod down-dev down-prod logs-dev logs-prod clean

help: ## 顯示此幫助訊息
	@echo "可用指令："
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# 開發環境指令
dev: ## 啟動開發環境 (hot reloading)
	docker-compose up -d

build-dev: ## 重新建置開發環境映像檔
	docker-compose build

up-dev: ## 重新建置並啟動開發環境
	docker-compose up -d --build

down-dev: ## 停止開發環境
	docker-compose down

logs-dev: ## 查看開發環境日誌
	docker-compose logs -f

# 正式環境指令
prod: ## 啟動正式環境
	docker-compose -f docker-compose.prod.yml up -d

build-prod: ## 重新建置正式環境映像檔
	docker-compose -f docker-compose.prod.yml build

up-prod: ## 重新建置並啟動正式環境
	docker-compose -f docker-compose.prod.yml up -d --build

down-prod: ## 停止正式環境
	docker-compose -f docker-compose.prod.yml down

logs-prod: ## 查看正式環境日誌
	docker-compose -f docker-compose.prod.yml logs -f

# 清理指令
clean: ## 清理所有容器、映像檔和 volumes
	docker-compose down -v
	docker-compose -f docker-compose.prod.yml down -v
	docker system prune -f

# 快速指令
restart-dev: down-dev dev ## 重啟開發環境

restart-prod: down-prod prod ## 重啟正式環境

ps: ## 查看運行中的容器
	docker-compose ps

# 開發工具指令
setup: ## 初始化開發環境
	@echo "🚀 Setting up development environment..."
	@bash scripts/dev-setup.sh

test: ## 執行所有測試
	@echo "🧪 Running all tests..."
	@bash scripts/dev-test.sh

test-frontend: ## 執行 frontend 測試
	@echo "🧪 Running frontend tests..."
	@bash scripts/dev-test.sh --frontend

test-backend: ## 執行 backend 測試
	@echo "🧪 Running backend tests..."
	@bash scripts/dev-test.sh --backend

test-coverage: ## 執行測試並生成覆蓋率報告
	@echo "📊 Running tests with coverage..."
	@bash scripts/dev-test.sh --coverage

test-watch: ## 執行測試監視模式 (frontend)
	@echo "👀 Running tests in watch mode..."
	@bash scripts/dev-test.sh --frontend --watch

# 資料庫管理指令
db-status: ## 檢查資料庫狀態
	@echo "🔍 Checking database status..."
	@bash scripts/dev-migrate.sh status

db-init: ## 初始化資料庫結構
	@echo "🗄️ Initializing database..."
	@bash scripts/dev-migrate.sh init

db-seed: ## 填充預設資料
	@echo "🌱 Seeding database..."
	@bash scripts/dev-migrate.sh seed

db-reset: ## 重置資料庫
	@echo "🔄 Resetting database..."
	@bash scripts/dev-migrate.sh reset

db-backup: ## 備份資料庫
	@echo "💾 Creating database backup..."
	@bash scripts/dev-migrate.sh backup

# 開發體驗指令
test-hmr: ## 測試熱模組替換性能
	@echo "🔥 Testing Hot Module Replacement..."
	@bash scripts/test-hmr.sh

test-hmr-frontend: ## 測試前端 HMR
	@echo "🔥 Testing frontend HMR..."
	@bash scripts/test-hmr.sh --frontend

test-hmr-backend: ## 測試後端自動重載
	@echo "🔥 Testing backend auto-reload..."
	@bash scripts/test-hmr.sh --backend

# 程式碼品質指令
lint: ## 執行所有程式碼檢查 (frontend + backend)
	@echo "🔍 Running frontend linting..."
	cd frontend && npm run lint
	@echo "🔍 Running backend linting..."
	cd backend && make lint
	@echo "✅ All linting checks passed!"

lint-frontend: ## 執行 frontend 程式碼檢查
	cd frontend && npm run lint

lint-backend: ## 執行 backend 程式碼檢查
	cd backend && make lint

format: ## 格式化所有程式碼 (frontend + backend)
	@echo "✨ Formatting frontend code..."
	cd frontend && npm run format
	@echo "✨ Formatting backend code..."
	cd backend && make format
	@echo "✅ All code formatted!"

format-frontend: ## 格式化 frontend 程式碼
	cd frontend && npm run format

format-backend: ## 格式化 backend 程式碼
	cd backend && make format

format-check: ## 檢查程式碼格式 (不修改)
	@echo "🔍 Checking frontend formatting..."
	cd frontend && npm run format:check
	@echo "🔍 Checking backend formatting..."
	cd backend && make format-check
	@echo "✅ All formatting checks passed!"

check: lint format-check ## 執行所有程式碼品質檢查

# Pre-commit hooks
pre-commit-install: ## 安裝 pre-commit hooks
	@echo "🔧 Installing pre-commit hooks..."
	@bash scripts/setup-pre-commit.sh

pre-commit-run: ## 執行所有 pre-commit hooks
	@echo "🔍 Running pre-commit hooks on all files..."
	pre-commit run --all-files

pre-commit-update: ## 更新 pre-commit hooks 到最新版本
	@echo "🔄 Updating pre-commit hooks..."
	pre-commit autoupdate

pre-commit-clean: ## 清理 pre-commit cache
	@echo "🧹 Cleaning pre-commit cache..."
	pre-commit clean
	pre-commit install
