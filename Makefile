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
