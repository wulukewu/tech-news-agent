#!/bin/bash
# DM 對話記憶系統 - 快速測試腳本

echo "🧪 DM 對話記憶系統 - 快速測試"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test counter
PASS=0
FAIL=0

echo -e "${BLUE}📋 測試清單${NC}"
echo "--------------------------------"
echo ""

echo -e "${YELLOW}測試 1: 資料庫 Schema 驗證${NC}"
echo "請在 Supabase Dashboard 執行以下 SQL:"
echo ""
echo "SELECT COUNT(*) FROM dm_conversations;"
echo "SELECT column_name FROM information_schema.columns"
echo "WHERE table_name = 'preference_model'"
echo "  AND column_name IN ('preference_summary', 'summary_updated_at');"
echo ""
read -p "✓ Schema 驗證通過? (y/n): " schema_ok
if [ "$schema_ok" = "y" ]; then
    echo -e "${GREEN}✓ 測試 1 通過${NC}"
    ((PASS++))
else
    echo -e "${RED}✗ 測試 1 失敗${NC}"
    ((FAIL++))
fi
echo ""

echo -e "${YELLOW}測試 2: Discord DM 測試${NC}"
echo "步驟:"
echo "1. 在 Discord 發送 DM 給 bot: '我喜歡 Rust 和系統程式設計'"
echo "2. Bot 應該回覆: '✅ 已記錄你的偏好！...'"
echo ""
read -p "✓ Bot 有正確回應? (y/n): " dm_ok
if [ "$dm_ok" = "y" ]; then
    echo -e "${GREEN}✓ 測試 2 通過${NC}"
    ((PASS++))
else
    echo -e "${RED}✗ 測試 2 失敗${NC}"
    ((FAIL++))
fi
echo ""

echo -e "${YELLOW}測試 3: 生成偏好摘要${NC}"
echo "步驟:"
echo "1. 發送 2-3 則 DM 給 bot"
echo "2. 在 Discord 執行: /update_profile"
echo "3. 應該看到生成的偏好摘要"
echo ""
read -p "✓ 偏好摘要生成成功? (y/n): " summary_ok
if [ "$summary_ok" = "y" ]; then
    echo -e "${GREEN}✓ 測試 3 通過${NC}"
    ((PASS++))
else
    echo -e "${RED}✗ 測試 3 失敗${NC}"
    ((FAIL++))
fi
echo ""

echo -e "${YELLOW}測試 4: 查看偏好檔案${NC}"
echo "步驟:"
echo "1. 在 Discord 執行: /my_profile"
echo "2. 應該看到偏好摘要和分類權重"
echo ""
read -p "✓ 偏好檔案顯示正常? (y/n): " profile_ok
if [ "$profile_ok" = "y" ]; then
    echo -e "${GREEN}✓ 測試 4 通過${NC}"
    ((PASS++))
else
    echo -e "${RED}✗ 測試 4 失敗${NC}"
    ((FAIL++))
fi
echo ""

echo -e "${YELLOW}測試 5: 前端介面${NC}"
echo "步驟:"
echo "1. 訪問: http://localhost:3000/preferences"
echo "2. 應該看到偏好摘要和分類權重視覺化"
echo ""
read -p "✓ 前端頁面正常顯示? (y/n): " frontend_ok
if [ "$frontend_ok" = "y" ]; then
    echo -e "${GREEN}✓ 測試 5 通過${NC}"
    ((PASS++))
else
    echo -e "${RED}✗ 測試 5 失敗${NC}"
    ((FAIL++))
fi
echo ""

# Summary
echo "================================"
echo -e "${BLUE}📊 測試總結${NC}"
echo "================================"
TOTAL=$((PASS + FAIL))
PERCENTAGE=$((PASS * 100 / TOTAL))

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ 所有測試通過！($PASS/$TOTAL)${NC}"
    echo ""
    echo -e "${GREEN}🎉 DM 對話記憶系統運作正常！${NC}"
    echo ""
    echo "下一步:"
    echo "  1. 開始使用系統，累積更多 DM 對話"
    echo "  2. 觀察推薦是否變得更精準"
    echo "  3. 監控用戶反饋和數據指標"
    echo ""
elif [ $PERCENTAGE -ge 60 ]; then
    echo -e "${YELLOW}⚠ 大部分測試通過 ($PASS/$TOTAL - $PERCENTAGE%)${NC}"
    echo ""
    echo -e "${YELLOW}系統基本可用，但有 $FAIL 個問題需要修復${NC}"
    echo ""
    echo "請查看 TEST_DM_MEMORY.md 的故障排除章節"
    echo ""
else
    echo -e "${RED}✗ 多數測試失敗 ($PASS/$TOTAL - $PERCENTAGE%)${NC}"
    echo ""
    echo -e "${RED}系統需要修復${NC}"
    echo ""
    echo "建議:"
    echo "  1. 檢查 backend logs: docker-compose logs -f backend"
    echo "  2. 驗證 migration 是否正確執行"
    echo "  3. 確認 ENABLE_DM_LISTENER=true"
    echo "  4. 查看詳細測試指南: TEST_DM_MEMORY.md"
    echo ""
fi
