#!/bin/bash

# 環境變數設定腳本
# 此腳本會幫助你快速設定開發環境的環境變數

set -e

echo "=================================="
echo "Tech News Agent - 環境變數設定"
echo "=================================="
echo ""

# 檢查 .env.example 是否存在
if [ ! -f ".env.example" ]; then
    echo "❌ 錯誤: .env.example 不存在"
    exit 1
fi

# 環境變數設定
echo "📦 設定環境變數..."
if [ -f ".env" ]; then
    echo "⚠️  .env 已存在"
    read -p "是否要覆蓋? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "⏭️  跳過 .env"
    else
        cp .env.example .env
        echo "✅ 已建立 .env"
    fi
else
    cp .env.example .env
    echo "✅ 已建立 .env"
fi

echo ""
echo "=================================="
echo "✅ 環境變數檔案設定完成！"
echo "=================================="
echo ""
echo "📝 下一步:"
echo "1. 編輯 .env 填入你的實際值"
echo "   nano .env"
echo ""
echo "2. 必填項目:"
echo "   - SUPABASE_URL"
echo "   - SUPABASE_KEY"
echo "   - DISCORD_TOKEN"
echo "   - DISCORD_CHANNEL_ID"
echo "   - DISCORD_CLIENT_ID"
echo "   - DISCORD_CLIENT_SECRET"
echo "   - GROQ_API_KEY"
echo "   - JWT_SECRET (使用: openssl rand -hex 32)"
echo ""
echo "3. 啟動開發環境"
echo "   make dev"
echo ""
echo "4. 查看日誌確認啟動成功"
echo "   make logs-dev"
echo ""
echo "📚 相關文件:"
echo "- ENV_SETUP_GUIDE.md - 環境變數完整說明"
echo "- QUICKSTART.md - 快速開始指南"
echo "- DOCKER_GUIDE.md - Docker 使用指南"
echo ""
