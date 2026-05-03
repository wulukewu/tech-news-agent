#!/bin/bash
# 測試對話 API

echo "🧪 測試對話 API"
echo "================================"
echo ""

# Test 1: Health check
echo "測試 1: Backend 健康檢查"
HEALTH=$(curl -s http://localhost:8000/health)
if echo "$HEALTH" | grep -q "ok"; then
    echo "✓ Backend 正常運行"
else
    echo "✗ Backend 異常"
    exit 1
fi
echo ""

# Test 2: Conversations endpoint (without auth)
echo "測試 2: Conversations API (無認證)"
RESPONSE=$(curl -s http://localhost:8000/api/conversations)
echo "回應: $RESPONSE"

if echo "$RESPONSE" | grep -q "Unauthorized\|Not authenticated"; then
    echo "✓ API 需要認證（正常）"
elif echo "$RESPONSE" | grep -q "Method Not Allowed"; then
    echo "⚠ Method Not Allowed - 可能是路由問題"
else
    echo "? 未預期的回應"
fi
echo ""

# Test 3: Check if user is logged in (frontend)
echo "測試 3: 前端登入狀態"
echo "請在瀏覽器 Console 執行以下指令檢查:"
echo ""
echo "localStorage.getItem('auth_token')"
echo ""
echo "如果返回 null，表示沒有登入"
echo ""

echo "================================"
echo "診斷建議:"
echo "================================"
echo ""
echo "1. 確認你已經登入系統"
echo "   - 訪問: http://localhost:3000"
echo "   - 點擊右上角「登入」"
echo "   - 使用 Discord OAuth 登入"
echo ""
echo "2. 如果已登入但還是失敗:"
echo "   - 清除瀏覽器快取"
echo "   - 在 Console 執行: localStorage.clear()"
echo "   - 重新登入"
echo ""
echo "3. 檢查 backend logs:"
echo "   docker-compose logs backend --tail 50"
echo ""
