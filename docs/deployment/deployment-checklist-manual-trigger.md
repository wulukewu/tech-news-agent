# 手動觸發功能部署檢查清單

在部署手動觸發 scheduler 功能前，請確認以下項目。

## 程式碼檢查

### 後端

- [x] `backend/app/api/scheduler.py` 已創建
- [x] `backend/app/bot/cogs/admin_commands.py` 已創建
- [x] `backend/app/main.py` 已更新（註冊 router）
- [x] `backend/app/bot/client.py` 已更新（載入 cog）
- [x] 所有檔案無語法錯誤
- [x] Import 路徑正確

### 前端

- [x] `frontend/lib/api/scheduler.ts` 已創建
- [x] `frontend/components/TriggerSchedulerButton.tsx` 已創建
- [x] `frontend/app/dashboard/page.tsx` 已更新
- [x] 所有檔案無語法錯誤
- [x] Import 路徑正確

### 測試

- [x] `backend/tests/test_scheduler_manual_trigger.py` 已創建
- [x] `backend/tests/test_admin_commands.py` 已創建
- [x] `scripts/test_manual_trigger.sh` 已創建並有執行權限

### 文件

- [x] `docs/MANUAL_SCHEDULER_TRIGGER.md` 已創建
- [x] `docs/MANUAL_TRIGGER_EXAMPLES.md` 已創建
- [x] `docs/QUICK_START_MANUAL_TRIGGER.md` 已創建
- [x] `README.md` 已更新
- [x] `CHANGELOG.md` 已創建
- [x] `IMPLEMENTATION_SUMMARY.md` 已創建

## 部署前測試

### 本地測試

- [ ] 後端服務啟動成功

  ```bash
  cd backend && python -m app.main
  ```

- [ ] Discord bot 連線成功

  ```bash
  # 檢查日誌中是否有 "Discord Bot is fully ready and listening."
  ```

- [ ] 前端應用啟動成功

  ```bash
  cd frontend && npm run dev
  ```

- [ ] API endpoint 測試通過
  ```bash
  ./scripts/test_manual_trigger.sh http://localhost:8000 YOUR_JWT_TOKEN
  ```

### 功能測試

- [ ] Discord `/trigger_fetch` 指令可執行
- [ ] Discord `/scheduler_status` 指令可執行
- [ ] 前端按鈕可點擊
- [ ] 前端按鈕顯示載入狀態
- [ ] 前端按鈕顯示成功/失敗訊息
- [ ] API 返回正確的狀態碼（202, 200）
- [ ] 未認證請求返回 401

### 整合測試

- [ ] 觸發後 scheduler 確實執行

  ```bash
  # 檢查日誌中是否有 "Starting background_fetch_job"
  ```

- [ ] 執行完成後狀態更新

  ```bash
  # 使用 /scheduler_status 確認
  ```

- [ ] 新文章出現在資料庫
  ```bash
  # 使用 /news_now 確認
  ```

### 單元測試

- [ ] 後端測試通過

  ```bash
  python3 -m pytest backend/tests/test_scheduler_manual_trigger.py -v
  python3 -m pytest backend/tests/test_admin_commands.py -v
  ```

- [ ] 現有測試未被破壞
  ```bash
  python3 -m pytest backend/tests/test_scheduler_unit.py -v
  ```

## 環境變數檢查

- [ ] `SUPABASE_URL` 已設定
- [ ] `SUPABASE_KEY` 已設定
- [ ] `DISCORD_TOKEN` 已設定
- [ ] `GROQ_API_KEY` 已設定
- [ ] `JWT_SECRET` 已設定
- [ ] `CORS_ORIGINS` 包含前端網址

## Docker 部署檢查

### 開發環境

- [ ] `docker-compose.yml` 無需修改（使用現有配置）
- [ ] 建置成功

  ```bash
  docker-compose build
  ```

- [ ] 啟動成功

  ```bash
  docker-compose up -d
  ```

