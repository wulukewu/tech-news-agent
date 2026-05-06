# 通知狀態「未排程」問題修復指南

## 🎯 問題描述

用戶反映通知設定已開啟，但狀態顯示為「未排程」，這表示前端設定和後端排程系統之間沒有正確連接。

## 🔧 修復內容

### 1. 改進前端狀態顯示

- ✅ 添加了更詳細的狀態檢查邏輯
- ✅ 區分「已停用」、「未排程」、「狀態未知」等不同情況
- ✅ 添加了載入狀態和錯誤處理

### 2. 新增重新排程功能

- ✅ 後端新增 `/api/notifications/preferences/reschedule` 端點
- ✅ 前端添加「重新排程」按鈕
- ✅ 用戶可以手動觸發排程修復

### 3. 診斷工具

- ✅ 創建了 `debug_notification_status.py` 診斷腳本
- ✅ 可以檢查排程器狀態、用戶偏好設定、排程任務等

## 🚀 使用方法

### 方法1: 使用前端重新排程按鈕

1. **訪問通知設定頁面**

   ```
   http://localhost:3000/app/settings/notifications
   ```

2. **檢查狀態顯示**
   - 🟢 「已排程」- 正常狀態
   - 🟡 「檢查中...」- 正在載入狀態
   - 🟠 「未排程」- 需要修復
   - 🔴 「已停用」- 通知已關閉
   - 🟡 「狀態未知」- API錯誤

3. **使用重新排程按鈕**
   - 如果狀態顯示「未排程」，會出現「重新排程」按鈕
   - 點擊按鈕會自動修復排程問題
   - 成功後狀態會更新為「已排程」

### 方法2: 使用診斷腳本

```bash
# 運行診斷腳本
python3 debug_notification_status.py
```

**腳本功能**:

1. 檢查動態排程器狀態
2. 檢查通知系統集成
3. 檢查用戶偏好設定
4. 檢查個別用戶的排程狀態
5. 自動嘗試修復問題

### 方法3: 手動API調用

```bash
# 獲取通知狀態
curl -X GET "http://localhost:8000/api/notifications/preferences/status" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 手動重新排程
curl -X POST "http://localhost:8000/api/notifications/preferences/reschedule" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🔍 問題排查

### 常見原因

1. **動態排程器未初始化**
   - 檢查後端啟動日誌
   - 確認 `DynamicScheduler initialized successfully` 消息

2. **通知系統集成未初始化**
   - 檢查 `Notification system integration initialized successfully` 消息

3. **用戶偏好設定問題**
   - 確認用戶有有效的偏好設定記錄
   - 檢查頻率不是 'disabled'，dm_enabled 為 true

4. **排程任務丟失**
   - 可能由於服務重啟導致內存中的排程任務丟失
   - 使用重新排程功能可以恢復

### 檢查步驟

1. **檢查後端日誌**

   ```bash
   # 查看後端啟動日誌
   tail -f backend/logs/app.log
   ```

2. **檢查數據庫**

   ```sql
   -- 檢查用戶偏好設定
   SELECT * FROM user_notification_preferences;

   -- 檢查用戶表
   SELECT id, discord_id, dm_enabled FROM users;
   ```

3. **檢查排程器狀態**
   ```python
   # 在後端控制台中
   from app.tasks.scheduler import get_dynamic_scheduler
   scheduler = get_dynamic_scheduler()
   if scheduler:
       jobs = scheduler.scheduler.get_jobs()
       print(f"Active jobs: {len(jobs)}")
   ```

## 🎉 修復後的改進

### 用戶體驗改進

- ✅ 更清晰的狀態指示
- ✅ 自助修復功能
- ✅ 實時狀態更新
- ✅ 詳細的錯誤信息

### 系統穩定性改進

- ✅ 更好的錯誤處理
- ✅ 自動重試機制
- ✅ 診斷和修復工具
- ✅ 詳細的日誌記錄

## 📋 部署檢查清單

在部署修復後，請確認：

- [ ] 後端服務正常啟動
- [ ] 動態排程器初始化成功
- [ ] 通知系統集成初始化成功
- [ ] 前端狀態顯示正確
- [ ] 重新排程按鈕功能正常
- [ ] 診斷腳本可以正常運行

## 🔄 預防措施

為了避免將來出現類似問題：

1. **監控排程器健康狀態**
   - 定期檢查排程任務數量
   - 監控排程執行成功率

2. **自動修復機制**
   - 在系統啟動時自動檢查和修復排程
   - 定期運行健康檢查

3. **用戶通知**
   - 當檢測到排程問題時通知用戶
   - 提供自助修復選項

---

**修復完成時間**: 2026-04-20
**修復狀態**: ✅ 完成
**測試狀態**: ✅ 待測試
**部署建議**: 需要重啟後端服務以應用新的API端點
