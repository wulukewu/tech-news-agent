#!/bin/bash

# Tech News Agent - 遷移到 Docker Compose 架構腳本
# 此腳本將現有的 FastAPI 後端移動到 backend/ 目錄

set -e

echo "=========================================="
echo "Tech News Agent 專案重構遷移工具"
echo "=========================================="
echo ""

# 檢查是否在專案根目錄
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 錯誤：請在專案根目錄執行此腳本"
    exit 1
fi

# 檢查 backend 目錄是否已存在
if [ -d "backend/app" ]; then
    echo "⚠️  警告：backend/app 目錄已存在"
    read -p "是否要覆蓋？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 取消遷移"
        exit 1
    fi
fi

echo "📦 步驟 1: 建立 backend 目錄結構..."
mkdir -p backend

echo "📦 步驟 2: 移動後端檔案..."

# 移動核心檔案
if [ -d "app" ]; then
    echo "  - 移動 app/ 目錄"
    mv app backend/ 2>/dev/null || cp -r app backend/
fi

if [ -f "requirements.txt" ]; then
    echo "  - 移動 requirements.txt"
    cp requirements.txt backend/
fi

if [ -f "requirements-dev.txt" ]; then
    echo "  - 移動 requirements-dev.txt"
    cp requirements-dev.txt backend/
fi

if [ -f "pytest.ini" ]; then
    echo "  - 移動 pytest.ini"
    cp pytest.ini backend/
fi

if [ -d "tests" ]; then
    echo "  - 移動 tests/ 目錄"
    cp -r tests backend/
fi

if [ -d "scripts" ]; then
    echo "  - 移動 scripts/ 目錄"
    cp -r scripts backend/
fi

# 複製環境變數檔案
if [ -f ".env" ]; then
    echo "  - 複製 .env 到 backend/"
    cp .env backend/.env
    echo ""
    echo "⚠️  重要：請檢查 backend/.env 並確保包含以下設定："
    echo "    CORS_ORIGINS=http://localhost:3000,http://localhost:8000"
    echo ""
fi

# 複製文件
if [ -d "docs" ]; then
    echo "  - 複製 docs/ 目錄"
    cp -r docs backend/
fi

if [ -f "README.md" ]; then
    echo "  - 複製 README.md"
    cp README.md backend/
fi

if [ -f "README_zh.md" ]; then
    echo "  - 複製 README_zh.md"
    cp README_zh.md backend/
fi

echo "✅ 後端檔案遷移完成"
echo ""

echo "📦 步驟 3: 建立 frontend 目錄結構..."
mkdir -p frontend

# 檢查 frontend/.env.example 是否已存在
if [ ! -f "frontend/.env.example" ]; then
    echo "❌ 錯誤：frontend/.env.example 不存在"
    echo "   請確保已執行 git pull 獲取最新的專案結構"
    exit 1
fi

# 複製環境變數範例
if [ ! -f "frontend/.env.local" ]; then
    echo "  - 建立 frontend/.env.local"
    cp frontend/.env.example frontend/.env.local
fi

echo "✅ 前端目錄結構建立完成"
echo ""

echo "📦 步驟 4: 驗證 Docker 配置..."

# 檢查 Docker 和 Docker Compose
if ! command -v docker &> /dev/null; then
    echo "⚠️  警告：未安裝 Docker"
    echo "   請先安裝 Docker: https://docs.docker.com/get-docker/"
else
    echo "✅ Docker 已安裝"
fi

if ! command -v docker-compose &> /dev/null; then
    echo "⚠️  警告：未安裝 Docker Compose"
    echo "   請先安裝 Docker Compose: https://docs.docker.com/compose/install/"
else
    echo "✅ Docker Compose 已安裝"
fi

echo ""
echo "=========================================="
echo "✅ 遷移完成！"
echo "=========================================="
echo ""
echo "下一步："
echo ""
echo "1. 檢查並更新 backend/.env 檔案"
echo "   確保包含: CORS_ORIGINS=http://localhost:3000,http://localhost:8000"
echo ""
echo "2. 初始化前端專案（如果尚未初始化）："
echo "   cd frontend"
echo "   npx create-next-app@latest . --typescript --tailwind --app --no-src-dir"
echo ""
echo "3. 啟動服務："
echo "   docker-compose up -d"
echo ""
echo "4. 查看日誌："
echo "   docker-compose logs -f"
echo ""
echo "5. 訪問服務："
echo "   - 後端: http://localhost:8000"
echo "   - 前端: http://localhost:3000"
echo ""
echo "詳細說明請參考 MIGRATION_GUIDE.md 和 README_DOCKER.md"
echo ""