- [ ] 服務健康檢查通過
  ```bash
  docker-compose ps
  ```

### 生產環境

- [ ] `docker-compose.prod.yml` 無需修改
- [ ] 建置成功

  ```bash
  docker-compose -f docker-compose.prod.yml build
  ```

- [ ] 啟動成功

  ```bash
  docker-compose -f docker-compose.prod.yml up -d
  ```

- [ ] 服務健康檢查通過
  ```bash
  docker-compose -f docker-compose.prod.yml ps
  ```

## 安全性檢查

- [ ] API endpoint 需要認證
- [ ] JWT token 驗證正常
- [ ] 未認證請求被拒絕
- [ ] 錯誤訊息不洩漏敏感資訊
- [ ] 日誌記錄所有觸發操作
- [ ] 考慮添加 rate limiting（建議）
- [ ] 考慮添加權限檢查（建議）

## 效能檢查

- [ ] 背景任務不阻塞 API 回應
- [ ] 多次觸發不會造成系統崩潰
- [ ] 記憶體使用正常
- [ ] CPU 使用正常
- [ ] 資料庫連線正常

## 監控檢查

- [ ] 日誌記錄正常

  ```bash
  # 檢查是否有 "Manual scheduler trigger requested by user"
  ```

- [ ] 錯誤日誌正常

  ```bash
  # 檢查是否有錯誤堆疊追蹤
  ```

- [ ] 健康檢查端點正常
  ```bash
  curl http://localhost:8000/health/scheduler
  ```

## 文件檢查

- [ ] README.md 更新正確
- [ ] 新功能已記錄在 CHANGELOG.md
- [ ] 使用範例清晰易懂
- [ ] API 文件完整
- [ ] 故障排除指南完整

## 使用者體驗檢查

- [ ] Discord 指令回應友善
- [ ] 前端按鈕位置合理
- [ ] 載入狀態清晰
- [ ] 錯誤訊息有幫助
- [ ] 成功訊息明確

## 回滾計畫

如果部署後發現問題，可以：

1. **移除 Discord 指令**

   ```python
   # 在 backend/app/bot/client.py 中註解掉
   # await self.load_extension("app.bot.cogs.admin_commands")
   ```

2. **移除 API endpoint**

   ```python
   # 在 backend/app/main.py 中註解掉
   # app.include_router(scheduler_api.router, prefix="/api", tags=["scheduler"])
   ```

3. **移除前端按鈕**

   ```typescript
   // 在 frontend/app/dashboard/page.tsx 中註解掉
   // <TriggerSchedulerButton />
   ```

4. **重新部署**
   ```bash
   docker-compose restart
   ```

## 部署後驗證

### 立即驗證（部署後 5 分鐘內）

- [ ] 服務啟動成功
- [ ] Discord bot 在線
- [ ] 前端可訪問
- [ ] 健康檢查通過

### 短期驗證（部署後 1 小時內）

- [ ] Discord 指令可用
- [ ] 前端按鈕可用
- [ ] API endpoint 可用
- [ ] 觸發功能正常

### 長期驗證（部署後 24 小時內）

- [ ] 無異常錯誤日誌
- [ ] 效能指標正常
- [ ] 使用者回饋正面
- [ ] 定時排程未受影響

## 通知相關人員

- [ ] 通知團隊成員新功能已部署
- [ ] 更新內部文件
- [ ] 通知使用者新功能可用
- [ ] 提供使用指南連結

## 完成確認

- [ ] 所有檢查項目已完成
- [ ] 測試結果已記錄
- [ ] 問題已解決或記錄
- [ ] 部署已完成
- [ ] 驗證已通過

---

## 簽核

- 開發者: ********\_******** 日期: ****\_****
- 測試者: ********\_******** 日期: ****\_****
- 部署者: ********\_******** 日期: ****\_****

## 備註

記錄任何特殊情況或需要注意的事項：

```
[在此記錄備註]
```
